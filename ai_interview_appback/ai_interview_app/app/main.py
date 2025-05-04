# app/main.py - Entry point for the FastAPI application

from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.config.settings import settings
from app.api.v1.endpoints import documents, interview
from app.tasks.celery import celery_app # Import the Celery app instance

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles startup and shutdown events for the FastAPI application.
    Connects to Celery broker on startup (optional, Celery tasks will handle connections)
    """
    print("Application startup...")
    # Optional: Basic check or initialization related to services if needed
    # e.g., check storage path exists, connect to database (if not handled by ORM)

    # Note: Celery connections are typically managed by Celery itself within tasks/workers,
    # but you could add checks here if required.

    yield # Application runs

    print("Application shutdown...")
    # Clean up resources if necessary
    # e.g., close database connections (if not handled automatically)

app = FastAPI(
    title="AI Interview Application",
    description="Live AI interviewer based on JD and Resume",
    version="1.0.0",
    lifespan=lifespan # Register the lifespan context manager
)

# Include routers for API endpoints
app.include_router(documents.router, prefix="/api/v1", tags=["documents"])
app.include_router(interview.router, prefix="/api/v1", tags=["interview"])

@app.get("/")
async def read_root():
    """Root endpoint for basic health check."""
    return {"message": "AI Interview App is running"}

# Basic health check for Celery broker connection status (optional)
# This would typically check if the broker is reachable, not if tasks are running
# from celery.utils.nodenames import default_nodename
# @app.get("/health/celery")
# async def celery_health_check():
#     try:
#         with celery_app.connection_or_acquire(block=True) as conn:
#              conn.ensure_connection(max_retries=1) # Check connection once
#         return {"status": "ok", "broker": "connected"}
#     except Exception as e:
#         return {"status": "error", "broker": "disconnected", "detail": str(e)}, 500