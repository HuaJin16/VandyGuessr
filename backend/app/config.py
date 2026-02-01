"""Application configuration using Pydantic Settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_name: str = "VandyGuessr API"
    debug: bool = False

    # Server
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    backend_reload: bool = False

    # MongoDB
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_database: str = "vandyguessr"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Auth0
    auth0_domain: str = ""
    auth0_api_audience: str = ""
    auth0_issuer: str = ""
    auth0_algorithms: str = "RS256"

    # CORS
    cors_origins: list[str] = ["http://localhost:5173"]

    # Upload
    upload_secret_code: str = ""
    upload_max_bytes: int = 50 * 1024 * 1024

    # DigitalOcean Spaces (S3-compatible)
    spaces_region: str = ""
    spaces_endpoint: str = ""
    spaces_bucket: str = ""
    spaces_access_key: str = ""
    spaces_secret_key: str = ""

    @property
    def auth0_jwks_url(self) -> str:
        """Get the JWKS URL for Auth0."""
        return f"https://{self.auth0_domain}/.well-known/jwks.json"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
