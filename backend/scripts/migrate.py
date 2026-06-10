import asyncio
import sys
from pathlib import Path

import asyncpg

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# This should be imported after sys.path otherwise Python won't find app.core.config
from app.core.config import get_settings  # noqa: E402

MIGRATIONS_DIR = BACKEND_ROOT / "db" / "migrations"


async def ensure_schema_migrations(connection: asyncpg.Connection) -> None:
    await connection.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            filename TEXT PRIMARY KEY,
            applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )


async def applied_migrations(connection: asyncpg.Connection) -> set[str]:
    rows = await connection.fetch("SELECT filename FROM schema_migrations")
    return {row["filename"] for row in rows}


async def apply_migration(connection: asyncpg.Connection, path: Path) -> None:
    sql = path.read_text(encoding="utf-8")
    async with connection.transaction():
        await connection.execute(sql)
        await connection.execute(
            "INSERT INTO schema_migrations (filename) VALUES ($1)",
            path.name,
        )


async def main() -> None:
    settings = get_settings()
    connection = await asyncpg.connect(dsn=settings.database_url)

    try:
        await ensure_schema_migrations(connection)
        applied = await applied_migrations(connection)
        migration_paths = sorted(MIGRATIONS_DIR.glob("*.sql"))

        for path in migration_paths:
            if path.name in applied:
                print(f"Skipping {path.name}")
                continue

            print(f"Applying {path.name}")
            await apply_migration(connection, path)
    finally:
        await connection.close()


if __name__ == "__main__":
    asyncio.run(main())
