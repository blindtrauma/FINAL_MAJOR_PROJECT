# app/config/celery_config.py - Celery configuration settings

from app.config.settings import settings

# Define the Celery configuration dictionary
# This will be loaded by the Celery app instance
celery_config = {
    "broker_url": settings.CELERY_BROKER_URL,
    "result_backend": settings.CELERY_RESULT_BACKEND,
    "task_ignore_result": False, # Set to True if you don't need task results
    "task_track_started": True, # To know when a task has started
    "task_serializer": "json",
    "result_serializer": "json",
    "accept_content": ["json"],
    "timezone": "UTC", # Use UTC
    "enable_utc": True,

    # Optional: Define task queues if you want to route tasks
    # "task_queues": (
    #     Queue('default', routing_key='default'),
    #     Queue('mini_llm', routing_key='mini_llm'), # Example queue for mini-LLM tasks
    # ),
    # "task_routes": {
    #     'app.tasks.interview_tasks.run_mini_llm_surprise': {'queue': 'mini_llm'},
    # },

    # Optional: Configure beat for periodic tasks
    # "beat_schedule": {
    #     'monitor-interviews': {
    #         'task': 'app.tasks.interview_tasks.monitor_interview_progress',
    #         'schedule': 60.0, # Run every 60 seconds
    #     },
    # }
}