"""
Rule-based intent parser for the spending assistant.

This is the single boundary the controlled assistant relies on: it turns a free
text question into a structured `Intent` (which query to run + extracted
parameters). Everything downstream is deterministic SQL, so the engine can only
ever answer with real numbers from the database.

A future version can swap `parse_intent` for an LLM that emits the same `Intent`
without touching the query layer.
"""

import calendar
import re
from dataclasses import dataclass
from datetime import date

from app.schemas.assistant import AssistantQueryType

# Maps free-text words to the fixed financial_records category taxonomy. The
# first keyword found in the question wins.
CATEGORY_KEYWORDS: list[tuple[str, str]] = [
    ("grocery", "groceries"),
    ("groceries", "groceries"),
    ("supermarket", "groceries"),
    ("food", "groceries"),
    ("utility", "utilities"),
    ("utilities", "utilities"),
    ("electricity", "utilities"),
    ("power bill", "utilities"),
    ("energy", "utilities"),
    ("gas", "utilities"),
    ("water", "utilities"),
    ("internet", "internet_phone"),
    ("broadband", "internet_phone"),
    ("phone", "internet_phone"),
    ("mobile", "internet_phone"),
    ("transport", "transport"),
    ("transit", "transport"),
    ("uber", "transport"),
    ("taxi", "transport"),
    ("fuel", "transport"),
    ("petrol", "transport"),
]

MONTH_NAMES: dict[str, int] = {
    "january": 1,
    "jan": 1,
    "february": 2,
    "feb": 2,
    "march": 3,
    "mar": 3,
    "april": 4,
    "apr": 4,
    "may": 5,
    "june": 6,
    "jun": 6,
    "july": 7,
    "jul": 7,
    "august": 8,
    "aug": 8,
    "september": 9,
    "sept": 9,
    "sep": 9,
    "october": 10,
    "oct": 10,
    "november": 11,
    "nov": 11,
    "december": 12,
    "dec": 12,
}

YEAR_RE = re.compile(r"\b(20\d{2})\b")

ALL_TIME = "all time"


@dataclass(slots=True)
class Intent:
    query_type: AssistantQueryType
    category: str | None = None
    vendor: str | None = None
    date_from: date | None = None
    date_to: date | None = None
    period_label: str = ALL_TIME


def _month_bounds(year: int, month: int) -> tuple[date, date]:
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, 1), date(year, month, last_day)


def _infer_year(month: int, today: date, prefer_future: bool) -> int:
    # A bare month name resolves to its nearest occurrence. Spending questions
    # look backward ("spent in July" = last July); due-date questions look
    # forward ("due in July" = the upcoming July).
    if prefer_future:
        return today.year if month >= today.month else today.year + 1
    return today.year if month <= today.month else today.year - 1


# "not unpaid" / "nothing overdue" etc. — a negated bill question shouldn't be
# treated as a request for outstanding bills.
_NEGATED_UNPAID_RE = re.compile(
    r"\b(?:not|never|aren't|isn't|don't|no)\b[^.?!]{0,20}"
    r"\b(?:unpaid|overdue|outstanding|due|owe|owing)\b"
)


# "unpaid" / "due" / "owe" -> outstanding bills. Also drives forward-looking
# month inference, since these questions are about upcoming due dates.
def _is_unpaid(lowered: str) -> bool:
    if _NEGATED_UNPAID_RE.search(lowered):
        return False
    return any(word in lowered for word in ("unpaid", "overdue", "outstanding")) or bool(
        re.search(r"\b(due|owe|owing)\b", lowered)
    )


def _parse_period(
    lowered: str, today: date, prefer_future: bool = False
) -> tuple[date | None, date | None, str]:
    if "last month" in lowered:
        year = today.year if today.month > 1 else today.year - 1
        month = today.month - 1 or 12
        start, end = _month_bounds(year, month)
        return start, end, "last month"

    if "this month" in lowered:
        start, end = _month_bounds(today.year, today.month)
        return start, end, "this month"

    if "year to date" in lowered or "ytd" in lowered:
        return date(today.year, 1, 1), today, "year to date"

    if "last year" in lowered:
        year = today.year - 1
        return date(year, 1, 1), date(year, 12, 31), str(year)

    if "this year" in lowered:
        return date(today.year, 1, 1), date(today.year, 12, 31), str(today.year)

    if "today" in lowered:
        return today, today, "today"

    for name, month in MONTH_NAMES.items():
        if re.search(rf"\b{name}\b", lowered):
            year_match = YEAR_RE.search(lowered)
            year = int(year_match[1]) if year_match else _infer_year(
                month, today, prefer_future)
            start, end = _month_bounds(year, month)
            return start, end, f"{calendar.month_name[month]} {year}"

    return None, None, ALL_TIME


def match_category(lowered: str) -> str | None:
    """The fixed-taxonomy category named in the question, if any. The first
    keyword found wins. Shared with the LLM tier to validate its category."""
    best: tuple[int, str] | None = None
    for keyword, category in CATEGORY_KEYWORDS:
        match = re.search(rf"\b{re.escape(keyword)}\b", lowered)
        if match and (best is None or match.start() < best[0]):
            best = (match.start(), category)
    return best[1] if best is not None else None


# Words signalling "the single biggest", e.g. "what do I spend the most on".
_SUPERLATIVES = ("most", "highest", "biggest", "largest", "top")


def _wants_top(lowered: str) -> bool:
    spend_terms = ("spend", "spent", "spending",
                   "expense", "expenses", "cost", "costs")
    return any(word in lowered for word in _SUPERLATIVES) and any(
        word in lowered for word in spend_terms
    )


# "vendors" / "merchants" / "who do I pay" -> list the businesses on record.
_VENDOR_LIST_RE = re.compile(
    r"\b(?:vendors?|merchants?|payees?|suppliers?)\b|\bwho (?:do|am) i pay(?:ing)?\b"
)


def _wants_top_vendor(lowered: str) -> bool:
    """A superlative aimed at vendors, e.g. "which vendor do I pay the most"."""
    return bool(_VENDOR_LIST_RE.search(lowered)) and any(
        word in lowered for word in _SUPERLATIVES
    )

# "how many invoices / documents / receipts do I have" -> a document count.
# Deliberately excludes "bills" so unpaid-bill questions still route to unpaid.
_DOC_COUNT_RE = re.compile(
    r"\b(?:how many|number of|count of)\b.*"
    r"\b(?:documents?|invoices?|receipts?|records?|uploads?|files?|statements?)\b"
)

# Generic spend words that, absent a specific category, mean "all spending".
_SPEND_TERMS = (
    "spend", "spent", "spending", "cost", "costs",
    "expense", "expenses", "paid", "pay",
)
_TOTAL_TERMS = ("total", "overall", "altogether", "in all")


def _wants_vendor_list(lowered: str) -> bool:
    return bool(_VENDOR_LIST_RE.search(lowered))


def _wants_document_count(lowered: str) -> bool:
    return bool(_DOC_COUNT_RE.search(lowered))


def _wants_spend_overview(lowered: str) -> bool:
    """A general 'how much / total / overall spending' question, no category named."""
    return any(term in lowered for term in _SPEND_TERMS) or any(
        term in lowered for term in _TOTAL_TERMS
    )


def build_intent(
    query_type: AssistantQueryType,
    category: str | None,
    question: str,
    today: date | None = None,
) -> Intent:
    """
    Assemble an Intent from a query type + category, attaching the time window 
    with the same deterministic period parser the rules use. Category is only 
    meaningful for category_total; it's dropped otherwise so downstream handlers 
    behave identically to the rules path.
    """
    today = today or date.today()
    lowered = question.lower()
    date_from, date_to, period_label = _parse_period(
        lowered, today, prefer_future=query_type == "unpaid_bills"
    )
    return Intent(
        query_type=query_type,
        category=category if query_type == "category_total" else None,
        date_from=date_from,
        date_to=date_to,
        period_label=period_label,
    )


def build_vendor_intent(question: str, vendor: str, today: date | None = None) -> Intent:
    """
    Assemble an intent scoped to a single named vendor, honouring any period and
    "unpaid"/"owe" framing in the question. Used when the service layer matches a
    vendor we hold records for, so vendor questions resolve deterministically.
    """
    today = today or date.today()
    lowered = question.lower()
    is_unpaid = _is_unpaid(lowered)
    date_from, date_to, period_label = _parse_period(
        lowered, today, prefer_future=is_unpaid)
    return Intent(
        query_type="unpaid_bills" if is_unpaid else "vendor_total",
        vendor=vendor,
        date_from=date_from,
        date_to=date_to,
        period_label=period_label,
    )


def parse_intent(question: str, today: date | None = None) -> Intent:
    """Map a question to a structured intent. Order encodes precedence."""
    today = today or date.today()
    lowered = question.lower()
    is_unpaid = _is_unpaid(lowered)
    date_from, date_to, period_label = _parse_period(
        lowered, today, prefer_future=is_unpaid)

    def intent(query_type: AssistantQueryType, category: str | None = None) -> Intent:
        return Intent(
            query_type=query_type,
            category=category,
            date_from=date_from,
            date_to=date_to,
            period_label=period_label,
        )

    # superlative + vendor -> the single biggest vendor. Checked before the plain
    # vendor list so "which vendor do I pay the most" names one, not all six.
    if _wants_top_vendor(lowered):
        return intent("top_vendor")

    # "vendors" / "merchants" / "who do I pay" -> list the businesses on record.
    # Checked first so "not unpaid bills, but vendors" lands here, not on unpaid.
    if _wants_vendor_list(lowered):
        return intent("vendor_list")

    # "how many invoices / documents do I have" -> a document count.
    if _wants_document_count(lowered):
        return intent("document_count")

    # "unpaid" / "due" / "owe" -> outstanding bills.
    if is_unpaid:
        return intent("unpaid_bills")

    # "subscription" / "recurring" -> recurring vendors.
    if "subscription" in lowered or "recurring" in lowered:
        return intent("subscriptions")

    # "summary" / "summarise" / "overview" / "breakdown" -> period breakdown.
    if any(
        word in lowered
        for word in ("summary", "summarise", "summarize", "overview", "breakdown", "break down")
    ):
        return intent("spending_summary")

    # superlative + spend -> top category.
    if _wants_top(lowered):
        return intent("top_spending_category")

    # a category keyword (optionally with a month) -> that category's total.
    category = match_category(lowered)
    if category is not None:
        return intent("category_total", category=category)

    # a plain "how much did I spend" / "total spending" with no category named
    # -> a whole-of-spending breakdown, rather than punting to the LLM.
    if _wants_spend_overview(lowered):
        return intent("spending_summary")

    return intent("unknown")
