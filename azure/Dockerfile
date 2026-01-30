# azure/Dockerfile
# Note: do not run locally

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

# Copy folders (Context is project root)
COPY engines/bot /app/engines/bot
COPY server /app/server
COPY .env .

ENV PYTHONPATH=/app
ENV ENVIRONMENT=production
EXPOSE 80

CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "80"]