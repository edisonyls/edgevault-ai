from uuid import UUID

from asyncpg import Pool, Record

from app.schemas.document_extractions import ExtractionMethod, ExtractionStatus

DOCUMENT_EXTRACTION_RETURNING_COLUMNS = """
    id,
    upload_id,
    raw_text,
    ocr_engine,
    ocr_engine_version,
    extraction_method,
    ocr_confidence,
    page_count,
    processing_latency_ms,
    status,
    error_message,
    created_at
"""


class DocumentExtractionRepository:
    def __init__(self, database_pool: Pool) -> None:
        self.database_pool = database_pool

    async def create(
        self,
        *,
        upload_id: UUID,
        raw_text: str | None,
        ocr_engine: str,
        ocr_engine_version: str | None,
        extraction_method: ExtractionMethod | None,
        ocr_confidence: float | None,
        page_count: int | None,
        processing_latency_ms: int,
        status: ExtractionStatus,
        error_message: str | None,
    ) -> Record:
        async with self.database_pool.acquire() as connection:
            return await connection.fetchrow(
                f"""
                INSERT INTO document_extractions (
                    upload_id,
                    raw_text,
                    ocr_engine,
                    ocr_engine_version,
                    extraction_method,
                    ocr_confidence,
                    page_count,
                    processing_latency_ms,
                    status,
                    error_message
                )
                VALUES (
                    $1, $2, $3, $4,
                    $5::document_extraction_method,
                    $6, $7, $8,
                    $9::document_extraction_status,
                    $10
                )
                RETURNING
                    {DOCUMENT_EXTRACTION_RETURNING_COLUMNS}
                """,
                upload_id,
                raw_text,
                ocr_engine,
                ocr_engine_version,
                extraction_method,
                ocr_confidence,
                page_count,
                processing_latency_ms,
                status,
                error_message,
            )

    async def list_for_upload(self, upload_id: UUID) -> list[Record]:
        async with self.database_pool.acquire() as connection:
            return await connection.fetch(
                f"""
                SELECT
                    {DOCUMENT_EXTRACTION_RETURNING_COLUMNS}
                FROM document_extractions
                WHERE upload_id = $1
                ORDER BY created_at DESC, id DESC
                """,
                upload_id,
            )

    async def get_latest(self, upload_id: UUID) -> Record | None:
        async with self.database_pool.acquire() as connection:
            return await connection.fetchrow(
                f"""
                SELECT
                    {DOCUMENT_EXTRACTION_RETURNING_COLUMNS}
                FROM document_extractions
                WHERE upload_id = $1
                ORDER BY created_at DESC, id DESC
                LIMIT 1
                """,
                upload_id,
            )
