from pathlib import PurePath
from uuid import UUID, uuid4

from asyncpg import Record

from app.repositories.uploads import UniqueDisplayFilenameError, UploadRepository
from app.schemas.uploads import UploadMetadataResponse, UploadMetadataUpdate, UploadStatus

MAX_FILENAME_LENGTH = 255
DEFAULT_MIME_TYPE = "application/octet-stream"
MAX_DISPLAY_FILENAME_ATTEMPTS = 10_000


class UploadServiceError(Exception):
    pass


class UploadValidationError(UploadServiceError):
    pass


class UploadNotFoundError(UploadServiceError):
    pass


class UploadConflictError(UploadServiceError):
    pass


def clean_original_filename(filename: str | None) -> str:
    if filename is None:
        raise UploadValidationError("Uploaded file must include a filename.")

    clean_filename = PurePath(filename).name.strip()
    if not clean_filename:
        raise UploadValidationError("Uploaded file must include a filename.")

    if len(clean_filename) > MAX_FILENAME_LENGTH:
        raise UploadValidationError(f"Filename must be {MAX_FILENAME_LENGTH} characters or fewer.")

    return clean_filename


def clean_display_filename(filename: str | None) -> str:
    if filename is None:
        raise UploadValidationError("Display filename cannot be null.")

    clean_filename = PurePath(filename).name.strip()
    if not clean_filename:
        raise UploadValidationError("Display filename cannot be empty.")

    if len(clean_filename) > MAX_FILENAME_LENGTH:
        raise UploadValidationError(
            f"Display filename must be {MAX_FILENAME_LENGTH} characters or fewer."
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
        extension = extension[-(MAX_FILENAME_LENGTH - len(suffix) - 1) :]

    max_stem_length = max(1, MAX_FILENAME_LENGTH - len(extension) - len(suffix))
    return f"{stem[:max_stem_length]}{suffix}{extension}"


def row_to_upload_metadata(row: Record) -> UploadMetadataResponse:
    return UploadMetadataResponse(
        id=row["id"],
        text=row["text"],
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


class UploadService:
    def __init__(self, upload_repository: UploadRepository) -> None:
        self.upload_repository = upload_repository

    async def create_upload_metadata(
        self,
        *,
        filename: str | None,
        content_type: str | None,
        file_size: int,
    ) -> UploadMetadataResponse:
        original_filename = clean_original_filename(filename)
        stored_filename = build_stored_filename(original_filename)
        mime_type = content_type or DEFAULT_MIME_TYPE

        for duplicate_index in range(MAX_DISPLAY_FILENAME_ATTEMPTS):
            display_filename = build_display_filename(original_filename, duplicate_index)

            try:
                row = await self.upload_repository.create(
                    original_filename=original_filename,
                    display_filename=display_filename,
                    stored_filename=stored_filename,
                    file_path=None,
                    mime_type=mime_type,
                    file_size=file_size,
                )
                return row_to_upload_metadata(row)
            except UniqueDisplayFilenameError:
                continue

        raise UploadConflictError("Unable to generate a unique display filename.")

    async def list_upload_metadata(
        self,
        *,
        status_filter: UploadStatus | None,
        limit: int,
        offset: int,
    ) -> list[UploadMetadataResponse]:
        rows = await self.upload_repository.list(
            status_filter=status_filter,
            limit=limit,
            offset=offset,
        )
        return [row_to_upload_metadata(row) for row in rows]

    async def get_upload_metadata(self, upload_id: UUID) -> UploadMetadataResponse:
        row = await self.upload_repository.get(upload_id)

        if row is None:
            raise UploadNotFoundError("Upload not found.")

        return row_to_upload_metadata(row)

    async def update_upload_metadata(
        self,
        upload_id: UUID,
        update: UploadMetadataUpdate,
    ) -> UploadMetadataResponse:
        update_data = update.model_dump(exclude_unset=True)

        if not update_data:
            raise UploadValidationError("At least one field must be provided.")

        if "display_filename" in update_data:
            update_data["display_filename"] = clean_display_filename(update.display_filename)

        if "status" in update_data and update.status is None:
            raise UploadValidationError("Status cannot be null.")

        try:
            row = await self.upload_repository.update(upload_id, update_data)
        except UniqueDisplayFilenameError as exc:
            raise UploadConflictError("Display filename already exists.") from exc

        if row is None:
            raise UploadNotFoundError("Upload not found.")

        return row_to_upload_metadata(row)

    async def delete_upload_metadata(self, upload_id: UUID) -> None:
        deleted = await self.upload_repository.delete(upload_id)

        if not deleted:
            raise UploadNotFoundError("Upload not found.")
