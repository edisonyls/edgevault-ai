import asyncio
import logging

from app.services.assistant.llm_client import ChatCompletionClient

logger = logging.getLogger(__name__)


async def keep_model_warm(client: ChatCompletionClient, interval: float) -> None:
    """
    Periodically ping the local model so hailo-ollama keeps it resident on the
    NPU. 
    """
    while True:
        result = await client.complete(system="ping", user="ping")
        if result is None:
            logger.info(
                "Keep-warm ping to %s did not complete; retrying later.", client.model)
        await asyncio.sleep(interval)
