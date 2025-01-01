from pydantic import BaseModel
from langchain_core.documents import Document
from langchain_chroma import Chroma
from typing import List
from app.config import settings
import logging


# Redirect the chroma logs
logging.basicConfig(
    filename=f'{settings.log_dir}/chroma_warnings.log',
    level=logging.WARNING,
    format='%(levelname)s:%(name)s:%(message)s'
)


EMBEDDING_TASKS = {}


class EmbeddingRequest(BaseModel):
    name: str
    texts: List[str]


class TaskStatus(BaseModel):
    task_id: str
    progress: float
    status: str


def start_embedding_task(name: str, task_id: str, texts: List[str]) -> str:
    """
    Starts an embedding task and updates its progress for client polling.
    This function initiates a long-running embedding task, which typically takes 5-10 minutes.
    It updates the progress of the task in the global EMBEDDING_TASKS dictionary, allowing clients
    to poll for the current status and progress of the task.
    Args:
        name (str): The name of the embedding task.
        task_id (str): The unique identifier for the task.
        texts (List[str]): A list of texts to be embedded.
    Returns:
        str: The task_id of the started embedding task.
    """
    try:
        EMBEDDING_TASKS[task_id]["status"] = "running"
        EMBEDDING_TASKS[task_id]["progress"] = 0.2

        from langchain_ollama import OllamaEmbeddings
        import hashlib
        embeddings = OllamaEmbeddings(
            # TODO: Make both url and model configurable
            base_url="http://localhost:11434",
            model="nomic-embed-text:latest",
        )
        # TODO: Track embedding progress
        vector_store = Chroma(
            collection_name=name,
            embedding_function=embeddings,
            # TODO: Make persist_directory configurable
            persist_directory=settings.embeddings_dir,
        )
        total_texts = len(texts)
        for i, text in enumerate(texts):
            text_id = hashlib.md5(text.encode()).hexdigest()
            document = Document(
                id=text_id, 
                metadata={"source": "upload"}, 
                page_content=text)
            # Warning: use add_documents instead of update_documents to avoid empty search results
            vector_store.add_documents(documents=[document])
            EMBEDDING_TASKS[task_id]["progress"] = 0.2 + (i + 1) / total_texts * 0.8 
        
        # Mark as completed
        EMBEDDING_TASKS[task_id]["progress"] = 1.0
        EMBEDDING_TASKS[task_id]["status"] = "completed"
    except Exception as e:
        EMBEDDING_TASKS[task_id]["status"] = "failed"
        raise e


def initialize_embedding_task(task_id: str):
    """
    Initialize a new embedding task with the given task_id.
    """
    EMBEDDING_TASKS[task_id] = {
        "progress": 0.0,
        "status": "initialized"
    }


def get_task_status(task_id: str) -> TaskStatus:
    """
    Retrieve the status of a given task by its task_id.
    """
    if task_id not in EMBEDDING_TASKS:
        raise ValueError(f"Task with id {task_id} does not exist.")
    
    task_info = EMBEDDING_TASKS[task_id]
    return TaskStatus(task_id=task_id, progress=task_info["progress"], status=task_info["status"])


def is_task_id_in_tasks(task_id: str) -> bool:
    """
    Check if a task_id exists in the TASKS dictionary.
    """
    return task_id in EMBEDDING_TASKS