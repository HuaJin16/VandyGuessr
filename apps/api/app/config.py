"""Application configuration using Pydantic Settings."""

from functools import lru_cache

from pydantic import Field
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

    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    google_algorithms: str = "RS256"

    # CORS
    cors_origins: list[str] = ["http://localhost:5173"]

    # Upload
    upload_secret_code: str = ""
    upload_max_bytes: int = 50 * 1024 * 1024
    upload_max_dimension: int = Field(default=17000, ge=1024, le=65535)
    upload_max_pixels: int = Field(default=70_000_000, ge=1_000_000, le=500_000_000)
    upload_max_projected_full_width: int = Field(default=17000, ge=1024, le=65535)
    upload_queue_key: str = "images:submission:queue"
    upload_queue_max_attempts: int = Field(default=3, ge=1, le=10)
    upload_temp_prefix: str = "images/uploads-temp"

    # Image processing
    panorama_base_max_width: int = Field(default=2048, ge=512, le=8192)
    panorama_max_source_width: int = Field(default=16384, ge=1024, le=32768)
    panorama_base_quality: int = Field(default=60, ge=1, le=95)
    panorama_tile_quality: int = Field(default=80, ge=1, le=95)
    image_original_jpeg_quality: int = Field(default=84, ge=1, le=95)
    image_original_min_savings_ratio: float = Field(default=0.08, ge=0.0, le=1.0)

    # Comma-separated @vanderbilt.edu emails allowed to approve/reject crowd submissions
    reviewer_email_allowlist: str = ""

    # Feature flags
    feature_multiplayer: bool = False
    feature_vanderbilt_restricted_logins: bool = True

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

    @property
    def google_jwks_url(self) -> str:
        return "https://www.googleapis.com/oauth2/v3/certs"

    @property
    def google_issuers(self) -> list[str]:
        return ["accounts.google.com", "https://accounts.google.com"]

    @property
    def reviewer_emails(self) -> list[str]:
        raw = self.reviewer_email_allowlist.strip()
        if not raw:
            return []
        return [p.strip() for p in raw.split(",") if p.strip()]


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
