from pathlib import PurePath
from typing import Annotated
from uuid import uuid4

from asyncpg import Record
from asyncpg.exceptions import UniqueViolationError
from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.core.database import DatabasePoolDep
from app.schemas.uploads import UploadMetadataResponse

router = APIRouter(prefix="/uploads", tags=["uploads"])

MAX_FILENAME_LENGTH = 255
UPLOAD_READ_CHUNK_SIZE = 1024 * 1024
DEFAULT_MIME_TYPE = "application/octet-stream"
MAX_DISPLAY_FILENAME_ATTEMPTS = 10_000


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


def build_display_filename(original_filename: str, duplicate_index: int) -> str:
    if duplicate_index == 0:
        return original_filename

    suffix = f" ({duplicate_index})"
    path = PurePath(original_filename)
    extension = path.suffix
    stem = path.stem if extension else original_filename

    if len(extension) + len(suffix) >= MAX_FILENAME_LENGTH:
        extension = extension[-(MAX_FILENAME_LENGTH - len(suffix) - 1):]

    max_stem_length = max(1, MAX_FILENAME_LENGTH - len(extension) - len(suffix))
    return f"{stem[:max_stem_length]}{suffix}{extension}"


async def calculate_file_size(file: UploadFile) -> int:
    size = 0

    while chunk := await file.read(UPLOAD_READ_CHUNK_SIZE):
        size += len(chunk)

    return size


def row_to_upload_metadata(row: Record) -> UploadMetadataResponse:
    return UploadMetadataResponse(
        id=row["id"],
        original_filename=row["original_filename"],
        display_filename=row["display_filename"],
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
        for duplicate_index in range(MAX_DISPLAY_FILENAME_ATTEMPTS):
            display_filename = build_display_filename(original_filename, duplicate_index)

            try:
                row = await connection.fetchrow(
                    """
                    INSERT INTO resume_uploads (
                        original_filename,
                        display_filename,
                        stored_filename,
                        file_path,
                        mime_type,
                        file_size
                    )
                    VALUES ($1, $2, $3, $4, $5, $6)
                    RETURNING
                        id,
                        original_filename,
                        display_filename,
                        stored_filename,
                        file_path,
                        mime_type,
                        file_size,
                        status,
                        created_at,
                        updated_at
                    """,
                    original_filename,
                    display_filename,
                    stored_filename,
                    None,
                    mime_type,
                    file_size,
                )
                break
            except UniqueViolationError as exc:
                if exc.constraint_name != "idx_resume_uploads_display_filename":
                    raise
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Unable to generate a unique display filename.",
            )

    return row_to_upload_metadata(row)
