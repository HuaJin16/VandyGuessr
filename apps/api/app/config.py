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

    # Microsoft OAuth
    microsoft_client_id: str = ""
    microsoft_tenant_id: str = "common"
    microsoft_algorithms: str = "RS256"

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
    def microsoft_jwks_url(self) -> str:
        """Get the JWKS URL for Microsoft OAuth."""
        return f"https://login.microsoftonline.com/{self.microsoft_tenant_id}/discovery/v2.0/keys"

    @property
    def microsoft_issuer(self) -> str:
        """Get the issuer URL for Microsoft OAuth."""
        return f"https://login.microsoftonline.com/{self.microsoft_tenant_id}/v2.0"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
