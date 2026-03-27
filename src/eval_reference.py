from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from src.logging_utils import write_csv_report, write_json, write_jsonl


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REFERENCE_CSV = PROJECT_ROOT / "data/reference/reference.csv"
DEFAULT_ATTEMPT_LOG_PATH = PROJECT_ROOT / "artifacts/logs/reference_eval_attempts.jsonl"
DEFAULT_REPORT_CSV_PATH = PROJECT_ROOT / "artifacts/reports/reference_eval.csv"
DEFAULT_SUMMARY_JSON_PATH = PROJECT_ROOT / "artifacts/reports/reference_eval_summary.json"

REFERENCE_COLUMNS = ["id", "problem", "answer"]
PREDICTION_COLUMNS = ["id", "answer"]
REPORT_COLUMNS = ["id", "expected_answer", "predicted_answer", "is_correct"]


def evaluate_reference(
    predictions_csv_path: str | Path,
    *,
    reference_csv_path: str | Path = DEFAULT_REFERENCE_CSV,
    attempt_log_path: str | Path = DEFAULT_ATTEMPT_LOG_PATH,
    report_csv_path: str | Path = DEFAULT_REPORT_CSV_PATH,
    summary_json_path: str | Path = DEFAULT_SUMMARY_JSON_PATH,
) -> dict[str, Any]:
    reference_rows = _read_csv(reference_csv_path, expected_columns=REFERENCE_COLUMNS)
    prediction_rows = _read_csv(predictions_csv_path, expected_columns=PREDICTION_COLUMNS)

    reference_by_id = _build_row_lookup(reference_rows, path=reference_csv_path)
    prediction_by_id = _build_row_lookup(prediction_rows, path=predictions_csv_path)
    _validate_id_sets(reference_by_id, prediction_by_id)

    comparison_rows: list[dict[str, Any]] = []
    attempt_records: list[dict[str, Any]] = []
    num_correct = 0

    for reference_row in reference_rows:
        row_id = reference_row["id"]
        expected_answer = _parse_int(
            reference_row["answer"],
            column_name="answer",
            row_id=row_id,
            path=reference_csv_path,
        )
        predicted_answer = _parse_int(
            prediction_by_id[row_id]["answer"],
            column_name="answer",
            row_id=row_id,
            path=predictions_csv_path,
        )
        is_correct = predicted_answer == expected_answer
        if is_correct:
            num_correct += 1

        comparison_row = {
            "id": row_id,
            "expected_answer": expected_answer,
            "predicted_answer": predicted_answer,
            "is_correct": is_correct,
        }
        comparison_rows.append(comparison_row)

        attempt_records.append(
            {
                "event": "reference_eval_question",
                "id": row_id,
                "expected_answer": expected_answer,
                "predicted_answer": predicted_answer,
                "is_correct": is_correct,
            }
        )

    num_questions = len(reference_rows)
    accuracy = num_correct / num_questions if num_questions else 0.0
    summary = {
        "num_questions": num_questions,
        "num_correct": num_correct,
        "accuracy": accuracy,
        "reference_csv_path": str(Path(reference_csv_path)),
        "predictions_csv_path": str(Path(predictions_csv_path)),
        "attempt_log_path": str(Path(attempt_log_path)),
        "report_csv_path": str(Path(report_csv_path)),
        "summary_json_path": str(Path(summary_json_path)),
    }

    write_jsonl(attempt_log_path, attempt_records)
    write_csv_report(report_csv_path, comparison_rows, fieldnames=REPORT_COLUMNS)
    write_json(summary_json_path, summary)

    return {
        "summary": summary,
        "comparisons": comparison_rows,
    }


def _read_csv(path: str | Path, *, expected_columns: list[str]) -> list[dict[str, str]]:
    csv_path = Path(path)
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        actual_columns = reader.fieldnames
        if actual_columns != expected_columns:
            raise ValueError(
                f"schema mismatch for {csv_path}: expected columns {expected_columns}, got {actual_columns}"
            )
        return list(reader)


def _build_row_lookup(
    rows: list[dict[str, str]],
    *,
    path: str | Path,
) -> dict[str, dict[str, str]]:
    lookup: dict[str, dict[str, str]] = {}
    for row in rows:
        row_id = row["id"]
        if row_id in lookup:
            raise ValueError(f"duplicate id '{row_id}' found in {Path(path)}")
        lookup[row_id] = row
    return lookup


def _validate_id_sets(
    reference_by_id: dict[str, dict[str, str]],
    prediction_by_id: dict[str, dict[str, str]],
) -> None:
    reference_ids = set(reference_by_id)
    prediction_ids = set(prediction_by_id)
    missing_ids = sorted(reference_ids - prediction_ids)
    extra_ids = sorted(prediction_ids - reference_ids)

    if missing_ids or extra_ids:
        raise ValueError(
            f"prediction ids do not match reference ids: missing={missing_ids}, extra={extra_ids}"
        )


def _parse_int(value: str, *, column_name: str, row_id: str, path: str | Path) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(
            f"invalid integer in column '{column_name}' for id '{row_id}' in {Path(path)}: {value!r}"
        ) from exc
