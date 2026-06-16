"""
Pure, DB-free scoring for extraction evaluation.
"""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

# Text fields are compared case-insensitively after trimming; amounts are
# compared numerically; everything else (dates) is compared as trimmed strings.
TEXT_FIELDS = frozenset(
    {"vendor", "document_type", "currency", "category", "payment_status"}
)
AMOUNT_FIELDS = frozenset({"total_amount"})


def normalize(field: str, value: object) -> object | None:
    """Coerce a raw field value into a canonical, comparable form."""
    if value is None:
        return None
    if field in AMOUNT_FIELDS:
        try:
            return Decimal(str(value))
        except InvalidOperation:
            return None
    text = str(value).strip()
    if field in TEXT_FIELDS:
        return text.lower() or None
    return text or None


@dataclass(slots=True)
class FieldScore:
    field: str
    labeled: int = 0
    correct: int = 0

    @property
    def accuracy(self) -> float:
        return self.correct / self.labeled if self.labeled else 0.0


@dataclass(slots=True)
class EvalReport:
    field_scores: list[FieldScore]
    example_count: int
    exact_match: int

    @property
    def exact_match_rate(self) -> float:
        return self.exact_match / self.example_count if self.example_count else 0.0


def score_example(
    gold: dict[str, object],
    predicted: dict[str, object],
    fields: Sequence[str],
) -> tuple[dict[str, bool], bool]:
    """Score one example. Returns per-field correctness (only for fields the
    gold label covers) and whether every covered field was correct."""
    per_field: dict[str, bool] = {}
    all_correct = True
    for field in fields:
        gold_value = normalize(field, gold.get(field))
        if gold_value is None:
            continue
        is_correct = normalize(field, predicted.get(field)) == gold_value
        per_field[field] = is_correct
        all_correct = all_correct and is_correct
    return per_field, bool(per_field) and all_correct


def evaluate(
    examples: Iterable[tuple[dict[str, object], dict[str, object]]],
    fields: Sequence[str],
) -> EvalReport:
    scores = {field: FieldScore(field) for field in fields}
    example_count = 0
    exact_match = 0

    for gold, predicted in examples:
        example_count += 1
        per_field, is_exact = score_example(gold, predicted, fields)
        for field, is_correct in per_field.items():
            scores[field].labeled += 1
            scores[field].correct += int(is_correct)
        exact_match += int(is_exact)

    return EvalReport(
        field_scores=[scores[field] for field in fields],
        example_count=example_count,
        exact_match=exact_match,
    )
