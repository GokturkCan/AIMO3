from src.selection import select_best_attempt
from src.solver_core import build_attempt_record


def test_select_best_attempt_prefers_verified_boxed_candidate_over_low_entropy_fallback():
    problem = "The final answer should be in [0, 99999]."

    weak_attempt = build_attempt_record(
        attempt_index=0,
        prompt_family="baseline_tir",
        raw_problem_text=problem,
        prompted_problem_text=problem,
        raw_output_text="We considered 99, then 42, and maybe the answer is 42",
        entropy=0.4,
    )
    strong_attempt = build_attempt_record(
        attempt_index=1,
        prompt_family="tool_guided",
        raw_problem_text=problem,
        prompted_problem_text=problem,
        raw_output_text="Independent verification confirms the final answer is \\boxed{17}.",
        tool_used=True,
        python_calls=1,
        entropy=1.2,
    )

    result = select_best_attempt([weak_attempt, strong_attempt])

    assert result.selected_answer == 17
    assert result.selected_attempt is strong_attempt
    assert result.scored_attempts[0].answer == 17


def test_select_best_attempt_falls_back_to_consensus_when_best_attempt_is_invalid():
    problem = "Give the answer modulo 100000."

    invalid_attempt = build_attempt_record(
        attempt_index=0,
        prompt_family="baseline_tir",
        raw_problem_text=problem,
        prompted_problem_text=problem,
        raw_output_text="Final answer is \\boxed{100000}",
        entropy=0.2,
    )
    valid_attempt = build_attempt_record(
        attempt_index=1,
        prompt_family="baseline_tir",
        raw_problem_text=problem,
        prompted_problem_text=problem,
        raw_output_text="Final answer is \\boxed{0}",
        entropy=1.0,
    )

    result = select_best_attempt([invalid_attempt, valid_attempt])

    assert result.selected_answer == 0
