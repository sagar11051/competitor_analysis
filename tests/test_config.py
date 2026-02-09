"""Tests for src.config.settings module."""

import os
from unittest.mock import patch

from src.config.settings import Settings, OVHSettings


def test_ovh_settings_defaults():
    ovh = OVHSettings()
    assert ovh.llm_model == "Mistral-Nemo-Instruct-2407"
    assert ovh.llm_base_url == ""
    assert ovh.ai_endpoints_access_token == ""


def test_settings_loads_env_vars():
    env = {
        "OVH_LLM_BASE_URL": "https://test.ovh.com/v1",
        "OVH_AI_ENDPOINTS_ACCESS_TOKEN": "test-token-123",
        "OVH_LLM_MODEL": "custom-model",
        "TAVILY_API_KEY": "tvly-key",
        "FIRECRAWL_API_KEY": "fc-key",
        "GEMINI_API_KEY": "gem-key",
    }
    with patch.dict(os.environ, env, clear=False):
        s = Settings()
        assert s.ovh.llm_base_url == "https://test.ovh.com/v1"
        assert s.ovh.ai_endpoints_access_token == "test-token-123"
        assert s.ovh.llm_model == "custom-model"
        assert s.tavily_api_key == "tvly-key"
        assert s.firecrawl_api_key == "fc-key"
        assert s.gemini_api_key == "gem-key"


def test_settings_singleton_import():
    from src.config import settings
    assert isinstance(settings, Settings)
    assert isinstance(settings.ovh, OVHSettings)
