import uuid
import threading

from fastapi import APIRouter, Body, HTTPException
from fastapi.responses import JSONResponse

from app.retrieval.embedding import (
    TaskStatus,
    EmbeddingRequest,
    start_embedding_task, 
    initialize_embedding_task,
    get_task_status,
    is_task_id_in_tasks
)

router = APIRouter(prefix="/embedding", tags=["Embedding related functions"])


@router.post("/start", status_code=202)
def start_embedding(request: EmbeddingRequest = Body(...)):
    """
    POST endpoint to start the long-running task.
    Creates a unique task_id, starts the thread, and returns the task_id.
    """
    task_id = str(uuid.uuid4())
    # Initialize this task's state in the dictionary
    initialize_embedding_task(task_id)
    # Create and start the thread
    thread = threading.Thread(
        target=start_embedding_task, 
        args=(request.name, task_id, request.texts),
        daemon=True
    )
    thread.start()

    check_status_url = f"/embedding/{task_id}"
    return JSONResponse(
        status_code=202,
        content={
            "message": "Embedding task started successfully.",
            "task_id": task_id,
            "check_status_url": check_status_url
        }
    )


@router.get("/{task_id}", response_model=TaskStatus)
def get_progress(task_id: str):
    """
    GET endpoint to retrieve the current progress and status of a task.
    """
    if not is_task_id_in_tasks(task_id):
        raise HTTPException(status_code=404, detail="Task not found")

    task_info = get_task_status(task_id)
    return TaskStatus(
        task_id=task_id,
        progress=task_info.progress,
        status=task_info.status
    )