# app/api/v1/dependencies.py - FastAPI dependency functions

from fastapi import Depends, Request
from typing import Annotated

from app.config.settings import Settings, settings # Import settings class and instance
from app.core.interview_manager import InterviewManager # Import the manager class
from app.services.llm_service import LLMService # Import services the manager depends on
from app.services.mini_llm_service import MiniLLMService
from app.core.interview_state import InterviewState # Import the state class (or its representation)
from app.services.storage_service import StorageService # Assuming storage service is needed

# --- Dependency to inject Settings ---
# This is already done by importing the settings instance directly,
# but creating a dependency allows for overriding in tests.
def get_settings() -> Settings:
    return settings

# --- Dependency to get/create InterviewManager ---
# In a real app, you might want to manage the lifespan of the manager
# or services it depends on (e.g., using a dependency container or just
# initializing once in lifespan). For simplicity here, we'll create
# service instances. A more robust approach might use singletons or
# application-level state.

def get_llm_service(settings: Annotated[Settings, Depends(get_settings)]) -> LLMService:
    """Dependency to get the main LLM Service."""
    # In a real app, you might want to cache/singleton this service instance
    return LLMService(api_key=settings.OPENAI_API_KEY, model_name=settings.MAIN_LLM_MODEL)

def get_mini_llm_service(settings: Annotated[Settings, Depends(get_settings)]) -> MiniLLMService:
    """Dependency to get the Mini LLM Service."""
    # In a real app, you might want to cache/singleton this service instance
    return MiniLLMService(api_key=settings.OPENAI_API_KEY, model_name=settings.MINI_LLM_MODEL)

def get_storage_service(settings: Annotated[Settings, Depends(get_settings)]) -> StorageService:
    """Dependency to get the Storage Service."""
    # Assuming StorageService needs the base storage path
    return StorageService(base_path=settings.STORAGE_PATH)

# Dependency to get the InterviewManager
# It depends on other services it needs to operate
def get_interview_manager(
    llm_service: Annotated[LLMService, Depends(get_llm_service)],
    mini_llm_service: Annotated[MiniLLMService, Depends(get_mini_llm_service)],
    storage_service: Annotated[StorageService, Depends(get_storage_service)],
    settings: Annotated[Settings, Depends(get_settings)] # Manager might need settings too
) -> InterviewManager:
    """Dependency to get the Interview Manager."""
    # This is where the manager is instantiated.
    # The manager needs access to the *live* state of interviews.
    # This implies the manager itself might need to be a singleton or
    # have access to a shared state registry.
    # For now, we'll assume the Manager class itself handles finding/loading state by ID.
    # A more complex setup might have a separate state registry dependency.
    return InterviewManager(
        llm_service=llm_service,
        mini_llm_service=mini_llm_service,
        storage_service=storage_service,
        settings=settings # Pass settings if needed internally
        # Pass reference to Celery app or task dispatch method?
        # Or maybe manager just calls task.delay directly? Let's assume direct call for now.
    )

# Example of a dependency that uses the request object
# async def get_user(request: Request):
#     # Logic to extract user from header, session, etc.
#     pass