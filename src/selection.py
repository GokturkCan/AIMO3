from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from src.solver_core import AttemptRecord


PARSE_TIER_SCORES = {
    "tier1": 3.0,
    "tier2": 2.0,
    "tier3": 0.5,
    "none": -2.0,
}

VERIFY_STATUS_SCORES = {
    "ok": 2.5,
    "flagged": 1.0,
    "retry": -3.0,
}


@dataclass(slots=True)
class SelectionBreakdown:
    attempt_index: int
    answer: int | None
    total_score: float
    consensus_score: float
    parse_score: float
    verify_score: float
    finality_score: float
    tool_score: float
    entropy_score: float
    suspicion_penalty: float


@dataclass(slots=True)
class SelectionResult:
    selected_answer: int | None
    selected_attempt: AttemptRecord | None
    scored_attempts: list[SelectionBreakdown] = field(default_factory=list)


def select_best_attempt(attempts: list[AttemptRecord]) -> SelectionResult:
    # Current Sprint 1/2 selector corresponds to the "verifier_weighted"
    # selection mode from the policy layer.
    if not attempts:
        return SelectionResult(selected_answer=None, selected_attempt=None, scored_attempts=[])

    valid_answers = [attempt.parsed_answer for attempt in attempts if attempt.parsed_answer is not None]
    answer_counts = Counter(valid_answers)
    max_count = max(answer_counts.values(), default=0)

    scored: list[tuple[AttemptRecord, SelectionBreakdown]] = []
    for attempt in attempts:
        breakdown = _score_attempt(attempt, answer_counts=answer_counts, max_count=max_count)
        scored.append((attempt, breakdown))

    scored.sort(
        key=lambda item: (
            item[1].total_score,
            item[0].finality_score,
            -item[0].entropy,
            -(item[0].tool_used and item[0].python_errors == 0),
        ),
        reverse=True,
    )

    best_attempt = scored[0][0]
    selected_answer = best_attempt.parsed_answer if best_attempt.valid_candidate else None
    if selected_answer is None and answer_counts:
        selected_answer = answer_counts.most_common(1)[0][0]

    return SelectionResult(
        selected_answer=selected_answer,
        selected_attempt=best_attempt,
        scored_attempts=[breakdown for _, breakdown in scored],
    )


def _score_attempt(
    attempt: AttemptRecord,
    *,
    answer_counts: Counter[int],
    max_count: int,
) -> SelectionBreakdown:
    # Sprint 1 stays heuristic and inspectable on purpose.
    # Later stability and retry-aware signals can be added here without
    # changing the caller contract or the breakdown shape.
    consensus_count = answer_counts.get(attempt.parsed_answer, 0) if attempt.parsed_answer is not None else 0
    consensus_score = (consensus_count / max_count) * 3.0 if max_count else 0.0
    parse_score = PARSE_TIER_SCORES.get(attempt.parse_tier, -2.0)
    verify_score = VERIFY_STATUS_SCORES.get(attempt.verify_result.status, -1.0)
    finality_score = min(attempt.finality_score, 1.5)
    tool_score = 0.75 if attempt.tool_consistency else 0.0
    entropy_score = _entropy_score(attempt.entropy)
    suspicion_penalty = min(attempt.verify_result.suspicion_score, 3.0)

    total_score = (
        consensus_score
        + parse_score
        + verify_score
        + finality_score
        + tool_score
        + entropy_score
        - suspicion_penalty
    )

    return SelectionBreakdown(
        attempt_index=attempt.attempt_index,
        answer=attempt.parsed_answer,
        total_score=total_score,
        consensus_score=consensus_score,
        parse_score=parse_score,
        verify_score=verify_score,
        finality_score=finality_score,
        tool_score=tool_score,
        entropy_score=entropy_score,
        suspicion_penalty=suspicion_penalty,
    )


def _entropy_score(entropy: float) -> float:
    if entropy == float("inf"):
        return 0.0
    if entropy <= 0.75:
        return 1.0
    if entropy <= 1.5:
        return 0.6
    if entropy <= 3.0:
        return 0.2
    return 0.0
