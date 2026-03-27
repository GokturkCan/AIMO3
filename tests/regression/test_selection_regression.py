from src.regression import assess_selection_outcome
from src.selection import select_best_attempt
from src.solver_core import build_attempt_record


def test_regression_selection_does_not_choose_ambiguous_consensus_over_verified_outlier():
    problem = "The final answer should be in [0, 99999]."

    ambiguous_a = build_attempt_record(
        attempt_index=0,
        prompt_family="baseline_tir",
        raw_problem_text=problem,
        prompted_problem_text=problem,
        raw_output_text="We looked at 31, 32, and perhaps the answer is 31",
        entropy=0.7,
    )
    ambiguous_b = build_attempt_record(
        attempt_index=1,
        prompt_family="baseline_tir",
        raw_problem_text=problem,
        prompted_problem_text=problem,
        raw_output_text="I think 31 might work.",
        entropy=0.9,
    )
    verified = build_attempt_record(
        attempt_index=2,
        prompt_family="tool_guided",
        raw_problem_text=problem,
        prompted_problem_text=problem,
        raw_output_text="After checking with Python, the final answer is \\boxed{44}.",
        tool_used=True,
        python_calls=1,
        entropy=1.4,
    )

    result = select_best_attempt([ambiguous_a, ambiguous_b, verified])
    assessment = assess_selection_outcome(
        [ambiguous_a, ambiguous_b, verified],
        result,
        expected_answer=44,
    )

    assert result.selected_answer == 44
    assert assessment.candidate_correct_exists is True
    assert assessment.selected_is_correct is True
    assert assessment.selection_failure is False
