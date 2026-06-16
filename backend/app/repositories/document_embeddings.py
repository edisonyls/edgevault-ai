from uuid import UUID

from asyncpg import Pool, Record


class DocumentEmbeddingRepository:
    def __init__(self, database_pool: Pool, workspace_id: UUID) -> None:
        self.database_pool = database_pool
        self.workspace_id = workspace_id

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
                    """
                    DELETE FROM document_embeddings
                    USING resume_uploads
                    WHERE document_embeddings.upload_id = $1
                      AND resume_uploads.id = document_embeddings.upload_id
                      AND resume_uploads.workspace_id = $2
                    """,
                    upload_id,
                    self.workspace_id,
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
                    SELECT $1, $2, $3, $4, $5
                    WHERE EXISTS (
                        SELECT 1
                        FROM resume_uploads
                        WHERE id = $1
                          AND workspace_id = $6
                    )
                    """,
                    [
                        (
                            upload_id,
                            chunk_index,
                            content,
                            embedding_model,
                            embedding,
                            self.workspace_id,
                        )
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
                JOIN resume_uploads ON resume_uploads.id = document_embeddings.upload_id
                WHERE resume_uploads.workspace_id = $2
                ORDER BY embedding <=> $1
                LIMIT $3
                """,
                embedding,
                self.workspace_id,
                limit,
            )

    # Count total chunks in the database, for monitoring and to help set limits.
    async def count(self) -> int:
        async with self.database_pool.acquire() as connection:
            return await connection.fetchval(
                """
                SELECT count(*)
                FROM document_embeddings
                JOIN resume_uploads ON resume_uploads.id = document_embeddings.upload_id
                WHERE resume_uploads.workspace_id = $1
                """,
                self.workspace_id,
            )
