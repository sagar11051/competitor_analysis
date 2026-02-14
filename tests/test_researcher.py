"""Tests for the Research Orchestrator with mocked tools.

These tests verify the researcher node functions work correctly with
mocked Tavily and Crawl4AI calls — no real API calls are made.
"""

from unittest.mock import patch

from langchain_core.messages import HumanMessage

from src.agents.researcher import (
    _execute_company_profile,
    _execute_competitor_discovery,
    _execute_competitor_deep_dive,
    aggregate_results,
    build_researcher_subgraph,
    dispatch_research,
    research_agent,
)
from src.agents.state import APPROVAL_PENDING_RESEARCH, AgentState


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


# ── dispatch_research ────────────────────────────────────────────────


def test_dispatch_filters_invalid_tasks():
    state = _make_state(research_tasks=[
        {"type": "company_profile", "target": "https://example.com"},
        {"type": "", "target": ""},  # invalid — no type
        {"type": "competitor_discovery", "target": "example"},
    ])
    result = dispatch_research(state)
    assert len(result["research_tasks"]) == 2


def test_dispatch_keeps_all_valid_tasks():
    tasks = [
        {"type": "company_profile", "target": "https://a.com", "url": "https://a.com", "focus_areas": []},
        {"type": "competitor_discovery", "target": "acme", "url": None, "focus_areas": ["pricing"]},
    ]
    state = _make_state(research_tasks=tasks)
    result = dispatch_research(state)
    assert len(result["research_tasks"]) == 2


# ── _execute_company_profile ─────────────────────────────────────────


def test_company_profile_no_url():
    task = {"type": "company_profile", "target": "", "url": ""}
    result = _execute_company_profile(task)
    assert "error" in result["data"]


@patch("src.agents.researcher.asyncio.run")
def test_company_profile_success(mock_run):
    mock_run.return_value = [
        {"markdown": "# About Us\nWe build stuff.", "title": "About", "success": True},
        {"markdown": "# Pricing\n$10/mo", "title": "Pricing", "success": True},
    ]
    task = {"type": "company_profile", "target": "https://example.com", "url": "https://example.com"}
    result = _execute_company_profile(task)
    assert result["source"] == "crawl4ai"
    assert result["data"]["pages_scraped"] == 2
    assert result["data"]["total_chars"] > 0


# ── _execute_competitor_discovery ────────────────────────────────────


@patch("src.agents.researcher._tavily")
def test_competitor_discovery_not_configured(mock_tavily):
    mock_tavily.is_configured.return_value = False
    task = {"type": "competitor_discovery", "target": "acme"}
    result = _execute_competitor_discovery(task)
    assert "error" in result["data"]


@patch("src.agents.researcher._tavily")
def test_competitor_discovery_success(mock_tavily):
    mock_tavily.is_configured.return_value = True
    mock_tavily.search.return_value = [
        {"title": "Rival Corp", "url": "https://rival.com", "content": "A competitor", "score": 0.9},
    ]
    task = {"type": "competitor_discovery", "target": "acme", "focus_areas": ["pricing"]}
    result = _execute_competitor_discovery(task)
    assert result["source"] == "tavily"
    assert result["data"]["result_count"] == 1


# ── _execute_competitor_deep_dive ────────────────────────────────────


def test_deep_dive_no_url():
    task = {"type": "competitor_deep_dive", "target": "", "url": ""}
    result = _execute_competitor_deep_dive(task)
    assert "error" in result["data"]


@patch("src.agents.researcher.asyncio.run")
def test_deep_dive_with_focus_areas(mock_run):
    mock_run.return_value = [
        {"markdown": "# Pricing\n$20/mo", "title": "Pricing", "success": True},
    ]
    task = {
        "type": "competitor_deep_dive",
        "target": "https://rival.com",
        "url": "https://rival.com",
        "focus_areas": ["pricing", "features"],
    }
    result = _execute_competitor_deep_dive(task)
    assert result["source"] == "crawl4ai"
    assert result["data"]["pages_scraped"] == 1


# ── research_agent ───────────────────────────────────────────────────


@patch("src.agents.researcher._tavily")
@patch("src.agents.researcher.asyncio.run")
def test_research_agent_executes_all_task_types(mock_run, mock_tavily):
    mock_run.return_value = [
        {"markdown": "content", "title": "Page", "success": True},
    ]
    mock_tavily.is_configured.return_value = True
    mock_tavily.search.return_value = [{"title": "R", "url": "https://r.com", "content": "c", "score": 0.5}]

    state = _make_state(research_tasks=[
        {"type": "company_profile", "target": "https://example.com", "url": "https://example.com"},
        {"type": "competitor_discovery", "target": "example", "focus_areas": []},
        {"type": "competitor_deep_dive", "target": "https://rival.com", "url": "https://rival.com", "focus_areas": []},
    ])
    result = research_agent(state)
    assert len(result["research_results"]) == 3


def test_research_agent_handles_unknown_type():
    state = _make_state(research_tasks=[
        {"type": "unknown_type", "target": "test"},
    ])
    result = research_agent(state)
    assert len(result["research_results"]) == 1
    assert "error" in result["research_results"][0]["data"]


# ── aggregate_results ────────────────────────────────────────────────


def test_aggregate_deduplicates():
    state = _make_state(research_results=[
        {"competitor": "a.com", "data": {}, "source": "tavily", "timestamp": "t1"},
        {"competitor": "a.com", "data": {}, "source": "tavily", "timestamp": "t2"},  # duplicate
        {"competitor": "b.com", "data": {}, "source": "crawl4ai", "timestamp": "t3"},
    ])
    result = aggregate_results(state)
    assert len(result["research_results"]) == 2
    assert result["approval_status"] == APPROVAL_PENDING_RESEARCH


def test_aggregate_counts_errors():
    state = _make_state(research_results=[
        {"competitor": "a.com", "data": {"pages_scraped": 3}, "source": "crawl4ai", "timestamp": "t1"},
        {"competitor": "b.com", "data": {"error": "timeout"}, "source": "crawl4ai", "timestamp": "t2"},
    ])
    result = aggregate_results(state)
    msg = result["messages"][0].content
    assert "1 successful" in msg
    assert "1 failed" in msg


# ── Subgraph ─────────────────────────────────────────────────────────


@patch("src.agents.researcher._tavily")
@patch("src.agents.researcher.asyncio.run")
def test_researcher_subgraph_end_to_end(mock_run, mock_tavily):
    mock_run.return_value = [
        {"markdown": "content", "title": "Page", "success": True},
    ]
    mock_tavily.is_configured.return_value = True
    mock_tavily.search.return_value = []

    graph = build_researcher_subgraph()
    compiled = graph.compile()
    state = _make_state(research_tasks=[
        {"type": "company_profile", "target": "https://example.com", "url": "https://example.com"},
    ])
    result = compiled.invoke(state)
    assert result["approval_status"] == APPROVAL_PENDING_RESEARCH
    assert len(result["research_results"]) >= 1
