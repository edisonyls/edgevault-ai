from functools import lru_cache
from pathlib import Path
from typing import Literal

from dotenv import find_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["local", "development", "staging", "production"]
DATABASE_POOL_MIN_SIZE = 1
DATABASE_POOL_MAX_SIZE = 5
OCR_PDF_TEXT_THRESHOLD = 20
OCR_PDF_RENDER_DPI = 200


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

    model_config = SettingsConfigDict(
        env_file=find_dotenv(usecwd=True) or None,
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
