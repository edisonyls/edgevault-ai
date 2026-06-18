import asyncio
import contextlib
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.database import close_database_pool, create_database_pool
from app.services.assistant.clients import build_local_client
from app.services.assistant.warmup import keep_model_warm


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()

    # It creates one shared async Postgres pool at startup
    app.state.database_pool = await create_database_pool(settings)

    warm_task: asyncio.Task[None] | None = None

    # Initialize the LOCAL llm client and keep it warm
    local_client = build_local_client(settings)

    # Ping the local
    if local_client is not None and settings.assistant_llm_keep_warm:
        warm_task = asyncio.create_task(
            keep_model_warm(
                local_client, settings.assistant_llm_keep_warm_interval)
        )

    try:
        yield
    finally:
        # cleans up background resources on shutdown
        if warm_task is not None:
            warm_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await warm_task
        await close_database_pool(app.state.database_pool)


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix=settings.api_prefix)

    return app


app = create_app()
