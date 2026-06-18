from uuid import UUID

from asyncpg import Pool, Record

DOCUMENT_TYPE_RULE_COLUMNS = """
    id,
    keyword,
    document_type,
    created_at,
    updated_at
"""


class DocumentTypeRuleRepository:
    def __init__(self, database_pool: Pool, workspace_id: UUID) -> None:
        self.database_pool = database_pool
        self.workspace_id = workspace_id

    # List every learned document-type rule
    async def list_all(self) -> list[Record]:
        async with self.database_pool.acquire() as connection:
            return await connection.fetch(
                f"""
                SELECT
                    {DOCUMENT_TYPE_RULE_COLUMNS}
                FROM document_type_rules
                WHERE workspace_id = $1
                ORDER BY updated_at DESC
                """,
                self.workspace_id,
            )

    # Learn a rule. Keyed by keyword so correcting the same vendor again just
    # updates the document type instead of duplicating.
    async def upsert(self, *, keyword: str, document_type: str) -> Record | None:
        async with self.database_pool.acquire() as connection:
            return await connection.fetchrow(
                f"""
                INSERT INTO document_type_rules (workspace_id, keyword, document_type)
                VALUES ($1, $2, $3)
                ON CONFLICT (workspace_id, keyword) DO UPDATE SET
                    document_type = EXCLUDED.document_type
                RETURNING
                    {DOCUMENT_TYPE_RULE_COLUMNS}
                """,
                self.workspace_id,
                keyword,
                document_type,
            )
