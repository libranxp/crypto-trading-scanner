FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

# Create data dir for caches/logs
RUN mkdir -p /app/data

# Default to API (FastAPI). In Render, set Start Command to:
# uvicorn app:app --host 0.0.0.0 --port 10000
EXPOSE 10000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "10000"]
