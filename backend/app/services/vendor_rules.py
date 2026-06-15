from uuid import UUID

from asyncpg import Record
from asyncpg.exceptions import UniqueViolationError

from app.repositories.vendor_rules import VendorRuleRepository
from app.schemas.vendor_rules import (
    VendorRuleCreate,
    VendorRuleResponse,
    VendorRuleUpdate,
)


class VendorRuleConflictError(Exception):
    """Raised when a create or edit would give two rules the same keyword."""


# Helper to convert a database row to a VendorRuleResponse.
def row_to_vendor_rule(row: Record) -> VendorRuleResponse:
    return VendorRuleResponse(
        id=row["id"],
        keyword=row["keyword"],
        vendor=row["vendor"],
        category=row["category"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class VendorRuleService:
    def __init__(self, repository: VendorRuleRepository) -> None:
        self.repository = repository

    # List every vendor rule, most recently updated first.
    async def list_rules(self) -> list[VendorRuleResponse]:
        rows = await self.repository.list_all()
        return [row_to_vendor_rule(row) for row in rows]

    # Add a new rule by hand. Raises VendorRuleConflictError when the keyword is
    # already taken.
    async def create(self, payload: VendorRuleCreate) -> VendorRuleResponse:
        try:
            row = await self.repository.create(
                keyword=payload.keyword,
                vendor=payload.vendor,
                category=payload.category,
            )
        except UniqueViolationError as exc:
            raise VendorRuleConflictError(
                "A rule with that keyword already exists.") from exc

        # create() only returns None when nothing was inserted, which the unique
        # violation above already covers, so a row is guaranteed here.
        assert row is not None
        return row_to_vendor_rule(row)

    # Apply an edit to a rule. Returns None when the rule does not exist and
    # raises VendorRuleConflictError when the new keyword is already taken.
    async def update(
        self,
        rule_id: UUID,
        update: VendorRuleUpdate,
    ) -> VendorRuleResponse | None:
        update_data = update.model_dump(exclude_unset=True)
        if not update_data:
            existing = await self.repository.get(rule_id)
            return row_to_vendor_rule(existing) if existing is not None else None

        try:
            row = await self.repository.update(rule_id, update_data)
        except UniqueViolationError as exc:
            raise VendorRuleConflictError(
                "Another rule already uses that keyword.") from exc

        return row_to_vendor_rule(row) if row is not None else None

    async def delete(self, rule_id: UUID) -> bool:
        return await self.repository.delete(rule_id)
