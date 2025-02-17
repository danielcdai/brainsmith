from fastapi import FastAPI, HTTPException, Request
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.staticfiles import StaticFiles

from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from cortex.routers import embedding, chunk, search, summarize, auth, oauth, files
from cortex.config import settings
from cortex.middleware import log_requests


class SPAStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        try:
            return await super().get_response(path, scope)
        except (HTTPException, StarletteHTTPException) as ex:
            if ex.status_code == 404:
                return await super().get_response("index.html", scope)
            else:
                raise ex


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
app.include_router(summarize.router)
app.include_router(oauth.router)
app.include_router(files.router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
app.add_middleware(BaseHTTPMiddleware, dispatch=log_requests)


def verify_bearer_token(request: Request):
    from cortex.admin.authenticate import verify_jwt
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            return verify_jwt(token)
        except ValueError as e:
            raise HTTPException(status_code=401, detail=str(e))
    else:
        raise HTTPException(status_code=401, detail="Invalid or missing token")


# Export the UI build as static files, served under /ui path.
# app.mount("/ui", SPAStaticFiles(directory=settings.static_dist_path, html=True), name="ui")


# Redirect the root path to the UI.
# For development, simply comment this out.
# @app.get("/")
# async def root():
#     return RedirectResponse(url="/ui")