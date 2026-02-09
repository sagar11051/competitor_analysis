# Product Requirements Document: Multi-Agent Competitive Analysis System

## 1. Overview

A LangGraph-based multi-agent system that enables company consultants to conduct competitive analysis through persistent chat sessions with intelligent orchestration, memory, and human-in-the-loop controls.

**Goal:** Demonstration-quality system showcasing multi-agent orchestration, persistent memory, and human-in-the-loop workflows in a clean, testable architecture.

**LLM:** OVH Mistral-Nemo via OpenAI-compatible API (see `ovhllm.py`)
**Tools:** Tavily Search (web discovery), Crawl4AI (deep web scraping)
**Framework:** LangGraph 0.5+ with StateGraph, subgraphs, checkpointing, and Store

---

## 2. System Architecture

```
                         ┌─────────────────────────┐
                         │     FastAPI / CLI        │
                         │   Session Management     │
                         └────────┬────────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────────┐
                    │        MAIN GRAPH            │
                    │   (StateGraph + Checkpointer)│
                    │                              │
                    │  ┌────────────────────────┐  │
                    │  │   1. PLANNER AGENT     │  │
                    │  │   - Analyze user query  │  │
                    │  │   - Create research plan│  │
                    │  │   - Define tasks        │  │
                    │  └──────────┬─────────────┘  │
                    │             │                 │
                    │      ╔══════╧═══════╗        │
                    │      ║  HITL GATE 1  ║        │
                    │      ║ Approve Plan   ║        │
                    │      ╚══════╤═══════╝        │
                    │             │                 │
                    │  ┌──────────▼─────────────┐  │
                    │  │ 2. RESEARCH ORCHESTRATOR│  │
                    │  │  - Dispatch agents      │  │
                    │  │  - Tavily search        │  │
                    │  │  - Crawl4AI scraping    │  │
                    │  │  - Aggregate results    │  │
                    │  └──────────┬─────────────┘  │
                    │             │                 │
                    │      ╔══════╧═══════╗        │
                    │      ║  HITL GATE 2  ║        │
                    │      ║ Review Research║        │
                    │      ╚══════╤═══════╝        │
                    │             │                 │
                    │  ┌──────────▼─────────────┐  │
                    │  │ 3. STRATEGY BUILDER    │  │
                    │  │  - Analyze findings     │  │
                    │  │  - Generate strategies  │  │
                    │  │  - Produce final report │  │
                    │  └──────────┬─────────────┘  │
                    │             │                 │
                    │      ╔══════╧═══════╗        │
                    │      ║  HITL GATE 3  ║        │
                    │      ║ Refine Strategy║        │
                    │      ╚══════╤═══════╝        │
                    │             │                 │
                    │             ▼                 │
                    │         END / Report          │
                    └─────────────────────────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │     LANGGRAPH STORE         │
                    │  ("users", user_id)         │
                    │  ("sessions", session_id)   │
                    │  ("competitors", name)      │
                    └────────────────────────────┘
```

---

## 3. Agent Specifications

### 3.1 Planner Agent (Subgraph)

**Purpose:** Orchestrate research strategy based on user query and historical memory.

**Nodes:**
| Node | Input | Output |
|------|-------|--------|
| `analyze_query` | User message + memory context | Parsed intent (company URL, focus areas, constraints) |
| `create_research_tasks` | Parsed intent | List of research task dicts: `{type, target, url, focus_areas}` |

**Behavior:**
- Reads user profile and past competitor knowledge from Store
- Generates a structured research plan
- Sets `approval_status = "pending_plan_approval"`
- Graph interrupts here — user approves plan or requests modifications

**User interactions at HITL Gate 1:**
- "Approve" → proceed to Research Orchestrator
- "Add competitor X" → re-run planner with updated tasks
- "Focus on pricing only" → re-run with narrowed scope

### 3.2 Research Orchestrator (Subgraph)

**Purpose:** Execute research tasks in parallel, aggregate findings.

**Nodes:**
| Node | Input | Output |
|------|-------|--------|
| `dispatch_research` | `research_tasks` list | Tasks prepared for execution |
| `research_agent` | Single task dict | Research result dict per competitor |
| `aggregate_results` | All research results | Merged `research_results` list |

**Tools available to research agents:**
- **Tavily Search** — discover competitors, find company information, market data
- **Crawl4AI** — deep-scrape specific URLs for detailed analysis (pricing pages, feature lists, blog content)

**Behavior:**
- Iterates over research tasks, executes each with appropriate tools
- Chunks large scraped content (15KB chunks, 2KB overlap) for LLM processing
- Aggregates and deduplicates results
- Sets `approval_status = "pending_research_approval"`

**User interactions at HITL Gate 2:**
- "Approve" → proceed to Strategy Builder
- "Dig deeper into competitor Y" → re-run research for specific competitor
- "Also look at their GitHub" → add new research task and re-run

### 3.3 Strategy Builder (Subgraph)

**Purpose:** Synthesize research into actionable competitive strategies.

**Nodes:**
| Node | Input | Output |
|------|-------|--------|
| `analyze_findings` | `research_results` + `company_profile` | Synthesized analysis |
| `generate_strategy` | Synthesized analysis | `strategy_drafts` list |

**Output fields per strategy draft:**
- `feature_gaps` — features competitors have that the target lacks
- `opportunities` — market gaps and growth opportunities
- `positioning_suggestions` — how to differentiate
- `fundraising_intel` — competitive fundraising intelligence

**User interactions at HITL Gate 3:**
- "Approve" → finalize report, save to memory
- "Elaborate on feature gaps" → re-generate with more detail
- "What about international expansion?" → add new dimension and re-analyze

---

## 4. State Schema

```python
class AgentState(TypedDict):
    # Conversation
    messages: Annotated[list[BaseMessage], add_messages]
    session_id: str

    # User context
    user_profile: dict  # {role, company, preferences}

    # Workflow tracking
    research_tasks: list[dict]      # [{type, target, url, focus_areas}]
    research_results: list[dict]    # [{competitor, data, source, timestamp}]
    strategy_drafts: list[dict]     # [{feature_gaps, opportunities, ...}]
    approval_status: str            # pending_plan | approved_plan | pending_research | ...

    # Data
    company_url: str
    company_profile: dict | None
    competitors: list[dict]
    competitor_analyses: list[dict]
    strategic_insights: dict | None
```

**`approval_status` values:**
| Status | Meaning |
|--------|---------|
| `pending_plan_approval` | Planner done, waiting for user approval of research plan |
| `approved_plan` | User approved, proceeding to research |
| `pending_research_approval` | Research done, waiting for user review |
| `approved_research` | User approved, proceeding to strategy |
| `pending_strategy_approval` | Strategy done, waiting for user refinement |
| `approved_strategy` | User approved, final report ready |
| `revision_requested` | User requested changes at any stage |

---

## 5. Memory Layer (LangGraph Store)

### Namespace Schema

| Namespace | Key | Value | Purpose |
|-----------|-----|-------|---------|
| `("users", user_id)` | `"profile"` | `{role, company, industry}` | User context for personalized analysis |
| `("users", user_id)` | `"preferences"` | `{focus_areas, depth, format}` | Remembered user preferences |
| `("sessions", session_id)` | `"summary"` | `{query, key_findings, decisions}` | Conversation memory |
| `("competitors", name)` | `"profile"` | `{website, model, market, ...}` | Cached competitor intelligence |

### Memory Access Patterns
- **Planner** reads: user preferences, existing competitor knowledge (avoids redundant research)
- **Researcher** reads: existing competitor data (updates rather than re-scrapes)
- **Strategist** reads: historical analyses for trend comparison
- **All agents** write: updated data back to Store after each stage

---

## 6. Tool Specifications

### 6.1 Tavily Search
- **Package:** `tavily-python`
- **Usage:** Competitor discovery, market research, company information lookup
- **Integration:** LangChain `TavilySearchResults` tool
- **Config:** `TAVILY_API_KEY` from environment

### 6.2 Crawl4AI
- **Package:** `crawl4ai`
- **Usage:** Deep website scraping — pricing pages, feature lists, blog content, about pages
- **Integration:** Custom LangChain tool wrapping Crawl4AI's async crawler
- **Strategy:** Scrape multiple subpages per domain (/, /about, /pricing, /product, /blog)

---

## 7. API Design

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/sessions` | Create new analysis session |
| `POST` | `/sessions/{id}/message` | Send message (initial query or approval/feedback) |
| `GET` | `/sessions/{id}/state` | Get current session state and approval status |

### Request/Response Examples

**Create session:**
```json
POST /sessions
{
  "user_id": "consultant-1",
  "company_url": "https://example.com",
  "query": "Analyze competitive landscape for this company"
}
→ {"session_id": "abc-123", "status": "processing"}
```

**Send approval:**
```json
POST /sessions/abc-123/message
{
  "content": "Looks good, proceed with research",
  "action": "approve"
}
→ {"status": "processing", "stage": "research"}
```

**Send modification:**
```json
POST /sessions/abc-123/message
{
  "content": "Also include CompetitorX in the analysis",
  "action": "modify"
}
→ {"status": "processing", "stage": "planning"}
```

---

## 8. LangGraph Studio Compatibility

- `langgraph.json` config file at project root
- Clear node naming for visualization
- Proper checkpointer (MemorySaver) for state inspection
- Conditional edges visible in graph view

---

## 9. Implementation Milestones

| Day | Milestone | Key Deliverables |
|-----|-----------|-----------------|
| 1 | PRD + Foundation | This document, config/settings, logger, new deps |
| 2 | State + Skeletons | AgentState TypedDict, 3 subgraph skeletons |
| 3 | Tools | Tavily + Crawl4AI integration, research agent implementation |
| 4 | Main Graph + HITL | Composed graph, interrupt gates, session API endpoints |
| 5 | Memory | LangGraph Store with namespaced storage |
| 6 | LLM Integration | OVH LLM wired into all agents, refined prompts |
| 7 | Polish | Studio config, CLI, integration tests, docs update |

---

## 10. Non-Goals (Scope Boundaries)

- Production-grade error handling and retries
- Authentication/authorization on API
- Database-backed persistence (InMemoryStore is sufficient)
- Frontend UI
- Rate limiting or cost tracking for LLM/API calls
- Comprehensive input validation beyond Pydantic basics
