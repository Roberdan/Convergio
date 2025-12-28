"""
AI Provider Configuration and Management

This module provides:
- Provider modes (Ollama-only, Azure-only, Hybrid, Cloud-first)
- Feature capability mapping
- Per-feature and per-agent provider configuration
- Strict mode enforcement (no silent fallback to cloud)

Copyright (c) 2025 Convergio.io
"""

import os
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class ProviderMode(str, Enum):
    """
    AI Provider operation modes.

    Users can choose how they want Convergio to use AI:
    - OLLAMA_ONLY: 100% local, FREE, no cloud calls ever
    - AZURE_ONLY: Enterprise Azure OpenAI only (GDPR/SOC2 compliant)
    - HYBRID: Local for simple tasks, cloud for complex
    - CLOUD_FIRST: Best quality using OpenAI/Anthropic
    """
    OLLAMA_ONLY = "ollama_only"
    AZURE_ONLY = "azure_only"
    HYBRID = "hybrid"
    CLOUD_FIRST = "cloud_first"


class AIProvider(str, Enum):
    """Available AI providers."""
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE_OPENAI = "azure_openai"
    PERPLEXITY = "perplexity"
    LOCAL_EMBEDDINGS = "local_embeddings"  # sentence-transformers


class FeatureCapability(str, Enum):
    """
    AI capabilities required by different features.

    Used to determine if a provider can handle a specific feature.
    """
    CHAT_SIMPLE = "chat_simple"           # Basic text generation
    CHAT_COMPLEX = "chat_complex"         # Long context, reasoning
    CODE_REVIEW = "code_review"           # Code understanding
    EMBEDDINGS = "embeddings"             # Vector embeddings
    FUNCTION_CALLING = "function_calling" # Tool use
    VISION = "vision"                     # Image analysis
    VOICE_REALTIME = "voice_realtime"     # Speech-to-text, TTS
    WEB_SEARCH = "web_search"             # Real-time web search


class ProviderCapabilities(BaseModel):
    """Capabilities of a specific provider."""
    provider: AIProvider
    capabilities: list[FeatureCapability]
    requires_api_key: bool = True
    requires_gpu: bool = False
    is_local: bool = False
    is_free: bool = False
    context_window: int = 8192
    supports_streaming: bool = True


class FeatureProviderConfig(BaseModel):
    """Configuration for a specific feature's provider."""
    provider: AIProvider
    model: str
    fallback_provider: Optional[AIProvider] = None
    fallback_model: Optional[str] = None


class AgentProviderConfig(BaseModel):
    """Per-agent provider override configuration."""
    agent_id: str
    provider: AIProvider
    model: str


class AIConfig(BaseModel):
    """
    Complete AI configuration for Convergio.

    Supports:
    - Global provider mode
    - Strict mode (no cloud fallback)
    - Per-feature provider configuration
    - Per-agent provider overrides
    """
    mode: ProviderMode = Field(
        default=ProviderMode.HYBRID,
        description="Global AI provider mode"
    )
    strict_mode: bool = Field(
        default=False,
        description="If true, NEVER fallback to cloud providers"
    )
    default_provider: AIProvider = Field(
        default=AIProvider.OLLAMA,
        description="Default provider when mode is hybrid"
    )
    default_model: str = Field(
        default="llama3.2:latest",
        description="Default model for the default provider"
    )

    # Feature-level overrides
    features: dict[FeatureCapability, FeatureProviderConfig] = Field(
        default_factory=dict,
        description="Per-feature provider configuration"
    )

    # Agent-level overrides
    agents: dict[str, AgentProviderConfig] = Field(
        default_factory=dict,
        description="Per-agent provider overrides"
    )

    # Provider-specific configurations
    ollama_host: str = Field(
        default="http://localhost:11434",
        description="Ollama server URL"
    )
    azure_endpoint: Optional[str] = Field(
        default=None,
        description="Azure OpenAI endpoint"
    )
    azure_deployment: Optional[str] = Field(
        default=None,
        description="Azure OpenAI deployment name"
    )
    azure_api_version: str = Field(
        default="2024-02-15-preview",
        description="Azure OpenAI API version"
    )


# Capability matrix: which providers support which capabilities
CAPABILITY_MATRIX: dict[AIProvider, list[FeatureCapability]] = {
    AIProvider.OLLAMA: [
        FeatureCapability.CHAT_SIMPLE,
        FeatureCapability.CHAT_COMPLEX,  # Slower but works
        FeatureCapability.CODE_REVIEW,
        FeatureCapability.EMBEDDINGS,
        FeatureCapability.FUNCTION_CALLING,  # llama3.1+, qwen2.5+
        FeatureCapability.VISION,  # llava, bakllava
    ],
    AIProvider.OPENAI: [
        FeatureCapability.CHAT_SIMPLE,
        FeatureCapability.CHAT_COMPLEX,
        FeatureCapability.CODE_REVIEW,
        FeatureCapability.EMBEDDINGS,
        FeatureCapability.FUNCTION_CALLING,
        FeatureCapability.VISION,
    ],
    AIProvider.ANTHROPIC: [
        FeatureCapability.CHAT_SIMPLE,
        FeatureCapability.CHAT_COMPLEX,
        FeatureCapability.CODE_REVIEW,
        FeatureCapability.VISION,
    ],
    AIProvider.AZURE_OPENAI: [
        FeatureCapability.CHAT_SIMPLE,
        FeatureCapability.CHAT_COMPLEX,
        FeatureCapability.CODE_REVIEW,
        FeatureCapability.EMBEDDINGS,
        FeatureCapability.FUNCTION_CALLING,
        FeatureCapability.VISION,
        FeatureCapability.VOICE_REALTIME,  # Azure-exclusive
    ],
    AIProvider.PERPLEXITY: [
        FeatureCapability.CHAT_SIMPLE,
        FeatureCapability.WEB_SEARCH,  # Perplexity-exclusive
    ],
    AIProvider.LOCAL_EMBEDDINGS: [
        FeatureCapability.EMBEDDINGS,
    ],
}


# Provider metadata
PROVIDER_INFO: dict[AIProvider, ProviderCapabilities] = {
    AIProvider.OLLAMA: ProviderCapabilities(
        provider=AIProvider.OLLAMA,
        capabilities=CAPABILITY_MATRIX[AIProvider.OLLAMA],
        requires_api_key=False,
        requires_gpu=True,
        is_local=True,
        is_free=True,
        context_window=32768,  # Varies by model
    ),
    AIProvider.OPENAI: ProviderCapabilities(
        provider=AIProvider.OPENAI,
        capabilities=CAPABILITY_MATRIX[AIProvider.OPENAI],
        requires_api_key=True,
        context_window=128000,
    ),
    AIProvider.ANTHROPIC: ProviderCapabilities(
        provider=AIProvider.ANTHROPIC,
        capabilities=CAPABILITY_MATRIX[AIProvider.ANTHROPIC],
        requires_api_key=True,
        context_window=200000,
    ),
    AIProvider.AZURE_OPENAI: ProviderCapabilities(
        provider=AIProvider.AZURE_OPENAI,
        capabilities=CAPABILITY_MATRIX[AIProvider.AZURE_OPENAI],
        requires_api_key=True,
        context_window=128000,
    ),
    AIProvider.PERPLEXITY: ProviderCapabilities(
        provider=AIProvider.PERPLEXITY,
        capabilities=CAPABILITY_MATRIX[AIProvider.PERPLEXITY],
        requires_api_key=True,
        context_window=127000,
    ),
    AIProvider.LOCAL_EMBEDDINGS: ProviderCapabilities(
        provider=AIProvider.LOCAL_EMBEDDINGS,
        capabilities=CAPABILITY_MATRIX[AIProvider.LOCAL_EMBEDDINGS],
        requires_api_key=False,
        is_local=True,
        is_free=True,
        context_window=512,
        supports_streaming=False,
    ),
}


def get_ai_config_from_env() -> AIConfig:
    """
    Load AI configuration from environment variables.

    Returns an AIConfig instance with settings from environment.
    """
    mode_str = os.getenv("AI_PROVIDER_MODE", "hybrid")
    try:
        mode = ProviderMode(mode_str)
    except ValueError:
        mode = ProviderMode.HYBRID

    strict_mode = os.getenv("AI_STRICT_MODE", "false").lower() == "true"

    # Determine default provider based on mode
    if mode == ProviderMode.OLLAMA_ONLY:
        default_provider = AIProvider.OLLAMA
        default_model = os.getenv("OLLAMA_DEFAULT_MODEL", "llama3.2:latest")
    elif mode == ProviderMode.AZURE_ONLY:
        default_provider = AIProvider.AZURE_OPENAI
        default_model = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
    elif mode == ProviderMode.CLOUD_FIRST:
        default_provider = AIProvider.OPENAI
        default_model = os.getenv("DEFAULT_AI_MODEL", "gpt-4o")
    else:  # HYBRID
        default_provider = AIProvider.OLLAMA
        default_model = os.getenv("OLLAMA_DEFAULT_MODEL", "llama3.2:latest")

    return AIConfig(
        mode=mode,
        strict_mode=strict_mode,
        default_provider=default_provider,
        default_model=default_model,
        ollama_host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        azure_api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
    )


def can_provider_handle_capability(
    provider: AIProvider,
    capability: FeatureCapability
) -> bool:
    """Check if a provider can handle a specific capability."""
    if provider not in CAPABILITY_MATRIX:
        return False
    return capability in CAPABILITY_MATRIX[provider]


def get_provider_for_capability(
    capability: FeatureCapability,
    config: AIConfig
) -> tuple[AIProvider, str]:
    """
    Get the best provider for a capability based on configuration.

    Respects:
    - Provider mode (ollama_only, azure_only, etc.)
    - Strict mode (no fallback)
    - Feature-level overrides

    Returns:
        Tuple of (provider, model)

    Raises:
        ValueError: If no provider can handle the capability and strict mode is on
    """
    # Check for feature-level override first
    if capability in config.features:
        feature_config = config.features[capability]
        return feature_config.provider, feature_config.model

    # Get default provider for the mode
    provider = config.default_provider
    model = config.default_model

    # Check if default provider can handle the capability
    if can_provider_handle_capability(provider, capability):
        return provider, model

    # If strict mode, fail instead of falling back
    if config.strict_mode:
        raise ValueError(
            f"Provider {provider.value} cannot handle capability {capability.value} "
            f"and strict mode is enabled. No fallback allowed."
        )

    # Find a provider that can handle this capability
    for p, caps in CAPABILITY_MATRIX.items():
        if capability in caps:
            # Skip local providers if we need cloud capabilities
            if config.mode == ProviderMode.CLOUD_FIRST and PROVIDER_INFO[p].is_local:
                continue
            # Skip cloud providers if mode is local-only
            if config.mode == ProviderMode.OLLAMA_ONLY and not PROVIDER_INFO[p].is_local:
                continue
            return p, _get_default_model_for_provider(p)

    raise ValueError(f"No provider can handle capability {capability.value}")


def get_provider_for_agent(
    agent_id: str,
    config: AIConfig
) -> tuple[AIProvider, str]:
    """
    Get the provider configuration for a specific agent.

    Checks for agent-level override first, then falls back to default.

    Returns:
        Tuple of (provider, model)
    """
    if agent_id in config.agents:
        agent_config = config.agents[agent_id]
        return agent_config.provider, agent_config.model

    return config.default_provider, config.default_model


def _get_default_model_for_provider(provider: AIProvider) -> str:
    """Get the default model for a provider."""
    defaults = {
        AIProvider.OLLAMA: os.getenv("OLLAMA_DEFAULT_MODEL", "llama3.2:latest"),
        AIProvider.OPENAI: os.getenv("DEFAULT_AI_MODEL", "gpt-4o"),
        AIProvider.ANTHROPIC: "claude-sonnet-4-20250514",
        AIProvider.AZURE_OPENAI: os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
        AIProvider.PERPLEXITY: "sonar",
        AIProvider.LOCAL_EMBEDDINGS: "all-MiniLM-L6-v2",
    }
    return defaults.get(provider, "gpt-4o")
