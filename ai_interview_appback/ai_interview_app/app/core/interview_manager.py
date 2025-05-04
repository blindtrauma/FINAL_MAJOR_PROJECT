# app/core/interview_manager.py - Core logic for managing interview sessions

import uuid
import asyncio
from typing import Dict, Any, Optional
from fastapi import WebSocket # Need WebSocket type hint if passed

from app.core.interview_state import InterviewState # Assuming InterviewState exists
from app.core.exceptions import InterviewNotFound, InvalidInterviewState # Assuming exceptions exist
from app.services.llm_service import LLMService # Import needed services
from app.services.mini_llm_service import MiniLLMService
from app.services.storage_service import StorageService
from app.config.settings import Settings # Manager might need settings
# Import Celery tasks the manager will trigger
from app.tasks.interview_tasks import process_chunk_task, process_final_response_task, trigger_mini_llm_surprise_task
# Assuming tasks are imported and callable via .delay()

# In-memory store for active interview states (for simplicity).
# In a real production app, this might be a database or a dedicated state service
# that handles persistence and concurrent access.
active_interview_states: Dict[str, InterviewState] = {}

class InterviewManager:
    """
    Manages the lifecycle and state of individual interview sessions.
    Orchestrates interactions between API, state, services, and Celery tasks.
    """
    def __init__(
        self,
        llm_service: LLMService,
        mini_llm_service: MiniLLMService,
        storage_service: StorageService,
        settings: Settings
    ):
        self.llm_service = llm_service
        self.mini_llm_service = mini_llm_service
        self.storage_service = storage_service
        self.settings = settings
        # Note: Accessing active_interview_states directly here assumes
        # this manager instance is effectively a singleton or operates
        # on a globally accessible state registry.

    async def start_interview(self, job_description_id: str, resume_id: str) -> str:
        """
        Initiates a new interview session.
        Loads analyzed documents, performs pre-interview analysis (if needed here),
        and creates an initial state.
        """
        interview_id = str(uuid.uuid4())
        print(f"Starting new interview with ID: {interview_id}")

        # TODO: Load JD and Resume analysis results using storage_service
        # jd_data = await self.storage_service.load_analysis(job_description_id)
        # resume_data = await self.storage_service.load_analysis(resume_id)

        # TODO: Perform pre-interview analysis or trigger task
        # This analysis determines the initial questions and interview plan
        # interview_plan = await self.run_pre_interview_analysis(jd_data, resume_data)
        # For now, let's use placeholders
        interview_plan = {"initial_questions": ["Tell me about yourself.", "Walk me through your resume."], "topics": ["Experience", "Skills"]}

        initial_state = InterviewState(
            id=interview_id,
            job_description_id=job_description_id,
            resume_id=resume_id,
            interview_plan=interview_plan,
            transcript="", # Start with empty transcript
            conversation_history=[] # LLM conversation history format
            # ... other state fields
        )

        # Store the initial state (e.g., in memory, database, or cache)
        # For this example, use the simple in-memory dict
        active_interview_states[interview_id] = initial_state
        print(f"Interview state created for {interview_id}")

        # Potentially trigger the first question generation task here
        # Or the first question is sent when the WebSocket connects
        # Let's assume the first question is handled on WS connection for live chat feel.

        return interview_id

    async def activate_interview_session(self, interview_id: str, websocket: WebSocket):
        """
        Loads or retrieves an active interview state and associates a WebSocket connection.
        Sends the initial state/first question to the client.
        """
        state = active_interview_states.get(interview_id)
        if not state:
            # Attempt to load from persistent storage if not in memory?
            # For now, just raise error if not in active states
            raise InterviewNotFound(f"Interview session {interview_id} not found.")

        if state.websocket is not None:
             print(f"Warning: Existing WebSocket found for {interview_id}. Closing previous connection.")
             # TODO: Handle existing connection - either reject new one or close old one gracefully
             try:
                 await state.websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Another connection opened.")
             except Exception as e:
                 print(f"Error closing previous websocket for {interview_id}: {e}")


        state.websocket = websocket # Store the active websocket
        print(f"WebSocket associated with interview_id: {interview_id}")

        # Send initial data to the client (e.g., first question, state info)
        # TODO: Get the initial question based on the interview_plan
        initial_question = state.interview_plan["initial_questions"][0] if state.interview_plan["initial_questions"] else "Hello, please tell me about yourself."

        await state.send_message(
            ServerMessage(type="llm_response", payload=initial_question).model_dump_json()
        )

        # Send the current state as well? Useful for client sync on reconnect.
        # await state.send_message(
        #      ServerMessage(type="interview_state", payload=state.model_dump_json()).model_dump_json()
        # )


    async def deactivate_interview_session(self, interview_id: str):
        """Removes WebSocket association and potentially marks state as inactive."""
        state = active_interview_states.get(interview_id)
        if state:
            state.websocket = None # Remove websocket reference
            # Decide if the state should be kept in memory or moved/persisted
            # For simplicity, keep it for now. In production, maybe move to 'completed'/'inactive' storage.
            print(f"WebSocket un-associated from interview_id: {interview_id}")

    async def handle_user_input(self, interview_id: str, input_type: str, content: str, is_final: bool, timestamp: float):
        """
        Processes incoming user input (transcription chunks).
        Determines when to send tasks to Celery for LLM processing.
        """
        state = active_interview_states.get(interview_id)
        if not state:
            raise InterviewNotFound(f"Interview session {interview_id} not found or inactive.")

        # Append the new chunk to the state's transcript and chunk buffer
        state.add_chunk(content, is_final, timestamp)
        print(f"Added chunk to {interview_id}. is_final: {is_final}. Current buffer: '{state.current_chunk_buffer}'")

        if is_final:
            print(f"Final input received for {interview_id}. Triggering final processing.")
            # User has finished speaking (pause detected).
            # Send the accumulated buffer to a Celery task for final LLM processing.
            # The task will generate the definitive response based on the full utterance.
            process_final_response_task.delay(
                interview_id=interview_id,
                full_utterance=state.current_chunk_buffer,
                conversation_history=state.conversation_history # Send history for context
            )
            # Clear the chunk buffer as the full utterance has been sent
            state.clear_chunk_buffer()

            # Potentially trigger a mini-LLM surprise task here?
            # Maybe based on randomness or specific context after a pause.
            # trigger_mini_llm_surprise_task.delay(interview_id=interview_id, context="after_user_pause")

        else:
            # User is still speaking. Process the chunk incrementally.
            # Trigger a Celery task to process the incremental chunk.
            # This task *might* trigger a background LLM call that generates
            # a *draft* response, which updates the state.
            # The front-end polls or is pushed the *latest draft* stored in the state.
            # Or, the LLM task could potentially push partial results back if using streaming.
            # The prompt for this task tells the LLM the input is incomplete.
            process_chunk_task.delay(
                interview_id=interview_id,
                chunk=content,
                current_buffer=state.current_chunk_buffer, # Send current buffer for context
                conversation_history=state.conversation_history
            )

            # --- Logic for sending back latest draft / handling "live" response ---
            # This part is tricky in a strict request/response model.
            # With WebSockets, the manager or a background process/task needs
            # to monitor the state for `latest_llm_draft` updates and push them.
            # A dedicated task monitoring state changes or the `process_chunk_task`
            # itself could send messages back via the stored websocket reference.
            # For now, the `handle_user_input` function just triggers the processing task.
            # The mechanism for sending responses back is handled elsewhere (e.g., in tasks or a state watcher).

    # Add methods to be called by Celery tasks upon completion
    async def update_state_with_llm_draft(self, interview_id: str, latest_draft: str):
        """Called by process_chunk_task to update the latest draft."""
        state = active_interview_states.get(interview_id)
        if state and state.websocket:
            state.latest_llm_draft = latest_draft
            # Send the latest draft to the client immediately
            try:
                await state.send_message(
                   ServerMessage(type="llm_response_draft", payload=latest_draft).model_dump_json()
                )
            except Exception as e:
                 print(f"Error sending LLM draft to websocket {interview_id}: {e}")
                 # Handle potential dead websocket? Mark state inactive?

    async def finalize_llm_response(self, interview_id: str, final_response: str, conversation_entry: Dict[str, Any]):
        """Called by process_final_response_task to finalize the LLM response."""
        state = active_interview_states.get(interview_id)
        if state and state.websocket:
            state.conversation_history.append(conversation_entry) # Add user input + LLM response
            state.latest_llm_draft = "" # Clear draft once final response is sent
            state.transcript += f"User: {conversation_entry['user']}\nAI: {final_response}\n" # Add to full transcript

            # Send the final response to the client
            try:
                 await state.send_message(
                    ServerMessage(type="llm_response", payload=final_response).model_dump_json()
                 )
            except Exception as e:
                 print(f"Error sending final LLM response to websocket {interview_id}: {e}")
                 # Handle potential dead websocket?

    async def send_mini_llm_surprise(self, interview_id: str, surprise_text: str):
         """Called by trigger_mini_llm_surprise_task to send a filler."""
         state = active_interview_states.get(interview_id)
         if state and state.websocket:
             try:
                 await state.send_message(
                     ServerMessage(type="mini_llm_filler", payload=surprise_text).model_dump_json()
                 )
             except Exception as e:
                 print(f"Error sending mini-LLM surprise to websocket {interview_id}: {e}")
                 # Handle potential dead websocket?


    # TODO: Implement methods for ending interview, running post-analysis, etc.
    async def end_interview(self, interview_id: str):
        """Marks interview as complete and triggers post-interview analysis."""
        state = active_interview_states.pop(interview_id, None) # Remove from active states
        if state:
            print(f"Interview {interview_id} ended. Triggering post-analysis.")
            # TODO: Trigger post-interview analysis task
            # analysis_tasks.run_post_interview_analysis.delay(interview_id=interview_id, transcript=state.transcript, ...)
            if state.websocket:
                 try:
                     await state.send_message(ServerMessage(type="interview_end", payload="Interview completed.").model_dump_json())
                     await state.websocket.close() # Close the websocket connection
                 except Exception as e:
                      print(f"Error sending end message or closing websocket for {interview_id}: {e}")

            # TODO: Save final state/transcript to persistent storage
            # await self.storage_service.save_interview_state(interview_id, state.to_dict()) # Assuming a state serialization method
        else:
            print(f"Attempted to end non-existent interview {interview_id}")
            raise InterviewNotFound(f"Interview session {interview_id} not found.")


    # TODO: Method for triggering code analysis if needed during interview
    # async def request_code_analysis(self, interview_id: str, code_snippet: str, context: str):
    #     """Triggers a code analysis task for a given snippet."""
    #     state = active_interview_states.get(interview_id)
    #     if state:
    #          analysis_tasks.analyze_code.delay(
    #              interview_id=interview_id,
    #              code_snippet=code_snippet,
    #              context=context, # Context from conversation
    #              job_description_id=state.job_description_id # JD for context
    #          )
    #     else:
    #          print(f"Attempted to request code analysis for non-existent interview {interview_id}")
    #          # Handle error - maybe send an error message back to client if websocket is active?