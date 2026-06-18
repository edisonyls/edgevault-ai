from functools import lru_cache
from pathlib import Path
from typing import Literal, Self

from dotenv import find_dotenv
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# General app settings
APP_NAME = "EdgeVault AI API"
APP_VERSION = "1.0.0"
DEBUG = False
API_PREFIX = "/api"
Environment = Literal["local", "development", "staging", "production"]
UPLOAD_STORAGE_DIR = Path("var/uploads")
AUTH_SESSION_COOKIE_NAME = "edgevault_ai_session"
AUTH_COOKIE_SAMESITE = "lax"
EMBEDDING_PROVIDER = "fastembed"

# Database pool sizes
DATABASE_POOL_MIN_SIZE = 1
DATABASE_POOL_MAX_SIZE = 5
# We expect at least 20 extracted text characters per page before trusting the
# PDF’s built-in text layer.
OCR_PDF_TEXT_THRESHOLD = 20
OCR_PDF_RENDER_DPI = 200
EMBEDDING_DIMENSION = 384
EMBEDDING_CHUNK_SIZE = 1500
EMBEDDING_CHUNK_OVERLAP = 150
# The default timeout value for assistant LLM calls.
ASSISTANT_LLM_TIMEOUT = 30.0
# How often to ping the local assistant LLM to keep it warm
ASSISTANT_LLM_KEEP_WARM_INTERVAL = 300.0
ALLOWED_ORIGINS = ["*"]
# Whether the authentication cookie should be marked as secure.
AUTH_COOKIE_SECURE = False
# The TTL for authentication sessions default to 7 days.
AUTH_SESSION_TTL_SECONDS = 60 * 60 * 24 * 7


class Settings(BaseSettings):
    app_name: str = APP_NAME
    app_version: str = APP_VERSION
    environment: Environment = Field(
        default="development",
        validation_alias="NODE_ENV",
    )
    debug: bool = DEBUG
    api_prefix: str = API_PREFIX
    allowed_origins: list[str] = ALLOWED_ORIGINS
    database_url: str
    database_pool_min_size: int = DATABASE_POOL_MIN_SIZE
    database_pool_max_size: int = DATABASE_POOL_MAX_SIZE
    upload_storage_dir: Path = UPLOAD_STORAGE_DIR
    ocr_engine: str = "tesseract"
    ocr_pdf_text_threshold: int = OCR_PDF_TEXT_THRESHOLD
    ocr_pdf_render_dpi: int = OCR_PDF_RENDER_DPI
    embeddings_enabled: bool = True
    embedding_provider: str = EMBEDDING_PROVIDER
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_dimension: int = EMBEDDING_DIMENSION
    embedding_chunk_size: int = EMBEDDING_CHUNK_SIZE
    embedding_chunk_overlap: int = EMBEDDING_CHUNK_OVERLAP
    assistant_llm_base_url: str = "http://localhost:8000/v1"
    assistant_llm_model: str
    assistant_llm_timeout: float = ASSISTANT_LLM_TIMEOUT
    assistant_llm_keep_warm: bool = True
    assistant_llm_keep_warm_interval: float = ASSISTANT_LLM_KEEP_WARM_INTERVAL
    assistant_fallback_enabled: bool = False
    assistant_fallback_base_url: str = "https://api.deepseek.com"
    assistant_fallback_model: str = "DeepSeek-V4-Flash"
    assistant_fallback_api_key: str | None = Field(
        default=None, validation_alias="DEEPSEEK_API_KEY"
    )
    assistant_fallback_timeout: float = 30.0
    auth_owner_password: str
    auth_demo_password: str
    auth_session_secret: str
    auth_session_cookie_name: str = AUTH_SESSION_COOKIE_NAME
    auth_session_ttl_seconds: int = AUTH_SESSION_TTL_SECONDS
    auth_cookie_secure: bool = AUTH_COOKIE_SECURE
    auth_cookie_samesite: str = AUTH_COOKIE_SAMESITE

    @field_validator(
        "assistant_fallback_enabled",
        "auth_cookie_secure",
        mode="before",
    )
    @classmethod
    def _blank_is_disabled(cls, value: object) -> object:
        if isinstance(value, str) and value.strip() == "":
            return False
        return value

    @field_validator("auth_cookie_samesite", mode="before")
    @classmethod
    def _blank_samesite_is_lax(cls, value: object) -> object:
        if isinstance(value, str) and value.strip() == "":
            return "lax"
        return value

    @field_validator(
        "auth_owner_password",
        "auth_demo_password",
        "auth_session_secret",
        mode="before",
    )
    @classmethod
    def _blank_is_none(cls, value: object) -> object:
        if isinstance(value, str) and value.strip() == "":
            return None
        return value

    @model_validator(mode="after")
    def _production_auth_secrets_required(self) -> Self:
        if self.environment != "production":
            return self

        missing = [
            name
            for name, value in (
                ("AUTH_OWNER_PASSWORD", self.auth_owner_password),
                ("AUTH_DEMO_PASSWORD", self.auth_demo_password),
                ("AUTH_SESSION_SECRET", self.auth_session_secret),
            )
            if not value
        ]
        if missing:
            raise ValueError(
                f"Missing required production auth settings: {', '.join(missing)}."
            )

        return self

    model_config = SettingsConfigDict(
        env_file=find_dotenv(usecwd=True) or None,
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
