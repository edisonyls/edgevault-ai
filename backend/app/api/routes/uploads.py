import json
from typing import Annotated, NoReturn
from uuid import UUID

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)
from sse_starlette.sse import EventSourceResponse

from app.core.auth import CurrentWorkspaceDep
from app.core.config import Settings, get_settings
from app.core.database import DatabasePoolDep
from app.core.events import UploadEventBus, get_upload_event_bus
from app.repositories.document_embeddings import DocumentEmbeddingRepository
from app.repositories.document_extractions import DocumentExtractionRepository
from app.repositories.document_type_rules import DocumentTypeRuleRepository
from app.repositories.extraction_corrections import ExtractionCorrectionRepository
from app.repositories.financial_records import FinancialRecordRepository
from app.repositories.uploads import UploadRepository
from app.repositories.vendor_rules import VendorRuleRepository
from app.schemas.document_extractions import DocumentExtractionResponse
from app.schemas.financial_records import FinancialRecordResponse
from app.schemas.uploads import (
    UploadDeleteResponse,
    UploadMetadataResponse,
    UploadMetadataUpdate,
    UploadStatus,
)
from app.services.document_extraction import DocumentExtractionService
from app.services.embeddings import get_embedding_model
from app.services.embeddings.service import EmbeddingService
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
OCR_LANGUAGE = "eng"

type SettingsDep = Annotated[Settings, Depends(get_settings)]


# Get the OCR engine
def get_ocr_engine() -> OcrEngine:
    # Currently using the Tesseract engine but in the future we will swap to Hailo
    return TesseractEngine(language=OCR_LANGUAGE)


# Get the upload service
def get_upload_service(
    database_pool: DatabasePoolDep,
    settings: SettingsDep,
    workspace: CurrentWorkspaceDep,
) -> UploadService:
    return UploadService(
        UploadRepository(database_pool, workspace.id),
        settings.upload_storage_dir,
    )


type UploadServiceDep = Annotated[UploadService, Depends(get_upload_service)]


# Get the financial record service
def get_financial_record_service(
    database_pool: DatabasePoolDep,
    workspace: CurrentWorkspaceDep,
) -> FinancialRecordService:
    return FinancialRecordService(
        FinancialRecordRepository(database_pool, workspace.id),
        VendorRuleRepository(database_pool, workspace.id),
        ExtractionCorrectionRepository(database_pool),
        DocumentTypeRuleRepository(database_pool, workspace.id),
    )


type FinancialRecordServiceDep = Annotated[
    FinancialRecordService, Depends(get_financial_record_service)
]


# Get the document extraction service.
def get_document_extraction_service(
    database_pool: DatabasePoolDep,
    settings: SettingsDep,
    workspace: CurrentWorkspaceDep,
    engine: Annotated[OcrEngine, Depends(get_ocr_engine)],
    financial_record_service: FinancialRecordServiceDep,
) -> DocumentExtractionService:
    embedding_service: EmbeddingService | None = None
    if settings.embeddings_enabled:
        embedding_service = EmbeddingService(
            repository=DocumentEmbeddingRepository(
                database_pool, workspace.id),
            model=get_embedding_model(settings),
            chunk_size=settings.embedding_chunk_size,
            chunk_overlap=settings.embedding_chunk_overlap,
        )

    return DocumentExtractionService(
        extraction_repository=DocumentExtractionRepository(database_pool),
        upload_repository=UploadRepository(database_pool, workspace.id),
        financial_record_service=financial_record_service,
        engine=engine,
        pdf_text_threshold=settings.ocr_pdf_text_threshold,
        pdf_render_dpi=settings.ocr_pdf_render_dpi,
        embedding_service=embedding_service,
        event_bus=get_upload_event_bus(),
        workspace_id=workspace.id,
    )


type DocumentExtractionServiceDep = Annotated[
    DocumentExtractionService, Depends(get_document_extraction_service)
]


# Helper function to raise appropriate HTTP exceptions based on upload service errors
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


# Create a new upload metadata in the DB and save the file to disk
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
        # Create the upload metadata and store the file.
        upload = await upload_service.create_upload(file=file)

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


# Stream upload status changes to the client over Server-Sent Events so the UI
# updates in real time instead of polling.
@router.get("/events")
async def stream_upload_events(
    request: Request,
    workspace: CurrentWorkspaceDep,
    event_bus: Annotated[UploadEventBus, Depends(get_upload_event_bus)],
) -> EventSourceResponse:
    queue = event_bus.subscribe(workspace.id)

    async def event_generator():
        try:
            while True:
                event = await queue.get()
                yield {
                    "event": "upload-status",
                    "data": json.dumps(
                        {"id": str(event.upload_id), "status": event.status}
                    ),
                }
        finally:
            # Runs when the client disconnects and sse-starlette closes the
            # generator, so we never leak subscriber queues.
            event_bus.unsubscribe(workspace.id, queue)

    return EventSourceResponse(event_generator())


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
