from __future__ import annotations

import re

from src.result_schema import ModulusResult


DEFAULT_FINAL_ANSWER_MODULUS = 100_000
POWER_PATTERN = re.compile(r"(?P<base>\d+)\s*\^\s*(?P<exponent>\d+)")
PATTERN_SPECS = (
    ("modulo", re.compile(r"\bmodulo\s+(?P<value>\d+(?:\s*\^\s*\d+)?)", re.IGNORECASE)),
    ("mod", re.compile(r"\bmod\s+(?P<value>\d+(?:\s*\^\s*\d+)?)", re.IGNORECASE)),
    (
        "remainder_when_divided_by",
        re.compile(r"\bremainder\s+when\s+divided\s+by\s+(?P<value>\d+)", re.IGNORECASE),
    ),
    (
        "remainder_when_expression_is_divided_by",
        re.compile(
            r"\bremainder\s+when\b.*?\bis\s+divided\s+by\s+(?P<value>\d+)",
            re.IGNORECASE,
        ),
    ),
    (
        "final_answer_range",
        re.compile(
            r"\bfinal\s+answer\s+should\s+be\s+in\s*\[\s*0\s*,\s*99999\s*\]",
            re.IGNORECASE,
        ),
    ),
)


def detect_modulus(problem_text: str) -> ModulusResult:
    if not isinstance(problem_text, str):
        raise TypeError("problem_text must be a string")

    notes: list[str] = []

    for source, pattern in PATTERN_SPECS:
        match = pattern.search(problem_text)
        if match is None:
            continue

        matched_text = match.group(0)
        if source == "final_answer_range":
            notes.append("used fixed normalization modulus for required final answer range")
            return ModulusResult(
                modulus=DEFAULT_FINAL_ANSWER_MODULUS,
                source=source,
                matched_text=matched_text,
                success=True,
                notes=notes,
            )

        raw_value = match.group("value")
        modulus = _parse_modulus_value(raw_value)
        if modulus is None:
            notes.append(f"matched modulus instruction but could not parse value: {raw_value}")
            return ModulusResult(
                modulus=None,
                source=source,
                matched_text=matched_text,
                success=False,
                notes=notes,
            )

        return ModulusResult(
            modulus=modulus,
            source=source,
            matched_text=matched_text,
            success=True,
            notes=notes,
        )

    notes.append("no modulus instruction detected")
    return ModulusResult(
        modulus=None,
        source="none",
        matched_text=None,
        success=False,
        notes=notes,
    )


def _parse_modulus_value(raw_value: str) -> int | None:
    stripped = raw_value.strip()
    if stripped.isdigit():
        return int(stripped)

    power_match = POWER_PATTERN.fullmatch(stripped)
    if power_match is None:
        return None

    base = int(power_match.group("base"))
    exponent = int(power_match.group("exponent"))
    return base**exponent
