from datetime import date
from typing import Literal

from asyncpg import Record

from app.repositories.search import SearchRepository
from app.schemas.financial_records import FinancialRecordResponse
from app.schemas.search import SearchResultResponse
from app.services.embeddings.service import EmbeddingService
from app.services.uploads import row_to_upload_metadata

SearchMode = Literal["keyword", "semantic", "hybrid"]

# RRF_K controls how much the top few positions dominate
RRF_K = 60


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
    def __init__(
        self,
        repository: SearchRepository,
        embedding_service: EmbeddingService | None = None,
    ) -> None:
        self.repository = repository
        self.embedding_service = embedding_service

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
        mode: SearchMode = "keyword",
    ) -> list[SearchResultResponse]:
        has_query = bool(q and q.strip())
        # Keyword search
        if mode == "keyword" or not has_query or self.embedding_service is None:
            return await self._keyword(
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

        # Semantic or hybrid search
        filters = {
            "category": category,
            "vendor": vendor,
            "document_type": document_type,
            "payment_status": payment_status,
            "date_from": date_from,
            "date_to": date_to,
        }

        embedding = await self.embedding_service.embed_query(q or "")
        if embedding is None:
            return await self._keyword(q=q, limit=limit, offset=offset, **filters)

        # Pure semantic search
        if mode == "semantic":
            rows = await self.repository.search_semantic(
                embedding=embedding, limit=limit, offset=offset, **filters
            )
            return [_row_to_search_result(row) for row in rows]

        # Hybrid search with Reciprocal Rank Fusion
        return await self._hybrid(
            q=q,
            embedding=embedding,
            limit=limit,
            offset=offset,
            filters=filters,
        )

    # Simple keyword search with SQL ranking and pagination.
    async def _keyword(
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

    # Blend keyword and semantic rankings with Reciprocal Rank Fusion.
    async def _hybrid(
        self,
        *,
        q: str | None,
        embedding: list[float],
        limit: int,
        offset: int,
        filters: dict[str, object],
    ) -> list[SearchResultResponse]:
        window = limit + offset

        keyword_rows = await self.repository.search(q=q, limit=window, offset=0, **filters)
        semantic_rows = await self.repository.search_semantic(
            embedding=embedding, limit=window, offset=0, **filters
        )

        scores: dict[str, float] = {}
        chosen: dict[str, SearchResultResponse] = {}

        for ranking in (keyword_rows, semantic_rows):
            for position, row in enumerate(ranking):
                result = _row_to_search_result(row)
                key = str(result.upload.id)
                scores[key] = scores.get(key, 0.0) + \
                    1.0 / (RRF_K + position + 1)
                if key not in chosen:
                    chosen[key] = result

        ordered = sorted(
            chosen.values(),
            key=lambda result: scores[str(result.upload.id)],
            reverse=True,
        )
        for result in ordered:
            result.rank = scores[str(result.upload.id)]

        return ordered[offset: offset + limit]
