#!/bin/bash

# scripts/run_app.sh - Script to run the FastAPI application

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

echo "Starting FastAPI application..."
# Run the FastAPI application using uvicorn
# app.main:app refers to the app instance in app/main.py
# --host 0.0.0.0 makes it accessible externally
# --port 8000 sets the port
# --reload enables hot reloading for development (remove in prod)

uvicorn app.main:app --host 0.0.0.0 --port 8000
# For production, remove --reload and potentially use a process manager like Gunicorn
# Example Gunicorn command:
# gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app -b 0.0.0.0:8000