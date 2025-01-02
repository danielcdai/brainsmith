from pydantic_settings import BaseSettings, SettingsConfigDict
import os


class Settings(BaseSettings):
    """Environment settings for the application."""
    server_port: int
    log_level: str
    log_dir: str
    static_dist_path: str
    embeddings_dir: str
    provider: str
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    model_config = SettingsConfigDict(
        env_file=os.environ.get("ENV_FILE_PATH", ".env"),
        env_file_encoding="utf-8",
        env_prefix="",
        extra="allow",
    )


settings = Settings()