# app/config/settings.py - Application settings management

import os
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or .env file.
    Uses pydantic-settings for validation and loading.
    """
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Core Settings ---
    ENVIRONMENT: str = "development"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    # --- LLM Service Settings ---
    OPENAI_API_KEY: str = Field(..., env="OPENAI_API_KEY") # ... means required
    MAIN_LLM_MODEL: str = "gpt-4o-mini"
    MINI_LLM_MODEL: str = "gpt-3.5-turbo-0125"

    # --- Celery & Broker Settings ---
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str ="redis://localhost:6379/1"

    # --- Storage Settings ---
    # Ensure this path exists or is handled correctly by the app/docker setup
    STORAGE_PATH: str = "/app/data"


# Create a settings instance to be imported elsewhere
settings = Settings()

# Example of how to use in another file:
# from app.config.settings import settings
# api_key = settings.OPENAI_API_KEY