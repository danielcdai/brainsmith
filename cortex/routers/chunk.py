import os
from typing import List

from fastapi import APIRouter
from fastapi import UploadFile, File, Form
from fastapi.responses import JSONResponse

import uuid
import redis
from cortex.retrieval.chunking import Chunker
from cortex.config import settings


router = APIRouter(prefix="/chunk", tags=["Chunk related functions"])


@router.post("/", response_model=List[str])
async def get_chunks_from_file(
    file: UploadFile = File(...),
    chunk_size: int = Form(1000),
    chunk_overlap: int = Form(50),
    splitter: str = Form("char"),
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

    file_extension = os.path.splitext(file.filename)[1]
    file_extension = file_extension.lstrip(".")
    chunker = Chunker.of(file_extension, chunk_size=chunk_size, chunk_overlap=chunk_overlap, splitter=splitter)
    documents = chunker.split(file_path=tmp_file_path)
    if content_only:
        # Concise response for later embedding tasks
        return JSONResponse(content=[doc.page_content for doc in documents])
    chunks = [{"length": len(doc.page_content), "content": doc.page_content} for doc in documents]
    return JSONResponse(content={"total": len(chunks), "chunks": chunks})


# TODO: Below is new chunking endpoints under development

@router.get("/fetch")
async def fetch_chunks():
    pass


@router.get("/file/upload")
async def upload_file(
    file: UploadFile = File(...)
):
    # Initialize Redis client
    redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)

    # Read the file content
    content = await file.read()

    # Save the uploaded file to the collection directory
    collection_dir = settings.file_collection_folder
    if not os.path.exists(collection_dir):
        os.makedirs(collection_dir)
    file_path = os.path.join(collection_dir, file.filename)
    with open(file_path, "wb") as f:
        f.write(content)

    file_id = str(uuid.uuid4())
    redis_client.set(file_id, file_path)

    return JSONResponse(content={"name": file.filename, "id": file_id})


@router.post('/file/upload')
def upload_file(
    file: UploadFile = File(...)
):
    file_id = str(uuid.uuid4())
    chunk_size = 1 * 1024 * 1024
    offset = 0
    chunk_index = 0
    while True:
        chunk_data = file.read(chunk_size)
        if not chunk_data:
            break

        chunk_id = f"{file_id}-{chunk_index}"
        from cortex.storage.chunks import save_chunk_to_storage, store_chunk_metadata
        # TODO: Save logic to be implemented
        # storage_path = save_chunk_to_storage(chunk_data, chunk_id)  # Store to S3, DB, etc.

        # store_chunk_metadata(file_id, chunk_id, offset, len(chunk_data), storage_path)
        
        offset += len(chunk_data)
        chunk_index += 1

    return JSONResponse(content={"fileID": file_id, "totalChunks": chunk_index})