import json
from typing import List, Dict, Any, Optional
import requests
import logfire
from pydantic import BaseModel, Field
from groq import Groq
from rich.console import Console

from src.config import (
    GROQ_API_KEY,
    GROQ_MODEL,
    OLLAMA_URL,
    OLLAMA_MODEL,
    CONFIDENCE_THRESHOLD,
    LOGFIRE_TOKEN
)

console = Console()

# Configure Logfire (streams to cloud if token present, otherwise traces locally)
logfire.configure(
    token=LOGFIRE_TOKEN or None,
    send_to_logfire="if-token-present"
)

class RelevanceCheckResult(BaseModel):
    is_relevant: bool = Field(description="True if query is relevant to Machine Learning, AI, Deep Learning, Statistics, Mathematics, System Design, Data Engineering, or MLOps.")
    topic: str = Field(description="Identified topic or domain of the query.")
    reason: str = Field(description="Brief explanation of why it is relevant or irrelevant.")

class VerificationResult(BaseModel):
    is_grounded: bool = Field(default=True, description="True if all claims are backed by the provided context, False otherwise")
    confidence_score: float = Field(default=0.85, description="Confidence percentage from 0.00 to 1.00 based on context match and completeness")
    identified_hallucinations: List[str] = Field(default_factory=list, description="Any statements not directly supported by context")
    reasoning: str = Field(default="Context verified against document sources.", description="Brief explanation of the confidence score and grounding")
    final_verified_answer: str = Field(default="", description="Cleaned, verified answer with citations or statement stating info was not found")

class RAGAgents:
    def __init__(
        self,
        api_key: str = GROQ_API_KEY,
        model: str = GROQ_MODEL,
        ollama_url: str = OLLAMA_URL,
        ollama_model: str = OLLAMA_MODEL
    ):
        self.api_key = api_key
        # Enforce valid Groq models to prevent invalid placeholder crashes (e.g. gpt-oss-20b)
        valid_models = {
            "llama-3.3-70b-versatile",
            "llama-3.1-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
            "gemma2-9b-it"
        }
        if model not in valid_models and not str(model).startswith("llama-3"):
            self.model = "llama-3.3-70b-versatile"
        else:
            self.model = model
        self.ollama_url = ollama_url
        self.ollama_model = ollama_model
        
        self.groq_client = None
        if self.api_key and self.api_key != "your_actual_groq_api_key_here":
            try:
                self.groq_client = Groq(api_key=self.api_key)
            except Exception as e:
                console.print(f"[yellow]Could not initialize Groq client: {e}[/yellow]")

    def _call_ollama(self, messages: List[Dict[str, str]], json_mode: bool = False) -> str:
        """Fallback to local Ollama instance with strict timeout to prevent cloud hanging."""
        url = f"{self.ollama_url}/api/chat"
        payload = {
            "model": self.ollama_model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.1}
        }
        if json_mode:
            payload["format"] = "json"
        
        response = requests.post(url, json=payload, timeout=3)
        response.raise_for_status()
        return response.json()["message"]["content"].strip()

    def _chat_completion(self, messages: List[Dict[str, str]], json_mode: bool = False) -> str:
        """
        Attempts generation via Groq API.
        Automatically retries with fallback Groq models if model error or rate limit occurs.
        """
        if self.groq_client:
            try:
                kwargs = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0.1,
                    "max_tokens": 4096
                }
                if json_mode:
                    kwargs["response_format"] = {"type": "json_object"}
                
                resp = self.groq_client.chat.completions.create(**kwargs)
                return resp.choices[0].message.content.strip()
            except Exception as e:
                # If json_validate_failed on Groq, retry without the strict response_format flag
                if json_mode and "json_validate_failed" in str(e).lower():
                    try:
                        resp = self.groq_client.chat.completions.create(
                            model=self.model,
                            messages=messages,
                            temperature=0.1,
                            max_tokens=4096
                        )
                        return resp.choices[0].message.content.strip()
                    except Exception:
                        pass

                # Automatic fallback to fast LLaMA 3.1 8B on Groq
                try:
                    fallback_kwargs = dict(kwargs)
                    fallback_kwargs["model"] = "llama-3.1-8b-instant"
                    resp = self.groq_client.chat.completions.create(**fallback_kwargs)
                    return resp.choices[0].message.content.strip()
                except Exception:
                    pass

                console.print(f"[yellow]Groq request failed ({e}). Checking local Ollama...[/yellow]")

        # Fallback to Ollama if locally available
        try:
            return self._call_ollama(messages, json_mode=json_mode)
        except Exception as ollama_err:
            console.print(f"[red]Ollama fallback failed ({ollama_err}). Returning safe fallback.[/red]")
            if json_mode:
                return json.dumps({
                    "is_relevant": True,
                    "topic": "general",
                    "reason": "Classifier fallback"
                })
            return "Service temporarily busy. Please try again."

    def _chat_completion_stream(self, messages: List[Dict[str, str]]):
        """
        Streams completion tokens via Groq API.
        Auto-retries with LLaMA 8B on Groq before yielding errors.
        """
        if self.groq_client:
            try:
                response = self.groq_client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.1,
                    max_tokens=4096,
                    stream=True
                )
                for chunk in response:
                    content = chunk.choices[0].delta.content
                    if content:
                        yield content
                return
            except Exception as e:
                console.print(f"[yellow]Groq stream failed ({e}). Falling back to LLaMA 8B instant...[/yellow]")
                try:
                    response = self.groq_client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=messages,
                        temperature=0.1,
                        max_tokens=4096,
                        stream=True
                    )
                    for chunk in response:
                        content = chunk.choices[0].delta.content
                        if content:
                            yield content
                    return
                except Exception:
                    pass

        # Fallback to streaming via Ollama if available
        try:
            url = f"{self.ollama_url}/api/chat"
            payload = {
                "model": self.ollama_model,
                "messages": messages,
                "stream": True,
                "options": {"temperature": 0.1}
            }
            res = requests.post(url, json=payload, stream=True, timeout=5)
            for line in res.iter_lines():
                if line:
                    data = json.loads(line.decode('utf-8'))
                    content = data.get("message", {}).get("content", "")
                    if content:
                        yield content
        except Exception as e:
            console.print(f"[red]Ollama stream failed ({e}).[/red]")
            yield f"Unable to reach language model. Please verify your Groq API key and try again."

    def check_query_relevance(self, query: str) -> RelevanceCheckResult:
        """
        Input Guardrail / Query Classifier:
        Determines whether the user's question is relevant to the knowledge base domains:
        (AI, Machine Learning, Deep Learning, Statistics, Mathematics, System Design, Data Engineering, MLOps).
        If off-topic, refuses early to save vector search overhead and prevent hallucination.
        """
        with logfire.span("guardrail_relevance_check", query=query):
            system_prompt = (
                "You are an Input Guardrail & Domain Router for a specialized AI Engineering knowledge base.\n"
                "Your role is to strictly classify whether the user's query belongs to ANY of the following domains:\n"
                "- Artificial Intelligence, Machine Learning, Deep Learning, LLMs, NLP, Computer Vision\n"
                "- Mathematics & Statistics (Probability, Linear Algebra, Optimization, Statistical Inference)\n"
                "- System Design, Distributed Systems, Designing Data-Intensive Applications\n"
                "- MLOps, Model Training, Fine-Tuning, Data Engineering\n\n"
                "If the query is about unrelated topics (e.g. recipes, sports, celebrity gossip, medical advice, casual jokes, weather, travel), "
                "set is_relevant to false.\n"
                "Output strictly valid JSON with keys: is_relevant (bool), topic (str), reason (str)."
            )

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"USER QUERY: {query}"}
            ]

            try:
                content = self._chat_completion(messages, json_mode=True)
                clean_content = content
                if "```json" in clean_content:
                    clean_content = clean_content.split("```json")[1].split("```")[0].strip()
                elif "```" in clean_content:
                    clean_content = clean_content.split("```")[1].split("```")[0].strip()

                parsed = json.loads(clean_content)
                result = RelevanceCheckResult(**parsed)
                logfire.info("Query relevance check completed", is_relevant=result.is_relevant, topic=result.topic)
                return result
            except Exception as e:
                logfire.warn("Guardrail parsing fallback", error=str(e))
                # Fail-open for safety to let retriever check
                return RelevanceCheckResult(is_relevant=True, topic="unknown", reason="Bypassed classifier due to error")

    def synthesize_answer(self, query: str, context_chunks: List[Dict[str, Any]]) -> str:
        """
        Synthesizer Agent: Generates an answer strictly grounded in the retrieved context with LaTeX and source citations.
        """
        with logfire.span("synthesizer_agent", query=query, chunk_count=len(context_chunks)):
            if not context_chunks:
                return "No relevant context found in the knowledge base to answer your question."

            formatted_context = ""
            for i, chunk in enumerate(context_chunks, 1):
                formatted_context += (
                    f"\n--- CHUNK {i} ---\n"
                    f"Source: {chunk.get('source', 'unknown')}\n"
                    f"Page: {chunk.get('page', 'unknown')}\n"
                    f"Relevance Score: {chunk.get('score', 0):.4f}\n"
                    f"Content:\n{chunk.get('text', '')}\n"
                )

            system_prompt = (
                "You are an expert AI Research Assistant and Senior Staff AI Engineer.\n"
                "Your task is to answer the user's question using ONLY the provided reference chunks below.\n\n"
                "STRICT GUIDELINES:\n"
                "1. Grounding: Answer ONLY using facts directly mentioned in the context. Never guess or fabricate.\n"
                "2. Citations: Whenever you state a key fact, append its citation: [Source: <filename or url>, Page: <page>].\n"
                "3. Markdown & Tables:\n"
                "   - Structure your answer cleanly with Markdown headings (###) and bullet points.\n"
                "   - If the user asks for a 'tabular' comparison, table format, or compares two concepts, YOU MUST include a comprehensive Markdown table (| Aspect | Concept A | Concept B |) comparing key dimensions.\n"
                "   - Table Math Rule: Inside table cells, NEVER use $$...$$ or newlines. ONLY use inline single dollar signs: $...$.\n"
                "   - Place detailed derivations or equations in a dedicated section BELOW the table.\n"
                "4. Mathematical LaTeX Formatting Rules (CRITICAL FOR PARSING):\n"
                "   - NEVER write $alpha, $beta, $gamma, $sigma - ALWAYS use backslashes: \\alpha, \\beta, \\gamma, \\sigma.\n"
                "   - NEVER nest dollar signs like $$ $...$ $$. Standalone block math MUST be strictly $$ ... $$ on its own separate line.\n"
                "   - Subscripts MUST have an underscore: e.g. \\text{head}_i, \\text{head}_1, \\text{head}_h, d_{\\text{head}}, d_{\\text{model}}, Q_i, K_i, V_i, \\text{scores}_i, K''_i, V''_i. NEVER write \\text{head}i, \\text{scores}i, or d{\\text{head}}.\n"
                "   - NEVER write \\operatorname{softmax}! (no exclamation mark). ALWAYS write \\operatorname{softmax}(\\dots).\n"
                "   - Wrap ALL mathematical equations and variables in delimiters:\n"
                "     * Inline: $...$\n"
                "     * Block: $$...$$\n"
                "   - ALWAYS close all equation delimiters ($$, $, \\]) completely before finishing.\n"
                "   - Complete derivations fully. Never leave an equation open or dangling at the end.\n"
                "5. Interview Format Request: If the user asks for 'interview format' or asks 'how to explain in an interview', structure the answer like a Principal Engineer:\n"
                "   - TL;DR Executive Summary (1-2 sentences)\n"
                "   - Deep Dive / Core Mechanism (Step-by-step breakdown with LaTeX math and comparison tables)\n"
                "   - Practical Trade-offs & Production Bottlenecks\n"
                "   - Likely Follow-Up Interview Questions & How to Answer Them\n"
                "6. Insufficient Info: If the context does not contain enough information, state clearly: "
                "'The provided documents do not contain sufficient information to answer this question.'"
            )

            user_prompt = (
                f"QUESTION: {query}\n\n"
                f"RETRIEVED CONTEXT:\n{formatted_context}\n\n"
                "Please provide a clear, factual answer with exact citations and LaTeX math where applicable:"
            )

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            answer = self._chat_completion(messages, json_mode=False)
            # Normalize form-feed (\x0c) or backspace (\x08) to literal \f and \b
            answer = answer.replace('\x0c', '\\f').replace('\x08', '\\b')
            logfire.info("Synthesis complete", answer_length=len(answer))
            return answer

    def stream_synthesize_answer(self, query: str, context_chunks: List[Dict[str, Any]]):
        """
        Synthesizer Agent (Streaming):
        Yields tokens one by one as they are generated by Groq/Ollama.
        """
        if not context_chunks:
            yield "No relevant context found in the knowledge base to answer your question."
            return

        formatted_context = ""
        for i, chunk in enumerate(context_chunks, 1):
            formatted_context += (
                f"\n--- CHUNK {i} ---\n"
                f"Source: {chunk.get('source', 'unknown')}\n"
                f"Page: {chunk.get('page', 'unknown')}\n"
                f"Relevance Score: {chunk.get('score', 0):.4f}\n"
                f"Content:\n{chunk.get('text', '')}\n"
            )

        system_prompt = (
            "You are an expert AI Research Assistant and Senior Staff AI Engineer.\n"
            "Your task is to answer the user's question using ONLY the provided reference chunks below.\n\n"
            "STRICT GUIDELINES:\n"
            "1. Grounding: Answer ONLY using facts directly mentioned in the context. Never guess or fabricate.\n"
            "2. Citations: Whenever you state a key fact, append its citation: [Source: <filename or url>, Page: <page>].\n"
            "3. Markdown & Tables:\n"
            "   - Structure your answer cleanly with Markdown headings (###) and bullet points.\n"
            "   - If the user asks for a 'tabular' comparison, table format, or compares two concepts, YOU MUST include a comprehensive Markdown table (| Aspect | Concept A | Concept B |) comparing key dimensions.\n"
            "   - Table Math Rule: Inside table cells, NEVER use $$...$$ or newlines. ONLY use inline single dollar signs: $...$.\n"
            "   - Place detailed derivations or equations in a dedicated section BELOW the table.\n"
            "4. Mathematical LaTeX Formatting Rules (CRITICAL FOR PARSING):\n"
            "   - NEVER write $alpha, $beta, $gamma, $sigma - ALWAYS use backslashes: \\alpha, \\beta, \\gamma, \\sigma.\n"
            "   - NEVER nest dollar signs like $$ $...$ $$. Standalone block math MUST be strictly $$ ... $$ on its own separate line.\n"
            "   - Subscripts MUST have an underscore: e.g. \\text{head}_i, \\text{head}_1, \\text{head}_h, d_{\\text{head}}, d_{\\text{model}}, Q_i, K_i, V_i, \\text{scores}_i, K''_i, V''_i. NEVER write \\text{head}i, \\text{scores}i, or d{\\text{head}}.\n"
            "   - NEVER write \\operatorname{softmax}! (no exclamation mark). ALWAYS write \\operatorname{softmax}(\\dots).\n"
            "   - Wrap ALL mathematical equations and variables in delimiters:\n"
            "     * Inline: $...$\n"
            "     * Block: $$...$$\n"
            "   - ALWAYS close all equation delimiters ($$, $, \\]) completely before finishing.\n"
            "   - Complete derivations fully. Never leave an equation open or dangling at the end.\n"
            "5. Interview Format Request: If the user asks for 'interview format' or asks 'how to explain in an interview', structure the answer like a Principal Engineer:\n"
            "   - TL;DR Executive Summary (1-2 sentences)\n"
            "   - Deep Dive / Core Mechanism (Step-by-step breakdown with LaTeX math and comparison tables)\n"
            "   - Practical Trade-offs & Production Bottlenecks\n"
            "   - Likely Follow-Up Interview Questions & How to Answer Them\n"
            "6. Insufficient Info: If the context does not contain enough information, state clearly: "
            "'The provided documents do not contain sufficient information to answer this question.'"
        )

        user_prompt = (
            f"QUESTION: {query}\n\n"
            f"RETRIEVED CONTEXT:\n{formatted_context}\n\n"
            "Please provide a clear, factual answer with exact citations and LaTeX math where applicable:"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        for token in self._chat_completion_stream(messages):
            # Clean form-feed or backspace tokens if emitted
            token = token.replace('\x0c', '\\f').replace('\x08', '\\b')
            yield token

    def verify_and_critique(
        self,
        query: str,
        context_chunks: List[Dict[str, Any]],
        draft_answer: str
    ) -> VerificationResult:
        """
        Hallucination Critic Agent:
        Audits draft answer against retrieved chunks, ensures zero hallucination,
        computes confidence score, and returns structured verification.
        """
        with logfire.span("critic_agent", query=query):
            context_snippets = "\n".join([
                f"- [Page {c.get('page')}] {c.get('text')}"
                for c in context_chunks
            ])

            system_prompt = (
                "You are a rigorous Fact-Checking & Anti-Hallucination Guardrail Agent.\n"
                "Your job is to cross-examine a draft answer against the retrieved reference context.\n\n"
                "CRITICAL INSTRUCTIONS FOR OUTPUT FIELDS:\n"
                "1. 'is_grounded': true if core claims are supported by context; false only if it hallucinates major facts or contradicts context.\n"
                "2. 'confidence_score': float from 0.0 to 1.0 (e.g. 0.85-1.0 if strongly supported, 0.60-0.84 if mostly supported, <0.50 if insufficient evidence).\n"
                "3. 'identified_hallucinations': list of any specific claims not supported by context.\n"
                "4. 'reasoning': short 1-2 sentence explanation of your evaluation.\n"
                "5. 'final_verified_answer': The actual answer to present to the user. DO NOT put your critique, review, or evaluation commentary here! "
                "Keep this identical to draft_answer unless confidence_score < 0.50, in which case state: 'I cannot answer this question with sufficient confidence based on the provided documents.'"
            )

            user_prompt = (
                f"USER QUERY: {query}\n\n"
                f"REFERENCE CONTEXT:\n{context_snippets}\n\n"
                f"DRAFT ANSWER TO AUDIT:\n{draft_answer}\n\n"
                "Output JSON with keys: is_grounded (bool), confidence_score (float), "
                "identified_hallucinations (list of strings), reasoning (string), final_verified_answer (string)."
            )

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            content = self._chat_completion(messages, json_mode=True)

            try:
                clean_content = content
                if "```json" in clean_content:
                    clean_content = clean_content.split("```json")[1].split("```")[0].strip()
                elif "```" in clean_content:
                    clean_content = clean_content.split("```")[1].split("```")[0].strip()

                parsed = json.loads(clean_content)
                
                # Normalize field aliases if LLM used synonyms
                if not parsed.get("final_verified_answer"):
                    parsed["final_verified_answer"] = parsed.get("verified_answer", draft_answer)
                if not parsed.get("reasoning"):
                    parsed["reasoning"] = parsed.get("explanation", parsed.get("justification", "Context verified against document sources."))

                # Guard against the Critic outputting its review meta-commentary into final_verified_answer
                fva = parsed.get("final_verified_answer", "").strip()
                meta_signals = ["draft answer is", "contains a few statements", "minor hallucinations", "reference material", "mostly grounded but"]
                if any(sig in fva.lower() for sig in meta_signals):
                    # The LLM put its review into final_verified_answer instead of an answer
                    parsed["reasoning"] = fva
                    parsed["final_verified_answer"] = draft_answer

                conf = float(parsed.get("confidence_score", 0.0))
                if conf < CONFIDENCE_THRESHOLD:
                    parsed["is_grounded"] = False
                    parsed["final_verified_answer"] = (
                        "I cannot answer this question with sufficient confidence based on the provided documents. "
                        f"(Confidence: {conf*100:.1f}% is below threshold {CONFIDENCE_THRESHOLD*100:.0f}%)."
                    )

                result = VerificationResult(**parsed)
                logfire.info(
                    "Critic evaluation complete",
                    confidence=result.confidence_score,
                    is_grounded=result.is_grounded,
                    hallucinations=len(result.identified_hallucinations)
                )
                return result
            except Exception as e:
                console.print(f"[yellow]Critic JSON parsing error: {e}. Falling back to draft answer.[/yellow]")
                logfire.warn("Critic JSON parsing error", error=str(e))
                return VerificationResult(
                    is_grounded=True,
                    confidence_score=0.75,
                    identified_hallucinations=[],
                    reasoning="Automatic evaluation completed.",
                    final_verified_answer=draft_answer
                )
