from __future__ import annotations

from dataclasses import dataclass

from src.selection import SelectionResult
from src.solver_core import AttemptRecord


@dataclass(frozen=True, slots=True)
class RegressionAssessment:
    expected_answer: int
    selected_answer: int | None
    candidate_correct_exists: bool
    selected_is_correct: bool
    selection_failure: bool
    generation_failure: bool
    extraction_failure: bool


def assess_selection_outcome(
    attempts: list[AttemptRecord],
    selection_result: SelectionResult,
    *,
    expected_answer: int,
) -> RegressionAssessment:
    any_extraction_success = any(not attempt.extraction_failed for attempt in attempts)
    candidate_correct_exists = any(
        attempt.parsed_answer == expected_answer for attempt in attempts
    )
    selected_is_correct = selection_result.selected_answer == expected_answer
    selection_failure = candidate_correct_exists and not selected_is_correct
    generation_failure = not candidate_correct_exists
    extraction_failure = (
        generation_failure
        and not any_extraction_success
        and selection_result.selected_answer is None
    )

    return RegressionAssessment(
        expected_answer=expected_answer,
        selected_answer=selection_result.selected_answer,
        candidate_correct_exists=candidate_correct_exists,
        selected_is_correct=selected_is_correct,
        selection_failure=selection_failure,
        generation_failure=generation_failure,
        extraction_failure=extraction_failure,
    )
