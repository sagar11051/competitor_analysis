from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, field_validator


class CompanyAnalysis(BaseModel):
    """Structured output for LLM company analysis focused on developer tools"""
    pricing_model: Union[str, List[str], None] = None  # Free, Freemium, Paid, Enterprise, Unknown
    is_open_source: Optional[bool] = None
    tech_stack: Union[List[str], str, None] = []
    description: Union[str, List[str], None] = ""
    api_available: Optional[bool] = None
    language_support: Union[List[str], str, None] = []
    integration_capabilities: Union[List[str], str, None] = []

    @field_validator("pricing_model", "description", mode="before")
    @classmethod
    def handle_str_or_list(cls, v):
        if v == []:
            return None
        if isinstance(v, list):
            return ", ".join(str(x) for x in v)
        return v

    @field_validator("tech_stack", "language_support", "integration_capabilities", mode="before")
    @classmethod
    def handle_list_or_str(cls, v):
        if v == []:
            return []
        if isinstance(v, str):
            return [v]
        return v

class CompanyInfo(BaseModel):
    name: Union[str, List[str], None] = None
    description: Union[str, List[str], None] = ""
    website: Union[str, List[str], None] = None
    pricing_model: Union[str, List[str], None] = None
    is_open_source: Optional[bool] = None
    tech_stack: Union[List[str], str, None] = []
    competitors: Union[List[str], str, None] = []
    api_available: Optional[bool] = None
    language_support: Union[List[str], str, None] = []
    integration_capabilities: Union[List[str], str, None] = []
    developer_experience_rating: Union[str, List[str], None] = None

    @field_validator("name", "description", "website", "pricing_model", "developer_experience_rating", mode="before")
    @classmethod
    def handle_str_or_list(cls, v):
        if v == []:
            return None
        if isinstance(v, list):
            return ", ".join(str(x) for x in v)
        return v

    @field_validator("tech_stack", "competitors", "language_support", "integration_capabilities", mode="before")
    @classmethod
    def handle_list_or_str(cls, v):
        if v == []:
            return []
        if isinstance(v, str):
            return [v]
        return v

class ResearchState(BaseModel):
    query: Union[str, List[str], None] = None
    extracted_tools: Union[List[str], str, None] = []
    companies: List[CompanyInfo] = []
    search_results: List[Dict[str, Any]] = []
    analysis: Union[str, List[str], None] = None

    @field_validator("query", "analysis", mode="before")
    @classmethod
    def handle_str_or_list(cls, v):
        if v == []:
            return None
        if isinstance(v, list):
            return ", ".join(str(x) for x in v)
        return v

    @field_validator("extracted_tools", mode="before")
    @classmethod
    def handle_list_or_str(cls, v):
        if v == []:
            return []
        if isinstance(v, str):
            return [v]
        return v

class CompanyProfile(BaseModel):
    name: Union[str, List[str], None] = None
    website: Union[str, List[str], None] = None
    business_model: Union[str, List[str], None] = None
    target_market: Union[str, List[str], None] = None
    key_services: Union[List[str], str, None] = []
    tech_stack: Union[List[str], str, None] = []
    description: Union[str, List[str], None] = None

    @field_validator("name", "website", "business_model", "target_market", "description", mode="before")
    @classmethod
    def handle_str_or_list(cls, v):
        if v == []:
            return None
        if isinstance(v, list):
            return ", ".join(str(x) for x in v)
        return v

    @field_validator("key_services", "tech_stack", mode="before")
    @classmethod
    def handle_list_or_str(cls, v):
        if v == []:
            return []
        if isinstance(v, str):
            return [v]
        return v

class CompetitorProfile(BaseModel):
    name: Union[str, List[str], None] = None
    website: Union[str, List[str], None] = None
    description: Union[str, List[str], None] = None
    relevance_score: Union[float, str, List[str], None] = None

    @field_validator("name", "website", "description", mode="before")
    @classmethod
    def handle_str_or_list(cls, v):
        if v == []:
            return None
        if isinstance(v, list):
            return ", ".join(str(x) for x in v)
        return v

class CompetitorAnalysis(BaseModel):
    name: Union[str, List[str], None] = None
    website: Union[str, List[str], None] = None
    business_model: Union[str, List[str], None] = None
    target_market: Union[str, List[str], None] = None
    key_services: Union[List[str], str, None] = []
    tech_stack: Union[List[str], str, None] = []
    description: Union[str, List[str], None] = None
    features: Union[List[str], str, None] = []
    pricing: Union[str, List[str], None] = None
    integration_capabilities: Union[List[str], str, None] = []
    messaging: Union[str, List[str], None] = None
    target_audience: Union[str, List[str], None] = None
    value_propositions: Union[List[str], str, None] = []
    infrastructure: Union[str, List[str], None] = None
    development_patterns: Union[List[str], str, None] = []
    team_size: Union[int, str, List[str], None] = None
    funding_history: Union[List[str], str, None] = []
    market_expansion_signals: Union[List[str], str, None] = []
    blog_topics: Union[List[str], str, None] = []
    seo_keywords: Union[List[str], str, None] = []
    thought_leadership_themes: Union[List[str], str, None] = []

    @field_validator(
        "name", "website", "business_model", "target_market", "description", "pricing", "messaging", "target_audience", "infrastructure", mode="before"
    )
    @classmethod
    def handle_str_or_list(cls, v):
        if v == []:
            return None
        if isinstance(v, list):
            return ", ".join(str(x) for x in v)
        return v

    @field_validator(
        "key_services", "tech_stack", "features", "integration_capabilities", "value_propositions", "development_patterns", "funding_history", "market_expansion_signals", "blog_topics", "seo_keywords", "thought_leadership_themes", mode="before"
    )
    @classmethod
    def handle_list_or_str(cls, v):
        if v == []:
            return []
        if isinstance(v, str):
            return [v]
        return v

    @field_validator("team_size", mode="before")
    @classmethod
    def handle_team_size(cls, v):
        if v == []:
            return None
        if isinstance(v, list) and len(v) == 1:
            return v[0]
        return v

class FeatureComparison(BaseModel):
    features: Union[List[str], str, None] = []
    pricing: Union[str, List[str], None] = None
    integration_capabilities: Union[List[str], str, None] = []

    @field_validator("features", "integration_capabilities", mode="before")
    @classmethod
    def handle_list_or_str(cls, v):
        if v == []:
            return []
        if isinstance(v, str):
            return [v]
        return v

    @field_validator("pricing", mode="before")
    @classmethod
    def handle_str_or_list(cls, v):
        if v == []:
            return None
        if isinstance(v, list):
            return ", ".join(str(x) for x in v)
        return v

class MarketPositioning(BaseModel):
    messaging: Union[str, List[str], None] = None
    target_audience: Union[str, List[str], None] = None
    value_propositions: Union[List[str], str, None] = []

    @field_validator("messaging", "target_audience", mode="before")
    @classmethod
    def handle_str_or_list(cls, v):
        if v == []:
            return None
        if isinstance(v, list):
            return ", ".join(str(x) for x in v)
        return v

    @field_validator("value_propositions", mode="before")
    @classmethod
    def handle_list_or_str(cls, v):
        if v == []:
            return []
        if isinstance(v, str):
            return [v]
        return v

class TechnicalArchitecture(BaseModel):
    tech_stack: Union[List[str], str, None] = []
    infrastructure: Union[str, List[str], None] = None
    development_patterns: Union[List[str], str, None] = []

    @field_validator("tech_stack", "development_patterns", mode="before")
    @classmethod
    def handle_list_or_str(cls, v):
        if v == []:
            return []
        if isinstance(v, str):
            return [v]
        return v

    @field_validator("infrastructure", mode="before")
    @classmethod
    def handle_str_or_list(cls, v):
        if v == []:
            return None
        if isinstance(v, list):
            return ", ".join(str(x) for x in v)
        return v

class GrowthMetrics(BaseModel):
    team_size: Union[int, str, List[str], None] = None
    funding_history: Union[List[str], str, None] = []
    market_expansion_signals: Union[List[str], str, None] = []

    @field_validator("funding_history", "market_expansion_signals", mode="before")
    @classmethod
    def handle_list_or_str(cls, v):
        if v == []:
            return []
        if isinstance(v, str):
            return [v]
        return v

    @field_validator("team_size", mode="before")
    @classmethod
    def handle_team_size(cls, v):
        if v == []:
            return None
        if isinstance(v, list) and len(v) == 1:
            return v[0]
        return v

class ContentStrategy(BaseModel):
    blog_topics: Union[List[str], str, None] = []
    seo_keywords: Union[List[str], str, None] = []
    thought_leadership_themes: Union[List[str], str, None] = []

    @field_validator("blog_topics", "seo_keywords", "thought_leadership_themes", mode="before")
    @classmethod
    def handle_list_or_str(cls, v):
        if v == []:
            return []
        if isinstance(v, str):
            return [v]
        return v

class StrategicInsight(BaseModel):
    feature_gaps: Union[List[str], str, None] = []
    opportunities: Union[List[str], str, None] = []
    positioning_suggestions: Union[List[str], str, None] = []
    fundraising_intel: Union[List[str], str, None] = []

    @field_validator("feature_gaps", "opportunities", "positioning_suggestions", "fundraising_intel", mode="before")
    @classmethod
    def handle_list_or_str(cls, v):
        if v == []:
            return []
        if isinstance(v, str):
            return [v]
        return v

class AgentState(BaseModel):
    company_url: Union[str, List[str], None] = None
    company_profile: Optional[CompanyProfile] = None
    competitors: List[CompetitorProfile] = []
    competitor_analyses: List[CompetitorAnalysis] = []
    strategic_insights: Optional[StrategicInsight] = None
    analysis_report: Union[str, List[str], None] = None

    @field_validator("company_url", "analysis_report", mode="before")
    @classmethod
    def handle_str_or_list(cls, v):
        if v == []:
            return None
        if isinstance(v, list):
            return ", ".join(str(x) for x in v)
        return v