"""Strategy Builder — subgraph that synthesizes research into competitive strategies.

Nodes:
    analyze_findings: Cross-reference research results with company profile.
    generate_strategy: Produce strategy drafts with feature gaps, opportunities, etc.

The subgraph sets approval_status to "pending_strategy_approval" so the main
graph can interrupt for HITL Gate 3.

Skeleton implementation — real LLM logic added on Day 6.
Day 5: Added memory store integration for historical analysis and session summaries.
"""

from langchain_core.messages import AIMessage
from langgraph.graph import END, StateGraph

from src.agents.state import APPROVAL_PENDING_STRATEGY, AgentState
from src.utils.logger import get_logger

logger = get_logger(__name__)


def _get_store_from_context():
    """Get MemoryStore from LangGraph runtime context if available."""
    try:
        from langgraph.store.base import get_store
        from src.memory.store import MemoryStore
        raw_store = get_store()
        if raw_store is not None:
            return MemoryStore(raw_store)
    except (ImportError, RuntimeError):
        pass
    return None


def analyze_findings(state: AgentState) -> dict:
    """Cross-reference research results with company profile.

    Reads: research_results, company_profile
    Writes: competitor_analyses

    Also reads historical competitor analyses from store if available.
    TODO (Day 6): LLM call to synthesize findings into structured analyses.
    """
    logger.info("Strategist: analyzing findings")

    results = state.get("research_results", [])
    analyses = []

    # Try to get historical analyses from memory store
    store = _get_store_from_context()
    historical_count = 0

    # Skeleton: create placeholder analyses from research results
    for result in results:
        competitor_name = result.get("competitor", "unknown")

        # Check for historical analysis in store
        historical_analysis = None
        if store:
            cached_profile = store.get_competitor_profile(competitor_name)
            if cached_profile and "analysis" in cached_profile:
                historical_analysis = cached_profile.get("analysis")
                historical_count += 1
                logger.info(f"Found historical analysis for: {competitor_name}")

        analysis = {
            "competitor": competitor_name,
            "strengths": historical_analysis.get("strengths", []) if historical_analysis else [],
            "weaknesses": historical_analysis.get("weaknesses", []) if historical_analysis else [],
            "market_position": historical_analysis.get("market_position", "unknown") if historical_analysis else "unknown",
            "has_historical_data": historical_analysis is not None,
        }
        analyses.append(analysis)

    if historical_count > 0:
        logger.info(f"Strategist: enriched {historical_count} analyses with historical data")

    return {
        "competitor_analyses": analyses,
        "messages": [
            AIMessage(content=f"Analyzed {len(analyses)} competitor findings ({historical_count} with historical data).")
        ],
    }


def generate_strategy(state: AgentState) -> dict:
    """Generate strategy drafts from the synthesized analysis.

    Reads: competitor_analyses, company_profile
    Writes: strategy_drafts, strategic_insights, approval_status

    Also writes the session summary to memory for future reference.
    TODO (Day 6): LLM call to produce detailed strategic recommendations.
    """
    logger.info("Strategist: generating strategy")

    session_id = state.get("session_id", "")
    company_url = state.get("company_url", "")
    competitor_analyses = state.get("competitor_analyses", [])

    # Skeleton: create a placeholder strategy draft
    draft = {
        "feature_gaps": [],
        "opportunities": [],
        "positioning_suggestions": [],
        "fundraising_intel": [],
    }

    insights = {
        "summary": "Strategic analysis pending full LLM integration.",
        "recommendations": [],
    }

    # Extract key findings for session summary
    key_findings = [
        f"Analyzed {len(competitor_analyses)} competitors"
    ]
    for analysis in competitor_analyses[:3]:  # Top 3
        competitor = analysis.get("competitor", "unknown")
        position = analysis.get("market_position", "unknown")
        key_findings.append(f"{competitor}: {position}")

    # Write session summary to memory
    store = _get_store_from_context()
    if store and session_id:
        session_summary = {
            "query": company_url,
            "phase": "completed",
            "key_findings": key_findings,
            "competitor_count": len(competitor_analyses),
            "decisions": ["Strategy draft generated"],
        }
        store.put_session_summary(session_id, session_summary)
        logger.info(f"Strategist: saved session summary to memory")

    return {
        "strategy_drafts": [draft],
        "strategic_insights": insights,
        "approval_status": APPROVAL_PENDING_STRATEGY,
        "messages": [
            AIMessage(
                content=(
                    "Strategy draft generated. "
                    "Awaiting your approval to finalize the report."
                )
            )
        ],
    }


def build_strategist_subgraph() -> StateGraph:
    """Build and return the Strategy Builder subgraph (uncompiled).

    Graph: analyze_findings → generate_strategy → END
    """
    graph = StateGraph(AgentState)

    graph.add_node("analyze_findings", analyze_findings)
    graph.add_node("generate_strategy", generate_strategy)

    graph.set_entry_point("analyze_findings")
    graph.add_edge("analyze_findings", "generate_strategy")
    graph.add_edge("generate_strategy", END)

    return graph
