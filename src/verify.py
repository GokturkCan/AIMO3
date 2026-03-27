from __future__ import annotations

from dataclasses import dataclass, field
import re

from src.result_schema import ModulusResult, ParseResult


@dataclass(slots=True)
class VerifyFixResult:
    status: str
    retry_recommended: bool
    notes: list[str] = field(default_factory=list)
    retry_reasons: list[str] = field(default_factory=list)
    soft_flags: list[str] = field(default_factory=list)
    suspicion_score: float = 0.0


def verify_candidate(
    problem_text: str,
    candidate_answer: int | None,
    parser_result: ParseResult,
    modulus_result: ModulusResult,
    raw_reasoning_text: str | None = None,
) -> VerifyFixResult:
    if not isinstance(problem_text, str):
        raise TypeError("problem_text must be a string")

    retry_reasons: list[str] = []
    soft_flags: list[str] = []

    if not isinstance(candidate_answer, int) or isinstance(candidate_answer, bool):
        retry_reasons.append("candidate answer is not an integer")

    if not parser_result.success:
        retry_reasons.append("parser did not produce a successful answer")

    if parser_result.method != "boxed":
        soft_flags.append("parse ambiguity flagged: answer did not come from boxed extraction")

    if any("fallback" in note or "invalid boxed" in note for note in parser_result.notes):
        soft_flags.append("parse ambiguity flagged: parser notes indicate fallback behavior")

    if raw_reasoning_text and raw_reasoning_text.count(r"\boxed{") > 1:
        soft_flags.append("parse ambiguity flagged: multiple boxed answers appeared in reasoning")

    if isinstance(candidate_answer, int) and not isinstance(candidate_answer, bool):
        if modulus_result.success and modulus_result.modulus is not None:
            expected_min = 0
            expected_max = modulus_result.modulus - 1
            if not expected_min <= candidate_answer <= expected_max:
                retry_reasons.append(
                    f"answer is outside expected range [0, {expected_max}]"
                )

            normalized_candidate = candidate_answer % modulus_result.modulus
            if candidate_answer != normalized_candidate:
                retry_reasons.append("candidate answer is not modulus-normalized")

            if (
                parser_result.normalized_answer is not None
                and parser_result.normalized_answer != normalized_candidate
            ):
                retry_reasons.append("parser normalization is inconsistent with modulus result")

        if _looks_suspiciously_tiny(problem_text, candidate_answer):
            soft_flags.append("suspiciously tiny answer flagged for review")

    suspicion_score = (1.5 * len(retry_reasons)) + (0.5 * len(soft_flags))
    notes = [*retry_reasons, *soft_flags]

    if retry_reasons:
        return VerifyFixResult(
            status="retry",
            retry_recommended=True,
            notes=notes,
            retry_reasons=retry_reasons,
            soft_flags=soft_flags,
            suspicion_score=suspicion_score,
        )

    if soft_flags:
        return VerifyFixResult(
            status="flagged",
            retry_recommended=any("parse ambiguity" in flag for flag in soft_flags),
            notes=notes,
            retry_reasons=[],
            soft_flags=soft_flags,
            suspicion_score=suspicion_score,
        )

    return VerifyFixResult(
        status="ok",
        retry_recommended=False,
        notes=["verification checks passed"],
        retry_reasons=[],
        soft_flags=[],
        suspicion_score=0.0,
    )


def _looks_suspiciously_tiny(problem_text: str, candidate_answer: int) -> bool:
    if abs(candidate_answer) > 2:
        return False
    return bool(re.search(r"10\s*\^|\b\d{4,}\b", problem_text))
