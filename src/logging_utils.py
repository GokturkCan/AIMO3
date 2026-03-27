from __future__ import annotations

import csv
import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any


def write_jsonl(path: str | Path, records: Iterable[Mapping[str, Any]]) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(dict(record), ensure_ascii=True, sort_keys=True))
            handle.write("\n")

    return output_path


def write_csv_report(
    path: str | Path,
    rows: Iterable[Mapping[str, Any]],
    *,
    fieldnames: list[str],
) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    return output_path


def write_json(path: str | Path, payload: Mapping[str, Any]) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(dict(payload), handle, ensure_ascii=True, indent=2, sort_keys=True)
        handle.write("\n")

    return output_path
