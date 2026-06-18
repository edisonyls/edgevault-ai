from app.core.config import Settings
from app.services.assistant.llm_client import ChatCompletionClient


# Initialize the local assistant LLM client
def build_local_client(settings: Settings) -> ChatCompletionClient | None:
    return ChatCompletionClient(
        base_url=settings.assistant_llm_base_url,
        model=settings.assistant_llm_model,
        timeout=settings.assistant_llm_timeout,
    )


def build_fallback_client(settings: Settings) -> ChatCompletionClient | None:
    """Tier 3: the cloud fallback (DeepSeek); only built when a key is present."""
    if not (settings.assistant_fallback_enabled and settings.assistant_fallback_api_key):
        return None
    return ChatCompletionClient(
        base_url=settings.assistant_fallback_base_url,
        model=settings.assistant_fallback_model,
        api_key=settings.assistant_fallback_api_key,
        timeout=settings.assistant_fallback_timeout,
        extra_params={"temperature": 0},
    )
