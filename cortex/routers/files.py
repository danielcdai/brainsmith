import os
import json
import time
import hashlib
import numpy as np
import faiss

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query, BackgroundTasks
from cortex.config import settings

from langchain_community.document_loaders import TextLoader
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pydantic import BaseModel


# Ensure directories exist
os.makedirs(settings.upload_folder, exist_ok=True)
os.makedirs(settings.temp_index_folder, exist_ok=True)

# ---------------------
# Global in-memory session storage
# ---------------------
# Mapping from session_id to a list of file_ids
session_files = {}


# Mapping from file_id to progress status (e.g., "Received", "Saving file", "Building FAISS index", "Done", or error)
progress_status = {}


# ---------------------
# Dummy embedding function
# ---------------------
def get_embedding(text: str, dim: int = 128) -> np.ndarray:
    """
    Returns a deterministic "dummy" embedding for a given text by seeding
    a random generator with a hash of the text.
    """
    seed = int(hashlib.sha256(text.encode("utf-8")).hexdigest(), 16) % (2**32)
    rng = np.random.default_rng(seed)
    return rng.random(dim).astype("float32")

# ---------------------
# FastAPI Application
# ---------------------

router = APIRouter(prefix="/files",  tags=["Files API"])


# ---------------------
# Background Task for Processing the Uploaded File
# ---------------------
def process_file(file_id: str, text: str, original_filename: str, session_id: str):
    try:
        # Update progress: Saving file (0.3)
        progress_status[file_id] = {"status": "Saving file", "progress": 0.3}
        upload_path = os.path.join(settings.upload_folder, file_id)
        os.makedirs(upload_path, exist_ok=True)
        file_path = os.path.join(upload_path, original_filename)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(text)

        # Update progress: Building FAISS index (0.7)
        index_folder = os.path.join(settings.temp_index_folder, file_id)
        os.makedirs(index_folder, exist_ok=True)

        # Split the file content into chunks (fixed-size chunks of 1000 characters)
        chunk_size = 1000
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
        )
        loader = TextLoader(
            file_path=file_path,
            autodetect_encoding=True,
        )
        chunks = loader.load_and_split(text_splitter=splitter)
        progress_status[file_id] = {"status": "Building FAISS index", "progress": 0.7}

        if not chunks:
            raise Exception("File is empty after processing.")

        # Compute embeddings for each chunk
        embeddings = OllamaEmbeddings(
            base_url=settings.ollama_base_url,
            model="nomic-embed-text:latest",
        )
        vector_store = FAISS.from_documents(documents=chunks, embedding=embeddings)

        # vector_store = FAISS(
        #     embedding_function=embeddings,
        #     index=index,
        #     docstore=InMemoryDocstore(),
        #     index_to_docstore_id={},
        # )
        # for i, chunk in enumerate(chunks):
        #     vector_store.aadd_documents([chunk])
        #     # Update progress based on the number of chunks processed
        #     progress_status[file_id] = {"status": "Adding documents to vector store", "progress": 0.7 + 0.2 * (i / len(chunks))}
        vector_store.save_local(folder_path=index_folder)
        session_files.setdefault(session_id, []).append(file_id)

        # Mark progress as complete (1.0)
        progress_status[file_id] = {"status": "Done", "progress": 1.0}
    except Exception as e:
        progress_status[file_id] = {"status": f"Error: {str(e)}", "progress": 0.0}


# ---------------------
# API 1: Asynchronous File Upload and Indexing
# ---------------------
@router.post("/upload")
async def upload_file(
    background_tasks: BackgroundTasks,
    session_id: str = Form(...),
    file: UploadFile = File(...)
):
    # Read the uploaded file asynchronously
    contents = await file.read()
    try:
        text = contents.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded text.")

    # Generate a unique file_id (hash of content + current time)
    hash_input = text + str(time.time())
    file_id = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()[:16]

    # Initialize progress: "Received" with 0 progress
    progress_status[file_id] = {"status": "Received", "progress": 0.0}

    # Trigger background processing
    background_tasks.add_task(process_file, file_id, text, file.filename, session_id)

    # Build progress URL (assuming client can reach the same server address)
    progress_url = f"/files/progress?file_id={file_id}"
    return {"file_id": file_id, "progress_url": progress_url}


# ---------------------
# API: Get Upload & Embedding Progress by File ID
# ---------------------
@router.get("/progress")
def get_progress(file_id: str = Query(..., description="File ID to check progress")):
    progress = progress_status.get(file_id)
    if progress is None:
        raise HTTPException(status_code=404, detail="File ID not found.")
    return {"file_id": file_id, "status": progress["status"], "progress": progress["progress"]}


# ---------------------
# API 2: Get Files List for a Session
# ---------------------
@router.get("/current")
def list_files(session_id: str = Query(..., description="Session ID to fetch file list")):
    files = session_files.get(session_id, [])
    return {"session_id": session_id, "files": files}

# ---------------------
# API 3: Get File Content by File ID
# ---------------------
@router.get("/file/{file_id}")
def get_file_content(file_id: str):
    upload_path = os.path.join(settings.upload_folder, file_id)
    if not os.path.exists(upload_path):
        raise HTTPException(status_code=404, detail="File not found.")

    # For simplicity, assume the uploaded file is the first file in the folder.
    file_names = os.listdir(upload_path)
    if not file_names:
        raise HTTPException(status_code=404, detail="No file found in the folder.")

    file_path = os.path.join(upload_path, file_names[0])
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")

    return {"file_id": file_id, "content": content}

# ---------------------
# API 4: Get Relevant Chunks by Query
# ---------------------
class FileSearchRequest(BaseModel):
    file_id: str
    query: str
    top_k: int = 5

@router.post("/search")
async def search_chunks(
    request: FileSearchRequest
):
    # Locate the FAISS index folder for this file_id
    file_id = request.file_id
    query = request.query
    top_k = request.top_k

    index_folder = os.path.join(settings.temp_index_folder, file_id)
    index_file = os.path.join(index_folder, "index.faiss")
    pkl_file = os.path.join(index_folder, "index.pkl")

    if not os.path.exists(index_file) or not os.path.exists(pkl_file):
        raise HTTPException(
            status_code=404,
            detail="FAISS index or chunk mapping not found for the given file ID."
        )

    embeddings = OllamaEmbeddings(
        base_url=settings.ollama_base_url,
        model="nomic-embed-text:latest",
    )
    vector_store = FAISS.load_local(
        index_folder, embeddings, allow_dangerous_deserialization=True
    )
    print(f"Loaded FAISS index for file ID: {index_folder}")
    results = vector_store.similarity_search(
        query=query,
        k=top_k,
        search_type="mmr"
    )
    print(results)

    return {"file_id": file_id, "query": query, "results": results}
