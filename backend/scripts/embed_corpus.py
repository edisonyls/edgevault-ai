"""Backfill document embeddings into pgvector for the owner workspace.

The RAG extractor retrieves nearest corrected documents from the
``document_embeddings`` table, so that table has to be populated first. This
re-runs the *production* embedding pipeline (EmbeddingService + fastembed) over
every upload that has succeeded OCR text — it adds no new embedding logic, it
just fills the table the app would normally fill on upload.

Idempotent: each upload's embeddings are replaced, so re-running is safe.

Usage:
    uv run python scripts/embed_corpus.py
"""

import asyncio
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.auth import OWNER_WORKSPACE_ID  # noqa: E402
from app.core.config import get_settings  # noqa: E402
from app.core.database import create_database_pool  # noqa: E402
from app.repositories.document_embeddings import (  # noqa: E402
    DocumentEmbeddingRepository,
)
from app.services.embeddings import get_embedding_model  # noqa: E402
from app.services.embeddings.service import EmbeddingService  # noqa: E402

UPLOADS_SQL = """
    SELECT u.id AS upload_id, de.raw_text
    FROM resume_uploads u
    JOIN LATERAL (
        SELECT raw_text
        FROM document_extractions
        WHERE upload_id = u.id
          AND status = 'succeeded'
          AND raw_text IS NOT NULL
        ORDER BY created_at DESC
        LIMIT 1
    ) de ON TRUE
    WHERE u.workspace_id = $1
    ORDER BY u.created_at ASC
"""


async def main() -> None:
    settings = get_settings()
    pool = await create_database_pool(settings)
    try:
        async with pool.acquire() as connection:
            rows = await connection.fetch(UPLOADS_SQL, OWNER_WORKSPACE_ID)

        repository = DocumentEmbeddingRepository(pool, OWNER_WORKSPACE_ID)
        service = EmbeddingService(
            repository=repository,
            model=get_embedding_model(settings),
            chunk_size=settings.embedding_chunk_size,
            chunk_overlap=settings.embedding_chunk_overlap,
        )

        total_chunks = 0
        for row in rows:
            chunks = await service.embed_and_store(
                upload_id=row["upload_id"], text=row["raw_text"]
            )
            total_chunks += chunks

        print(
            f"Embedded {len(rows)} uploads into pgvector "
            f"({total_chunks} chunks, model {service.model.name})."
        )
    finally:
        await pool.close()


if __name__ == "__main__":
    asyncio.run(main())
