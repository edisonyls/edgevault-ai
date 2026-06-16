from collections.abc import Sequence
from typing import Protocol

from app.services.financial_extraction import (
    ExtractedFinancials,
    VendorRule,
    extract_financials,
)


class Extractor(Protocol):
    name: str

    def extract(self, text: str) -> dict[str, object]:
        """Return a field snapshot keyed by the SNAPSHOT_FIELDS names."""
        ...


def extracted_to_snapshot(result: ExtractedFinancials) -> dict[str, object]:
    return {
        "document_type": result.document_type,
        "vendor": result.vendor,
        "transaction_date": (
            result.transaction_date.isoformat() if result.transaction_date else None
        ),
        "due_date": result.due_date.isoformat() if result.due_date else None,
        "total_amount": (
            str(result.total_amount) if result.total_amount is not None else None
        ),
        "currency": result.currency,
        "category": result.category,
        "payment_status": result.payment_status,
    }


class RulesExtractor:
    """The current deterministic rules engine — the Phase 0 baseline."""

    name = "rules_v1"

    def __init__(self, rules: Sequence[VendorRule] = ()) -> None:
        self._rules = rules

    def extract(self, text: str) -> dict[str, object]:
        return extracted_to_snapshot(extract_financials(text, self._rules))
