import asyncio
from uuid import UUID

from app.repositories.document_embeddings import DocumentEmbeddingRepository
from app.services.embeddings import chunk_text
from app.services.embeddings.base import EmbeddingModel


class EmbeddingService:
    """
    Generates and persists document embeddings. Chunks text, embeds each chunk
    with the configured model, and stores them.
    """

    def __init__(
        self,
        *,
        repository: DocumentEmbeddingRepository,
        model: EmbeddingModel,
        chunk_size: int,
        chunk_overlap: int,
    ) -> None:
        self.repository = repository
        self.model = model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    # Embed a single query string. Runs in a worker thread because the model is
    # synchronous and CPU-bound.
    async def embed_query(self, text: str) -> list[float] | None:
        cleaned = text.strip()
        if not cleaned:
            return None

        vectors = await asyncio.to_thread(self.model.embed, [cleaned])
        return vectors[0] if vectors else None

    # Chunk, embed, and persist the embeddings for one document's OCR text.
    async def embed_and_store(self, *, upload_id: UUID, text: str | None) -> int:
        if not text or not text.strip():
            await self.repository.replace_for_upload(
                upload_id=upload_id,
                embedding_model=self.model.name,
                chunks=[],
            )
            return 0

        chunks = chunk_text(
            text,
            size=self.chunk_size,
            overlap=self.chunk_overlap,
        )
        vectors = await asyncio.to_thread(self.model.embed, chunks)

        rows = [
            (index, content, vector)
            for index, (content, vector) in enumerate(zip(chunks, vectors, strict=True))
        ]
        await self.repository.replace_for_upload(
            upload_id=upload_id,
            embedding_model=self.model.name,
            chunks=rows,
        )
        return len(rows)
