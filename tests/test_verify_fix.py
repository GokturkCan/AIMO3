from src.result_schema import ModulusResult, ParseResult
from src.verify_fix import verify_candidate


def test_verify_candidate_returns_ok_for_clean_boxed_and_normalized_answer():
    parser_result = ParseResult(
        raw_answer=336,
        normalized_answer=336,
        method="boxed",
        success=True,
        confidence=0.95,
        notes=[],
    )
    modulus_result = ModulusResult(
        modulus=100000,
        source="modulo",
        matched_text="modulo 100000",
        success=True,
        notes=[],
    )

    result = verify_candidate(
        problem_text="Find the remainder when divided by 100000.",
        candidate_answer=336,
        parser_result=parser_result,
        modulus_result=modulus_result,
        raw_reasoning_text="Final answer: \\boxed{336}",
    )

    assert result.status == "ok"
    assert result.retry_recommended is False
    assert "verification checks passed" in result.notes


def test_verify_candidate_retries_when_answer_is_out_of_range():
    parser_result = ParseResult(
        raw_answer=100000,
        normalized_answer=0,
        method="boxed",
        success=True,
        confidence=0.95,
        notes=[],
    )
    modulus_result = ModulusResult(
        modulus=100000,
        source="modulo",
        matched_text="modulo 100000",
        success=True,
        notes=[],
    )

    result = verify_candidate(
        problem_text="Give the answer modulo 100000.",
        candidate_answer=100000,
        parser_result=parser_result,
        modulus_result=modulus_result,
    )

    assert result.status == "retry"
    assert result.retry_recommended is True
    assert "answer is outside expected range [0, 99999]" in result.notes
    assert "candidate answer is not modulus-normalized" in result.notes


def test_verify_candidate_flags_parse_ambiguity_from_fallback():
    parser_result = ParseResult(
        raw_answer=-7,
        normalized_answer=99993,
        method="last_integer",
        success=True,
        confidence=0.6,
        notes=["boxed answer not found; used last integer fallback"],
    )
    modulus_result = ModulusResult(
        modulus=100000,
        source="final_answer_range",
        matched_text="final answer should be in [0, 99999]",
        success=True,
        notes=[],
    )

    result = verify_candidate(
        problem_text="The final answer should be in [0, 99999].",
        candidate_answer=99993,
        parser_result=parser_result,
        modulus_result=modulus_result,
        raw_reasoning_text="We think the answer is -7",
    )

    assert result.status == "flagged"
    assert result.retry_recommended is True
    assert "parse ambiguity flagged: answer did not come from boxed extraction" in result.notes


def test_verify_candidate_flags_suspiciously_tiny_answer():
    parser_result = ParseResult(
        raw_answer=1,
        normalized_answer=1,
        method="boxed",
        success=True,
        confidence=0.95,
        notes=[],
    )
    modulus_result = ModulusResult(
        modulus=100000,
        source="mod",
        matched_text="mod 10^5",
        success=True,
        notes=[],
    )

    result = verify_candidate(
        problem_text="Compute 2^(10^6) + 3^(10^6) mod 10^5.",
        candidate_answer=1,
        parser_result=parser_result,
        modulus_result=modulus_result,
    )

    assert result.status == "flagged"
    assert result.retry_recommended is False
    assert "suspiciously tiny answer flagged for review" in result.notes


def test_verify_candidate_retries_when_candidate_answer_is_not_integer():
    parser_result = ParseResult(
        raw_answer=None,
        normalized_answer=None,
        method="none",
        success=False,
        confidence=0.0,
        notes=["no integer answer found in model output"],
    )
    modulus_result = ModulusResult(
        modulus=None,
        source="none",
        matched_text=None,
        success=False,
        notes=["no modulus instruction detected"],
    )

    result = verify_candidate(
        problem_text="Find the integer answer.",
        candidate_answer=None,
        parser_result=parser_result,
        modulus_result=modulus_result,
    )

    assert result.status == "retry"
    assert result.retry_recommended is True
    assert "candidate answer is not an integer" in result.notes
    assert "parser did not produce a successful answer" in result.notes
