"""Tests for the main graph composition and execution."""

import pytest
from langchain_core.messages import HumanMessage

from src.agents.graph import (
    _get_initial_state,
    _resolve_approval_action,
    build_main_graph,
    get_compiled_graph,
    hitl_gate_1,
    hitl_gate_2,
    hitl_gate_3,
    route_after_gate_1,
    route_after_gate_2,
    route_after_gate_3,
)
from src.agents.state import (
    APPROVAL_APPROVED_PLAN,
    APPROVAL_APPROVED_RESEARCH,
    APPROVAL_APPROVED_STRATEGY,
    APPROVAL_PENDING_PLAN,
    APPROVAL_PENDING_RESEARCH,
    APPROVAL_PENDING_STRATEGY,
    APPROVAL_REVISION_REQUESTED,
    AgentState,
)


def _make_state(**overrides) -> AgentState:
    """Create a minimal valid AgentState for testing."""
    base: AgentState = {
        "messages": [HumanMessage(content="Analyze https://example.com")],
        "session_id": "test-session",
        "user_profile": {"role": "consultant"},
        "research_tasks": [],
        "research_results": [],
        "strategy_drafts": [],
        "approval_status": "",
        "company_url": "https://example.com",
        "company_profile": None,
        "competitors": [],
        "competitor_analyses": [],
        "strategic_insights": None,
    }
    base.update(overrides)
    return base


# -----------------------------------------------------------------------------
# Initial State Tests
# -----------------------------------------------------------------------------


def test_get_initial_state_sets_company_url():
    state = _get_initial_state("https://test.com")
    assert state["company_url"] == "https://test.com"
    assert state["session_id"] is not None
    assert state["messages"] == []
    assert state["research_tasks"] == []


def test_get_initial_state_with_session_id():
    state = _get_initial_state("https://test.com", session_id="custom-id")
    assert state["session_id"] == "custom-id"


def test_get_initial_state_with_user_profile():
    profile = {"role": "analyst", "company": "TestCorp"}
    state = _get_initial_state("https://test.com", user_profile=profile)
    assert state["user_profile"] == profile


# -----------------------------------------------------------------------------
# HITL Gate Node Tests
# -----------------------------------------------------------------------------


def test_hitl_gate_1_returns_empty_dict():
    state = _make_state(approval_status=APPROVAL_PENDING_PLAN)
    result = hitl_gate_1(state)
    assert result == {}


def test_hitl_gate_2_returns_empty_dict():
    state = _make_state(approval_status=APPROVAL_PENDING_RESEARCH)
    result = hitl_gate_2(state)
    assert result == {}


def test_hitl_gate_3_returns_empty_dict():
    state = _make_state(approval_status=APPROVAL_PENDING_STRATEGY)
    result = hitl_gate_3(state)
    assert result == {}


# -----------------------------------------------------------------------------
# Routing Function Tests
# -----------------------------------------------------------------------------


def test_route_after_gate_1_approved():
    state = _make_state(approval_status=APPROVAL_APPROVED_PLAN)
    result = route_after_gate_1(state)
    assert result == "researcher"


def test_route_after_gate_1_revision():
    state = _make_state(approval_status=APPROVAL_REVISION_REQUESTED)
    result = route_after_gate_1(state)
    assert result == "planner"


def test_route_after_gate_1_unexpected():
    state = _make_state(approval_status="invalid_status")
    result = route_after_gate_1(state)
    assert result == "__end__"


def test_route_after_gate_2_approved():
    state = _make_state(approval_status=APPROVAL_APPROVED_RESEARCH)
    result = route_after_gate_2(state)
    assert result == "strategist"


def test_route_after_gate_2_revision():
    state = _make_state(approval_status=APPROVAL_REVISION_REQUESTED)
    result = route_after_gate_2(state)
    assert result == "researcher"


def test_route_after_gate_2_unexpected():
    state = _make_state(approval_status="invalid_status")
    result = route_after_gate_2(state)
    assert result == "__end__"


def test_route_after_gate_3_approved():
    state = _make_state(approval_status=APPROVAL_APPROVED_STRATEGY)
    result = route_after_gate_3(state)
    assert result == "__end__"


def test_route_after_gate_3_revision():
    state = _make_state(approval_status=APPROVAL_REVISION_REQUESTED)
    result = route_after_gate_3(state)
    assert result == "strategist"


# -----------------------------------------------------------------------------
# Approval Action Resolution Tests
# -----------------------------------------------------------------------------


def test_resolve_approval_action_approve_plan():
    result = _resolve_approval_action(APPROVAL_PENDING_PLAN, "approve")
    assert result == APPROVAL_APPROVED_PLAN


def test_resolve_approval_action_approve_research():
    result = _resolve_approval_action(APPROVAL_PENDING_RESEARCH, "approve")
    assert result == APPROVAL_APPROVED_RESEARCH


def test_resolve_approval_action_approve_strategy():
    result = _resolve_approval_action(APPROVAL_PENDING_STRATEGY, "approve")
    assert result == APPROVAL_APPROVED_STRATEGY


def test_resolve_approval_action_modify():
    result = _resolve_approval_action(APPROVAL_PENDING_PLAN, "modify")
    assert result == APPROVAL_REVISION_REQUESTED


def test_resolve_approval_action_reject():
    result = _resolve_approval_action(APPROVAL_PENDING_RESEARCH, "reject")
    assert result == APPROVAL_REVISION_REQUESTED


def test_resolve_approval_action_unknown_keeps_current():
    result = _resolve_approval_action(APPROVAL_PENDING_PLAN, "unknown_action")
    assert result == APPROVAL_PENDING_PLAN


# -----------------------------------------------------------------------------
# Graph Building Tests
# -----------------------------------------------------------------------------


def test_build_main_graph_returns_state_graph():
    graph = build_main_graph()
    assert graph is not None


def test_main_graph_has_expected_nodes():
    graph = build_main_graph()
    node_names = list(graph.nodes.keys())
    expected_nodes = ["planner", "researcher", "strategist", "hitl_gate_1", "hitl_gate_2", "hitl_gate_3"]
    for node in expected_nodes:
        assert node in node_names, f"Missing node: {node}"


def test_get_compiled_graph_returns_compiled_graph():
    compiled = get_compiled_graph()
    assert compiled is not None
    # Verify it has invoke method
    assert hasattr(compiled, "invoke")
    assert hasattr(compiled, "get_state")
    assert hasattr(compiled, "update_state")


def test_compiled_graph_has_checkpointer():
    compiled = get_compiled_graph()
    # The compiled graph should have a checkpointer attribute
    assert hasattr(compiled, "checkpointer")
