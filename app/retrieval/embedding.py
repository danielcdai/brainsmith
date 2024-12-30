from pydantic import BaseModel
import time
import uuid


# TODO: Encapsulate the whole embedding task management in a class.


TASKS = {}


class TaskStatus(BaseModel):
    task_id: str
    progress: float
    status: str


def start_embedding_task():
    """
    This function simulates a long running embedding task, e.g. 5-10 min.
    Updates TASKS[task_id]["progress"] along the way.
    """
    task_id = str(uuid.uuid4())
    TASKS[task_id] = {
        "progress": 0.0,
        "status": "initialized"
    }
    try:
        TASKS[task_id]["status"] = "running"
        for i in range(100):
            # Simulate work being done
            time.sleep(0.2)  # 0.2 * 100 = 20 seconds for example
            # Update progress
            TASKS[task_id]["progress"] = i / 99.0  # final iteration => 1.0
        # Mark as completed
        TASKS[task_id]["progress"] = 1.0
        TASKS[task_id]["status"] = "completed"
    except Exception as e:
        # If something goes wrong, record the failure
        TASKS[task_id]["status"] = "failed"
        raise e  # Optionally log or handle the exception

    return task_id


def initialize_embedding_task(task_id: str):
    """
    Initialize a new embedding task with the given task_id.
    """
    TASKS[task_id] = {
        "progress": 0.0,
        "status": "initialized"
    }


def get_task_status(task_id: str) -> TaskStatus:
    """
    Retrieve the status of a given task by its task_id.
    """
    if task_id not in TASKS:
        raise ValueError(f"Task with id {task_id} does not exist.")
    
    task_info = TASKS[task_id]
    return TaskStatus(task_id=task_id, progress=task_info["progress"], status=task_info["status"])


def is_task_id_in_tasks(task_id: str) -> bool:
    """
    Check if a task_id exists in the TASKS dictionary.
    """
    return task_id in TASKS