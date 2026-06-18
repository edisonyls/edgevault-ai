import asyncio
import io
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

import fitz  # PyMuPDF
from asyncpg import Record
from PIL import Image

from app.core.events import UploadEventBus, UploadStatusEvent
from app.repositories.document_extractions import DocumentExtractionRepository
from app.repositories.uploads import UploadRepository
from app.schemas.document_extractions import DocumentExtractionResponse, ExtractionMethod
from app.services.embeddings.service import EmbeddingService
from app.services.financial_extraction import FinancialRecordService
from app.services.ocr.base import OcrEngine

logger = logging.getLogger(__name__)

PDF_MIME_TYPE = "application/pdf"


class UnsupportedDocumentError(Exception):
    pass


@dataclass(slots=True)
class ExtractionOutcome:
    text: str
    extraction_method: ExtractionMethod
    confidence: float | None
    page_count: int | None


def row_to_document_extraction(row: Record) -> DocumentExtractionResponse:
    return DocumentExtractionResponse(
        id=row["id"],
        upload_id=row["upload_id"],
        raw_text=row["raw_text"],
        ocr_engine=row["ocr_engine"],
        ocr_engine_version=row["ocr_engine_version"],
        extraction_method=row["extraction_method"],
        ocr_confidence=row["ocr_confidence"],
        page_count=row["page_count"],
        processing_latency_ms=row["processing_latency_ms"],
        status=row["status"],
        error_message=row["error_message"],
        created_at=row["created_at"],
    )


class DocumentExtractionService:
    def __init__(
        self,
        *,
        extraction_repository: DocumentExtractionRepository,
        upload_repository: UploadRepository,
        financial_record_service: FinancialRecordService,
        engine: OcrEngine,
        pdf_text_threshold: int,
        pdf_render_dpi: int,
        embedding_service: EmbeddingService | None = None,
        event_bus: UploadEventBus | None = None,
        workspace_id: UUID | None = None,
    ) -> None:
        self.extraction_repository = extraction_repository
        self.upload_repository = upload_repository
        self.financial_record_service = financial_record_service
        self.engine = engine
        self.pdf_text_threshold = pdf_text_threshold
        self.pdf_render_dpi = pdf_render_dpi
        self.embedding_service = embedding_service
        self.event_bus = event_bus
        self.workspace_id = workspace_id

    # Persist a new upload status and push it to any SSE subscribers so the UI
    # reflects the change without polling.
    async def _set_status(
        self, upload_id: UUID, status: str, *, extra: dict[str, object] | None = None
    ) -> None:
        payload: dict[str, object] = {"status": status}
        if extra:
            payload.update(extra)
        await self.upload_repository.update(upload_id, payload)
        if self.event_bus is not None and self.workspace_id is not None:
            self.event_bus.publish(
                self.workspace_id,
                UploadStatusEvent(upload_id=upload_id, status=status),
            )

    # Background task entry point to run OCR extraction and post-processing for an uploads
    async def run(self, *, upload_id: UUID, storage_path: Path, mime_type: str) -> None:
        """
        Background entry point: OCR the document and persist the result.
        """
        started_at = time.perf_counter()
        try:
            # Mark the upload as extracting now that OCR is actually starting.
            await self._set_status(upload_id, "extracting")

            # Extract the text from the uploaded document using OCR
            outcome = await asyncio.to_thread(self._extract, storage_path, mime_type)

            latency_ms = int((time.perf_counter() - started_at) * 1000)

            # Save the OCR result in the database that is linked to the upload
            await self.extraction_repository.create(
                upload_id=upload_id,
                raw_text=outcome.text,
                ocr_engine=self.engine.name,
                ocr_engine_version=self.engine.version,
                extraction_method=outcome.extraction_method,
                ocr_confidence=outcome.confidence,
                page_count=outcome.page_count,
                processing_latency_ms=latency_ms,
                status="succeeded",
                error_message=None,
            )

            # Update upload status to 'indexing'
            await self._set_status(
                upload_id, "indexing", extra={"text": outcome.text}
            )

            # Derive structured financial fields from the OCR text using the
            # financial record service, and persist them in the database.
            try:
                await self.financial_record_service.extract_and_store(
                    upload_id=upload_id, text=outcome.text
                )
            except Exception:
                logger.exception(
                    "Financial extraction failed for upload %s", upload_id)

            if self.embedding_service is not None:
                try:
                    await self.embedding_service.embed_and_store(
                        upload_id=upload_id, text=outcome.text
                    )
                except Exception:
                    logger.exception(
                        "Embedding generation failed for upload %s", upload_id)

            # Update upload status to 'processed' after all post-processing is done.
            await self._set_status(upload_id, "processed")
        except Exception as exc:
            latency_ms = int((time.perf_counter() - started_at) * 1000)
            error_message = str(exc) or exc.__class__.__name__
            logger.exception("OCR extraction failed for upload %s", upload_id)
            try:
                await self.extraction_repository.create(
                    upload_id=upload_id,
                    raw_text=None,
                    ocr_engine=self.engine.name,
                    ocr_engine_version=self.engine.version,
                    extraction_method=None,
                    ocr_confidence=None,
                    page_count=None,
                    processing_latency_ms=latency_ms,
                    status="failed",
                    error_message=error_message[:2000],
                )
                await self._set_status(upload_id, "failed")
            except Exception:
                logger.exception(
                    "Failed to record OCR failure for upload %s", upload_id)

    async def list_extractions(self, upload_id: UUID) -> list[DocumentExtractionResponse]:
        rows = await self.extraction_repository.list_for_upload(upload_id)
        return [row_to_document_extraction(row) for row in rows]

    # OCR extraction.
    def _extract(self, storage_path: Path, mime_type: str) -> ExtractionOutcome:
        if mime_type == PDF_MIME_TYPE or storage_path.suffix.lower() == ".pdf":
            return self._extract_pdf(storage_path)
        if mime_type.startswith("image/"):
            return self._extract_image_file(storage_path)
        raise UnsupportedDocumentError(
            f"Unsupported document type for OCR: {mime_type}")

    # Extract text from a PDF
    def _extract_pdf(self, storage_path: Path) -> ExtractionOutcome:
        with fitz.open(storage_path) as document:
            # 1. Try to extract text from the PDF text layer first if it meets
            # the threshold since this is a much faster way.
            page_count = document.page_count
            text_layer = "\n".join(page.get_text() for page in document)
            threshold = self.pdf_text_threshold * max(page_count, 1)
            if len(text_layer.strip()) >= threshold:
                return ExtractionOutcome(
                    text=text_layer.strip(),
                    extraction_method="pdf_text_layer",
                    confidence=None,
                    page_count=page_count,
                )

            # 2. Render each page as an image and performing OCR on it if the
            # text layer is too sparse.
            page_texts: list[str] = []
            weighted_confidence = 0.0
            total_words = 0
            for page in document:
                image = self._render_page(page)
                result = self.engine.extract_image(image)
                page_texts.append(result.text)
                if result.confidence is not None and result.word_count:
                    weighted_confidence += result.confidence * result.word_count
                    total_words += result.word_count

        # Average the confidence across all words in the document, so pages with
        # more text weigh proportionally more than short ones.
        confidence = weighted_confidence / total_words if total_words else None
        return ExtractionOutcome(
            text="\n\n".join(page_texts).strip(),
            extraction_method="ocr",
            confidence=confidence,
            page_count=page_count,
        )

    # Extract text from an image file
    def _extract_image_file(self, storage_path: Path) -> ExtractionOutcome:
        with Image.open(storage_path) as image:
            image.load()
            result = self.engine.extract_image(image)
        return ExtractionOutcome(
            text=result.text.strip(),
            extraction_method="ocr",
            confidence=result.confidence,
            page_count=1,
        )

    # Render a PDF page to an image for OCR processing
    def _render_page(self, page: fitz.Page) -> Image.Image:
        pixmap = page.get_pixmap(dpi=self.pdf_render_dpi)
        return Image.open(io.BytesIO(pixmap.tobytes("png")))
