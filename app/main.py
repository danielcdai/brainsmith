from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic_settings import BaseSettings
from uvicorn.config import LOGGING_CONFIG
from typing import List
from datetime import datetime
from fastapi import UploadFile, File, Form
from typing import List
from app.retrieval.loader import BrainSmithLoader
import logging
import logging.config
import uvicorn
import os


class Settings(BaseSettings):
    """Environment settings for the application."""
    server_port: int
    log_level: str = "INFO"
    log_dir: str = "logs"
    static_dist_path: str = "ui/build"

    class Config:
        # TODO: Load the env file path from an environment variable.
        env_file = ".env"

settings = Settings()


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
    chunk_overlap: int = Form(50)
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
    chunks = [doc.page_content for doc in documents]

    return {"count": len(chunks), "chunks": chunks}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=settings.server_port)