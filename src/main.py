import sys
from pathlib import Path

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Enforce UTF-8 encoding in Windows terminal to support Unicode math & hyphens
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

import argparse
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt

from src.workflow import RAGWorkflow

console = Console()

def display_result(result: dict):
    confidence = result.get("confidence", 0.0)
    is_grounded = result.get("is_grounded", False)
    
    # Confidence color badge
    if confidence >= 80:
        conf_color = "bold green"
    elif confidence >= 60:
        conf_color = "bold yellow"
    else:
        conf_color = "bold red"

    # Main answer panel
    console.print()
    console.print(Panel(
        result.get("answer", ""),
        title="[bold green]AI Assistant Answer[/bold green]",
        subtitle=f"[{conf_color}]Confidence: {confidence}%[/] | Grounded: {'[green]Yes[/green]' if is_grounded else '[red]No[/red]'}",
        border_style="green"
    ))

    # Reasoning / Critic notes
    if result.get("reasoning"):
        console.print(f"[dim]Critic Reasoning: {result['reasoning']}[/dim]")

    # Hallucinations warning if any
    hallucinations = result.get("hallucinations_detected", [])
    if hallucinations:
        console.print(Panel(
            "\n".join([f"- {h}" for h in hallucinations]),
            title="[bold red]Filtered Claims / Hallucination Warnings[/bold red]",
            border_style="red"
        ))

    # Sources table
    sources = result.get("sources", [])
    if sources:
        table = Table(title="Sources & Citations", show_header=True, header_style="bold magenta")
        table.add_column("Document / Source", style="dim", max_width=50, overflow="fold")
        table.add_column("Page", justify="center")
        table.add_column("Similarity Score", justify="right")

        for s in sources:
            src_text = s.get("source") or s.get("filename") or "unknown"
            table.add_row(
                str(src_text),
                str(s.get("page", "-")),
                f"{s.get('score', 0):.4f}"
            )
        console.print(table)
    console.print()

def interactive_mode(workflow: RAGWorkflow):
    console.print(Panel(
        "[bold cyan]Multi-Agent RAG Assistant[/bold cyan]\n"
        "[dim]Featuring Qdrant Vector DB, FastEmbed Local Embeddings & Groq Multi-Agent Validation[/dim]",
        border_style="cyan"
    ))

    while True:
        console.print("\n[bold]Main Menu:[/bold]")
        console.print("1. [cyan]Ingest Single PDF (URL or Local File)[/cyan]")
        console.print("2. [cyan]Ingest All PDFs in data/ folder[/cyan]")
        console.print("3. [cyan]Ask a Question (RAG with Confidence & Sources)[/cyan]")
        console.print("4. [cyan]Exit[/cyan]")

        choice = Prompt.ask("Select an option", choices=["1", "2", "3", "4"], default="3")

        if choice == "1":
            source = Prompt.ask("\nEnter PDF URL (e.g., https://.../paper.pdf) or local file path")
            if source.strip():
                try:
                    workflow.ingest_document(source.strip())
                except Exception as e:
                    console.print(f"[bold red]Ingestion error:[/bold red] {e}")
        elif choice == "2":
            try:
                workflow.ingest_directory("data")
            except Exception as e:
                console.print(f"[bold red]Directory ingestion error:[/bold red] {e}")
        elif choice == "3":
            query = Prompt.ask("\nEnter your doubt/question")
            if query.strip():
                try:
                    result = workflow.ask(query.strip())
                    display_result(result)
                except Exception as e:
                    console.print(f"[bold red]Query error:[/bold red] {e}")
        elif choice == "4":
            console.print("[dim]Goodbye![/dim]")
            break

def main():
    parser = argparse.ArgumentParser(description="Multi-Agent RAG with Vector Database")
    parser.add_argument("--ingest", type=str, help="URL or path to single PDF file to ingest")
    parser.add_argument("--ingest-dir", type=str, help="Path to directory containing PDF files to ingest")
    parser.add_argument("--ask", type=str, help="Question to ask the RAG agent")
    args = parser.parse_args()

    workflow = RAGWorkflow()
    try:
        if args.ingest:
            workflow.ingest_document(args.ingest)
        elif args.ingest_dir:
            workflow.ingest_directory(args.ingest_dir)
        elif args.ask:
            result = workflow.ask(args.ask)
            display_result(result)
        else:
            interactive_mode(workflow)
    finally:
        workflow.close()

if __name__ == "__main__":
    main()
