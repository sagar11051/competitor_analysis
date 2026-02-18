# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**crawl-agent** — an AI-powered competitive intelligence tool that analyzes a company's website and generates structured reports covering company profile, top competitors, detailed competitor analyses, and strategic insights.

**Stack:** Python 3.12+, FastAPI, LangGraph 1.0+, LangChain, OVH LLM (Mistral-Nemo), Tavily, Crawl4AI, Pydantic

## Package Manager

This project uses **uv** as the package manager. Use `uv run` to execute Python files (it ensures the correct virtual environment and dependencies are used).

## Commands

### Install dependencies
```bash
uv sync --extra dev
```

### Run interactive CLI (recommended entry point)
```bash
uv run python -m src.agents.cli
uv run python -m src.agents.cli --url https://stripe.com
```

### Run API server
```bash
uv run uvicorn src.app:app --host 0.0.0.0 --port 5000 --reload
```

### Run tests
```bash
uv run pytest tests/ -v
```

### Open LangGraph Studio
```bash
langgraph dev
```

## Required Environment Variables

Set in `.env` at the project root:
- `OVH_ENDPOINT` — OVH AI endpoint URL
- `OVH_API_KEY` — OVH AI API key
- `TAVILY_API_KEY` — Tavily search API key
- `FIRECRAWL_API_KEY` — Firecrawl API key
- `GEMINI_API_KEY` — Google Gemini API key (legacy workflow only)

## Architecture

The new multi-agent system uses a **LangGraph StateGraph** with three agent subgraphs and three HITL gates:

```
planner → [Gate 1] → researcher → [Gate 2] → strategist → [Gate 3] → END
```

### Agent subgraphs

1. **Planner** ([src/agents/planner.py](src/agents/planner.py)) — Extracts intent from user message via LLM, generates a list of research tasks. Sets `approval_status = pending_plan_approval`.
2. **Researcher** ([src/agents/researcher.py](src/agents/researcher.py)) — Executes research tasks using Tavily (search) and Crawl4AI (scraping). Sets `approval_status = pending_research_approval`.
3. **Strategist** ([src/agents/strategist.py](src/agents/strategist.py)) — Synthesizes research into competitor analyses and strategic recommendations via LLM. Sets `approval_status = pending_strategy_approval`.

### Key modules

- [src/agents/state.py](src/agents/state.py) — `AgentState` TypedDict with 12 fields + 7 `APPROVAL_*` constants.
- [src/agents/graph.py](src/agents/graph.py) — Main graph with HITL gates, `create_session()`, `resume_session()`, `get_session_state()`.
- [src/agents/cli.py](src/agents/cli.py) — Interactive terminal CLI for the full HITL workflow.
- [src/agents/llm.py](src/agents/llm.py) — LLM helpers: `generate()`, `generate_json()`, `get_chat_model()`, `is_llm_configured()`.
- [src/agents/prompts.py](src/agents/prompts.py) — Prompt templates for all three agents.
- [src/memory/store.py](src/memory/store.py) — `MemoryStore` wrapping `InMemoryStore` for cross-session memory.
- [src/tools/tavily_search.py](src/tools/tavily_search.py) — Tavily search wrapper.
- [src/tools/web_scraper.py](src/tools/web_scraper.py) — Crawl4AI scraping wrapper.
- [src/app.py](src/app.py) — FastAPI with `/sessions`, `/sessions/{id}/message`, `/sessions/{id}/state`, and legacy `/analyze`.
- [langgraph.json](langgraph.json) — LangGraph Studio config pointing at `get_compiled_graph`.

### Patterns

- LLM calls go through `ovhllm.py` → `OVHLLM` class → `get_chat_model()` → returns `ChatOpenAI`.
- `src/agents/llm.py` wraps `ovhllm.py` with `generate()`, `generate_json()`, and JSON fence-stripping.
- Every agent node has an LLM path and a graceful fallback for when LLM is not configured.
- Graph uses `MemorySaver` checkpointer + `InMemoryStore` for memory, compiled with `interrupt_before` each gate node.
- Legacy `src/workflow.py` (Gemini + Firecrawl) is kept for the `/analyze` backward-compat endpoint.

### Known test notes

- `test_ovhllm_is_configured` fails when real OVH creds are in `.env` (empty-string test params fall through to settings) — pre-existing, not a regression.
- Run `uv run pytest tests/ -v` → should see 140+ passing tests.
