# app/models/pydantic_models.py - Pydantic models for API request/response validation

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

# --- Request Models ---

class InterviewStartRequest(BaseModel):
    """Request body for starting a new interview."""
    job_description_id: str = Field(..., description="ID of the uploaded and processed Job Description.")
    resume_id: str = Field(..., description="ID of the uploaded and processed Resume.")

# Model for incoming chat messages (representing audio chunks or user input) - Copied from interview.py temporarily
# Redefine here as the central source of truth for models
class ChatMessage(BaseModel):
    """Represents a message sent from the user during the interview chat."""
    type: str = Field(..., description="Type of message, e.g., 'chunk', 'final', 'control'.")
    payload: str = Field(..., description="The transcribed text chunk, final sentence, or control command.")
    timestamp: float = Field(..., description="Client-side timestamp of the event.")
    is_final: bool = Field(False, description="True if this is the final transcription after a pause.")


# --- Response Models ---

class UploadResponse(BaseModel):
    """Response model for document upload endpoints."""
    message: str
    filename: str
    stored_path: str = Field(..., description="Temporary storage path for the uploaded file.")
    task_id: str = Field(..., description="Celery task ID for background processing.")

class StartInterviewResponse(BaseModel):
    """Response model for starting a new interview."""
    interview_id: str = Field(..., description="Unique ID for the new interview session.")
    message: str

# Model for outgoing messages from the server (LLM response or control) - Copied from interview.py temporarily
# Redefine here as the central source of truth for models
class ServerMessage(BaseModel):
    """Represents a message sent from the server to the user."""
    type: str = Field(..., description="Type of message, e.g., 'llm_response', 'mini_llm_filler', 'interview_state', 'error', 'end', 'llm_response_draft'.")
    payload: str = Field(..., description="The text content (LLM response, filler, error message, etc.).")
    # Could add more fields like 'partial' for streaming, 'timestamp', etc.

# Optional: Model for analysis results if exposed via API
# class AnalysisResultResponse(BaseModel):
#     status: str
#     details: Dict[str, Any] # Structure depends on analyzer output