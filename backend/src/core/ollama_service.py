"""
Ollama Service - Local AI Integration

This module provides:
- Health check for Ollama server
- Model listing and management
- Model capabilities mapping
- GPU detection and recommendations

Copyright (c) 2025 Convergio.io
"""

import os
import httpx
import logging
from typing import Optional
from pydantic import BaseModel
from enum import Enum

logger = logging.getLogger(__name__)


class OllamaModelCapability(str, Enum):
    """Capabilities that Ollama models can have."""
    CHAT = "chat"
    EMBEDDINGS = "embeddings"
    VISION = "vision"
    FUNCTION_CALLING = "function_calling"
    CODE = "code"


class OllamaModel(BaseModel):
    """Ollama model information."""
    name: str
    size: int  # Size in bytes
    digest: str
    modified_at: str
    capabilities: list[OllamaModelCapability] = []


class OllamaStatus(BaseModel):
    """Ollama server status."""
    available: bool
    version: Optional[str] = None
    models: list[OllamaModel] = []
    gpu_available: bool = False
    gpu_name: Optional[str] = None
    error: Optional[str] = None


# Known model capabilities (based on model names)
MODEL_CAPABILITIES: dict[str, list[OllamaModelCapability]] = {
    "llama3": [OllamaModelCapability.CHAT, OllamaModelCapability.FUNCTION_CALLING],
    "llama3.1": [OllamaModelCapability.CHAT, OllamaModelCapability.FUNCTION_CALLING],
    "llama3.2": [OllamaModelCapability.CHAT, OllamaModelCapability.FUNCTION_CALLING],
    "qwen2": [OllamaModelCapability.CHAT, OllamaModelCapability.FUNCTION_CALLING],
    "qwen2.5": [OllamaModelCapability.CHAT, OllamaModelCapability.FUNCTION_CALLING, OllamaModelCapability.CODE],
    "qwen2.5-coder": [OllamaModelCapability.CHAT, OllamaModelCapability.CODE],
    "codellama": [OllamaModelCapability.CHAT, OllamaModelCapability.CODE],
    "mistral": [OllamaModelCapability.CHAT],
    "mixtral": [OllamaModelCapability.CHAT, OllamaModelCapability.FUNCTION_CALLING],
    "llava": [OllamaModelCapability.CHAT, OllamaModelCapability.VISION],
    "bakllava": [OllamaModelCapability.CHAT, OllamaModelCapability.VISION],
    "nomic-embed-text": [OllamaModelCapability.EMBEDDINGS],
    "mxbai-embed-large": [OllamaModelCapability.EMBEDDINGS],
    "all-minilm": [OllamaModelCapability.EMBEDDINGS],
}


def _get_model_capabilities(model_name: str) -> list[OllamaModelCapability]:
    """
    Determine model capabilities based on name.

    Matches against known model prefixes.
    """
    # Remove tag (e.g., :latest, :7b)
    base_name = model_name.split(":")[0].lower()

    # Check for exact match first
    if base_name in MODEL_CAPABILITIES:
        return MODEL_CAPABILITIES[base_name]

    # Check for prefix match
    for known_model, caps in MODEL_CAPABILITIES.items():
        if base_name.startswith(known_model):
            return caps

    # Default: assume basic chat capability
    return [OllamaModelCapability.CHAT]


class OllamaService:
    """
    Service for interacting with Ollama.

    Provides health checks, model management, and capability detection.
    """

    def __init__(self, host: Optional[str] = None):
        """
        Initialize Ollama service.

        Args:
            host: Ollama server URL (default: from OLLAMA_HOST env var or localhost:11434)
        """
        self.host = host or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self._client = httpx.AsyncClient(timeout=10.0)

    async def health_check(self) -> OllamaStatus:
        """
        Check if Ollama is running and get status.

        Returns:
            OllamaStatus with availability, version, models, and GPU info
        """
        try:
            # Check if Ollama is responding
            response = await self._client.get(f"{self.host}/api/version")

            if response.status_code != 200:
                return OllamaStatus(
                    available=False,
                    error=f"Ollama returned status {response.status_code}"
                )

            version_data = response.json()
            version = version_data.get("version", "unknown")

            # Get list of models
            models = await self._list_models()

            # Check GPU availability
            gpu_available, gpu_name = await self._check_gpu()

            return OllamaStatus(
                available=True,
                version=version,
                models=models,
                gpu_available=gpu_available,
                gpu_name=gpu_name,
            )

        except httpx.ConnectError:
            return OllamaStatus(
                available=False,
                error="Cannot connect to Ollama. Is it running? Install from https://ollama.ai"
            )
        except httpx.TimeoutException:
            return OllamaStatus(
                available=False,
                error="Ollama connection timed out. Server may be overloaded."
            )
        except Exception as e:
            logger.exception("Unexpected error checking Ollama status")
            return OllamaStatus(
                available=False,
                error=f"Unexpected error: {str(e)}"
            )

    async def _list_models(self) -> list[OllamaModel]:
        """Get list of available models."""
        try:
            response = await self._client.get(f"{self.host}/api/tags")
            if response.status_code != 200:
                return []

            data = response.json()
            models = []

            for model_data in data.get("models", []):
                name = model_data.get("name", "")
                models.append(OllamaModel(
                    name=name,
                    size=model_data.get("size", 0),
                    digest=model_data.get("digest", ""),
                    modified_at=model_data.get("modified_at", ""),
                    capabilities=_get_model_capabilities(name),
                ))

            return models

        except Exception as e:
            logger.warning(f"Failed to list Ollama models: {e}")
            return []

    async def _check_gpu(self) -> tuple[bool, Optional[str]]:
        """
        Check if GPU is available for Ollama.

        Returns:
            Tuple of (gpu_available, gpu_name)
        """
        try:
            # Try to get GPU info from Ollama's show endpoint with a common model
            # This is a heuristic - Ollama doesn't have a dedicated GPU endpoint
            response = await self._client.get(f"{self.host}/api/ps")

            if response.status_code == 200:
                data = response.json()
                # If any model is running, Ollama has GPU access (or is using CPU)
                running_models = data.get("models", [])
                for model in running_models:
                    # Check for GPU indicators in model info
                    if model.get("size_vram", 0) > 0:
                        return True, "GPU detected (VRAM in use)"

            # Fallback: check environment for CUDA
            import shutil
            if shutil.which("nvidia-smi"):
                return True, "NVIDIA GPU available"

            return False, None

        except Exception:
            return False, None

    async def pull_model(self, model_name: str) -> bool:
        """
        Pull (download) a model from Ollama registry.

        Args:
            model_name: Name of model to pull (e.g., "llama3.2:latest")

        Returns:
            True if pull started successfully
        """
        try:
            response = await self._client.post(
                f"{self.host}/api/pull",
                json={"name": model_name},
                timeout=None  # Pull can take a long time
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to pull model {model_name}: {e}")
            return False

    async def generate(
        self,
        model: str,
        prompt: str,
        system: Optional[str] = None,
        stream: bool = False,
    ) -> dict:
        """
        Generate completion using Ollama.

        Args:
            model: Model name
            prompt: User prompt
            system: System prompt (optional)
            stream: Whether to stream response

        Returns:
            Response dict with generated text
        """
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
        }
        if system:
            payload["system"] = system

        try:
            response = await self._client.post(
                f"{self.host}/api/generate",
                json=payload,
                timeout=60.0,
            )

            if response.status_code != 200:
                raise Exception(f"Ollama returned status {response.status_code}")

            return response.json()

        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise

    async def chat(
        self,
        model: str,
        messages: list[dict],
        stream: bool = False,
        tools: Optional[list[dict]] = None,
        tool_choice: Optional[str] = None,
    ) -> dict:
        """
        Chat completion using Ollama (OpenAI-compatible format).

        Args:
            model: Model name
            messages: List of message dicts with role and content
            stream: Whether to stream response
            tools: Optional list of function/tool definitions (OpenAI format)
            tool_choice: Optional tool choice ("auto", "none", or specific tool)

        Returns:
            Response dict with message (and tool_calls if function calling)
        """
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
        }

        # Add tools for function calling (Ollama 0.4+ supports this)
        if tools:
            payload["tools"] = tools
            if tool_choice:
                payload["tool_choice"] = tool_choice

        try:
            response = await self._client.post(
                f"{self.host}/api/chat",
                json=payload,
                timeout=60.0,
            )

            if response.status_code != 200:
                raise Exception(f"Ollama returned status {response.status_code}")

            return response.json()

        except Exception as e:
            logger.error(f"Ollama chat failed: {e}")
            raise

    async def chat_with_tools(
        self,
        model: str,
        messages: list[dict],
        tools: list[dict],
        tool_choice: str = "auto",
    ) -> dict:
        """
        Chat with function/tool calling support.

        Requires Ollama 0.4+ and a compatible model (llama3.1+, qwen2+, mixtral).

        Args:
            model: Model name (must support function calling)
            messages: List of message dicts (including tool role for function results)
            tools: List of tool definitions in OpenAI format:
                   [{"type": "function", "function": {"name": "...", "parameters": {...}}}]
            tool_choice: "auto" (model decides), "none" (no tools), or
                         {"type": "function", "function": {"name": "specific_function"}}

        Returns:
            Response dict with message. If tool call requested:
            {
                "message": {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {
                            "id": "call_xxx",
                            "type": "function",
                            "function": {"name": "func_name", "arguments": "{}"}
                        }
                    ]
                }
            }
        """
        # Validate model supports function calling
        capabilities = _get_model_capabilities(model)
        if OllamaModelCapability.FUNCTION_CALLING not in capabilities:
            logger.warning(
                f"Model {model} may not support function calling. "
                f"Known function-calling models: llama3.1+, qwen2+, mixtral"
            )

        return await self.chat(
            model=model,
            messages=messages,
            stream=False,  # Streaming not supported with tools
            tools=tools,
            tool_choice=tool_choice,
        )

    async def execute_tool_loop(
        self,
        model: str,
        messages: list[dict],
        tools: list[dict],
        tool_executor: callable,
        max_iterations: int = 10,
    ) -> dict:
        """
        Execute a complete tool-calling loop until the model stops requesting tools.

        Args:
            model: Model name
            messages: Initial conversation messages
            tools: Available tool definitions
            tool_executor: Async function that executes tools:
                           async def executor(name: str, arguments: dict) -> str
            max_iterations: Maximum tool calls before stopping

        Returns:
            Final response dict with complete conversation
        """
        conversation = list(messages)
        iterations = 0

        while iterations < max_iterations:
            response = await self.chat_with_tools(
                model=model,
                messages=conversation,
                tools=tools,
            )

            message = response.get("message", {})
            tool_calls = message.get("tool_calls", [])

            if not tool_calls:
                # No more tool calls - return final response
                return response

            # Add assistant message with tool calls
            conversation.append({
                "role": "assistant",
                "content": message.get("content", ""),
                "tool_calls": tool_calls,
            })

            # Execute each tool and add results
            for tool_call in tool_calls:
                func = tool_call.get("function", {})
                func_name = func.get("name", "")
                func_args = func.get("arguments", "{}")

                # Parse arguments (Ollama returns JSON string)
                import json
                try:
                    args_dict = json.loads(func_args) if isinstance(func_args, str) else func_args
                except json.JSONDecodeError:
                    args_dict = {}

                # Execute tool
                try:
                    result = await tool_executor(func_name, args_dict)
                except Exception as e:
                    result = f"Error executing {func_name}: {str(e)}"

                # Add tool result to conversation
                conversation.append({
                    "role": "tool",
                    "tool_call_id": tool_call.get("id", ""),
                    "name": func_name,
                    "content": str(result),
                })

            iterations += 1

        logger.warning(f"Tool loop reached max iterations ({max_iterations})")
        return response

    async def embeddings(self, model: str, text: str) -> list[float]:
        """
        Generate embeddings using Ollama.

        Args:
            model: Embedding model name (e.g., "nomic-embed-text")
            text: Text to embed

        Returns:
            List of embedding floats
        """
        try:
            response = await self._client.post(
                f"{self.host}/api/embeddings",
                json={"model": model, "prompt": text},
                timeout=30.0,
            )

            if response.status_code != 200:
                raise Exception(f"Ollama returned status {response.status_code}")

            data = response.json()
            return data.get("embedding", [])

        except Exception as e:
            logger.error(f"Ollama embeddings failed: {e}")
            raise

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()


# Singleton instance
_ollama_service: Optional[OllamaService] = None


def get_ollama_service() -> OllamaService:
    """Get or create the Ollama service singleton."""
    global _ollama_service
    if _ollama_service is None:
        _ollama_service = OllamaService()
    return _ollama_service
