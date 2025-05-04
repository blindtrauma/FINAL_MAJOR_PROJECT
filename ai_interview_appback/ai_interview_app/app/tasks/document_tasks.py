# app/tasks/document_tasks.py - Celery tasks for document processing

import uuid # For generating analysis IDs
from celery import Task
import os
from typing import Dict, Any
from app.tasks.celery import celery_app # Import the Celery app instance
from app.services.document_parser import DocumentParser # Import parser service
from app.services.storage_service import StorageService # Import storage service
from app.analysis.pre_interview_analyzer import PreInterviewAnalyzer # Import analyzer
from app.core.exceptions import DocumentProcessingError, StorageError # Import exceptions

# Dependencies - Injected into tasks (or instantiated within)
# For tasks, it's often simpler to instantiate dependencies inside the task
# or use a base Task class that handles dependency injection if needed.
# Let's instantiate inside for simplicity here.

class DocumentProcessingTask(Task):
    """Base task for document processing to potentially handle shared resources."""
    _parser = None
    _storage = None
    _analyzer = None

    @property
    def parser(self):
        if self._parser is None:
            # Instantiate DocumentParser (no dependencies needed for it)
            self._parser = DocumentParser()
        return self._parser

    @property
    def storage(self):
        if self._storage is None:
            # Instantiate StorageService - needs base_path from settings
            from app.config.settings import settings # Import settings here to avoid circular dependency on app start
            self._storage = StorageService(base_path=settings.STORAGE_PATH)
        return self._storage

    @property
    def analyzer(self):
        if self._analyzer is None:
            # Instantiate PreInterviewAnalyzer - might need LLM service or other deps
            # For now, let's assume it needs StorageService to load document content
            # and LLMService for analysis using LLM.
            from app.config.settings import settings
            from app.services.llm_service import LLMService # Import LLMService here
            llm_service = LLMService(api_key=settings.OPENAI_API_KEY, model_name=settings.MAIN_LLM_MODEL)
            self._analyzer = PreInterviewAnalyzer(llm_service=llm_service, storage_service=self.storage) # Pass storage service
        return self._analyzer


# Define the task using the Celery app decorator
@celery_app.task(bind=True, base=DocumentProcessingTask, name="app.tasks.document_tasks.process_document")
def process_document(self: DocumentProcessingTask, file_path: str, document_type: str) -> Dict[str, Any]:
    """
    Celery task to parse a document (JD or Resume), store its content,
    and trigger pre-interview analysis.
    """
    print(f"Starting document processing task for {file_path} ({document_type})")

    try:
        # 1. Parse the document content
        print(f"Parsing document: {file_path}")
        text_content = self.parser.parse_document(file_path)
        print(f"Parsed {len(text_content)} characters.")

        # Generate a unique ID for this document processing/analysis cycle
        # We could reuse the file's temporary unique ID, or generate a new one.
        # Let's assume the unique filename generated in the API endpoint is the ID for storage.
        doc_id = os.path.splitext(os.path.basename(file_path))[0] # Extract ID from unique filename

        # 2. Save the parsed content
        print(f"Saving parsed content for ID: {doc_id}")
        saved_path = self.storage.save_document_content(doc_id, text_content)
        print(f"Content saved to {saved_path}")

        # 3. Trigger pre-interview analysis task
        # The analyzer needs the document type and ID to load the content.
        print(f"Triggering pre-interview analysis task for ID: {doc_id}")
        # Import analysis tasks here to avoid circular imports on task definition level
        from app.tasks.analysis_tasks import run_pre_interview_analysis
        analysis_task_result = run_pre_interview_analysis.delay(doc_id=doc_id, document_type=document_type)

        print(f"Document processing task finished for {file_path}. Analysis task ID: {analysis_task_result.id}")

        return {
            "status": "completed",
            "doc_id": doc_id,
            "saved_path": saved_path,
            "analysis_task_id": analysis_task_result.id
        }

    except (DocumentProcessingError, StorageError) as e:
        print(f"Document processing failed for {file_path}: {e}")
        # Update task state to failure and store error info
        self.update_state(state='FAILURE', meta={'exc_type': type(e).__name__, 'exc_message': str(e)})
        raise # Re-raise the exception to be caught by Celery

    except Exception as e:
        print(f"An unexpected error occurred during document processing for {file_path}: {e}")
        self.update_state(state='FAILURE', meta={'exc_type': type(e).__name__, 'exc_message': str(e)})
        raise # Re-raise the exception


# You might add other document related tasks here, e.g.,
# - Task to clean up temporary uploaded files after processing
# @celery_app.task
# def cleanup_upload_file(file_path: str):
#     try:
#         os.remove(file_path)
#         print(f"Cleaned up uploaded file: {file_path}")
#     except OSError as e:
#         print(f"Error cleaning up file {file_path}: {e}")