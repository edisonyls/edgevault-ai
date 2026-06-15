from datetime import date

from asyncpg import Pool, Record

# Upload columns keep their natural names so the existing row_to_upload_metadata
# helper can read them directly. Financial-record columns are prefixed because
# they would otherwise collide with the upload's id/created_at/updated_at.
_UPLOAD_COLUMNS = """
    u.id,
    u.text,
    u.original_filename,
    u.display_filename,
    u.stored_filename,
    u.file_path,
    u.mime_type,
    u.file_size,
    u.status,
    u.created_at,
    u.updated_at
"""

_FINANCIAL_RECORD_COLUMNS = """
    f.id AS fr_id,
    f.upload_id AS fr_upload_id,
    f.document_type AS fr_document_type,
    f.vendor AS fr_vendor,
    f.transaction_date AS fr_transaction_date,
    f.due_date AS fr_due_date,
    f.total_amount AS fr_total_amount,
    f.currency AS fr_currency,
    f.category AS fr_category,
    f.payment_status AS fr_payment_status,
    f.extraction_method AS fr_extraction_method,
    f.confidence AS fr_confidence,
    f.created_at AS fr_created_at,
    f.updated_at AS fr_updated_at
"""

# ts_headline wraps matches in these tags; the frontend splits on them to render
# highlights safely without trusting raw HTML.
_HEADLINE_OPTIONS = (
    "MaxFragments=2, MinWords=3, MaxWords=12, "
    "StartSel=<mark>, StopSel=</mark>"
)


class SearchRepository:
    def __init__(self, database_pool: Pool) -> None:
        self.database_pool = database_pool

    # Search documents by OCR text and/or structured filters.
    async def search(
        self,
        *,
        q: str | None,
        category: str | None,
        vendor: str | None,
        document_type: str | None,
        payment_status: str | None,
        date_from: date | None,
        date_to: date | None,
        limit: int,
        offset: int,
    ) -> list[Record]:
        values: list[object] = []
        where: list[str] = []

        select_rank = "NULL::real AS rank"
        select_snippet = "left(u.text, 200) AS snippet"
        order_by = "f.transaction_date DESC NULLS LAST, u.created_at DESC"

        normalized_q = q.strip() if q is not None else ""
        if normalized_q:
            values.append(normalized_q)
            query_placeholder = f"${len(values)}"
            values.append(f"%{normalized_q}%")
            like_placeholder = f"${len(values)}"

            tsquery = f"websearch_to_tsquery('english', {query_placeholder})"
            select_rank = f"ts_rank(u.search_tsv, {tsquery}) AS rank"
            select_snippet = (
                f"ts_headline('english', coalesce(u.text, ''), {tsquery}, "
                f"'{_HEADLINE_OPTIONS}') AS snippet"
            )
            where.append(
                f"(u.search_tsv @@ {tsquery} "
                f"OR u.display_filename ILIKE {like_placeholder} "
                f"OR f.vendor ILIKE {like_placeholder})"
            )
            order_by = "rank DESC, u.created_at DESC"

        if category is not None:
            values.append(category)
            where.append(f"f.category = ${len(values)}")

        if vendor is not None:
            values.append(f"%{vendor.strip()}%")
            where.append(f"f.vendor ILIKE ${len(values)}")

        if document_type is not None:
            values.append(document_type)
            where.append(f"f.document_type = ${len(values)}")

        if payment_status is not None:
            values.append(payment_status)
            where.append(f"f.payment_status = ${len(values)}")

        if date_from is not None:
            values.append(date_from)
            where.append(f"f.transaction_date >= ${len(values)}")

        if date_to is not None:
            values.append(date_to)
            where.append(f"f.transaction_date <= ${len(values)}")

        where_clause = f"WHERE {' AND '.join(where)}" if where else ""

        values.extend([limit, offset])
        limit_placeholder = f"${len(values) - 1}"
        offset_placeholder = f"${len(values)}"

        async with self.database_pool.acquire() as connection:
            return await connection.fetch(
                f"""
                SELECT
                    {_UPLOAD_COLUMNS},
                    {_FINANCIAL_RECORD_COLUMNS},
                    {select_rank},
                    {select_snippet}
                FROM resume_uploads u
                LEFT JOIN financial_records f ON f.upload_id = u.id
                {where_clause}
                ORDER BY {order_by}
                LIMIT {limit_placeholder}
                OFFSET {offset_placeholder}
                """,
                *values,
            )
