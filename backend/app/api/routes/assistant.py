from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.core.database import DatabasePoolDep
from app.repositories.assistant import AssistantRepository
from app.schemas.assistant import AssistantQueryRequest, AssistantQueryResponse
from app.services.assistant.clients import build_fallback_client, build_local_client
from app.services.assistant.llm_intent import LLMIntentParser
from app.services.assistant.service import AssistantService

router = APIRouter(prefix="/assistant", tags=["assistant"])


def get_assistant_service(
    database_pool: DatabasePoolDep,
    settings: Annotated[Settings, Depends(get_settings)],
) -> AssistantService:
    local_client = build_local_client(settings)
    fallback_client = build_fallback_client(settings)

    return AssistantService(
        AssistantRepository(database_pool),
        local_parser=LLMIntentParser(local_client) if local_client else None,
        fallback_parser=LLMIntentParser(
            fallback_client) if fallback_client else None,
    )


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
