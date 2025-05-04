# app/core/exceptions.py - Custom application exceptions

class AIInterviewAppException(Exception):
    """Base exception for the AI Interview Application."""
    pass

class InterviewNotFound(AIInterviewAppException):
    """Raised when an interview session with a given ID is not found."""
    def __init__(self, interview_id: str):
        self.interview_id = interview_id
        super().__init__(f"Interview session '{interview_id}' not found.")

class InvalidInterviewState(AIInterviewAppException):
    """Raised when an operation is attempted on an interview in an invalid state."""
    def __init__(self, interview_id: str, current_state: str, expected_state: str = "any"):
        self.interview_id = interview_id
        self.current_state = current_state
        self.expected_state = expected_state
        super().__init__(f"Invalid state for interview '{interview_id}'. Expected '{expected_state}', got '{current_state}'.")

class DocumentProcessingError(AIInterviewAppException):
    """Raised when document parsing or initial analysis fails."""
    def __init__(self, document_path: str, detail: str = "Failed to process document."):
        self.document_path = document_path
        self.detail = detail
        super().__init__(f"Document processing failed for '{document_path}': {detail}")

class LLMServiceError(AIInterviewAppException):
    """Raised when there's an error interacting with the LLM service."""
    def __init__(self, message: str, original_exception: Exception = None):
        self.message = message
        self.original_exception = original_exception
        super().__init__(f"LLM service error: {message}")

class StorageError(AIInterviewAppException):
    """Raised when there's an error interacting with the storage service."""
    def __init__(self, message: str, original_exception: Exception = None):
        self.message = message
        self.original_exception = original_exception
        super().__init__(f"Storage error: {message}")


# Add other specific exceptions as needed, e.g., for analysis failures, etc.