"""End-to-end tests for agent workflows with LLM integration.

Tests the full flow of Planner and Strategist agents with mocked LLM calls.
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import HumanMessage


class TestPlannerE2E:
    """End-to-end tests for Planner agent."""

    def test_analyze_query_with_llm(self):
        """Test analyze_query extracts intent using LLM."""
        from src.agents.planner import analyze_query
        from src.agents.state import AgentState

        mock_intent = {
            "company_url": "https://stripe.com",
            "company_name": "Stripe",
            "focus_areas": ["payments", "developer_tools", "pricing"],
            "constraints": [],
        }

        with patch("src.agents.planner.is_llm_configured", return_value=True):
            with patch("src.agents.planner.generate_json", return_value=mock_intent):
                state: AgentState = {
                    "messages": [HumanMessage(content="Analyze Stripe's competitors")],
                    "company_url": "https://stripe.com",
                    "user_profile": {},
                    "session_id": "test-session",
                    "research_tasks": [],
                    "research_results": [],
                    "strategy_drafts": [],
                    "approval_status": "",
                    "company_profile": None,
                    "competitors": [],
                    "competitor_analyses": [],
                    "strategic_insights": None,
                }

                result = analyze_query(state)

                assert result["company_url"] == "https://stripe.com"
                assert "extracted_intent" in result["user_profile"]
                assert result["user_profile"]["extracted_intent"]["company_name"] == "Stripe"

    def test_analyze_query_fallback_without_llm(self):
        """Test analyze_query uses fallback when LLM not configured."""
        from src.agents.planner import analyze_query
        from src.agents.state import AgentState

        with patch("src.agents.planner.is_llm_configured", return_value=False):
            state: AgentState = {
                "messages": [],
                "company_url": "https://example.com",
                "user_profile": {},
                "session_id": "test-session",
                "research_tasks": [],
                "research_results": [],
                "strategy_drafts": [],
                "approval_status": "",
                "company_profile": None,
                "competitors": [],
                "competitor_analyses": [],
                "strategic_insights": None,
            }

            result = analyze_query(state)

            assert result["company_url"] == "https://example.com"
            assert "extracted_intent" in result["user_profile"]
            # Fallback should infer company name from URL
            assert result["user_profile"]["extracted_intent"]["company_name"] == "Example"

    def test_create_research_tasks_with_llm(self):
        """Test create_research_tasks generates tasks using LLM."""
        from src.agents.planner import create_research_tasks
        from src.agents.state import APPROVAL_PENDING_PLAN, AgentState

        mock_tasks = {
            "tasks": [
                {"type": "company_profile", "target": "Stripe", "url": "https://stripe.com", "focus_areas": ["payments"]},
                {"type": "competitor_discovery", "target": "Stripe", "url": None, "focus_areas": ["direct_competitors"]},
                {"type": "competitor_deep_dive", "target": "Square", "url": "https://squareup.com", "focus_areas": ["pricing"]},
            ]
        }

        with patch("src.agents.planner.is_llm_configured", return_value=True):
            with patch("src.agents.planner.generate_json", return_value=mock_tasks):
                state: AgentState = {
                    "messages": [],
                    "company_url": "https://stripe.com",
                    "user_profile": {
                        "extracted_intent": {
                            "company_name": "Stripe",
                            "focus_areas": ["payments", "pricing"],
                            "constraints": [],
                        }
                    },
                    "session_id": "test-session",
                    "research_tasks": [],
                    "research_results": [],
                    "strategy_drafts": [],
                    "approval_status": "",
                    "company_profile": None,
                    "competitors": [],
                    "competitor_analyses": [],
                    "strategic_insights": None,
                }

                result = create_research_tasks(state)

                assert len(result["research_tasks"]) == 3
                assert result["approval_status"] == APPROVAL_PENDING_PLAN
                assert result["research_tasks"][0]["type"] == "company_profile"
                assert result["research_tasks"][2]["type"] == "competitor_deep_dive"

    def test_create_research_tasks_validates_task_types(self):
        """Test create_research_tasks filters invalid task types."""
        from src.agents.planner import create_research_tasks
        from src.agents.state import AgentState

        mock_tasks = {
            "tasks": [
                {"type": "company_profile", "target": "Stripe", "url": "https://stripe.com"},
                {"type": "invalid_type", "target": "Bad", "url": None},  # Should be filtered
                {"type": "competitor_discovery", "target": "Stripe", "url": None},
            ]
        }

        with patch("src.agents.planner.is_llm_configured", return_value=True):
            with patch("src.agents.planner.generate_json", return_value=mock_tasks):
                state: AgentState = {
                    "messages": [],
                    "company_url": "https://stripe.com",
                    "user_profile": {"extracted_intent": {"company_name": "Stripe", "focus_areas": [], "constraints": []}},
                    "session_id": "",
                    "research_tasks": [],
                    "research_results": [],
                    "strategy_drafts": [],
                    "approval_status": "",
                    "company_profile": None,
                    "competitors": [],
                    "competitor_analyses": [],
                    "strategic_insights": None,
                }

                result = create_research_tasks(state)

                # Invalid task type should be filtered out
                assert len(result["research_tasks"]) == 2
                task_types = [t["type"] for t in result["research_tasks"]]
                assert "invalid_type" not in task_types


class TestStrategistE2E:
    """End-to-end tests for Strategist agent."""

    def test_analyze_findings_with_llm(self):
        """Test analyze_findings synthesizes research using LLM."""
        from src.agents.strategist import analyze_findings
        from src.agents.state import AgentState

        mock_analyses = {
            "analyses": [
                {
                    "competitor": "Square",
                    "strengths": ["Strong POS integration", "Good SMB focus"],
                    "weaknesses": ["Limited enterprise features"],
                    "market_position": "SMB market leader",
                    "threat_level": "high",
                },
                {
                    "competitor": "Adyen",
                    "strengths": ["Global coverage", "Enterprise focus"],
                    "weaknesses": ["Complex integration"],
                    "market_position": "Enterprise payments",
                    "threat_level": "medium",
                },
            ]
        }

        with patch("src.agents.strategist.is_llm_configured", return_value=True):
            with patch("src.agents.strategist.generate_json", return_value=mock_analyses):
                state: AgentState = {
                    "messages": [],
                    "company_url": "https://stripe.com",
                    "user_profile": {},
                    "session_id": "test-session",
                    "research_tasks": [],
                    "research_results": [
                        {"competitor": "Square", "content": "Square is a payments company..."},
                        {"competitor": "Adyen", "content": "Adyen provides enterprise payments..."},
                    ],
                    "strategy_drafts": [],
                    "approval_status": "",
                    "company_profile": {"name": "Stripe"},
                    "competitors": [],
                    "competitor_analyses": [],
                    "strategic_insights": None,
                }

                result = analyze_findings(state)

                assert len(result["competitor_analyses"]) == 2
                assert result["competitor_analyses"][0]["competitor"] == "Square"
                assert result["competitor_analyses"][0]["threat_level"] == "high"
                assert result["competitor_analyses"][1]["competitor"] == "Adyen"

    def test_generate_strategy_with_llm(self):
        """Test generate_strategy produces recommendations using LLM."""
        from src.agents.strategist import generate_strategy
        from src.agents.state import APPROVAL_PENDING_STRATEGY, AgentState

        mock_strategy = {
            "feature_gaps": ["In-person POS system", "Hardware offerings"],
            "opportunities": ["SMB market expansion", "Vertical-specific solutions"],
            "positioning_suggestions": ["Focus on developer experience", "Emphasize reliability"],
            "fundraising_intel": ["Square raised $1B", "Adyen IPO successful"],
            "summary": "Stripe should focus on expanding developer tools while entering the SMB POS market to compete with Square.",
        }

        with patch("src.agents.strategist.is_llm_configured", return_value=True):
            with patch("src.agents.strategist.generate_json", return_value=mock_strategy):
                state: AgentState = {
                    "messages": [],
                    "company_url": "https://stripe.com",
                    "user_profile": {},
                    "session_id": "test-session",
                    "research_tasks": [],
                    "research_results": [],
                    "strategy_drafts": [],
                    "approval_status": "",
                    "company_profile": {"name": "Stripe", "description": "Payments infrastructure"},
                    "competitors": [],
                    "competitor_analyses": [
                        {"competitor": "Square", "strengths": ["POS"], "weaknesses": [], "market_position": "SMB", "threat_level": "high"},
                    ],
                    "strategic_insights": None,
                }

                result = generate_strategy(state)

                assert result["approval_status"] == APPROVAL_PENDING_STRATEGY
                assert len(result["strategy_drafts"]) == 1
                assert len(result["strategy_drafts"][0]["feature_gaps"]) == 2
                assert "strategic_insights" in result
                assert result["strategic_insights"]["company_name"] == "Stripe"

    def test_generate_strategy_fallback_without_llm(self):
        """Test generate_strategy uses placeholder when LLM not configured."""
        from src.agents.strategist import generate_strategy
        from src.agents.state import APPROVAL_PENDING_STRATEGY, AgentState

        with patch("src.agents.strategist.is_llm_configured", return_value=False):
            state: AgentState = {
                "messages": [],
                "company_url": "https://example.com",
                "user_profile": {},
                "session_id": "test-session",
                "research_tasks": [],
                "research_results": [],
                "strategy_drafts": [],
                "approval_status": "",
                "company_profile": None,
                "competitors": [],
                "competitor_analyses": [],
                "strategic_insights": None,
            }

            result = generate_strategy(state)

            assert result["approval_status"] == APPROVAL_PENDING_STRATEGY
            assert len(result["strategy_drafts"]) == 1
            # Placeholder should have empty lists
            assert result["strategy_drafts"][0]["feature_gaps"] == []
            assert result["strategic_insights"]["llm_generated"] is False


class TestPlannerSubgraph:
    """Tests for the full Planner subgraph execution."""

    def test_planner_subgraph_compiles(self):
        """Test that the Planner subgraph compiles successfully."""
        from src.agents.planner import build_planner_subgraph

        graph = build_planner_subgraph()
        compiled = graph.compile()

        assert compiled is not None

    def test_planner_subgraph_execution(self):
        """Test full Planner subgraph execution with mocked LLM."""
        from src.agents.planner import build_planner_subgraph
        from src.agents.state import APPROVAL_PENDING_PLAN

        mock_intent = {
            "company_url": "https://stripe.com",
            "company_name": "Stripe",
            "focus_areas": ["payments"],
            "constraints": [],
        }
        mock_tasks = {
            "tasks": [
                {"type": "company_profile", "target": "Stripe", "url": "https://stripe.com", "focus_areas": []},
            ]
        }

        with patch("src.agents.planner.is_llm_configured", return_value=True):
            with patch("src.agents.planner.generate_json", side_effect=[mock_intent, mock_tasks]):
                graph = build_planner_subgraph()
                compiled = graph.compile()

                initial_state = {
                    "messages": [HumanMessage(content="Analyze Stripe")],
                    "company_url": "https://stripe.com",
                    "user_profile": {},
                    "session_id": "test",
                    "research_tasks": [],
                    "research_results": [],
                    "strategy_drafts": [],
                    "approval_status": "",
                    "company_profile": None,
                    "competitors": [],
                    "competitor_analyses": [],
                    "strategic_insights": None,
                }

                result = compiled.invoke(initial_state)

                assert result["approval_status"] == APPROVAL_PENDING_PLAN
                assert len(result["research_tasks"]) == 1


class TestStrategistSubgraph:
    """Tests for the full Strategist subgraph execution."""

    def test_strategist_subgraph_compiles(self):
        """Test that the Strategist subgraph compiles successfully."""
        from src.agents.strategist import build_strategist_subgraph

        graph = build_strategist_subgraph()
        compiled = graph.compile()

        assert compiled is not None

    def test_strategist_subgraph_execution(self):
        """Test full Strategist subgraph execution with mocked LLM."""
        from src.agents.strategist import build_strategist_subgraph
        from src.agents.state import APPROVAL_PENDING_STRATEGY

        mock_analyses = {
            "analyses": [
                {"competitor": "Competitor A", "strengths": ["Good"], "weaknesses": ["Bad"], "market_position": "Leader", "threat_level": "high"},
            ]
        }
        mock_strategy = {
            "feature_gaps": ["Feature X"],
            "opportunities": ["Market Y"],
            "positioning_suggestions": ["Position Z"],
            "fundraising_intel": [],
            "summary": "Strategic summary here.",
        }

        with patch("src.agents.strategist.is_llm_configured", return_value=True):
            with patch("src.agents.strategist.generate_json", side_effect=[mock_analyses, mock_strategy]):
                graph = build_strategist_subgraph()
                compiled = graph.compile()

                initial_state = {
                    "messages": [],
                    "company_url": "https://example.com",
                    "user_profile": {},
                    "session_id": "test",
                    "research_tasks": [],
                    "research_results": [{"competitor": "Competitor A", "content": "Some content"}],
                    "strategy_drafts": [],
                    "approval_status": "",
                    "company_profile": {"name": "Example Co"},
                    "competitors": [],
                    "competitor_analyses": [],
                    "strategic_insights": None,
                }

                result = compiled.invoke(initial_state)

                assert result["approval_status"] == APPROVAL_PENDING_STRATEGY
                assert len(result["competitor_analyses"]) == 1
                assert result["strategic_insights"]["summary"] == "Strategic summary here."
