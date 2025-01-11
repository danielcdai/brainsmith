import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment settings for the application."""
    log_level: str
    log_dir: str
    static_dist_path: str
    embeddings_dir: str
    provider: str
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    file_collection_folder: str = "tests/corpus"
    redis_host: str = "localhost"
    redis_port: int = 6379
    
    model_config = SettingsConfigDict(
        env_file=os.environ.get("ENV_FILE_PATH", ".env"),
        env_file_encoding="utf-8",
        env_prefix="",
        extra="allow",
    )
    
    github_client_id: str = os.getenv("github_client_id", "")
    github_client_secret: str = os.getenv("github_secret", "")


settings = Settings()