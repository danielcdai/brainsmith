import uuid
import threading

from fastapi import APIRouter, Body, HTTPException
from fastapi.responses import JSONResponse
from cortex.retrieval.embedding import *


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
        args=(request.name, request.tag, task_id, request.texts),
        daemon=True
    )
    thread.start()

    check_status_url = f"/embedding/task/{task_id}"
    return JSONResponse(
        status_code=202,
        content={
            "message": "Embedding task started successfully.",
            "task_id": task_id,
            "check_status_url": check_status_url
        }
    )


@router.get("/task/{task_id}", response_model=TaskStatus)
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
        status=task_info.status,
        estimated_time_left=task_info.estimated_time_left
    )


@router.get("/task")
def get_all_tasks():
    """
    GET endpoint to retrieve the status of all tasks.
    """
    return load_all_tasks()


@router.get("/names", response_model=set)
def get_embedded_names():
    """
    GET endpoint to retrieve the list of names that have been embedded.
    """
    names = get_all_embedded_names()
    if names is None:
        raise HTTPException(status_code=404, detail="No names found")
    return names


@router.get("/tags", response_model=set)
def get_tags_by_name(name: str):
    """
    GET endpoint to retrieve the tags of a collection by its name.
    """
    tags = get_all_tags_by_name(name)
    if tags is None:
        raise HTTPException(status_code=404, detail="Name not found")
    return tags


@router.delete("/tags")
def delete_tags_by_name(name: str, tags: str):
    """
    DELETE endpoint to delete the tags of a collection by its name.
    """
    [delete_tag(name, t) for t in tags.split(",")]
    return JSONResponse(status_code=204, content={"message": "Tags deleted successfully."})