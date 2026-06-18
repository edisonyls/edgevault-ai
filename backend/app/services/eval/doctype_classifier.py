"""Focused single-field classifier for document_type.

document_type is the one field the LLM beats rules on. Rather than run the full
8-field RAG extraction just to use that one field, this asks the model *only* to
classify the type — a tiny, on-task prompt: short snippets of the nearest
corrected documents (to carry the workspace's labelling convention) paired with
their type, then the query. Smaller and faster than the full extractor, and the
model isn't splitting attention across 8 fields.

It exposes the same `extract_async(text) -> dict` shape the HybridExtractor reads,
returning just `{"document_type": <type|None>}`.
"""

import json
import logging
from collections.abc import Awaitable, Callable, Sequence

from app.services.assistant.llm_client import ChatCompletionClient
from app.services.eval.rag_extractor import (
    DOCUMENT_TYPES,
    LabelledExample,
    _clip,
    _enum,
    _extract_json,
)

logger = logging.getLogger(__name__)

# document_type clues live at the top of a document, and each demo is just a
# snippet + a one-word label, so we can afford a few neighbours cheaply.
DEFAULT_TOP_K = 4
MAX_DEMO_CHARS = 400
MAX_QUERY_CHARS = 900

# Fixed priority for the fallback token-scan when JSON parsing fails.
_DOCTYPE_PRIORITY = ("statement", "invoice", "receipt", "bill", "other")

SYSTEM_PROMPT = """Classify ONE financial document by type from its OCR text.
Reply with ONLY a JSON object: {"document_type": "<type>"} where <type> is exactly one of:
- "receipt": proof of a completed purchase/payment (store receipt, paid tax invoice)
- "invoice": a request for payment, usually with an invoice number
- "bill": a recurring amount owed (utilities, telecom, council rates, body corporate)
- "statement": an account statement summarising activity over a period
- "other": none of the above
The labelled examples below are from this same workspace — match their conventions.
JSON only, no prose."""

Retriever = Callable[[str, int], Awaitable[list[LabelledExample]]]


class DocumentTypeClassifier:
    """Asks the LLM only for document_type, with few-shot type demonstrations."""

    name = "doctype_clf"

    def __init__(
        self,
        *,
        retriever: Retriever,
        llm: ChatCompletionClient,
        top_k: int = DEFAULT_TOP_K,
    ) -> None:
        self._retriever = retriever
        self._llm = llm
        self._top_k = top_k

    async def extract_async(self, text: str) -> dict[str, object]:
        neighbours = await self._retriever(text, self._top_k)
        system, user = self._build_prompt(text, neighbours)
        content = await self._llm.complete(system=system, user=user)
        return {"document_type": _parse_doctype(content)}

    def _build_prompt(
        self, text: str, neighbours: Sequence[LabelledExample]
    ) -> tuple[str, str]:
        blocks: list[str] = []
        for index, example in enumerate(neighbours, start=1):
            snippet = _clip(example.text, MAX_DEMO_CHARS)
            doctype = example.target.get("document_type")
            blocks.append(
                f"Example {index}:\n{snippet}\n"
                f'Type: {json.dumps(doctype)}'
            )

        query = _clip(text, MAX_QUERY_CHARS)
        if blocks:
            user = "\n\n".join(
                blocks) + f"\n\nClassify this document:\n{query}\n\nAnswer:"
        else:
            user = f"Classify this document:\n{query}\n\nAnswer:"
        return SYSTEM_PROMPT, user


def _parse_doctype(content: str | None) -> str | None:
    if content is None:
        return None
    parsed = _extract_json(content)
    if parsed is not None:
        return _enum(parsed.get("document_type"), DOCUMENT_TYPES)
    # Fallback: the model answered in prose — take the first type word it names.
    lowered = content.lower()
    for doctype in _DOCTYPE_PRIORITY:
        if doctype in lowered:
            return doctype
    logger.warning("doctype: could not parse a document_type from %r", content)
    return None
