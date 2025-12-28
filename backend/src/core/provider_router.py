"""
AI Provider Router - Unified Provider Access with Strict Mode Enforcement

This module provides:
- Unified interface for all AI providers
- Respects provider mode (ollama_only, azure_only, hybrid, cloud_first)
- Strict mode enforcement (blocks cloud calls when ollama_only)
- Per-feature and per-agent routing
- Cost tracking per provider

Copyright (c) 2025 Convergio.io
"""

import os
import logging
from typing import Optional
from pydantic import BaseModel

from .ai_providers import (
    AIConfig,
    AIProvider,
    ProviderMode,
    FeatureCapability,
    get_ai_config_from_env,
    get_provider_for_capability,
    get_provider_for_agent,
    can_provider_handle_capability,
    PROVIDER_INFO,
)
from .ollama_service import get_ollama_service

logger = logging.getLogger(__name__)


class ProviderError(Exception):
    """Error from AI provider."""
    pass


class StrictModeViolation(Exception):
    """Attempted to use cloud provider in strict mode."""
    pass


class ProviderUnavailable(Exception):
    """Requested provider is not available."""
    pass


class ChatMessage(BaseModel):
    """Chat message format."""
    role: str  # "system", "user", "assistant"
    content: str


class ToolCall(BaseModel):
    """Tool/function call from model."""
    id: str
    type: str = "function"
    function_name: str
    arguments: dict


class ChatResponse(BaseModel):
    """Response from chat completion."""
    content: str
    provider: AIProvider
    model: str
    tokens_used: int = 0
    cost_usd: float = 0.0
    tool_calls: list[ToolCall] = []


class ProviderRouter:
    """
    Routes AI requests to the appropriate provider based on configuration.

    Key features:
    - Respects AI_PROVIDER_MODE environment setting
    - Enforces strict mode (no cloud fallback)
    - Tracks costs per provider
    - Supports per-feature and per-agent routing
    """

    def __init__(self, config: Optional[AIConfig] = None):
        """
        Initialize provider router.

        Args:
            config: AI configuration (loads from env if not provided)
        """
        self.config = config or get_ai_config_from_env()
        self._ollama = get_ollama_service()
        self._costs = {p: 0.0 for p in AIProvider}
        self._call_counts = {p: 0 for p in AIProvider}

        logger.info(
            f"ProviderRouter initialized: mode={self.config.mode.value}, "
            f"strict={self.config.strict_mode}, default={self.config.default_provider.value}"
        )

    def _validate_provider(self, provider: AIProvider) -> None:
        """
        Validate that provider can be used with current config.

        Raises:
            StrictModeViolation: If trying to use cloud in strict mode
            ProviderUnavailable: If provider is not configured
        """
        # Check strict mode
        if self.config.strict_mode and self.config.mode == ProviderMode.OLLAMA_ONLY:
            if provider != AIProvider.OLLAMA and provider != AIProvider.LOCAL_EMBEDDINGS:
                raise StrictModeViolation(
                    f"Cannot use {provider.value} - strict mode is ON and mode is ollama_only. "
                    f"Cloud providers are blocked."
                )

        # Check Azure mode
        if self.config.mode == ProviderMode.AZURE_ONLY:
            if provider not in [AIProvider.AZURE_OPENAI, AIProvider.LOCAL_EMBEDDINGS]:
                raise StrictModeViolation(
                    f"Cannot use {provider.value} - mode is azure_only. "
                    f"Only Azure OpenAI is allowed."
                )

        # Check provider is available
        info = PROVIDER_INFO.get(provider)
        if info and info.requires_api_key:
            if provider == AIProvider.OPENAI and not os.getenv("OPENAI_API_KEY"):
                raise ProviderUnavailable("OpenAI API key not configured")
            if provider == AIProvider.ANTHROPIC and not os.getenv("ANTHROPIC_API_KEY"):
                raise ProviderUnavailable("Anthropic API key not configured")
            if provider == AIProvider.AZURE_OPENAI and not os.getenv("AZURE_OPENAI_API_KEY"):
                raise ProviderUnavailable("Azure OpenAI API key not configured")
            if provider == AIProvider.PERPLEXITY and not os.getenv("PERPLEXITY_API_KEY"):
                raise ProviderUnavailable("Perplexity API key not configured")

    async def chat_completion(
        self,
        messages: list[ChatMessage],
        capability: FeatureCapability = FeatureCapability.CHAT_SIMPLE,
        agent_id: Optional[str] = None,
        stream: bool = False,
    ) -> ChatResponse:
        """
        Route chat completion to appropriate provider.

        Args:
            messages: List of chat messages
            capability: Required capability
            agent_id: Optional agent ID for per-agent routing
            stream: Whether to stream response

        Returns:
            ChatResponse with content and metadata

        Raises:
            StrictModeViolation: If cloud provider would be used in strict mode
            ProviderError: If provider call fails
        """
        # Determine provider
        if agent_id:
            provider, model = get_provider_for_agent(agent_id, self.config)
        else:
            provider, model = get_provider_for_capability(capability, self.config)

        # Validate provider is allowed
        self._validate_provider(provider)

        # Route to provider
        logger.info(f"Routing chat to {provider.value} with model {model}")

        if provider == AIProvider.OLLAMA:
            return await self._ollama_chat(messages, model)
        elif provider == AIProvider.AZURE_OPENAI:
            return await self._azure_chat(messages, model)
        elif provider == AIProvider.OPENAI:
            return await self._openai_chat(messages, model)
        elif provider == AIProvider.ANTHROPIC:
            return await self._anthropic_chat(messages, model)
        else:
            raise ProviderError(f"Unsupported provider: {provider.value}")

    async def chat_with_tools(
        self,
        messages: list[ChatMessage],
        tools: list[dict],
        tool_choice: str = "auto",
        agent_id: Optional[str] = None,
    ) -> ChatResponse:
        """
        Route chat with function/tool calling to appropriate provider.

        Args:
            messages: List of chat messages
            tools: List of tool definitions in OpenAI format
            tool_choice: "auto", "none", or specific tool
            agent_id: Optional agent ID for per-agent routing

        Returns:
            ChatResponse with content and optional tool_calls

        Raises:
            StrictModeViolation: If cloud provider would be used in strict mode
            ProviderError: If provider call fails
        """
        # Determine provider - use FUNCTION_CALLING capability
        if agent_id:
            provider, model = get_provider_for_agent(agent_id, self.config)
        else:
            provider, model = get_provider_for_capability(
                FeatureCapability.FUNCTION_CALLING, self.config
            )

        # Validate provider is allowed
        self._validate_provider(provider)

        # Check if provider supports function calling
        if not can_provider_handle_capability(provider, FeatureCapability.FUNCTION_CALLING):
            logger.warning(
                f"Provider {provider.value} may not support function calling. "
                f"Attempting anyway..."
            )

        logger.info(f"Routing function call to {provider.value} with model {model}")

        if provider == AIProvider.OLLAMA:
            return await self._ollama_chat_with_tools(messages, model, tools, tool_choice)
        elif provider == AIProvider.AZURE_OPENAI:
            return await self._azure_chat_with_tools(messages, model, tools, tool_choice)
        elif provider == AIProvider.OPENAI:
            return await self._openai_chat_with_tools(messages, model, tools, tool_choice)
        elif provider == AIProvider.ANTHROPIC:
            return await self._anthropic_chat_with_tools(messages, model, tools, tool_choice)
        else:
            raise ProviderError(f"Unsupported provider for function calling: {provider.value}")

    async def _ollama_chat(
        self,
        messages: list[ChatMessage],
        model: str,
    ) -> ChatResponse:
        """Chat using Ollama (local, FREE)."""
        try:
            # Check Ollama is available
            status = await self._ollama.health_check()
            if not status.available:
                raise ProviderUnavailable(
                    f"Ollama is not available: {status.error}. "
                    f"Please start Ollama or switch provider mode."
                )

            # Format messages for Ollama
            ollama_messages = [
                {"role": m.role, "content": m.content}
                for m in messages
            ]

            response = await self._ollama.chat(model, ollama_messages)

            # Track stats (Ollama is free!)
            self._call_counts[AIProvider.OLLAMA] += 1

            message = response.get("message", {})
            tool_calls_raw = message.get("tool_calls", [])

            # Parse tool calls
            tool_calls = []
            for tc in tool_calls_raw:
                func = tc.get("function", {})
                import json
                args_str = func.get("arguments", "{}")
                try:
                    args = json.loads(args_str) if isinstance(args_str, str) else args_str
                except json.JSONDecodeError:
                    args = {}
                tool_calls.append(ToolCall(
                    id=tc.get("id", ""),
                    type=tc.get("type", "function"),
                    function_name=func.get("name", ""),
                    arguments=args,
                ))

            return ChatResponse(
                content=message.get("content", ""),
                provider=AIProvider.OLLAMA,
                model=model,
                tokens_used=response.get("eval_count", 0),
                cost_usd=0.0,  # Ollama is FREE
                tool_calls=tool_calls,
            )

        except Exception as e:
            logger.error(f"Ollama chat failed: {e}")
            raise ProviderError(f"Ollama error: {str(e)}")

    async def _ollama_chat_with_tools(
        self,
        messages: list[ChatMessage],
        model: str,
        tools: list[dict],
        tool_choice: str = "auto",
    ) -> ChatResponse:
        """Chat with function calling using Ollama."""
        try:
            status = await self._ollama.health_check()
            if not status.available:
                raise ProviderUnavailable(
                    f"Ollama is not available: {status.error}"
                )

            ollama_messages = [
                {"role": m.role, "content": m.content}
                for m in messages
            ]

            response = await self._ollama.chat_with_tools(
                model=model,
                messages=ollama_messages,
                tools=tools,
                tool_choice=tool_choice,
            )

            self._call_counts[AIProvider.OLLAMA] += 1

            message = response.get("message", {})
            tool_calls_raw = message.get("tool_calls", [])

            # Parse tool calls
            tool_calls = []
            for tc in tool_calls_raw:
                func = tc.get("function", {})
                import json
                args_str = func.get("arguments", "{}")
                try:
                    args = json.loads(args_str) if isinstance(args_str, str) else args_str
                except json.JSONDecodeError:
                    args = {}
                tool_calls.append(ToolCall(
                    id=tc.get("id", ""),
                    type=tc.get("type", "function"),
                    function_name=func.get("name", ""),
                    arguments=args,
                ))

            return ChatResponse(
                content=message.get("content", ""),
                provider=AIProvider.OLLAMA,
                model=model,
                tokens_used=response.get("eval_count", 0),
                cost_usd=0.0,
                tool_calls=tool_calls,
            )

        except Exception as e:
            logger.error(f"Ollama function call failed: {e}")
            raise ProviderError(f"Ollama error: {str(e)}")

    async def _azure_chat(
        self,
        messages: list[ChatMessage],
        model: str,
    ) -> ChatResponse:
        """Chat using Azure OpenAI."""
        import httpx

        endpoint = self.config.azure_endpoint or os.getenv("AZURE_OPENAI_ENDPOINT")
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        deployment = self.config.azure_deployment or os.getenv("AZURE_OPENAI_DEPLOYMENT")
        api_version = self.config.azure_api_version

        if not all([endpoint, api_key, deployment]):
            raise ProviderUnavailable("Azure OpenAI not fully configured")

        url = f"{endpoint.rstrip('/')}/openai/deployments/{deployment}/chat/completions?api-version={api_version}"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers={"api-key": api_key},
                    json={
                        "messages": [
                            {"role": m.role, "content": m.content}
                            for m in messages
                        ],
                    },
                    timeout=60.0,
                )

                if response.status_code != 200:
                    raise ProviderError(f"Azure returned {response.status_code}: {response.text}")

                data = response.json()
                content = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})
                tokens = usage.get("total_tokens", 0)

                # Estimate cost (Azure pricing similar to OpenAI)
                cost = tokens * 0.00003  # Rough estimate

                self._call_counts[AIProvider.AZURE_OPENAI] += 1
                self._costs[AIProvider.AZURE_OPENAI] += cost

                return ChatResponse(
                    content=content,
                    provider=AIProvider.AZURE_OPENAI,
                    model=deployment,
                    tokens_used=tokens,
                    cost_usd=cost,
                )

        except httpx.HTTPError as e:
            raise ProviderError(f"Azure HTTP error: {str(e)}")

    async def _openai_chat(
        self,
        messages: list[ChatMessage],
        model: str,
    ) -> ChatResponse:
        """Chat using OpenAI."""
        import httpx

        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_API_BASE", "https://api.openai.com")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{base_url}/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={
                        "model": model,
                        "messages": [
                            {"role": m.role, "content": m.content}
                            for m in messages
                        ],
                    },
                    timeout=60.0,
                )

                if response.status_code != 200:
                    raise ProviderError(f"OpenAI returned {response.status_code}: {response.text}")

                data = response.json()
                content = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})
                tokens = usage.get("total_tokens", 0)

                # Estimate cost based on model
                if "gpt-4" in model:
                    cost = tokens * 0.00003
                else:
                    cost = tokens * 0.000002

                self._call_counts[AIProvider.OPENAI] += 1
                self._costs[AIProvider.OPENAI] += cost

                return ChatResponse(
                    content=content,
                    provider=AIProvider.OPENAI,
                    model=model,
                    tokens_used=tokens,
                    cost_usd=cost,
                )

        except httpx.HTTPError as e:
            raise ProviderError(f"OpenAI HTTP error: {str(e)}")

    async def _anthropic_chat(
        self,
        messages: list[ChatMessage],
        model: str,
    ) -> ChatResponse:
        """Chat using Anthropic Claude."""
        import httpx

        api_key = os.getenv("ANTHROPIC_API_KEY")

        # Extract system message
        system_msg = None
        filtered_messages = []
        for m in messages:
            if m.role == "system":
                system_msg = m.content
            else:
                filtered_messages.append({"role": m.role, "content": m.content})

        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "model": model,
                    "messages": filtered_messages,
                    "max_tokens": 4096,
                }
                if system_msg:
                    payload["system"] = system_msg

                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json=payload,
                    timeout=60.0,
                )

                if response.status_code != 200:
                    raise ProviderError(f"Anthropic returned {response.status_code}: {response.text}")

                data = response.json()
                content = data["content"][0]["text"]
                usage = data.get("usage", {})
                tokens = usage.get("input_tokens", 0) + usage.get("output_tokens", 0)

                # Claude pricing
                cost = tokens * 0.00003

                self._call_counts[AIProvider.ANTHROPIC] += 1
                self._costs[AIProvider.ANTHROPIC] += cost

                return ChatResponse(
                    content=content,
                    provider=AIProvider.ANTHROPIC,
                    model=model,
                    tokens_used=tokens,
                    cost_usd=cost,
                )

        except httpx.HTTPError as e:
            raise ProviderError(f"Anthropic HTTP error: {str(e)}")

    async def _azure_chat_with_tools(
        self,
        messages: list[ChatMessage],
        model: str,
        tools: list[dict],
        tool_choice: str = "auto",
    ) -> ChatResponse:
        """Chat with function calling using Azure OpenAI."""
        import httpx
        import json

        endpoint = self.config.azure_endpoint or os.getenv("AZURE_OPENAI_ENDPOINT")
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        deployment = self.config.azure_deployment or os.getenv("AZURE_OPENAI_DEPLOYMENT")
        api_version = self.config.azure_api_version

        if not all([endpoint, api_key, deployment]):
            raise ProviderUnavailable("Azure OpenAI not fully configured")

        url = f"{endpoint.rstrip('/')}/openai/deployments/{deployment}/chat/completions?api-version={api_version}"

        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "messages": [
                        {"role": m.role, "content": m.content}
                        for m in messages
                    ],
                    "tools": tools,
                }
                if tool_choice != "auto":
                    payload["tool_choice"] = tool_choice

                response = await client.post(
                    url,
                    headers={"api-key": api_key},
                    json=payload,
                    timeout=60.0,
                )

                if response.status_code != 200:
                    raise ProviderError(f"Azure returned {response.status_code}: {response.text}")

                data = response.json()
                message = data["choices"][0]["message"]
                content = message.get("content", "") or ""
                usage = data.get("usage", {})
                tokens = usage.get("total_tokens", 0)
                cost = tokens * 0.00003

                # Parse tool calls
                tool_calls = []
                for tc in message.get("tool_calls", []):
                    func = tc.get("function", {})
                    args_str = func.get("arguments", "{}")
                    try:
                        args = json.loads(args_str) if isinstance(args_str, str) else args_str
                    except json.JSONDecodeError:
                        args = {}
                    tool_calls.append(ToolCall(
                        id=tc.get("id", ""),
                        type=tc.get("type", "function"),
                        function_name=func.get("name", ""),
                        arguments=args,
                    ))

                self._call_counts[AIProvider.AZURE_OPENAI] += 1
                self._costs[AIProvider.AZURE_OPENAI] += cost

                return ChatResponse(
                    content=content,
                    provider=AIProvider.AZURE_OPENAI,
                    model=deployment,
                    tokens_used=tokens,
                    cost_usd=cost,
                    tool_calls=tool_calls,
                )

        except httpx.HTTPError as e:
            raise ProviderError(f"Azure HTTP error: {str(e)}")

    async def _openai_chat_with_tools(
        self,
        messages: list[ChatMessage],
        model: str,
        tools: list[dict],
        tool_choice: str = "auto",
    ) -> ChatResponse:
        """Chat with function calling using OpenAI."""
        import httpx
        import json

        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_API_BASE", "https://api.openai.com")

        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "model": model,
                    "messages": [
                        {"role": m.role, "content": m.content}
                        for m in messages
                    ],
                    "tools": tools,
                }
                if tool_choice != "auto":
                    payload["tool_choice"] = tool_choice

                response = await client.post(
                    f"{base_url}/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json=payload,
                    timeout=60.0,
                )

                if response.status_code != 200:
                    raise ProviderError(f"OpenAI returned {response.status_code}: {response.text}")

                data = response.json()
                message = data["choices"][0]["message"]
                content = message.get("content", "") or ""
                usage = data.get("usage", {})
                tokens = usage.get("total_tokens", 0)

                if "gpt-4" in model:
                    cost = tokens * 0.00003
                else:
                    cost = tokens * 0.000002

                # Parse tool calls
                tool_calls = []
                for tc in message.get("tool_calls", []):
                    func = tc.get("function", {})
                    args_str = func.get("arguments", "{}")
                    try:
                        args = json.loads(args_str) if isinstance(args_str, str) else args_str
                    except json.JSONDecodeError:
                        args = {}
                    tool_calls.append(ToolCall(
                        id=tc.get("id", ""),
                        type=tc.get("type", "function"),
                        function_name=func.get("name", ""),
                        arguments=args,
                    ))

                self._call_counts[AIProvider.OPENAI] += 1
                self._costs[AIProvider.OPENAI] += cost

                return ChatResponse(
                    content=content,
                    provider=AIProvider.OPENAI,
                    model=model,
                    tokens_used=tokens,
                    cost_usd=cost,
                    tool_calls=tool_calls,
                )

        except httpx.HTTPError as e:
            raise ProviderError(f"OpenAI HTTP error: {str(e)}")

    async def _anthropic_chat_with_tools(
        self,
        messages: list[ChatMessage],
        model: str,
        tools: list[dict],
        tool_choice: str = "auto",
    ) -> ChatResponse:
        """Chat with function calling using Anthropic Claude."""
        import httpx

        api_key = os.getenv("ANTHROPIC_API_KEY")

        # Extract system message
        system_msg = None
        filtered_messages = []
        for m in messages:
            if m.role == "system":
                system_msg = m.content
            else:
                filtered_messages.append({"role": m.role, "content": m.content})

        # Convert OpenAI tool format to Anthropic format
        anthropic_tools = []
        for tool in tools:
            if tool.get("type") == "function":
                func = tool.get("function", {})
                anthropic_tools.append({
                    "name": func.get("name", ""),
                    "description": func.get("description", ""),
                    "input_schema": func.get("parameters", {}),
                })

        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "model": model,
                    "messages": filtered_messages,
                    "max_tokens": 4096,
                    "tools": anthropic_tools,
                }
                if system_msg:
                    payload["system"] = system_msg

                # Anthropic uses different tool_choice format
                if tool_choice == "none":
                    payload["tool_choice"] = {"type": "none"}
                elif tool_choice != "auto":
                    # Specific tool requested
                    payload["tool_choice"] = {"type": "tool", "name": tool_choice}
                else:
                    payload["tool_choice"] = {"type": "auto"}

                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json=payload,
                    timeout=60.0,
                )

                if response.status_code != 200:
                    raise ProviderError(f"Anthropic returned {response.status_code}: {response.text}")

                data = response.json()
                usage = data.get("usage", {})
                tokens = usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
                cost = tokens * 0.00003

                # Parse content and tool calls from Anthropic format
                content = ""
                tool_calls = []
                for block in data.get("content", []):
                    if block.get("type") == "text":
                        content += block.get("text", "")
                    elif block.get("type") == "tool_use":
                        tool_calls.append(ToolCall(
                            id=block.get("id", ""),
                            type="function",
                            function_name=block.get("name", ""),
                            arguments=block.get("input", {}),
                        ))

                self._call_counts[AIProvider.ANTHROPIC] += 1
                self._costs[AIProvider.ANTHROPIC] += cost

                return ChatResponse(
                    content=content,
                    provider=AIProvider.ANTHROPIC,
                    model=model,
                    tokens_used=tokens,
                    cost_usd=cost,
                    tool_calls=tool_calls,
                )

        except httpx.HTTPError as e:
            raise ProviderError(f"Anthropic HTTP error: {str(e)}")

    def get_costs(self) -> dict[str, float]:
        """Get accumulated costs per provider."""
        return {
            provider.value: cost
            for provider, cost in self._costs.items()
            if cost > 0
        }

    def get_stats(self) -> dict:
        """Get usage statistics."""
        return {
            "mode": self.config.mode.value,
            "strict_mode": self.config.strict_mode,
            "default_provider": self.config.default_provider.value,
            "call_counts": {
                p.value: count
                for p, count in self._call_counts.items()
                if count > 0
            },
            "costs_usd": self.get_costs(),
            "total_cost_usd": sum(self._costs.values()),
            "savings_vs_cloud": self._calculate_savings(),
        }

    def _calculate_savings(self) -> float:
        """Calculate savings from using Ollama vs cloud."""
        ollama_calls = self._call_counts[AIProvider.OLLAMA]
        # Assume average 1000 tokens per call, GPT-4o pricing
        estimated_cloud_cost = ollama_calls * 1000 * 0.00003
        return estimated_cloud_cost


# Singleton instance
_router: Optional[ProviderRouter] = None


def get_provider_router() -> ProviderRouter:
    """Get or create the provider router singleton."""
    global _router
    if _router is None:
        _router = ProviderRouter()
    return _router


def reset_provider_router() -> None:
    """Reset the provider router (for testing or config changes)."""
    global _router
    _router = None
