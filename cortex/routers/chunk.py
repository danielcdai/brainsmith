import os
import uuid
from typing import List

from fastapi import APIRouter, Depends
from fastapi import UploadFile, File, Form
from fastapi.responses import JSONResponse

from cortex.retrieval.chunking import Chunker
from cortex.admin.authenticate import verify_bearer_token


router = APIRouter(prefix="/api/v1/chunk", tags=["Chunking"], dependencies=[Depends(verify_bearer_token)])


@router.post("/", response_model=List[str])
async def get_chunks_from_file(
    file: UploadFile = File(...),
    chunk_size: int = Form(1000),
    chunk_overlap: int = Form(50),
    splitter: str = Form("text"),
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


@router.post("/uploadfile")
async def upload_file(
    upload_name: str = Form(
        default_factory=lambda: str(uuid.uuid4()), regex=r"^[a-z][a-z0-9-]*$"
    ),
    files: List[UploadFile] = File(...),
):
    from cortex.config import settings
    upload_dir = settings.upload_folder or \
                 os.path.join(os.getcwd(), "uploaded_sources")
    
    # Create a subdirectory for the upload_name
    upload_subdir = os.path.join(upload_dir, upload_name)
    if not os.path.exists(upload_subdir):
        os.makedirs(upload_subdir)

    saved_files = []
    for file in files:
        file_path = os.path.join(upload_subdir, file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())
        saved_files.append(file_path)

    return {"upload_name": upload_name, "files": saved_files}