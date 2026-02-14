"""FastAPI application with session-based API for competitive analysis.

Endpoints:
- POST /sessions - Create new analysis session
- POST /sessions/{id}/message - Send message (query or approval/feedback)
- GET /sessions/{id}/state - Get current session state and approval status
- POST /analyze - Legacy endpoint (backward compatibility)
- GET / - Health check
"""

from typing import Literal, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.agents.graph import create_session, get_session_state, resume_session
from src.utils.logger import get_logger

# Legacy import for backward compatibility
from .workflow import Workflow

logger = get_logger(__name__)

app = FastAPI(
    title="Competitive Analysis API",
    description="Multi-agent competitive intelligence system with HITL workflows",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Legacy workflow for /analyze endpoint
workflow = Workflow()


# -----------------------------------------------------------------------------
# Request/Response Models
# -----------------------------------------------------------------------------


class CreateSessionRequest(BaseModel):
    """Request body for POST /sessions."""

    user_id: Optional[str] = None
    company_url: str
    query: Optional[str] = None


class CreateSessionResponse(BaseModel):
    """Response body for POST /sessions."""

    session_id: str
    status: str
    approval_status: str
    message: str


class MessageRequest(BaseModel):
    """Request body for POST /sessions/{id}/message."""

    content: Optional[str] = None
    action: Literal["approve", "modify", "reject"]


class MessageResponse(BaseModel):
    """Response body for POST /sessions/{id}/message."""

    status: str
    stage: str
    approval_status: str
    message: str


class SessionStateResponse(BaseModel):
    """Response body for GET /sessions/{id}/state."""

    session_id: str
    approval_status: str
    company_url: str
    research_tasks_count: int
    research_results_count: int
    strategy_drafts_count: int
    has_strategic_insights: bool
    messages_count: int


class AnalyzeRequest(BaseModel):
    """Request body for POST /analyze (legacy)."""

    company_url: str


# -----------------------------------------------------------------------------
# Session Endpoints (Day 4)
# -----------------------------------------------------------------------------


@app.post("/sessions", response_model=CreateSessionResponse)
async def create_analysis_session(request: CreateSessionRequest):
    """Create a new analysis session.

    Starts the analysis pipeline for the given company URL.
    The graph will run until the first HITL gate (plan approval).
    """
    logger.info(f"Creating session for {request.company_url}")

    try:
        user_profile = {"user_id": request.user_id} if request.user_id else {}

        session_id, state = create_session(
            company_url=request.company_url,
            user_profile=user_profile,
            initial_query=request.query,
        )

        approval_status = state.get("approval_status", "")
        messages = state.get("messages", [])
        last_message = messages[-1].content if messages else "Session created"

        return CreateSessionResponse(
            session_id=session_id,
            status="processing",
            approval_status=approval_status,
            message=last_message,
        )
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sessions/{session_id}/message", response_model=MessageResponse)
async def send_message(session_id: str, request: MessageRequest):
    """Send a message to an existing session.

    Use this to approve/modify/reject at HITL gates.
    The graph will resume and run until the next interrupt point.
    """
    logger.info(f"Message for session {session_id}: action={request.action}")

    try:
        state = resume_session(
            session_id=session_id,
            approval_action=request.action,
            user_message=request.content or "",
        )

        approval_status = state.get("approval_status", "")
        messages = state.get("messages", [])
        last_message = messages[-1].content if messages else "Processing..."

        # Determine current stage
        stage = _determine_stage(approval_status)

        return MessageResponse(
            status="processing",
            stage=stage,
            approval_status=approval_status,
            message=last_message,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to process message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions/{session_id}/state", response_model=SessionStateResponse)
async def get_state(session_id: str):
    """Get the current state of a session."""
    logger.info(f"Getting state for session {session_id}")

    state = get_session_state(session_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    return SessionStateResponse(
        session_id=state.get("session_id", session_id),
        approval_status=state.get("approval_status", ""),
        company_url=state.get("company_url", ""),
        research_tasks_count=len(state.get("research_tasks", [])),
        research_results_count=len(state.get("research_results", [])),
        strategy_drafts_count=len(state.get("strategy_drafts", [])),
        has_strategic_insights=state.get("strategic_insights") is not None,
        messages_count=len(state.get("messages", [])),
    )


def _determine_stage(approval_status: str) -> str:
    """Determine the current stage based on approval status."""
    if "plan" in approval_status:
        return "planning"
    elif "research" in approval_status:
        return "research"
    elif "strategy" in approval_status:
        return "strategy"
    else:
        return "unknown"


# -----------------------------------------------------------------------------
# Legacy Endpoints
# -----------------------------------------------------------------------------


@app.post("/analyze")
async def analyze(request: AnalyzeRequest):
    """Legacy endpoint for one-shot analysis (no HITL).

    Kept for backward compatibility with existing clients.
    """
    company_url = request.company_url
    try:
        result = workflow.run(company_url)

        def model_to_dict(obj):
            if hasattr(obj, "model_dump"):
                return obj.model_dump()
            if isinstance(obj, list):
                return [model_to_dict(i) for i in obj]
            return obj

        response = {
            "company_profile": model_to_dict(result["company_profile"]),
            "competitors": model_to_dict(result["competitors"]),
            "competitor_analyses": model_to_dict(result["competitor_analyses"]),
            "strategic_insights": model_to_dict(result["strategic_insights"]),
            "analysis_report": result["analysis_report"],
        }
        return response
    except Exception as e:
        return {"error": str(e)}


@app.get("/")
async def index():
    """Health check endpoint."""
    return {
        "message": "Competitive Analysis API is running.",
        "version": "0.2.0",
        "endpoints": {
            "sessions": "POST /sessions",
            "message": "POST /sessions/{id}/message",
            "state": "GET /sessions/{id}/state",
            "legacy": "POST /analyze",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.app:app", host="0.0.0.0", port=5000, reload=True) 