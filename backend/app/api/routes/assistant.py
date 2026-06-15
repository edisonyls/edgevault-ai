from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.database import DatabasePoolDep
from app.repositories.assistant import AssistantRepository
from app.schemas.assistant import AssistantQueryRequest, AssistantQueryResponse
from app.services.assistant.service import AssistantService

router = APIRouter(prefix="/assistant", tags=["assistant"])


def get_assistant_service(database_pool: DatabasePoolDep) -> AssistantService:
    return AssistantService(AssistantRepository(database_pool))


type AssistantServiceDep = Annotated[AssistantService, Depends(
    get_assistant_service)]


@router.post("/query", response_model=AssistantQueryResponse)
async def query_assistant(
    assistant_service: AssistantServiceDep,
    request: AssistantQueryRequest,
) -> AssistantQueryResponse:
    """
    Answer a natural-language question about spending and documents.
    """
    return await assistant_service.answer(request.question)
