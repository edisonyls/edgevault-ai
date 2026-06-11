from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class UploadMetadataResponse(BaseModel):
    id: UUID
    original_filename: str
    display_filename: str
    stored_filename: str
    file_path: str | None
    mime_type: str
    file_size: int
    status: str
    created_at: datetime
    updated_at: datetime
