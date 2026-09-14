FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/app/.cache/huggingface

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY api.py .
COPY src ./src
COPY dataset ./dataset

EXPOSE 8765

CMD ["sh", "-c", "uvicorn api:app --host 0.0.0.0 --port ${PORT:-8765}"]
