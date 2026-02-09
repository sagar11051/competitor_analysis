import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class OVHSettings:
    llm_base_url: str = ""
    ai_endpoints_access_token: str = ""
    llm_model: str = "Mistral-Nemo-Instruct-2407"


@dataclass
class Settings:
    ovh: OVHSettings = field(default_factory=OVHSettings)
    tavily_api_key: str = ""
    firecrawl_api_key: str = ""
    gemini_api_key: str = ""

    def __post_init__(self):
        self.ovh.llm_base_url = os.getenv("OVH_LLM_BASE_URL", self.ovh.llm_base_url)
        self.ovh.ai_endpoints_access_token = os.getenv(
            "OVH_AI_ENDPOINTS_ACCESS_TOKEN", self.ovh.ai_endpoints_access_token
        )
        self.ovh.llm_model = os.getenv("OVH_LLM_MODEL", self.ovh.llm_model)
        self.tavily_api_key = os.getenv("TAVILY_API_KEY", self.tavily_api_key)
        self.firecrawl_api_key = os.getenv("FIRECRAWL_API_KEY", self.firecrawl_api_key)
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", self.gemini_api_key)


settings = Settings()
