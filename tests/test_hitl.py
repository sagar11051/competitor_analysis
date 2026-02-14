"""Tests for Human-in-the-Loop (HITL) functionality.

Tests interrupt behavior, approval flows, and state resumption.
"""

import pytest
from langchain_core.messages import HumanMessage

from src.agents.graph import (
    _get_initial_state,
    checkpointer,
    create_session,
    get_compiled_graph,
    get_session_state,
    resume_session,
)
from src.agents.state import (
    APPROVAL_APPROVED_PLAN,
    APPROVAL_APPROVED_RESEARCH,
    APPROVAL_PENDING_PLAN,
    APPROVAL_PENDING_RESEARCH,
    APPROVAL_PENDING_STRATEGY,
)


# -----------------------------------------------------------------------------
# Session Creation Tests
# -----------------------------------------------------------------------------


def test_create_session_returns_session_id():
    session_id, state = create_session("https://example.com")
    assert session_id is not None
    assert len(session_id) > 0


def test_create_session_returns_state():
    session_id, state = create_session("https://example.com")
    assert state is not None
    assert "approval_status" in state
    assert "company_url" in state


def test_create_session_sets_company_url():
    session_id, state = create_session("https://test-company.com")
    assert state["company_url"] == "https://test-company.com"


def test_create_session_with_initial_query():
    session_id, state = create_session(
        company_url="https://example.com",
        initial_query="Analyze competitors for this company",
    )
    messages = state.get("messages", [])
    # Should have the initial user message plus AI messages from planner
    assert len(messages) >= 1


def test_create_session_stops_at_first_hitl_gate():
    """Session should pause at pending_plan_approval after planner runs."""
    session_id, state = create_session("https://example.com")
    # After planner completes, status should be pending_plan_approval
    assert state["approval_status"] == APPROVAL_PENDING_PLAN


def test_create_session_generates_research_tasks():
    """Planner should create research tasks before interrupting."""
    session_id, state = create_session("https://example.com")
    tasks = state.get("research_tasks", [])
    assert len(tasks) >= 1
    for task in tasks:
        assert "type" in task
        assert "target" in task


# -----------------------------------------------------------------------------
# Session State Retrieval Tests
# -----------------------------------------------------------------------------


def test_get_session_state_returns_state():
    session_id, _ = create_session("https://example.com")
    state = get_session_state(session_id)
    assert state is not None
    assert state["session_id"] == session_id


def test_get_session_state_returns_none_for_unknown():
    state = get_session_state("nonexistent-session-id")
    assert state is None


def test_get_session_state_preserves_values():
    session_id, original = create_session("https://mycompany.com")
    retrieved = get_session_state(session_id)
    assert retrieved["company_url"] == "https://mycompany.com"
    assert retrieved["approval_status"] == original["approval_status"]


# -----------------------------------------------------------------------------
# Session Resumption Tests
# -----------------------------------------------------------------------------


def test_resume_session_with_approve():
    """Approving the plan should proceed to researcher."""
    session_id, state = create_session("https://example.com")
    assert state["approval_status"] == APPROVAL_PENDING_PLAN

    # Approve the plan
    new_state = resume_session(session_id, "approve")

    # After researcher runs, status should be pending_research_approval
    assert new_state["approval_status"] == APPROVAL_PENDING_RESEARCH


def test_resume_session_with_approve_adds_results():
    """After approving plan and running researcher, should have results."""
    session_id, state = create_session("https://example.com")

    # Approve the plan
    new_state = resume_session(session_id, "approve")

    # Should have research results (even if some failed)
    results = new_state.get("research_results", [])
    assert len(results) >= 1


def test_resume_session_with_user_message():
    """User message should be added to messages."""
    session_id, state = create_session("https://example.com")
    initial_message_count = len(state.get("messages", []))

    # Approve with a message
    new_state = resume_session(
        session_id, "approve", user_message="Looks good, proceed!"
    )

    # Should have at least one more message (user's)
    new_message_count = len(new_state.get("messages", []))
    assert new_message_count > initial_message_count


def test_resume_session_raises_for_unknown_session():
    """Should raise ValueError for unknown session."""
    with pytest.raises(ValueError, match="not found"):
        resume_session("unknown-session-123", "approve")


# -----------------------------------------------------------------------------
# Full Workflow Tests
# -----------------------------------------------------------------------------


def test_full_workflow_approve_all_stages():
    """Test approving through all 3 HITL gates."""
    # Stage 1: Create session (runs planner)
    session_id, state = create_session("https://example.com")
    assert state["approval_status"] == APPROVAL_PENDING_PLAN

    # Stage 2: Approve plan (runs researcher)
    state = resume_session(session_id, "approve")
    assert state["approval_status"] == APPROVAL_PENDING_RESEARCH

    # Stage 3: Approve research (runs strategist)
    state = resume_session(session_id, "approve")
    assert state["approval_status"] == APPROVAL_PENDING_STRATEGY

    # Stage 4: Approve strategy (completes workflow)
    state = resume_session(session_id, "approve")

    # Final state checks
    assert state.get("strategic_insights") is not None
    assert len(state.get("strategy_drafts", [])) >= 1


def test_workflow_progression_accumulates_data():
    """Each stage should accumulate data from previous stages."""
    session_id, state = create_session("https://example.com")

    # After planner: should have tasks but no results
    assert len(state.get("research_tasks", [])) >= 1
    assert len(state.get("research_results", [])) == 0

    # After researcher: should have results
    state = resume_session(session_id, "approve")
    assert len(state.get("research_results", [])) >= 1
    assert len(state.get("strategy_drafts", [])) == 0

    # After strategist: should have strategy
    state = resume_session(session_id, "approve")
    assert len(state.get("strategy_drafts", [])) >= 1


# -----------------------------------------------------------------------------
# Checkpointer Tests
# -----------------------------------------------------------------------------


def test_checkpointer_persists_state():
    """State should persist in checkpointer between operations."""
    session_id, state = create_session("https://persisted.com")

    # Retrieve state directly from checkpointer
    compiled = get_compiled_graph()
    config = {"configurable": {"thread_id": session_id}}
    snapshot = compiled.get_state(config)

    assert snapshot is not None
    assert snapshot.values["company_url"] == "https://persisted.com"


def test_multiple_sessions_are_independent():
    """Multiple sessions should not interfere with each other."""
    # Create two sessions
    session1_id, state1 = create_session("https://company1.com")
    session2_id, state2 = create_session("https://company2.com")

    # Verify they're different
    assert session1_id != session2_id

    # Verify each maintains its own state
    retrieved1 = get_session_state(session1_id)
    retrieved2 = get_session_state(session2_id)

    assert retrieved1["company_url"] == "https://company1.com"
    assert retrieved2["company_url"] == "https://company2.com"
