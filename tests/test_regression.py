from src.regression import assess_selection_outcome
from src.selection import select_best_attempt
from src.solver_core import build_attempt_record


def test_assess_selection_outcome_reports_generation_failure_when_correct_candidate_never_appears():
    problem = "The final answer should be in [0, 99999]."

    wrong_consensus_a = build_attempt_record(
        attempt_index=0,
        prompt_family="baseline_tir",
        raw_problem_text=problem,
        prompted_problem_text=problem,
        raw_output_text="I think 31 might work.",
        entropy=0.8,
    )
    wrong_consensus_b = build_attempt_record(
        attempt_index=1,
        prompt_family="baseline_tir",
        raw_problem_text=problem,
        prompted_problem_text=problem,
        raw_output_text="Perhaps the answer is 31.",
        entropy=0.9,
    )
    correct_verified = build_attempt_record(
        attempt_index=2,
        prompt_family="tool_guided",
        raw_problem_text=problem,
        prompted_problem_text=problem,
        raw_output_text="After checking with Python, the final answer is \\boxed{44}.",
        tool_used=True,
        python_calls=1,
        entropy=1.4,
    )

    selection_result = select_best_attempt([wrong_consensus_a, wrong_consensus_b, correct_verified])
    assessment = assess_selection_outcome(
        [wrong_consensus_a, wrong_consensus_b, correct_verified],
        selection_result,
        expected_answer=17,
    )

    assert assessment.candidate_correct_exists is False
    assert assessment.selected_is_correct is False
    assert assessment.generation_failure is True
    assert assessment.selection_failure is False
    assert assessment.extraction_failure is False


def test_assess_selection_outcome_detects_selection_failure_when_correct_candidate_exists():
    problem = "The final answer should be in [0, 99999]."

    wrong_a = build_attempt_record(
        attempt_index=0,
        prompt_family="baseline_tir",
        raw_problem_text=problem,
        prompted_problem_text=problem,
        raw_output_text="The answer is 31.",
        entropy=0.7,
    )
    correct_b = build_attempt_record(
        attempt_index=1,
        prompt_family="tool_guided",
        raw_problem_text=problem,
        prompted_problem_text=problem,
        raw_output_text="Final answer is \\boxed{44}.",
        tool_used=True,
        python_calls=1,
        entropy=2.2,
    )

    selection_result = select_best_attempt([wrong_a, correct_b])
    assessment = assess_selection_outcome(
        [wrong_a, correct_b],
        selection_result,
        expected_answer=44,
    )

    assert assessment.candidate_correct_exists is True
    assert assessment.selected_is_correct is True
    assert assessment.selection_failure is False
    assert assessment.generation_failure is False


def test_assess_selection_outcome_detects_extraction_failure():
    problem = "The final answer should be in [0, 99999]."

    extraction_miss = build_attempt_record(
        attempt_index=0,
        prompt_family="baseline_tir",
        raw_problem_text=problem,
        prompted_problem_text=problem,
        raw_output_text="We derive a symbolic form but never provide a final integer.",
        entropy=1.0,
    )
    another_miss = build_attempt_record(
        attempt_index=1,
        prompt_family="self_refute",
        raw_problem_text=problem,
        prompted_problem_text=problem,
        raw_output_text="No final number is written here either.",
        entropy=1.1,
    )

    selection_result = select_best_attempt([extraction_miss, another_miss])
    assessment = assess_selection_outcome(
        [extraction_miss, another_miss],
        selection_result,
        expected_answer=12,
    )

    assert assessment.candidate_correct_exists is False
    assert assessment.selected_answer is None
    assert assessment.extraction_failure is True
