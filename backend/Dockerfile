FROM python:3.10

WORKDIR /app

# Install dependencies first to leverage Docker layer cache
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy application source
COPY . /app

# Cloud Run sets PORT env var (defaults to 8080). Respect it, defaulting to 8080 locally.
EXPOSE 8080
CMD ["/bin/sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
