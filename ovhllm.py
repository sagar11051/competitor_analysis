"""
OVH LLM client using Mistral-Nemo via OpenAI-compatible API.

Provides synchronous and asynchronous methods for text generation
using OVH AI Endpoints.
"""

from functools import lru_cache
from typing import Any, AsyncGenerator, Dict, Generator, List, Optional

from langchain_openai import ChatOpenAI
from openai import AsyncOpenAI, OpenAI

from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class OVHLLM:
    """
    OVH LLM client using Mistral-Nemo model via OpenAI-compatible API.

    Features:
    - Chat completions with conversation history
    - Streaming support for real-time responses
    - Configurable temperature and max tokens
    - Synchronous and asynchronous methods
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        access_token: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ):
        """
        Initialize OVH LLM client.

        Args:
            base_url: OVH LLM base URL (default from settings)
            access_token: OVH AI Endpoints access token (default from settings)
            model: Model name (default from settings)
            temperature: Generation temperature (0.0 to 1.0)
            max_tokens: Maximum tokens in response
        """
        self.base_url = base_url or settings.ovh.llm_base_url
        self.access_token = access_token or settings.ovh.ai_endpoints_access_token
        self.model = model or settings.ovh.llm_model
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Initialize OpenAI clients
        self._sync_client: Optional[OpenAI] = None
        self._async_client: Optional[AsyncOpenAI] = None

        logger.info(
            f"Initialized OVH LLM client "
            f"(model: {self.model}, temp: {self.temperature})"
        )

    def is_configured(self) -> bool:
        """Check if OVH credentials are configured."""
        return bool(self.base_url and self.access_token)

    @property
    def sync_client(self) -> OpenAI:
        """Get or create synchronous OpenAI client."""
        if self._sync_client is None:
            self._sync_client = OpenAI(
                api_key=self.access_token,
                base_url=self.base_url,
            )
        return self._sync_client

    @property
    def async_client(self) -> AsyncOpenAI:
        """Get or create asynchronous OpenAI client."""
        if self._async_client is None:
            self._async_client = AsyncOpenAI(
                api_key=self.access_token,
                base_url=self.base_url,
            )
        return self._async_client

    def get_chat_model(self) -> ChatOpenAI:
        """
        Get a LangChain ChatOpenAI instance for use with LangGraph agents.

        Returns:
            ChatOpenAI instance configured for OVH endpoint
        """
        return ChatOpenAI(
            model=self.model,
            api_key=self.access_token,
            base_url=self.base_url,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

    # =========================================================================
    # Synchronous Methods
    # =========================================================================

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate text from a prompt (synchronous).

        Args:
            prompt: User prompt/question
            system_prompt: Optional system instructions
            temperature: Override default temperature
            max_tokens: Override default max tokens

        Returns:
            Generated text response
        """
        if not self.is_configured():
            raise ValueError(
                "OVH credentials not configured. "
                "Set OVH_AI_ENDPOINTS_ACCESS_TOKEN in .env"
            )

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        return self.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate chat completion (synchronous).

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Override default temperature
            max_tokens: Override default max tokens

        Returns:
            Assistant's response text
        """
        if not self.is_configured():
            raise ValueError(
                "OVH credentials not configured. "
                "Set OVH_AI_ENDPOINTS_ACCESS_TOKEN in .env"
            )

        try:
            response = self.sync_client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
            )

            content = response.choices[0].message.content
            logger.debug(f"Generated response: {len(content)} chars")
            return content

        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise

    def chat_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Generator[str, None, None]:
        """
        Generate chat completion with streaming (synchronous).

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Override default temperature
            max_tokens: Override default max tokens

        Yields:
            Text chunks as they are generated
        """
        if not self.is_configured():
            raise ValueError(
                "OVH credentials not configured. "
                "Set OVH_AI_ENDPOINTS_ACCESS_TOKEN in .env"
            )

        try:
            stream = self.sync_client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
                stream=True,
            )

            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"LLM streaming failed: {e}")
            raise

    # =========================================================================
    # Asynchronous Methods
    # =========================================================================

    async def agenerate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate text from a prompt (asynchronous).

        Args:
            prompt: User prompt/question
            system_prompt: Optional system instructions
            temperature: Override default temperature
            max_tokens: Override default max tokens

        Returns:
            Generated text response
        """
        if not self.is_configured():
            raise ValueError(
                "OVH credentials not configured. "
                "Set OVH_AI_ENDPOINTS_ACCESS_TOKEN in .env"
            )

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        return await self.achat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    async def achat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate chat completion (asynchronous).

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Override default temperature
            max_tokens: Override default max tokens

        Returns:
            Assistant's response text
        """
        if not self.is_configured():
            raise ValueError(
                "OVH credentials not configured. "
                "Set OVH_AI_ENDPOINTS_ACCESS_TOKEN in .env"
            )

        try:
            response = await self.async_client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
            )

            content = response.choices[0].message.content
            logger.debug(f"Generated response: {len(content)} chars")
            return content

        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise

    async def achat_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Generate chat completion with streaming (asynchronous).

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Override default temperature
            max_tokens: Override default max tokens

        Yields:
            Text chunks as they are generated
        """
        if not self.is_configured():
            raise ValueError(
                "OVH credentials not configured. "
                "Set OVH_AI_ENDPOINTS_ACCESS_TOKEN in .env"
            )

        try:
            stream = await self.async_client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"LLM streaming failed: {e}")
            raise

    # =========================================================================
    # RAG-Specific Methods
    # =========================================================================

    def generate_with_context(
        self,
        query: str,
        context: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate response using retrieved context (RAG).

        Args:
            query: User's question
            context: Retrieved context from vector search
            system_prompt: Optional custom system prompt
            temperature: Override default temperature
            max_tokens: Override default max tokens

        Returns:
            Generated response based on context
        """
        default_system = """You are a helpful documentation assistant.
Answer questions based on the provided context.
If the context doesn't contain relevant information, say so.
Always cite the source when possible."""

        full_prompt = f"""Context:
{context}

Question: {query}

Answer based on the context above:"""

        return self.generate(
            prompt=full_prompt,
            system_prompt=system_prompt or default_system,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    async def agenerate_with_context(
        self,
        query: str,
        context: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate response using retrieved context (RAG, async).

        Args:
            query: User's question
            context: Retrieved context from vector search
            system_prompt: Optional custom system prompt
            temperature: Override default temperature
            max_tokens: Override default max tokens

        Returns:
            Generated response based on context
        """
        default_system = """You are a helpful documentation assistant.
Answer questions based on the provided context.
If the context doesn't contain relevant information, say so.
Always cite the source when possible."""

        full_prompt = f"""Context:
{context}

Question: {query}

Answer based on the context above:"""

        return await self.agenerate(
            prompt=full_prompt,
            system_prompt=system_prompt or default_system,
            temperature=temperature,
            max_tokens=max_tokens,
        )


@lru_cache()
def get_llm_client() -> OVHLLM:
    """Get cached OVH LLM client instance."""
    return OVHLLM()
