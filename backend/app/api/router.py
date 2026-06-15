from fastapi import APIRouter

from app.api.routes.financial_records import router as financial_records_router
from app.api.routes.health import router as health_router
from app.api.routes.uploads import router as uploads_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(uploads_router)
api_router.include_router(financial_records_router)
