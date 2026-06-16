import asyncio
import json
import logging
import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from uuid import UUID

from asyncpg import Pool

from app.services.assistant.llm_client import ChatCompletionClient
from app.services.embeddings.base import EmbeddingModel
from app.services.financial_extraction import SNAPSHOT_FIELDS

logger = logging.getLogger(__name__)

# Valid values per field, mirrored from app/schemas/financial_records.py. Anything
# the model returns outside these sets is dropped to None
DOCUMENT_TYPES = frozenset(
    {"receipt", "invoice", "bill", "statement", "other"})
CATEGORIES = frozenset(
    {"groceries", "utilities", "internet_phone",
        "transport", "subscription", "other"}
)
PAYMENT_STATUSES = frozenset({"paid", "unpaid", "unknown"})

# Keep the prompt lean: the Pi runs a 1.5B model with a small context window, so
# cap how much OCR text each demonstration and the query contribute.
MAX_DEMO_CHARS = 1200
MAX_QUERY_CHARS = 1600

_JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

SYSTEM_PROMPT = """You extract structured fields from a financial document's \
OCR text (receipts, invoices, bills, statements).

Reply with ONLY a JSON object, no prose and no code fences, with exactly these keys:
{
  "document_type": one of "receipt","invoice","bill","statement","other", or null,
  "vendor": the merchant/biller name as a short string, or null,
  "transaction_date": the date on the document as "YYYY-MM-DD", or null,
  "due_date": the payment due date as "YYYY-MM-DD", or null,
  "total_amount": the total payable as a plain number string e.g. "123.45", or null,
  "currency": the 3-letter ISO code e.g. "AUD","USD", or null,
  "category": one of "groceries","utilities","internet_phone","transport",\
"subscription","other", or null,
  "payment_status": one of "paid","unpaid","unknown", or null
}

Rules:
- Use null when the document does not state a field; never guess.
- total_amount is the final grand total: digits with a decimal point, no \
currency symbol and no thousands separators.
- "utilities" = electricity/gas/water; "internet_phone" = internet/mobile/phone; \
"transport" = fuel/petrol/rideshare/transit/parking.
- A receipt that has been paid is "paid"; an invoice or bill with a due date and \
no payment confirmation is "unpaid"; otherwise "unknown".

The examples below are real documents from this same workspace with their correct \
answers. Match their conventions."""


@dataclass(slots=True)
class LabelledExample:
    """One corrected document available as a retrieval neighbour / demonstration."""

    upload_id: UUID
    text: str
    target: dict[str, object]


# Nearest corrected uploads to a query embedding, restricted to the labelled
# corpus and excluding the query's own upload. MIN over a document's chunk
# embeddings = its best-matching chunk distance.
_NEIGHBOUR_SQL = """
    SELECT upload_id, MIN(embedding <=> $1) AS distance
    FROM document_embeddings
    WHERE upload_id = ANY($2::uuid[])
      AND upload_id <> $3
    GROUP BY upload_id
    ORDER BY distance
    LIMIT $4
"""


class RagExtractor:
    """Retrieval-augmented few-shot extractor over the corrected-document corpus."""

    name = "rag_v1"

    def __init__(
        self,
        *,
        examples: Sequence[LabelledExample],
        pool: Pool,
        model: EmbeddingModel,
        llm: ChatCompletionClient,
        top_k: int = 3,
    ) -> None:
        self._examples = list(examples)
        self._pool = pool
        self._model = model
        self._llm = llm
        self._top_k = top_k
        self._by_upload = {ex.upload_id: ex for ex in self._examples}
        # Identical OCR text -> upload_id, so we can find (and exclude) the query
        # document in the corpus during leave-one-out retrieval.
        self._upload_by_text = {ex.text: ex.upload_id for ex in self._examples}

    # Sync entry point for Protocol conformance / standalone use. The eval
    # harness prefers extract_async; this only runs when no loop is active.
    def extract(self, text: str) -> dict[str, object]:
        return asyncio.run(self.extract_async(text))

    async def extract_async(self, text: str) -> dict[str, object]:
        neighbours = await self._retrieve(text)
        system, user = self._build_prompt(text, neighbours)
        content = await self._llm.complete(system=system, user=user)
        if content is None:
            logger.warning(
                "RAG: LLM returned no content; scoring empty snapshot")
            return self._empty_snapshot()

        parsed = _extract_json(content)
        if parsed is None:
            logger.warning("RAG: LLM output was not valid JSON: %r", content)
            return self._empty_snapshot()
        return self._coerce_snapshot(parsed)

    async def _retrieve(self, text: str) -> list[LabelledExample]:
        if not self._examples:
            return []
        vector = await asyncio.to_thread(self._model.embed, [text.strip()])
        if not vector:
            return []

        self_upload = self._upload_by_text.get(text)
        # A UUID that can't match a real row when this document isn't in the corpus.
        exclude = self_upload or UUID(int=0)
        candidate_ids = [ex.upload_id for ex in self._examples]

        async with self._pool.acquire() as connection:
            rows = await connection.fetch(
                _NEIGHBOUR_SQL, vector[0], candidate_ids, exclude, self._top_k
            )
        return [
            self._by_upload[row["upload_id"]]
            for row in rows
            if row["upload_id"] in self._by_upload
        ]

    def _build_prompt(
        self, text: str, neighbours: Sequence[LabelledExample]
    ) -> tuple[str, str]:
        blocks: list[str] = []
        for index, example in enumerate(neighbours, start=1):
            demo_text = _clip(example.text, MAX_DEMO_CHARS)
            answer = json.dumps(_ordered(example.target), ensure_ascii=False)
            blocks.append(
                f"Example {index} document:\n{demo_text}\n\n"
                f"Example {index} answer:\n{answer}"
            )

        query = _clip(text, MAX_QUERY_CHARS)
        if blocks:
            user = "\n\n".join(
                blocks) + f"\n\nNow extract this document:\n{query}\n\nAnswer:"
        else:
            user = f"Extract this document:\n{query}\n\nAnswer:"
        return SYSTEM_PROMPT, user

    def _coerce_snapshot(self, parsed: dict[str, object]) -> dict[str, object]:
        return {
            "document_type": _enum(parsed.get("document_type"), DOCUMENT_TYPES),
            "vendor": _string(parsed.get("vendor")),
            "transaction_date": _iso_date(parsed.get("transaction_date")),
            "due_date": _iso_date(parsed.get("due_date")),
            "total_amount": _amount(parsed.get("total_amount")),
            "currency": _currency(parsed.get("currency")),
            "category": _enum(parsed.get("category"), CATEGORIES),
            "payment_status": _enum(parsed.get("payment_status"), PAYMENT_STATUSES),
        }

    @staticmethod
    def _empty_snapshot() -> dict[str, object]:
        return {field: None for field in SNAPSHOT_FIELDS}


def _extract_json(text: str) -> dict[str, object] | None:
    """Pull the first JSON object out of a model response, tolerating stray text."""
    match = _JSON_OBJECT_RE.search(text)
    if match is None:
        return None
    try:
        parsed = json.loads(match.group(0))
    except ValueError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _ordered(target: dict[str, object]) -> dict[str, object]:
    """Render a demonstration answer with keys in the canonical field order."""
    return {field: target.get(field) for field in SNAPSHOT_FIELDS}


def _clip(text: str, limit: int) -> str:
    cleaned = (text or "").strip()
    return cleaned if len(cleaned) <= limit else cleaned[:limit]


def _string(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _enum(value: object, allowed: frozenset[str]) -> str | None:
    if value is None:
        return None
    text = str(value).strip().lower()
    return text if text in allowed else None


def _iso_date(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not _ISO_DATE_RE.match(text):
        return None
    try:
        date.fromisoformat(text)
    except ValueError:
        return None
    return text


def _amount(value: object) -> str | None:
    if value is None:
        return None
    text = re.sub(r"[^0-9.\-]", "", str(value).strip())
    if not text:
        return None
    try:
        return str(Decimal(text))
    except InvalidOperation:
        return None


def _currency(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip().upper()
    return text or None
