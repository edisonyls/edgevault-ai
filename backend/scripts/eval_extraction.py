"""Evaluate an extractor against the corrections you've made.

Two complementary views:

  * Offline accuracy — re-run an extractor over every document you've manually
    corrected and score it field by field. This is how we
    compare the rules baseline against future RAG / fine-tuned extractors.

  * Online correction rate — from the captured correction log, how often each
    field was actually wrong. This needs no re-running.

Usage:
    uv run python scripts/eval_extraction.py            # rules_v1 (frozen baseline)
    uv run python scripts/eval_extraction.py rag         # RAG candidate vs Pi qwen
"""

import asyncio
import sys
import time
from pathlib import Path

import asyncpg

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# Imported after sys.path is set so `app.*` resolves.
from app.core.auth import OWNER_WORKSPACE_ID  # noqa: E402
from app.core.config import get_settings  # noqa: E402
from app.core.database import create_database_pool  # noqa: E402
from app.services.assistant.llm_client import ChatCompletionClient  # noqa: E402
from app.services.embeddings import get_embedding_model  # noqa: E402
from app.services.eval.extractor import Extractor, RulesExtractor  # noqa: E402
from app.services.eval.metrics import evaluate  # noqa: E402
from app.services.eval.rag_extractor import LabelledExample, RagExtractor  # noqa: E402
from app.services.financial_extraction import (  # noqa: E402
    SNAPSHOT_FIELDS,
    VendorRule,
    _record_snapshot,
)

# RAG extraction prompts are larger than intent prompts and the Pi is slow, so
# give the local model more room than the assistant's default timeout.
RAG_LLM_TIMEOUT = 120.0
RAG_TOP_K = 2

RAG_LLM_EXTRA_PARAMS: dict[str, object] = {
    "temperature": 0,
    "max_tokens": 200,
}

# Pull the latest succeeded OCR text for each upload that has a manually
# corrected record, and treat the corrected record as the gold label.
LABELLED_EXAMPLES_SQL = """
    SELECT fr.*, de.raw_text
    FROM financial_records fr
    JOIN resume_uploads u ON u.id = fr.upload_id
    JOIN LATERAL (
        SELECT raw_text
        FROM document_extractions
        WHERE upload_id = fr.upload_id
          AND status = 'succeeded'
          AND raw_text IS NOT NULL
        ORDER BY created_at DESC
        LIMIT 1
    ) de ON TRUE
    WHERE fr.extraction_method = 'manual'
      AND u.workspace_id = $1
"""


async def load_labelled_examples(
    connection: asyncpg.Connection,
) -> list[tuple[dict[str, object], str]]:
    rows = await connection.fetch(LABELLED_EXAMPLES_SQL, OWNER_WORKSPACE_ID)
    return [(_record_snapshot(row), row["raw_text"]) for row in rows]


async def load_corpus(connection: asyncpg.Connection) -> list[LabelledExample]:
    """Same labelled set, but carrying upload_id so RAG can do leave-one-out
    retrieval and key demonstrations back to their gold targets."""
    rows = await connection.fetch(LABELLED_EXAMPLES_SQL, OWNER_WORKSPACE_ID)
    return [
        LabelledExample(
            upload_id=row["upload_id"],
            text=row["raw_text"],
            target=_record_snapshot(row),
        )
        for row in rows
    ]


async def load_vendor_rules(connection: asyncpg.Connection) -> list[VendorRule]:
    rows = await connection.fetch(
        "SELECT keyword, vendor, category FROM vendor_rules WHERE workspace_id = $1",
        OWNER_WORKSPACE_ID,
    )
    return [(row["keyword"], row["vendor"], row["category"]) for row in rows]


async def _predict(extractor: Extractor, text: str) -> dict[str, object]:
    """Use the extractor's async path when it has one (RAG hits the network);
    otherwise call the synchronous Protocol method (rules)."""
    extract_async = getattr(extractor, "extract_async", None)
    if extract_async is not None:
        return await extract_async(text)
    return extractor.extract(text)


async def print_offline_report(
    extractor: Extractor, examples: list[tuple[dict, str]]
) -> None:
    show_progress = getattr(extractor, "extract_async", None) is not None
    total = len(examples)
    started = time.monotonic()

    scored = []
    for index, (gold, text) in enumerate(examples, start=1):
        predicted = await _predict(extractor, text)
        scored.append((gold, predicted))
        if show_progress:
            elapsed = time.monotonic() - started
            print(
                f"  [{index}/{total}] {elapsed:.0f}s elapsed",
                file=sys.stderr,
                flush=True,
            )

    report = evaluate(scored, SNAPSHOT_FIELDS)

    print(f"\n=== Offline accuracy — extractor: {extractor.name} ===")
    print(f"labelled documents: {report.example_count}")
    print(f"{'field':<18}{'accuracy':>10}{'correct/labelled':>20}")
    print("-" * 48)
    for score in report.field_scores:
        ratio = f"{score.correct}/{score.labeled}"
        print(f"{score.field:<18}{score.accuracy:>9.0%}{ratio:>20}")
    print("-" * 48)
    print(f"{'exact match':<18}{report.exact_match_rate:>9.0%}"
          f"{f'{report.exact_match}/{report.example_count}':>20}")


async def print_online_report(connection: asyncpg.Connection) -> None:
    # Only first-pass predictions, not corrections of corrections.
    rows = await connection.fetch(
        """
        SELECT changed_fields
        FROM extraction_corrections
        WHERE extraction_method = 'rules_v1'
          AND workspace_id = $1
        """,
        OWNER_WORKSPACE_ID,
    )
    print("\n=== Online correction rate (rules_v1 first-pass) ===")
    if not rows:
        print("no corrections captured yet")
        return

    total = len(rows)
    miss_counts = {field: 0 for field in SNAPSHOT_FIELDS}
    for row in rows:
        for field in row["changed_fields"]:
            if field in miss_counts:
                miss_counts[field] += 1

    print(f"corrected documents: {total}")
    print(f"{'field':<18}{'corrected %':>14}{'count':>10}")
    print("-" * 42)
    for field in SNAPSHOT_FIELDS:
        count = miss_counts[field]
        print(f"{field:<18}{count / total:>13.0%}{count:>10}")


async def run_rules_report(
    connection: asyncpg.Connection, examples: list[tuple[dict, str]]
) -> None:
    rules = await load_vendor_rules(connection)
    await print_offline_report(RulesExtractor(rules), examples)


async def run_rag_report(
    connection: asyncpg.Connection,
    examples: list[tuple[dict, str]],
    settings,  # noqa: ANN001 - Settings, imported lazily to keep the rules path clean
) -> None:
    corpus = await load_corpus(connection)
    vendor_rules = await load_vendor_rules(connection)
    model = get_embedding_model(settings)
    llm = ChatCompletionClient(
        base_url=settings.assistant_llm_base_url,
        model=settings.assistant_llm_model,
        timeout=RAG_LLM_TIMEOUT,
        extra_params=RAG_LLM_EXTRA_PARAMS,
    )
    # A vector-codec-aware pool so the query embedding encodes for `<=>`.
    pool = await create_database_pool(settings)
    try:
        extractor = RagExtractor(
            examples=corpus,
            pool=pool,
            model=model,
            llm=llm,
            vendor_rules=vendor_rules,
            top_k=RAG_TOP_K,
        )
        await print_offline_report(extractor, examples)
    finally:
        await pool.close()


async def main() -> None:
    mode = sys.argv[1].lower() if len(sys.argv) > 1 else "rules"
    if mode not in {"rules", "rag"}:
        print(f"unknown extractor '{mode}' — use 'rules' (default) or 'rag'")
        return

    settings = get_settings()
    connection = await asyncpg.connect(dsn=settings.database_url)
    try:
        examples = await load_labelled_examples(connection)

        if not examples:
            print("\n=== Offline accuracy ===")
            print("no manually corrected documents yet — nothing to score")
        elif mode == "rag":
            await run_rag_report(connection, examples, settings)
        else:
            await run_rules_report(connection, examples)

        await print_online_report(connection)
    finally:
        await connection.close()


if __name__ == "__main__":
    asyncio.run(main())
