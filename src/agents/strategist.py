"""Strategy Builder — subgraph that synthesizes research into competitive strategies.

Nodes:
    analyze_findings: Cross-reference research results with company profile.
    generate_strategy: Produce strategy drafts with feature gaps, opportunities, etc.

The subgraph sets approval_status to "pending_strategy_approval" so the main
graph can interrupt for HITL Gate 3.

Day 5: Added memory store integration for historical analysis and session summaries.
Day 6: Added LLM integration for findings analysis and strategy generation.
"""

import json
from typing import Any, Optional

from langchain_core.messages import AIMessage
from langgraph.graph import END, StateGraph
from langgraph.store.base import BaseStore

from src.agents.llm import generate_json, is_llm_configured
from src.agents.prompts import (
    STRATEGIST_ANALYZE,
    STRATEGIST_GENERATE,
    STRATEGIST_SYSTEM,
)
from src.agents.state import APPROVAL_PENDING_STRATEGY, AgentState
from src.memory.store import MemoryStore
from src.utils.logger import get_logger

logger = get_logger(__name__)


def _format_company_profile(profile: Optional[dict]) -> str:
    """Format company profile for prompt injection."""
    if not profile:
        return "No company profile available."

    lines = []
    if profile.get("name"):
        lines.append(f"Name: {profile['name']}")
    if profile.get("website"):
        lines.append(f"Website: {profile['website']}")
    if profile.get("description"):
        lines.append(f"Description: {profile['description']}")
    if profile.get("products"):
        products = profile["products"]
        if isinstance(products, list):
            lines.append(f"Products: {', '.join(products)}")
        else:
            lines.append(f"Products: {products}")
    if profile.get("pricing_model"):
        lines.append(f"Pricing Model: {profile['pricing_model']}")
    if profile.get("target_market"):
        lines.append(f"Target Market: {profile['target_market']}")
    if profile.get("key_features"):
        features = profile["key_features"]
        if isinstance(features, list):
            lines.append(f"Key Features: {', '.join(features)}")
        else:
            lines.append(f"Key Features: {features}")

    return "\n".join(lines) if lines else "Limited company profile data."


def _format_research_results(results: list[dict]) -> str:
    """Format research results for prompt injection."""
    if not results:
        return "No research results available."

    formatted = []
    for i, result in enumerate(results, 1):
        competitor = result.get("competitor", f"Competitor {i}")
        content = result.get("content", "")
        url = result.get("url", "")
        task_type = result.get("task_type", "unknown")

        # Truncate content if too long
        if len(content) > 2000:
            content = content[:2000] + "..."

        formatted.append(f"### {competitor}")
        if url:
            formatted.append(f"Source: {url}")
        formatted.append(f"Type: {task_type}")
        if content:
            formatted.append(f"Content:\n{content}")
        formatted.append("")

    return "\n".join(formatted)


def _format_competitor_analyses(analyses: list[dict]) -> str:
    """Format competitor analyses for prompt injection."""
    if not analyses:
        return "No competitor analyses available."

    formatted = []
    for analysis in analyses:
        competitor = analysis.get("competitor", "Unknown")
        formatted.append(f"### {competitor}")

        strengths = analysis.get("strengths", [])
        if strengths:
            formatted.append(f"Strengths: {', '.join(strengths) if isinstance(strengths, list) else strengths}")

        weaknesses = analysis.get("weaknesses", [])
        if weaknesses:
            formatted.append(f"Weaknesses: {', '.join(weaknesses) if isinstance(weaknesses, list) else weaknesses}")

        position = analysis.get("market_position", "unknown")
        formatted.append(f"Market Position: {position}")

        threat = analysis.get("threat_level", "unknown")
        formatted.append(f"Threat Level: {threat}")

        formatted.append("")

    return "\n".join(formatted)


def _analyze_with_llm(
    company_profile: Optional[dict],
    research_results: list[dict],
) -> list[dict[str, Any]]:
    """Use LLM to analyze research findings.

    Returns:
        List of competitor analysis dicts
    """
    prompt = STRATEGIST_ANALYZE.format(
        company_profile=_format_company_profile(company_profile),
        competitor_analyses=_format_research_results(research_results),
    )

    try:
        result = generate_json(prompt=prompt, system_prompt=STRATEGIST_SYSTEM)
        analyses = result.get("analyses", [])
        logger.info(f"LLM analyzed {len(analyses)} competitors")

        # Validate and normalize analyses
        validated = []
        for analysis in analyses:
            validated.append({
                "competitor": analysis.get("competitor", "Unknown"),
                "strengths": analysis.get("strengths", []),
                "weaknesses": analysis.get("weaknesses", []),
                "market_position": analysis.get("market_position", "unknown"),
                "threat_level": analysis.get("threat_level", "medium"),
                "llm_generated": True,
            })

        return validated

    except Exception as e:
        logger.warning(f"LLM analysis failed: {e}, using placeholder analyses")
        return _placeholder_analyses(research_results)


def _placeholder_analyses(research_results: list[dict]) -> list[dict[str, Any]]:
    """Generate placeholder analyses when LLM is unavailable."""
    analyses = []
    for result in research_results:
        competitor = result.get("competitor", "unknown")
        analyses.append({
            "competitor": competitor,
            "strengths": [],
            "weaknesses": [],
            "market_position": "unknown",
            "threat_level": "unknown",
            "llm_generated": False,
        })
    return analyses


def analyze_findings(state: AgentState, store: BaseStore = None) -> dict:
    """Cross-reference research results with company profile.

    Reads: research_results, company_profile
    Writes: competitor_analyses

    Uses LLM to synthesize raw research data into structured competitor analyses
    with strengths, weaknesses, market position, and threat level.

    Args:
        store: LangGraph-injected BaseStore for cross-session memory (LangGraph 1.0+).
    """
    logger.info("Strategist: analyzing findings")

    results = state.get("research_results", [])
    company_profile = state.get("company_profile")

    # Wrap injected store in our MemoryStore helper
    memory = MemoryStore(store) if store is not None else None
    historical_count = 0

    # Use LLM to analyze if configured
    if is_llm_configured() and results:
        analyses = _analyze_with_llm(company_profile, results)
    else:
        logger.warning("LLM not configured or no results, using placeholder analyses")
        analyses = _placeholder_analyses(results)

    # Enrich analyses with historical data from memory store
    if memory:
        for analysis in analyses:
            competitor_name = analysis.get("competitor", "")
            if not competitor_name:
                continue

            cached_profile = memory.get_competitor_profile(competitor_name)
            if cached_profile and "analysis" in cached_profile:
                historical = cached_profile["analysis"]
                historical_count += 1
                logger.info(f"Found historical analysis for: {competitor_name}")

                # Merge historical data (prefer LLM-generated if available)
                if not analysis.get("llm_generated"):
                    analysis["strengths"] = historical.get("strengths", analysis["strengths"])
                    analysis["weaknesses"] = historical.get("weaknesses", analysis["weaknesses"])
                    analysis["market_position"] = historical.get("market_position", analysis["market_position"])

                analysis["has_historical_data"] = True
            else:
                analysis["has_historical_data"] = False

    if historical_count > 0:
        logger.info(f"Strategist: enriched {historical_count} analyses with historical data")

    # Cache new analyses in memory store
    if memory:
        for analysis in analyses:
            competitor_name = analysis.get("competitor", "")
            if competitor_name and analysis.get("llm_generated"):
                # Update competitor profile with new analysis
                existing = memory.get_competitor_profile(competitor_name) or {}
                existing["analysis"] = {
                    "strengths": analysis.get("strengths", []),
                    "weaknesses": analysis.get("weaknesses", []),
                    "market_position": analysis.get("market_position", "unknown"),
                    "threat_level": analysis.get("threat_level", "medium"),
                }
                memory.put_competitor_profile(competitor_name, existing)
                logger.debug(f"Cached analysis for: {competitor_name}")

    return {
        "competitor_analyses": analyses,
        "messages": [
            AIMessage(
                content=(
                    f"Analyzed {len(analyses)} competitors "
                    f"({historical_count} with historical data).\n\n"
                    "Key findings:\n" +
                    "\n".join([
                        f"• {a['competitor']}: {a['market_position']} (threat: {a['threat_level']})"
                        for a in analyses[:5]
                    ])
                )
            )
        ],
    }


def _generate_strategy_with_llm(
    company_name: str,
    company_profile: Optional[dict],
    competitor_analyses: list[dict],
) -> dict[str, Any]:
    """Use LLM to generate strategic recommendations.

    Returns:
        Dict with feature_gaps, opportunities, positioning_suggestions,
        fundraising_intel, summary
    """
    prompt = STRATEGIST_GENERATE.format(
        company_name=company_name,
        company_profile=_format_company_profile(company_profile),
        competitive_analysis=_format_competitor_analyses(competitor_analyses),
    )

    try:
        result = generate_json(
            prompt=prompt,
            system_prompt=STRATEGIST_SYSTEM,
            max_tokens=3000,  # Allow longer response for strategy
        )
        logger.info("LLM generated strategic recommendations")

        # Validate and normalize
        return {
            "feature_gaps": result.get("feature_gaps", []),
            "opportunities": result.get("opportunities", []),
            "positioning_suggestions": result.get("positioning_suggestions", []),
            "fundraising_intel": result.get("fundraising_intel", []),
            "summary": result.get("summary", "Strategy generation completed."),
            "llm_generated": True,
        }

    except Exception as e:
        logger.warning(f"LLM strategy generation failed: {e}, using placeholder")
        return _placeholder_strategy()


def _placeholder_strategy() -> dict[str, Any]:
    """Generate placeholder strategy when LLM is unavailable."""
    return {
        "feature_gaps": [],
        "opportunities": [],
        "positioning_suggestions": [],
        "fundraising_intel": [],
        "summary": "Strategic analysis pending full LLM integration.",
        "llm_generated": False,
    }


def generate_strategy(state: AgentState, store: BaseStore = None) -> dict:
    """Generate strategy drafts from the synthesized analysis.

    Reads: competitor_analyses, company_profile, session_id, company_url
    Writes: strategy_drafts, strategic_insights, approval_status

    Uses LLM to produce detailed strategic recommendations including
    feature gaps, opportunities, positioning suggestions, and executive summary.

    Args:
        store: LangGraph-injected BaseStore for cross-session memory (LangGraph 1.0+).
    """
    logger.info("Strategist: generating strategy")

    session_id = state.get("session_id", "")
    company_url = state.get("company_url", "")
    company_profile = state.get("company_profile")
    competitor_analyses = state.get("competitor_analyses", [])

    # Infer company name
    company_name = "the company"
    if company_profile and company_profile.get("name"):
        company_name = company_profile["name"]
    elif company_url:
        # Extract from URL
        domain = company_url.replace("https://", "").replace("http://", "").split("/")[0]
        company_name = domain.replace("www.", "").split(".")[0].title()

    # Generate strategy with LLM if configured
    if is_llm_configured() and competitor_analyses:
        strategy = _generate_strategy_with_llm(
            company_name=company_name,
            company_profile=company_profile,
            competitor_analyses=competitor_analyses,
        )
    else:
        logger.warning("LLM not configured or no analyses, using placeholder strategy")
        strategy = _placeholder_strategy()

    # Create draft and insights objects
    draft = {
        "feature_gaps": strategy.get("feature_gaps", []),
        "opportunities": strategy.get("opportunities", []),
        "positioning_suggestions": strategy.get("positioning_suggestions", []),
        "fundraising_intel": strategy.get("fundraising_intel", []),
    }

    insights = {
        "summary": strategy.get("summary", ""),
        "recommendations": (
            strategy.get("positioning_suggestions", [])[:3] +
            strategy.get("opportunities", [])[:2]
        ),
        "company_name": company_name,
        "competitor_count": len(competitor_analyses),
        "llm_generated": strategy.get("llm_generated", False),
    }

    # Extract key findings for session summary
    key_findings = [
        f"Analyzed {len(competitor_analyses)} competitors for {company_name}",
    ]

    # Add top threats
    high_threats = [
        a["competitor"] for a in competitor_analyses
        if a.get("threat_level") == "high"
    ]
    if high_threats:
        key_findings.append(f"High-threat competitors: {', '.join(high_threats[:3])}")

    # Add top opportunities
    if strategy.get("opportunities"):
        key_findings.append(f"Key opportunity: {strategy['opportunities'][0]}")

    # Write session summary to memory
    memory = MemoryStore(store) if store is not None else None
    if memory and session_id:
        session_summary = {
            "query": company_url,
            "company_name": company_name,
            "phase": "completed",
            "key_findings": key_findings,
            "competitor_count": len(competitor_analyses),
            "decisions": ["Strategy draft generated"],
            "feature_gaps_count": len(draft.get("feature_gaps", [])),
            "opportunities_count": len(draft.get("opportunities", [])),
        }
        memory.put_session_summary(session_id, session_summary)
        logger.info(f"Strategist: saved session summary to memory")

    # Build user-facing summary
    summary_lines = [strategy.get("summary", "Strategy analysis complete.")]
    if draft.get("feature_gaps"):
        summary_lines.append(f"\nFeature gaps identified: {len(draft['feature_gaps'])}")
    if draft.get("opportunities"):
        summary_lines.append(f"Opportunities identified: {len(draft['opportunities'])}")
    if draft.get("positioning_suggestions"):
        summary_lines.append(f"Positioning suggestions: {len(draft['positioning_suggestions'])}")

    return {
        "strategy_drafts": [draft],
        "strategic_insights": insights,
        "approval_status": APPROVAL_PENDING_STRATEGY,
        "messages": [
            AIMessage(
                content=(
                    "\n".join(summary_lines) +
                    "\n\nAwaiting your approval to finalize the report."
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
