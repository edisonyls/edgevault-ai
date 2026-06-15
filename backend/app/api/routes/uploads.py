from typing import Annotated, NoReturn
from uuid import UUID

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)

from app.core.config import Settings, get_settings
from app.core.database import DatabasePoolDep
from app.repositories.document_extractions import DocumentExtractionRepository
from app.repositories.financial_records import FinancialRecordRepository
from app.repositories.uploads import UploadRepository
from app.schemas.document_extractions import DocumentExtractionResponse
from app.schemas.financial_records import FinancialRecordResponse
from app.schemas.uploads import (
    UploadDeleteResponse,
    UploadMetadataResponse,
    UploadMetadataUpdate,
    UploadStatus,
)
from app.services.document_extraction import DocumentExtractionService
from app.services.financial_extraction import FinancialRecordService
from app.services.ocr.base import OcrEngine
from app.services.ocr.tesseract import TesseractEngine
from app.services.uploads import (
    UploadConflictError,
    UploadNotFoundError,
    UploadService,
    UploadServiceError,
    UploadStorageError,
    UploadValidationError,
)

router = APIRouter(prefix="/uploads", tags=["uploads"])

MAX_UPLOAD_LIST_LIMIT = 500


type SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_upload_service(database_pool: DatabasePoolDep, settings: SettingsDep) -> UploadService:
    return UploadService(UploadRepository(database_pool), settings.upload_storage_dir)


type UploadServiceDep = Annotated[UploadService, Depends(get_upload_service)]


def get_ocr_engine(settings: SettingsDep) -> OcrEngine:
    # Currently using the Tesseract engine but in the future we will swap to Hailo
    return TesseractEngine(language=settings.ocr_language)


def get_financial_record_service(database_pool: DatabasePoolDep) -> FinancialRecordService:
    return FinancialRecordService(FinancialRecordRepository(database_pool))


type FinancialRecordServiceDep = Annotated[
    FinancialRecordService, Depends(get_financial_record_service)
]


# Get the document extraction service.
def get_document_extraction_service(
    database_pool: DatabasePoolDep,
    settings: SettingsDep,
    engine: Annotated[OcrEngine, Depends(get_ocr_engine)],
    financial_record_service: FinancialRecordServiceDep,
) -> DocumentExtractionService:
    return DocumentExtractionService(
        extraction_repository=DocumentExtractionRepository(database_pool),
        upload_repository=UploadRepository(database_pool),
        financial_record_service=financial_record_service,
        engine=engine,
        pdf_text_threshold=settings.ocr_pdf_text_threshold,
        pdf_render_dpi=settings.ocr_pdf_render_dpi,
    )


type DocumentExtractionServiceDep = Annotated[
    DocumentExtractionService, Depends(get_document_extraction_service)
]


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

    if isinstance(exc, UploadStorageError):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
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
    extraction_service: DocumentExtractionServiceDep,
    settings: SettingsDep,
    background_tasks: BackgroundTasks,
    file: Annotated[UploadFile, File()],
) -> UploadMetadataResponse:
    try:
        # First create the upload metadata and store the file
        upload = await upload_service.create_upload(file=file)

        if not settings.ocr_enabled or upload.file_path is None:
            return upload

        # Mark the upload as processing.
        upload = await upload_service.mark_processing(upload.id)

        # Resolve the storage path for the uploaded file.
        storage_path = upload_service.resolve_storage_path(upload.file_path)
    except UploadServiceError as exc:
        raise_upload_http_exception(exc)

    # Kick off the document extraction in the background.
    background_tasks.add_task(
        extraction_service.run,
        upload_id=upload.id,
        storage_path=storage_path,
        mime_type=upload.mime_type,
    )
    return upload


@router.get("", response_model=list[UploadMetadataResponse])
async def list_upload_metadata(
    upload_service: UploadServiceDep,
    status_filter: Annotated[UploadStatus |
                             None, Query(alias="status")] = None,
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


@router.get(
    "/{upload_id}/extractions",
    response_model=list[DocumentExtractionResponse],
)
async def list_document_extractions(
    upload_service: UploadServiceDep,
    extraction_service: DocumentExtractionServiceDep,
    upload_id: UUID,
) -> list[DocumentExtractionResponse]:
    try:
        await upload_service.get_upload_metadata(upload_id)
    except UploadServiceError as exc:
        raise_upload_http_exception(exc)

    return await extraction_service.list_extractions(upload_id)


@router.get(
    "/{upload_id}/financial-record",
    response_model=FinancialRecordResponse,
)
async def get_financial_record(
    upload_service: UploadServiceDep,
    financial_record_service: FinancialRecordServiceDep,
    upload_id: UUID,
) -> FinancialRecordResponse:
    try:
        # Ensure the upload exists before attempting to fetch the financial record.
        await upload_service.get_upload_metadata(upload_id)
    except UploadServiceError as exc:
        raise_upload_http_exception(exc)

    record = await financial_record_service.get_for_upload(upload_id)

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No financial record found for this document.",
        )

    return record


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
