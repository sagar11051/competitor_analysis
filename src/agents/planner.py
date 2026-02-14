"""Planner Agent — subgraph that analyzes user queries and creates research plans.

Nodes:
    analyze_query: Parse user message into structured intent (company URL, focus areas).
    create_research_tasks: Generate a list of research task dicts from the parsed intent.

The subgraph sets approval_status to "pending_plan_approval" so the main graph
can interrupt for HITL Gate 1.

Skeleton implementation — real LLM logic added on Day 6.
Day 5: Added memory store integration for user preferences and known competitors.
"""

from typing import Optional

from langchain_core.messages import AIMessage
from langgraph.graph import END, StateGraph

from src.agents.state import APPROVAL_PENDING_PLAN, AgentState
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


def analyze_query(state: AgentState) -> dict:
    """Parse the latest user message to extract intent.

    Reads: messages, company_url, user_profile
    Writes: company_url (confirmed/extracted), user_profile (enriched from memory)

    Also reads user preferences and known competitors from store if available.
    TODO (Day 6): LLM call to extract intent from user message + memory context.
    """
    logger.info("Planner: analyzing user query")

    # Skeleton: pass through the company_url already in state
    company_url = state.get("company_url", "")
    user_profile = dict(state.get("user_profile", {}))

    # Try to read user preferences and enrich profile from memory store
    store = _get_store_from_context()
    known_competitors = []

    if store:
        user_id = user_profile.get("user_id", "default")

        # Read user preferences from memory
        prefs = store.get_user_preferences(user_id)
        if prefs:
            logger.info(f"Planner: loaded user preferences from memory: {list(prefs.keys())}")
            user_profile["preferences"] = prefs

        # Read stored user profile
        stored_profile = store.get_user_profile(user_id)
        if stored_profile:
            logger.info(f"Planner: loaded user profile from memory")
            # Merge stored profile (don't overwrite existing keys)
            for key, value in stored_profile.items():
                if key not in user_profile:
                    user_profile[key] = value

        # Search for known competitors in memory cache
        if company_url:
            # Extract domain for search
            domain = company_url.replace("https://", "").replace("http://", "").split("/")[0]
            known_competitors = store.search_competitors(domain, limit=5)
            if known_competitors:
                logger.info(f"Planner: found {len(known_competitors)} cached competitors")

    return {
        "company_url": company_url,
        "user_profile": user_profile,
        "competitors": known_competitors,  # Pre-populate from cache
        "messages": [
            AIMessage(content=f"Analyzing competitive landscape for {company_url}...")
        ],
    }


def create_research_tasks(state: AgentState) -> dict:
    """Generate research tasks from the parsed intent.

    Reads: company_url, user_profile
    Writes: research_tasks, approval_status

    Also writes the research plan to session memory for later reference.
    TODO (Day 6): LLM call to generate a detailed research plan.
    """
    logger.info("Planner: creating research tasks")

    company_url = state.get("company_url", "")
    session_id = state.get("session_id", "")
    user_profile = state.get("user_profile", {})

    # Get focus areas from user preferences if available
    prefs = user_profile.get("preferences", {})
    focus_areas = prefs.get("focus_areas", ["overview", "products", "pricing", "team"])

    # Skeleton: create a default research plan
    tasks = [
        {
            "type": "company_profile",
            "target": company_url,
            "url": company_url,
            "focus_areas": focus_areas,
        },
        {
            "type": "competitor_discovery",
            "target": company_url,
            "url": None,
            "focus_areas": ["direct_competitors", "indirect_competitors"],
        },
    ]

    # Write research plan to session memory
    store = _get_store_from_context()
    if store and session_id:
        session_summary = {
            "query": company_url,
            "phase": "planning",
            "task_count": len(tasks),
            "focus_areas": focus_areas,
        }
        store.put_session_summary(session_id, session_summary)
        logger.info(f"Planner: saved research plan to session memory")

    return {
        "research_tasks": tasks,
        "approval_status": APPROVAL_PENDING_PLAN,
        "messages": [
            AIMessage(
                content=(
                    f"Research plan created with {len(tasks)} tasks. "
                    "Awaiting your approval to proceed."
                )
            )
        ],
    }


def build_planner_subgraph() -> StateGraph:
    """Build and return the Planner subgraph (uncompiled).

    Graph: analyze_query → create_research_tasks → END
    """
    graph = StateGraph(AgentState)

    graph.add_node("analyze_query", analyze_query)
    graph.add_node("create_research_tasks", create_research_tasks)

    graph.set_entry_point("analyze_query")
    graph.add_edge("analyze_query", "create_research_tasks")
    graph.add_edge("create_research_tasks", END)

    return graph
