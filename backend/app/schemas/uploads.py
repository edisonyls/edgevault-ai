from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

UploadStatus = Literal["uploaded", "extracting",
                       "indexing", "processed", "failed"]


class UploadMetadataResponse(BaseModel):
    id: UUID
    text: str | None
    original_filename: str
    display_filename: str
    stored_filename: str
    file_path: str | None
    mime_type: str
    file_size: int
    status: UploadStatus
    created_at: datetime
    updated_at: datetime


class UploadMetadataUpdate(BaseModel):
    display_filename: str | None = Field(default=None, max_length=255)
    status: UploadStatus | None = None
    text: str | None = None


class UploadDeleteResponse(BaseModel):
    message: str
