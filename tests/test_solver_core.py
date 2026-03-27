from src.solver_core import build_attempt_record


def test_build_attempt_record_uses_raw_problem_text_for_modulus_detection():
    raw_problem = "Find the remainder when 10^6 is divided by 100000."
    prompted_problem = raw_problem + " Additional preference prompt noise with boxed examples."
    raw_output = "After computation, the final answer is \\boxed{0}."

    record = build_attempt_record(
        attempt_index=0,
        prompt_family="baseline_tir",
        raw_problem_text=raw_problem,
        prompted_problem_text=prompted_problem,
        raw_output_text=raw_output,
        response_length=12,
        entropy=0.8,
    )

    assert record.parsed_answer == 0
    assert record.modulus_result.success is True
    assert record.modulus_result.modulus == 100000
    assert record.parse_tier == "tier1"
    assert record.valid_candidate is True
    assert record.verify_status == "flagged"
    assert "suspiciously tiny answer flagged for review" in record.suspicious_flags
    assert record.tool_consistency is False
    assert record.parse_tier_rank == 3
    assert "suspicious_tiny_answer" in record.policy_retry_reasons


def test_build_attempt_record_marks_weak_last_integer_as_tier3():
    raw_problem = "The final answer should be in [0, 99999]."
    raw_output = "We tried 10 and 11 and I guess maybe the answer is 12"

    record = build_attempt_record(
        attempt_index=1,
        prompt_family="self_refute",
        raw_problem_text=raw_problem,
        prompted_problem_text=raw_problem,
        raw_output_text=raw_output,
    )

    assert record.parsed_answer == 12
    assert record.parse_tier == "tier3"
    assert record.verify_result.status == "flagged"
    assert record.retry_reasons == []
    assert record.suspicious_flags
    assert "weak_parse" in record.policy_retry_reasons
