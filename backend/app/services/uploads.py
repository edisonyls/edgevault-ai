import asyncio
from contextlib import suppress
from datetime import UTC, datetime
from pathlib import Path, PurePath, PurePosixPath
from uuid import UUID, uuid4

from asyncpg import Record
from fastapi import UploadFile

from app.repositories.uploads import UniqueDisplayFilenameError, UploadRepository
from app.schemas.uploads import UploadMetadataResponse, UploadMetadataUpdate, UploadStatus

MAX_FILENAME_LENGTH = 255
# This is the IANA/RFC-defined meaning of "arbitrary bytes of unknown type."
DEFAULT_MIME_TYPE = "application/octet-stream"
MAX_DISPLAY_FILENAME_ATTEMPTS = 10_000
UPLOAD_READ_CHUNK_SIZE = 1024 * 1024


class UploadServiceError(Exception):
    pass


class UploadValidationError(UploadServiceError):
    pass


class UploadNotFoundError(UploadServiceError):
    pass


class UploadConflictError(UploadServiceError):
    pass


class UploadStorageError(UploadServiceError):
    pass


# Clean and validate the original filename.
def clean_original_filename(filename: str | None) -> str:
    if filename is None:
        raise UploadValidationError("Uploaded file must include a filename.")

    clean_filename = PurePath(filename).name.strip()
    if not clean_filename:
        raise UploadValidationError("Uploaded file must include a filename.")

    if len(clean_filename) > MAX_FILENAME_LENGTH:
        raise UploadValidationError(
            f"Filename must be {MAX_FILENAME_LENGTH} characters or fewer.")

    return clean_filename


# Clean and validate the display filename.
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


# Build a unique stored filename using a UUID and the original file extension
def build_stored_filename(original_filename: str) -> str:
    suffix = PurePath(original_filename).suffix[:32]
    return f"{uuid4()}{suffix}"


# Build the file path for storing the uploaded file using a date_based directory structure
def build_file_path(stored_filename: str) -> str:
    now = datetime.now(UTC)
    return PurePosixPath(
        str(now.year),
        f"{now.month:02}",
        f"{now.day:02}",
        stored_filename,
    ).as_posix()


# Build the display filename and add a suffix if found a duplicate
def build_display_filename(original_filename: str, duplicate_index: int) -> str:
    if duplicate_index == 0:
        return original_filename

    suffix = f" ({duplicate_index})"
    path = PurePath(original_filename)
    extension = path.suffix
    stem = path.stem if extension else original_filename

    if len(extension) + len(suffix) >= MAX_FILENAME_LENGTH:
        extension = extension[-(MAX_FILENAME_LENGTH - len(suffix) - 1):]

    max_stem_length = max(1, MAX_FILENAME_LENGTH -
                          len(extension) - len(suffix))
    return f"{stem[:max_stem_length]}{suffix}{extension}"


# Convert a DB record to the upload metadata response model
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
    def __init__(self, upload_repository: UploadRepository, upload_storage_dir: Path) -> None:
        self.upload_repository = upload_repository
        self.upload_storage_dir = upload_storage_dir

    # Resolve the storage path for a given file path
    def resolve_storage_path(self, file_path: str) -> Path:
        relative_path = PurePosixPath(file_path)

        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise UploadStorageError("Stored file path is invalid.")

        return self.upload_storage_dir.joinpath(*relative_path.parts)

    # Save the uploaded file to disk at the resolved storage path and return the
    # file size.
    async def save_uploaded_file(self, file: UploadFile, file_path: str) -> int:
        storage_path = self.resolve_storage_path(file_path)
        temp_path = storage_path.with_name(
            f".{storage_path.name}.{uuid4()}.tmp")
        file_size = 0
        handle = None

        try:
            await asyncio.to_thread(storage_path.parent.mkdir, parents=True, exist_ok=True)
            handle = await asyncio.to_thread(temp_path.open, "xb")

            # Streams the uploaded file to disk in fixed-size byte blocks instead
            # of loading the whole thing into memory at once.
            while chunk := await file.read(UPLOAD_READ_CHUNK_SIZE):
                file_size += len(chunk)
                await asyncio.to_thread(handle.write, chunk)

            await asyncio.to_thread(handle.close)
            handle = None
            await asyncio.to_thread(temp_path.replace, storage_path)
        except OSError as exc:
            raise UploadStorageError("Unable to store uploaded file.") from exc
        finally:
            if handle is not None:
                await asyncio.to_thread(handle.close)
            with suppress(OSError):
                await asyncio.to_thread(temp_path.unlink)

        return file_size

    async def delete_stored_file(self, file_path: str | None) -> None:
        if file_path is None:
            return

        storage_path = self.resolve_storage_path(file_path)

        try:
            await asyncio.to_thread(storage_path.unlink)
        except FileNotFoundError:
            return
        except OSError as exc:
            raise UploadStorageError("Unable to delete stored file.") from exc

    # Create a new upload metadata in the DB and save the file to disk
    async def create_upload(
        self,
        *,
        file: UploadFile,
    ) -> UploadMetadataResponse:
        original_filename = clean_original_filename(file.filename)
        stored_filename = build_stored_filename(original_filename)
        file_path = build_file_path(stored_filename)
        mime_type = file.content_type or DEFAULT_MIME_TYPE
        file_saved = False
        created_row: Record | None = None

        try:
            # Save the uploaded file to disk and get the size.
            file_size = await self.save_uploaded_file(file, file_path)
            file_saved = True

            for duplicate_index in range(MAX_DISPLAY_FILENAME_ATTEMPTS):
                display_filename = build_display_filename(
                    original_filename, duplicate_index)

                try:
                    # Create the uploaded file's metadata in the DB
                    row = await self.upload_repository.create(
                        original_filename=original_filename,
                        display_filename=display_filename,
                        stored_filename=stored_filename,
                        file_path=file_path,
                        mime_type=mime_type,
                        file_size=file_size,
                    )
                    break
                except UniqueDisplayFilenameError:
                    continue

            if row is None:
                raise UploadConflictError(
                    "Unable to generate a unique display filename.")
        except Exception:
            if file_saved:
                with suppress(UploadStorageError):
                    await self.delete_stored_file(file_path)
            raise

        return row_to_upload_metadata(row)

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
            update_data["display_filename"] = clean_display_filename(
                update.display_filename)

        if "status" in update_data and update.status is None:
            raise UploadValidationError("Status cannot be null.")

        try:
            row = await self.upload_repository.update(upload_id, update_data)
        except UniqueDisplayFilenameError as exc:
            raise UploadConflictError(
                "Display filename already exists.") from exc

        if row is None:
            raise UploadNotFoundError("Upload not found.")

        return row_to_upload_metadata(row)

    async def delete_upload_metadata(self, upload_id: UUID) -> None:
        existing = await self.upload_repository.get(upload_id)

        if existing is None:
            raise UploadNotFoundError("Upload not found.")

        deleted = await self.upload_repository.delete(upload_id)

        if not deleted:
            raise UploadNotFoundError("Upload not found.")

        await self.delete_stored_file(existing["file_path"])
