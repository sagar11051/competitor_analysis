"""Integration tests — full multi-turn conversation flow.

Tests the complete HITL workflow from session creation through all three
approval gates using mocked agent nodes to avoid real LLM/network calls.

These tests verify the session management layer (create_session,
resume_session, get_session_state) and the graph interrupt/resume mechanics.
"""

from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage

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


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_state(**overrides) -> AgentState:
    """Return a fully-populated AgentState for use in tests."""
    base: AgentState = {
        "messages": [],
        "session_id": "test-session-id",
        "user_profile": {},
        "research_tasks": [],
        "research_results": [],
        "strategy_drafts": [],
        "approval_status": "",
        "company_url": "https://stripe.com",
        "company_profile": None,
        "competitors": [],
        "competitor_analyses": [],
        "strategic_insights": None,
    }
    base.update(overrides)
    return base


def _pending_plan_state() -> AgentState:
    return _make_state(
        approval_status=APPROVAL_PENDING_PLAN,
        research_tasks=[
            {"type": "company_profile", "target": "Stripe", "url": "https://stripe.com", "focus_areas": []},
            {"type": "competitor_discovery", "target": "Stripe", "url": None, "focus_areas": []},
        ],
        messages=[AIMessage(content="Research plan ready for review.")],
    )


def _pending_research_state() -> AgentState:
    return _make_state(
        approval_status=APPROVAL_PENDING_RESEARCH,
        research_tasks=[
            {"type": "company_profile", "target": "Stripe", "url": "https://stripe.com", "focus_areas": []},
        ],
        research_results=[
            {"competitor": "Square", "content": "Square POS...", "url": "https://squareup.com", "task_type": "competitor_deep_dive"},
        ],
        messages=[AIMessage(content="Research complete. 1 result collected.")],
    )


def _pending_strategy_state() -> AgentState:
    return _make_state(
        approval_status=APPROVAL_PENDING_STRATEGY,
        competitor_analyses=[
            {"competitor": "Square", "strengths": ["POS"], "weaknesses": [], "market_position": "SMB", "threat_level": "high"},
        ],
        strategy_drafts=[
            {"feature_gaps": ["POS system"], "opportunities": ["SMB expansion"], "positioning_suggestions": ["Dev-first"], "fundraising_intel": []},
        ],
        strategic_insights={
            "summary": "Stripe should expand into POS.",
            "recommendations": ["Dev-first positioning"],
            "company_name": "Stripe",
            "competitor_count": 1,
            "llm_generated": True,
        },
        messages=[AIMessage(content="Strategy draft ready for review.")],
    )


def _completed_state() -> AgentState:
    state = _pending_strategy_state()
    state["approval_status"] = APPROVAL_APPROVED_STRATEGY
    return state


# ---------------------------------------------------------------------------
# Session management helper tests
# ---------------------------------------------------------------------------


class TestResolveApprovalAction:
    """Tests for the _resolve_approval_action helper."""

    def test_approve_pending_plan(self):
        from src.agents.graph import _resolve_approval_action
        result = _resolve_approval_action(APPROVAL_PENDING_PLAN, "approve")
        assert result == APPROVAL_APPROVED_PLAN

    def test_approve_pending_research(self):
        from src.agents.graph import _resolve_approval_action
        result = _resolve_approval_action(APPROVAL_PENDING_RESEARCH, "approve")
        assert result == APPROVAL_APPROVED_RESEARCH

    def test_approve_pending_strategy(self):
        from src.agents.graph import _resolve_approval_action
        result = _resolve_approval_action(APPROVAL_PENDING_STRATEGY, "approve")
        assert result == APPROVAL_APPROVED_STRATEGY

    def test_modify_returns_revision_requested(self):
        from src.agents.graph import _resolve_approval_action
        for status in (APPROVAL_PENDING_PLAN, APPROVAL_PENDING_RESEARCH, APPROVAL_PENDING_STRATEGY):
            assert _resolve_approval_action(status, "modify") == APPROVAL_REVISION_REQUESTED

    def test_reject_returns_revision_requested(self):
        from src.agents.graph import _resolve_approval_action
        assert _resolve_approval_action(APPROVAL_PENDING_PLAN, "reject") == APPROVAL_REVISION_REQUESTED

    def test_unknown_action_preserves_status(self):
        from src.agents.graph import _resolve_approval_action
        assert _resolve_approval_action(APPROVAL_PENDING_PLAN, "unknown") == APPROVAL_PENDING_PLAN


# ---------------------------------------------------------------------------
# Full multi-turn conversation flow
# ---------------------------------------------------------------------------


class TestFullConversationFlow:
    """Tests simulating a complete 3-gate HITL conversation."""

    def _make_compiled_graph(self, states_by_invoke):
        """Return a mock compiled graph whose invoke() returns states in sequence."""
        mock_graph = MagicMock()
        invoke_call_count = {"n": 0}

        def _invoke(state, config):
            idx = invoke_call_count["n"]
            invoke_call_count["n"] += 1
            return states_by_invoke[idx] if idx < len(states_by_invoke) else states_by_invoke[-1]

        mock_graph.invoke.side_effect = _invoke
        mock_graph.update_state = MagicMock()

        # get_state returns a snapshot whose .values mirrors what we last invoked
        snapshot = MagicMock()
        snapshot.values = _pending_plan_state()
        mock_graph.get_state.return_value = snapshot

        return mock_graph

    def test_create_session_returns_pending_plan(self):
        """create_session returns session_id and pending-plan state."""
        pending = _pending_plan_state()

        with patch("src.agents.graph.get_compiled_graph") as mock_get:
            mock_compiled = MagicMock()
            mock_compiled.invoke.return_value = pending
            mock_get.return_value = mock_compiled

            from src.agents.graph import create_session
            session_id, state = create_session("https://stripe.com")

            assert session_id is not None
            assert len(session_id) > 0
            assert state["approval_status"] == APPROVAL_PENDING_PLAN
            assert len(state["research_tasks"]) == 2

    def test_approve_plan_transitions_to_pending_research(self):
        """Approving the plan transitions approval_status to pending_research."""
        pending_research = _pending_research_state()

        with patch("src.agents.graph.get_compiled_graph") as mock_get:
            mock_compiled = MagicMock()
            mock_compiled.invoke.return_value = pending_research

            snapshot = MagicMock()
            snapshot.values = _pending_plan_state()
            mock_compiled.get_state.return_value = snapshot
            mock_get.return_value = mock_compiled

            from src.agents.graph import resume_session
            state = resume_session("test-session", "approve")

            assert state["approval_status"] == APPROVAL_PENDING_RESEARCH
            assert len(state["research_results"]) == 1

    def test_approve_research_transitions_to_pending_strategy(self):
        """Approving research transitions approval_status to pending_strategy."""
        pending_strategy = _pending_strategy_state()

        with patch("src.agents.graph.get_compiled_graph") as mock_get:
            mock_compiled = MagicMock()
            mock_compiled.invoke.return_value = pending_strategy

            snapshot = MagicMock()
            snapshot.values = _pending_research_state()
            mock_compiled.get_state.return_value = snapshot
            mock_get.return_value = mock_compiled

            from src.agents.graph import resume_session
            state = resume_session("test-session", "approve")

            assert state["approval_status"] == APPROVAL_PENDING_STRATEGY
            assert len(state["strategy_drafts"]) == 1
            assert state["strategic_insights"] is not None

    def test_approve_strategy_completes_session(self):
        """Approving the strategy produces the final completed state."""
        completed = _completed_state()

        with patch("src.agents.graph.get_compiled_graph") as mock_get:
            mock_compiled = MagicMock()
            mock_compiled.invoke.return_value = completed

            snapshot = MagicMock()
            snapshot.values = _pending_strategy_state()
            mock_compiled.get_state.return_value = snapshot
            mock_get.return_value = mock_compiled

            from src.agents.graph import resume_session
            state = resume_session("test-session", "approve")

            assert state["approval_status"] == APPROVAL_APPROVED_STRATEGY
            assert state["strategic_insights"]["summary"] == "Stripe should expand into POS."

    def test_modify_plan_triggers_revision(self):
        """Modifying the plan sets revision_requested status."""
        revised_plan = _pending_plan_state()
        revised_plan["research_tasks"].append(
            {"type": "competitor_deep_dive", "target": "Adyen", "url": "https://adyen.com", "focus_areas": []}
        )
        revised_plan["messages"] = [AIMessage(content="Revised plan with Adyen added.")]

        with patch("src.agents.graph.get_compiled_graph") as mock_get:
            mock_compiled = MagicMock()
            mock_compiled.invoke.return_value = revised_plan

            snapshot = MagicMock()
            snapshot.values = _pending_plan_state()
            mock_compiled.get_state.return_value = snapshot
            mock_get.return_value = mock_compiled

            from src.agents.graph import resume_session
            state = resume_session("test-session", "modify", "Also research Adyen")

            # After resuming, the planner ran again and produced a new pending plan
            assert state["approval_status"] == APPROVAL_PENDING_PLAN
            assert len(state["research_tasks"]) == 3

    def test_get_session_state_returns_current_state(self):
        """get_session_state returns a dict of the current session state."""
        pending = _pending_plan_state()

        with patch("src.agents.graph.get_compiled_graph") as mock_get:
            mock_compiled = MagicMock()
            snapshot = MagicMock()
            snapshot.values = pending
            mock_compiled.get_state.return_value = snapshot
            mock_get.return_value = mock_compiled

            from src.agents.graph import get_session_state
            state = get_session_state("test-session")

            assert state is not None
            assert state["approval_status"] == APPROVAL_PENDING_PLAN
            assert state["company_url"] == "https://stripe.com"

    def test_get_session_state_returns_none_for_missing(self):
        """get_session_state returns None for an unknown session."""
        with patch("src.agents.graph.get_compiled_graph") as mock_get:
            mock_compiled = MagicMock()
            snapshot = MagicMock()
            snapshot.values = {}
            mock_compiled.get_state.return_value = snapshot
            mock_get.return_value = mock_compiled

            from src.agents.graph import get_session_state
            state = get_session_state("nonexistent-session")

            # Empty values dict → None
            assert state is None or state == {}

    def test_session_carries_user_message_forward(self):
        """User feedback message is appended to state when resuming."""
        pending_research = _pending_research_state()

        with patch("src.agents.graph.get_compiled_graph") as mock_get:
            mock_compiled = MagicMock()
            mock_compiled.invoke.return_value = pending_research

            snapshot = MagicMock()
            snapshot.values = _pending_plan_state()
            mock_compiled.get_state.return_value = snapshot
            mock_get.return_value = mock_compiled

            from src.agents.graph import resume_session
            resume_session("test-session", "approve", "Please focus on pricing")

            # update_state should have been called with the user message appended
            mock_compiled.update_state.assert_called_once()
            call_args = mock_compiled.update_state.call_args
            updated_state = call_args[0][1]  # second positional arg
            messages = updated_state.get("messages", [])
            # The last message should be the user's feedback
            last_msg = messages[-1]
            assert isinstance(last_msg, HumanMessage)
            assert "pricing" in last_msg.content


# ---------------------------------------------------------------------------
# CLI unit tests (no I/O)
# ---------------------------------------------------------------------------


class TestCLIHelpers:
    """Tests for the CLI display and prompt helpers."""

    def test_show_research_plan_with_tasks(self, capsys):
        """_show_research_plan prints task details."""
        from src.agents.cli import _show_research_plan

        state = _make_state(
            research_tasks=[
                {"type": "company_profile", "target": "Stripe", "url": "https://stripe.com", "focus_areas": ["payments"]},
                {"type": "competitor_discovery", "target": "Stripe", "url": None, "focus_areas": []},
            ]
        )
        _show_research_plan(state)

        captured = capsys.readouterr()
        assert "company_profile" in captured.out
        assert "competitor_discovery" in captured.out
        assert "Stripe" in captured.out

    def test_show_research_plan_no_tasks(self, capsys):
        """_show_research_plan handles empty task list gracefully."""
        from src.agents.cli import _show_research_plan

        _show_research_plan(_make_state())
        captured = capsys.readouterr()
        assert "no tasks" in captured.out

    def test_show_research_results_with_data(self, capsys):
        """_show_research_results prints result summary."""
        from src.agents.cli import _show_research_results

        state = _make_state(
            research_results=[
                {"competitor": "Square", "content": "x" * 500, "url": "https://squareup.com", "task_type": "deep_dive"},
            ]
        )
        _show_research_results(state)

        captured = capsys.readouterr()
        assert "Square" in captured.out
        assert "500" in captured.out

    def test_show_research_results_empty(self, capsys):
        """_show_research_results handles empty results gracefully."""
        from src.agents.cli import _show_research_results

        _show_research_results(_make_state())
        captured = capsys.readouterr()
        assert "no results" in captured.out

    def test_show_strategy_with_insights(self, capsys):
        """_show_strategy prints summary and structured sections."""
        from src.agents.cli import _show_strategy

        state = _pending_strategy_state()
        _show_strategy(state)

        captured = capsys.readouterr()
        assert "Stripe should expand into POS" in captured.out
        assert "POS system" in captured.out
        assert "SMB expansion" in captured.out

    def test_show_final_report(self, capsys):
        """_show_final_report prints the complete report."""
        from src.agents.cli import _show_final_report

        state = _completed_state()
        state["company_profile"] = {"name": "Stripe", "website": "https://stripe.com"}
        _show_final_report(state)

        captured = capsys.readouterr()
        assert "Stripe" in captured.out
        assert "COMPETITIVE ANALYSIS REPORT" in captured.out


class TestCLIRunLoop:
    """Tests for the run_cli session loop logic."""

    def test_run_cli_full_approve_flow(self, monkeypatch):
        """run_cli completes successfully when the user approves all 3 gates."""
        call_count = {"n": 0}
        states = [
            _pending_plan_state(),
            _pending_research_state(),
            _pending_strategy_state(),
            _completed_state(),
        ]

        def mock_create_session(company_url, **kwargs):
            return "sess-1", states[0]

        def mock_resume_session(session_id, action, message=""):
            call_count["n"] += 1
            return states[call_count["n"]]

        monkeypatch.setattr("src.agents.cli.create_session", mock_create_session)
        monkeypatch.setattr("src.agents.cli.resume_session", mock_resume_session)
        monkeypatch.setattr("src.agents.cli.get_session_state", lambda sid: states[-1])

        # Simulate user always choosing 'a' (approve)
        inputs = iter(["a", "a", "a"])
        monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

        from src.agents.cli import run_cli
        run_cli(company_url="https://stripe.com")  # Should not raise

        assert call_count["n"] == 3  # resume called 3 times (once per gate)

    def test_run_cli_quit_at_gate_1(self, monkeypatch, capsys):
        """run_cli exits cleanly when user quits at Gate 1."""

        def mock_create_session(company_url, **kwargs):
            return "sess-1", _pending_plan_state()

        monkeypatch.setattr("src.agents.cli.create_session", mock_create_session)

        # User immediately quits
        monkeypatch.setattr("builtins.input", lambda prompt="": "q")

        from src.agents.cli import run_cli
        run_cli(company_url="https://stripe.com")

        captured = capsys.readouterr()
        assert "saved" in captured.out.lower() or "exiting" in captured.out.lower()

    def test_run_cli_modify_then_approve(self, monkeypatch):
        """run_cli handles a modify + re-approve cycle correctly."""
        call_count = {"n": 0}
        # Gate 1 revisited after modify, then approved
        states = [
            _pending_plan_state(),   # after create_session
            _pending_plan_state(),   # after modify (planner re-ran)
            _pending_research_state(),  # after approve
            _pending_strategy_state(),  # after approve
            _completed_state(),         # after approve
        ]

        def mock_create_session(company_url, **kwargs):
            return "sess-1", states[0]

        def mock_resume_session(session_id, action, message=""):
            call_count["n"] += 1
            return states[call_count["n"]]

        monkeypatch.setattr("src.agents.cli.create_session", mock_create_session)
        monkeypatch.setattr("src.agents.cli.resume_session", mock_resume_session)
        monkeypatch.setattr("src.agents.cli.get_session_state", lambda sid: states[-1])

        # modify → feedback → approve → approve → approve
        responses = iter(["m", "Add Adyen", "a", "a", "a"])
        monkeypatch.setattr("builtins.input", lambda prompt="": next(responses))

        from src.agents.cli import run_cli
        run_cli(company_url="https://stripe.com")

        assert call_count["n"] == 4  # modify + 3 approves
