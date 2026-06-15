from app.core.config import Settings
from app.services.embeddings.base import EmbeddingModel
from app.services.embeddings.fastembed_model import FastEmbedModel


class UnsupportedEmbeddingProviderError(Exception):
    pass


# Resolve the configured embedding backend.
def get_embedding_model(settings: Settings) -> EmbeddingModel:
    if settings.embedding_provider == "fastembed":
        return FastEmbedModel(
            model_name=settings.embedding_model,
            dimension=settings.embedding_dimension,
        )

    raise UnsupportedEmbeddingProviderError(
        f"Unknown embedding provider: {settings.embedding_provider}"
    )


# Split text into overlapping character windows.
def chunk_text(text: str, *, size: int, overlap: int) -> list[str]:
    cleaned = text.strip()
    if not cleaned:
        return []

    if len(cleaned) <= size:
        return [cleaned]

    step = max(size - overlap, 1)
    chunks: list[str] = []
    for start in range(0, len(cleaned), step):
        chunk = cleaned[start: start + size].strip()
        if chunk:
            chunks.append(chunk)
        if start + size >= len(cleaned):
            break

    return chunks


__all__ = [
    "EmbeddingModel",
    "FastEmbedModel",
    "UnsupportedEmbeddingProviderError",
    "chunk_text",
    "get_embedding_model",
]
