from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.schemas.financial_records import FinancialCategory


class VendorRuleResponse(BaseModel):
    id: UUID
    keyword: str
    vendor: str
    category: FinancialCategory
    created_at: datetime
    updated_at: datetime


class VendorRuleCreate(BaseModel):
    """
    Payload for adding a vendor rule by hand. Keyword is the token matched
    against a document's text, so it is normalised to lowercase before storage.
    """

    keyword: str = Field(min_length=1, max_length=255)
    vendor: str = Field(min_length=1, max_length=255)
    category: FinancialCategory

    @field_validator("keyword")
    @classmethod
    def normalise_keyword(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if not cleaned:
            raise ValueError("Keyword must not be blank.")
        return cleaned

    @field_validator("vendor")
    @classmethod
    def strip_vendor(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Vendor must not be blank.")
        return cleaned


class VendorRuleUpdate(BaseModel):
    """
    Edit payload for a learned rule. Every field is optional; only the fields
    that are present are written. Keyword is the token matched against a
    document's text, so it is normalised to lowercase before storage.
    """

    keyword: str | None = Field(default=None, max_length=255)
    vendor: str | None = Field(default=None, max_length=255)
    category: FinancialCategory | None = None

    @field_validator("keyword")
    @classmethod
    def normalise_keyword(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip().lower()
        return cleaned or None

    @field_validator("vendor")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None
