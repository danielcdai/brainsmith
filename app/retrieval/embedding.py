from pydantic import BaseModel
from langchain_core.documents import Document
from langchain_chroma import Chroma
from typing import List
from app.config import settings
import logging
import uuid


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
        embeddings = None
        if settings.provider == "openai":
            if not settings.openai_api_key:
                raise ValueError("OpenAI API key not found in environment variables.")
            from langchain_openai import OpenAIEmbeddings
            embeddings = OpenAIEmbeddings(
                api_key=settings.openai_api_key,
                # TODO: Make openai embedding model configurable, hard-coded for now
                dimensions=768,
                model="text-embedding-3-large",
            )
            EMBEDDING_TASKS[task_id]["progress"] = 0.50
            vector_store = Chroma(
                collection_name=name,
                embedding_function=embeddings,
                persist_directory=settings.embeddings_dir,
            )
            uuids = [str(uuid.uuid4()) for _ in range(len(texts))]
            metadatas = [{"source": "upload"} for _ in range(len(texts))]
            vector_store.add_texts(texts=texts, metadatas=metadatas, ids=uuids)
        elif settings.provider == "ollama":
            from langchain_ollama import OllamaEmbeddings
            embeddings = OllamaEmbeddings(
                base_url=settings.ollama_base_url,
                # TODO: Make ollama embedding model configurable, hard-coded for now
                model="nomic-embed-text:latest",
            )
            vector_store = Chroma(
                collection_name=name,
                embedding_function=embeddings,
                persist_directory=settings.embeddings_dir,
            )
            total_texts = len(texts)
            for i, text in enumerate(texts):
                text_id = str(uuid.uuid4())
                document = Document(
                    id=text_id, 
                    metadata={"source": "upload"}, 
                    page_content=text)
                # Warning: use add_documents instead of update_documents to avoid empty search results
                vector_store.add_documents(documents=[document])
                EMBEDDING_TASKS[task_id]["progress"] = (i + 1) / total_texts
        
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