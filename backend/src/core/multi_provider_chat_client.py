"""
Multi-Provider Chat Client - Agent Framework Compatible

This module provides:
- Agent Framework compatible chat client interface
- Routes through ProviderRouter for provider-agnostic AI access
- Respects strict mode (blocks cloud calls when ollama_only)
- Supports Ollama, Azure OpenAI, OpenAI, Anthropic

Copyright (c) 2025 Convergio.io
"""

import logging
from typing import Optional

from .ai_providers import (
    AIConfig,
    AIProvider,
    FeatureCapability,
    get_ai_config_from_env,
)
from .provider_router import (
    ChatMessage,
    StrictModeViolation,
    ProviderUnavailable,
    get_provider_router,
)

logger = logging.getLogger(__name__)


class MultiProviderChatClient:
    """
    Chat client that routes to multiple AI providers.

    Compatible with Agent Framework's chat client interface while
    supporting Ollama, Azure, OpenAI, and Anthropic through ProviderRouter.

    Key features:
    - Respects AI_PROVIDER_MODE setting
    - Enforces strict mode (no cloud fallback)
    - Per-agent provider routing
    - Cost tracking
    """

    def __init__(
        self,
        config: Optional[AIConfig] = None,
        model_id: Optional[str] = None,
        agent_id: Optional[str] = None,
    ):
        """
        Initialize multi-provider chat client.

        Args:
            config: AI configuration (loads from env if not provided)
            model_id: Override model ID (uses config default if not provided)
            agent_id: Agent ID for per-agent routing
        """
        self.config = config or get_ai_config_from_env()
        self._router = get_provider_router()
        self._model_id = model_id or self.config.default_model
        self._agent_id = agent_id

        logger.info(
            f"MultiProviderChatClient initialized: mode={self.config.mode.value}, "
            f"provider={self.config.default_provider.value}, model={self._model_id}"
        )

    @property
    def model_id(self) -> str:
        """Get the model ID."""
        return self._model_id

    @property
    def provider(self) -> AIProvider:
        """Get the current provider."""
        return self.config.default_provider

    @property
    def is_local(self) -> bool:
        """Check if using local provider (Ollama)."""
        return self.config.default_provider in [AIProvider.OLLAMA, AIProvider.LOCAL_EMBEDDINGS]

    @property
    def is_strict_mode(self) -> bool:
        """Check if strict mode is enabled."""
        return self.config.strict_mode

    async def create_chat_completion(
        self,
        messages: list[dict[str, str]],
        **kwargs
    ) -> dict:
        """
        Create chat completion (Agent Framework compatible interface).

        Args:
            messages: List of message dicts with "role" and "content"
            **kwargs: Additional arguments (temperature, max_tokens, etc.)

        Returns:
            Response dict with "choices" containing the completion

        Raises:
            StrictModeViolation: If cloud provider would be used in strict mode
            ProviderUnavailable: If requested provider is not available
        """
        # Convert to ChatMessage format
        chat_messages = [
            ChatMessage(role=m["role"], content=m["content"])
            for m in messages
        ]

        # Determine capability based on context
        capability = self._determine_capability(messages, kwargs)

        try:
            response = await self._router.chat_completion(
                messages=chat_messages,
                capability=capability,
                agent_id=self._agent_id,
            )

            # Return in OpenAI-compatible format for Agent Framework
            return {
                "id": f"chatcmpl-{response.provider.value}",
                "object": "chat.completion",
                "model": response.model,
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response.content,
                    },
                    "finish_reason": "stop",
                }],
                "usage": {
                    "total_tokens": response.tokens_used,
                },
                # Custom fields for tracking
                "_provider": response.provider.value,
                "_cost_usd": response.cost_usd,
                "_is_local": response.provider in [AIProvider.OLLAMA, AIProvider.LOCAL_EMBEDDINGS],
            }

        except StrictModeViolation as e:
            logger.error(f"Strict mode violation: {e}")
            raise
        except ProviderUnavailable as e:
            logger.error(f"Provider unavailable: {e}")
            raise

    async def chat(
        self,
        messages: list[dict[str, str]],
        **kwargs
    ) -> str:
        """
        Simple chat interface returning just the content.

        Args:
            messages: List of message dicts
            **kwargs: Additional arguments

        Returns:
            Response content string
        """
        response = await self.create_chat_completion(messages, **kwargs)
        return response["choices"][0]["message"]["content"]

    def _determine_capability(
        self,
        messages: list[dict[str, str]],
        kwargs: dict
    ) -> FeatureCapability:
        """
        Determine the required capability based on message context.

        Simple heuristic based on:
        - Message length (complex = longer context)
        - Presence of code markers
        - Explicit capability request in kwargs
        """
        # Check for explicit capability
        if "capability" in kwargs:
            return kwargs["capability"]

        # Analyze messages
        total_length = sum(len(m.get("content", "")) for m in messages)
        has_code = any(
            "```" in m.get("content", "") or
            "def " in m.get("content", "") or
            "function " in m.get("content", "")
            for m in messages
        )

        if has_code:
            return FeatureCapability.CODE_REVIEW
        elif total_length > 10000:
            return FeatureCapability.CHAT_COMPLEX
        else:
            return FeatureCapability.CHAT_SIMPLE

    def get_stats(self) -> dict:
        """Get usage statistics from router."""
        return self._router.get_stats()

    def get_costs(self) -> dict[str, float]:
        """Get accumulated costs per provider."""
        return self._router.get_costs()


def get_multi_provider_client(
    config: Optional[AIConfig] = None,
    agent_id: Optional[str] = None,
) -> MultiProviderChatClient:
    """
    Get a multi-provider chat client.

    Args:
        config: AI configuration (loads from env if not provided)
        agent_id: Optional agent ID for per-agent routing

    Returns:
        MultiProviderChatClient instance
    """
    return MultiProviderChatClient(config=config, agent_id=agent_id)


def create_chat_client_for_agent(
    agent_id: str,
    config: Optional[AIConfig] = None,
) -> MultiProviderChatClient:
    """
    Create a chat client configured for a specific agent.

    This respects per-agent provider overrides in the AI config.

    Args:
        agent_id: The agent's identifier
        config: AI configuration (loads from env if not provided)

    Returns:
        MultiProviderChatClient configured for the agent
    """
    if config is None:
        config = get_ai_config_from_env()

    return MultiProviderChatClient(
        config=config,
        agent_id=agent_id,
    )


# Compatibility wrapper for Agent Framework
class AgentFrameworkCompatibleClient:
    """
    Wrapper that provides exact Agent Framework ChatClient interface.

    This class mimics OpenAIChatClient's interface while routing
    through the multi-provider system.
    """

    def __init__(
        self,
        model_id: Optional[str] = None,
        api_key: Optional[str] = None,  # Ignored, uses config
        agent_id: Optional[str] = None,
    ):
        """
        Initialize compatible client.

        Args:
            model_id: Model to use (optional)
            api_key: Ignored - uses provider config from env
            agent_id: Agent ID for per-agent routing
        """
        self._inner = MultiProviderChatClient(
            model_id=model_id,
            agent_id=agent_id,
        )

    @property
    def model_id(self) -> str:
        return self._inner.model_id

    async def create_chat_completion(
        self,
        messages: list[dict[str, str]],
        **kwargs
    ) -> dict:
        """Agent Framework compatible chat completion."""
        return await self._inner.create_chat_completion(messages, **kwargs)

    # Alias for Agent Framework compatibility
    async def complete(
        self,
        messages: list[dict[str, str]],
        **kwargs
    ) -> dict:
        """Agent Framework complete method."""
        return await self.create_chat_completion(messages, **kwargs)


def get_agent_framework_compatible_client(
    agent_id: Optional[str] = None,
) -> AgentFrameworkCompatibleClient:
    """
    Get a client compatible with Agent Framework.

    Use this as a drop-in replacement for OpenAIChatClient.

    Args:
        agent_id: Optional agent ID for per-agent routing

    Returns:
        AgentFrameworkCompatibleClient instance
    """
    return AgentFrameworkCompatibleClient(agent_id=agent_id)
