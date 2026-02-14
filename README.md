# AI Startup Competitive Intelligence Analyzer

This project provides automated, AI-powered competitive intelligence for startups and developer tool companies. By analyzing a company website, it generates a comprehensive report covering the company profile, top competitors, detailed competitor analyses, and actionable strategic insights.

## What Information Does the Analysis Provide?

After running an analysis, the tool outputs the following:

### 1. Company Profile
A structured summary of the target company, including:
- **name**: Company name
- **website**: Official website URL
- **business_model**: Business model (e.g., SaaS, Open Source, Marketplace)
- **target_market**: Main customer or user segment
- **key_services**: List of main products/services
- **tech_stack**: Technologies, frameworks, or languages used
- **description**: 1-2 sentence summary of the company

### 2. Top Competitors
A ranked list of the most relevant competitors, each with:
- **name**: Competitor name
- **website**: Competitor website
- **description**: 1-2 sentence summary
- **relevance_score**: Relevance (0-1, higher is more relevant)

### 3. Competitor Analyses (Top 3)
For the top 3 competitors, a deep-dive analysis is provided, including:
- **name**: Competitor name
- **website**: URL
- **business_model**: Business model
- **target_market**: Target market
- **key_services**: List of main services/products
- **tech_stack**: Technologies used
- **description**: 1-2 sentence summary
- **features**: List of notable features
- **pricing**: Pricing information
- **integration_capabilities**: Integrations with other tools/platforms
- **messaging**: Key marketing or product messaging
- **target_audience**: Intended users/customers
- **value_propositions**: Unique value points
- **infrastructure**: Infrastructure details
- **development_patterns**: Notable development practices
- **team_size**: Team size (number, range, or unknown)
- **funding_history**: Funding rounds or history
- **market_expansion_signals**: Signs of market growth or expansion
- **blog_topics**: Main blog topics
- **seo_keywords**: SEO keywords targeted
- **thought_leadership_themes**: Themes in thought leadership content

### 4. Strategic Insights
Actionable recommendations and intelligence, including:
- **feature_gaps**: Features missing in the target company compared to competitors
- **opportunities**: Market or product opportunities
- **positioning_suggestions**: Suggestions for market positioning
- **fundraising_intel**: Fundraising tips or intelligence

## Output Format
- All fields are robust to missing data: if information is not found, fields may be `None`, an empty string, or an empty list.
- Lists may contain strings or numbers, and some fields may be a string, a list, or `None` depending on the data found.

## How It Works
1. **Company Analysis**: Scrapes and analyzes the target company's website to extract a structured profile.
2. **Competitor Search**: Identifies and ranks relevant competitors using web search and AI analysis.
3. **Competitor Analysis**: Scrapes and analyzes the top competitors' websites for detailed comparison.
4. **Insight Generation**: Synthesizes all data to generate actionable strategic insights.

## Example Usage
Run the tool and enter a company website URL when prompted. The tool will output a competitive intelligence report with all the information described above.

---

## Project Architecture

This project uses a **LangGraph-powered multi-agent system** with sophisticated workflow management:

### Agent Pipeline
```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Planner   │────▶│  Researcher  │────▶│  Strategist │
│   Agent     │     │    Agent     │     │    Agent    │
└─────────────┘     └──────────────┘     └─────────────┘
       │                   │                    │
       ▼                   ▼                    ▼
   HITL Gate 1        HITL Gate 2         HITL Gate 3
   (Plan Approval)   (Research Approval)  (Strategy Approval)
```

### Core Features

#### Human-in-the-Loop (HITL) Workflow
- **3 approval gates** for plan, research, and strategy phases
- Users can approve, modify, or reject at each stage
- Revision loops allow iterating on any phase

#### Persistent Memory Layer (Day 5)
Cross-session memory using LangGraph's `InMemoryStore`:

| Namespace | Purpose |
|-----------|---------|
| `users/{id}/profile` | User context (role, company, industry) |
| `users/{id}/preferences` | Analysis preferences (focus areas, depth) |
| `sessions/{id}/summary` | Session memory (query, findings, decisions) |
| `competitors/{name}/profile` | Cached competitor data for faster lookups |

#### Tool Integration
- **Tavily Search** - AI-powered web search for competitor discovery
- **Crawl4AI** - Async web scraping with intelligent content chunking
- **Google Gemini 1.5 Flash** - LLM for analysis and synthesis

### Tech Stack
- **Python 3.12+**
- **LangGraph** - Multi-agent orchestration with state management
- **LangChain** - LLM integration and tool abstraction
- **FastAPI** - REST API server
- **Pydantic** - Data validation and serialization
- **Firecrawl** - Web scraping service

---

## Development Progress

| Day | Milestone | Description |
|-----|-----------|-------------|
| 1 | Foundation | Project setup, config, logger, dependencies |
| 2 | State Schema | AgentState TypedDict, agent subgraph skeletons |
| 3 | Tools | Tavily Search + Crawl4AI integration |
| 4 | HITL Workflow | Main graph with human-in-the-loop breakpoints |
| 5 | Memory Layer | LangGraph Store for cross-session persistence |

---

## Quick Start

```bash
# Install dependencies
uv sync

# Set environment variables
cp .env.example .env
# Edit .env with your API keys

# Run CLI (interactive mode)
uv run python main.py

# Run API server
uv run uvicorn src.app:app --host 0.0.0.0 --port 5000 --reload
```

## Running Tests

```bash
# Run all tests
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/test_memory.py -v
```

---

For more details, see the `src/models.py` file for the full data structure and field definitions.
