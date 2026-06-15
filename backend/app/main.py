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

# Gives the app one shared DB pool and guarantees both are cleaned up on shutdown.


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    app.state.database_pool = await create_database_pool(settings)

    warm_task: asyncio.Task[None] | None = None
    local_client = build_local_client(settings)
    if local_client is not None and settings.assistant_llm_keep_warm:
        warm_task = asyncio.create_task(
            keep_model_warm(
                local_client, settings.assistant_llm_keep_warm_interval)
        )

    try:
        yield
    finally:
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

    @app.get("/", include_in_schema=False)
    async def root() -> dict[str, str]:
        return {"service": settings.app_name}

    return app


app = create_app()
