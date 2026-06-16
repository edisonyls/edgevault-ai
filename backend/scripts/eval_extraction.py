"""Evaluate an extractor against the corrections you've made.

Two complementary views:

  * Offline accuracy — re-run an extractor over every document you've manually
    corrected and score it field by field. This is how we
    compare the rules baseline against future RAG / fine-tuned extractors.

  * Online correction rate — from the captured correction log, how often each
    field was actually wrong. This needs no re-running.

Usage:
    uv run python scripts/eval_extraction.py
"""

import asyncio
import sys
from pathlib import Path

import asyncpg

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# Imported after sys.path is set so `app.*` resolves.
from app.core.config import get_settings  # noqa: E402
from app.services.eval.extractor import Extractor, RulesExtractor  # noqa: E402
from app.services.eval.metrics import evaluate  # noqa: E402
from app.services.financial_extraction import (  # noqa: E402
    SNAPSHOT_FIELDS,
    VendorRule,
    _record_snapshot,
)

# Pull the latest succeeded OCR text for each upload that has a manually
# corrected record, and treat the corrected record as the gold label.
LABELLED_EXAMPLES_SQL = """
    SELECT fr.*, de.raw_text
    FROM financial_records fr
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
"""


async def load_labelled_examples(
    connection: asyncpg.Connection,
) -> list[tuple[dict[str, object], str]]:
    rows = await connection.fetch(LABELLED_EXAMPLES_SQL)
    return [(_record_snapshot(row), row["raw_text"]) for row in rows]


async def load_vendor_rules(connection: asyncpg.Connection) -> list[VendorRule]:
    rows = await connection.fetch("SELECT keyword, vendor, category FROM vendor_rules")
    return [(row["keyword"], row["vendor"], row["category"]) for row in rows]


def print_offline_report(extractor: Extractor, examples: list[tuple[dict, str]]) -> None:
    scored = [(gold, extractor.extract(text)) for gold, text in examples]
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
        """
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


async def main() -> None:
    settings = get_settings()
    connection = await asyncpg.connect(dsn=settings.database_url)
    try:
        examples = await load_labelled_examples(connection)
        rules = await load_vendor_rules(connection)

        if examples:
            print_offline_report(RulesExtractor(rules), examples)
        else:
            print("\n=== Offline accuracy ===")
            print("no manually corrected documents yet — nothing to score")

        await print_online_report(connection)
    finally:
        await connection.close()


if __name__ == "__main__":
    asyncio.run(main())
