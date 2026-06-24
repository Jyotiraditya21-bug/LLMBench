#!/bin/bash
set -e

# Start Redis in the background (if REDIS_URL is not set externally)
if [ -z "$REDIS_URL" ]; then
  echo "REDIS_URL not set. Launching local Redis server in user space..."
  redis-server --port 6379 --daemonize yes --dir /tmp --pidfile /tmp/redis.pid
  export REDIS_URL="redis://localhost:6379/0"
fi

# Start Celery worker in the background
echo "Starting Celery worker..."
celery -A backend.app.core.celery_app worker --pool=solo --loglevel=info &

# Start Uvicorn backend server in the foreground
echo "Starting Uvicorn server on port ${PORT:-7860}..."
exec uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-7860}
