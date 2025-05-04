# app/tasks/celery.py - Celery application instance setup

from celery import Celery
from app.config.celery_config import celery_config # Import Celery configuration

# Create the Celery application instance
# Use the app name (e.g., 'app.tasks') where tasks are defined
celery_app = Celery("ai_interview_app.tasks", broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1",
    include=[
        "app.tasks.document_tasks",
        "app.tasks.interview_tasks",
        "app.tasks.analysis_tasks",
    ],)

# Load configuration from the dictionary
celery_app.conf.update(celery_config)

# Auto-discover tasks in specified modules (e.g., within app.tasks package)
# This makes Celery find tasks in document_tasks.py, interview_tasks.py, etc.
celery_app.autodiscover_tasks(["app.tasks"])


# Optional: Example task (can be removed once actual tasks are defined)
@celery_app.task
def add(x, y):
    """Example task to add two numbers."""
    print(f"Executing add task: {x} + {y}")
    return x + y

# To run worker: celery -A app.tasks.celery worker -l info
# To run beat (if periodic tasks are configured): celery -A app.tasks.celery beat -l info