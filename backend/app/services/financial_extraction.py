import logging
import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from uuid import UUID

from asyncpg import Record

from app.repositories.document_type_rules import DocumentTypeRuleRepository
from app.repositories.extraction_corrections import ExtractionCorrectionRepository
from app.repositories.financial_records import FinancialRecordRepository
from app.repositories.vendor_rules import VendorRuleRepository
from app.schemas.financial_records import (
    DocumentTypeSource,
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

# Record fields that make up one labelled example.
SNAPSHOT_FIELDS = (
    "document_type",
    "vendor",
    "transaction_date",
    "due_date",
    "total_amount",
    "currency",
    "category",
    "payment_status",
)

# All vendor rules now live in the vendor_rules table so the engine matches
# against the rules passed in from the database rather than a hardcoded list.
VendorRule = tuple[str, str, FinancialCategory]

DocumentTypeRule = tuple[str, FinancialDocumentType]

# Keyword ranking
TOTAL_KEYWORDS: list[tuple[str, int]] = [
    ("grand total", 5),
    ("invoice amount", 5),
    ("total amount", 5),
    ("total", 3),
    ("total due", 2),
    ("amount due", 2),
    ("balance due", 2),
]

LOOKAHEAD_MIN_WEIGHT = 2
VALUE_LOOKAHEAD_LINES = 2
MAX_LABEL_WORDS = 6
# Shortest collapsed keyword allowed to match a condensed domain/email, to avoid
# spurious hits from very short vendor names.
MIN_COLLAPSED_KEYWORD_LENGTH = 5

AMOUNT_RE = re.compile(r"\d[\d,]*\.\d{2}")

CURRENCY_AMOUNT_RE = re.compile(
    r"(?P<sym>[$€£])?\s?(?P<num>\d[\d,]*\.\d{2})(?!\d)(?!\s?%)"
)
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
    document_type_source: DocumentTypeSource
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


# Parse every date in a single line, in the order they appear.
def _parse_dates_in(line: str) -> list[date]:
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


# Detect the vendor by looking for the keywords from the extracted text
def _detect_vendor(
    text: str,
    vendor_rules: Sequence[VendorRule] = (),
) -> tuple[str | None, FinancialCategory | None]:
    lowered = text.lower()
    best: tuple[int, str, FinancialCategory] | None = None

    for keyword, vendor, category in vendor_rules:
        match = re.search(rf"\b{re.escape(keyword)}\b", lowered)
        if match and (best is None or match.start() < best[0]):
            best = (match.start(), vendor, category)

    # Known vendor is found in the text, return it immediately. (vendor, category)
    if best is not None:
        return best[1], best[2]

    # If no exact keyword match is found, try collapsed matching to catch
    # condensed domains or emails
    collapsed = re.sub(r"\s+", "", lowered)
    for keyword, vendor, category in vendor_rules:
        token = re.sub(r"\s+", "", keyword)
        if " " not in keyword or len(token) < MIN_COLLAPSED_KEYWORD_LENGTH:
            continue
        idx = collapsed.find(token)
        if idx != -1 and (best is None or idx < best[0]):
            best = (idx, vendor, category)

    if best is not None:
        return best[1], best[2]

    # None of the rules matched. We will scan the OCR text and guess the vendor
    # from the top by excluding the dates and amounts.
    for line in text.splitlines():
        candidate = line.strip()
        if len(candidate) < 2 or not re.search(r"[A-Za-z]", candidate):
            continue
        if _parse_dates_in(candidate) or AMOUNT_RE.search(candidate):
            continue
        return candidate[:MAX_VENDOR_GUESS_LENGTH], None
    return None, None


# Decide the document type and record how it was decided.
def _resolve_document_type(
    text: str,
    document_type_rules: Sequence[DocumentTypeRule],
) -> tuple[FinancialDocumentType, DocumentTypeSource]:
    lowered = text.lower()

    #  We first get the document type from the keywords in the OCR text
    if "amount due" in lowered or "due date" in lowered or "bill" in lowered:
        return "bill", "document"
    if "tax invoice" in lowered or "invoice" in lowered:
        return "invoice", "document"
    if "receipt" in lowered:
        return "receipt", "document"
    if "statement" in lowered:
        return "statement", "document"

    best: tuple[int, FinancialDocumentType] | None = None

    # If no document-type keywords are found, we look for learned rules based
    # on the vendor name.
    for keyword, document_type in document_type_rules:
        match = re.search(rf"\b{re.escape(keyword)}\b", lowered)
        if match and (best is None or match.start() < best[0]):
            best = (match.start(), document_type)

    if best is not None:
        return best[1], "learned"

    # None of the rules matched. Default to "receipt" since it's the most common
    return "receipt", "default"


# Extract every currency amount on a line, flagging which ones carried an
# explicit currency symbol so a "$xxx" can be preferred over a bare "xxx".
def _currency_amounts(line: str) -> list[tuple[bool, Decimal]]:
    found: list[tuple[bool, Decimal]] = []
    for match in CURRENCY_AMOUNT_RE.finditer(line):
        amount = _parse_amount(match.group("num"))
        if amount is not None:
            found.append((match.group("sym") is not None, amount))
    return found


# Choose the amount that best represents a line's value
def _pick_line_amount(amounts: list[tuple[bool, Decimal]]) -> tuple[bool, Decimal]:
    symboled = [amount for has_symbol, amount in amounts if has_symbol]
    if symboled:
        return True, symboled[-1]
    return False, amounts[-1][1]


def _pick_stacked_amount(amounts: list[tuple[bool, Decimal]]) -> tuple[bool, Decimal]:
    symboled = [amount for has_symbol, amount in amounts if has_symbol]
    pool = symboled if symboled else [amount for _, amount in amounts]
    return bool(symboled), max(pool)


def _is_label_line(line: str) -> bool:
    return len(line.split()) <= MAX_LABEL_WORDS


# When a label sits on its own line, scan the next few non-empty lines for the
# value printed beneath it.
def _lookahead_amount(lines: list[str], start: int) -> tuple[bool, Decimal] | None:
    collected: list[tuple[bool, Decimal]] = []
    seen = 0
    for line in lines[start + 1:]:
        if not line.strip():
            continue
        amounts = _currency_amounts(line)
        if amounts:
            collected.extend(amounts)
            continue
        # The first non-empty line without an amount ends the value stack.
        if collected:
            break
        seen += 1
        if seen >= VALUE_LOOKAHEAD_LINES:
            break
    if not collected:
        return None
    return _pick_stacked_amount(collected)


# Detect the total amount by looking for lines containing total-related keywords.
def _detect_total(text: str, lines: list[str]) -> Decimal | None:
    best: tuple[int, bool, int, Decimal] | None = None

    for idx, line in enumerate(lines):
        lowered = line.lower()
        if "subtotal" in lowered:
            continue

        weight = max(
            (value for keyword, value in TOTAL_KEYWORDS if keyword in lowered),
            default=0,
        )
        if weight == 0:
            continue

        amounts = _currency_amounts(line)
        if amounts:
            has_symbol, amount = _pick_line_amount(amounts)
        elif weight >= LOOKAHEAD_MIN_WEIGHT and _is_label_line(line):
            picked = _lookahead_amount(lines, idx)
            if picked is None:
                continue
            has_symbol, amount = picked
        else:
            continue

        candidate = (weight, has_symbol, idx, amount)
        if best is None or candidate[:3] >= best[:3]:
            best = candidate

    if best is not None:
        return best[3]

    all_amounts = [amount for line in lines for _,
                   amount in _currency_amounts(line)]
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


# Get the transaction date and due date by looking for date keywords and
# applying some heuristics to assign them to the right field.
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
    if "paid" in lowered or "payment received" in lowered:
        return "paid"
    if any(marker in lowered for marker in ("amount due", "balance due", "outstanding")):
        return "unpaid"
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


# Turn the OCR text into structured financial fields using deterministic rules
def extract_financials(
    text: str,
    vendor_rules: Sequence[VendorRule] = (),
    document_type_rules: Sequence[DocumentTypeRule] = (),
) -> ExtractedFinancials:
    lines = text.splitlines()
    # Get the vendor and its category
    vendor, category = _detect_vendor(text, vendor_rules)
    vendor_is_known = category is not None
    # Get the document type
    document_type, document_type_source = _resolve_document_type(
        text, document_type_rules)
    # Get the transaction date and due date
    transaction_date, due_date = _detect_dates(lines)

    total_amount = _detect_total(text, lines)

    currency = _detect_currency(text)

    payment_status = _detect_payment_status(text, document_type, due_date)

    result = ExtractedFinancials(
        document_type=document_type,
        document_type_source=document_type_source,
        vendor=vendor,
        transaction_date=transaction_date,
        due_date=due_date,
        total_amount=total_amount,
        currency=currency,
        category=category or "other",
        payment_status=payment_status,
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
        document_type_source=row["document_type_source"],
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


# Snapshot a record's extracted fields into a JSON-serialisable dict. Dates and
# Decimals become strings so the snapshot round-trips cleanly through JSONB.
def _record_snapshot(row: Record) -> dict[str, object]:
    snapshot: dict[str, object] = {}
    for field in SNAPSHOT_FIELDS:
        value = row[field]
        if isinstance(value, Decimal):
            snapshot[field] = str(value)
        elif isinstance(value, date):
            snapshot[field] = value.isoformat()
        else:
            snapshot[field] = value
    return snapshot


class FinancialRecordService:
    def __init__(
        self,
        repository: FinancialRecordRepository,
        vendor_rule_repository: VendorRuleRepository,
        correction_repository: ExtractionCorrectionRepository,
        document_type_rule_repository: DocumentTypeRuleRepository,
    ) -> None:
        self.repository = repository
        self.vendor_rule_repository = vendor_rule_repository
        self.correction_repository = correction_repository
        self.document_type_rule_repository = document_type_rule_repository

    # Get all the vendor rules
    async def _load_vendor_rules(self) -> list[VendorRule]:
        rows = await self.vendor_rule_repository.list_all()
        return [(row["keyword"], row["vendor"], row["category"]) for row in rows]

    # Get all the document type rules
    async def _load_document_type_rules(self) -> list[DocumentTypeRule]:
        rows = await self.document_type_rule_repository.list_all()
        return [(row["keyword"], row["document_type"]) for row in rows]

    # Run the rules engine over OCR text and persist the structured record.
    async def extract_and_store(self, *, upload_id: UUID, text: str | None) -> None:
        if not text or not text.strip():
            return

        vendor_rules = await self._load_vendor_rules()

        document_type_rules = await self._load_document_type_rules()

        extracted = extract_financials(text, vendor_rules, document_type_rules)

        await self.repository.upsert_from_extraction(
            upload_id=upload_id,
            document_type=extracted.document_type,
            document_type_source=extracted.document_type_source,
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

        existing = await self.repository.get(record_id)
        if existing is None:
            return None
        if not update_data:
            return row_to_financial_record(existing)

        row = await self.repository.update(record_id, update_data)
        if row is None:
            return None

        # Capture the before/after as a labelled example before anything else
        # consumes the correction.
        await self._capture_correction(existing, row, set(update_data))

        # A correction to vendor or category teaches a reusable rule so future
        # documents mentioning this vendor are categorised automatically.
        if "vendor" in update_data or "category" in update_data:
            await self._learn_rule_from_record(row)

        # A correction to the document type teaches a rule keyed by vendor so
        # future documents from the same vendor are classified the same way.
        if "document_type" in update_data:
            await self._learn_document_type_rule_from_record(existing, row)

        return row_to_financial_record(row)

    # Log one correction event
    async def _capture_correction(
        self,
        before: Record,
        after: Record,
        updated_fields: set[str],
    ) -> None:
        try:
            predicted = _record_snapshot(before)
            corrected = _record_snapshot(after)
            changed = sorted(
                field
                for field in updated_fields
                if field in SNAPSHOT_FIELDS
                and predicted.get(field) != corrected.get(field)
            )
            if not changed:
                return

            await self.correction_repository.insert(
                workspace_id=self.repository.workspace_id,
                upload_id=after["upload_id"],
                financial_record_id=after["id"],
                predicted=predicted,
                corrected=corrected,
                changed_fields=changed,
                extraction_method=before["extraction_method"],
            )
        except Exception:
            logger.exception(
                "Failed to capture correction for record %s", after["id"])

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

    async def _learn_document_type_rule_from_record(
        self,
        before: Record,
        after: Record,
    ) -> None:
        if before["document_type_source"] == "document":
            return

        vendor = (after["vendor"] or "").strip()
        document_type = (after["document_type"] or "").strip()

        if not vendor or not document_type:
            return

        try:
            await self.document_type_rule_repository.upsert(
                keyword=vendor.lower(),
                document_type=document_type,
            )
        except Exception:
            logger.exception(
                "Failed to learn document-type rule from record %s", after["id"])
