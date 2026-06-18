from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from PIL.Image import Image


@dataclass(slots=True)
class OcrPageResult:
    """Text and mean word confidence for one image.
    """

    text: str
    confidence: float | None
    word_count: int


@runtime_checkable
class OcrEngine(Protocol):
    """A swappable OCR backend. Phase 2 adds a Hailo-accelerated implementation."""

    @property
    def name(self) -> str: ...

    @property
    def version(self) -> str | None: ...

    def extract_image(self, image: Image) -> OcrPageResult: ...
