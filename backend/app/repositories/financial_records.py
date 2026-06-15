from datetime import date
from decimal import Decimal
from uuid import UUID

from asyncpg import Pool, Record

FINANCIAL_RECORD_RETURNING_COLUMNS = """
    id,
    upload_id,
    document_type,
    vendor,
    transaction_date,
    due_date,
    total_amount,
    currency,
    category,
    payment_status,
    extraction_method,
    confidence,
    created_at,
    updated_at
"""


class FinancialRecordRepository:
    def __init__(self, database_pool: Pool) -> None:
        self.database_pool = database_pool

    # Upsert a financial record based on extraction results, keyed by upload_id.
    # If a record with the same upload_id already exists, update it only if the
    # existing record's extraction method is not 'manual'.
    async def upsert_from_extraction(
        self,
        *,
        upload_id: UUID,
        document_type: str | None,
        vendor: str | None,
        transaction_date: date | None,
        due_date: date | None,
        total_amount: Decimal | None,
        currency: str,
        category: str | None,
        payment_status: str | None,
        extraction_method: str,
        confidence: float | None,
    ) -> Record | None:
        async with self.database_pool.acquire() as connection:
            return await connection.fetchrow(
                f"""
                INSERT INTO financial_records (
                    upload_id,
                    document_type,
                    vendor,
                    transaction_date,
                    due_date,
                    total_amount,
                    currency,
                    category,
                    payment_status,
                    extraction_method,
                    confidence
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                ON CONFLICT (upload_id) DO UPDATE SET
                    document_type = EXCLUDED.document_type,
                    vendor = EXCLUDED.vendor,
                    transaction_date = EXCLUDED.transaction_date,
                    due_date = EXCLUDED.due_date,
                    total_amount = EXCLUDED.total_amount,
                    currency = EXCLUDED.currency,
                    category = EXCLUDED.category,
                    payment_status = EXCLUDED.payment_status,
                    extraction_method = EXCLUDED.extraction_method,
                    confidence = EXCLUDED.confidence
                WHERE financial_records.extraction_method <> 'manual'
                RETURNING
                    {FINANCIAL_RECORD_RETURNING_COLUMNS}
                """,
                upload_id,
                document_type,
                vendor,
                transaction_date,
                due_date,
                total_amount,
                currency,
                category,
                payment_status,
                extraction_method,
                confidence,
            )

    # Get a financial record by upload_id.
    async def get_for_upload(self, upload_id: UUID) -> Record | None:
        async with self.database_pool.acquire() as connection:
            return await connection.fetchrow(
                f"""
                SELECT
                    {FINANCIAL_RECORD_RETURNING_COLUMNS}
                FROM financial_records
                WHERE upload_id = $1
                """,
                upload_id,
            )

    # Get a financial record by its ID.
    async def get(self, record_id: UUID) -> Record | None:
        async with self.database_pool.acquire() as connection:
            return await connection.fetchrow(
                f"""
                SELECT
                    {FINANCIAL_RECORD_RETURNING_COLUMNS}
                FROM financial_records
                WHERE id = $1
                """,
                record_id,
            )

    # List financial records, optionally filtering by category, with pagination.
    async def list(
        self,
        *,
        category: str | None,
        limit: int,
        offset: int,
    ) -> list[Record]:
        values: list[object] = []
        where_clause = ""

        if category is not None:
            values.append(category)
            where_clause = "WHERE category = $1"

        values.extend([limit, offset])
        limit_placeholder = f"${len(values) - 1}"
        offset_placeholder = f"${len(values)}"

        async with self.database_pool.acquire() as connection:
            return await connection.fetch(
                f"""
                SELECT
                    {FINANCIAL_RECORD_RETURNING_COLUMNS}
                FROM financial_records
                {where_clause}
                ORDER BY created_at DESC, id DESC
                LIMIT {limit_placeholder}
                OFFSET {offset_placeholder}
                """,
                *values,
            )

    # Update a financial record by ID with the provided fields.
    async def update(
        self,
        record_id: UUID,
        update_data: dict[str, object],
    ) -> Record | None:
        set_clauses = ["extraction_method = 'manual'"]
        values: list[object] = []

        for column, value in update_data.items():
            values.append(value)
            set_clauses.append(f"{column} = ${len(values)}")

        values.append(record_id)

        async with self.database_pool.acquire() as connection:
            return await connection.fetchrow(
                f"""
                UPDATE financial_records
                SET {", ".join(set_clauses)}
                WHERE id = ${len(values)}
                RETURNING
                    {FINANCIAL_RECORD_RETURNING_COLUMNS}
                """,
                *values,
            )
