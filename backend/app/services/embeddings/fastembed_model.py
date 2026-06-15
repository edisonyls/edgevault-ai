from functools import lru_cache

from fastembed import TextEmbedding


# Loading a fastembed model downloads weights and builds an ONNX session, both
# expensive, so cache one instance per model name for the process.
@lru_cache(maxsize=2)
def _load_text_embedding(model_name: str) -> TextEmbedding:
    return TextEmbedding(model_name=model_name)


class FastEmbedModel:
    """Local, offline embeddings via fastembed (ONNX runtime)."""

    def __init__(self, model_name: str, dimension: int) -> None:
        self._model_name = model_name
        self._dimension = dimension

    @property
    def name(self) -> str:
        return self._model_name

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        # fastembed yields numpy arrays lazily; materialize as plain float lists
        # so they can be passed straight to pgvector.
        model = _load_text_embedding(self._model_name)
        return [vector.tolist() for vector in model.embed(texts)]
