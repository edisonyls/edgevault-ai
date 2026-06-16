from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.auth import CurrentWorkspaceDep
from app.core.database import DatabasePoolDep
from app.repositories.document_type_rules import DocumentTypeRuleRepository
from app.repositories.extraction_corrections import ExtractionCorrectionRepository
from app.repositories.financial_records import FinancialRecordRepository
from app.repositories.vendor_rules import VendorRuleRepository
from app.schemas.financial_records import (
    FinancialCategory,
    FinancialRecordResponse,
    FinancialRecordUpdate,
)
from app.services.financial_extraction import FinancialRecordService

router = APIRouter(prefix="/financial-records", tags=["financial-records"])

MAX_FINANCIAL_RECORD_LIST_LIMIT = 500


def get_financial_record_service(
    database_pool: DatabasePoolDep,
    workspace: CurrentWorkspaceDep,
) -> FinancialRecordService:
    return FinancialRecordService(
        FinancialRecordRepository(database_pool, workspace.id),
        VendorRuleRepository(database_pool, workspace.id),
        ExtractionCorrectionRepository(database_pool),
        DocumentTypeRuleRepository(database_pool, workspace.id),
    )


type FinancialRecordServiceDep = Annotated[
    FinancialRecordService, Depends(get_financial_record_service)
]


@router.get("", response_model=list[FinancialRecordResponse])
async def list_financial_records(
    financial_record_service: FinancialRecordServiceDep,
    category: Annotated[FinancialCategory | None, Query()] = None,
    limit: Annotated[int, Query(
        ge=1, le=MAX_FINANCIAL_RECORD_LIST_LIMIT)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[FinancialRecordResponse]:
    """
    List financial records, optionally filtering by category, with pagination.
    """
    return await financial_record_service.list_records(
        category=category,
        limit=limit,
        offset=offset,
    )


@router.patch("/{record_id}", response_model=FinancialRecordResponse)
async def update_financial_record(
    financial_record_service: FinancialRecordServiceDep,
    record_id: UUID,
    update: FinancialRecordUpdate,
) -> FinancialRecordResponse:
    record = await financial_record_service.update(record_id, update)

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Financial record not found.",
        )

    return record
