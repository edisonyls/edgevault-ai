from typing import Annotated, NoReturn
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status

from app.core.database import DatabasePoolDep
from app.repositories.uploads import UploadRepository
from app.schemas.uploads import (
    UploadDeleteResponse,
    UploadMetadataResponse,
    UploadMetadataUpdate,
    UploadStatus,
)
from app.services.uploads import (
    UploadConflictError,
    UploadNotFoundError,
    UploadService,
    UploadServiceError,
    UploadValidationError,
)

router = APIRouter(prefix="/uploads", tags=["uploads"])

UPLOAD_READ_CHUNK_SIZE = 1024 * 1024
MAX_UPLOAD_LIST_LIMIT = 500


def get_upload_service(database_pool: DatabasePoolDep) -> UploadService:
    return UploadService(UploadRepository(database_pool))


type UploadServiceDep = Annotated[UploadService, Depends(get_upload_service)]


async def calculate_file_size(file: UploadFile) -> int:
    size = 0

    while chunk := await file.read(UPLOAD_READ_CHUNK_SIZE):
        size += len(chunk)

    return size


def raise_upload_http_exception(exc: UploadServiceError) -> NoReturn:
    if isinstance(exc, UploadValidationError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    if isinstance(exc, UploadNotFoundError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    if isinstance(exc, UploadConflictError):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Unexpected upload service error.",
    ) from exc


@router.post(
    "",
    response_model=UploadMetadataResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_upload_metadata(
    upload_service: UploadServiceDep,
    file: Annotated[UploadFile, File()],
) -> UploadMetadataResponse:
    file_size = await calculate_file_size(file)

    try:
        return await upload_service.create_upload_metadata(
            filename=file.filename,
            content_type=file.content_type,
            file_size=file_size,
        )
    except UploadServiceError as exc:
        raise_upload_http_exception(exc)


@router.get("", response_model=list[UploadMetadataResponse])
async def list_upload_metadata(
    upload_service: UploadServiceDep,
    status_filter: Annotated[UploadStatus | None, Query(alias="status")] = None,
    limit: Annotated[int, Query(ge=1, le=MAX_UPLOAD_LIST_LIMIT)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[UploadMetadataResponse]:
    return await upload_service.list_upload_metadata(
        status_filter=status_filter,
        limit=limit,
        offset=offset,
    )


@router.get("/{upload_id}", response_model=UploadMetadataResponse)
async def get_upload_metadata(
    upload_service: UploadServiceDep,
    upload_id: UUID,
) -> UploadMetadataResponse:
    try:
        return await upload_service.get_upload_metadata(upload_id)
    except UploadServiceError as exc:
        raise_upload_http_exception(exc)


@router.patch("/{upload_id}", response_model=UploadMetadataResponse)
async def update_upload_metadata(
    upload_service: UploadServiceDep,
    upload_id: UUID,
    update: UploadMetadataUpdate,
) -> UploadMetadataResponse:
    try:
        return await upload_service.update_upload_metadata(upload_id, update)
    except UploadServiceError as exc:
        raise_upload_http_exception(exc)


@router.delete(
    "/{upload_id}",
    response_model=UploadDeleteResponse,
    status_code=status.HTTP_200_OK,
)
async def delete_upload_metadata(
    upload_service: UploadServiceDep,
    upload_id: UUID,
) -> UploadDeleteResponse:
    try:
        await upload_service.delete_upload_metadata(upload_id)
    except UploadServiceError as exc:
        raise_upload_http_exception(exc)

    return UploadDeleteResponse(message="Upload deleted successfully.")
