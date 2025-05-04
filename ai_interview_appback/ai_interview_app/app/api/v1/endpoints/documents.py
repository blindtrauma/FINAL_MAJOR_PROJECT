# app/api/v1/endpoints/documents.py - API endpoints for document handling

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from typing import Annotated
import os
import uuid # To generate unique filenames

from app.config.settings import settings
from app.tasks.document_tasks import process_document # Assuming this task exists
from app.api.v1.dependencies import get_settings # Dependency to get settings

router = APIRouter()

@router.post("/documents/upload/jd")
async def upload_job_description(
    file: Annotated[UploadFile, File()],
    settings: Annotated[get_settings, Depends()] # Use dependency for settings
):
    """
    Uploads a Job Description document and triggers background processing.
    """
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file uploaded")

    # Create a directory to save uploads if it doesn't exist
    upload_dir = os.path.join(settings.STORAGE_PATH, "uploads")
    os.makedirs(upload_dir, exist_ok=True)

    # Generate a unique filename to prevent conflicts
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"jd_{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(upload_dir, unique_filename)

    # Save the file asynchronously
    try:
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Could not save file: {e}")

    # Trigger celery task to process the document
    # The task will parse, analyze, and store the structured data
    task_result = process_document.delay(file_path, "job_description") # Assuming task takes path and type

    return {
        "message": "Job Description uploaded and processing started.",
        "filename": file.filename,
        "stored_path": file_path,
        "task_id": task_result.id
    }

@router.post("/documents/upload/resume")
async def upload_resume(
    file: Annotated[UploadFile, File()],
    settings: Annotated[get_settings, Depends()]
):
    """
    Uploads a Resume document and triggers background processing.
    """
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file uploaded")

    upload_dir = os.path.join(settings.STORAGE_PATH, "uploads")
    os.makedirs(upload_dir, exist_ok=True)

    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"resume_{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(upload_dir, unique_filename)

    try:
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Could not save file: {e}")

    # Trigger celery task to process the document
    task_result = process_document.delay(file_path, "resume")

    return {
        "message": "Resume uploaded and processing started.",
        "filename": file.filename,
        "stored_path": file_path,
        "task_id": task_result.id
    }

# Optional: Endpoint to check document processing status
# @router.get("/documents/status/{task_id}")
# async def get_document_status(task_id: str):
#     task = process_document.AsyncResult(task_id)
#     if task.state == 'PENDING':
#         response = {'state': task.state, 'status': 'Pending...'}
#     elif task.state != 'FAILURE':
#         response = {'state': task.state, 'status': task.info.get('status', 'Processing...')}
#         if task.result: # If task has finished successfully
#             response['result'] = task.result # The result might be the parsed data ID or confirmation
#     else:
#         # Something went wrong in the task
#         response = {
#             'state': task.state,
#             'status': str(task.info), # Exception message
#         }
#     return response