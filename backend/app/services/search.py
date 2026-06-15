from datetime import date

from asyncpg import Record

from app.repositories.search import SearchRepository
from app.schemas.financial_records import FinancialRecordResponse
from app.schemas.search import SearchResultResponse
from app.services.uploads import row_to_upload_metadata


def _row_to_financial_record(row: Record) -> FinancialRecordResponse | None:
    if row["fr_id"] is None:
        return None

    total_amount = row["fr_total_amount"]
    return FinancialRecordResponse(
        id=row["fr_id"],
        upload_id=row["fr_upload_id"],
        document_type=row["fr_document_type"],
        vendor=row["fr_vendor"],
        transaction_date=row["fr_transaction_date"],
        due_date=row["fr_due_date"],
        total_amount=float(total_amount) if total_amount is not None else None,
        currency=row["fr_currency"],
        category=row["fr_category"],
        payment_status=row["fr_payment_status"],
        extraction_method=row["fr_extraction_method"],
        confidence=row["fr_confidence"],
        created_at=row["fr_created_at"],
        updated_at=row["fr_updated_at"],
    )


def _row_to_search_result(row: Record) -> SearchResultResponse:
    return SearchResultResponse(
        upload=row_to_upload_metadata(row),
        financial_record=_row_to_financial_record(row),
        snippet=row["snippet"],
        rank=row["rank"],
    )


class SearchService:
    def __init__(self, repository: SearchRepository) -> None:
        self.repository = repository

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
    ) -> list[SearchResultResponse]:
        rows = await self.repository.search(
            q=q,
            category=category,
            vendor=vendor,
            document_type=document_type,
            payment_status=payment_status,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
            offset=offset,
        )
        return [_row_to_search_result(row) for row in rows]
