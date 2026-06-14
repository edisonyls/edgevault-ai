from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

ExtractionMethod = Literal["pdf_text_layer", "ocr"]
ExtractionStatus = Literal["succeeded", "failed"]


class DocumentExtractionResponse(BaseModel):
    id: UUID
    upload_id: UUID
    raw_text: str | None
    ocr_engine: str
    ocr_engine_version: str | None
    extraction_method: ExtractionMethod | None
    ocr_confidence: float | None
    page_count: int | None
    processing_latency_ms: int
    status: ExtractionStatus
    error_message: str | None
    created_at: datetime
