"""AgentState schema for the multi-agent competitive analysis system.

Defines the shared state that flows through the main graph and all subgraphs.
See docs/PRD.md Section 4 for the full specification.
"""

from typing import Annotated, Optional

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


# Valid values for approval_status
APPROVAL_PENDING_PLAN = "pending_plan_approval"
APPROVAL_APPROVED_PLAN = "approved_plan"
APPROVAL_PENDING_RESEARCH = "pending_research_approval"
APPROVAL_APPROVED_RESEARCH = "approved_research"
APPROVAL_PENDING_STRATEGY = "pending_strategy_approval"
APPROVAL_APPROVED_STRATEGY = "approved_strategy"
APPROVAL_REVISION_REQUESTED = "revision_requested"


class AgentState(TypedDict):
    """Shared state for the competitive analysis agent pipeline.

    Fields:
        messages: Conversation history (auto-merged via add_messages reducer).
        session_id: Unique identifier for this analysis session.
        user_profile: User context — {role, company, preferences}.
        research_tasks: Planner output — [{type, target, url, focus_areas}].
        research_results: Research output — [{competitor, data, source, timestamp}].
        strategy_drafts: Strategy output — [{feature_gaps, opportunities, ...}].
        approval_status: Current HITL gate status (see APPROVAL_* constants).
        company_url: Target company URL to analyze.
        company_profile: Extracted company profile dict (or None).
        competitors: List of identified competitor dicts.
        competitor_analyses: Detailed competitor analysis dicts.
        strategic_insights: Final strategic insights dict (or None).
    """

    # Conversation
    messages: Annotated[list[BaseMessage], add_messages]
    session_id: str

    # User context
    user_profile: dict

    # Workflow tracking
    research_tasks: list[dict]
    research_results: list[dict]
    strategy_drafts: list[dict]
    approval_status: str

    # Data
    company_url: str
    company_profile: Optional[dict]
    competitors: list[dict]
    competitor_analyses: list[dict]
    strategic_insights: Optional[dict]
