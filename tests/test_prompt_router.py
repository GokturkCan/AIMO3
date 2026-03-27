from src.policies import default_policy_set
from src.prompt_router import build_prompt_routes, build_prompt_routes_for_policy, build_retry_prompt_route


def test_build_prompt_routes_resolves_prompt_families():
    routes = build_prompt_routes(("baseline", "tool_guided", "self_refute"))

    assert len(routes) == 3
    assert routes[0].family_name == "baseline"
    assert routes[1].include_tool_guidance is True
    assert routes[2].variant_name == "reflexion_self_refute"


def test_build_prompt_routes_supports_legacy_baseline_alias():
    routes = build_prompt_routes(("baseline_tir",))

    assert routes[0].family_name == "baseline"


def test_build_prompt_routes_for_policy_and_retry_route_use_small_controlled_families():
    policy = default_policy_set().medium
    routes = build_prompt_routes_for_policy(policy)
    retry_route = build_retry_prompt_route(
        policy,
        type("RetryDecisionStub", (), {"should_retry": True, "prompt_family": "self_refute"})(),
    )

    assert {route.family_name for route in routes} <= {"baseline", "tool_guided", "self_refute"}
    assert retry_route is not None
    assert retry_route.family_name == "self_refute"
