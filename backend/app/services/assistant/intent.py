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


# "unpaid" / "due" / "owe" -> outstanding bills. Also drives forward-looking
# month inference, since these questions are about upcoming due dates.
def _is_unpaid(lowered: str) -> bool:
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


def _match_category(lowered: str) -> str | None:
    best: tuple[int, str] | None = None
    for keyword, category in CATEGORY_KEYWORDS:
        match = re.search(rf"\b{re.escape(keyword)}\b", lowered)
        if match and (best is None or match.start() < best[0]):
            best = (match.start(), category)
    return best[1] if best is not None else None


def _wants_top(lowered: str) -> bool:
    superlatives = ("most", "highest", "biggest", "largest", "top")
    spend_terms = ("spend", "spent", "spending",
                   "expense", "expenses", "cost", "costs")
    return any(word in lowered for word in superlatives) and any(
        word in lowered for word in spend_terms
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
    category = _match_category(lowered)
    if category is not None:
        return intent("category_total", category=category)

    return intent("unknown")
