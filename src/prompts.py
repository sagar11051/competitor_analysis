class DeveloperToolsPrompts:
    """Collection of prompts for analyzing developer tools and technologies"""

    # Tool extraction prompts
    TOOL_EXTRACTION_SYSTEM = """You are a tech researcher. Extract specific tool, library, platform, or service names from articles.
                            Focus on actual products/tools that developers can use, not general concepts or features."""

    @staticmethod
    def tool_extraction_user(query: str, content: str) -> str:
        return f"""Query: {query}
                Article Content: {content}

                Extract a list of specific tool/service names mentioned in this content that are relevant to "{query}".

                Rules:
                - Only include actual product names, not generic terms
                - Focus on tools developers can directly use/implement
                - Include both open source and commercial options
                - Limit to the 5 most relevant tools
                - Return just the tool names, one per line, no descriptions

                Example format:
                Supabase
                PlanetScale
                Railway
                Appwrite
                Nhost"""

    # Company/Tool analysis prompts
    TOOL_ANALYSIS_SYSTEM = """You are analyzing developer tools and programming technologies. 
                            Focus on extracting information relevant to programmers and software developers. 
                            Pay special attention to programming languages, frameworks, APIs, SDKs, and development workflows."""

    @staticmethod
    def tool_analysis_user(company_name: str, content: str) -> str:
        return f"""Company/Tool: {company_name}
                Website Content: {content[:2500]}

                Analyze this content from a developer's perspective and provide:
                - pricing_model: One of "Free", "Freemium", "Paid", "Enterprise", or "Unknown"
                - is_open_source: true if open source, false if proprietary, null if unclear
                - tech_stack: List of programming languages, frameworks, databases, APIs, or technologies supported/used
                - description: Brief 1-sentence description focusing on what this tool does for developers
                - api_available: true if REST API, GraphQL, SDK, or programmatic access is mentioned
                - language_support: List of programming languages explicitly supported (e.g., Python, JavaScript, Go, etc.)
                - integration_capabilities: List of tools/platforms it integrates with (e.g., GitHub, VS Code, Docker, AWS, etc.)

                Focus on developer-relevant features like APIs, SDKs, language support, integrations, and development workflows."""

    # Recommendation prompts
    RECOMMENDATIONS_SYSTEM = """You are a senior software engineer providing quick, concise tech recommendations. 
                            Keep responses brief and actionable - maximum 3-4 sentences total."""

    @staticmethod
    def recommendations_user(query: str, company_data: str) -> str:
        return f"""Developer Query: {query}
                Tools/Technologies Analyzed: {company_data}

                Provide a brief recommendation (3-4 sentences max) covering:
                - Which tool is best and why
                - Key cost/pricing consideration
                - Main technical advantage

                Be concise and direct - no long explanations needed."""

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