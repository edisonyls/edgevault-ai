from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

# The set of rule-based intents the controlled query engine can answer.
# "unknown" means no rule matched, in which case the assistant explains what it
# can do instead of guessing.
AssistantQueryType = Literal[
    "top_spending_category",
    "category_total",
    "unpaid_bills",
    "subscriptions",
    "spending_summary",
    "unknown",
]


class AssistantQueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)

    @field_validator("question")
    @classmethod
    def strip_question(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("question must not be empty")
        return cleaned


class SupportingRecord(BaseModel):
    """
    A single financial record cited as evidence for an answer. These come
    straight from the database so the user can verify every claim.
    """

    upload_id: UUID
    vendor: str | None
    amount: float | None
    date: date | None
    category: str | None


class AssistantQueryResponse(BaseModel):
    answer: str
    query_type: AssistantQueryType
    supporting_records: list[SupportingRecord]
