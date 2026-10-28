from typing import List, Dict, Any, Optional
import logfire
from rich.console import Console
from fastembed import TextEmbedding
from fastembed.rerank.cross_encoder import TextCrossEncoder
from qdrant_client import QdrantClient
from qdrant_client.http import models

from src.config import (
    QDRANT_URL,
    QDRANT_API_KEY,
    QDRANT_COLLECTION,
    STORAGE_DIR,
    TOP_K_CHUNKS
)

console = Console()

class VectorStore:
    def __init__(self, collection_name: str = QDRANT_COLLECTION):
        self.collection_name = collection_name
        self.embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        self.reranker = TextCrossEncoder(model_name="Xenova/ms-marco-MiniLM-L-6-v2")
        self.vector_size = 384
        self.client = self._init_client()
        self._ensure_collection()

    def _init_client(self) -> QdrantClient:
        """
        1. Checks for Qdrant Cloud (if QDRANT_API_KEY is provided or URL is HTTPS)
        2. Checks for local Docker Qdrant (http://localhost:6333)
        3. Falls back to embedded local disk storage in ./qdrant_storage
        """
        if QDRANT_API_KEY or "qdrant.tech" in QDRANT_URL or QDRANT_URL.startswith("https://"):
            try:
                # 60s timeout to handle overseas AWS roundtrips smoothly
                client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY or None, timeout=60.0, check_compatibility=False)
                client.get_collections()
                console.print(f"[bold green]Connected to Qdrant Cloud at[/bold green] {QDRANT_URL}")
                return client
            except Exception as e:
                console.print(f"[yellow]Could not connect to Qdrant Cloud: {e}. Falling back to local storage.[/yellow]")

        try:
            client = QdrantClient(url=QDRANT_URL, timeout=1.5, check_compatibility=False)
            client.get_collections()
            console.print(f"[green]Connected to local Qdrant server at[/green] {QDRANT_URL}")
            return client
        except Exception:
            console.print(f"[yellow]Qdrant server not reachable at {QDRANT_URL}. Using embedded local storage at {STORAGE_DIR}[/yellow]")
            return QdrantClient(path=str(STORAGE_DIR))

    def _ensure_collection(self):
        """Ensure collection exists in Qdrant with cosine distance."""
        collections = [c.name for c in self.client.get_collections().collections]
        if self.collection_name not in collections:
            console.print(f"[cyan]Creating collection:[/cyan] '{self.collection_name}' (vector size {self.vector_size})")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=self.vector_size,
                    distance=models.Distance.COSINE
                )
            )

    def add_chunks(self, chunks: List[Dict[str, Any]]) -> int:
        """
        Computes embeddings locally and upserts chunks with metadata into Qdrant.
        """
        if not chunks:
            return 0

        console.print(f"[cyan]Generating embeddings for {len(chunks)} chunks...[/cyan]")
        texts = [c["text"] for c in chunks]
        embeddings = list(self.embedding_model.embed(texts))

        points = []
        for chunk, vector in zip(chunks, embeddings):
            points.append(
                models.PointStruct(
                    id=chunk["id"],
                    vector=vector.tolist(),
                    payload={
                        "text": chunk["text"],
                        "source": chunk["metadata"].get("source", "unknown"),
                        "filename": chunk["metadata"].get("filename", "unknown"),
                        "page": chunk["metadata"].get("page", 1),
                        "chunk_index": chunk["metadata"].get("chunk_index", 0)
                    }
                )
            )

        # Batch upsert into Qdrant Cloud in chunks with auto-retry
        import time
        batch_size = 150
        total_batches = (len(points) + batch_size - 1) // batch_size
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            for attempt in range(3):
                try:
                    self.client.upsert(
                        collection_name=self.collection_name,
                        points=batch
                    )
                    break
                except Exception as e:
                    if attempt == 2:
                        console.print(f"[red]Failed batch after 3 attempts: {e}[/red]")
                        raise e
                    time.sleep(2 * (attempt + 1))
            console.print(f"[dim]Uploaded batch {i//batch_size + 1}/{total_batches} ({len(batch)} points)...[/dim]")

        console.print(f"[bold green]Successfully saved {len(points)} chunks into Qdrant Cloud collection '{self.collection_name}'![/bold green]")
        return len(points)

    def search(self, query: str, top_k: int = TOP_K_CHUNKS, candidate_pool: int = 16) -> List[Dict[str, Any]]:
        """
        Two-Stage Production Retrieval:
        1. Fast Bi-Encoder Retrieval: Fetch candidate_pool (e.g. 16) candidates from Qdrant Cloud.
        2. Cross-Encoder Re-Ranking: Score (Query, Chunk) joint attention with local ms-marco-MiniLM.
        3. Sort by re-rank score and return top_k highest-signal chunks.
        """
        with logfire.span("vector_retrieval_and_rerank", query=query, target_top_k=top_k):
            query_embedding = list(self.embedding_model.embed([query]))[0].tolist()
            
            # Fetch a larger candidate pool from Qdrant
            candidate_limit = max(top_k * 4, candidate_pool)
            search_results = self.client.query_points(
                collection_name=self.collection_name,
                query=query_embedding,
                limit=candidate_limit,
                with_payload=True
            ).points

            if not search_results:
                return []

            candidates = []
            for hit in search_results:
                candidates.append({
                    "vector_score": round(hit.score, 4),
                    "text": hit.payload.get("text", ""),
                    "source": hit.payload.get("source", "unknown"),
                    "filename": hit.payload.get("filename", "unknown"),
                    "page": hit.payload.get("page", 1),
                    "chunk_index": hit.payload.get("chunk_index", 0)
                })

            # Stage 2: Cross-Encoder Re-Ranking
            try:
                candidate_texts = [c["text"] for c in candidates]
                with logfire.span("cross_encoder_scoring", candidate_count=len(candidate_texts)):
                    rerank_scores = list(self.reranker.rerank(query, candidate_texts))

                for c, r_score in zip(candidates, rerank_scores):
                    c["score"] = round(float(r_score), 4)

                # Sort by reranker score descending
                candidates.sort(key=lambda x: x["score"], reverse=True)
                top_results = candidates[:top_k]
                logfire.info("Re-ranking complete", returned_chunks=len(top_results), top_score=top_results[0]["score"])
                return top_results
            except Exception as e:
                console.print(f"[yellow]Re-ranking fallback to vector score: {e}[/yellow]")
                for c in candidates:
                    c["score"] = c["vector_score"]
                return candidates[:top_k]

    def close(self):
        """Explicitly closes client to release file locks cleanly."""
        try:
            self.client.close()
        except Exception:
            pass
