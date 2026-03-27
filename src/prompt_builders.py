from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROMPTS_DIR = PROJECT_ROOT / "prompts"
SYSTEM_PROMPT_VARIANTS = {
    "baseline",
    "reflexion_rigor",
    "reflexion_self_refute",
    "large_number_pattern",
}


@dataclass(slots=True)
class PromptBuildResult:
    variant_name: str
    system_prompt: str
    tool_guidance: str | None
    task_hint: str | None
    full_prompt: str


def list_prompt_variants() -> list[str]:
    return sorted(SYSTEM_PROMPT_VARIANTS)


def load_prompt_template(name: str, *, prompts_dir: str | Path = DEFAULT_PROMPTS_DIR) -> str:
    template_path = Path(prompts_dir) / f"{name}.txt"
    if not template_path.exists():
        raise ValueError(f"unknown prompt template: {name}")
    return template_path.read_text(encoding="utf-8").strip()


def build_prompt(
    variant_name: str,
    *,
    include_tool_guidance: bool = False,
    task_hint: str | None = None,
    prompts_dir: str | Path = DEFAULT_PROMPTS_DIR,
) -> PromptBuildResult:
    if variant_name not in SYSTEM_PROMPT_VARIANTS:
        raise ValueError(
            f"unknown prompt variant: {variant_name}. Available variants: {list_prompt_variants()}"
        )

    system_prompt = load_prompt_template(variant_name, prompts_dir=prompts_dir)
    tool_guidance = None
    if include_tool_guidance:
        tool_guidance = load_prompt_template("tool_guided", prompts_dir=prompts_dir)

    full_prompt = compose_prompt(
        system_prompt=system_prompt,
        tool_guidance=tool_guidance,
        task_hint=task_hint,
    )
    return PromptBuildResult(
        variant_name=variant_name,
        system_prompt=system_prompt,
        tool_guidance=tool_guidance,
        task_hint=task_hint,
        full_prompt=full_prompt,
    )


def compose_prompt(
    *,
    system_prompt: str,
    tool_guidance: str | None = None,
    task_hint: str | None = None,
) -> str:
    sections = [system_prompt.strip()]
    if tool_guidance:
        sections.append(tool_guidance.strip())
    if task_hint:
        sections.append(f"Task hint:\n{task_hint.strip()}")
    return "\n\n".join(section for section in sections if section)
