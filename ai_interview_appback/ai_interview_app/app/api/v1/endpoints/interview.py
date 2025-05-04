# app/api/v1/endpoints/interview.py - API endpoints for interview management

from fastapi import APIRouter, HTTPException, status, Depends, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Annotated, Dict, Any
import uuid # To generate interview IDs

from app.core.interview_manager import InterviewManager # Assuming this class exists
from app.core.exceptions import InterviewNotFound, InvalidInterviewState # Assuming these exist
from app.api.v1.dependencies import get_interview_manager # Assuming a dependency for the manager
from app.models.pydantic_models import InterviewStartRequest # Assuming this model exists

router = APIRouter()

# --- Pydantic Models (or import from models/pydantic_models.py) ---
# For now, let's define the request model here for clarity in this file
class InterviewStartRequest(BaseModel):
    """Request body for starting a new interview."""
    # Assuming document IDs are returned from document upload/processing
    job_description_id: str
    resume_id: str

# Model for incoming chat messages (representing audio chunks or user input)
class ChatMessage(BaseModel):
    """Represents a message sent from the user during the interview chat."""
    type: str # e.g., "chunk", "final", "control"
    payload: str # The transcribed text chunk or final sentence
    timestamp: float # Client-side timestamp of the event
    is_final: bool = False # True if this is the final transcription after a pause

# Model for outgoing messages from the server (LLM response or control)
class ServerMessage(BaseModel):
    """Represents a message sent from the server to the user."""
    type: str # e.g., "llm_response", "mini_llm_filler", "interview_state", "error", "end"
    payload: str # The text content
    # Could add more fields like 'partial' for streaming, 'timestamp', etc.

# --- End Pydantic Models ---


@router.post("/interview/start")
async def start_interview(
    request: InterviewStartRequest,
    manager: Annotated[InterviewManager, Depends(get_interview_manager)] # Inject manager
):
    """
    Starts a new interview session based on uploaded documents.
    Returns the interview ID.
    """
    try:
        interview_id = await manager.start_interview(
            job_description_id=request.job_description_id,
            resume_id=request.resume_id
        )
        return {"interview_id": interview_id, "message": "Interview started. Connect to websocket for chat."}
    except Exception as e: # Catch potential errors from manager (e.g., document analysis failure)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to start interview: {e}")


@router.websocket("/interview/{interview_id}/chat")
async def websocket_interview_chat(
    websocket: WebSocket,
    interview_id: str,
    manager: Annotated[InterviewManager, Depends(get_interview_manager)] # Inject manager
):
    """
    WebSocket endpoint for the live interview chat.
    Receives user transcription chunks and sends LLM responses.
    """
    await websocket.accept()
    print(f"WebSocket connection accepted for interview_id: {interview_id}")

    try:
        # Initialize the interview state for this connection if not already active
        # The manager should handle loading state for an existing ID
        await manager.activate_interview_session(interview_id, websocket) # Associate websocket with session

        # --- Handle Incoming Messages (User Speech Chunks) ---
        while True:
            # Expecting text messages containing JSON payloads
            data = await websocket.receive_text()
            try:
                message = ChatMessage.model_validate_json(data) # Validate incoming JSON
                print(f"Received message type: {message.type}, final: {message.is_final}")

                # Process the incoming message via the InterviewManager
                # The manager will handle the logic of sending tasks to Celery
                # based on message type (chunk vs. final)
                await manager.handle_user_input(
                    interview_id=interview_id,
                    input_type=message.type,
                    content=message.payload,
                    is_final=message.is_final,
                    timestamp=message.timestamp
                )

                # The manager (or a separate task) will send responses back
                # via the websocket instance stored in the session state.

            except ValueError:
                # Handle invalid JSON or Pydantic validation errors
                await websocket.send_json({"type": "error", "payload": "Invalid message format"})
            except WebSocketDisconnect:
                print(f"WebSocket disconnected for interview_id: {interview_id}")
                # Clean up session in manager
                await manager.deactivate_interview_session(interview_id)
                break
            except InterviewNotFound:
                 print(f"InterviewNotFound for interview_id: {interview_id}")
                 await websocket.send_json({"type": "error", "payload": "Interview session not found."})
                 await websocket.close(code=status.WS_1008_POLICY_VIOLATION) # Or appropriate code
                 break
            except Exception as e:
                print(f"Error processing websocket message for {interview_id}: {e}")
                # Send a generic error back and potentially close the connection
                await websocket.send_json({"type": "error", "payload": "An internal error occurred."})
                # await websocket.close(code=status.WS_1011_INTERNAL_ERROR) # Decide on closing behavior
                # continue # Or break/close depending on error severity

    except WebSocketDisconnect:
        print(f"WebSocket disconnected for interview_id: {interview_id}")
        # Clean up session in manager if not already done
        await manager.deactivate_interview_session(interview_id)
    except InterviewNotFound:
        print(f"Initial InterviewNotFound for interview_id: {interview_id}")
        # Cannot activate session, close connection immediately
        await websocket.send_json({"type": "error", "payload": "Interview session not found."})
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
    except Exception as e:
        print(f"Unhandled error during websocket connection for {interview_id}: {e}")
        await websocket.send_json({"type": "error", "payload": "An unexpected error occurred establishing connection."})
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)