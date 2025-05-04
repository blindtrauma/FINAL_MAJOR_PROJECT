# app/tasks/interview_tasks.py - Celery tasks for live interview processing

import time
from celery import Task, chord, group # Import Celery primitives for potential chaining/grouping
import asyncio# Import asyncio for async task handling
from app.tasks.celery import celery_app # Import the Celery app instance
from app.services.llm_service import LLMService # Import LLM service
from app.services.mini_llm_service import MiniLLMService # Import Mini-LLM service
from app.services.storage_service import StorageService # Storage for state persistence/loading

from app.core.exceptions import LLMServiceError, StorageError, InterviewNotFound # Import exceptions
from app.config.settings import settings # Import settings

# Base task for tasks requiring services and access to manager/state
class InterviewProcessingTask(Task):
    """Base task for interview-related tasks."""
    _llm_service = None
    _mini_llm_service = None
    _storage_service = None
    _manager = None # Reference to a shared manager instance? Or instantiated?

    # Note: Accessing the singleton InterviewManager from tasks requires care.
    # A simple approach is to re-instantiate services and call Manager methods
    # via a new Manager instance that knows how to access shared state (e.g., active_interview_states).
    # Or, the Manager itself could be a singleton loaded here.
    # For simplicity now, let's instantiate services and interact with the shared state/manager methods.

    @property
    def llm_service(self):
        if self._llm_service is None:
             # Pass settings here to avoid circular import issues at top level
             self._llm_service = LLMService(api_key=settings.OPENAI_API_KEY, model_name=settings.MAIN_LLM_MODEL)
        return self._llm_service

    @property
    def mini_llm_service(self):
        if self._mini_llm_service is None:
            self._mini_llm_service = MiniLLMService(api_key=settings.OPENAI_API_KEY, model_name=settings.MINI_LLM_MODEL)
        return self._mini_llm_service

    @property
    def storage_service(self):
        if self._storage_service is None:
            self._storage_service = StorageService(base_path=settings.STORAGE_PATH)
        return self._storage_service

    @property
    def manager(self):
        # Instantiate manager within the task. It should access the shared state dict.
        # This might need a more sophisticated state management if not using a global dict.
        from app.core.interview_manager import InterviewManager # Access manager's state/methods
        if self._manager is None:
             # Instantiate Manager with necessary services
             # Need a way for the manager instance in the task to find/update
             # the *correct* state object in the shared dictionary.
             # The manager methods called below (e.g., update_state_with_llm_draft)
             # already handle this by looking up the state by interview_id.
             self._manager = InterviewManager(
                 llm_service=self.llm_service,
                 mini_llm_service=self.mini_llm_service,
                 storage_service=self.storage_service,
                 settings=settings
             )
        return self._manager


# Task for processing incremental chunks
@celery_app.task(bind=True, base=InterviewProcessingTask)
def process_chunk_task(self: InterviewProcessingTask, interview_id: str, chunk: str, current_buffer: str, conversation_history: list):
    """
    Celery task to process an incremental user speech chunk.
    Calls LLMService to potentially generate a draft response.
    """
    print(f"Task: Processing chunk for interview {interview_id}. Chunk: '{chunk}'")
    try:
        # Use LLM service to process the chunk in incremental mode
        # This calls the method that uses the "user is still speaking" prompt
        # The LLM generates a *draft* or internal thought process.
        latest_draft = self.llm_service.process_incremental_chunk(
             conversation_history=conversation_history, # Pass context
             current_buffer=current_buffer # Pass the full buffer accumulated so far
        )
        print(f"Task: Generated draft for {interview_id}: '{latest_draft}'")

        # Update the interview state with the latest draft
        # The manager method also sends the draft via the websocket if active
        # Note: This call is synchronous from the task's perspective.
        # If update_state_with_llm_draft involves await, Celery worker needs async support (gevent, eventlet).
        # Assuming simple in-memory state update and WebSocket send for now.
        # If running a prefork worker, direct state modification is problematic.
        # Accessing `active_interview_states` directly from a prefork worker is unsafe.
        # A safer approach would be to send a message back to the main application process
        # or a dedicated state-management process/queue.
        # For simplicity with `solo` worker or gevent/eventlet, direct state access is shown,
        # but be aware of limitations with prefork. A dedicated state service (Redis, DB)
        # is the most robust for distributed workers.

        # Assuming the manager instance inside the task can safely interact with state
        # (e.g., via shared memory in gevent/solo, or accessing a persistent store)
        # Let's use the manager's method to handle the state update and WebSocket push.
        # This call needs to be awaited if the manager method is async, which requires async Celery worker.
        # If not using async workers, manager methods updating state/sending WS must be sync or use another mechanism.
        # Let's assume an async worker and async manager methods for WebSockets.
        # If sync worker, need to refactor state update/WS communication mechanism.
        # Assuming async capabilities for now.

        # Need to import asyncio to await manager calls
        # from app.core.interview_manager import active_interview_states # Direct access is simpler for example
        # state = active_interview_states.get(interview_id)
        # if state:
        #     # Assuming state object methods are awaited
        #     await state.update_latest_llm_draft(latest_draft) # State method to update and send WS

        # Or call manager method:
        asyncio.run(self.manager.update_state_with_llm_draft(interview_id, latest_draft))
        # Note: asyncio.run() in a task can be problematic. Best is to use async celery worker.
        # If sync worker, state updates/WS sends must be handled via non-async means (e.g., another queue, pub/sub).
        # Let's assume async worker capabilities for async/await within tasks.

        # Potentially trigger mini-LLM surprise task here based on interval or logic
        # trigger_mini_llm_surprise_task.delay(interview_id=interview_id, context="after_chunk")

    except InterviewNotFound:
        print(f"Task failed: Interview session {interview_id} not found for chunk processing.")
        # Task might not need to update Celery state for this, as it's an interview state issue.
        # It could log or signal back to the main app somehow if needed.
    except (LLMServiceError, StorageError) as e:
        print(f"Task failed: Error processing chunk for {interview_id}: {e}")
        self.update_state(state='FAILURE', meta={'exc_type': type(e).__name__, 'exc_message': str(e)})
        raise # Re-raise exception

    except Exception as e:
        print(f"Task failed: Unexpected error processing chunk for {interview_id}: {e}")
        self.update_state(state='FAILURE', meta={'exc_type': type(e).__name__, 'exc_message': str(e)})
        raise


# Task for processing the final utterance after user pause
@celery_app.task(bind=True, base=InterviewProcessingTask)
def process_final_response_task(self: InterviewProcessingTask, interview_id: str, full_utterance: str, conversation_history: list):
    """
    Celery task to process the full user utterance after a pause.
    Calls LLMService to generate the final response and updates state.
    """
    print(f"Task: Processing final utterance for interview {interview_id}.")
    try:
        # Use LLM service to generate the final response
        final_response = self.llm_service.process_final_utterance(
             conversation_history=conversation_history,
             full_utterance=full_utterance
        )
        print(f"Task: Generated final response for {interview_id}: '{final_response}'")

        # Prepare conversation entry to add to history
        new_history_entry = {
            "user": full_utterance,
            "assistant": final_response
            # Maybe include timestamp?
        }

        # Update the interview state with the final response and conversation history
        # The manager method also sends the final response via the websocket
        # Assuming async worker
        asyncio.run(self.manager.finalize_llm_response(interview_id, final_response, new_history_entry))


    except InterviewNotFound:
        print(f"Task failed: Interview session {interview_id} not found for final processing.")
    except (LLMServiceError, StorageError) as e:
        print(f"Task failed: Error processing final response for {interview_id}: {e}")
        self.update_state(state='FAILURE', meta={'exc_type': type(e).__name__, 'exc_message': str(e)})
        raise # Re-raise exception
    except Exception as e:
        print(f"Task failed: Unexpected error processing final response for {interview_id}: {e}")
        self.update_state(state='FAILURE', meta={'exc_type': type(e).__name__, 'exc_message': str(e)})
        raise


# Task for triggering mini-LLM surprises/fillers
@celery_app.task(bind=True, base=InterviewProcessingTask)
def trigger_mini_llm_surprise_task(self: InterviewProcessingTask, interview_id: str, context: str, conversation_snippet: str = ""):
    """
    Celery task to trigger the mini-LLM and send a surprise/filler message.
    Can be triggered periodically or based on events.
    """
    print(f"Task: Triggering mini-LLM surprise for interview {interview_id}, context: {context}")
    try:
        # Use mini-LLM service to generate the surprise text
        surprise_text = self.mini_llm_service.generate_surprise(context, conversation_snippet)

        if surprise_text:
            print(f"Task: Generated mini-LLM surprise for {interview_id}: '{surprise_text}'")
            # Send the surprise text via the websocket
            # Assuming async worker
            asyncio.run(self.manager.send_mini_llm_surprise(interview_id, surprise_text))
        else:
            print(f"Task: Mini-LLM generated no surprise text for {interview_id}, context: {context}")

    except InterviewNotFound:
        print(f"Task failed: Interview session {interview_id} not found for mini-LLM surprise.")
    except LLMServiceError as e:
        print(f"Task failed: Error generating mini-LLM surprise for {interview_id}: {e}")
        # Don't necessarily set task state to failure for a filler error
    except Exception as e:
        print(f"Task failed: Unexpected error triggering mini-LLM surprise for {interview_id}: {e}")
        # Don't necessarily set task state to failure for a filler error


# Optional: Task to periodically monitor interview state (e.g., for timeouts, pushing latest drafts)
# This would typically be scheduled by Celery Beat.
# @celery_app.task(bind=True, base=InterviewProcessingTask)
# def monitor_interview_progress(self: InterviewProcessingTask):
#     """
#     Periodic task to monitor active interviews.
#     Could check for inactivity timeouts, push latest drafts if not already sent, etc.
#     Requires accessing active_interview_states safely (e.g., via state service).
#     """
#     print("Task: Monitoring active interviews...")
#     # This task needs a safe way to iterate over active_interview_states
#     # (which is currently an in-memory dict, unsafe for prefork workers).
#     # If using a persistent state store (Redis, DB), this task would query it.
#
#     # Example (unsafe with prefork):
#     # for interview_id, state in list(active_interview_states.items()): # Iterate over a copy
#     #     if state.websocket and state.latest_llm_draft:
#     #         # Push the latest draft if it hasn't been pushed recently?
#     #         # Or based on timer since last draft generation?
#     #         print(f"Monitoring: Considering pushing draft for {interview_id}")
#     #         # Need logic to avoid spamming drafts
#     #         # await state.send_message(...) # Requires async worker or different mechanism
#     pass