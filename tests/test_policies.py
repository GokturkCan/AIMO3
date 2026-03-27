from src.policies import classify_problem_difficulty, default_policy_set, recommend_retry, should_early_stop
from src.solver_core import build_attempt_record


def test_classify_problem_difficulty_marks_short_mod_problem_as_easy():
    problem = "What is the remainder when 7^20 is divided by 100000?"

    assert classify_problem_difficulty(problem) == "easy"


def test_classify_problem_difficulty_marks_geometry_problem_as_hard():
    problem = (
        "In triangle ABC, let the angle bisector from A meet the circumcircle again at D. "
        "Suppose the circle through B, C, and D meets the altitude from A at E."
    )

    assert classify_problem_difficulty(problem) == "hard"


def test_default_policy_set_returns_structured_policy_for_medium_problem():
    policies = default_policy_set()
    problem = "Let f be a polynomial with integer coefficients such that f(1)=1 and f(2)=3."

    policy = policies.for_problem(problem)

    assert policy.name == "medium"
    assert "self_refute" in policy.prompt_families
    assert policy.selection_policy.mode == "verifier_weighted"
    assert policy.attempt_policy.tool_use_mode == "encouraged"


def test_should_early_stop_requires_verify_aware_consensus():
    policy = default_policy_set().medium
    problem = "The final answer should be in [0, 99999]."

    attempts = [
        build_attempt_record(
            attempt_index=0,
            prompt_family="baseline_tir",
            raw_problem_text=problem,
            prompted_problem_text=problem,
            raw_output_text="Final answer is \\boxed{44}.",
            entropy=1.0,
        ),
        build_attempt_record(
            attempt_index=1,
            prompt_family="tool_guided",
            raw_problem_text=problem,
            prompted_problem_text=problem,
            raw_output_text="Independent check confirms the final answer is \\boxed{44}.",
            tool_used=True,
            python_calls=1,
            entropy=1.1,
        ),
        build_attempt_record(
            attempt_index=2,
            prompt_family="baseline_tir",
            raw_problem_text=problem,
            prompted_problem_text=problem,
            raw_output_text="After a second method, final answer is \\boxed{44}.",
            entropy=1.2,
        ),
    ]

    decision = should_early_stop(attempts, policy)

    assert decision.should_stop is True
    assert decision.answer == 44
    assert decision.reason == "verify_aware_consensus"


def test_should_early_stop_rejects_weak_parse_consensus():
    policy = default_policy_set().medium
    problem = "The final answer should be in [0, 99999]."

    attempts = [
        build_attempt_record(
            attempt_index=0,
            prompt_family="baseline_tir",
            raw_problem_text=problem,
            prompted_problem_text=problem,
            raw_output_text="Maybe it is 31.",
            entropy=0.7,
        ),
        build_attempt_record(
            attempt_index=1,
            prompt_family="baseline_tir",
            raw_problem_text=problem,
            prompted_problem_text=problem,
            raw_output_text="I think 31 might work.",
            entropy=0.8,
        ),
        build_attempt_record(
            attempt_index=2,
            prompt_family="self_refute",
            raw_problem_text=problem,
            prompted_problem_text=problem,
            raw_output_text="Could be 31.",
            entropy=0.9,
        ),
    ]

    decision = should_early_stop(attempts, policy)

    assert decision.should_stop is False


def test_recommend_retry_returns_reason_based_prompt_family():
    policy = default_policy_set().hard
    problem = "The final answer should be in [0, 99999]."

    attempts = [
        build_attempt_record(
            attempt_index=0,
            prompt_family="baseline_tir",
            raw_problem_text=problem,
            prompted_problem_text=problem,
            raw_output_text="We tried 10 and 11 and maybe the answer is 12",
        ),
        build_attempt_record(
            attempt_index=1,
            prompt_family="tool_guided",
            raw_problem_text=problem,
            prompted_problem_text=problem,
            raw_output_text="Final answer is \\boxed{100000}",
            tool_used=True,
            python_calls=1,
            python_errors=1,
        ),
    ]

    decision = recommend_retry(attempts, policy, retries_used=0)

    assert decision.should_retry is True
    assert decision.reason == "weak_parse"
    assert decision.prompt_family == "tool_guided"
    assert decision.remaining_budget == 2
