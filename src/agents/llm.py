"""LLM integration helpers for agent nodes.

Provides a thin wrapper around ovhllm.py for use in LangGraph agent nodes.
Includes JSON response parsing utilities.
"""

import json
import re
from typing import Any, Optional

from langchain_openai import ChatOpenAI

from ovhllm import OVHLLM, get_llm_client
from src.utils.logger import get_logger

logger = get_logger(__name__)


def get_chat_model(temperature: float = 0.7, max_tokens: int = 2048) -> ChatOpenAI:
    """Get a LangChain ChatOpenAI instance for use with LangGraph agents.

    Args:
        temperature: Generation temperature (0.0 to 1.0)
        max_tokens: Maximum tokens in response

    Returns:
        ChatOpenAI instance configured for OVH endpoint
    """
    client = get_llm_client()
    # Create a new client with custom settings if needed
    if temperature != 0.7 or max_tokens != 2048:
        custom_client = OVHLLM(temperature=temperature, max_tokens=max_tokens)
        return custom_client.get_chat_model()
    return client.get_chat_model()


def generate(
    prompt: str,
    system_prompt: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> str:
    """Generate text using OVH LLM.

    Args:
        prompt: User prompt
        system_prompt: Optional system instructions
        temperature: Generation temperature
        max_tokens: Maximum tokens in response

    Returns:
        Generated text response
    """
    client = get_llm_client()
    return client.generate(
        prompt=prompt,
        system_prompt=system_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def generate_json(
    prompt: str,
    system_prompt: Optional[str] = None,
    temperature: float = 0.3,
    max_tokens: int = 2048,
) -> dict[str, Any]:
    """Generate and parse a JSON response from the LLM.

    Uses lower temperature by default for more deterministic JSON output.
    Automatically cleans markdown code fences from the response.

    Args:
        prompt: User prompt (should ask for JSON response)
        system_prompt: Optional system instructions
        temperature: Generation temperature (default 0.3 for JSON)
        max_tokens: Maximum tokens in response

    Returns:
        Parsed JSON dict

    Raises:
        ValueError: If the response is not valid JSON
    """
    response = generate(
        prompt=prompt,
        system_prompt=system_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    return parse_json_response(response)


def parse_json_response(response: str) -> dict[str, Any]:
    """Parse a JSON response, stripping markdown code fences if present.

    Args:
        response: Raw LLM response text

    Returns:
        Parsed JSON dict

    Raises:
        ValueError: If the response is not valid JSON
    """
    text = response.strip()

    # Remove markdown code fences
    # Handle ```json ... ``` and ``` ... ```
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]

    if text.endswith("```"):
        text = text[:-3]

    text = text.strip()

    # Try to extract JSON from the text if there's extra content
    # Look for first { and last }
    if not text.startswith("{") and "{" in text:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            text = text[start:end]

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {e}")
        logger.debug(f"Raw response: {response[:500]}...")
        raise ValueError(f"Invalid JSON response from LLM: {e}")


def is_llm_configured() -> bool:
    """Check if LLM credentials are properly configured.

    Returns:
        True if OVH credentials are set
    """
    try:
        client = get_llm_client()
        return client.is_configured()
    except Exception:
        return False
