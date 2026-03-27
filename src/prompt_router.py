from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.prompt_builders import DEFAULT_PROMPTS_DIR, build_prompt
from src.policies import RetryDecision, SolvePolicy


PROMPT_FAMILY_SPECS = {
    "baseline": {"variant_name": "baseline", "include_tool_guidance": False},
    "tool_guided": {"variant_name": "baseline", "include_tool_guidance": True},
    "self_refute": {"variant_name": "reflexion_self_refute", "include_tool_guidance": False},
}

PROMPT_FAMILY_ALIASES = {
    "baseline_tir": "baseline",
    "reflexion_rigor": "self_refute",
    "large_number": "baseline",
}


@dataclass(frozen=True, slots=True)
class PromptRoute:
    family_name: str
    variant_name: str
    include_tool_guidance: bool
    task_hint: str | None
    full_prompt: str


def build_prompt_routes(
    family_sequence: tuple[str, ...] | list[str],
    *,
    task_hint: str | None = None,
    prompts_dir: str | Path = DEFAULT_PROMPTS_DIR,
) -> list[PromptRoute]:
    routes: list[PromptRoute] = []
    for family_name in family_sequence:
        normalized_family = normalize_prompt_family(family_name)
        spec = PROMPT_FAMILY_SPECS.get(normalized_family)
        if spec is None:
            raise ValueError(f"unknown prompt family: {family_name}")

        prompt = build_prompt(
            spec["variant_name"],
            include_tool_guidance=spec["include_tool_guidance"],
            task_hint=task_hint,
            prompts_dir=prompts_dir,
        )
        routes.append(
            PromptRoute(
                family_name=normalized_family,
                variant_name=prompt.variant_name,
                include_tool_guidance=spec["include_tool_guidance"],
                task_hint=task_hint,
                full_prompt=prompt.full_prompt,
            )
        )
    return routes


def build_prompt_routes_for_policy(
    policy: SolvePolicy,
    *,
    task_hint: str | None = None,
    prompts_dir: str | Path = DEFAULT_PROMPTS_DIR,
) -> list[PromptRoute]:
    return build_prompt_routes(
        policy.prompt_families,
        task_hint=task_hint,
        prompts_dir=prompts_dir,
    )


def build_retry_prompt_route(
    policy: SolvePolicy,
    retry_decision: RetryDecision,
    *,
    task_hint: str | None = None,
    prompts_dir: str | Path = DEFAULT_PROMPTS_DIR,
) -> PromptRoute | None:
    if not retry_decision.should_retry or retry_decision.prompt_family is None:
        return None
    routes = build_prompt_routes(
        [retry_decision.prompt_family],
        task_hint=task_hint,
        prompts_dir=prompts_dir,
    )
    return routes[0]


def normalize_prompt_family(family_name: str) -> str:
    return PROMPT_FAMILY_ALIASES.get(family_name, family_name)
