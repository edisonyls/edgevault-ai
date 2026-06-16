import logging
import re
from collections.abc import Sequence
from datetime import date
from decimal import Decimal

from asyncpg import Record

from app.repositories.assistant import AssistantRepository
from app.schemas.assistant import (
    AssistantQueryResponse,
    SupportingRecord,
)
from app.services.assistant.intent import (
    ALL_TIME,
    Intent,
    build_vendor_intent,
    parse_intent,
)
from app.services.assistant.llm_intent import LLMIntentParser

logger = logging.getLogger(__name__)

# How many evidence records to attach to an answer.
EVIDENCE_LIMIT = 10
# How many categories to name in a spending summary.
SUMMARY_TOP_CATEGORIES = 3
# Shortest vendor-name token we'll match on its own to avoid latching onto short, common words.
MIN_VENDOR_TOKEN = 5
# Vendor-name tokens that are ordinary English words
_GENERIC_VENDOR_TOKENS = {
    "energy", "circle", "group", "store", "shop", "company", "services", "solutions",
}

# Friendlier labels for the fixed category taxonomy when shown in answer text.
CATEGORY_DISPLAY: dict[str, str] = {
    "groceries": "groceries",
    "utilities": "utilities",
    "internet_phone": "internet & phone",
    "transport": "transport",
    "subscription": "subscriptions",
    "other": "other expenses",
}

# Periods that read naturally on their own; everything else (a specific month or
# year) takes an "in " prefix, e.g. "in May 2026".
_BARE_PERIODS = {"this month", "last month",
                 "this year", "last year", "today", "year to date"}

CAPABILITIES = (
    "I can answer questions about your spending from your uploaded documents — "
    'for example: "What did I spend the most on this month?", '
    '"How much did I spend on groceries in May?", "Find unpaid bills", or '
    '"Which subscriptions am I paying for?"'
)


def _money(value: Decimal | float | int | None) -> str:
    return f"${value or 0:,.2f}"


def _display_category(category: str | None) -> str:
    if category is None:
        return "uncategorised"
    return CATEGORY_DISPLAY.get(category, category)


def _plural(word: str, count: int) -> str:
    return word if count == 1 else f"{word}s"


def _humanize_list(items: Sequence[str]) -> str:
    items = list(items)
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return f"{', '.join(items[:-1])} and {items[-1]}"


def _period_phrase(label: str) -> str:
    """Natural phrase for a period, including any preposition. "" for all time."""
    if label == ALL_TIME:
        return ""
    if label in _BARE_PERIODS:
        return label
    return f"in {label}"


def _suffix(label: str) -> str:
    """Trailing period phrase ready to append to a sentence, e.g. " this month"."""
    phrase = _period_phrase(label)
    return f" {phrase}" if phrase else ""


def _to_supporting(rows: Sequence[Record]) -> list[SupportingRecord]:
    return [
        SupportingRecord(
            upload_id=row["upload_id"],
            vendor=row["vendor"],
            amount=float(row["total_amount"]
                         ) if row["total_amount"] is not None else None,
            date=row["transaction_date"],
            category=row["category"],
        )
        for row in rows
    ]


class AssistantService:
    def __init__(
        self,
        repository: AssistantRepository,
        *,
        local_parser: LLMIntentParser | None = None,
        fallback_parser: LLMIntentParser | None = None,
    ) -> None:
        self.repository = repository
        self.local_parser = local_parser
        self.fallback_parser = fallback_parser

    async def answer(self, question: str, *, today: date | None = None) -> AssistantQueryResponse:
        if today is None:
            today = await self.repository.current_date()
        intent, source = await self._resolve_intent(question, today)
        answer_text, supporting = await self._dispatch(intent)

        await self.repository.log_query(
            question=question,
            answer=answer_text,
            query_type=intent.query_type,
            source=source,
        )

        return AssistantQueryResponse(
            answer=answer_text,
            query_type=intent.query_type,
            supporting_records=supporting,
        )

    async def _resolve_intent(self, question: str, today: date) -> tuple[Intent, str]:
        """
        Rules first (instant); only escalate to the LLM tiers when a tier can't
        place the question. The first tier to return a usable intent wins.
        """
        intent = parse_intent(question, today)

        vendor = await self._match_known_vendor(question)
        if vendor is not None:
            return build_vendor_intent(question, vendor, today), "rules"

        if intent.query_type != "unknown":
            return intent, "rules"

        tiers = (
            (self.local_parser, "local_llm"),
            (self.fallback_parser, "fallback_llm"),
        )
        for parser, source in tiers:
            if parser is None:
                continue
            try:
                resolved = await parser.parse(question, today)
            except Exception:
                logger.exception(
                    "Assistant %s tier failed; falling through.", source)
                continue
            if resolved is not None and resolved.query_type != "unknown":
                return resolved, source

        return intent, "rules"

    async def _match_known_vendor(self, question: str) -> str | None:
        """
        Return the canonical name of a vendor mentioned in the question, matched
        against the vendors actually on record. Prefers a full-name hit; falls
        back to a distinctive single token (e.g. "anthropic", "chargefox").
        """
        rows = await self.repository.list_vendors()
        names = [row["vendor"] for row in rows if row["vendor"]]
        if not names:
            return None
        lowered = question.lower()

        # Longest full names first so "Origin Energy" wins over a stray "energy".
        for name in sorted(names, key=len, reverse=True):
            if re.search(rf"\b{re.escape(name.lower())}\b", lowered):
                return name

        for name in names:
            for token in re.findall(r"[a-z0-9]+", name.lower()):
                if len(token) < MIN_VENDOR_TOKEN or token in _GENERIC_VENDOR_TOKENS:
                    continue
                if re.search(rf"\b{re.escape(token)}\b", lowered):
                    return name
        return None

    async def _dispatch(self, intent: Intent) -> tuple[str, list[SupportingRecord]]:
        handlers = {
            "top_spending_category": self._top_spending_category,
            "category_total": self._category_total,
            "vendor_total": self._vendor_total,
            "vendor_list": self._vendor_list,
            "document_count": self._document_count,
            "unpaid_bills": self._unpaid_bills,
            "subscriptions": self._subscriptions,
            "spending_summary": self._spending_summary,
        }
        handler = handlers.get(intent.query_type)
        if handler is None:
            return CAPABILITIES, []
        return await handler(intent)

    async def _top_spending_category(self, intent: Intent) -> tuple[str, list[SupportingRecord]]:
        row = await self.repository.top_category(date_from=intent.date_from, date_to=intent.date_to)
        if row is None or row["total"] is None:
            return f"I couldn't find any spending records{_suffix(intent.period_label)}.", []

        category = row["category"]
        records = await self.repository.records(
            category=category,
            date_from=intent.date_from,
            date_to=intent.date_to,
            order="amount",
            limit=EVIDENCE_LIMIT,
        )
        answer = (
            f"Your highest spending category{_suffix(intent.period_label)} is "
            f"{_display_category(category)} at {_money(row['total'])}."
        )
        return answer, _to_supporting(records)

    async def _category_total(self, intent: Intent) -> tuple[str, list[SupportingRecord]]:
        category = intent.category
        assert category is not None  # category_total is only produced with a category
        aggregate = await self.repository.category_aggregate(
            category=category, date_from=intent.date_from, date_to=intent.date_to
        )
        count = aggregate["count"]
        display = _display_category(category)
        if count == 0:
            return f"I couldn't find any {display} spending{_suffix(intent.period_label)}.", []

        records = await self.repository.records(
            category=category,
            date_from=intent.date_from,
            date_to=intent.date_to,
            order="amount",
            limit=EVIDENCE_LIMIT,
        )
        answer = (
            f"You spent {_money(aggregate['total'])} on {display}"
            f"{_suffix(intent.period_label)}, across {count} {_plural('record', count)}."
        )
        return answer, _to_supporting(records)

    async def _unpaid_bills(self, intent: Intent) -> tuple[str, list[SupportingRecord]]:
        aggregate = await self.repository.unpaid_aggregate(
            date_from=intent.date_from, date_to=intent.date_to, vendor=intent.vendor
        )
        count = aggregate["count"]
        # Period filters apply to the due date, so phrase it as "due …".
        due_phrase = (
            f" due {_period_phrase(intent.period_label)}" if intent.period_label != ALL_TIME else ""
        )
        vendor_phrase = f" to {intent.vendor}" if intent.vendor else ""
        if count == 0:
            return f"You don't have any unpaid bills{vendor_phrase}{due_phrase}.", []

        records = await self.repository.records(
            payment_status="unpaid",
            vendor=intent.vendor,
            date_from=intent.date_from,
            date_to=intent.date_to,
            date_column="due_date",
            require_amount=False,
            order="due",
            limit=EVIDENCE_LIMIT,
        )
        answer = f"You have {count} unpaid {_plural('bill', count)}{vendor_phrase}{due_phrase}"
        if aggregate["total"]:
            answer += f" totalling {_money(aggregate['total'])}"
        answer += "."
        return answer, _to_supporting(records)

    async def _vendor_total(self, intent: Intent) -> tuple[str, list[SupportingRecord]]:
        vendor = intent.vendor
        assert vendor is not None  # vendor_total is only produced with a vendor
        aggregate = await self.repository.vendor_aggregate(
            vendor=vendor, date_from=intent.date_from, date_to=intent.date_to
        )
        count = aggregate["count"]
        if count == 0:
            return f"I couldn't find any spending for {vendor}{_suffix(intent.period_label)}.", []

        records = await self.repository.records(
            vendor=vendor,
            date_from=intent.date_from,
            date_to=intent.date_to,
            order="amount",
            limit=EVIDENCE_LIMIT,
        )
        answer = (
            f"You spent {_money(aggregate['total'])} at {vendor}"
            f"{_suffix(intent.period_label)}, across {count} {_plural('record', count)}."
        )
        return answer, _to_supporting(records)

    async def _vendor_list(self, intent: Intent) -> tuple[str, list[SupportingRecord]]:
        vendors = await self.repository.list_vendors()
        if not vendors:
            return "I couldn't find any vendors in your documents.", []

        names = [row["vendor"] for row in vendors]
        records = await self.repository.records(
            require_amount=False, order="date", limit=EVIDENCE_LIMIT
        )
        answer = (
            f"You have {len(names)} {_plural('vendor', len(names))}: "
            f"{_humanize_list(names)}."
        )
        return answer, _to_supporting(records)

    async def _document_count(self, intent: Intent) -> tuple[str, list[SupportingRecord]]:
        counts = await self.repository.document_count(
            date_from=intent.date_from, date_to=intent.date_to
        )
        documents = counts["documents"]
        record_count = counts["records"]
        if record_count == 0:
            return f"I couldn't find any documents{_suffix(intent.period_label)}.", []

        records = await self.repository.records(
            date_from=intent.date_from,
            date_to=intent.date_to,
            require_amount=False,
            order="date",
            limit=EVIDENCE_LIMIT,
        )
        answer = (
            f"You have {documents} {_plural('document', documents)}{_suffix(intent.period_label)} "
            f"with {record_count} financial {_plural('record', record_count)}."
        )
        return answer, _to_supporting(records)

    async def _subscriptions(self, intent: Intent) -> tuple[str, list[SupportingRecord]]:
        vendors = await self.repository.subscription_vendors()
        if not vendors:
            return "I couldn't find any subscriptions in your documents.", []

        names = [row["vendor"] or "an unnamed vendor" for row in vendors]
        records = await self.repository.records(
            category="subscription",
            require_amount=False,
            order="date",
            limit=EVIDENCE_LIMIT,
        )
        answer = (
            f"You're paying for {len(names)} {_plural('subscription', len(names))}: "
            f"{_humanize_list(names)}."
        )
        return answer, _to_supporting(records)

    async def _spending_summary(self, intent: Intent) -> tuple[str, list[SupportingRecord]]:
        breakdown = await self.repository.category_breakdown(
            date_from=intent.date_from, date_to=intent.date_to
        )
        total = sum((row["total"] for row in breakdown), Decimal(0))
        count = sum(row["count"] for row in breakdown)
        if count == 0:
            return f"I couldn't find any spending records{_suffix(intent.period_label)}.", []

        phrase = _period_phrase(intent.period_label)
        lead = f"{phrase[0].upper()}{phrase[1:]} you spent" if phrase else "Overall, you spent"

        parts = [
            f"{_display_category(row['category'])} {_money(row['total'])}"
            for row in breakdown[:SUMMARY_TOP_CATEGORIES]
        ]
        answer = (
            f"{lead} {_money(total)} across {count} {_plural('record', count)}. "
            f"Top categories: {_humanize_list(parts)}."
        )

        records = await self.repository.records(
            date_from=intent.date_from,
            date_to=intent.date_to,
            order="amount",
            limit=EVIDENCE_LIMIT,
        )
        return answer, _to_supporting(records)
