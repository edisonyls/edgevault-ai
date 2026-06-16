"""Export corrected documents as a JSONL dataset.

Each line is one labelled example:
    {"upload_id": "...", "input": "<ocr text>", "target": {<corrected fields>}}

Usage:
    uv run python scripts/export_dataset.py [output_path]
    (defaults to var/datasets/extraction_dataset.jsonl)
"""

import asyncio
import json
import sys
from pathlib import Path

import asyncpg

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.auth import OWNER_WORKSPACE_ID  # noqa: E402
from app.core.config import get_settings  # noqa: E402
from app.services.financial_extraction import _record_snapshot  # noqa: E402

DEFAULT_OUTPUT = BACKEND_ROOT / "var" / "datasets" / "extraction_dataset.jsonl"

DATASET_SQL = """
    SELECT fr.upload_id, fr.*, de.raw_text
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
    ORDER BY fr.created_at ASC
"""


async def main() -> None:
    output_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUTPUT
    output_path.parent.mkdir(parents=True, exist_ok=True)

    settings = get_settings()
    connection = await asyncpg.connect(dsn=settings.database_url)
    try:
        rows = await connection.fetch(DATASET_SQL, OWNER_WORKSPACE_ID)
    finally:
        await connection.close()

    with output_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            example = {
                "upload_id": str(row["upload_id"]),
                "input": row["raw_text"],
                "target": _record_snapshot(row),
            }
            handle.write(json.dumps(example, ensure_ascii=False) + "\n")

    print(f"Wrote {len(rows)} examples to {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
