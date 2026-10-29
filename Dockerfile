# Production-Grade Container for Multi-Agent RAG Assistant
# Compatible with Hugging Face Spaces (Docker), Cloud Run, Render, and Railway
FROM python:3.11-slim

# Prevent Python from writing .pyc files & enable real-time streaming logs
# Restrict OpenMP / ONNX thread pools and enforce glibc malloc_trim to stay strictly under 250MB RAM
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=7860 \
    OMP_NUM_THREADS=1 \
    OPENBLAS_NUM_THREADS=1 \
    MKL_NUM_THREADS=1 \
    VECLIB_MAXIMUM_THREADS=1 \
    NUMEXPR_NUM_THREADS=1 \
    ORT_THREAD_POOL_SIZE=1 \
    MALLOC_TRIM_THRESHOLD_=100000

WORKDIR /app

# Install minimal system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Create non-root user (Mandatory for Hugging Face Spaces & container security)
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/qdrant_storage /tmp/fastembed_cache && \
    chown -R appuser:appuser /app /tmp/fastembed_cache

# Copy application code
COPY --chown=appuser:appuser src/ ./src/

USER appuser

EXPOSE 7860

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT}/ || exit 1

# Launch ASGI server with streaming support
CMD ["sh", "-c", "uvicorn src.app:app --host 0.0.0.0 --port ${PORT}"]
