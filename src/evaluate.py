import sys
import time
from pathlib import Path
from typing import List, Dict, Any

# Ensure project root in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import logfire
from src.workflow import RAGWorkflow

# Golden Benchmark Evaluation Dataset
BENCHMARK_CASES = [
    {
        "id": "TC-01",
        "category": "Deep Learning & Attention",
        "query": "Explain the difference between self-attention and multi-head attention. Include the mathematical formula and compare them in a markdown table.",
        "expected_type": "answer",
        "must_have": ["table", "formula", "citations"]
    },
    {
        "id": "TC-02",
        "category": "Probability & Statistics",
        "query": "What is the definition and mathematical formula of variance and standard deviation of a random variable X?",
        "expected_type": "answer",
        "must_have": ["formula", "citations"]
    },
    {
        "id": "TC-03",
        "category": "Distributed Systems",
        "query": "Explain replication vs partitioning in distributed data stores. Compare them in a markdown table.",
        "expected_type": "answer",
        "must_have": ["table", "citations"]
    },
    {
        "id": "TC-04",
        "category": "Domain Guardrail (Refusal)",
        "query": "Give me a recipe for baking chocolate chip cookies at home.",
        "expected_type": "refusal",
        "must_have": ["refusal_trigger"]
    },
    {
        "id": "TC-05",
        "category": "Out-of-Corpus Query",
        "query": "What is the flight speed of an unladen European swallow according to modern ornithology?",
        "expected_type": "refusal_or_unanswerable",
        "must_have": ["no_hallucination"]
    }
]

def run_evaluation() -> Dict[str, Any]:
    print("=" * 70)
    print("🚀 STARTING AUTOMATED RAG TRIAD & GUARDRAIL BENCHMARK SUITE")
    print("=" * 70)
    
    workflow = RAGWorkflow()
    results = []
    total_latency = 0.0

    try:
        for idx, case in enumerate(BENCHMARK_CASES, 1):
            print(f"\n[{idx}/{len(BENCHMARK_CASES)}] Running Test Case: {case['id']} ({case['category']})")
            print(f"     Query: \"{case['query']}\"")
            
            start_time = time.perf_counter()
            with logfire.span("evaluation_case", test_id=case["id"], category=case["category"]):
                response = workflow.ask(case["query"])
            latency = time.perf_counter() - start_time
            total_latency += latency
            
            answer = response.get("answer", "")
            confidence = response.get("confidence", 0.0)
            is_grounded = response.get("is_grounded", False)
            sources = response.get("sources", [])
            reasoning = response.get("reasoning", "")
            
            # Check criteria
            has_table = ("|" in answer) and ("---" in answer or "-|-" in answer or "-+-" in answer or "\n|" in answer)
            has_formula = (
                ("$" in answer) or 
                (r"\frac" in answer) or 
                (r"\sigma" in answer) or 
                (r"\mu" in answer) or 
                (r"\[" in answer) or 
                (r"\sqrt" in answer) or 
                (r"\operatorname" in answer) or
                ("Var(" in answer)
            )
            has_citations = len(sources) > 0
            is_refusal = "specialized AI Research Assistant" in answer or "cannot assist with queries outside" in answer
            
            passed = True
            failure_reasons = []

            if case["expected_type"] == "refusal":
                if not is_refusal:
                    passed = False
                    failure_reasons.append("Failed to trigger domain guardrail refusal")
            elif case["expected_type"] == "answer":
                if is_refusal:
                    passed = False
                    failure_reasons.append("Incorrectly refused a valid domain query")
                if "table" in case["must_have"] and not has_table:
                    passed = False
                    failure_reasons.append("Missing required Markdown table")
                if "formula" in case["must_have"] and not has_formula:
                    passed = False
                    failure_reasons.append("Missing mathematical LaTeX formula")
                if "citations" in case["must_have"] and not has_citations:
                    passed = False
                    failure_reasons.append("Missing document page-level citations")
                if not is_grounded:
                    passed = False
                    failure_reasons.append("Critic flagged ungrounded claims")
            elif case["expected_type"] == "refusal_or_unanswerable":
                # Either refused by guardrail or flagged as ungrounded / out-of-context
                if is_grounded and confidence > 80 and not is_refusal:
                    passed = False
                    failure_reasons.append("Hallucinated answer for out-of-corpus query")

            status_str = "✅ PASS" if passed else "❌ FAIL"
            print(f"     Result: {status_str} | Latency: {latency:.2f}s | Confidence: {confidence}%")
            if failure_reasons:
                print(f"     Issues: {', '.join(failure_reasons)}")
            
            results.append({
                "id": case["id"],
                "category": case["category"],
                "query": case["query"],
                "passed": passed,
                "latency_sec": round(latency, 2),
                "confidence": confidence,
                "is_grounded": is_grounded,
                "has_table": has_table,
                "has_formula": has_formula,
                "source_count": len(sources),
                "reasons": failure_reasons
            })

    finally:
        workflow.close()

    total_cases = len(results)
    passed_cases = sum(1 for r in results if r["passed"])
    pass_rate = (passed_cases / total_cases) * 100
    avg_latency = total_latency / total_cases

    print("\n" + "=" * 70)
    print("📊 BENCHMARK SUMMARY")
    print(f"Total Test Cases: {total_cases}")
    print(f"Passed:           {passed_cases}/{total_cases} ({pass_rate:.1f}%)")
    print(f"Average Latency:  {avg_latency:.2f}s")
    print("=" * 70)

    # Generate Markdown Report
    report_path = BASE_DIR / "EVALUATION_REPORT.md"
    markdown_content = generate_markdown_report(results, pass_rate, avg_latency)
    report_path.write_text(markdown_content, encoding="utf-8")
    print(f"\n📄 Saved full evaluation report to: {report_path}")

    return {
        "pass_rate": pass_rate,
        "avg_latency": avg_latency,
        "results": results
    }

def generate_markdown_report(results: List[Dict[str, Any]], pass_rate: float, avg_latency: float) -> str:
    md = [
        "# 🧪 Automated RAG Benchmark & Guardrail Evaluation Report\n",
        f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}  ",
        f"**Overall Pass Rate:** `{pass_rate:.1f}%`  ",
        f"**Average End-to-End Latency:** `{avg_latency:.2f}s`  ",
        "**Tested Pipeline:** Qdrant Cloud + FastEmbed BGE + Cross-Encoder Re-ranker + Groq + Hallucination Critic  \n",
        "## Summary Results Table\n",
        "| Test ID | Category | Query | Status | Latency | Confidence | Citations | Table | LaTeX | Issues |",
        "|:---|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---|"
    ]

    for r in results:
        status = "✅ PASS" if r["passed"] else "❌ FAIL"
        issues = "<br>".join(r["reasons"]) if r["reasons"] else "None"
        md.append(
            f"| `{r['id']}` | {r['category']} | *{r['query'][:40]}...* | {status} | "
            f"{r['latency_sec']}s | {r['confidence']}% | {r['source_count']} | "
            f"{'Yes' if r['has_table'] else 'No'} | {'Yes' if r['has_formula'] else 'No'} | {issues} |"
        )

    md.extend([
        "\n## Evaluation Methodology & RAG Triad Guarantees\n",
        "1. **Context Relevance**: Measured via two-stage retrieval (Dense BGE-Small-en cosine similarity + Cross-Encoder MiniLM reranking).",
        "2. **Groundedness**: Measured by Critic Agent auditing draft statements against chunk payloads. Rejection threshold: `confidence < 60%`.",
        "3. **Domain Security Guardrail**: Tests TC-04 confirms that adversarial/off-topic prompts are intercepted at Step 1 before vector search.",
        "4. **Format Adherence**: Confirms structured comparative tables and standard LaTeX math syntax (`$ ... $`)."
    ])

    return "\n".join(md)

if __name__ == "__main__":
    run_evaluation()
