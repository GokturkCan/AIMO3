import csv
import json

import pytest

from src.eval_reference import evaluate_reference


def test_evaluate_reference_writes_reports_and_summary(tmp_path):
    reference_csv = tmp_path / "reference.csv"
    predictions_csv = tmp_path / "predictions.csv"
    attempt_log = tmp_path / "logs" / "attempts.jsonl"
    report_csv = tmp_path / "reports" / "reference_eval.csv"
    summary_json = tmp_path / "reports" / "reference_eval_summary.json"

    _write_csv(
        reference_csv,
        fieldnames=["id", "problem", "answer"],
        rows=[
            {"id": "a", "problem": "Problem A", "answer": "7"},
            {"id": "b", "problem": "Problem B", "answer": "11"},
        ],
    )
    _write_csv(
        predictions_csv,
        fieldnames=["id", "answer"],
        rows=[
            {"id": "a", "answer": "7"},
            {"id": "b", "answer": "13"},
        ],
    )

    result = evaluate_reference(
        predictions_csv,
        reference_csv_path=reference_csv,
        attempt_log_path=attempt_log,
        report_csv_path=report_csv,
        summary_json_path=summary_json,
    )

    assert result["summary"]["num_questions"] == 2
    assert result["summary"]["num_correct"] == 1
    assert result["summary"]["accuracy"] == pytest.approx(0.5)
    assert len(result["comparisons"]) == 2

    report_rows = _read_csv_rows(report_csv)
    assert report_rows == [
        {
            "id": "a",
            "expected_answer": "7",
            "predicted_answer": "7",
            "is_correct": "True",
        },
        {
            "id": "b",
            "expected_answer": "11",
            "predicted_answer": "13",
            "is_correct": "False",
        },
    ]

    attempt_lines = attempt_log.read_text(encoding="utf-8").strip().splitlines()
    assert len(attempt_lines) == 2
    first_attempt = json.loads(attempt_lines[0])
    assert first_attempt["event"] == "reference_eval_question"
    assert first_attempt["id"] == "a"
    assert first_attempt["is_correct"] is True

    summary_payload = json.loads(summary_json.read_text(encoding="utf-8"))
    assert summary_payload["num_questions"] == 2
    assert summary_payload["num_correct"] == 1
    assert summary_payload["accuracy"] == pytest.approx(0.5)


def test_evaluate_reference_fails_loudly_on_prediction_schema_mismatch(tmp_path):
    reference_csv = tmp_path / "reference.csv"
    predictions_csv = tmp_path / "predictions.csv"

    _write_csv(
        reference_csv,
        fieldnames=["id", "problem", "answer"],
        rows=[{"id": "a", "problem": "Problem A", "answer": "7"}],
    )
    _write_csv(
        predictions_csv,
        fieldnames=["id", "prediction"],
        rows=[{"id": "a", "prediction": "7"}],
    )

    with pytest.raises(ValueError, match="schema mismatch"):
        evaluate_reference(predictions_csv, reference_csv_path=reference_csv)


def _write_csv(path, *, fieldnames, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _read_csv_rows(path):
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))
