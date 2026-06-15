from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query

from app.core.config import Settings, get_settings
from app.core.database import DatabasePoolDep
from app.repositories.document_embeddings import DocumentEmbeddingRepository
from app.repositories.search import SearchRepository
from app.schemas.financial_records import (
    FinancialCategory,
    FinancialDocumentType,
    PaymentStatus,
)
from app.schemas.search import SearchResultResponse
from app.services.embeddings import get_embedding_model
from app.services.embeddings.service import EmbeddingService
from app.services.search import SearchMode, SearchService

router = APIRouter(tags=["search"])

MAX_SEARCH_LIMIT = 500


def get_search_service(
    database_pool: DatabasePoolDep,
    settings: Annotated[Settings, Depends(get_settings)],
) -> SearchService:
    embedding_service: EmbeddingService | None = None
    if settings.embeddings_enabled:
        embedding_service = EmbeddingService(
            repository=DocumentEmbeddingRepository(database_pool),
            model=get_embedding_model(settings),
            chunk_size=settings.embedding_chunk_size,
            chunk_overlap=settings.embedding_chunk_overlap,
        )

    return SearchService(SearchRepository(database_pool), embedding_service)


type SearchServiceDep = Annotated[SearchService, Depends(get_search_service)]


#    Keyword search over document OCR text with optional structured filters.
#    Results are ranked by relevance when `q` is provided.
@router.get("/search", response_model=list[SearchResultResponse])
async def search_documents(
    search_service: SearchServiceDep,
    q: Annotated[str | None, Query()] = None,
    category: Annotated[FinancialCategory | None, Query()] = None,
    vendor: Annotated[str | None, Query()] = None,
    document_type: Annotated[FinancialDocumentType | None, Query()] = None,
    payment_status: Annotated[PaymentStatus | None, Query()] = None,
    date_from: Annotated[date | None, Query(alias="from")] = None,
    date_to: Annotated[date | None, Query(alias="to")] = None,
    mode: Annotated[Literal["keyword", "semantic",
                            "hybrid"], Query()] = "keyword",
    limit: Annotated[int, Query(ge=1, le=MAX_SEARCH_LIMIT)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[SearchResultResponse]:
    search_mode: SearchMode = mode
    return await search_service.search(
        q=q,
        category=category,
        vendor=vendor,
        document_type=document_type,
        payment_status=payment_status,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset,
        mode=search_mode,
    )


# Filter the document corpus by category, vendor, type, status, and date range
# without a keyword query. Ordered by transaction date.
@router.get("/documents", response_model=list[SearchResultResponse])
async def list_documents(
    search_service: SearchServiceDep,
    category: Annotated[FinancialCategory | None, Query()] = None,
    vendor: Annotated[str | None, Query()] = None,
    document_type: Annotated[FinancialDocumentType | None, Query()] = None,
    payment_status: Annotated[PaymentStatus | None, Query()] = None,
    date_from: Annotated[date | None, Query(alias="from")] = None,
    date_to: Annotated[date | None, Query(alias="to")] = None,
    limit: Annotated[int, Query(ge=1, le=MAX_SEARCH_LIMIT)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[SearchResultResponse]:
    return await search_service.search(
        q=None,
        category=category,
        vendor=vendor,
        document_type=document_type,
        payment_status=payment_status,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset,
    )
