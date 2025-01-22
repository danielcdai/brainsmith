import logging
import logging.config
import os
from datetime import datetime

from fastapi import FastAPI, HTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.staticfiles import StaticFiles
from starlette.responses import RedirectResponse
from uvicorn.config import LOGGING_CONFIG

from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware 
from cortex.routers import embedding, chunk, search, summarize, auth
from cortex.config import settings

class SPAStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        try:
            return await super().get_response(path, scope)
        except (HTTPException, StarletteHTTPException) as ex:
            if ex.status_code == 404:
                return await super().get_response("index.html", scope)
            else:
                raise ex

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
app.include_router(auth.router)
app.add_middleware(SessionMiddleware, secret_key="brainsmith")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
app.include_router(summarize.router)

# Middleware to log the requests and responses in debug.
@app.middleware("http")
async def log_requests(request, call_next):
    client_host = request.client.host
    log.debug(f"Request: {request.method} {request.url} from {client_host}")
    response = await call_next(request)
    log.debug(f"Response status: {response.status_code} for {client_host}")
    return response


# Export the UI build as static files, served under /ui path.
app.mount("/ui", SPAStaticFiles(directory=settings.static_dist_path, html=True), name="ui")


