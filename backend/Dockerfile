FROM python:3.13-slim

WORKDIR /workspace

# Install system utilities and redis-server for self-contained celery queue
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    redis-server \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files maintaining the 'backend.app' package structure
COPY app /workspace/backend/app
COPY start.sh /workspace/backend/start.sh

# Make entrypoint script executable
RUN chmod +x /workspace/backend/start.sh

# Set python path environment variable to resolve backend module imports
ENV PYTHONPATH=/workspace

EXPOSE 7860

CMD ["/workspace/backend/start.sh"]
