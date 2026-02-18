"""Multi-agent competitive analysis system — agent subgraphs.

Exports:
    - State schema and approval status constants
    - Subgraph builders for Planner, Researcher, Strategist
    - LLM utilities for agent nodes
"""

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
from src.agents.planner import build_planner_subgraph
from src.agents.researcher import build_researcher_subgraph
from src.agents.strategist import build_strategist_subgraph
from src.agents.llm import (
    generate,
    generate_json,
    get_chat_model,
    is_llm_configured,
    parse_json_response,
)

__all__ = [
    # State
    "AgentState",
    "APPROVAL_PENDING_PLAN",
    "APPROVAL_APPROVED_PLAN",
    "APPROVAL_PENDING_RESEARCH",
    "APPROVAL_APPROVED_RESEARCH",
    "APPROVAL_PENDING_STRATEGY",
    "APPROVAL_APPROVED_STRATEGY",
    "APPROVAL_REVISION_REQUESTED",
    # Subgraph builders
    "build_planner_subgraph",
    "build_researcher_subgraph",
    "build_strategist_subgraph",
    # LLM utilities
    "get_chat_model",
    "generate",
    "generate_json",
    "parse_json_response",
    "is_llm_configured",
]
