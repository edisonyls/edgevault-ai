from asyncpg import Pool, Record

VENDOR_RULE_COLUMNS = """
    id,
    keyword,
    vendor,
    category,
    created_at,
    updated_at
"""


class VendorRuleRepository:
    def __init__(self, database_pool: Pool) -> None:
        self.database_pool = database_pool

    # List every learned vendor rule, most recently updated first so the
    # freshest correction wins when two rules share a match position.
    async def list_all(self) -> list[Record]:
        async with self.database_pool.acquire() as connection:
            return await connection.fetch(
                f"""
                SELECT
                    {VENDOR_RULE_COLUMNS}
                FROM vendor_rules
                ORDER BY updated_at DESC
                """
            )

    # Learn a rule. Keyed by keyword so correcting the same vendor again just
    # updates the canonical vendor/category instead of duplicating.
    async def upsert(self, *, keyword: str, vendor: str, category: str) -> Record | None:
        async with self.database_pool.acquire() as connection:
            return await connection.fetchrow(
                f"""
                INSERT INTO vendor_rules (keyword, vendor, category)
                VALUES ($1, $2, $3)
                ON CONFLICT (keyword) DO UPDATE SET
                    vendor = EXCLUDED.vendor,
                    category = EXCLUDED.category
                RETURNING
                    {VENDOR_RULE_COLUMNS}
                """,
                keyword,
                vendor,
                category,
            )
