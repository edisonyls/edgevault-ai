from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.core.database import DatabasePoolDep, check_database_connection
from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])
type SettingsDep = Annotated[Settings, Depends(get_settings)]


@router.get("/health", response_model=HealthResponse)
async def health_check(settings: SettingsDep,
                       database_pool: DatabasePoolDep) -> HealthResponse:
    database_ok = await check_database_connection(database_pool)
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        environment=settings.environment,
        database="ok" if database_ok else "unavailable",
    )
