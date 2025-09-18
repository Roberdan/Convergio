"""
GroupChat Initializer
Sets up model client and agent loader for AutoGen GroupChat.
"""

from typing import Dict
import structlog
import logging

from autogen_ext.models.openai import OpenAIChatCompletionClient

from ..agent_loader import DynamicAgentLoader, AgentMetadata
from src.agents.utils.config import get_settings


logger = structlog.get_logger()

# Configure detailed OpenAI logging
openai_logger = logging.getLogger("openai")
openai_logger.setLevel(logging.DEBUG)
httpx_logger = logging.getLogger("httpx")
httpx_logger.setLevel(logging.DEBUG)

# Create console handler for OpenAI conversations
if not openai_logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '🤖 OPENAI-%(name)s [%(levelname)s] %(asctime)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    openai_logger.addHandler(console_handler)
    httpx_logger.addHandler(console_handler)
    openai_logger.propagate = False
    httpx_logger.propagate = False


def initialize_model_client() -> OpenAIChatCompletionClient:
    """Initialize model client using centralized AI client manager"""
    from ....core.ai_clients import get_autogen_client
    
    settings = get_settings()
    
    try:
        # Use centralized client manager
        client = get_autogen_client(provider="openai", model=settings.default_ai_model)
        
        logger.info("🔍 Model client initialized via AI Client Manager", 
                   model=settings.default_ai_model,
                   provider="openai")
        
        return client
        
    except Exception as e:
        logger.error("❌ Failed to initialize model client", error=str(e))
        
        # Fallback to direct initialization
        logger.info("🔄 Falling back to direct client initialization")
        
        client_params = {
            "model": settings.default_ai_model,
            "api_key": settings.openai_api_key,
        }
        
        if settings.openai_api_base and settings.openai_api_base.strip():
            client_params["base_url"] = settings.openai_api_base
        
        return OpenAIChatCompletionClient(**client_params)


def initialize_agent_loader(agents_directory: str) -> tuple[DynamicAgentLoader, Dict[str, AgentMetadata]]:
    loader = DynamicAgentLoader(agents_directory)
    metadata: Dict[str, AgentMetadata] = loader.scan_and_load_agents()
    logger.info("Agent loader initialized", agent_count=len(metadata))
    return loader, metadata


