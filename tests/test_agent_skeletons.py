"""Tests for agent subgraph skeletons — verify they compile and run end-to-end."""

from langchain_core.messages import HumanMessage

from src.agents.planner import (
    analyze_query,
    build_planner_subgraph,
    create_research_tasks,
)
from src.agents.researcher import (
    aggregate_results,
    build_researcher_subgraph,
    dispatch_research,
    research_agent,
)
from src.agents.state import (
    APPROVAL_PENDING_PLAN,
    APPROVAL_PENDING_RESEARCH,
    APPROVAL_PENDING_STRATEGY,
    AgentState,
)
from src.agents.strategist import (
    analyze_findings,
    build_strategist_subgraph,
    generate_strategy,
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


# ── Planner node tests ──────────────────────────────────────────────


def test_analyze_query_returns_company_url():
    state = _make_state()
    result = analyze_query(state)
    assert result["company_url"] == "https://example.com"
    assert len(result["messages"]) == 1


def test_create_research_tasks_sets_pending_approval():
    state = _make_state()
    result = create_research_tasks(state)
    assert result["approval_status"] == APPROVAL_PENDING_PLAN
    assert len(result["research_tasks"]) >= 1
    for task in result["research_tasks"]:
        assert "type" in task
        assert "focus_areas" in task


def test_planner_subgraph_compiles():
    graph = build_planner_subgraph()
    compiled = graph.compile()
    assert compiled is not None


def test_planner_subgraph_runs():
    graph = build_planner_subgraph()
    compiled = graph.compile()
    state = _make_state()
    result = compiled.invoke(state)
    assert result["approval_status"] == APPROVAL_PENDING_PLAN
    assert len(result["research_tasks"]) >= 1


# ── Researcher node tests ───────────────────────────────────────────


def test_dispatch_research_returns_message():
    state = _make_state(research_tasks=[
        {"type": "company_profile", "target": "https://example.com", "url": "https://example.com", "focus_areas": ["overview"]},
    ])
    result = dispatch_research(state)
    assert len(result["messages"]) == 1


def test_research_agent_creates_results():
    state = _make_state(research_tasks=[
        {"type": "company_profile", "target": "https://example.com", "url": "https://example.com", "focus_areas": ["overview"]},
        {"type": "competitor_discovery", "target": "https://example.com", "url": None, "focus_areas": ["competitors"]},
    ])
    result = research_agent(state)
    assert len(result["research_results"]) == 2
    for r in result["research_results"]:
        assert "competitor" in r
        assert "timestamp" in r


def test_aggregate_results_sets_pending_approval():
    state = _make_state(research_results=[
        {"competitor": "rival.com", "data": {}, "source": "tavily", "timestamp": "2026-01-01T00:00:00Z"},
    ])
    result = aggregate_results(state)
    assert result["approval_status"] == APPROVAL_PENDING_RESEARCH


def test_researcher_subgraph_compiles():
    graph = build_researcher_subgraph()
    compiled = graph.compile()
    assert compiled is not None


def test_researcher_subgraph_runs():
    graph = build_researcher_subgraph()
    compiled = graph.compile()
    state = _make_state(research_tasks=[
        {"type": "company_profile", "target": "https://example.com", "url": "https://example.com", "focus_areas": ["overview"]},
    ])
    result = compiled.invoke(state)
    assert result["approval_status"] == APPROVAL_PENDING_RESEARCH
    assert len(result["research_results"]) >= 1


# ── Strategist node tests ───────────────────────────────────────────


def test_analyze_findings_creates_analyses():
    state = _make_state(research_results=[
        {"competitor": "rival.com", "data": {}, "source": "tavily", "timestamp": "2026-01-01T00:00:00Z"},
    ])
    result = analyze_findings(state)
    assert len(result["competitor_analyses"]) == 1
    assert result["competitor_analyses"][0]["competitor"] == "rival.com"


def test_generate_strategy_sets_pending_approval():
    state = _make_state(competitor_analyses=[
        {"competitor": "rival.com", "strengths": [], "weaknesses": [], "market_position": "unknown"},
    ])
    result = generate_strategy(state)
    assert result["approval_status"] == APPROVAL_PENDING_STRATEGY
    assert len(result["strategy_drafts"]) == 1
    draft = result["strategy_drafts"][0]
    assert "feature_gaps" in draft
    assert "opportunities" in draft
    assert "positioning_suggestions" in draft
    assert "fundraising_intel" in draft
    assert result["strategic_insights"] is not None


def test_strategist_subgraph_compiles():
    graph = build_strategist_subgraph()
    compiled = graph.compile()
    assert compiled is not None


def test_strategist_subgraph_runs():
    graph = build_strategist_subgraph()
    compiled = graph.compile()
    state = _make_state(research_results=[
        {"competitor": "rival.com", "data": {}, "source": "tavily", "timestamp": "2026-01-01T00:00:00Z"},
    ])
    result = compiled.invoke(state)
    assert result["approval_status"] == APPROVAL_PENDING_STRATEGY
    assert len(result["strategy_drafts"]) >= 1
    assert result["strategic_insights"] is not None
