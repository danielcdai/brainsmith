import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment settings for the application."""
    log_level: str
    log_dir: str
    static_dist_path: str
    embeddings_dir: str
    upload_folder: str
    provider: str
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    file_collection_folder: str = "tests/corpus"
    redis_host: str = "localhost"
    redis_port: int = 6379
    postgre_host: str = "localhost"
    postgre_port: int = 5432
    postgres_password: str
    github_client_id: str
    github_client_secret: str 
    secret_key: str                  # For signing your own JWT
    algorithm: str = "HS256"         # JWT signing algorithm
    redirect_uri: str = "http://localhost:8000/auth/github/callback"
    frontend_url: str = "http://localhost:5173"
    jwt_expires_in: str = "1h"

    model_config = SettingsConfigDict(
        env_file=os.environ.get("ENV_FILE_PATH", ".env"),
        env_file_encoding="utf-8",
        env_prefix="",
        extra="allow",
    )
    

# Load the project settings
settings = Settings()


# OAuth settings
OAUTH_PROVIDERS = {}


def load_oauth_providers():
    OAUTH_PROVIDERS.clear()
    # Only GitHub OAuth is supported for now, google and microsoft are commented out.
    # if GOOGLE_CLIENT_ID.value and GOOGLE_CLIENT_SECRET.value:

    #     def google_oauth_register(client):
    #         client.register(
    #             name="google",
    #             client_id=GOOGLE_CLIENT_ID.value,
    #             client_secret=GOOGLE_CLIENT_SECRET.value,
    #             server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    #             client_kwargs={"scope": GOOGLE_OAUTH_SCOPE.value},
    #             redirect_uri=GOOGLE_REDIRECT_URI.value,
    #         )

    #     OAUTH_PROVIDERS["google"] = {
    #         "redirect_uri": GOOGLE_REDIRECT_URI.value,
    #         "register": google_oauth_register,
    #     }

    # if (
    #     MICROSOFT_CLIENT_ID.value
    #     and MICROSOFT_CLIENT_SECRET.value
    #     and MICROSOFT_CLIENT_TENANT_ID.value
    # ):

    #     def microsoft_oauth_register(client):
    #         client.register(
    #             name="microsoft",
    #             client_id=MICROSOFT_CLIENT_ID.value,
    #             client_secret=MICROSOFT_CLIENT_SECRET.value,
    #             server_metadata_url=f"https://login.microsoftonline.com/{MICROSOFT_CLIENT_TENANT_ID.value}/v2.0/.well-known/openid-configuration",
    #             client_kwargs={
    #                 "scope": MICROSOFT_OAUTH_SCOPE.value,
    #             },
    #             redirect_uri=MICROSOFT_REDIRECT_URI.value,
    #         )

    #     OAUTH_PROVIDERS["microsoft"] = {
    #         "redirect_uri": MICROSOFT_REDIRECT_URI.value,
    #         "picture_url": "https://graph.microsoft.com/v1.0/me/photo/$value",
    #         "register": microsoft_oauth_register,
    #     }

    if settings.github_client_id and settings.github_client_secret:
        GITHUB_CLIENT_SCOPE = "user:email"
        # TODO: change it to github_redirect_uri later
        GITHUB_CLIENT_REDIRECT_URI = settings.redirect_uri

        def github_oauth_register(client):
            client.register(
                name="github",
                client_id=settings.github_client_id,
                client_secret=settings.github_client_secret,
                access_token_url="https://github.com/login/oauth/access_token",
                authorize_url="https://github.com/login/oauth/authorize",
                api_base_url="https://api.github.com",
                userinfo_endpoint="https://api.github.com/user",
                client_kwargs={"scope": GITHUB_CLIENT_SCOPE},
                redirect_uri=GITHUB_CLIENT_REDIRECT_URI,
            )

        OAUTH_PROVIDERS["github"] = {
            "redirect_uri": GITHUB_CLIENT_REDIRECT_URI,
            "register": github_oauth_register,
            "sub_claim": "id",
        }


load_oauth_providers()