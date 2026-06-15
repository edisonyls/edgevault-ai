import logging
import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from uuid import UUID

from asyncpg import Record

from app.repositories.financial_records import FinancialRecordRepository
from app.repositories.vendor_rules import VendorRuleRepository
from app.schemas.financial_records import (
    FinancialCategory,
    FinancialDocumentType,
    FinancialRecordResponse,
    FinancialRecordUpdate,
    PaymentStatus,
)

logger = logging.getLogger(__name__)

RULES_VERSION = "rules_v1"
DEFAULT_CURRENCY = "AUD"
MAX_VENDOR_GUESS_LENGTH = 60

# All vendor rules now live in the vendor_rules table so the engine matches
# against the rules passed in from the database rather than a hardcoded list.
VendorRule = tuple[str, str, FinancialCategory]

# Higher weight wins; "subtotal" lines are ignored entirely.
TOTAL_KEYWORDS: list[tuple[str, int]] = [
    ("balance due", 4),
    ("amount due", 4),
    ("total due", 4),
    ("grand total", 3),
    ("total amount", 3),
    ("total", 1),
]

AMOUNT_RE = re.compile(r"\d[\d,]*\.\d{2}")
NUMERIC_DATE_RE = re.compile(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b")
ISO_DATE_RE = re.compile(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b")
TEXT_DATE_RE = re.compile(
    r"\b(\d{1,2})(?:st|nd|rd|th)?\s+"
    r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+(\d{2,4})\b",
    re.IGNORECASE,
)
MONTH_FIRST_DATE_RE = re.compile(
    r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+"
    r"(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{2,4})\b",
    re.IGNORECASE,
)

MONTHS = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}


@dataclass(slots=True)
class ExtractedFinancials:
    document_type: FinancialDocumentType | None
    vendor: str | None
    transaction_date: date | None
    due_date: date | None
    total_amount: Decimal | None
    currency: str
    category: FinancialCategory | None
    payment_status: PaymentStatus | None
    confidence: float


def _normalize_year(year: int) -> int:
    return year + 2000 if year < 100 else year


def _safe_date(year: int, month: int, day: int) -> date | None:
    try:
        return date(_normalize_year(year), month, day)
    except ValueError:
        return None


def _parse_dates_in(line: str) -> list[date]:
    """Parse every date in a single line, in the order they appear."""
    found: list[tuple[int, date]] = []

    for match in ISO_DATE_RE.finditer(line):
        parsed = _safe_date(int(match[1]), int(match[2]), int(match[3]))
        if parsed:
            found.append((match.start(), parsed))

    # Australian convention: day comes first in numeric dates.
    for match in NUMERIC_DATE_RE.finditer(line):
        parsed = _safe_date(int(match[3]), int(match[2]), int(match[1]))
        if parsed:
            found.append((match.start(), parsed))

    for match in TEXT_DATE_RE.finditer(line):
        month = MONTHS[match[2][:3].lower()]
        parsed = _safe_date(int(match[3]), month, int(match[1]))
        if parsed:
            found.append((match.start(), parsed))

    for match in MONTH_FIRST_DATE_RE.finditer(line):
        month = MONTHS[match[1][:3].lower()]
        parsed = _safe_date(int(match[3]), month, int(match[2]))
        if parsed:
            found.append((match.start(), parsed))

    return [parsed for _, parsed in sorted(found, key=lambda item: item[0])]


def _parse_amount(raw: str) -> Decimal | None:
    try:
        return Decimal(raw.replace(",", ""))
    except InvalidOperation:
        return None


# Detect the vendor and category based on known keywords, or heuristics if no known vendor is found.
def _match_rules(
    lowered: str,
    rules: Sequence[VendorRule],
) -> tuple[str, FinancialCategory] | None:
    best: tuple[int, str, FinancialCategory] | None = None

    for keyword, vendor, category in rules:
        match = re.search(rf"\b{re.escape(keyword)}\b", lowered)
        if match and (best is None or match.start() < best[0]):
            best = (match.start(), vendor, category)

    return (best[1], best[2]) if best is not None else None


# Detect the vendor and category by matching the document against the known
# vendor rules, then fall back to a header heuristic when none match.
def _detect_vendor(
    text: str,
    rules: Sequence[VendorRule] = (),
) -> tuple[str | None, FinancialCategory | None]:
    lowered = text.lower()
    matched = _match_rules(lowered, rules)
    if matched is not None:
        return matched

    return _guess_vendor_from_header(text), None


# If no known brand is detected, guess the vendor from the first meaningful line
# of text that isn't likely to be a date or amount.
def _guess_vendor_from_header(text: str) -> str | None:
    for line in text.splitlines():
        candidate = line.strip()
        if len(candidate) < 2 or not re.search(r"[A-Za-z]", candidate):
            continue
        if _parse_dates_in(candidate) or AMOUNT_RE.search(candidate):
            continue
        return candidate[:MAX_VENDOR_GUESS_LENGTH]

    return None


# Detect the total amount by looking for lines containing total-related
# keywords, then falling back to any amount-looking text if no keywords are found.
def _detect_total(text: str, lines: list[str]) -> Decimal | None:
    best: tuple[int, Decimal] | None = None

    for line in lines:
        lowered = line.lower()
        if "subtotal" in lowered:
            continue

        amounts = AMOUNT_RE.findall(line)
        if not amounts:
            continue

        weight = max(
            (value for keyword, value in TOTAL_KEYWORDS if keyword in lowered),
            default=0,
        )
        if weight == 0:
            continue

        amount = _parse_amount(amounts[-1])
        if amount is None:
            continue

        # >= lets a later line of equal weight win, since the grand total is
        # usually the last total-looking line on the page.
        if best is None or weight >= best[0]:
            best = (weight, amount)

    if best is not None:
        return best[1]

    all_amounts = [parsed for raw in AMOUNT_RE.findall(
        text) if (parsed := _parse_amount(raw))]
    return max(all_amounts) if all_amounts else None


# Detect the currency by looking for common currency indicators, defaulting to
# AUD if none are found.
def _detect_currency(text: str) -> str:
    lowered = text.lower()
    if "aud" in lowered or "a$" in lowered:
        return "AUD"
    if "usd" in lowered or "us$" in lowered:
        return "USD"
    if "nzd" in lowered:
        return "NZD"
    if "€" in text or "eur" in lowered:
        return "EUR"
    if "£" in text or "gbp" in lowered:
        return "GBP"
    return DEFAULT_CURRENCY


def _detect_document_type(text: str) -> FinancialDocumentType:
    lowered = text.lower()
    if "tax invoice" in lowered or "invoice" in lowered:
        return "invoice"
    if "statement" in lowered:
        return "statement"
    if "amount due" in lowered or "due date" in lowered or "bill" in lowered:
        return "bill"
    if "receipt" in lowered:
        return "receipt"
    return "receipt"


def _detect_dates(lines: list[str]) -> tuple[date | None, date | None]:
    transaction_date: date | None = None
    due_date: date | None = None
    first_seen: date | None = None

    for line in lines:
        dates_in_line = _parse_dates_in(line)
        if not dates_in_line:
            continue

        first_seen = first_seen or dates_in_line[0]
        lowered = line.lower()

        if "due" in lowered and due_date is None:
            due_date = dates_in_line[0]
        elif transaction_date is None and any(
            keyword in lowered for keyword in ("date", "invoice", "issued", "receipt")
        ):
            transaction_date = dates_in_line[0]

    if transaction_date is None:
        transaction_date = first_seen if first_seen != due_date else None

    return transaction_date, due_date


# Detect the payment status based on keywords, document type, and presence of a
# due date.
def _detect_payment_status(
    text: str,
    document_type: FinancialDocumentType,
    due_date: date | None,
) -> PaymentStatus:
    lowered = text.lower()
    if any(marker in lowered for marker in ("amount due", "balance due", "outstanding")):
        return "unpaid"
    if "paid" in lowered or "payment received" in lowered:
        return "paid"
    if document_type == "receipt":
        return "paid"
    if due_date is not None:
        return "unpaid"
    return "unknown"


# Score the confidence of the extraction based on which fields were successfully
# extracted, giving more weight to the presence of a known vendor and the total
# amount.
def _score_confidence(result: ExtractedFinancials, vendor_is_known: bool) -> float:
    score = 0.2
    if vendor_is_known:
        score += 0.3
    elif result.vendor:
        score += 0.05
    if result.total_amount is not None:
        score += 0.25
    if result.transaction_date is not None:
        score += 0.15
    if result.category is not None and result.category != "other":
        score += 0.1
    return round(min(score, 0.95), 2)


# Turn the OCR text into structured financial fields using deterministic rules,
# then persist them.
def extract_financials(
    text: str,
    rules: Sequence[VendorRule] = (),
) -> ExtractedFinancials:
    lines = text.splitlines()
    vendor, category = _detect_vendor(text, rules)
    vendor_is_known = category is not None
    document_type = _detect_document_type(text)
    transaction_date, due_date = _detect_dates(lines)

    result = ExtractedFinancials(
        document_type=document_type,
        vendor=vendor,
        transaction_date=transaction_date,
        due_date=due_date,
        total_amount=_detect_total(text, lines),
        currency=_detect_currency(text),
        category=category or "other",
        payment_status=_detect_payment_status(text, document_type, due_date),
        confidence=0.0,
    )
    result.confidence = _score_confidence(result, vendor_is_known)
    return result


# Convert a database record to the API response model, applying necessary transformations.
def row_to_financial_record(row: Record) -> FinancialRecordResponse:
    total_amount = row["total_amount"]
    return FinancialRecordResponse(
        id=row["id"],
        upload_id=row["upload_id"],
        document_type=row["document_type"],
        vendor=row["vendor"],
        transaction_date=row["transaction_date"],
        due_date=row["due_date"],
        total_amount=float(total_amount) if total_amount is not None else None,
        currency=row["currency"],
        category=row["category"],
        payment_status=row["payment_status"],
        extraction_method=row["extraction_method"],
        confidence=row["confidence"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class FinancialRecordService:
    def __init__(
        self,
        repository: FinancialRecordRepository,
        vendor_rule_repository: VendorRuleRepository,
    ) -> None:
        self.repository = repository
        self.vendor_rule_repository = vendor_rule_repository

    async def _load_vendor_rules(self) -> list[VendorRule]:
        rows = await self.vendor_rule_repository.list_all()
        return [(row["keyword"], row["vendor"], row["category"]) for row in rows]

    # Run the rules engine over OCR text and persist the structured record.
    async def extract_and_store(self, *, upload_id: UUID, text: str | None) -> None:
        """
        Run the rules engine over OCR text and persist the structured record.
        """
        if not text or not text.strip():
            return

        rules = await self._load_vendor_rules()
        extracted = extract_financials(text, rules)
        await self.repository.upsert_from_extraction(
            upload_id=upload_id,
            document_type=extracted.document_type,
            vendor=extracted.vendor,
            transaction_date=extracted.transaction_date,
            due_date=extracted.due_date,
            total_amount=extracted.total_amount,
            currency=extracted.currency,
            category=extracted.category,
            payment_status=extracted.payment_status,
            extraction_method=RULES_VERSION,
            confidence=extracted.confidence,
        )

    # Get the financial record associated with a specific upload, if it exists.
    async def get_for_upload(self, upload_id: UUID) -> FinancialRecordResponse | None:
        row = await self.repository.get_for_upload(upload_id)
        return row_to_financial_record(row) if row is not None else None

    async def get(self, record_id: UUID) -> FinancialRecordResponse | None:
        row = await self.repository.get(record_id)
        return row_to_financial_record(row) if row is not None else None

    # List financial records, optionally filtering by category, with pagination.
    async def list_records(
        self,
        *,
        category: str | None,
        limit: int,
        offset: int,
    ) -> list[FinancialRecordResponse]:
        rows = await self.repository.list(category=category, limit=limit, offset=offset)
        return [row_to_financial_record(row) for row in rows]

    async def update(
        self,
        record_id: UUID,
        update: FinancialRecordUpdate,
    ) -> FinancialRecordResponse | None:
        update_data = update.model_dump(exclude_unset=True)
        if not update_data:
            existing = await self.repository.get(record_id)
            return row_to_financial_record(existing) if existing is not None else None

        row = await self.repository.update(record_id, update_data)
        if row is None:
            return None

        # A correction to vendor or category teaches a reusable rule so future
        # documents mentioning this vendor are categorised automatically.
        if "vendor" in update_data or "category" in update_data:
            await self._learn_rule_from_record(row)

        return row_to_financial_record(row)

    async def _learn_rule_from_record(self, row: Record) -> None:
        vendor = (row["vendor"] or "").strip()
        category = (row["category"] or "").strip()
        if not vendor or not category:
            return

        try:
            await self.vendor_rule_repository.upsert(
                keyword=vendor.lower(),
                vendor=vendor,
                category=category,
            )
        except Exception:
            logger.exception(
                "Failed to learn vendor rule from record %s", row["id"])
