from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

# The rules engine classifies into a fixed taxonomy; "manual" marks a record a
# user has corrected so re-extraction never clobbers their edits.
FinancialDocumentType = Literal["receipt",
                                "invoice", "bill", "statement", "other"]
FinancialCategory = Literal[
    "groceries",
    "utilities",
    "internet_phone",
    "transport",
    "subscription",
    "other",
]
PaymentStatus = Literal["paid", "unpaid", "unknown"]
ExtractionMethod = Literal["rules_v1", "manual"]
DocumentTypeSource = Literal["document", "learned", "default"]


class FinancialRecordResponse(BaseModel):
    id: UUID
    upload_id: UUID
    document_type: FinancialDocumentType | None
    document_type_source: DocumentTypeSource | None
    vendor: str | None
    transaction_date: date | None
    due_date: date | None
    total_amount: float | None
    currency: str
    category: FinancialCategory | None
    payment_status: PaymentStatus | None
    extraction_method: ExtractionMethod
    confidence: float | None
    created_at: datetime
    updated_at: datetime


class FinancialRecordUpdate(BaseModel):
    """
    Manual correction payload. Every field is optional; only the fields that
    are present are written, and any successful write flips the record to the
    'manual' extraction method.
    """

    document_type: FinancialDocumentType | None = None
    vendor: str | None = Field(default=None, max_length=255)
    transaction_date: date | None = None
    due_date: date | None = None
    total_amount: Decimal | None = Field(
        default=None, ge=0, max_digits=14, decimal_places=2)
    currency: str | None = Field(default=None, min_length=1, max_length=8)
    category: FinancialCategory | None = None
    payment_status: PaymentStatus | None = None

    @field_validator("vendor", "currency")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None
