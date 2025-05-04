#!/bin/bash

# scripts/setup.sh - Script for initial application setup

# Exit immediately if a command exits with a non-zero status.
set -e

echo "Running setup script..."

# Create a Python virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python -m venv .venv
fi

# Activate the virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create the storage directory if it doesn't exist (matching STORAGE_PATH in .env/settings)
# Need to parse .env or rely on default/manual creation
STORAGE_PATH="/app/data" # Default based on Dockerfile and docker-compose
if [ -f .env ]; then
    # Attempt to parse STORAGE_PATH from .env
    STORAGE_PATH=$(grep '^STORAGE_PATH=' .env | cut -d '=' -f 2 | sed 's/"//g')
    if [ -z "$STORAGE_PATH" ]; then
        STORAGE_PATH="/app/data" # Fallback if not found or empty
    fi
fi

echo "Ensuring storage directory exists: $STORAGE_PATH"
mkdir -p "$STORAGE_PATH"

# Create a dummy .env file if it doesn't exist (user needs to fill it out)
if [ ! -f .env ]; then
    echo "Creating dummy .env file. Please fill in your configuration (e.g., OPENAI_API_KEY)."
    cat << EOF > .env
# .env - Environment variables for the application

# --- Core Settings ---
ENVIRONMENT=development
APP_HOST=0.0.0.0
APP_PORT=8000

# --- LLM Service Settings ---
# Replace with your actual OpenAI API key
OPENAI_API_KEY="YOUR_OPENAI_API_KEY"
MAIN_LLM_MODEL="gpt-4o-mini"
MINI_LLM_MODEL="gpt-3.5-turbo-0125"

# --- Celery & Broker Settings ---
CELERY_BROKER_URL="redis://localhost:6379/0" # Or redis:6379 in Docker
CELERY_RESULT_BACKEND="redis://localhost:6379/1" # Or redis:6379 in Docker

# --- Storage Settings ---
STORAGE_PATH="$STORAGE_PATH"

# Add other settings as needed
EOF
fi


echo "Setup complete."
echo "Please check the .env file and fill in necessary values like OPENAI_API_KEY."
echo "You can run the application using docker-compose up --build or by running the scripts in ./scripts."