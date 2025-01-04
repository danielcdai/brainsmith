import logging
import logging.config
import os
from datetime import datetime

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from uvicorn.config import LOGGING_CONFIG

from cortex.routers import embedding, chunk, search
from cortex.config import settings


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
LLM Provider: {settings.provider}
https://github.com/danielcdai/brainsmith
"""
)

app = FastAPI()
app.include_router(embedding.router)
app.include_router(chunk.router)
app.include_router(search.router)

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

