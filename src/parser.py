from __future__ import annotations

import re

from src.result_schema import ParseResult


DEFAULT_NORMALIZATION_MODULUS = 100_000
BOXED_PREFIX = r"\boxed{"
INTEGER_PATTERN = re.compile(r"[-+]?\d+")


def normalize_answer(answer: int, modulus: int = DEFAULT_NORMALIZATION_MODULUS) -> int:
    if modulus <= 0:
        raise ValueError("modulus must be positive")
    return answer % modulus


def parse_model_output(
    raw_output: str,
    *,
    normalization_modulus: int = DEFAULT_NORMALIZATION_MODULUS,
) -> ParseResult:
    if not isinstance(raw_output, str):
        raise TypeError("raw_output must be a string")

    notes: list[str] = []

    boxed_content = _extract_last_boxed_content(raw_output)
    if boxed_content is not None:
        boxed_value = _parse_integer_text(boxed_content)
        if boxed_value is not None:
            return ParseResult(
                raw_answer=boxed_value,
                normalized_answer=normalize_answer(boxed_value, normalization_modulus),
                method="boxed",
                success=True,
                confidence=0.95,
                notes=notes,
            )
        notes.append("found boxed answer but its contents were not a valid integer")

    integers = INTEGER_PATTERN.findall(raw_output)
    if integers:
        raw_answer = int(integers[-1])
        if boxed_content is None:
            notes.append("boxed answer not found; used last integer fallback")
        else:
            notes.append("used last integer fallback after invalid boxed answer")
        return ParseResult(
            raw_answer=raw_answer,
            normalized_answer=normalize_answer(raw_answer, normalization_modulus),
            method="last_integer",
            success=True,
            confidence=0.6,
            notes=notes,
        )

    if boxed_content is None:
        notes.append("no boxed answer found")
    notes.append("no integer answer found in model output")
    return ParseResult(
        raw_answer=None,
        normalized_answer=None,
        method="none",
        success=False,
        confidence=0.0,
        notes=notes,
    )


def _parse_integer_text(value: str) -> int | None:
    candidate = value.strip()
    if not candidate:
        return None
    if not re.fullmatch(r"[-+]?\d+", candidate):
        return None
    return int(candidate)


def _extract_last_boxed_content(raw_output: str) -> str | None:
    start = 0
    last_content: str | None = None

    while True:
        prefix_index = raw_output.find(BOXED_PREFIX, start)
        if prefix_index == -1:
            return last_content

        content_start = prefix_index + len(BOXED_PREFIX)
        depth = 1
        index = content_start

        while index < len(raw_output) and depth > 0:
            char = raw_output[index]
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
            index += 1

        if depth == 0:
            last_content = raw_output[content_start : index - 1]
            start = index
            continue

        return last_content
