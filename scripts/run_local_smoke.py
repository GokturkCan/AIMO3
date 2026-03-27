from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.logging_utils import write_csv_report, write_json, write_jsonl
from src.modulus import detect_modulus
from src.parser import parse_model_output
from src.prompt_builders import build_prompt
from src.verify_fix import verify_candidate


ATTEMPT_LOG_PATH = PROJECT_ROOT / "artifacts/logs/local_smoke_attempts.jsonl"
SUMMARY_JSON_PATH = PROJECT_ROOT / "artifacts/reports/local_smoke_summary.json"
REPORT_CSV_PATH = PROJECT_ROOT / "artifacts/reports/local_smoke_report.csv"


def main() -> int:
    samples = [
        {
            "id": "smoke-1",
            "variant": "baseline",
            "task_hint": "Prefer a direct solution and a clear final integer.",
            "problem": "Find the remainder when divided by 99991.",
            "raw_output": "Quick check gives the final result \\boxed{336}.",
        },
        {
            "id": "smoke-2",
            "variant": "large_number_pattern",
            "task_hint": "Look for patterns in smaller cases before generalizing.",
            "problem": "Compute 2^(10^6) + 3^(10^6) mod 10^5.",
            "raw_output": "Small cases suggest a cycle. Final answer is 1",
        },
        {
            "id": "smoke-3",
            "variant": "reflexion_rigor",
            "task_hint": "Do a quick solve-and-check pass before finalizing.",
            "problem": "The final answer should be in [0, 99999].",
            "raw_output": "I found two candidates \\boxed{17} and later \\boxed{42}.",
        },
    ]

    attempt_records = []
    report_rows = []

    for sample in samples:
        prompt = build_prompt(
            sample["variant"],
            include_tool_guidance=True,
            task_hint=sample["task_hint"],
        )
        modulus_result = detect_modulus(sample["problem"])
        parser_result = parse_model_output(sample["raw_output"])
        candidate_answer = parser_result.normalized_answer
        verify_result = verify_candidate(
            problem_text=sample["problem"],
            candidate_answer=candidate_answer,
            parser_result=parser_result,
            modulus_result=modulus_result,
            raw_reasoning_text=sample["raw_output"],
        )

        attempt_records.append(
            {
                "id": sample["id"],
                "variant": sample["variant"],
                "prompt_length": len(prompt.full_prompt),
                "problem": sample["problem"],
                "raw_output": sample["raw_output"],
                "modulus_result": asdict(modulus_result),
                "parser_result": asdict(parser_result),
                "verify_result": asdict(verify_result),
            }
        )
        report_rows.append(
            {
                "id": sample["id"],
                "variant": sample["variant"],
                "parse_method": parser_result.method,
                "candidate_answer": candidate_answer,
                "verify_status": verify_result.status,
                "retry_recommended": verify_result.retry_recommended,
            }
        )

    write_jsonl(ATTEMPT_LOG_PATH, attempt_records)
    write_csv_report(
        REPORT_CSV_PATH,
        report_rows,
        fieldnames=[
            "id",
            "variant",
            "parse_method",
            "candidate_answer",
            "verify_status",
            "retry_recommended",
        ],
    )

    status_counts = _count_statuses(report_rows)
    retry_count = _count_retries(report_rows)
    summary = {
        "num_samples": len(samples),
        "status_counts": status_counts,
        "retry_count": retry_count,
        "attempt_log_path": str(ATTEMPT_LOG_PATH),
        "report_csv_path": str(REPORT_CSV_PATH),
        "summary_json_path": str(SUMMARY_JSON_PATH),
    }
    write_json(SUMMARY_JSON_PATH, summary)

    for row in report_rows:
        print(
            f"{row['id']} variant={row['variant']} parse={row['parse_method']} "
            f"answer={row['candidate_answer']} verify={row['verify_status']} "
            f"retry={row['retry_recommended']}"
        )

    print(
        f"summary samples={summary['num_samples']} "
        f"ok={status_counts.get('ok', 0)} "
        f"flagged={status_counts.get('flagged', 0)} "
        f"retry={retry_count}"
    )
    print(f"artifacts report={REPORT_CSV_PATH}")
    print(f"artifacts log={ATTEMPT_LOG_PATH}")
    print(f"artifacts summary={SUMMARY_JSON_PATH}")
    return 0


def _count_statuses(report_rows: list[dict[str, object]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in report_rows:
        status = str(row["verify_status"])
        counts[status] = counts.get(status, 0) + 1
    return counts


def _count_retries(report_rows: list[dict[str, object]]) -> int:
    return sum(1 for row in report_rows if bool(row["retry_recommended"]))


if __name__ == "__main__":
    raise SystemExit(main())
