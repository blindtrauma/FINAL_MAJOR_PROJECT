# app/services/storage_service.py - Service for handling data storage

import os
import json
from typing import Dict, Any, Optional
from app.core.exceptions import StorageError # Import custom exception

class StorageService:
    """
    Handles persistent storage and retrieval of application data,
    such as parsed documents, analysis results, and interview states.
    Currently implemented with local file storage.
    Could be extended for database or cloud storage.
    """
    def __init__(self, base_path: str):
        self.base_path = base_path
        # Ensure the base directory exists
        os.makedirs(self.base_path, exist_ok=True)
        print(f"StorageService initialized with base path: {self.base_path}")


    def _get_file_path(self, data_type: str, item_id: str, extension: str = ".json") -> str:
        """Helper to get the full path for a stored item."""
        # Example path structure: base_path/data_type/item_id.extension
        dir_path = os.path.join(self.base_path, data_type)
        os.makedirs(dir_path, exist_ok=True) # Ensure type directory exists
        file_name = f"{item_id}{extension}"
        return os.path.join(dir_path, file_name)

    def save_document_content(self, doc_id: str, content: str) -> str:
        """Saves parsed document text content."""
        file_path = self._get_file_path("documents", doc_id, ".txt")
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Saved document content to {file_path}")
            return file_path
        except Exception as e:
            raise StorageError(f"Failed to save document content for ID {doc_id}: {e}", original_exception=e)

    def load_document_content(self, doc_id: str) -> str:
        """Loads parsed document text content."""
        file_path = self._get_file_path("documents", doc_id, ".txt")
        if not os.path.exists(file_path):
            raise StorageError(f"Document content for ID {doc_id} not found.", original_exception=FileNotFoundError(file_path))
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return content
        except Exception as e:
            raise StorageError(f"Failed to load document content for ID {doc_id}: {e}", original_exception=e)


    def save_analysis_result(self, analysis_id: str, result: Dict[str, Any]) -> str:
        """Saves the result of a document analysis."""
        # analysis_id could be the doc_id or a separate analysis ID
        file_path = self._get_file_path("analysis_results", analysis_id, ".json")
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=4)
            print(f"Saved analysis result to {file_path}")
            return file_path
        except Exception as e:
            raise StorageError(f"Failed to save analysis result for ID {analysis_id}: {e}", original_exception=e)

    def load_analysis_result(self, analysis_id: str) -> Dict[str, Any]:
        """Loads a document analysis result."""
        file_path = self._get_file_path("analysis_results", analysis_id, ".json")
        if not os.path.exists(file_path):
            raise StorageError(f"Analysis result for ID {analysis_id} not found.", original_exception=FileNotFoundError(file_path))
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                result = json.load(f)
            return result
        except Exception as e:
            raise StorageError(f"Failed to load analysis result for ID {analysis_id}: {e}", original_exception=e)

    # Methods for saving/loading interview state or full transcripts if needed for persistence
    # async def save_interview_state(self, interview_id: str, state_data: Dict[str, Any]):
    #     """Saves the current interview state (excluding non-serializable parts)."""
    #     file_path = self._get_file_path("interview_states", interview_id, ".json")
    #     try:
    #         with open(file_path, "w", encoding="utf-8") as f:
    #             json.dump(state_data, f, indent=4)
    #         print(f"Saved interview state for {interview_id}")
    #     except Exception as e:
    #         raise StorageError(f"Failed to save interview state for ID {interview_id}: {e}", original_exception=e)

    # async def load_interview_state(self, interview_id: str) -> Optional[Dict[str, Any]]:
    #      """Loads an interview state."""
    #      file_path = self._get_file_path("interview_states", interview_id, ".json")
    #      if not os.path.exists(file_path):
    #          return None # State not found
    #      try:
    #          with open(file_path, "r", encoding="utf-8") as f:
    #              state_data = json.load(f)
    #          return state_data
    #      except Exception as e:
    #          raise StorageError(f"Failed to load interview state for ID {interview_id}: {e}", original_exception=e)