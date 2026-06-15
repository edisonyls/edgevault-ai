from uuid import UUID

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

    # Insert a brand-new rule. Raises asyncpg.UniqueViolationError when the
    # keyword already exists.
    async def create(
        self,
        *,
        keyword: str,
        vendor: str,
        category: str,
    ) -> Record | None:
        async with self.database_pool.acquire() as connection:
            return await connection.fetchrow(
                f"""
                INSERT INTO vendor_rules (keyword, vendor, category)
                VALUES ($1, $2, $3)
                RETURNING
                    {VENDOR_RULE_COLUMNS}
                """,
                keyword,
                vendor,
                category,
            )

    # Get a single rule by id.
    async def get(self, rule_id: UUID) -> Record | None:
        async with self.database_pool.acquire() as connection:
            return await connection.fetchrow(
                f"""
                SELECT
                    {VENDOR_RULE_COLUMNS}
                FROM vendor_rules
                WHERE id = $1
                """,
                rule_id,
            )

    # Update the editable columns of a rule. Raises asyncpg.UniqueViolationError
    # if the new keyword collides with another rule.
    async def update(
        self,
        rule_id: UUID,
        update_data: dict[str, object],
    ) -> Record | None:
        set_clauses: list[str] = []
        values: list[object] = []

        for column, value in update_data.items():
            values.append(value)
            set_clauses.append(f"{column} = ${len(values)}")

        values.append(rule_id)

        async with self.database_pool.acquire() as connection:
            return await connection.fetchrow(
                f"""
                UPDATE vendor_rules
                SET {", ".join(set_clauses)}
                WHERE id = ${len(values)}
                RETURNING
                    {VENDOR_RULE_COLUMNS}
                """,
                *values,
            )

    # Delete a rule. Returns True when a row was removed.
    async def delete(self, rule_id: UUID) -> bool:
        async with self.database_pool.acquire() as connection:
            row = await connection.fetchrow(
                "DELETE FROM vendor_rules WHERE id = $1 RETURNING id",
                rule_id,
            )
        return row is not None
