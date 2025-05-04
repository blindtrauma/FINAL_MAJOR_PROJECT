# app/tasks/analysis_tasks.py - Celery tasks for analysis processes

from celery import Task

from app.tasks.celery import celery_app # Import the Celery app instance
from app.analysis.pre_interview_analyzer import PreInterviewAnalyzer # Import analyzers
from app.analysis.post_interview_analyzer import PostInterviewAnalyzer
from app.analysis.code_analyzer import CodeAnalyzer
from app.services.storage_service import StorageService # Import storage
from app.services.llm_service import LLMService # Import LLM service for analyzers
from app.config.settings import settings # Import settings
from app.core.exceptions import DocumentProcessingError, StorageError, LLMServiceError # Import exceptions
from typing import Dict, Any
# Base task for tasks requiring analysis services or storage/LLM
class AnalysisTask(Task):
    """Base task for analysis tasks."""
    _storage_service = None
    _llm_service = None
    _pre_analyzer = None
    _post_analyzer = None
    _code_analyzer = None

    @property
    def storage_service(self):
        if self._storage_service is None:
            self._storage_service = StorageService(base_path=settings.STORAGE_PATH)
        return self._storage_service

    @property
    def llm_service(self):
        if self._llm_service is None:
            self._llm_service = LLMService(api_key=settings.OPENAI_API_KEY, model_name=settings.MAIN_LLM_MODEL)
        return self._llm_service

    @property
    def pre_analyzer(self):
        if self._pre_analyzer is None:
            # PreInterviewAnalyzer needs LLM and Storage services
            self._pre_analyzer = PreInterviewAnalyzer(
                llm_service=self.llm_service,
                storage_service=self.storage_service
            )
        return self._pre_analyzer

    @property
    def post_analyzer(self):
        if self._post_analyzer is None:
            # PostInterviewAnalyzer needs LLM and Storage services
            self._post_analyzer = PostInterviewAnalyzer(
                 llm_service=self.llm_service,
                 storage_service=self.storage_service
            )
        return self._post_analyzer

    @property
    def code_analyzer(self):
         if self._code_analyzer is None:
             # CodeAnalyzer needs LLM service (for agents/function calling)
             self._code_analyzer = CodeAnalyzer(llm_service=self.llm_service)
         return self._code_analyzer


# Task for running pre-interview analysis
@celery_app.task(bind=True, base=AnalysisTask)
def run_pre_interview_analysis(self: AnalysisTask, doc_id: str, document_type: str) -> Dict[str, Any]:
    """
    Celery task to run pre-interview analysis on a document (JD or Resume).
    Saves the analysis result.
    """
    print(f"Task: Running pre-interview analysis for {document_type} ID: {doc_id}")
    try:
        # Use the pre-interview analyzer
        analysis_result = self.pre_analyzer.analyze(doc_id=doc_id, document_type=document_type)

        # Save the analysis result
        self.storage_service.save_analysis_result(doc_id, analysis_result) # Use doc_id as analysis_id

        print(f"Task: Pre-interview analysis completed and saved for {document_type} ID: {doc_id}")

        return {
            "status": "completed",
            "doc_id": doc_id,
            "analysis_result": analysis_result # Return result or just ID? Returning result for now.
        }

    except (DocumentProcessingError, StorageError, LLMServiceError) as e:
        print(f"Task failed: Error running pre-interview analysis for {doc_id}: {e}")
        self.update_state(state='FAILURE', meta={'exc_type': type(e).__name__, 'exc_message': str(e)})
        raise

    except Exception as e:
        print(f"Task failed: Unexpected error running pre-interview analysis for {doc_id}: {e}")
        self.update_state(state='FAILURE', meta={'exc_type': type(e).__name__, 'exc_message': str(e)})
        raise


# Task for running post-interview analysis
@celery_app.task(bind=True, base=AnalysisTask)
def run_post_interview_analysis(self: AnalysisTask, interview_id: str, jd_doc_id: str, resume_doc_id: str, transcript: str) -> Dict[str, Any]:
    """
    Celery task to run post-interview analysis on the complete transcript.
    Compares transcript against JD/Resume analysis. Saves final evaluation.
    """
    print(f"Task: Running post-interview analysis for interview ID: {interview_id}")
    try:
        # Load JD and Resume analysis results for context
        jd_analysis = self.storage_service.load_analysis_result(jd_doc_id)
        resume_analysis = self.storage_service.load_analysis_result(resume_doc_id)

        # Use the post-interview analyzer
        evaluation_result = self.post_analyzer.analyze(
            interview_id=interview_id,
            transcript=transcript,
            jd_analysis=jd_analysis,
            resume_analysis=resume_analysis
        )

        # Save the evaluation result
        # Use a separate analysis ID or a combination, e.g., f"post_{interview_id}"
        analysis_id = f"post_{interview_id}"
        self.storage_service.save_analysis_result(analysis_id, evaluation_result)

        print(f"Task: Post-interview analysis completed and saved for interview ID: {interview_id}")

        return {
            "status": "completed",
            "interview_id": interview_id,
            "analysis_id": analysis_id,
            "evaluation_result": evaluation_result
        }

    except (StorageError, LLMServiceError) as e:
        print(f"Task failed: Error running post-interview analysis for {interview_id}: {e}")
        self.update_state(state='FAILURE', meta={'exc_type': type(e).__name__, 'exc_message': str(e)})
        raise
    except Exception as e:
        print(f"Task failed: Unexpected error running post-interview analysis for {interview_id}: {e}")
        self.update_state(state='FAILURE', meta={'exc_type': type(e).__name__, 'exc_message': str(e)})
        raise


# Task for analyzing code snippets
@celery_app.task(bind=True, base=AnalysisTask)
def analyze_code_snippet(self: AnalysisTask, interview_id: str, code_snippet: str, context: str, jd_doc_id: str) -> Dict[str, Any]:
    """
    Celery task to analyze a user-provided code snippet.
    Uses the CodeAnalyzer which may leverage LLM function calling/agents.
    """
    print(f"Task: Analyzing code snippet for interview ID: {interview_id}")
    try:
        # Load JD analysis for context if needed by the analyzer
        jd_analysis = self.storage_service.load_analysis_result(jd_doc_id)

        # Use the code analyzer
        code_analysis_result = self.code_analyzer.analyze(
            code_snippet=code_snippet,
            context=context, # e.g., "User provided this code when asked about algorithm X"
            jd_analysis=jd_analysis # Pass relevant context
        )

        # TODO: Save the code analysis result? Or is it only for immediate LLM feedback?
        # If saving, define a save method in StorageService
        # analysis_id = f"code_{interview_id}_{uuid.uuid4().hex[:8]}" # Unique ID for this snippet analysis
        # self.storage_service.save_analysis_result(analysis_id, code_analysis_result)

        print(f"Task: Code analysis completed for interview ID: {interview_id}")

        return {
            "status": "completed",
            "interview_id": interview_id,
            "code_analysis_result": code_analysis_result
        }

    except (LLMServiceError, StorageError) as e:
        print(f"Task failed: Error analyzing code for {interview_id}: {e}")
        self.update_state(state='FAILURE', meta={'exc_type': type(e).__name__, 'exc_message': str(e)})
        raise
    except Exception as e:
        print(f"Task failed: Unexpected error analyzing code for {interview_id}: {e}")
        self.update_state(state='FAILURE', meta={'exc_type': type(e).__name__, 'exc_message': str(e)})
        raise