#!/bin/bash

# scripts/run_worker.sh - Script to run the Celery worker

# Exit immediately if a command exits with a non-zero status.
set -e

# Activate virtual environment if using one
# source .venv/bin/activate

# Navigate to the application directory (if not already there)
# cd /app

# Check if .env exists and load it if necessary (useful for local dev)
# In Docker, env_file handles this.
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

echo "Starting Celery worker..."
# Run the Celery worker
# -A specifies the Celery application instance (module:app)
# worker specifies the worker command
# -l info sets logging level to info
# -P solo runs using the solo execution pool (good for dev, simple async tasks).
#    For production, consider gevent or prefork. gevent is needed for async tasks like websockets.
# --uid nobody --gid nobody # Optional: run as a non-root user

celery -A app.tasks.celery worker -l info -P solo
# For async tasks (needed for WS push from tasks): celery -A app.tasks.celery worker -l info -P gevent -c 1000 # Example gevent pool with 1000 concurrency