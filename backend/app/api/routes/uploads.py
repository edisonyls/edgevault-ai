from pathlib import PurePath
from typing import Annotated
from uuid import uuid4

from asyncpg import Record
from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.core.database import DatabasePoolDep
from app.schemas.uploads import UploadMetadataResponse

router = APIRouter(prefix="/uploads", tags=["uploads"])

MAX_FILENAME_LENGTH = 255
UPLOAD_READ_CHUNK_SIZE = 1024 * 1024
DEFAULT_MIME_TYPE = "application/octet-stream"


def clean_original_filename(filename: str | None) -> str:
    if filename is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must include a filename.",
        )

    clean_filename = PurePath(filename).name.strip()
    if not clean_filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must include a filename.",
        )

    if len(clean_filename) > MAX_FILENAME_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Filename must be {MAX_FILENAME_LENGTH} characters or fewer.",
        )

    return clean_filename


def build_stored_filename(original_filename: str) -> str:
    suffix = PurePath(original_filename).suffix[:32]
    return f"{uuid4()}{suffix}"


async def calculate_file_size(file: UploadFile) -> int:
    size = 0

    while chunk := await file.read(UPLOAD_READ_CHUNK_SIZE):
        size += len(chunk)

    return size


def row_to_upload_metadata(row: Record) -> UploadMetadataResponse:
    return UploadMetadataResponse(
        id=row["id"],
        original_filename=row["original_filename"],
        stored_filename=row["stored_filename"],
        file_path=row["file_path"],
        mime_type=row["mime_type"],
        file_size=row["file_size"],
        status=row["status"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


@router.post(
    "",
    response_model=UploadMetadataResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_upload_metadata(
    database_pool: DatabasePoolDep,
    file: Annotated[UploadFile, File()],
) -> UploadMetadataResponse:
    original_filename = clean_original_filename(file.filename)
    stored_filename = build_stored_filename(original_filename)
    mime_type = file.content_type or DEFAULT_MIME_TYPE
    file_size = await calculate_file_size(file)

    async with database_pool.acquire() as connection:
        row = await connection.fetchrow(
            """
            INSERT INTO resume_uploads (
                original_filename,
                stored_filename,
                file_path,
                mime_type,
                file_size
            )
            VALUES ($1, $2, $3, $4, $5)
            RETURNING
                id,
                original_filename,
                stored_filename,
                file_path,
                mime_type,
                file_size,
                status,
                created_at,
                updated_at
            """,
            original_filename,
            stored_filename,
            None,
            mime_type,
            file_size,
        )

    return row_to_upload_metadata(row)
