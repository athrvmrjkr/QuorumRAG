import os
import re
import uuid
from pathlib import Path
from typing import List, Dict, Any
from urllib.parse import urlparse
import requests
from pypdf import PdfReader
from rich.console import Console

from src.config import DATA_DIR, PDF_CHUNK_SIZE, PDF_CHUNK_OVERLAP

console = Console()

def is_valid_url(url: str) -> bool:
    """Check if the given string is a valid HTTP/HTTPS URL."""
    try:
        result = urlparse(url)
        return all([result.scheme in ("http", "https"), result.netloc])
    except Exception:
        return False

def download_pdf_from_url(url: str) -> Path:
    """
    Downloads a PDF file from a web URL and saves it into the data/ directory.
    """
    console.print(f"[cyan]Downloading PDF from URL:[/cyan] {url}")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    response = requests.get(url, headers=headers, stream=True, timeout=30)
    response.raise_for_status()

    # Determine filename from URL or header
    parsed = urlparse(url)
    filename = os.path.basename(parsed.path)
    if not filename.endswith(".pdf"):
        filename = f"doc_{uuid.uuid4().hex[:8]}.pdf"
    
    # Sanitize filename
    filename = re.sub(r'[^a-zA-Z0-9_\.-]', '_', filename)
    target_path = DATA_DIR / filename

    with open(target_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

    console.print(f"[green]Successfully saved to:[/green] {target_path}")
    return target_path

def chunk_text(text: str, chunk_size: int = PDF_CHUNK_SIZE, chunk_overlap: int = PDF_CHUNK_OVERLAP) -> List[str]:
    """
    Splits text into chunks of specified size with overlap.
    """
    if not text:
        return []
    
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - chunk_overlap
        
    return chunks

def extract_and_chunk_pdf(source: str) -> List[Dict[str, Any]]:
    """
    Accepts either a URL or a local file path.
    Extracts text per page, chunks it, and attaches page number and source metadata.
    """
    if is_valid_url(source):
        file_path = download_pdf_from_url(source)
        source_identifier = source
    else:
        file_path = Path(source)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {source}")
        source_identifier = file_path.name

    console.print(f"[cyan]Extracting text from:[/cyan] {file_path.name}")
    reader = PdfReader(str(file_path))
    total_pages = len(reader.pages)
    console.print(f"[dim]Total pages found: {total_pages}[/dim]")

    all_chunks = []
    chunk_counter = 0

    for page_idx, page in enumerate(reader.pages):
        page_num = page_idx + 1
        page_text = page.extract_text() or ""
        page_text = page_text.strip()
        
        if not page_text:
            continue

        page_chunks = chunk_text(page_text)
        for chunk in page_chunks:
            chunk_counter += 1
            all_chunks.append({
                "id": str(uuid.uuid4()),
                "text": chunk,
                "metadata": {
                    "source": source_identifier,
                    "filename": file_path.name,
                    "page": page_num,
                    "chunk_index": chunk_counter
                }
            })

    console.print(f"[green]Extracted {len(all_chunks)} chunks from {total_pages} pages.[/green]")
    return all_chunks
