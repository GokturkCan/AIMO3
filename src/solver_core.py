from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any

from src.modulus import detect_modulus
from src.parser import parse_model_output
from src.result_schema import ModulusResult, ParseResult
from src.verify import VerifyFixResult, verify_candidate


FINALITY_PATTERNS = (
    re.compile(r"\\boxed\s*\{", re.IGNORECASE),
    re.compile(r"\bfinal answer\b", re.IGNORECASE),
    re.compile(r"\bthe answer is\b", re.IGNORECASE),
)

PARSE_TIER_RANKS = {
    "none": 0,
    "tier3": 1,
    "tier2": 2,
    "tier1": 3,
}


@dataclass(slots=True)
class AttemptRecord:
    attempt_index: int
    prompt_family: str
    raw_problem_text: str
    prompted_problem_text: str
    raw_output_text: str
    parsed_answer: int | None
    parser_result: ParseResult
    modulus_result: ModulusResult
    verify_result: VerifyFixResult
    parse_tier: str
    finality_score: float
    tool_used: bool = False
    python_calls: int = 0
    python_errors: int = 0
    response_length: int = 0
    entropy: float = float("inf")
    finish_reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def valid_candidate(self) -> bool:
        return self.parsed_answer is not None and self.verify_result.status != "retry"

    @property
    def verify_status(self) -> str:
        return self.verify_result.status

    @property
    def retry_reasons(self) -> list[str]:
        return self.verify_result.retry_reasons

    @property
    def suspicious_flags(self) -> list[str]:
        return self.verify_result.soft_flags

    @property
    def tool_consistency(self) -> bool:
        return self.tool_used and self.python_errors == 0

    @property
    def extraction_failed(self) -> bool:
        return self.parsed_answer is None

    @property
    def parse_tier_rank(self) -> int:
        return PARSE_TIER_RANKS.get(self.parse_tier, 0)

    @property
    def policy_retry_reasons(self) -> tuple[str, ...]:
        reasons: list[str] = []

        if self.parse_tier in {"none", "tier3"} or self.extraction_failed:
            reasons.append("weak_parse")

        if any("multiple boxed answers" in flag.lower() for flag in self.suspicious_flags):
            reasons.append("multiple_boxed")

        if any("suspiciously tiny" in flag.lower() for flag in self.suspicious_flags):
            reasons.append("suspicious_tiny_answer")

        if self.tool_used and not self.tool_consistency:
            reasons.append("tool_mismatch")

        if self.verify_status == "retry":
            reasons.append("inconsistent_reasoning")

        if not reasons and self.verify_status == "flagged":
            reasons.append("inconsistent_reasoning")

        return tuple(dict.fromkeys(reasons))


def build_attempt_record(
    *,
    attempt_index: int,
    prompt_family: str,
    raw_problem_text: str,
    prompted_problem_text: str,
    raw_output_text: str,
    tool_used: bool = False,
    python_calls: int = 0,
    python_errors: int = 0,
    response_length: int = 0,
    entropy: float = float("inf"),
    finish_reason: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> AttemptRecord:
    modulus_result = detect_modulus(raw_problem_text)
    parser_result = parse_model_output(raw_output_text)
    parsed_answer = parser_result.normalized_answer if parser_result.success else None
    verify_result = verify_candidate(
        problem_text=raw_problem_text,
        candidate_answer=parsed_answer,
        parser_result=parser_result,
        modulus_result=modulus_result,
        raw_reasoning_text=raw_output_text,
    )
    finality_score = compute_finality_score(raw_output_text)
    parse_tier = classify_parse_tier(parser_result, finality_score=finality_score)

    return AttemptRecord(
        attempt_index=attempt_index,
        prompt_family=prompt_family,
        raw_problem_text=raw_problem_text,
        prompted_problem_text=prompted_problem_text,
        raw_output_text=raw_output_text,
        parsed_answer=parsed_answer,
        parser_result=parser_result,
        modulus_result=modulus_result,
        verify_result=verify_result,
        parse_tier=parse_tier,
        finality_score=finality_score,
        tool_used=tool_used,
        python_calls=python_calls,
        python_errors=python_errors,
        response_length=response_length,
        entropy=entropy,
        finish_reason=finish_reason,
        metadata=dict(metadata or {}),
    )


def classify_parse_tier(parser_result: ParseResult, *, finality_score: float) -> str:
    if not parser_result.success:
        return "none"

    if parser_result.method == "boxed" and finality_score >= 1.0:
        return "tier1"

    if parser_result.method == "boxed":
        return "tier2"

    if parser_result.method == "last_integer" and finality_score >= 1.0:
        return "tier2"

    return "tier3"


def compute_finality_score(raw_output_text: str) -> float:
    score = 0.0
    for pattern in FINALITY_PATTERNS:
        if pattern.search(raw_output_text):
            score += 0.6
    return min(score, 1.8)
