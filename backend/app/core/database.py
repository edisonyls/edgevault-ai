from typing import Annotated

import asyncpg
from fastapi import Depends, Request

from app.core.config import Settings


async def create_database_pool(settings: Settings) -> asyncpg.Pool:
    return await asyncpg.create_pool(
        dsn=settings.database_url,
        min_size=settings.database_pool_min_size,
        max_size=settings.database_pool_max_size,
    )


async def close_database_pool(pool: asyncpg.Pool | None) -> None:
    if pool is not None:
        await pool.close()


def get_database_pool(request: Request) -> asyncpg.Pool:
    return request.app.state.database_pool


async def check_database_connection(pool: asyncpg.Pool) -> bool:
    async with pool.acquire() as connection:
        return await connection.fetchval("SELECT 1") == 1


type DatabasePoolDep = Annotated[asyncpg.Pool, Depends(get_database_pool)]
