# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**crawl-agent** — an AI-powered competitive intelligence tool that analyzes a company's website and generates structured reports covering company profile, top competitors, detailed competitor analyses, and strategic insights.

**Stack:** Python 3.12+, FastAPI, LangGraph, LangChain, Google Gemini 1.5 Flash, Firecrawl, Pydantic

## Package Manager

This project uses **uv** as the package manager. Use `uv run` to execute Python files (it ensures the correct virtual environment and dependencies are used).

## Commands

### Install dependencies
```bash
uv sync
```

### Run CLI (interactive mode)
```bash
uv run python main.py
```

### Run API server
```bash
uv run uvicorn src.app:app --host 0.0.0.0 --port 5000 --reload
```

### No test suite or linter configured
There are currently no tests, no pytest, and no linting/formatting tools (ruff, black, flake8) in this project.

## Required Environment Variables

Set in `.env` at the project root:
- `GEMINI_API_KEY` — Google Gemini API key
- `FIRECRAWL_API_KEY` — Firecrawl API key

## Architecture

The application uses a **LangGraph StateGraph** with four sequential nodes that process an `AgentState` object through a pipeline:

```
company_analysis → competitor_search → competitor_analysis → insight_generation → END
```

### Workflow nodes ([src/workflow.py](src/workflow.py))

1. **company_analysis_step** — Scrapes the target company URL (homepage, /about, /products, /blog) via Firecrawl, then sends content to Gemini to extract a `CompanyProfile`.
2. **competitor_search_step** — Uses Firecrawl search to find competitor candidates, then Gemini to rank and filter them into `CompetitorProfile` objects.
3. **competitor_analysis_step** — Scrapes top 3 competitors' websites, chunks large content (15KB chunks, 2KB overlap), summarizes each chunk, then produces `CompetitorAnalysis` objects.
4. **insight_generation_step** — Synthesizes all collected data into a `StrategicInsight` with feature gaps, opportunities, positioning suggestions, and fundraising intel.

### Key modules

- [src/models.py](src/models.py) — Pydantic models (`CompanyProfile`, `CompetitorProfile`, `CompetitorAnalysis`, `StrategicInsight`, `AgentState`). Fields use `Union[str, List[str], None]` for robustness against missing data.
- [src/prompts.py](src/prompts.py) — `CompetitiveIntelligencePrompts` class with system/user prompt templates for each workflow step.
- [src/firecrawl_service.py](src/firecrawl_service.py) — `FirecrawlService` wrapping Firecrawl API for scraping and search. Combines multiple subpages per domain.
- [src/app.py](src/app.py) — FastAPI app with single `POST /analyze` endpoint accepting `{"company_url": "..."}`.
- [main.py](main.py) — CLI entry point with interactive URL input loop.

### Patterns

- All LLM calls go through `ChatGoogleGenerativeAI(model="gemini-1.5-flash")` via LangChain.
- LLM responses are cleaned of markdown code fences (````json ... ````) before JSON parsing.
- Errors in workflow nodes are caught and printed; the pipeline continues with partial data rather than failing entirely.
- The `Workflow` class compiles the `StateGraph` in `__init__` and exposes a `run(company_url)` method returning the final `AgentState` dict.
