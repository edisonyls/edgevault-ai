from uuid import UUID

from asyncpg import Pool, Record


class DocumentEmbeddingRepository:
    def __init__(self, database_pool: Pool) -> None:
        self.database_pool = database_pool

    # Replace all embeddings for an upload in one transaction so re-embedding a
    # document is idempotent.
    async def replace_for_upload(
        self,
        *,
        upload_id: UUID,
        embedding_model: str,
        chunks: list[tuple[int, str, list[float]]],
    ) -> None:
        async with self.database_pool.acquire() as connection:
            async with connection.transaction():
                await connection.execute(
                    "DELETE FROM document_embeddings WHERE upload_id = $1",
                    upload_id,
                )

                if not chunks:
                    return

                await connection.executemany(
                    """
                    INSERT INTO document_embeddings (
                        upload_id,
                        chunk_index,
                        content,
                        embedding_model,
                        embedding
                    )
                    VALUES ($1, $2, $3, $4, $5)
                    """,
                    [
                        (upload_id, chunk_index, content,
                         embedding_model, embedding)
                        for chunk_index, content, embedding in chunks
                    ],
                )

    # Nearest chunks to a query embedding by cosine distance.
    async def search(
        self,
        *,
        embedding: list[float],
        limit: int,
    ) -> list[Record]:
        async with self.database_pool.acquire() as connection:
            return await connection.fetch(
                """
                SELECT
                    upload_id,
                    chunk_index,
                    content,
                    embedding <=> $1 AS distance
                FROM document_embeddings
                ORDER BY embedding <=> $1
                LIMIT $2
                """,
                embedding,
                limit,
            )

    # Count total chunks in the database, for monitoring and to help set limits.
    async def count(self) -> int:
        async with self.database_pool.acquire() as connection:
            return await connection.fetchval(
                "SELECT count(*) FROM document_embeddings"
            )
