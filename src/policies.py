from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import re

from src.solver_core import AttemptRecord


SELECTION_MODE_VERIFIER_WEIGHTED = "verifier_weighted"
TOOL_USE_OPTIONAL = "optional"
TOOL_USE_ENCOURAGED = "encouraged"
TOOL_USE_REQUIRED = "required"


@dataclass(frozen=True, slots=True)
class AttemptPolicy:
    attempt_count: int
    prompt_family_distribution: tuple[str, ...]
    tool_use_mode: str = TOOL_USE_ENCOURAGED

    def __post_init__(self) -> None:
        if self.attempt_count <= 0:
            raise ValueError("attempt_count must be positive")
        if len(self.prompt_family_distribution) != self.attempt_count:
            raise ValueError("prompt_family_distribution length must match attempt_count")


@dataclass(frozen=True, slots=True)
class EarlyStopPolicy:
    min_matching_answers: int
    min_parse_tier: str
    allowed_verify_statuses: tuple[str, ...]
    require_tool_support: bool = False


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    retry_budget: int
    allowed_reasons: tuple[str, ...]
    reason_prompt_family_map: tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class SelectionPolicy:
    mode: str = SELECTION_MODE_VERIFIER_WEIGHTED


@dataclass(frozen=True, slots=True)
class SolvePolicy:
    name: str
    attempt_policy: AttemptPolicy
    early_stop_policy: EarlyStopPolicy
    retry_policy: RetryPolicy
    selection_policy: SelectionPolicy

    @property
    def attempt_count(self) -> int:
        return self.attempt_policy.attempt_count

    @property
    def prompt_families(self) -> tuple[str, ...]:
        return self.attempt_policy.prompt_family_distribution

    @property
    def early_stop_consensus(self) -> int:
        return self.early_stop_policy.min_matching_answers

    @property
    def retry_budget(self) -> int:
        return self.retry_policy.retry_budget

    @property
    def require_verify_for_early_stop(self) -> bool:
        return bool(self.early_stop_policy.allowed_verify_statuses)


@dataclass(frozen=True, slots=True)
class PolicySet:
    easy: SolvePolicy
    medium: SolvePolicy
    hard: SolvePolicy

    def for_problem(self, problem_text: str) -> SolvePolicy:
        difficulty = classify_problem_difficulty(problem_text)
        if difficulty == "easy":
            return self.easy
        if difficulty == "hard":
            return self.hard
        return self.medium


@dataclass(frozen=True, slots=True)
class EarlyStopDecision:
    should_stop: bool
    answer: int | None
    matching_attempts: tuple[int, ...]
    reason: str | None


@dataclass(frozen=True, slots=True)
class RetryDecision:
    should_retry: bool
    reason: str | None
    prompt_family: str | None
    remaining_budget: int


GEOMETRY_HINTS = re.compile(r"\btriangle\b|\bcircle\b|\bangle\b|\bpolygon\b|\bperpendicular\b", re.IGNORECASE)
NUMBER_THEORY_HINTS = re.compile(r"\bremainder\b|\bmod\b|\bdivisible\b|\bprime\b", re.IGNORECASE)


def default_policy_set() -> PolicySet:
    retry_reasons = (
        "weak_parse",
        "multiple_boxed",
        "suspicious_tiny_answer",
        "tool_mismatch",
        "inconsistent_reasoning",
    )
    retry_prompt_map = (
        ("weak_parse", "tool_guided"),
        ("multiple_boxed", "self_refute"),
        ("suspicious_tiny_answer", "self_refute"),
        ("tool_mismatch", "baseline"),
        ("inconsistent_reasoning", "self_refute"),
    )

    return PolicySet(
        easy=SolvePolicy(
            name="easy",
            attempt_policy=AttemptPolicy(
                attempt_count=3,
                prompt_family_distribution=("baseline", "tool_guided", "baseline"),
                tool_use_mode=TOOL_USE_OPTIONAL,
            ),
            early_stop_policy=EarlyStopPolicy(
                min_matching_answers=2,
                min_parse_tier="tier1",
                allowed_verify_statuses=("ok", "flagged"),
                require_tool_support=False,
            ),
            retry_policy=RetryPolicy(
                retry_budget=0,
                allowed_reasons=(),
                reason_prompt_family_map=(),
            ),
            selection_policy=SelectionPolicy(),
        ),
        medium=SolvePolicy(
            name="medium",
            attempt_policy=AttemptPolicy(
                attempt_count=5,
                prompt_family_distribution=(
                    "baseline",
                    "tool_guided",
                    "self_refute",
                    "tool_guided",
                    "baseline",
                ),
                tool_use_mode=TOOL_USE_ENCOURAGED,
            ),
            early_stop_policy=EarlyStopPolicy(
                min_matching_answers=3,
                min_parse_tier="tier1",
                allowed_verify_statuses=("ok", "flagged"),
                require_tool_support=False,
            ),
            retry_policy=RetryPolicy(
                retry_budget=1,
                allowed_reasons=retry_reasons,
                reason_prompt_family_map=retry_prompt_map,
            ),
            selection_policy=SelectionPolicy(),
        ),
        hard=SolvePolicy(
            name="hard",
            attempt_policy=AttemptPolicy(
                attempt_count=7,
                prompt_family_distribution=(
                    "baseline",
                    "tool_guided",
                    "self_refute",
                    "tool_guided",
                    "baseline",
                    "self_refute",
                    "tool_guided",
                ),
                tool_use_mode=TOOL_USE_REQUIRED,
            ),
            early_stop_policy=EarlyStopPolicy(
                min_matching_answers=4,
                min_parse_tier="tier1",
                allowed_verify_statuses=("ok",),
                require_tool_support=True,
            ),
            retry_policy=RetryPolicy(
                retry_budget=2,
                allowed_reasons=retry_reasons,
                reason_prompt_family_map=retry_prompt_map,
            ),
            selection_policy=SelectionPolicy(),
        ),
    )


def classify_problem_difficulty(problem_text: str) -> str:
    normalized = problem_text.strip()
    if len(normalized) >= 320 or GEOMETRY_HINTS.search(normalized):
        return "hard"
    if len(normalized) <= 120 and NUMBER_THEORY_HINTS.search(normalized):
        return "easy"
    return "medium"


def should_early_stop(attempts: list[AttemptRecord], policy: SolvePolicy) -> EarlyStopDecision:
    stop_policy = policy.early_stop_policy
    min_tier_rank = _parse_tier_rank(stop_policy.min_parse_tier)

    qualified_attempts = [
        attempt
        for attempt in attempts
        if attempt.parsed_answer is not None
        and attempt.parse_tier_rank >= min_tier_rank
        and attempt.verify_status in stop_policy.allowed_verify_statuses
    ]
    if not qualified_attempts:
        return EarlyStopDecision(False, None, (), None)

    grouped_attempts: dict[int, list[AttemptRecord]] = {}
    for attempt in qualified_attempts:
        grouped_attempts.setdefault(attempt.parsed_answer, []).append(attempt)

    best_answer = None
    best_group: list[AttemptRecord] = []
    for answer, group in grouped_attempts.items():
        if len(group) > len(best_group):
            best_answer = answer
            best_group = group

    if best_answer is None or len(best_group) < stop_policy.min_matching_answers:
        return EarlyStopDecision(False, None, (), None)

    if stop_policy.require_tool_support and not any(a.tool_consistency for a in best_group):
        return EarlyStopDecision(
            False,
            best_answer,
            tuple(a.attempt_index for a in best_group),
            None,
        )

    return EarlyStopDecision(
        True,
        best_answer,
        tuple(a.attempt_index for a in best_group),
        "verify_aware_consensus",
    )


def recommend_retry(
    attempts: list[AttemptRecord],
    policy: SolvePolicy,
    *,
    retries_used: int = 0,
) -> RetryDecision:
    retry_policy = policy.retry_policy
    remaining_budget = max(0, retry_policy.retry_budget - retries_used)
    if remaining_budget <= 0:
        return RetryDecision(False, None, None, remaining_budget)

    reason_counter: Counter[str] = Counter()
    for attempt in attempts:
        for reason in attempt.policy_retry_reasons:
            if reason in retry_policy.allowed_reasons:
                reason_counter[reason] += 1

    if not reason_counter:
        return RetryDecision(False, None, None, remaining_budget)

    prioritized_reasons = [
        reason for reason in retry_policy.allowed_reasons if reason in reason_counter
    ]
    chosen_reason = prioritized_reasons[0]
    prompt_family = _reason_prompt_family(retry_policy, chosen_reason)

    return RetryDecision(True, chosen_reason, prompt_family, remaining_budget)


def _reason_prompt_family(retry_policy: RetryPolicy, reason: str) -> str | None:
    for mapped_reason, prompt_family in retry_policy.reason_prompt_family_map:
        if mapped_reason == reason:
            return prompt_family
    return None


def _parse_tier_rank(parse_tier: str) -> int:
    ranks = {
        "none": 0,
        "tier3": 1,
        "tier2": 2,
        "tier1": 3,
    }
    return ranks.get(parse_tier, 0)
