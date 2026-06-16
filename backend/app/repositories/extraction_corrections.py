import json
from collections.abc import Sequence
from uuid import UUID

from asyncpg import Pool, Record

EXTRACTION_CORRECTION_COLUMNS = """
    id,
    upload_id,
    financial_record_id,
    predicted,
    corrected,
    changed_fields,
    extraction_method,
    created_at
"""


class ExtractionCorrectionRepository:
    def __init__(self, database_pool: Pool) -> None:
        self.database_pool = database_pool

    # Append a correction event.
    async def insert(
        self,
        *,
        upload_id: UUID,
        financial_record_id: UUID,
        predicted: dict[str, object],
        corrected: dict[str, object],
        changed_fields: Sequence[str],
        extraction_method: str,
    ) -> Record | None:
        async with self.database_pool.acquire() as connection:
            return await connection.fetchrow(
                f"""
                INSERT INTO extraction_corrections (
                    upload_id,
                    financial_record_id,
                    predicted,
                    corrected,
                    changed_fields,
                    extraction_method
                )
                VALUES ($1, $2, $3::jsonb, $4::jsonb, $5, $6)
                RETURNING
                    {EXTRACTION_CORRECTION_COLUMNS}
                """,
                upload_id,
                financial_record_id,
                json.dumps(predicted),
                json.dumps(corrected),
                list(changed_fields),
                extraction_method,
            )

    # List every correction event, oldest first, so callers can replay the history
    async def list_all(self) -> list[Record]:
        async with self.database_pool.acquire() as connection:
            return await connection.fetch(
                f"""
                SELECT
                    {EXTRACTION_CORRECTION_COLUMNS}
                FROM extraction_corrections
                ORDER BY created_at ASC, id ASC
                """
            )
