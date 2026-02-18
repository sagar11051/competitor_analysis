"""Planner Agent — subgraph that analyzes user queries and creates research plans.

Nodes:
    analyze_query: Parse user message into structured intent (company URL, focus areas).
    create_research_tasks: Generate a list of research task dicts from the parsed intent.

The subgraph sets approval_status to "pending_plan_approval" so the main graph
can interrupt for HITL Gate 1.

Day 5: Added memory store integration for user preferences and known competitors.
Day 6: Added LLM integration for intent extraction and task generation.
"""

import json
from typing import Any, Optional

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import END, StateGraph
from langgraph.store.base import BaseStore

from src.agents.llm import generate_json, is_llm_configured, parse_json_response
from src.agents.prompts import (
    PLANNER_ANALYZE_QUERY,
    PLANNER_CREATE_TASKS,
    PLANNER_SYSTEM,
)
from src.agents.state import APPROVAL_PENDING_PLAN, AgentState
from src.memory.store import MemoryStore
from src.utils.logger import get_logger

logger = get_logger(__name__)


def _extract_user_message(messages: list) -> str:
    """Extract the latest user message text from the messages list."""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            return msg.content
        if isinstance(msg, dict) and msg.get("role") == "user":
            return msg.get("content", "")
    return ""


def _extract_intent_with_llm(
    user_message: str,
    company_url: str,
) -> dict[str, Any]:
    """Use LLM to extract structured intent from user message.

    Returns:
        Dict with company_url, company_name, focus_areas, constraints
    """
    prompt = PLANNER_ANALYZE_QUERY.format(
        user_message=user_message,
        company_url=company_url,
    )

    try:
        result = generate_json(prompt=prompt, system_prompt=PLANNER_SYSTEM)
        logger.info(f"LLM extracted intent: {list(result.keys())}")
        return result
    except Exception as e:
        logger.warning(f"LLM intent extraction failed: {e}, using defaults")
        # Fallback to basic extraction
        return {
            "company_url": company_url,
            "company_name": _infer_company_name(company_url),
            "focus_areas": ["overview", "products", "pricing", "competitors"],
            "constraints": [],
        }


def _infer_company_name(url: str) -> str:
    """Infer company name from URL."""
    if not url:
        return "Unknown"
    # Extract domain and clean it
    domain = url.replace("https://", "").replace("http://", "").split("/")[0]
    domain = domain.replace("www.", "")
    # Get the main part (before .com, etc.)
    name = domain.split(".")[0]
    return name.title()


def analyze_query(state: AgentState, store: BaseStore = None) -> dict:
    """Parse the latest user message to extract intent.

    Reads: messages, company_url, user_profile
    Writes: company_url (confirmed/extracted), user_profile (enriched from memory),
            competitors (from cache)

    Uses LLM to extract structured intent from the user message including
    company URL, name, focus areas, and constraints.

    Args:
        store: LangGraph-injected BaseStore for cross-session memory (LangGraph 1.0+).
    """
    logger.info("Planner: analyzing user query")

    # Get initial state
    company_url = state.get("company_url", "")
    user_profile = dict(state.get("user_profile", {}))
    messages = state.get("messages", [])

    # Extract the user message
    user_message = _extract_user_message(messages)
    if not user_message and company_url:
        user_message = f"Analyze competitors for {company_url}"

    # Wrap injected store in our MemoryStore helper
    memory = MemoryStore(store) if store is not None else None
    known_competitors = []

    if memory:
        user_id = user_profile.get("user_id", "default")

        # Read user preferences from memory
        prefs = memory.get_user_preferences(user_id)
        if prefs:
            logger.info(f"Planner: loaded user preferences from memory: {list(prefs.keys())}")
            user_profile["preferences"] = prefs

        # Read stored user profile
        stored_profile = memory.get_user_profile(user_id)
        if stored_profile:
            logger.info(f"Planner: loaded user profile from memory")
            # Merge stored profile (don't overwrite existing keys)
            for key, value in stored_profile.items():
                if key not in user_profile:
                    user_profile[key] = value

        # Search for known competitors in memory cache
        if company_url:
            domain = company_url.replace("https://", "").replace("http://", "").split("/")[0]
            known_competitors = memory.search_competitors(domain, limit=5)
            if known_competitors:
                logger.info(f"Planner: found {len(known_competitors)} cached competitors")

    # Use LLM to extract intent if configured
    if is_llm_configured():
        intent = _extract_intent_with_llm(user_message, company_url)
        # Update company_url if LLM found a better one
        if intent.get("company_url"):
            company_url = intent["company_url"]
        # Store extracted intent in user_profile for create_research_tasks
        user_profile["extracted_intent"] = intent
    else:
        logger.warning("LLM not configured, using basic intent extraction")
        user_profile["extracted_intent"] = {
            "company_url": company_url,
            "company_name": _infer_company_name(company_url),
            "focus_areas": ["overview", "products", "pricing", "competitors"],
            "constraints": [],
        }

    company_name = user_profile["extracted_intent"].get("company_name", "the company")

    return {
        "company_url": company_url,
        "user_profile": user_profile,
        "competitors": known_competitors,
        "messages": [
            AIMessage(content=f"Analyzing competitive landscape for {company_name} ({company_url})...")
        ],
    }


def _generate_tasks_with_llm(
    company_name: str,
    company_url: str,
    focus_areas: list[str],
    constraints: list[str],
) -> list[dict[str, Any]]:
    """Use LLM to generate research tasks.

    Returns:
        List of task dicts with type, target, url, focus_areas
    """
    prompt = PLANNER_CREATE_TASKS.format(
        company_name=company_name,
        company_url=company_url,
        focus_areas=json.dumps(focus_areas),
        constraints=json.dumps(constraints),
    )

    try:
        result = generate_json(prompt=prompt, system_prompt=PLANNER_SYSTEM)
        tasks = result.get("tasks", [])
        logger.info(f"LLM generated {len(tasks)} research tasks")

        # Validate and normalize tasks
        valid_types = {"company_profile", "competitor_discovery", "competitor_deep_dive"}
        validated_tasks = []
        for task in tasks:
            task_type = task.get("type", "")
            if task_type not in valid_types:
                logger.warning(f"Skipping invalid task type: {task_type}")
                continue
            validated_tasks.append({
                "type": task_type,
                "target": task.get("target", ""),
                "url": task.get("url"),
                "focus_areas": task.get("focus_areas", focus_areas),
            })

        return validated_tasks if validated_tasks else _default_tasks(company_url, focus_areas)

    except Exception as e:
        logger.warning(f"LLM task generation failed: {e}, using defaults")
        return _default_tasks(company_url, focus_areas)


def _default_tasks(company_url: str, focus_areas: list[str]) -> list[dict[str, Any]]:
    """Generate default research tasks as fallback."""
    return [
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


def create_research_tasks(state: AgentState, store: BaseStore = None) -> dict:
    """Generate research tasks from the parsed intent.

    Reads: company_url, user_profile, session_id
    Writes: research_tasks, approval_status

    Uses LLM to generate a detailed research plan based on extracted intent.

    Args:
        store: LangGraph-injected BaseStore for cross-session memory (LangGraph 1.0+).
    """
    logger.info("Planner: creating research tasks")

    company_url = state.get("company_url", "")
    session_id = state.get("session_id", "")
    user_profile = state.get("user_profile", {})

    # Get extracted intent from analyze_query
    intent = user_profile.get("extracted_intent", {})
    company_name = intent.get("company_name", _infer_company_name(company_url))
    focus_areas = intent.get("focus_areas", ["overview", "products", "pricing", "competitors"])
    constraints = intent.get("constraints", [])

    # Also check user preferences for additional focus areas
    prefs = user_profile.get("preferences", {})
    pref_focus = prefs.get("focus_areas", [])
    if pref_focus:
        # Merge preference focus areas (avoiding duplicates)
        focus_areas = list(dict.fromkeys(focus_areas + pref_focus))

    # Generate tasks with LLM if configured
    if is_llm_configured():
        tasks = _generate_tasks_with_llm(
            company_name=company_name,
            company_url=company_url,
            focus_areas=focus_areas,
            constraints=constraints,
        )
    else:
        logger.warning("LLM not configured, using default tasks")
        tasks = _default_tasks(company_url, focus_areas)

    # Write research plan to session memory
    memory = MemoryStore(store) if store is not None else None
    if memory and session_id:
        session_summary = {
            "query": company_url,
            "company_name": company_name,
            "phase": "planning",
            "task_count": len(tasks),
            "focus_areas": focus_areas,
            "constraints": constraints,
        }
        memory.put_session_summary(session_id, session_summary)
        logger.info(f"Planner: saved research plan to session memory")

    # Build task summary for user message
    task_summary = []
    for task in tasks:
        task_type = task.get("type", "unknown")
        target = task.get("target", "")
        task_summary.append(f"• {task_type}: {target}")
    task_list = "\n".join(task_summary)

    return {
        "research_tasks": tasks,
        "approval_status": APPROVAL_PENDING_PLAN,
        "messages": [
            AIMessage(
                content=(
                    f"Research plan created with {len(tasks)} tasks:\n\n"
                    f"{task_list}\n\n"
                    "Awaiting your approval to proceed with research."
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
