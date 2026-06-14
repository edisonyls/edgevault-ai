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

from app.repositories.document_extractions import DocumentExtractionRepository
from app.repositories.uploads import UploadRepository
from app.schemas.document_extractions import DocumentExtractionResponse, ExtractionMethod
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
        engine: OcrEngine,
        pdf_text_threshold: int,
        pdf_render_dpi: int,
    ) -> None:
        self.extraction_repository = extraction_repository
        self.upload_repository = upload_repository
        self.engine = engine
        self.pdf_text_threshold = pdf_text_threshold
        self.pdf_render_dpi = pdf_render_dpi

    async def run(self, *, upload_id: UUID, storage_path: Path, mime_type: str) -> None:
        """Background entry point: OCR the document and persist the result.
        """
        started_at = time.perf_counter()
        try:
            outcome = await asyncio.to_thread(self._extract, storage_path, mime_type)
            latency_ms = int((time.perf_counter() - started_at) * 1000)
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
            await self.upload_repository.update(
                upload_id, {"text": outcome.text, "status": "processed"}
            )
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
                await self.upload_repository.update(upload_id, {"status": "failed"})
            except Exception:
                logger.exception(
                    "Failed to record OCR failure for upload %s", upload_id)

    async def list_extractions(self, upload_id: UUID) -> list[DocumentExtractionResponse]:
        rows = await self.extraction_repository.list_for_upload(upload_id)
        return [row_to_document_extraction(row) for row in rows]

    # --- blocking work (runs in a worker thread) ---------------------------------

    def _extract(self, storage_path: Path, mime_type: str) -> ExtractionOutcome:
        if mime_type == PDF_MIME_TYPE or storage_path.suffix.lower() == ".pdf":
            return self._extract_pdf(storage_path)
        if mime_type.startswith("image/"):
            return self._extract_image_file(storage_path)
        raise UnsupportedDocumentError(
            f"Unsupported document type for OCR: {mime_type}")

    def _extract_pdf(self, storage_path: Path) -> ExtractionOutcome:
        with fitz.open(storage_path) as document:
            page_count = document.page_count
            text_layer = "\n".join(page.get_text() for page in document)

            # A born-digital PDF already has a usable text layer; only fall back to
            # OCR when there is too little text to trust.
            threshold = self.pdf_text_threshold * max(page_count, 1)
            if len(text_layer.strip()) >= threshold:
                return ExtractionOutcome(
                    text=text_layer.strip(),
                    extraction_method="pdf_text_layer",
                    confidence=None,
                    page_count=page_count,
                )

            page_texts: list[str] = []
            confidences: list[float] = []
            for page in document:
                image = self._render_page(page)
                result = self.engine.extract_image(image)
                page_texts.append(result.text)
                if result.confidence is not None:
                    confidences.append(result.confidence)

        confidence = sum(confidences) / \
            len(confidences) if confidences else None
        return ExtractionOutcome(
            text="\n\n".join(page_texts).strip(),
            extraction_method="ocr",
            confidence=confidence,
            page_count=page_count,
        )

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

    def _render_page(self, page: fitz.Page) -> Image.Image:
        pixmap = page.get_pixmap(dpi=self.pdf_render_dpi)
        return Image.open(io.BytesIO(pixmap.tobytes("png")))
