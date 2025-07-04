class CompetitiveIntelligencePrompts:
    """Prompts for each step of the Competitive Intelligence Analyzer workflow."""

    # Step 1: Company Analysis
    COMPANY_ANALYSIS_SYSTEM = """You are an expert business analyst. Given the content of a company's website, extract a structured profile including business model, target market, key services, tech stack, and a brief description."""

    @staticmethod
    def company_analysis_user(content: str) -> str:
        return f"""Company Website Content: {content[:2500]}

Extract the following as a JSON object:
- name
- website
- business_model
- target_market
- key_services (list)
- tech_stack (list)
- description (1-2 sentences)
"""

    # Step 2: Competitor Search
    COMPETITOR_SEARCH_SYSTEM = """You are an AI agent tasked with identifying and ranking the most relevant competitors for a company, based on its profile. Use the provided company profile to find and rank competitors. Output a list of competitors with their name, website, brief description, and a relevance score (0-1)."""

    @staticmethod
    def competitor_search_user(company_profile: str, candidates: str) -> str:
        return f"""Company Profile: {company_profile}
Potential Competitors (from search): {candidates}

Return a JSON list of up to 10 competitors. For each competitor, include:
- name
- website
- description (1-2 sentences)
- relevance_score (0-1)
"""

    # Step 3: Competitor Analysis (for top 3)
    COMPETITOR_ANALYSIS_SYSTEM = """You are an AI agent analyzing a competitor company. Given the content of a competitor's website, extract a structured profile for comparison."""

    @staticmethod
    def competitor_analysis_user(content: str) -> str:
        return f"""Competitor Website Content: {content[:2500]}

Extract the following as a JSON object:
- name
- website
- business_model
- target_market
- key_services (list)
- tech_stack (list)
- description (1-2 sentences)
- features (list)
- pricing
- integration_capabilities (list)
- messaging
- target_audience
- value_propositions (list)
- infrastructure
- development_patterns (list)
- team_size
- funding_history (list)
- market_expansion_signals (list)
- blog_topics (list)
- seo_keywords (list)
- thought_leadership_themes (list)

just output None or empty list accordingly for the fields where information is not specified in the text
"""

    # Step 4: Insight Generation
    INSIGHT_GENERATION_SYSTEM = """You are an AI strategy consultant. Given a company profile, a list of competitors, and their analyses, generate actionable strategic insights: feature gaps, opportunities, positioning suggestions, and fundraising intelligence."""

    @staticmethod
    def insight_generation_user(company_profile: str, competitors: str, analyses: str) -> str:
        return f"""Company Profile: {company_profile}
Top Competitors: {competitors}
Analyses: {analyses}

Return a JSON object with:
- feature_gaps (list)
- opportunities (list)
- positioning_suggestions (list)
- fundraising_intel (list)
"""
