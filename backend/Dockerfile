FROM python:3.11-slim

WORKDIR /app

# Copy requirements FIRST
COPY requirements.txt .

# Install dependencies
RUN pip install -r requirements.txt

# Then copy the rest of the application
COPY . .

RUN mkdir -p chroma_db

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]