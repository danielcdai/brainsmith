import os
import json
import time
import hashlib
import numpy as np
import faiss

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from cortex.config import settings


# Ensure directories exist
os.makedirs(settings.upload_folder, exist_ok=True)
os.makedirs(settings.temp_index_folder, exist_ok=True)

# ---------------------
# Global in-memory session storage
# ---------------------
# Mapping from session_id to a list of file_ids
session_files = {}

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
# API 1: File Upload and Indexing
# ---------------------
@router.post("/upload")
async def upload_file(
    session_id: str = Form(...),
    file: UploadFile = File(...)
):
    # Read the uploaded file
    contents = await file.read()
    try:
        text = contents.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded text.")

    # Generate a unique file_id (hash of content + current time)
    hash_input = text + str(time.time())
    file_id = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()[:16]

    # Create a folder for this file under the upload directory
    upload_path = os.path.join(settings.upload_folder, file_id)
    os.makedirs(upload_path, exist_ok=True)
    # Save the file (using the original filename)
    file_path = os.path.join(upload_path, file.filename)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(text)

    # ---------------------
    # Build a FAISS index for the file
    # ---------------------
    # Create a folder for the FAISS index
    index_folder = os.path.join(settings.temp_index_folder, file_id)
    os.makedirs(index_folder, exist_ok=True)

    # Split the file content into chunks (here fixed size chunks of 1000 characters)
    chunk_size = 1000
    chunks = [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]
    if not chunks:
        raise HTTPException(status_code=400, detail="File is empty after processing.")

    # Compute embeddings for each chunk
    embeddings = np.array([get_embedding(chunk) for chunk in chunks])
    dim = embeddings.shape[1]

    # Build a FAISS index (using L2 distance)
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)

    # Save the FAISS index to disk
    index_file = os.path.join(index_folder, "index.faiss")
    faiss.write_index(index, index_file)

    # Also, store the list of chunks so that we can later map an index result to its text.
    chunks_file = os.path.join(index_folder, "chunks.json")
    with open(chunks_file, "w", encoding="utf-8") as f:
        json.dump(chunks, f)

    # ---------------------
    # Update the session mapping
    # ---------------------
    session_files.setdefault(session_id, []).append(file_id)

    return {"file_id": file_id, "filename": file.filename}

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
@router.get("/search")
def search_chunks(
    file_id: str = Query(..., description="The file id to search"),
    query: str = Query(..., description="Query text"),
    top_k: int = Query(5, description="Number of top chunks to return")
):
    # Locate the FAISS index folder for this file_id
    index_folder = os.path.join(settings.temp_index_folder, file_id)
    index_file = os.path.join(index_folder, "index.faiss")
    chunks_file = os.path.join(index_folder, "chunks.json")

    if not os.path.exists(index_file) or not os.path.exists(chunks_file):
        raise HTTPException(status_code=404, detail="FAISS index or chunk mapping not found for the given file_id.")

    # Load the FAISS index
    index = faiss.read_index(index_file)
    # Load the chunks
    with open(chunks_file, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    # Compute the embedding for the query
    query_embedding = get_embedding(query).reshape(1, -1)

    # Search the index
    distances, indices = index.search(query_embedding, top_k)
    indices = indices[0].tolist()
    distances = distances[0].tolist()

    # Map the index results back to chunks and scores
    results = []
    for idx, score in zip(indices, distances):
        if idx < len(chunks):
            results.append({"chunk": chunks[idx], "score": score})

    return {"file_id": file_id, "query": query, "results": results}

