from pathlib import Path
from typing import Dict, Any, List
import logfire
from rich.console import Console

from src.ingestion import extract_and_chunk_pdf
from src.vector_store import VectorStore
from src.agents import RAGAgents, VerificationResult

console = Console()

class RAGWorkflow:
    def __init__(self):
        self.vector_store = VectorStore()
        self.agents = RAGAgents()

    def ingest_document(self, source: str) -> int:
        """
        Ingests a PDF from either a web URL or a local file path.
        """
        with logfire.span("ingest_document", source=source):
            console.rule("[bold cyan]Step 1: Ingesting Knowledge Base Document[/bold cyan]")
            chunks = extract_and_chunk_pdf(source)
            if not chunks:
                console.print("[red]No text could be extracted from the document.[/red]")
                return 0
            
            console.rule("[bold cyan]Step 2: Storing Vectors & Metadata in Qdrant[/bold cyan]")
            count = self.vector_store.add_chunks(chunks)
            logfire.info("Document ingested successfully", source=source, total_chunks=count)
            return count

    def ingest_directory(self, dir_path: str) -> int:
        """
        Scans a directory for all .pdf files and ingests them sequentially into Qdrant.
        """
        with logfire.span("ingest_directory", directory=dir_path):
            p = Path(dir_path)
            if not p.exists() or not p.is_dir():
                raise FileNotFoundError(f"Directory not found: {dir_path}")

            pdf_files = list(p.glob("*.pdf"))
            if not pdf_files:
                console.print(f"[yellow]No PDF files found in {dir_path}[/yellow]")
                return 0

            console.print(f"[bold cyan]Found {len(pdf_files)} PDF books/documents to ingest in {dir_path}[/bold cyan]")
            total_chunks = 0
            for i, pdf_file in enumerate(pdf_files, 1):
                console.rule(f"[bold yellow]Document [{i}/{len(pdf_files)}]: {pdf_file.name}[/bold yellow]")
                try:
                    chunks = extract_and_chunk_pdf(str(pdf_file))
                    if chunks:
                        added = self.vector_store.add_chunks(chunks)
                        total_chunks += added
                except Exception as e:
                    console.print(f"[red]Error ingesting {pdf_file.name}: {e}. Skipping to next.[/red]")

            console.print(f"\n[bold green]Ingestion complete! Total {total_chunks} chunks stored across {len(pdf_files)} documents.[/bold green]")
            logfire.info("Directory ingestion complete", total_files=len(pdf_files), total_chunks=total_chunks)
            return total_chunks

    def ask(self, query: str) -> Dict[str, Any]:
        """
        Executes the multi-agent production RAG workflow:
        1. Domain Relevance Guardrail: Rejects off-topic inquiries early
        2. Retrieval: Qdrant semantic cosine search
        3. Synthesis: Groq/Ollama LLM draft with citations & LaTeX
        4. Fact-checking & Confidence Evaluation: Critic Guardrail Agent
        """
        with logfire.span("rag_ask_workflow", query=query):
            console.rule(f"[bold cyan]Query: {query}[/bold cyan]")

            # 1. Domain Relevance Guardrail
            console.print("[dim]Guardrail: Checking query domain relevance...[/dim]")
            relevance = self.agents.check_query_relevance(query)
            if not relevance.is_relevant:
                console.print(f"[bold yellow]Guardrail Refusal: Query off-topic ({relevance.topic})[/bold yellow]")
                refusal_msg = (
                    "I am a specialized AI Research Assistant focused exclusively on **Machine Learning, "
                    "Deep Learning, Statistics, LLMs, and System Design**.\n\n"
                    f"I cannot assist with queries outside these domains (*{relevance.reason}*).\n\n"
                    "**I can, however, help you with:**\n"
                    "- Large Language Model architectures, fine-tuning, and pre-training\n"
                    "- Designing data-intensive applications and distributed system architectures\n"
                    "- Mathematical statistics, probability theory, and ML derivations\n"
                    "- Production MLOps pipelines and technical interview preparation"
                )
                return {
                    "answer": refusal_msg,
                    "confidence": 0.0,
                    "is_grounded": False,
                    "reasoning": f"Refused by Domain Relevance Guardrail. Topic: {relevance.topic}.",
                    "sources": []
                }

            # 2. Retrieval
            console.print("[dim]Retriever: Searching Qdrant Cloud vector database...[/dim]")
            retrieved_chunks = self.vector_store.search(query)
            if not retrieved_chunks:
                return {
                    "answer": "No relevant documents found in the vector database to answer this question.",
                    "confidence": 0.0,
                    "is_grounded": False,
                    "reasoning": "Knowledge base empty or no matching chunks found.",
                    "sources": []
                }

            # 3. Synthesis
            console.print("[dim]Synthesizer: Drafting answer strictly from context with LaTeX math...[/dim]")
            draft_answer = self.agents.synthesize_answer(query, retrieved_chunks)

            # 4. Verification & Critic
            console.print("[dim]Critic: Fact-checking claims and computing confidence score...[/dim]")
            verification: VerificationResult = self.agents.verify_and_critique(
                query=query,
                context_chunks=retrieved_chunks,
                draft_answer=draft_answer
            )

            # Collect unique sources
            unique_sources = []
            seen = set()
            for c in retrieved_chunks:
                key = (c.get("source"), c.get("page"))
                if key not in seen:
                    seen.add(key)
                    unique_sources.append({
                        "source": c.get("source"),
                        "filename": c.get("filename"),
                        "page": c.get("page"),
                        "score": round(c.get("score", 0), 4)
                    })

            # If confidence is adequate (>= 0.50), preserve the rich draft answer with all tables and math!
            # Only fall back to insufficient context message if confidence is low (< 0.50)
            if verification.confidence_score >= 0.50:
                final_answer = draft_answer
            else:
                final_answer = verification.final_verified_answer

            return {
                "answer": final_answer,
                "confidence": round(verification.confidence_score * 100, 1),
                "is_grounded": verification.is_grounded,
                "hallucinations_detected": verification.identified_hallucinations,
                "reasoning": verification.reasoning,
                "sources": unique_sources
            }

    def stream_ask(self, query: str):
        """
        Streaming Generator for SSE (Server-Sent Events):
        Yields JSON events:
          - {"type": "status", "message": "..."}
          - {"type": "token", "token": "..."}
          - {"type": "refusal", "message": "..."}
          - {"type": "verification", "confidence": ..., "is_grounded": ..., "sources": [...]}
        """
        import json
        logfire.info("rag_stream_workflow_start", query=query)
        # 1. Domain Relevance Guardrail
        yield json.dumps({"type": "status", "message": "Checking query domain relevance..."}) + "\n"
        relevance = self.agents.check_query_relevance(query)
        if not relevance.is_relevant:
            refusal_msg = (
                "I am a specialized AI Research Assistant focused exclusively on **Machine Learning, "
                "Deep Learning, Statistics, LLMs, and System Design**.\n\n"
                f"I cannot assist with queries outside these domains (*{relevance.reason}*).\n\n"
                "**I can, however, help you with:**\n"
                "- Large Language Model architectures, fine-tuning, and pre-training\n"
                "- Designing data-intensive applications and distributed system architectures\n"
                "- Mathematical statistics, probability theory, and ML derivations\n"
                "- Production MLOps pipelines and technical interview preparation"
            )
            logfire.info("rag_stream_workflow_refusal", query=query, reason=relevance.reason)
            yield json.dumps({"type": "refusal", "message": refusal_msg}) + "\n"
            return

        # 2. Retrieval & Re-ranking
        yield json.dumps({"type": "status", "message": "Searching Qdrant & re-ranking with Cross-Encoder..."}) + "\n"
        retrieved_chunks = self.vector_store.search(query)
        if not retrieved_chunks:
            logfire.info("rag_stream_workflow_empty", query=query)
            yield json.dumps({"type": "empty", "message": "No relevant documents found in the vector database to answer this question."}) + "\n"
            return

        # 3. Stream Synthesis
        yield json.dumps({"type": "status", "message": "Synthesizing answer..."}) + "\n"
        full_draft = []
        for token in self.agents.stream_synthesize_answer(query, retrieved_chunks):
            full_draft.append(token)
            yield json.dumps({"type": "token", "token": token}) + "\n"

        draft_answer = "".join(full_draft)

        # 4. Critic Fact-Checking
        yield json.dumps({"type": "status", "message": "Critic verifying claims and computing confidence..."}) + "\n"
        verification: VerificationResult = self.agents.verify_and_critique(
            query=query,
            context_chunks=retrieved_chunks,
            draft_answer=draft_answer
        )

        # Only replace the streamed draft answer if confidence is too low (< 0.50)
        if verification.confidence_score < 0.50:
            yield json.dumps({"type": "replace_answer", "answer": verification.final_verified_answer}) + "\n"

        # Collect unique sources
        unique_sources = []
        seen = set()
        for c in retrieved_chunks:
            key = (c.get("source"), c.get("page"))
            if key not in seen:
                seen.add(key)
                unique_sources.append({
                    "source": c.get("source"),
                    "filename": c.get("filename"),
                    "page": c.get("page"),
                    "score": round(c.get("score", 0), 4)
                })

        # Emit final verification event
        logfire.info(
            "rag_stream_workflow_complete",
            query=query,
            confidence=verification.confidence_score,
            is_grounded=verification.is_grounded
        )
        yield json.dumps({
            "type": "verification",
            "confidence": round(verification.confidence_score * 100, 1),
            "is_grounded": verification.is_grounded,
            "reasoning": verification.reasoning,
            "sources": unique_sources
        }) + "\n"

    def close(self):
        self.vector_store.close()
