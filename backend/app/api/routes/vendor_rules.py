from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.core.database import DatabasePoolDep
from app.repositories.vendor_rules import VendorRuleRepository
from app.schemas.vendor_rules import (
    VendorRuleCreate,
    VendorRuleResponse,
    VendorRuleUpdate,
)
from app.services.vendor_rules import VendorRuleConflictError, VendorRuleService

router = APIRouter(prefix="/vendor-rules", tags=["vendor-rules"])


def get_vendor_rule_service(database_pool: DatabasePoolDep) -> VendorRuleService:
    return VendorRuleService(VendorRuleRepository(database_pool))


type VendorRuleServiceDep = Annotated[VendorRuleService, Depends(
    get_vendor_rule_service)]


# List every vendor rule, most recently updated first.
@router.get("", response_model=list[VendorRuleResponse])
async def list_vendor_rules(
    vendor_rule_service: VendorRuleServiceDep,
) -> list[VendorRuleResponse]:
    return await vendor_rule_service.list_rules()


# Learn a rule.
@router.post("", response_model=VendorRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_vendor_rule(
    vendor_rule_service: VendorRuleServiceDep,
    payload: VendorRuleCreate,
) -> VendorRuleResponse:
    try:
        return await vendor_rule_service.create(payload)
    except VendorRuleConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


# Update a rule.
@router.patch("/{rule_id}", response_model=VendorRuleResponse)
async def update_vendor_rule(
    vendor_rule_service: VendorRuleServiceDep,
    rule_id: UUID,
    update: VendorRuleUpdate,
) -> VendorRuleResponse:
    try:
        rule = await vendor_rule_service.update(rule_id, update)
    except VendorRuleConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    if rule is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor rule not found.",
        )

    return rule


# Delete a rule.
@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vendor_rule(
    vendor_rule_service: VendorRuleServiceDep,
    rule_id: UUID,
) -> Response:
    deleted = await vendor_rule_service.delete(rule_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor rule not found.",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
