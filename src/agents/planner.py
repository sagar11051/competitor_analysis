"""Planner Agent — subgraph that analyzes user queries and creates research plans.

Nodes:
    analyze_query: Parse user message into structured intent (company URL, focus areas).
    create_research_tasks: Generate a list of research task dicts from the parsed intent.

The subgraph sets approval_status to "pending_plan_approval" so the main graph
can interrupt for HITL Gate 1.

Skeleton implementation — real LLM logic added on Day 6.
"""

from langchain_core.messages import AIMessage
from langgraph.graph import END, StateGraph

from src.agents.state import APPROVAL_PENDING_PLAN, AgentState
from src.utils.logger import get_logger

logger = get_logger(__name__)


def analyze_query(state: AgentState) -> dict:
    """Parse the latest user message to extract intent.

    Reads: messages, company_url, user_profile
    Writes: company_url (confirmed/extracted)

    TODO (Day 6): LLM call to extract intent from user message + memory context.
    """
    logger.info("Planner: analyzing user query")

    # Skeleton: pass through the company_url already in state
    company_url = state.get("company_url", "")

    return {
        "company_url": company_url,
        "messages": [
            AIMessage(content=f"Analyzing competitive landscape for {company_url}...")
        ],
    }


def create_research_tasks(state: AgentState) -> dict:
    """Generate research tasks from the parsed intent.

    Reads: company_url, user_profile
    Writes: research_tasks, approval_status

    TODO (Day 6): LLM call to generate a detailed research plan.
    """
    logger.info("Planner: creating research tasks")

    company_url = state.get("company_url", "")

    # Skeleton: create a default research plan
    tasks = [
        {
            "type": "company_profile",
            "target": company_url,
            "url": company_url,
            "focus_areas": ["overview", "products", "pricing", "team"],
        },
        {
            "type": "competitor_discovery",
            "target": company_url,
            "url": None,
            "focus_areas": ["direct_competitors", "indirect_competitors"],
        },
    ]

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
