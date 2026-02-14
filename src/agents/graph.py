"""Main graph composing Planner, Researcher, and Strategist subgraphs with HITL gates.

This module builds the top-level StateGraph that:
1. Composes all 3 agent subgraphs
2. Implements 3 human-in-the-loop gates via interrupt_before
3. Routes based on approval_status for approve/revise flows
4. Uses MemorySaver for checkpointing
5. Uses InMemoryStore for cross-session memory

Day 4 + Day 5 implementation.
"""

from typing import Literal
import uuid

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from src.agents.planner import build_planner_subgraph
from src.agents.researcher import build_researcher_subgraph
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
from src.agents.strategist import build_strategist_subgraph
from src.memory import get_memory_store
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Module-level checkpointer (shared across sessions)
checkpointer = MemorySaver()

# Module-level memory store (shared across sessions)
memory_store = get_memory_store()


def _get_initial_state(
    company_url: str,
    session_id: str | None = None,
    user_profile: dict | None = None,
) -> AgentState:
    """Create a properly initialized AgentState for a new session."""
    return {
        "messages": [],
        "session_id": session_id or str(uuid.uuid4()),
        "user_profile": user_profile or {},
        "research_tasks": [],
        "research_results": [],
        "strategy_drafts": [],
        "approval_status": "",
        "company_url": company_url,
        "company_profile": None,
        "competitors": [],
        "competitor_analyses": [],
        "strategic_insights": None,
    }


# -----------------------------------------------------------------------------
# HITL Gate Nodes
# -----------------------------------------------------------------------------


def hitl_gate_1(state: AgentState) -> dict:
    """HITL Gate 1: Check plan approval and route accordingly.

    This node runs AFTER the user has had a chance to approve/modify.
    The graph interrupts BEFORE this node, user sends approval via message.
    """
    logger.info("HITL Gate 1: Checking plan approval")
    status = state.get("approval_status", "")

    # If still pending, the user approved (via /message endpoint updating status)
    # This node just logs and passes through - routing is done by conditional edge
    logger.info(f"HITL Gate 1: Current status = {status}")

    return {}


def hitl_gate_2(state: AgentState) -> dict:
    """HITL Gate 2: Check research approval and route accordingly."""
    logger.info("HITL Gate 2: Checking research approval")
    status = state.get("approval_status", "")
    logger.info(f"HITL Gate 2: Current status = {status}")
    return {}


def hitl_gate_3(state: AgentState) -> dict:
    """HITL Gate 3: Check strategy approval and route accordingly."""
    logger.info("HITL Gate 3: Checking strategy approval")
    status = state.get("approval_status", "")
    logger.info(f"HITL Gate 3: Current status = {status}")
    return {}


# -----------------------------------------------------------------------------
# Conditional Edge Routing Functions
# -----------------------------------------------------------------------------


def route_after_gate_1(
    state: AgentState,
) -> Literal["researcher", "planner", "__end__"]:
    """Route after HITL Gate 1 based on approval status.

    - approved_plan → proceed to researcher
    - revision_requested → go back to planner
    - otherwise → end (error state)
    """
    status = state.get("approval_status", "")

    if status == APPROVAL_APPROVED_PLAN:
        logger.info("Gate 1: Plan approved, proceeding to researcher")
        return "researcher"
    elif status == APPROVAL_REVISION_REQUESTED:
        logger.info("Gate 1: Revision requested, returning to planner")
        return "planner"
    else:
        logger.warning(f"Gate 1: Unexpected status '{status}', ending")
        return "__end__"


def route_after_gate_2(
    state: AgentState,
) -> Literal["strategist", "researcher", "__end__"]:
    """Route after HITL Gate 2 based on approval status.

    - approved_research → proceed to strategist
    - revision_requested → go back to researcher
    - otherwise → end (error state)
    """
    status = state.get("approval_status", "")

    if status == APPROVAL_APPROVED_RESEARCH:
        logger.info("Gate 2: Research approved, proceeding to strategist")
        return "strategist"
    elif status == APPROVAL_REVISION_REQUESTED:
        logger.info("Gate 2: Revision requested, returning to researcher")
        return "researcher"
    else:
        logger.warning(f"Gate 2: Unexpected status '{status}', ending")
        return "__end__"


def route_after_gate_3(
    state: AgentState,
) -> Literal["strategist", "__end__"]:
    """Route after HITL Gate 3 based on approval status.

    - approved_strategy → end (final report ready)
    - revision_requested → go back to strategist
    - otherwise → end
    """
    status = state.get("approval_status", "")

    if status == APPROVAL_APPROVED_STRATEGY:
        logger.info("Gate 3: Strategy approved, finalizing report")
        return "__end__"
    elif status == APPROVAL_REVISION_REQUESTED:
        logger.info("Gate 3: Revision requested, returning to strategist")
        return "strategist"
    else:
        logger.info(f"Gate 3: Status '{status}', ending")
        return "__end__"


# -----------------------------------------------------------------------------
# Main Graph Builder
# -----------------------------------------------------------------------------


def build_main_graph() -> StateGraph:
    """Build the main graph composing all 3 subgraphs with HITL gates.

    Graph structure:
        planner → hitl_gate_1 → researcher → hitl_gate_2 → strategist → hitl_gate_3 → END

    With conditional edges allowing revision loops back to earlier stages.

    Returns an UNCOMPILED StateGraph. Call .compile() with checkpointer and
    interrupt_before to get a runnable graph.
    """
    graph = StateGraph(AgentState)

    # Add subgraphs as nodes (compile them first)
    planner_subgraph = build_planner_subgraph().compile()
    researcher_subgraph = build_researcher_subgraph().compile()
    strategist_subgraph = build_strategist_subgraph().compile()

    graph.add_node("planner", planner_subgraph)
    graph.add_node("researcher", researcher_subgraph)
    graph.add_node("strategist", strategist_subgraph)

    # Add HITL gate nodes
    graph.add_node("hitl_gate_1", hitl_gate_1)
    graph.add_node("hitl_gate_2", hitl_gate_2)
    graph.add_node("hitl_gate_3", hitl_gate_3)

    # Set entry point
    graph.set_entry_point("planner")

    # Linear edges: planner → gate1 → researcher → gate2 → strategist → gate3
    graph.add_edge("planner", "hitl_gate_1")
    graph.add_edge("researcher", "hitl_gate_2")
    graph.add_edge("strategist", "hitl_gate_3")

    # Conditional edges from gates
    graph.add_conditional_edges(
        "hitl_gate_1",
        route_after_gate_1,
        {
            "researcher": "researcher",
            "planner": "planner",
            "__end__": END,
        },
    )

    graph.add_conditional_edges(
        "hitl_gate_2",
        route_after_gate_2,
        {
            "strategist": "strategist",
            "researcher": "researcher",
            "__end__": END,
        },
    )

    graph.add_conditional_edges(
        "hitl_gate_3",
        route_after_gate_3,
        {
            "strategist": "strategist",
            "__end__": END,
        },
    )

    return graph


def get_compiled_graph():
    """Get a compiled graph with checkpointer, store, and HITL interrupts configured.

    Returns a runnable CompiledStateGraph that:
    - Interrupts before each HITL gate node for human approval
    - Uses MemorySaver for state checkpointing
    - Uses InMemoryStore for cross-session memory
    """
    graph = build_main_graph()

    return graph.compile(
        checkpointer=checkpointer,
        store=memory_store.raw_store,
        interrupt_before=["hitl_gate_1", "hitl_gate_2", "hitl_gate_3"],
    )


# -----------------------------------------------------------------------------
# Session Management Helpers
# -----------------------------------------------------------------------------


def create_session(
    company_url: str,
    user_profile: dict | None = None,
    initial_query: str | None = None,
) -> tuple[str, dict]:
    """Create a new analysis session and start the graph.

    Args:
        company_url: Target company URL to analyze
        user_profile: Optional user context dict
        initial_query: Optional initial message from user

    Returns:
        (session_id, current_state) tuple
    """
    session_id = str(uuid.uuid4())
    state = _get_initial_state(company_url, session_id, user_profile)

    if initial_query:
        state["messages"] = [HumanMessage(content=initial_query)]

    # Get the compiled graph
    compiled = get_compiled_graph()

    # Run until first interrupt
    config = {"configurable": {"thread_id": session_id}}
    result = compiled.invoke(state, config)

    return session_id, result


def resume_session(session_id: str, approval_action: str, user_message: str = "") -> dict:
    """Resume a session after user provides approval or feedback.

    Args:
        session_id: The session to resume
        approval_action: One of "approve", "modify", "reject"
        user_message: Optional message content from user

    Returns:
        Updated state after graph execution
    """
    compiled = get_compiled_graph()
    config = {"configurable": {"thread_id": session_id}}

    # Get current state
    current_state = compiled.get_state(config)
    if not current_state or not current_state.values:
        raise ValueError(f"Session {session_id} not found")

    state = dict(current_state.values)
    current_status = state.get("approval_status", "")

    # Determine new status based on action and current status
    new_status = _resolve_approval_action(current_status, approval_action)
    state["approval_status"] = new_status

    # Add user message if provided
    if user_message:
        messages = list(state.get("messages", []))
        messages.append(HumanMessage(content=user_message))
        state["messages"] = messages

    # Update state and resume
    compiled.update_state(config, state)

    # Resume execution (None input continues from interrupt)
    result = compiled.invoke(None, config)

    return result


def get_session_state(session_id: str) -> dict | None:
    """Get the current state of a session.

    Args:
        session_id: The session ID

    Returns:
        Current state dict or None if session not found
    """
    compiled = get_compiled_graph()
    config = {"configurable": {"thread_id": session_id}}

    snapshot = compiled.get_state(config)
    if snapshot and snapshot.values:
        return dict(snapshot.values)
    return None


def _resolve_approval_action(current_status: str, action: str) -> str:
    """Resolve the new approval status based on current status and user action.

    Args:
        current_status: Current approval_status value
        action: User action - "approve", "modify", or "reject"

    Returns:
        New approval_status value
    """
    if action == "approve":
        if current_status == APPROVAL_PENDING_PLAN:
            return APPROVAL_APPROVED_PLAN
        elif current_status == APPROVAL_PENDING_RESEARCH:
            return APPROVAL_APPROVED_RESEARCH
        elif current_status == APPROVAL_PENDING_STRATEGY:
            return APPROVAL_APPROVED_STRATEGY
    elif action in ("modify", "reject"):
        return APPROVAL_REVISION_REQUESTED

    # Default: keep current status
    return current_status
