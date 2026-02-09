"""Tests for src.agents.state — AgentState TypedDict and approval constants."""

from langchain_core.messages import HumanMessage

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


def test_agent_state_can_be_instantiated():
    """AgentState TypedDict accepts all expected fields."""
    state: AgentState = {
        "messages": [HumanMessage(content="hello")],
        "session_id": "test-session",
        "user_profile": {"role": "consultant"},
        "research_tasks": [],
        "research_results": [],
        "strategy_drafts": [],
        "approval_status": APPROVAL_PENDING_PLAN,
        "company_url": "https://example.com",
        "company_profile": None,
        "competitors": [],
        "competitor_analyses": [],
        "strategic_insights": None,
    }
    assert state["session_id"] == "test-session"
    assert state["company_url"] == "https://example.com"
    assert state["company_profile"] is None
    assert state["strategic_insights"] is None
    assert len(state["messages"]) == 1


def test_agent_state_with_populated_data():
    """AgentState works with populated dicts and lists."""
    state: AgentState = {
        "messages": [],
        "session_id": "s-1",
        "user_profile": {"role": "analyst", "company": "Acme"},
        "research_tasks": [
            {"type": "company_profile", "target": "https://acme.com", "url": "https://acme.com", "focus_areas": ["pricing"]},
        ],
        "research_results": [
            {"competitor": "rival.com", "data": {"revenue": "10M"}, "source": "tavily", "timestamp": "2026-02-10T00:00:00Z"},
        ],
        "strategy_drafts": [
            {"feature_gaps": ["API"], "opportunities": ["EU market"]},
        ],
        "approval_status": APPROVAL_APPROVED_RESEARCH,
        "company_url": "https://acme.com",
        "company_profile": {"name": "Acme", "industry": "SaaS"},
        "competitors": [{"name": "Rival", "url": "https://rival.com"}],
        "competitor_analyses": [{"competitor": "Rival", "strengths": ["brand"]}],
        "strategic_insights": {"summary": "Good position"},
    }
    assert len(state["research_tasks"]) == 1
    assert state["research_results"][0]["competitor"] == "rival.com"
    assert state["company_profile"]["name"] == "Acme"


def test_approval_status_constants():
    """All approval status constants are distinct non-empty strings."""
    statuses = [
        APPROVAL_PENDING_PLAN,
        APPROVAL_APPROVED_PLAN,
        APPROVAL_PENDING_RESEARCH,
        APPROVAL_APPROVED_RESEARCH,
        APPROVAL_PENDING_STRATEGY,
        APPROVAL_APPROVED_STRATEGY,
        APPROVAL_REVISION_REQUESTED,
    ]
    assert len(statuses) == len(set(statuses)), "Duplicate approval status constants"
    for s in statuses:
        assert isinstance(s, str) and len(s) > 0


def test_agent_state_is_typed_dict():
    """AgentState is a TypedDict with the expected keys."""
    expected_keys = {
        "messages",
        "session_id",
        "user_profile",
        "research_tasks",
        "research_results",
        "strategy_drafts",
        "approval_status",
        "company_url",
        "company_profile",
        "competitors",
        "competitor_analyses",
        "strategic_insights",
    }
    assert set(AgentState.__annotations__.keys()) == expected_keys
