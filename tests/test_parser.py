import pytest

from src.parser import parse_model_output


def test_parse_prefers_boxed_answer():
    raw_output = "Reasoning here. Final: \\boxed{-42}. Ignore trailing 99."

    result = parse_model_output(raw_output)

    assert result.success is True
    assert result.method == "boxed"
    assert result.raw_answer == -42
    assert result.normalized_answer == 99958
    assert result.confidence == pytest.approx(0.95)
    assert result.notes == []


def test_parse_falls_back_to_last_integer_when_boxed_missing():
    raw_output = "We tried 11, then 12, and the final answer is -7"

    result = parse_model_output(raw_output)

    assert result.success is True
    assert result.method == "last_integer"
    assert result.raw_answer == -7
    assert result.normalized_answer == 99993
    assert "boxed answer not found; used last integer fallback" in result.notes


def test_parse_failure_has_explicit_notes():
    raw_output = "No final integer is available here."

    result = parse_model_output(raw_output)

    assert result.success is False
    assert result.method == "none"
    assert result.raw_answer is None
    assert result.normalized_answer is None
    assert result.confidence == pytest.approx(0.0)
    assert "no boxed answer found" in result.notes
    assert "no integer answer found in model output" in result.notes


def test_parse_normalizes_into_zero_to_99999():
    raw_output = "Final answer: \\boxed{-100001}"

    result = parse_model_output(raw_output)

    assert result.success is True
    assert result.raw_answer == -100001
    assert result.normalized_answer == 99999
