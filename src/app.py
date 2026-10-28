import sys
from pathlib import Path

# Ensure root in path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# pyrefly: ignore[missing-import]
from fastapi import FastAPI, HTTPException
# pyrefly: ignore[missing-import]
from fastapi.responses import HTMLResponse, StreamingResponse
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
# pyrefly: ignore[missing-import]
import logfire
from src.workflow import RAGWorkflow
from src.ui_template import HTML_TEMPLATE

app = FastAPI(
    title="Ruixen AI — Multi-Agent RAG Assistant",
    description="Interactive 3D Spline background, Ruixen Moon Chat UI, and zero-hallucination multi-agent RAG",
    version="1.2.0"
)

# Instrument FastAPI with Logfire
logfire.instrument_fastapi(app)

# Initialize workflow once at startup
rag_workflow = RAGWorkflow()

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000, description="User question")
    history: Optional[List[Dict[str, str]]] = Field(default_factory=list)

class SourceCitation(BaseModel):
    source: str
    page: Any
    score: float

class ChatResponse(BaseModel):
    answer: str
    confidence: float
    is_grounded: bool
    reasoning: str
    sources: List[SourceCitation]

@app.get("/", response_class=HTMLResponse)
async def serve_chat_ui():
    """Serves the secure, Ruixen Moon Chat interface with Spline 3D background."""
    return HTMLResponse(content=HTML_TEMPLATE)

@app.post("/api/chat", response_model=ChatResponse)
async def api_chat(req: ChatRequest):
    """
    Public API: Read-only RAG (synchronous).
    Takes user question, runs multi-agent retrieval & verification,
    and returns answer + confidence + citations.
    """
    try:
        result = rag_workflow.ask(req.message)
        return ChatResponse(
            answer=result.get("answer", ""),
            confidence=result.get("confidence", 0.0),
            is_grounded=result.get("is_grounded", False),
            reasoning=result.get("reasoning", ""),
            sources=result.get("sources", [])
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/stream")
async def api_chat_stream(req: ChatRequest):
    """
    Public API: Real-time Streaming RAG (Server-Sent Events / NDJSON).
    Streams agent status updates, synthesized tokens, and final verification metrics.
    """
    try:
        return StreamingResponse(
            rag_workflow.stream_ask(req.message),
            media_type="application/x-ndjson"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("src.app:app", host="0.0.0.0", port=port, reload=True)
