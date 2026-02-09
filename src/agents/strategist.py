"""Strategy Builder — subgraph that synthesizes research into competitive strategies.

Nodes:
    analyze_findings: Cross-reference research results with company profile.
    generate_strategy: Produce strategy drafts with feature gaps, opportunities, etc.

The subgraph sets approval_status to "pending_strategy_approval" so the main
graph can interrupt for HITL Gate 3.

Skeleton implementation — real LLM logic added on Day 6.
"""

from langchain_core.messages import AIMessage
from langgraph.graph import END, StateGraph

from src.agents.state import APPROVAL_PENDING_STRATEGY, AgentState
from src.utils.logger import get_logger

logger = get_logger(__name__)


def analyze_findings(state: AgentState) -> dict:
    """Cross-reference research results with company profile.

    Reads: research_results, company_profile
    Writes: competitor_analyses

    TODO (Day 6): LLM call to synthesize findings into structured analyses.
    """
    logger.info("Strategist: analyzing findings")

    results = state.get("research_results", [])
    analyses = []

    # Skeleton: create placeholder analyses from research results
    for result in results:
        analyses.append({
            "competitor": result.get("competitor", "unknown"),
            "strengths": [],
            "weaknesses": [],
            "market_position": "unknown",
        })

    return {
        "competitor_analyses": analyses,
        "messages": [
            AIMessage(content=f"Analyzed {len(analyses)} competitor findings.")
        ],
    }


def generate_strategy(state: AgentState) -> dict:
    """Generate strategy drafts from the synthesized analysis.

    Reads: competitor_analyses, company_profile
    Writes: strategy_drafts, strategic_insights, approval_status

    TODO (Day 6): LLM call to produce detailed strategic recommendations.
    """
    logger.info("Strategist: generating strategy")

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
