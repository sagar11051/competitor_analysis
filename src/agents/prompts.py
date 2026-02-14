"""Prompt templates for the 3 agent subgraphs.

Each section provides system and user prompt templates used by the
Planner, Research Orchestrator, and Strategy Builder agents.
"""

# ── Planner Agent ────────────────────────────────────────────────────

PLANNER_SYSTEM = """\
You are a competitive intelligence planning agent.  Your job is to analyze
the user's request and produce a structured JSON research plan.

Always respond with valid JSON — no markdown fences, no extra text."""

PLANNER_ANALYZE_QUERY = """\
Analyze the following request and extract:
- company_url: the URL of the target company
- company_name: inferred company name
- focus_areas: list of research focus areas (e.g. pricing, features, market position)
- constraints: any constraints the user specified

User request:
{user_message}

Company URL provided: {company_url}

Respond with JSON:
{{"company_url": "...", "company_name": "...", "focus_areas": [...], "constraints": [...]}}"""

PLANNER_CREATE_TASKS = """\
Given the following analysis intent, create a list of concrete research tasks.

Company: {company_name} ({company_url})
Focus areas: {focus_areas}
Constraints: {constraints}

Each task should have:
- type: one of "company_profile", "competitor_discovery", "competitor_deep_dive"
- target: what to research (company name or URL)
- url: specific URL to scrape, or null if search-based
- focus_areas: list of specific things to look for

Respond with JSON:
{{"tasks": [{{...}}, ...]}}"""

# ── Research Orchestrator ────────────────────────────────────────────

RESEARCHER_SYSTEM = """\
You are a competitive intelligence research agent.  You analyze raw data
from web searches and scraped pages to extract structured competitor
intelligence.

Always respond with valid JSON — no markdown fences, no extra text."""

RESEARCHER_EXTRACT_PROFILE = """\
Given the following scraped content from {url}, extract a company profile.

Content:
{content}

Extract as JSON:
{{
  "name": "company name",
  "website": "url",
  "description": "1-2 sentence summary",
  "products": ["product1", ...],
  "pricing_model": "freemium/subscription/etc or unknown",
  "target_market": "who they serve",
  "key_features": ["feature1", ...],
  "team_size": "approximate or unknown",
  "funding": "known funding info or unknown"
}}"""

RESEARCHER_RANK_COMPETITORS = """\
Given the following search results about competitors of {company_name},
identify and rank the top competitors.

Search results:
{search_results}

Return a JSON list of the top 5 competitors:
{{
  "competitors": [
    {{
      "name": "competitor name",
      "url": "website url",
      "relevance": "why this is a competitor",
      "priority": 1
    }},
    ...
  ]
}}"""

RESEARCHER_SUMMARIZE_CHUNK = """\
Summarize the following content chunk from {url} focusing on competitive
intelligence — products, features, pricing, market position, strengths,
and weaknesses.

Content chunk ({chunk_index}/{total_chunks}):
{chunk_content}

Provide a concise summary (3-5 sentences) as JSON:
{{"summary": "...", "key_points": [...]}}"""

# ── Strategy Builder ─────────────────────────────────────────────────

STRATEGIST_SYSTEM = """\
You are a competitive strategy analyst.  You synthesize research findings
into actionable strategic recommendations.

Always respond with valid JSON — no markdown fences, no extra text."""

STRATEGIST_ANALYZE = """\
Analyze the following research data and produce a competitive analysis.

Target company:
{company_profile}

Competitor analyses:
{competitor_analyses}

For each competitor, assess:
- strengths: what they do well
- weaknesses: where they fall short
- market_position: how they are positioned
- threat_level: high/medium/low

Respond with JSON:
{{
  "analyses": [
    {{
      "competitor": "name",
      "strengths": [...],
      "weaknesses": [...],
      "market_position": "...",
      "threat_level": "high|medium|low"
    }},
    ...
  ]
}}"""

STRATEGIST_GENERATE = """\
Based on the following competitive analysis, generate strategic
recommendations for {company_name}.

Company profile:
{company_profile}

Competitive analysis:
{competitive_analysis}

Generate strategic insights as JSON:
{{
  "feature_gaps": ["features competitors have that {company_name} lacks"],
  "opportunities": ["market gaps and growth opportunities"],
  "positioning_suggestions": ["how to differentiate"],
  "fundraising_intel": ["competitive fundraising intelligence"],
  "summary": "2-3 paragraph executive summary"
}}"""
