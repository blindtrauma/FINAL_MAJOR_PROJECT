# Dockerfile - Builds the Docker image for the FastAPI application service

# Use a lightweight Python base image
FROM python:3.11-slim-buster

# Set working directory in the container
WORKDIR /app

# Install build dependencies (needed for some libraries like PyMuPDF)
# and runtime dependencies. Clean up afterwards.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    libffi-dev \
    gcc \
    python3-dev \
    pandoc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY ./app /app/app
COPY ./.env /app/.env # Copy .env inside container if needed by app itself (e.g., for settings)

# Create a directory for storage if using local files
RUN mkdir -p /app/data

# Expose the port the FastAPI app will run on
EXPOSE 8000

# Command to run the application using uvicorn
# --host 0.0.0.0 makes the server accessible externally from the container
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]