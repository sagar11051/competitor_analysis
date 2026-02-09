"""Tests for ovhllm.py module — import resolution and instantiation."""

from unittest.mock import patch


def test_ovhllm_imports():
    """Verify ovhllm.py can be imported now that config/logger exist."""
    from ovhllm import OVHLLM, get_llm_client
    assert OVHLLM is not None
    assert callable(get_llm_client)


def test_ovhllm_instantiation_with_explicit_params():
    """OVHLLM can be created with explicit params (no settings needed)."""
    from ovhllm import OVHLLM
    client = OVHLLM(
        base_url="https://test.example.com/v1",
        access_token="test-token",
        model="test-model",
        temperature=0.5,
        max_tokens=512,
    )
    assert client.base_url == "https://test.example.com/v1"
    assert client.access_token == "test-token"
    assert client.model == "test-model"
    assert client.temperature == 0.5
    assert client.max_tokens == 512


def test_ovhllm_is_configured():
    from ovhllm import OVHLLM
    configured = OVHLLM(base_url="https://x.com", access_token="tok")
    assert configured.is_configured() is True

    not_configured = OVHLLM(base_url="", access_token="")
    assert not_configured.is_configured() is False


def test_ovhllm_get_chat_model():
    """get_chat_model returns a LangChain ChatOpenAI instance."""
    from ovhllm import OVHLLM
    client = OVHLLM(
        base_url="https://test.example.com/v1",
        access_token="test-token",
        model="test-model",
    )
    chat_model = client.get_chat_model()
    assert chat_model is not None
    assert chat_model.model_name == "test-model"
