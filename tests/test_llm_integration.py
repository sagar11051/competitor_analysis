"""Unit tests for LLM integration helpers.

Tests the src/agents/llm.py module functions.
"""

import json
from unittest.mock import MagicMock, patch

import pytest


class TestParseJsonResponse:
    """Tests for parse_json_response function."""

    def test_parse_clean_json(self):
        """Test parsing clean JSON without code fences."""
        from src.agents.llm import parse_json_response

        response = '{"key": "value", "number": 42}'
        result = parse_json_response(response)

        assert result == {"key": "value", "number": 42}

    def test_parse_json_with_code_fence(self):
        """Test parsing JSON wrapped in ```json ... ``` fences."""
        from src.agents.llm import parse_json_response

        response = '```json\n{"key": "value"}\n```'
        result = parse_json_response(response)

        assert result == {"key": "value"}

    def test_parse_json_with_plain_code_fence(self):
        """Test parsing JSON wrapped in ``` ... ``` fences."""
        from src.agents.llm import parse_json_response

        response = '```\n{"items": [1, 2, 3]}\n```'
        result = parse_json_response(response)

        assert result == {"items": [1, 2, 3]}

    def test_parse_json_with_whitespace(self):
        """Test parsing JSON with leading/trailing whitespace."""
        from src.agents.llm import parse_json_response

        response = '\n\n  {"key": "value"}  \n\n'
        result = parse_json_response(response)

        assert result == {"key": "value"}

    def test_parse_json_with_extra_text(self):
        """Test parsing JSON when there's extra text before/after."""
        from src.agents.llm import parse_json_response

        response = 'Here is the result:\n{"key": "value"}\nThat is all.'
        result = parse_json_response(response)

        assert result == {"key": "value"}

    def test_parse_invalid_json_raises(self):
        """Test that invalid JSON raises ValueError."""
        from src.agents.llm import parse_json_response

        response = "This is not JSON at all"

        with pytest.raises(ValueError) as excinfo:
            parse_json_response(response)

        assert "Invalid JSON response" in str(excinfo.value)

    def test_parse_nested_json(self):
        """Test parsing complex nested JSON."""
        from src.agents.llm import parse_json_response

        data = {
            "tasks": [
                {"type": "company_profile", "url": "https://example.com"},
                {"type": "competitor_discovery", "url": None},
            ],
            "metadata": {"count": 2},
        }
        response = json.dumps(data)
        result = parse_json_response(response)

        assert result == data


class TestIsLlmConfigured:
    """Tests for is_llm_configured function."""

    def test_llm_configured_returns_true(self):
        """Test is_llm_configured returns True when credentials are set."""
        from src.agents.llm import is_llm_configured

        with patch("src.agents.llm.get_llm_client") as mock_get:
            mock_client = MagicMock()
            mock_client.is_configured.return_value = True
            mock_get.return_value = mock_client

            assert is_llm_configured() is True

    def test_llm_not_configured_returns_false(self):
        """Test is_llm_configured returns False when credentials missing."""
        from src.agents.llm import is_llm_configured

        with patch("src.agents.llm.get_llm_client") as mock_get:
            mock_client = MagicMock()
            mock_client.is_configured.return_value = False
            mock_get.return_value = mock_client

            assert is_llm_configured() is False

    def test_llm_exception_returns_false(self):
        """Test is_llm_configured returns False on exception."""
        from src.agents.llm import is_llm_configured

        with patch("src.agents.llm.get_llm_client") as mock_get:
            mock_get.side_effect = Exception("Connection error")

            assert is_llm_configured() is False


class TestGenerate:
    """Tests for generate function."""

    def test_generate_calls_client(self):
        """Test generate calls the LLM client with correct params."""
        from src.agents.llm import generate

        with patch("src.agents.llm.get_llm_client") as mock_get:
            mock_client = MagicMock()
            mock_client.generate.return_value = "Generated response"
            mock_get.return_value = mock_client

            result = generate(
                prompt="Test prompt",
                system_prompt="You are a helpful assistant",
                temperature=0.5,
                max_tokens=1000,
            )

            assert result == "Generated response"
            mock_client.generate.assert_called_once_with(
                prompt="Test prompt",
                system_prompt="You are a helpful assistant",
                temperature=0.5,
                max_tokens=1000,
            )


class TestGenerateJson:
    """Tests for generate_json function."""

    def test_generate_json_parses_response(self):
        """Test generate_json calls generate and parses JSON."""
        from src.agents.llm import generate_json

        with patch("src.agents.llm.generate") as mock_gen:
            mock_gen.return_value = '{"result": "success"}'

            result = generate_json(
                prompt="Generate JSON",
                system_prompt="You are a JSON generator",
            )

            assert result == {"result": "success"}
            mock_gen.assert_called_once()

    def test_generate_json_with_code_fence(self):
        """Test generate_json handles code-fenced response."""
        from src.agents.llm import generate_json

        with patch("src.agents.llm.generate") as mock_gen:
            mock_gen.return_value = '```json\n{"key": "value"}\n```'

            result = generate_json(prompt="Generate JSON")

            assert result == {"key": "value"}

    def test_generate_json_uses_lower_temperature(self):
        """Test generate_json defaults to lower temperature for determinism."""
        from src.agents.llm import generate_json

        with patch("src.agents.llm.generate") as mock_gen:
            mock_gen.return_value = '{"ok": true}'

            generate_json(prompt="Test")

            # Check that temperature 0.3 was used (default for JSON)
            call_kwargs = mock_gen.call_args[1]
            assert call_kwargs["temperature"] == 0.3

    def test_generate_json_raises_on_invalid(self):
        """Test generate_json raises ValueError on invalid JSON response."""
        from src.agents.llm import generate_json

        with patch("src.agents.llm.generate") as mock_gen:
            mock_gen.return_value = "Not valid JSON at all"

            with pytest.raises(ValueError):
                generate_json(prompt="Test")


class TestGetChatModel:
    """Tests for get_chat_model function."""

    def test_get_chat_model_returns_chat_openai(self):
        """Test get_chat_model returns a ChatOpenAI instance."""
        from src.agents.llm import get_chat_model

        with patch("src.agents.llm.get_llm_client") as mock_get:
            mock_client = MagicMock()
            mock_chat_model = MagicMock()
            mock_client.get_chat_model.return_value = mock_chat_model
            mock_get.return_value = mock_client

            result = get_chat_model()

            assert result == mock_chat_model
            mock_client.get_chat_model.assert_called_once()

    def test_get_chat_model_with_custom_settings(self):
        """Test get_chat_model creates custom client for non-default settings."""
        from src.agents.llm import get_chat_model

        with patch("src.agents.llm.OVHLLM") as mock_ovhllm:
            mock_instance = MagicMock()
            mock_chat_model = MagicMock()
            mock_instance.get_chat_model.return_value = mock_chat_model
            mock_ovhllm.return_value = mock_instance

            result = get_chat_model(temperature=0.1, max_tokens=500)

            mock_ovhllm.assert_called_once_with(temperature=0.1, max_tokens=500)
            assert result == mock_chat_model
