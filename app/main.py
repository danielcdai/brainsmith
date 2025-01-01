from fastapi import FastAPI, HTTPException, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from uvicorn.config import LOGGING_CONFIG
from typing import List
from datetime import datetime
from fastapi import UploadFile, File, Form
from typing import List
from app.retrieval.loader import BrainSmithLoader
from app.retrieval.search import SearchRequest, search_by_collection
from app.config import settings
from app.retrieval.embedding import (
    TaskStatus,
    EmbeddingRequest,
    start_embedding_task, 
    initialize_embedding_task,
    get_task_status,
    is_task_id_in_tasks
)
import logging
import logging.config
import uvicorn
import os
import uuid
import threading


# Get the default logging configuration from uvicorn and update it.
LOGGING_CONFIG["loggers"][__name__] = {
    "handlers": ["default"],
    "level": "INFO",
}
# Hide the access logs from the console.
LOGGING_CONFIG["loggers"]["uvicorn.access"] = {
    "handlers": ["default"],
    "level": "WARNING",
}
logging.config.dictConfig(LOGGING_CONFIG)


log = logging.getLogger(__name__)
if not os.path.exists(settings.log_dir):
    os.makedirs(settings.log_dir)
log_filename = f"{settings.log_dir}/app_{datetime.now().strftime('%Y%m%d')}.log"
file_handler = logging.FileHandler(log_filename)
log.addHandler(file_handler)
# TODO: Specify the log level for different modules here, if needed.
log.setLevel(settings.log_level.upper())


print(
    rf"""
 ______             _                  _      _     
(____  \           (_)                (_)_   | |    
 ____)  ) ____ ____ _ ____   ___ ____  _| |_ | | _  
|  __  ( / ___) _  | |  _ \ /___)    \| |  _)| || \ 
| |__)  ) |  ( ( | | | | | |___ | | | | | |__| | | |
|______/|_|   \_||_|_|_| |_(___/|_|_|_|_|\___)_| |_|
                                                    

Personal knowledge playground powered by GenAI & RAG
https://github.com/danielcdai/brainsmith
"""
)

app = FastAPI()


# Middleware to log the requests and responses in debug.
@app.middleware("http")
async def log_requests(request, call_next):
    client_host = request.client.host
    log.debug(f"Request: {request.method} {request.url} from {client_host}")
    response = await call_next(request)
    log.debug(f"Response status: {response.status_code} for {client_host}")
    return response


@app.get("/", response_class=JSONResponse, status_code=404)
async def read_root():
    return {"detail": "Not Found. Please refer to the API documentation for available endpoints."}


# Export the UI build as static files, served under /ui path.
app.mount("/ui", StaticFiles(directory=settings.static_dist_path, html=True), name="ui")


@app.post("/chunk", response_model=List[str])
async def get_chunks_from_file(
    file: UploadFile = File(...),
    chunk_size: int = Form(1000),
    chunk_overlap: int = Form(50),
    content_only: bool = Form(False)
):
    content = await file.read()
    # Save the uploaded file to the system temporary directory
    tmp_dir = os.path.join(os.path.abspath(os.sep), "tmp")
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)
    tmp_file_path = os.path.join(tmp_dir, file.filename)
    with open(tmp_file_path, "wb") as f:
        f.write(content)

    loader = BrainSmithLoader(file_path=tmp_file_path) 
    documents = loader.load(load_type="text", chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    if content_only:
        # Concise response for later embedding tasks
        return JSONResponse(content=[doc.page_content for doc in documents])
    chunks = [{"length": len(doc.page_content), "content": doc.page_content} for doc in documents]
    return JSONResponse(content={"total": len(chunks), "chunks": chunks})


@app.post("/embedding/start", status_code=202)
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


@app.get("/embedding/{task_id}", response_model=TaskStatus)
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


@app.post("/search", response_model=List[str])
async def search(request: SearchRequest):
    """
    POST endpoint to perform a search based on the provided parameters.
    """
    # Perform the search using the provided parameters
    docs = search_by_collection(
        collection_name=request.name, 
        query=request.query, 
        top_k=request.top_k, 
        search_type=request.search_type,
        **request.opts
    )
    if request.content_only:
        # Concise response for later embedding tasks
        return JSONResponse(content=[doc.page_content for doc in docs])
    contents = [{"length": len(doc.page_content), "content": doc.page_content} for doc in docs]
    return JSONResponse(content={"total": len(contents), "contents": contents})


if __name__ == "__main__":
    # Not useful if using uvicorn to run the server.
    uvicorn.run(app, host="0.0.0.0", port=settings.server_port)