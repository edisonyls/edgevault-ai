import json
import logging
import re
from datetime import date
from typing import cast

from app.schemas.assistant import AssistantQueryType
from app.services.assistant.intent import Intent, build_intent
from app.services.assistant.llm_client import ChatCompletionClient

logger = logging.getLogger(__name__)

# The LLM only chooses the fuzzy bits — query type and category. Dates are left
# to the deterministic period parser, which small models handle poorly.
SYSTEM_PROMPT = """You convert a personal-finance question into a JSON label. \
The user is asking about their own spending, bills, and subscriptions.

Reply with ONLY a JSON object, no prose and no code fences:
{"query_type": <type>, "category": <category or null>}

query_type is exactly one of:
- "top_spending_category": which category they spent the most on. \
e.g. "what do I spend most on", "biggest expense", "where does my money go"
- "category_total": how much they spent in ONE specific category. Requires a category. \
e.g. "how much on groceries", "total fuel costs"
- "unpaid_bills": bills not yet paid, owed, or coming due. \
e.g. "what do I owe", "outstanding bills", "anything due soon"
- "subscriptions": recurring or subscription payments. \
e.g. "what am I subscribed to", "streaming services", "recurring charges"
- "spending_summary": an overview or breakdown of spending. \
e.g. "summarise my spending", "overview of last month"
- "unknown": anything not about the user's own spending, bills, or subscriptions.

category is null unless query_type is "category_total". When set it is exactly one of:
"groceries", "utilities" (electricity/gas/water), "internet_phone" (internet/mobile/phone), \
"transport" (fuel/petrol/uber/transit/parking), "subscription", "other".

Examples:
Q: "what did I waste the most money on?" -> {"query_type":"top_spending_category","category":null}
Q: "how much have I spent on petrol?" -> {"query_type":"category_total","category":"transport"}
Q: "any bills I haven't paid?" -> {"query_type":"unpaid_bills","category":null}
Q: "am I wasting money on streaming services?" -> {"query_type":"subscriptions","category":null}
Q: "give me a rundown of my spending" -> {"query_type":"spending_summary","category":null}
Q: "what's the capital of France?" -> {"query_type":"unknown","category":null}"""

_QUERY_TYPES: set[str] = {
    "top_spending_category",
    "category_total",
    "unpaid_bills",
    "subscriptions",
    "spending_summary",
    "unknown",
}
_CATEGORIES: set[str] = {
    "groceries",
    "utilities",
    "internet_phone",
    "transport",
    "subscription",
    "other",
}

_JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)


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


class LLMIntentParser:
    """
    Translates a question into an Intent using an OpenAI-compatible model.
    """

    def __init__(self, client: ChatCompletionClient) -> None:
        self.client = client

    async def parse(self, question: str, today: date | None = None) -> Intent | None:
        content = await self.client.complete(system=SYSTEM_PROMPT, user=question)
        if content is None:
            return None

        parsed = _extract_json(content)
        if parsed is None:
            logger.warning("LLM intent output was not valid JSON: %r", content)
            return None

        query_type = parsed.get("query_type")
        category = parsed.get("category")

        if not isinstance(query_type, str) or query_type not in _QUERY_TYPES:
            return None
        if not isinstance(category, str) or category not in _CATEGORIES:
            category = None

        # category_total is meaningless without a category; let the next tier try.
        if query_type == "category_total" and category is None:
            return None

        return build_intent(
            query_type=cast(AssistantQueryType, query_type),
            category=cast(str | None, category),
            question=question,
            today=today,
        )
