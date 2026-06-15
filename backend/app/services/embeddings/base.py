from typing import Protocol, runtime_checkable


@runtime_checkable
class EmbeddingModel(Protocol):
    """A swappable text-embedding backend."""

    @property
    def name(self) -> str: ...

    @property
    def dimension(self) -> int: ...

    def embed(self, texts: list[str]) -> list[list[float]]: ...
