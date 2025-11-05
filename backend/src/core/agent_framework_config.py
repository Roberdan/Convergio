"""
Microsoft Agent Framework Configuration
Centralized configuration for Agent Framework components
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
import structlog

from src.core.config import get_settings

logger = structlog.get_logger()


class AgentFrameworkConfig(BaseModel):
    """Configuration for Microsoft Agent Framework"""

    # Model Configuration
    model_provider: str = Field(default="openai", description="AI model provider")
    model_name: str = Field(default="gpt-4", description="Model to use for agents")
    api_key: Optional[str] = Field(default=None, description="API key for model provider")
    api_base: Optional[str] = Field(default=None, description="Custom API base URL")

    # Workflow Configuration
    enable_checkpointing: bool = Field(default=True, description="Enable workflow checkpointing")
    checkpoint_store: str = Field(default="redis", description="Checkpoint storage backend")
    max_workflow_iterations: int = Field(default=50, description="Max workflow iterations")

    # Agent Configuration
    default_max_iterations: int = Field(default=10, description="Default max iterations per agent")
    enable_tool_execution: bool = Field(default=True, description="Enable tool execution")
    tool_timeout: int = Field(default=30, description="Tool execution timeout in seconds")

    # Performance
    concurrent_agents: int = Field(default=5, description="Max concurrent agent executions")
    enable_caching: bool = Field(default=True, description="Enable response caching")
    cache_ttl: int = Field(default=300, description="Cache TTL in seconds")

    # Observability
    enable_telemetry: bool = Field(default=True, description="Enable OpenTelemetry")
    telemetry_endpoint: Optional[str] = Field(default=None, description="Telemetry endpoint")
    log_level: str = Field(default="INFO", description="Logging level")

    # Safety
    enable_safety_checks: bool = Field(default=True, description="Enable safety validation")
    max_tokens_per_request: int = Field(default=4000, description="Max tokens per request")
    rate_limit_per_minute: int = Field(default=60, description="Rate limit per minute")

    class Config:
        env_prefix = "AGENT_FRAMEWORK_"


def get_agent_framework_config() -> AgentFrameworkConfig:
    """
    Get Agent Framework configuration from settings.

    Returns:
        AgentFrameworkConfig instance
    """
    settings = get_settings()

    return AgentFrameworkConfig(
        model_provider=getattr(settings, "MODEL_PROVIDER", "openai"),
        model_name=getattr(settings, "OPENAI_MODEL", "gpt-4"),
        api_key=getattr(settings, "OPENAI_API_KEY", None),
        enable_checkpointing=getattr(settings, "ENABLE_WORKFLOW_CHECKPOINTING", True),
        checkpoint_store=getattr(settings, "CHECKPOINT_STORE", "redis"),
        max_workflow_iterations=getattr(settings, "MAX_WORKFLOW_ITERATIONS", 50),
        default_max_iterations=getattr(settings, "DEFAULT_AGENT_MAX_ITERATIONS", 10),
        enable_tool_execution=getattr(settings, "ENABLE_TOOL_EXECUTION", True),
        tool_timeout=getattr(settings, "TOOL_TIMEOUT", 30),
        concurrent_agents=getattr(settings, "CONCURRENT_AGENTS", 5),
        enable_caching=getattr(settings, "ENABLE_AGENT_CACHING", True),
        cache_ttl=getattr(settings, "AGENT_CACHE_TTL", 300),
        enable_telemetry=getattr(settings, "ENABLE_TELEMETRY", True),
        telemetry_endpoint=getattr(settings, "TELEMETRY_ENDPOINT", None),
        log_level=getattr(settings, "LOG_LEVEL", "INFO"),
        enable_safety_checks=getattr(settings, "ENABLE_SAFETY_CHECKS", True),
        max_tokens_per_request=getattr(settings, "MAX_TOKENS_PER_REQUEST", 4000),
        rate_limit_per_minute=getattr(settings, "RATE_LIMIT_PER_MINUTE_API", 60),
    )


def get_agent_framework_client(config: Optional[AgentFrameworkConfig] = None) -> Any:
    """
    Initialize Agent Framework client based on configuration.

    Args:
        config: AgentFrameworkConfig instance (uses default if None)

    Returns:
        Agent Framework client instance
    """
    if config is None:
        config = get_agent_framework_config()

    try:
        # Import based on provider
        if config.model_provider.lower() == "openai":
            from agent_framework.openai import OpenAIChatClient

            client_kwargs = {}
            if config.api_key:
                client_kwargs['api_key'] = config.api_key
            if config.model_name:
                client_kwargs['model'] = config.model_name

            client = OpenAIChatClient(**client_kwargs)

        elif config.model_provider.lower() == "azure":
            from agent_framework.azure import AzureOpenAIChatClient
            from azure.identity import AzureCliCredential

            # Azure client uses Azure CLI credentials by default
            client = AzureOpenAIChatClient(credential=AzureCliCredential())

        else:
            raise ValueError(f"Unsupported model provider: {config.model_provider}")

        logger.info(
            "Agent Framework client initialized",
            provider=config.model_provider,
            model=config.model_name,
        )

        return client

    except ImportError as e:
        logger.error(f"Agent Framework not installed: {e}")
        logger.info("Falling back to AutoGen client")

        # Fallback to AutoGen during migration
        from src.core.ai_clients import get_autogen_client

        return get_autogen_client(provider=config.model_provider)

    except Exception as e:
        logger.error(f"Failed to initialize Agent Framework client: {e}")
        raise


def get_checkpoint_store(config: Optional[AgentFrameworkConfig] = None):
    """
    Get checkpoint store for workflow persistence.

    Args:
        config: AgentFrameworkConfig instance

    Returns:
        Checkpoint store instance
    """
    if config is None:
        config = get_agent_framework_config()

    if not config.enable_checkpointing:
        return None

    try:
        if config.checkpoint_store == "redis":
            # Note: Agent Framework might not have Redis checkpoint store
            # Fallback to in-memory for now
            logger.warning("Redis checkpoint store not yet implemented, using in-memory")
            from agent_framework import InMemoryCheckpointStorage

            store = InMemoryCheckpointStorage()
            logger.info("In-memory checkpoint store initialized (Redis fallback)")
            return store

        elif config.checkpoint_store == "memory":
            from agent_framework import InMemoryCheckpointStorage

            store = InMemoryCheckpointStorage()
            logger.info("In-memory checkpoint store initialized")
            return store

        else:
            logger.warning(
                f"Unknown checkpoint store: {config.checkpoint_store}, using in-memory"
            )
            from agent_framework import InMemoryCheckpointStorage

            return InMemoryCheckpointStorage()

    except ImportError:
        logger.warning("Agent Framework checkpoint store not available")
        return None
    except Exception as e:
        logger.error(f"Failed to initialize checkpoint store: {e}")
        return None
