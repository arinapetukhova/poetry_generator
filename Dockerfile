FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code AND chroma_db folder
COPY backend/ .
COPY frontend/ ./frontend/
COPY chroma_db/ ./chroma_db/  # Copy your pre-built ChromaDB

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE $PORT

CMD uvicorn main:app --host 0.0.0.0 --port $PORT