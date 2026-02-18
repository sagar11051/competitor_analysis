"""Research Orchestrator — subgraph that executes research tasks and aggregates results.

Nodes:
    dispatch_research: Validate tasks and prepare for execution.
    research_agent: Execute tasks using Tavily Search and Crawl4AI.
    aggregate_results: Merge and deduplicate all research results.

The subgraph sets approval_status to "pending_research_approval" so the main
graph can interrupt for HITL Gate 2.

Day 5: Added memory store integration for competitor caching.
"""

import asyncio
from datetime import datetime, timezone
from typing import Optional

from langchain_core.messages import AIMessage
from langgraph.graph import END, StateGraph
from langgraph.store.base import BaseStore

from src.agents.state import APPROVAL_PENDING_RESEARCH, AgentState
from src.memory.store import MemoryStore
from src.tools.tavily_search import TavilySearchTool
from src.tools.web_scraper import WebScraperTool, chunk_content
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Module-level tool instances (reused across invocations)
_tavily = TavilySearchTool()
_scraper = WebScraperTool()


def dispatch_research(state: AgentState) -> dict:
    """Validate and prepare research tasks for execution.

    Reads: research_tasks
    Writes: messages
    """
    logger.info("Researcher: dispatching research tasks")

    tasks = state.get("research_tasks", [])

    # Validate: each task must have type and target
    valid_tasks = []
    for task in tasks:
        if task.get("type") and task.get("target"):
            valid_tasks.append(task)
        else:
            logger.warning(f"Skipping invalid task: {task}")

    logger.info(f"Researcher: {len(valid_tasks)}/{len(tasks)} tasks valid")

    return {
        "research_tasks": valid_tasks,
        "messages": [
            AIMessage(content=f"Dispatching {len(valid_tasks)} research tasks...")
        ],
    }


def _execute_company_profile(task: dict) -> dict:
    """Execute a company_profile task: scrape the target URL."""
    url = task.get("url") or task.get("target", "")
    if not url:
        return {
            "competitor": task.get("target", "unknown"),
            "data": {"error": "No URL provided"},
            "source": "company_profile",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    try:
        pages = asyncio.run(_scraper.scrape_domain(url))
        combined_markdown = "\n\n---\n\n".join(
            p["markdown"] for p in pages if p.get("markdown")
        )

        # Chunk if content is large
        chunks = chunk_content(combined_markdown) if combined_markdown else []

        return {
            "competitor": task.get("target", url),
            "data": {
                "pages_scraped": len(pages),
                "total_chars": len(combined_markdown),
                "chunks": len(chunks),
                "content_chunks": chunks[:5],  # Keep first 5 chunks for LLM
                "page_titles": [p.get("title", "") for p in pages],
            },
            "source": "crawl4ai",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.error(f"Company profile scrape failed: {e}")
        return {
            "competitor": task.get("target", url),
            "data": {"error": str(e)},
            "source": "crawl4ai",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


def _execute_competitor_discovery(task: dict) -> dict:
    """Execute a competitor_discovery task: search Tavily for competitors."""
    target = task.get("target", "")
    if not _tavily.is_configured():
        logger.warning("Tavily not configured — returning empty results")
        return {
            "competitor": target,
            "data": {"error": "Tavily API key not configured"},
            "source": "tavily",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    try:
        # Build a search query from the target
        query = f"{target} competitors alternatives"
        focus = task.get("focus_areas", [])
        if focus:
            query += " " + " ".join(focus)

        results = _tavily.search(query, max_results=10, search_depth="advanced")

        return {
            "competitor": target,
            "data": {
                "search_results": results,
                "result_count": len(results),
            },
            "source": "tavily",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.error(f"Competitor discovery failed: {e}")
        return {
            "competitor": target,
            "data": {"error": str(e)},
            "source": "tavily",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


def _execute_competitor_deep_dive(task: dict) -> dict:
    """Execute a competitor_deep_dive task: scrape a specific competitor URL."""
    url = task.get("url") or task.get("target", "")
    if not url:
        return {
            "competitor": task.get("target", "unknown"),
            "data": {"error": "No URL provided"},
            "source": "competitor_deep_dive",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # Determine which subpages to focus on
    focus = task.get("focus_areas", [])
    subpages = ["/"]
    for area in focus:
        area_lower = area.lower()
        if "pricing" in area_lower:
            subpages.append("/pricing")
        if "product" in area_lower or "feature" in area_lower:
            subpages.extend(["/product", "/products", "/features"])
        if "about" in area_lower or "team" in area_lower:
            subpages.append("/about")
        if "blog" in area_lower:
            subpages.append("/blog")
    if len(subpages) == 1:
        # Default subpages if no focus areas matched
        subpages = ["/", "/about", "/pricing", "/product"]

    try:
        pages = asyncio.run(_scraper.scrape_domain(url, subpages=subpages))
        combined = "\n\n---\n\n".join(
            p["markdown"] for p in pages if p.get("markdown")
        )
        chunks = chunk_content(combined) if combined else []

        return {
            "competitor": task.get("target", url),
            "data": {
                "pages_scraped": len(pages),
                "total_chars": len(combined),
                "chunks": len(chunks),
                "content_chunks": chunks[:5],
                "page_titles": [p.get("title", "") for p in pages],
            },
            "source": "crawl4ai",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.error(f"Competitor deep dive failed: {e}")
        return {
            "competitor": task.get("target", url),
            "data": {"error": str(e)},
            "source": "crawl4ai",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


# Task type → executor mapping
_TASK_EXECUTORS = {
    "company_profile": _execute_company_profile,
    "competitor_discovery": _execute_competitor_discovery,
    "competitor_deep_dive": _execute_competitor_deep_dive,
}


def research_agent(state: AgentState, store: BaseStore = None) -> dict:
    """Execute research tasks using Tavily Search and Crawl4AI.

    Reads: research_tasks
    Writes: research_results, messages

    Routes each task to the appropriate executor based on task type.
    Checks competitor cache before scraping and caches new results.

    Args:
        store: LangGraph-injected BaseStore for cross-session memory (LangGraph 1.0+).
    """
    logger.info("Researcher: executing research tasks")

    tasks = state.get("research_tasks", [])
    results = []

    # Wrap injected store in our MemoryStore helper
    memory = MemoryStore(store) if store is not None else None
    cache_hits = 0
    cache_writes = 0

    for task in tasks:
        task_type = task.get("type", "")
        target = task.get("target", "unknown")

        # Check cache for competitor deep dive tasks
        if memory and task_type == "competitor_deep_dive":
            cached = memory.get_competitor_profile(target)
            if cached and "data" in cached:
                logger.info(f"Cache hit for competitor: {target}")
                cache_hits += 1
                results.append({
                    "competitor": target,
                    "data": cached["data"],
                    "source": "cache",
                    "timestamp": cached.get("timestamp", datetime.now(timezone.utc).isoformat()),
                })
                continue

        executor = _TASK_EXECUTORS.get(task_type)

        if executor:
            logger.info(f"Executing task: {task_type} → {target}")
            result = executor(task)

            # Cache competitor results for future use
            if memory and task_type in ("competitor_deep_dive", "company_profile"):
                if "error" not in result.get("data", {}):
                    memory.put_competitor_profile(target, result)
                    cache_writes += 1
                    logger.info(f"Cached result for: {target}")
        else:
            logger.warning(f"Unknown task type: {task_type}")
            result = {
                "competitor": task.get("target", "unknown"),
                "data": {"error": f"Unknown task type: {task_type}"},
                "source": task_type,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        results.append(result)

    logger.info(f"Researcher: {cache_hits} cache hits, {cache_writes} cache writes")

    return {
        "research_results": results,
        "messages": [
            AIMessage(content=f"Completed {len(results)} research tasks ({cache_hits} from cache).")
        ],
    }


def aggregate_results(state: AgentState) -> dict:
    """Merge and deduplicate research results.

    Reads: research_results
    Writes: research_results (deduplicated), approval_status, messages

    TODO (Day 6): LLM-driven deduplication and summarization.
    """
    logger.info("Researcher: aggregating results")

    results = state.get("research_results", [])

    # Deduplicate by (competitor, source)
    seen = set()
    deduped = []
    for r in results:
        key = (r.get("competitor", ""), r.get("source", ""))
        if key not in seen:
            seen.add(key)
            deduped.append(r)

    successful = [r for r in deduped if "error" not in r.get("data", {})]
    failed = [r for r in deduped if "error" in r.get("data", {})]

    logger.info(
        f"Researcher: {len(deduped)} results "
        f"({len(successful)} successful, {len(failed)} failed)"
    )

    return {
        "research_results": deduped,
        "approval_status": APPROVAL_PENDING_RESEARCH,
        "messages": [
            AIMessage(
                content=(
                    f"Research complete — {len(successful)} successful results, "
                    f"{len(failed)} failed. "
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
