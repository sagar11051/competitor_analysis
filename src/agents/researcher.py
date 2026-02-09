"""Research Orchestrator — subgraph that executes research tasks and aggregates results.

Nodes:
    dispatch_research: Prepare research tasks for execution.
    research_agent: Execute a single research task (tool calls go here).
    aggregate_results: Merge and deduplicate all research results.

The subgraph sets approval_status to "pending_research_approval" so the main
graph can interrupt for HITL Gate 2.

Skeleton implementation — real tool integration added on Day 3, LLM logic on Day 6.
"""

from datetime import datetime, timezone

from langchain_core.messages import AIMessage
from langgraph.graph import END, StateGraph

from src.agents.state import APPROVAL_PENDING_RESEARCH, AgentState
from src.utils.logger import get_logger

logger = get_logger(__name__)


def dispatch_research(state: AgentState) -> dict:
    """Validate and prepare research tasks for execution.

    Reads: research_tasks
    Writes: research_tasks (validated/enriched)

    TODO (Day 3): Add task validation and prioritization logic.
    """
    logger.info("Researcher: dispatching research tasks")

    tasks = state.get("research_tasks", [])
    logger.info(f"Researcher: {len(tasks)} tasks to execute")

    return {
        "messages": [
            AIMessage(content=f"Dispatching {len(tasks)} research tasks...")
        ],
    }


def research_agent(state: AgentState) -> dict:
    """Execute research tasks using Tavily Search and Crawl4AI.

    Reads: research_tasks
    Writes: research_results

    TODO (Day 3): Tavily search + Crawl4AI scraping with real tool calls.
    TODO (Day 6): LLM-driven task interpretation and result extraction.
    """
    logger.info("Researcher: executing research tasks")

    tasks = state.get("research_tasks", [])
    results = []

    # Skeleton: create placeholder results for each task
    for task in tasks:
        results.append({
            "competitor": task.get("target", "unknown"),
            "data": {},
            "source": task.get("type", "unknown"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    return {
        "research_results": results,
        "messages": [
            AIMessage(content=f"Completed {len(results)} research tasks.")
        ],
    }


def aggregate_results(state: AgentState) -> dict:
    """Merge and deduplicate research results.

    Reads: research_results
    Writes: research_results (deduplicated), approval_status

    TODO (Day 6): LLM-driven deduplication and summarization.
    """
    logger.info("Researcher: aggregating results")

    results = state.get("research_results", [])
    logger.info(f"Researcher: aggregated {len(results)} results")

    return {
        "research_results": results,
        "approval_status": APPROVAL_PENDING_RESEARCH,
        "messages": [
            AIMessage(
                content=(
                    f"Research complete — {len(results)} results gathered. "
                    "Awaiting your approval to proceed to strategy."
                )
            )
        ],
    }


def build_researcher_subgraph() -> StateGraph:
    """Build and return the Research Orchestrator subgraph (uncompiled).

    Graph: dispatch_research → research_agent → aggregate_results → END
    """
    graph = StateGraph(AgentState)

    graph.add_node("dispatch_research", dispatch_research)
    graph.add_node("research_agent", research_agent)
    graph.add_node("aggregate_results", aggregate_results)

    graph.set_entry_point("dispatch_research")
    graph.add_edge("dispatch_research", "research_agent")
    graph.add_edge("research_agent", "aggregate_results")
    graph.add_edge("aggregate_results", END)

    return graph
