"""Interactive CLI for competitive analysis chat sessions.

Provides a conversational interface that walks the user through the full
HITL-gated workflow:
    1. Enter company URL
    2. Review & approve/modify the research plan  (Gate 1)
    3. Review & approve/modify the research results (Gate 2)
    4. Review & approve/modify the strategy draft  (Gate 3)
    5. Display the final strategic insights report

Usage:
    uv run python -m src.agents.cli
    uv run python -m src.agents.cli --url https://stripe.com
"""

from __future__ import annotations

import argparse
import json
import sys
import textwrap
from typing import Any

from langchain_core.messages import AIMessage

from src.agents.graph import create_session, get_session_state, resume_session
from src.agents.state import (
    APPROVAL_APPROVED_STRATEGY,
    APPROVAL_PENDING_PLAN,
    APPROVAL_PENDING_RESEARCH,
    APPROVAL_PENDING_STRATEGY,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)

# ── Terminal helpers ──────────────────────────────────────────────────────────

_WIDTH = 80


def _hr(char: str = "─") -> None:
    print(char * _WIDTH)


def _header(title: str) -> None:
    _hr("═")
    print(f"  {title}")
    _hr("═")


def _section(title: str) -> None:
    print()
    _hr()
    print(f"  {title}")
    _hr()


def _wrap(text: str, indent: int = 2) -> str:
    prefix = " " * indent
    return textwrap.fill(text, width=_WIDTH - indent, initial_indent=prefix, subsequent_indent=prefix)


def _bullet_list(items: list[str], indent: int = 4) -> None:
    prefix = " " * indent
    for item in items:
        print(f"{prefix}• {item}")


# ── State display helpers ─────────────────────────────────────────────────────


def _show_agent_messages(state: dict[str, Any]) -> None:
    """Print the latest AI messages from the state."""
    messages = state.get("messages", [])
    for msg in messages:
        if isinstance(msg, AIMessage):
            print(_wrap(msg.content))
        elif isinstance(msg, dict) and msg.get("role") == "assistant":
            print(_wrap(msg["content"]))


def _show_research_plan(state: dict[str, Any]) -> None:
    """Display the generated research plan."""
    tasks = state.get("research_tasks", [])
    if not tasks:
        print("  (no tasks generated)")
        return

    for i, task in enumerate(tasks, 1):
        task_type = task.get("type", "unknown")
        target = task.get("target", "")
        url = task.get("url", "")
        focus = task.get("focus_areas", [])

        print(f"\n  Task {i}: {task_type}")
        if target:
            print(f"    Target : {target}")
        if url:
            print(f"    URL    : {url}")
        if focus:
            areas = focus if isinstance(focus, list) else [focus]
            print(f"    Focus  : {', '.join(areas)}")


def _show_research_results(state: dict[str, Any]) -> None:
    """Display a summary of research results."""
    results = state.get("research_results", [])
    if not results:
        print("  (no results yet)")
        return

    print(f"  {len(results)} research result(s) collected:\n")
    for result in results:
        competitor = result.get("competitor", "unknown")
        task_type = result.get("task_type", "")
        url = result.get("url", "")
        content_len = len(result.get("content", ""))
        print(f"    • {competitor}  [{task_type}]  {url}  ({content_len} chars)")


def _show_strategy(state: dict[str, Any]) -> None:
    """Display the strategy drafts and insights."""
    drafts = state.get("strategy_drafts", [])
    insights = state.get("strategic_insights")

    if insights and insights.get("summary"):
        _section("Executive Summary")
        print(_wrap(insights["summary"]))

    if drafts:
        draft = drafts[0]

        feature_gaps = draft.get("feature_gaps", [])
        if feature_gaps:
            _section("Feature Gaps")
            _bullet_list(feature_gaps)

        opportunities = draft.get("opportunities", [])
        if opportunities:
            _section("Opportunities")
            _bullet_list(opportunities)

        positioning = draft.get("positioning_suggestions", [])
        if positioning:
            _section("Positioning Suggestions")
            _bullet_list(positioning)

        fundraising = draft.get("fundraising_intel", [])
        if fundraising:
            _section("Fundraising Intel")
            _bullet_list(fundraising)


def _show_final_report(state: dict[str, Any]) -> None:
    """Display the complete final report."""
    _header("COMPETITIVE ANALYSIS REPORT")

    company_url = state.get("company_url", "")
    profile = state.get("company_profile") or {}
    company_name = profile.get("name") or company_url or "the company"

    print(f"\n  Company: {company_name}")
    if company_url:
        print(f"  URL    : {company_url}")

    analyses = state.get("competitor_analyses", [])
    if analyses:
        _section(f"Competitor Analyses  ({len(analyses)} competitors)")
        for analysis in analyses:
            name = analysis.get("competitor", "unknown")
            position = analysis.get("market_position", "unknown")
            threat = analysis.get("threat_level", "unknown")
            strengths = analysis.get("strengths", [])
            weaknesses = analysis.get("weaknesses", [])

            print(f"\n    ▶ {name}")
            print(f"      Market Position : {position}")
            print(f"      Threat Level    : {threat}")
            if strengths:
                print(f"      Strengths       : {', '.join(strengths[:3])}")
            if weaknesses:
                print(f"      Weaknesses      : {', '.join(weaknesses[:3])}")

    _show_strategy(state)
    _hr("═")
    print()


# ── Approval prompt ───────────────────────────────────────────────────────────


def _prompt_approval(gate_name: str) -> tuple[str, str]:
    """Ask the user to approve, modify, or quit.

    Returns:
        (action, message) where action is 'approve' | 'modify' | 'quit'
    """
    print(f"\n  What would you like to do with the {gate_name}?")
    print("    [a] Approve and continue")
    print("    [m] Modify — provide feedback")
    print("    [q] Quit")
    print()

    while True:
        raw = input("  Your choice (a/m/q): ").strip().lower()

        if raw in ("a", "approve", ""):
            return "approve", ""

        if raw in ("m", "modify"):
            feedback = input("  Feedback (what to change): ").strip()
            return "modify", feedback

        if raw in ("q", "quit", "exit"):
            return "quit", ""

        print("  Please enter a, m, or q.")


# ── Main session loop ─────────────────────────────────────────────────────────


def _get_company_url(args_url: str | None) -> str:
    """Get company URL from CLI arg or interactive prompt."""
    if args_url:
        return args_url.strip()

    print("\n  Enter the company website URL to analyze.")
    print("  Example: https://stripe.com\n")
    url = input("  Company URL: ").strip()
    if not url:
        print("  No URL provided. Exiting.")
        sys.exit(0)
    return url


def run_cli(company_url: str | None = None) -> None:
    """Run an interactive analysis session."""
    _header("Competitive Intelligence Analyzer")
    print()
    print("  This tool analyzes a company's competitive landscape through a")
    print("  guided, human-in-the-loop workflow with three review gates.")
    print()

    url = _get_company_url(company_url)

    # ── Gate 1: Plan ──────────────────────────────────────────────────────────
    print()
    print(f"  Analyzing: {url}")
    print("  Creating session and generating research plan...")
    print()

    try:
        session_id, state = create_session(
            company_url=url,
            initial_query=f"Analyze competitors for {url}",
        )
    except Exception as exc:
        print(f"\n  ERROR: Failed to create session — {exc}")
        logger.error(f"Session creation failed: {exc}", exc_info=True)
        sys.exit(1)

    while True:
        approval_status = state.get("approval_status", "")

        # ── Plan gate ─────────────────────────────────────────────────────────
        if approval_status == APPROVAL_PENDING_PLAN:
            _section("Research Plan  (Gate 1 of 3)")
            _show_agent_messages(state)
            _show_research_plan(state)

            action, feedback = _prompt_approval("research plan")
            if action == "quit":
                print("\n  Session saved. Exiting.")
                return

            print("\n  Processing...")
            try:
                state = resume_session(session_id, action, feedback)
            except Exception as exc:
                print(f"\n  ERROR: {exc}")
                logger.error(f"Resume failed: {exc}", exc_info=True)
                return

        # ── Research gate ─────────────────────────────────────────────────────
        elif approval_status == APPROVAL_PENDING_RESEARCH:
            _section("Research Results  (Gate 2 of 3)")
            _show_agent_messages(state)
            _show_research_results(state)

            action, feedback = _prompt_approval("research results")
            if action == "quit":
                print("\n  Session saved. Exiting.")
                return

            print("\n  Processing...")
            try:
                state = resume_session(session_id, action, feedback)
            except Exception as exc:
                print(f"\n  ERROR: {exc}")
                logger.error(f"Resume failed: {exc}", exc_info=True)
                return

        # ── Strategy gate ─────────────────────────────────────────────────────
        elif approval_status == APPROVAL_PENDING_STRATEGY:
            _section("Strategy Draft  (Gate 3 of 3)")
            _show_agent_messages(state)
            _show_strategy(state)

            action, feedback = _prompt_approval("strategy draft")
            if action == "quit":
                print("\n  Session saved. Exiting.")
                return

            print("\n  Processing...")
            try:
                state = resume_session(session_id, action, feedback)
            except Exception as exc:
                print(f"\n  ERROR: {exc}")
                logger.error(f"Resume failed: {exc}", exc_info=True)
                return

        # ── Complete ──────────────────────────────────────────────────────────
        elif approval_status == APPROVAL_APPROVED_STRATEGY or not approval_status:
            # Workflow finished — show final report
            _show_final_report(state)
            return

        else:
            # Unexpected status — refresh state and continue
            logger.warning(f"Unexpected approval_status: {approval_status}")
            refreshed = get_session_state(session_id)
            if refreshed:
                state = refreshed
            else:
                print(f"\n  Unexpected state: {approval_status}. Exiting.")
                return


# ── Entry point ───────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Competitive Intelligence Analyzer — interactive CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
            Examples:
              uv run python -m src.agents.cli
              uv run python -m src.agents.cli --url https://stripe.com
        """),
    )
    parser.add_argument(
        "--url",
        metavar="URL",
        help="Company website URL to analyze (skips the interactive prompt)",
    )
    args = parser.parse_args()

    try:
        run_cli(company_url=args.url)
    except KeyboardInterrupt:
        print("\n\n  Interrupted. Exiting.")
        sys.exit(0)


if __name__ == "__main__":
    main()
