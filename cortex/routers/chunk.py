import os
from typing import List

from fastapi import APIRouter
from fastapi import UploadFile, File, Form
from fastapi.responses import JSONResponse

from cortex.retrieval.chunking import Chunker


router = APIRouter(prefix="/chunk", tags=["Chunk related functions"])


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

