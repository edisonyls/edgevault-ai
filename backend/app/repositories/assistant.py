from datetime import date
from typing import Literal
from uuid import UUID

from asyncpg import Pool, Record

# Fields cited back to the user as evidence. Kept small and stable so the
# SupportingRecord schema maps directly onto each row.
_EVIDENCE_COLUMNS = """
    upload_id,
    vendor,
    total_amount,
    transaction_date,
    category
"""

EvidenceOrder = Literal["amount", "due", "date"]
DateColumn = Literal["transaction_date", "due_date"]

_ORDER_BY: dict[EvidenceOrder, str] = {
    "amount": "total_amount DESC NULLS LAST, transaction_date DESC NULLS LAST",
    "due": "due_date ASC NULLS LAST, transaction_date DESC NULLS LAST",
    "date": "transaction_date DESC NULLS LAST",
}


class AssistantRepository:
    """
    All database access for the spending assistant: the append-only query log
    plus the fixed set of read-only aggregates the controlled engine runs. Every
    spend aggregate ignores rows without a parsed amount so totals only reflect
    real, attributable numbers.
    """

    def __init__(self, database_pool: Pool, workspace_id: UUID) -> None:
        self.database_pool = database_pool
        self.workspace_id = workspace_id

    # The database server's clock — the single source of truth for "today" so
    # relative periods ("this month") don't drift from the app process timezone.
    async def current_date(self) -> date:
        async with self.database_pool.acquire() as connection:
            return await connection.fetchval("SELECT CURRENT_DATE")

    async def log_query(
        self, *, question: str, answer: str, query_type: str, source: str = "rules"
    ) -> Record | None:
        async with self.database_pool.acquire() as connection:
            return await connection.fetchrow(
                """
                INSERT INTO assistant_queries (
                    workspace_id,
                    question,
                    answer,
                    query_type,
                    source
                )
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id, question, answer, query_type, source, created_at
                """,
                self.workspace_id,
                question,
                answer,
                query_type,
                source,
            )

    # Highest-spending category within an optional date window.
    async def top_category(self, *, date_from: date | None, date_to: date | None) -> Record | None:
        async with self.database_pool.acquire() as connection:
            return await connection.fetchrow(
                """
                SELECT
                    category,
                    SUM(total_amount) AS total,
                    COUNT(*) AS count
                FROM financial_records
                JOIN resume_uploads ON resume_uploads.id = financial_records.upload_id
                WHERE resume_uploads.workspace_id = $1
                  AND total_amount IS NOT NULL
                  AND category IS NOT NULL
                  AND ($2::date IS NULL OR transaction_date >= $2)
                  AND ($3::date IS NULL OR transaction_date <= $3)
                GROUP BY category
                ORDER BY total DESC
                LIMIT 1
                """,
                self.workspace_id,
                date_from,
                date_to,
            )

    # Total spent in one category within an optional date window.
    async def category_aggregate(
        self, *, category: str, date_from: date | None, date_to: date | None
    ) -> Record:
        async with self.database_pool.acquire() as connection:
            return await connection.fetchrow(
                """
                SELECT
                    COALESCE(SUM(total_amount), 0) AS total,
                    COUNT(*) AS count
                FROM financial_records
                JOIN resume_uploads ON resume_uploads.id = financial_records.upload_id
                WHERE resume_uploads.workspace_id = $1
                  AND category = $2
                  AND total_amount IS NOT NULL
                  AND ($3::date IS NULL OR transaction_date >= $3)
                  AND ($4::date IS NULL OR transaction_date <= $4)
                """,
                self.workspace_id,
                category,
                date_from,
                date_to,
            )

    # Per-category totals within an optional date window, biggest first.
    async def category_breakdown(
        self, *, date_from: date | None, date_to: date | None
    ) -> list[Record]:
        async with self.database_pool.acquire() as connection:
            return await connection.fetch(
                """
                SELECT
                    category,
                    SUM(total_amount) AS total,
                    COUNT(*) AS count
                FROM financial_records
                JOIN resume_uploads ON resume_uploads.id = financial_records.upload_id
                WHERE resume_uploads.workspace_id = $1
                  AND total_amount IS NOT NULL
                  AND category IS NOT NULL
                  AND ($2::date IS NULL OR transaction_date >= $2)
                  AND ($3::date IS NULL OR transaction_date <= $3)
                GROUP BY category
                ORDER BY total DESC
                """,
                self.workspace_id,
                date_from,
                date_to,
            )

    # Count and total of outstanding bills, optionally limited to those due
    # within a date window and/or owed to a single vendor.
    async def unpaid_aggregate(
        self,
        *,
        date_from: date | None = None,
        date_to: date | None = None,
        vendor: str | None = None,
    ) -> Record:
        async with self.database_pool.acquire() as connection:
            return await connection.fetchrow(
                """
                SELECT
                    COUNT(*) AS count,
                    COALESCE(SUM(total_amount), 0) AS total
                FROM financial_records
                JOIN resume_uploads ON resume_uploads.id = financial_records.upload_id
                WHERE resume_uploads.workspace_id = $1
                  AND payment_status = 'unpaid'
                  AND ($2::date IS NULL OR due_date >= $2)
                  AND ($3::date IS NULL OR due_date <= $3)
                  AND ($4::text IS NULL OR vendor = $4)
                """,
                self.workspace_id,
                date_from,
                date_to,
                vendor,
            )

    # Distinct vendors on record, with how many records and how much each totals.
    async def list_vendors(self) -> list[Record]:
        async with self.database_pool.acquire() as connection:
            return await connection.fetch(
                """
                SELECT
                    vendor,
                    COUNT(*) AS count,
                    COALESCE(SUM(total_amount), 0) AS total
                FROM financial_records
                JOIN resume_uploads ON resume_uploads.id = financial_records.upload_id
                WHERE resume_uploads.workspace_id = $1
                  AND vendor IS NOT NULL
                GROUP BY vendor
                ORDER BY total DESC, vendor
                """,
                self.workspace_id,
            )

    # Total spent at one vendor within an optional date window.
    async def vendor_aggregate(
        self, *, vendor: str, date_from: date | None, date_to: date | None
    ) -> Record:
        async with self.database_pool.acquire() as connection:
            return await connection.fetchrow(
                """
                SELECT
                    COALESCE(SUM(total_amount), 0) AS total,
                    COUNT(*) AS count
                FROM financial_records
                JOIN resume_uploads ON resume_uploads.id = financial_records.upload_id
                WHERE resume_uploads.workspace_id = $1
                  AND vendor = $2
                  AND total_amount IS NOT NULL
                  AND ($3::date IS NULL OR transaction_date >= $3)
                  AND ($4::date IS NULL OR transaction_date <= $4)
                """,
                self.workspace_id,
                vendor,
                date_from,
                date_to,
            )

    # How many documents and financial records exist within an optional date window.
    async def document_count(
        self, *, date_from: date | None = None, date_to: date | None = None
    ) -> Record:
        async with self.database_pool.acquire() as connection:
            return await connection.fetchrow(
                """
                SELECT
                    COUNT(DISTINCT upload_id) AS documents,
                    COUNT(*) AS records
                FROM financial_records
                JOIN resume_uploads ON resume_uploads.id = financial_records.upload_id
                WHERE resume_uploads.workspace_id = $1
                  AND ($2::date IS NULL OR transaction_date >= $2)
                  AND ($3::date IS NULL OR transaction_date <= $3)
                """,
                self.workspace_id,
                date_from,
                date_to,
            )

    # Distinct subscription vendors with how often and how much.
    async def subscription_vendors(self) -> list[Record]:
        async with self.database_pool.acquire() as connection:
            return await connection.fetch(
                """
                SELECT
                    vendor,
                    COUNT(*) AS count,
                    COALESCE(SUM(total_amount), 0) AS total
                FROM financial_records
                JOIN resume_uploads ON resume_uploads.id = financial_records.upload_id
                WHERE resume_uploads.workspace_id = $1
                  AND category = 'subscription'
                GROUP BY vendor
                ORDER BY vendor NULLS LAST
                """,
                self.workspace_id,
            )

    # Individual records used as supporting evidence for an answer.
    async def records(
        self,
        *,
        category: str | None = None,
        vendor: str | None = None,
        payment_status: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        date_column: DateColumn = "transaction_date",
        require_amount: bool = True,
        order: EvidenceOrder = "amount",
        limit: int = 10,
    ) -> list[Record]:
        values: list[object] = [self.workspace_id]
        where: list[str] = ["resume_uploads.workspace_id = $1"]

        if require_amount:
            where.append("total_amount IS NOT NULL")
        if category is not None:
            values.append(category)
            where.append(f"category = ${len(values)}")
        if vendor is not None:
            values.append(vendor)
            where.append(f"vendor = ${len(values)}")
        if payment_status is not None:
            values.append(payment_status)
            where.append(f"payment_status = ${len(values)}")
        if date_from is not None:
            values.append(date_from)
            where.append(f"{date_column} >= ${len(values)}")
        if date_to is not None:
            values.append(date_to)
            where.append(f"{date_column} <= ${len(values)}")

        where_clause = f"WHERE {' AND '.join(where)}" if where else ""

        values.append(limit)
        limit_placeholder = f"${len(values)}"

        async with self.database_pool.acquire() as connection:
            return await connection.fetch(
                f"""
                SELECT
                    {_EVIDENCE_COLUMNS}
                FROM financial_records
                JOIN resume_uploads ON resume_uploads.id = financial_records.upload_id
                {where_clause}
                ORDER BY {_ORDER_BY[order]}
                LIMIT {limit_placeholder}
                """,
                *values,
            )
