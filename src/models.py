from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, field_validator

class CompanyProfile(BaseModel):
    name: Union[str, List[str], None] = None
    website: Union[str, List[str], None] = None
    business_model: Union[str, List[str], None] = None
    target_market: Union[str, List[str], None] = None
    key_services: Union[List[str], str, None] = []
    tech_stack: Union[List[str], str, None] = []
    description: Union[str, List[str], None] = None

class CompetitorProfile(BaseModel):
    name: Union[str, List[str], None] = None
    website: Union[str, List[str], None] = None
    description: Union[str, List[str], None] = None
    relevance_score: Union[float, str, List[str], None] = None


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

class StrategicInsight(BaseModel):
    feature_gaps: Union[List[str], str, None] = []
    opportunities: Union[List[str], str, None] = []
    positioning_suggestions: Union[List[str], str, None] = []
    fundraising_intel: Union[List[str], str, None] = []



class AgentState(BaseModel):
    company_url: Union[str, List[str], None] = None
    company_profile: Optional[CompanyProfile] = None
    competitors: List[CompetitorProfile] = []
    competitor_analyses: List[CompetitorAnalysis] = []
    strategic_insights: Optional[StrategicInsight] = None
    analysis_report: Union[str, List[str], None] = None
