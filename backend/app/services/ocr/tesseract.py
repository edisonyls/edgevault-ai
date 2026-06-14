from functools import cached_property

import pytesseract
from PIL.Image import Image

from app.services.ocr.base import OcrPageResult


class TesseractEngine:
    """OCR backend backed by the system `tesseract` binary via pytesseract."""

    name = "tesseract"

    def __init__(self, language: str = "eng") -> None:
        self.language = language

    @cached_property
    def version(self) -> str | None:
        try:
            return str(pytesseract.get_tesseract_version())
        except Exception:
            return None

    def extract_image(self, image: Image) -> OcrPageResult:
        # A single image_to_data pass gives us both the text and the per-word
        # confidence, avoiding a second tesseract invocation.
        data = pytesseract.image_to_data(
            image,
            lang=self.language,
            output_type=pytesseract.Output.DICT,
        )

        lines: list[str] = []
        current_line_key: tuple[int, int, int] | None = None
        current_words: list[str] = []
        confidences: list[float] = []

        for index in range(len(data["text"])):
            word = data["text"][index].strip()
            if not word:
                continue

            line_key = (
                data["block_num"][index],
                data["par_num"][index],
                data["line_num"][index],
            )
            if current_words and line_key != current_line_key:
                lines.append(" ".join(current_words))
                current_words = []

            current_line_key = line_key
            current_words.append(word)

            # tesseract reports a numeric confidence (0-100) per word, or -1 for
            # rows without recognized text (already skipped above via empty `word`).
            confidence = float(data["conf"][index])
            if confidence >= 0:
                confidences.append(confidence)

        if current_words:
            lines.append(" ".join(current_words))

        mean_confidence = sum(confidences) / \
            len(confidences) if confidences else None
        return OcrPageResult(text="\n".join(lines), confidence=mean_confidence)
