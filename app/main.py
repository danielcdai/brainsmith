from fastapi import FastAPI
import uvicorn
from fastapi.staticfiles import StaticFiles
from pydantic_settings import BaseSettings
from typing import List

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}


class Settings(BaseSettings):
    server_port: int

    class Config:
        env_file = ".env"

settings = Settings()

# UI dist folder is mounted at /static
# app.mount("/static", StaticFiles(directory="static/dist"), name="static")

@app.get("/zones", response_model=List[str])
def get_zones():
    # TODO: This is a placeholder. Replace with actual logic to get zone names.
    return ["Zone1", "Zone2", "Zone3"]

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=settings.server_port)