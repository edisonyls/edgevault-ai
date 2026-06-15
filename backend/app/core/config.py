from functools import lru_cache
from pathlib import Path
from typing import Literal

from dotenv import find_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["local", "development", "staging", "production"]
DATABASE_POOL_MIN_SIZE = 1
DATABASE_POOL_MAX_SIZE = 5
OCR_PDF_TEXT_THRESHOLD = 20
OCR_PDF_RENDER_DPI = 200
EMBEDDING_DIMENSION = 384
EMBEDDING_CHUNK_SIZE = 1500
EMBEDDING_CHUNK_OVERLAP = 150


class Settings(BaseSettings):
    app_name: str = "EdgeVault AI API"
    app_version: str = "0.1.0"
    environment: Environment = Field(
        default="development",
        validation_alias="NODE_ENV",
    )
    debug: bool = False
    api_prefix: str = "/api"
    allowed_origins: list[str] = ["http://localhost:3000"]
    database_url: str
    database_pool_min_size: int = DATABASE_POOL_MIN_SIZE
    database_pool_max_size: int = DATABASE_POOL_MAX_SIZE
    upload_storage_dir: Path = Path("var/uploads")
    ocr_enabled: bool = True
    ocr_engine: str = "tesseract"
    ocr_language: str = "eng"
    ocr_pdf_text_threshold: int = OCR_PDF_TEXT_THRESHOLD
    ocr_pdf_render_dpi: int = OCR_PDF_RENDER_DPI
    embeddings_enabled: bool = True
    embedding_provider: str = "fastembed"
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_dimension: int = EMBEDDING_DIMENSION
    embedding_chunk_size: int = EMBEDDING_CHUNK_SIZE
    embedding_chunk_overlap: int = EMBEDDING_CHUNK_OVERLAP
    assistant_llm_enabled: bool = False
    assistant_llm_base_url: str = "http://localhost:8000/v1"
    assistant_llm_model: str = "qwen2.5-instruct:1.5b"
    assistant_llm_timeout: float = 30.0
    assistant_llm_keep_warm: bool = True
    assistant_llm_keep_warm_interval: float = 240.0
    assistant_fallback_enabled: bool = False
    assistant_fallback_base_url: str = "https://api.deepseek.com"
    assistant_fallback_model: str = "DeepSeek-V4-Flash"
    assistant_fallback_api_key: str | None = Field(
        default=None, validation_alias="DEEPSEEK_API_KEY"
    )
    assistant_fallback_timeout: float = 30.0

    @field_validator("assistant_llm_enabled", "assistant_fallback_enabled", mode="before")
    @classmethod
    def _blank_is_disabled(cls, value: object) -> object:
        if isinstance(value, str) and value.strip() == "":
            return False
        return value

    model_config = SettingsConfigDict(
        env_file=find_dotenv(usecwd=True) or None,
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
