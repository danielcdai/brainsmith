from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Environment settings for the application."""
    server_port: int
    log_level: str = "INFO"
    log_dir: str = "logs"
    static_dist_path: str = "ui/build"
    embeddings_dir: str = "embedding_results"

    class Config:
        # TODO: Load the env file path from an environment variable.
        env_file = ".env"

settings = Settings()