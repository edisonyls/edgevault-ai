"""Hybrid extractor — the rules baseline with selected fields overridden by the LLM.

The rules engine wins almost every field, but the coder LLM measured *better* on
`document_type` (75% vs 60%) — rules' single weakest field, and the one that gates
downstream category/payment logic. This composes the two: take the full rules
snapshot, then replace the configured fields with the LLM's value *when the LLM
produced one* (a null falls back to rules, so the override can only help or stay
neutral). Everything the LLM is worse at — payment_status, total_amount, dates,
category, vendor — stays on rules.

See docs/eval_baseline.md for the per-field comparison that motivates the choice
of override fields.
"""

import asyncio
from collections.abc import Sequence

from app.services.eval.extractor import RulesExtractor
from app.services.eval.rag_extractor import RagExtractor

# Fields where the LLM beat rules in the bake-off; everything else stays on rules.
DEFAULT_OVERRIDE_FIELDS = ("document_type",)


class HybridExtractor:
    """Rules snapshot + LLM override on the fields the LLM is actually better at."""

    name = "hybrid_v1"

    def __init__(
        self,
        *,
        rules: RulesExtractor,
        rag: RagExtractor,
        override_fields: Sequence[str] = DEFAULT_OVERRIDE_FIELDS,
    ) -> None:
        self._rules = rules
        self._rag = rag
        self._override_fields = tuple(override_fields)

    # Sync entry point for Protocol conformance; the eval harness uses the async one.
    def extract(self, text: str) -> dict[str, object]:
        return asyncio.run(self.extract_async(text))

    async def extract_async(self, text: str) -> dict[str, object]:
        # Rules produce a fresh dict per call, so mutating it here is safe.
        snapshot = self._rules.extract(text)
        predicted = await self._rag.extract_async(text)
        for field in self._override_fields:
            value = predicted.get(field)
            if value is not None:
                snapshot[field] = value
        return snapshot
