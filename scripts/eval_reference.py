from __future__ import annotations

import argparse

from src.eval_reference import (
    DEFAULT_ATTEMPT_LOG_PATH,
    DEFAULT_REFERENCE_CSV,
    DEFAULT_REPORT_CSV_PATH,
    DEFAULT_SUMMARY_JSON_PATH,
    evaluate_reference,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate predictions against reference.csv")
    parser.add_argument("predictions_csv", help="Path to predictions CSV with columns: id,answer")
    parser.add_argument(
        "--reference-csv",
        default=str(DEFAULT_REFERENCE_CSV),
        help="Path to reference CSV with columns: id,problem,answer",
    )
    parser.add_argument(
        "--attempt-log",
        default=str(DEFAULT_ATTEMPT_LOG_PATH),
        help="Path to attempt-level JSONL output",
    )
    parser.add_argument(
        "--report-csv",
        default=str(DEFAULT_REPORT_CSV_PATH),
        help="Path to per-question comparison CSV output",
    )
    parser.add_argument(
        "--summary-json",
        default=str(DEFAULT_SUMMARY_JSON_PATH),
        help="Path to final summary JSON output",
    )
    args = parser.parse_args()

    result = evaluate_reference(
        args.predictions_csv,
        reference_csv_path=args.reference_csv,
        attempt_log_path=args.attempt_log,
        report_csv_path=args.report_csv,
        summary_json_path=args.summary_json,
    )
    summary = result["summary"]

    print(f"accuracy={summary['accuracy']:.6f}")
    print(f"num_correct={summary['num_correct']}")
    print(f"num_questions={summary['num_questions']}")
    print(f"report_csv={summary['report_csv_path']}")
    print(f"attempt_log={summary['attempt_log_path']}")
    print(f"summary_json={summary['summary_json_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
