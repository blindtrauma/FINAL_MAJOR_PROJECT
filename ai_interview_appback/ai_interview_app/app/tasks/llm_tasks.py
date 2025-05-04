# app/tasks/llm_tasks.py - Celery tasks for general LLM interactions

from celery import Task

from app.tasks.celery import celery_app # Import the Celery app instance
from app.services.llm_service import LLMService # Import LLM service
# Import StorageService if tasks need to load/save data
from app.services.storage_service import StorageService
from app.config.settings import settings # Import settings to instantiate services
from app.core.exceptions import LLMServiceError, StorageError # Import exceptions

# Base task for tasks requiring LLMService or StorageService
class LLMTask(Task):
    """Base task for tasks requiring LLM or Storage services."""
    _llm_service = None
    _storage_service = None

    @property
    def llm_service(self):
        if self._llm_service is None:
            self._llm_service = LLMService(api_key=settings.OPENAI_API_KEY, model_name=settings.MAIN_LLM_MODEL)
        return self._llm_service

    @property
    def storage_service(self):
        if self._storage_service is None:
            self._storage_service = StorageService(base_path=settings.STORAGE_PATH)
        return self._storage_service

# Note: Tasks related to the live interview chunk processing are in interview_tasks.py
# This file is for other LLM tasks, e.g., initial question generation, post-analysis summarization etc.

# Example task: Generate the initial set of interview questions based on analysis
# This might be triggered by the process_document task or start_interview API endpoint.
@celery_app.task(bind=True, base=LLMTask)
def generate_initial_interview_plan(self: LLMTask, jd_doc_id: str, resume_doc_id: str) -> Dict[str, Any]:
    """
    Task to generate the detailed interview plan (topics, initial questions)
    after JD and Resume analysis is complete.
    """
    print(f"Task: Generating initial interview plan for JD:{jd_doc_id}, Resume:{resume_doc_id}")
    try:
        # Load analysis results
        jd_analysis = self.storage_service.load_analysis_result(jd_doc_id)
        resume_analysis = self.storage_service.load_analysis_result(resume_doc_id)

        # Use LLM to synthesize an interview plan
        # This requires a specific prompt in interview_prompts
        # Let's assume the PreInterviewAnalyzer handles the LLM call directly,
        # and this task just orchestrates loading/saving.
        # Or, the LLMService could have a specific method for this.
        # Let's refine: The analysis tasks actually *produce* the plan and save it.
        # So, this task might be redundant if analysis_tasks handles plan generation.

        # Alternative context: If the manager needs to *regenerate* a plan or
        # generate follow-up questions based on the *plan*, this is the place.
        # For now, let's assume the initial plan is part of the pre-analysis result.

        # Returning a placeholder or confirming analysis result contains the plan
        return {
            "status": "initial_plan_generation_task_placeholder",
            "jd_analysis_id": jd_doc_id, # Assuming analysis ID is doc ID
            "resume_analysis_id": resume_doc_id
            # The actual plan would be loaded from storage after analysis tasks complete
        }

    except (StorageError, LLMServiceError) as e:
        print(f"Task failed: Error generating initial interview plan: {e}")
        self.update_state(state='FAILURE', meta={'exc_type': type(e).__name__, 'exc_message': str(e)})
        raise

    except Exception as e:
        print(f"Task failed: Unexpected error generating initial interview plan: {e}")
        self.update_state(state='FAILURE', meta={'exc_type': type(e).__name__, 'exc_message': str(e)})
        raise


# You might have other LLM tasks here, e.g.,
# - Summarize interview transcript (used in post-analysis)
# - Generate evaluation points (used in post-analysis)
# - Refine interview plan mid-interview (more complex)