# Use official Python runtime as base image
FROM python:3.11-slim

# Set working directory in container
WORKDIR /app

# Install system dependencies (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY server.py .

# Cloud Run sets PORT automatically
ENV PORT=8080

# EXPOSE is optional but okay
EXPOSE 8080

# Create .env placeholder (ignored by Cloud Run)
RUN touch .env

# Cloud Run does health checks externally — remove Docker HEALTHCHECK

# Run app
CMD ["python", "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080"]