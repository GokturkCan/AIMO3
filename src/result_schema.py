from dataclasses import dataclass, field


@dataclass(slots=True)
class ParseResult:
    raw_answer: int | None
    normalized_answer: int | None
    method: str
    success: bool
    confidence: float
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ModulusResult:
    modulus: int | None
    source: str
    matched_text: str | None
    success: bool
    notes: list[str] = field(default_factory=list)
