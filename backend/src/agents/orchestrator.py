"""
🎭 Convergio - Agent Framework Orchestrator
Uses Microsoft Agent Framework for all agent operations

Provider Support:
- Respects AI_PROVIDER_MODE (ollama_only, azure_only, hybrid, cloud_first)
- Enforces strict mode when enabled
- Routes through ProviderRouter for multi-provider support
"""

import asyncio
import structlog
import os
from typing import Any, Dict, Optional, List

from src.core.config import get_settings
from src.core.redis import get_redis_client
from src.agents.orchestrators.base import OrchestratorRegistry

# AI Provider imports
from src.core.ai_providers import (
    ProviderMode,
    get_ai_config_from_env,
)
from src.core.multi_provider_chat_client import (
    get_agent_framework_compatible_client,
)
from src.core.provider_router import (
    StrictModeViolation,
    ProviderUnavailable,
    get_provider_router,
)

# Try Agent Framework first, fall back to UnifiedOrchestrator
try:
    from agent_framework import ChatAgent
    from agent_framework.openai import OpenAIChatClient
    from src.agents.services.agent_framework_loader import AgentFrameworkLoader
    from src.agents.orchestrators.agent_framework_orchestrator import AgentFrameworkOrchestrator
    from src.agents.tools.agent_framework_tools import get_all_agent_framework_tools
    AGENT_FRAMEWORK_AVAILABLE = True
except ImportError:
    AGENT_FRAMEWORK_AVAILABLE = False
    ChatAgent = None
    OpenAIChatClient = None
    AgentFrameworkLoader = None
    AgentFrameworkOrchestrator = None
    get_all_agent_framework_tools = None

# Fallback imports
if not AGENT_FRAMEWORK_AVAILABLE:
    from src.agents.orchestrators.unified import UnifiedOrchestrator

logger = structlog.get_logger()


class RealAgentOrchestrator:
    """
    Agent Orchestrator using Microsoft Agent Framework.

    Provider Mode Support:
    - ollama_only: 100% local, FREE, no cloud calls ever
    - azure_only: Enterprise Azure OpenAI only
    - hybrid: Local for simple, cloud for complex
    - cloud_first: Best quality (OpenAI/Anthropic)

    Strict Mode:
    - When enabled, raises StrictModeViolation if cloud would be used
    """

    def __init__(self):
        """Initialize with Agent Framework components and AI provider config."""
        self.settings = get_settings()
        self.orchestrator = None
        self.registry = OrchestratorRegistry()
        self.agent_loader = None
        self.chat_client = None

        # AI Provider Configuration
        self.ai_config = get_ai_config_from_env()
        self._provider_router = get_provider_router()

        logger.info(
            "🤖 AI Provider Configuration",
            mode=self.ai_config.mode.value,
            strict_mode=self.ai_config.strict_mode,
            default_provider=self.ai_config.default_provider.value,
            default_model=self.ai_config.default_model,
        )

        # Use absolute path for agent definitions
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.agents_directory: str = os.path.join(backend_dir, "src", "agents", "definitions")

        self._initialized = False
        self._use_agent_framework = AGENT_FRAMEWORK_AVAILABLE

    async def initialize(self) -> None:
        """Initialize the agent system with Microsoft Agent Framework."""
        try:
            if self._use_agent_framework:
                logger.info("🚀 Initializing Agent System with Microsoft Agent Framework")
                await self._initialize_agent_framework()
            else:
                logger.info("🚀 Initializing Agent System with fallback orchestrator")
                await self._initialize_fallback()

            self._initialized = True
            logger.info("✅ Agent System initialized successfully",
                       framework="Agent Framework" if self._use_agent_framework else "Fallback")

        except Exception as e:
            logger.error("❌ Failed to initialize Agent System", error=str(e))
            raise

    async def _initialize_agent_framework(self) -> None:
        """
        Initialize with Microsoft Agent Framework.

        Uses AI provider configuration to route to:
        - Ollama (local, FREE)
        - Azure OpenAI (enterprise)
        - OpenAI (cloud)
        - Anthropic (cloud)
        """
        # Create chat client based on provider mode
        self.chat_client = self._create_chat_client()

        # Load agent definitions
        self.agent_loader = AgentFrameworkLoader(
            agents_directory=self.agents_directory,
            enable_hot_reload=False
        )
        await asyncio.to_thread(self.agent_loader.scan_and_load_agents)

        # Get all Agent Framework tools
        self.tools = get_all_agent_framework_tools()
        logger.info(f"🔧 Loaded {len(self.tools)} tools for agents")

        # Create ChatAgent instances with tools
        agents = self.agent_loader.create_chat_agents(
            chat_client=self.chat_client,
            tools=self.tools
        )

        # Initialize AgentFrameworkOrchestrator
        self.orchestrator = AgentFrameworkOrchestrator()
        init_ok = await self.orchestrator.initialize(
            agents=agents,
            agent_metadata={k: v for k, v in self.agent_loader.agent_metadata.items()},
            enable_safety=True
        )

        if not init_ok:
            raise RuntimeError("AgentFrameworkOrchestrator failed to initialize")

        logger.info(
            "✅ Agent Framework initialized",
            agents_count=len(agents),
            provider=self.ai_config.default_provider.value,
            mode=self.ai_config.mode.value,
        )

    def _create_chat_client(self):
        """
        Create the appropriate chat client based on AI provider mode.

        Returns:
            Chat client compatible with Agent Framework

        Raises:
            StrictModeViolation: If strict mode prevents cloud usage
            ProviderUnavailable: If configured provider is not available
        """
        mode = self.ai_config.mode
        provider = self.ai_config.default_provider

        logger.info(
            "🔌 Creating chat client",
            mode=mode.value,
            provider=provider.value,
            strict_mode=self.ai_config.strict_mode,
        )

        # For Ollama-only mode, use Ollama's OpenAI-compatible API
        if mode == ProviderMode.OLLAMA_ONLY:
            return self._create_ollama_client()

        # For Azure-only mode, use Azure OpenAI
        if mode == ProviderMode.AZURE_ONLY:
            return self._create_azure_client()

        # For cloud-first mode, use OpenAI (or Anthropic via router)
        if mode == ProviderMode.CLOUD_FIRST:
            return self._create_cloud_client()

        # For hybrid mode, use multi-provider client
        # This routes through ProviderRouter for smart routing
        return get_agent_framework_compatible_client()

    def _create_ollama_client(self):
        """
        Create Ollama-compatible client using OpenAI interface.

        Ollama exposes an OpenAI-compatible API at /v1/chat/completions
        """
        ollama_host = self.ai_config.ollama_host.rstrip("/")
        model = self.ai_config.default_model

        logger.info(
            "🏠 Using Ollama (LOCAL, FREE)",
            host=ollama_host,
            model=model,
        )

        # Ollama's OpenAI-compatible endpoint
        # OpenAIChatClient from agent_framework may not support custom base_url,
        # so we use our multi-provider client which handles routing
        return get_agent_framework_compatible_client()

    def _create_azure_client(self):
        """
        Create Azure OpenAI client.

        Uses AzureOpenAIChatClient if available, otherwise routes through provider.
        """
        try:
            from agent_framework.azure import AzureOpenAIChatClient
            from azure.identity import DefaultAzureCredential

            endpoint = self.ai_config.azure_endpoint or os.getenv("AZURE_OPENAI_ENDPOINT")
            deployment = self.ai_config.azure_deployment or os.getenv("AZURE_OPENAI_DEPLOYMENT")

            if not endpoint:
                raise ProviderUnavailable("Azure OpenAI endpoint not configured")

            logger.info(
                "🏢 Using Azure OpenAI (Enterprise)",
                endpoint=endpoint,
                deployment=deployment,
            )

            # Try API key first, then fall back to credential
            api_key = os.getenv("AZURE_OPENAI_API_KEY")
            if api_key:
                # Use our multi-provider client for consistent routing
                return get_agent_framework_compatible_client()
            else:
                # Use Azure SDK credential-based auth
                return AzureOpenAIChatClient(credential=DefaultAzureCredential())

        except ImportError:
            logger.warning("Azure SDK not available, using multi-provider client")
            return get_agent_framework_compatible_client()

    def _create_cloud_client(self):
        """
        Create cloud provider client (OpenAI/Anthropic).

        In strict mode with ollama_only, this will raise StrictModeViolation.
        """
        # Check strict mode
        if self.ai_config.strict_mode and self.ai_config.mode == ProviderMode.OLLAMA_ONLY:
            raise StrictModeViolation(
                "Cannot create cloud client - strict mode is ON and mode is ollama_only"
            )

        api_key = self.settings.OPENAI_API_KEY
        if api_key:
            model_id = getattr(self.settings, 'DEFAULT_AI_MODEL', None) or "gpt-4o-mini"
            logger.info(
                "☁️ Using OpenAI (Cloud)",
                model=model_id,
            )
            return OpenAIChatClient(model_id=model_id, api_key=api_key)

        # Fall back to multi-provider client
        logger.info("☁️ Using multi-provider client for cloud routing")
        return get_agent_framework_compatible_client()

    async def _initialize_fallback(self) -> None:
        """Initialize with fallback UnifiedOrchestrator."""
        # Ensure Redis is initialized
        try:
            get_redis_client()
        except RuntimeError as e:
            if "Redis not initialized" in str(e):
                logger.info("🔄 Redis not initialized, initializing now...")
                from core.redis import init_redis
                await init_redis()
                get_redis_client()
            else:
                raise

        self.orchestrator = UnifiedOrchestrator()
        init_ok = await self.orchestrator.initialize(
            agents_dir=self.agents_directory,
            enable_rag=True,
            enable_safety=True
        )

        if not init_ok:
            raise RuntimeError("UnifiedOrchestrator failed to initialize")
    
    async def orchestrate_conversation(
        self,
        message: str,
        user_id: str,
        conversation_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Orchestrate conversation using UnifiedOrchestrator."""
        
        if not self._initialized:
            await self.initialize()
        
        logger.info("🎭 REAL Agent Conversation",
                   user_id=user_id,
                   message_preview=message[:100])
        
        # Use the UnifiedOrchestrator directly
        result = await self.orchestrator.orchestrate(
            message=message,
            user_id=user_id,
            conversation_id=conversation_id,
            context=context or {}
        )
        
        logger.info("✅ REAL Agent Conversation completed",
                   agents_used=len(result.get("agents_used", [])),
                   cost_usd=result.get("cost_breakdown", {}).get("total_cost_usd", 0))
        
        return result
    
    # Alias for API compatibility
    async def orchestrate(
        self,
        message: str,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Orchestrate agents - alias for orchestrate_conversation."""
        return await self.orchestrate_conversation(
            message=message,
            user_id=user_id or "api_user",
            conversation_id=conversation_id,
            context=context
        )
    
    async def process_agent_message(
        self,
        agent_name: str,
        message: str,
        conversation_id: Optional[str] = None,
        debug_mode: bool = False
    ) -> Dict[str, Any]:
        """Process message with specific agent (for debugging)."""
        
        if not self._initialized:
            await self.initialize()
            
        logger.info("🐛 Processing agent message", 
                   agent_name=agent_name, 
                   debug_mode=debug_mode,
                   message_preview=message[:50])
        
        # Use orchestrator with target agent
        result = await self.orchestrator.orchestrate(
            message=message,
            user_id="debug_user",
            conversation_id=conversation_id,
            context={"debug_mode": debug_mode, "target_agent": agent_name}
        )
        
        return {
            "agent_name": agent_name,
            "conversation_id": conversation_id,
            "debug_mode": debug_mode,
            "result": result,
            "agents_used": result.get("agents_used", []),
            "cost": result.get("cost_breakdown", {})
        }
    
    async def get_available_agents(self) -> Dict[str, Any]:
        """Get all available agents."""
        if not self._initialized:
            await self.initialize()
        
        agent_names = self.orchestrator.list_agents()
        return {"agents": agent_names, "total": len(agent_names)}
    
    def list_agents(self) -> List[str]:
        """List all agent IDs."""
        if not self._initialized or not self.orchestrator:
            return []
        return self.orchestrator.list_agents()
    
    def get_agent(self, agent_id: str):
        """Get a specific agent by ID."""
        if not self._initialized or not self.orchestrator:
            return None
        return self.orchestrator.agents.get(agent_id)
    
    def get_agent_metadata(self, agent_key: str):
        """Get original metadata for an agent."""
        if not self._initialized or not self.orchestrator:
            return None
        return self.orchestrator.get_agent_metadata(agent_key)
    
    def list_agents_with_metadata(self):
        """Get list of agents with their original metadata."""
        if not self._initialized or not self.orchestrator:
            return {}
        return self.orchestrator.list_agents_with_metadata()
    
    async def reload_agents(self) -> Dict[str, Any]:
        """Reload agents."""
        if not self._initialized:
            await self.initialize()
            return {"reloaded": True}

        # Reinitialize based on framework type
        if self._use_agent_framework:
            # Reload agent definitions and reinitialize
            await asyncio.to_thread(self.agent_loader.scan_and_load_agents)
            agents = self.agent_loader.create_chat_agents(
                chat_client=self.chat_client,
                tools=self.tools
            )
            ok = await self.orchestrator.initialize(
                agents=agents,
                agent_metadata={k: v for k, v in self.agent_loader.agent_metadata.items()},
                enable_safety=True
            )
        else:
            # Fallback to UnifiedOrchestrator reload
            ok = await self.orchestrator.initialize(
                agents_dir=self.agents_directory,
                enable_rag=True,
                enable_safety=True
            )
        return {"reloaded": ok}
    
    def is_healthy(self) -> bool:
        """Check if system is healthy."""
        return (self._initialized and
                self.orchestrator is not None and
                (self.orchestrator.is_healthy() if hasattr(self.orchestrator, "is_healthy") else True))

    def get_ai_config(self) -> Dict[str, Any]:
        """
        Get current AI provider configuration.

        Returns:
            Dict with mode, provider, model, and strict mode settings
        """
        return {
            "mode": self.ai_config.mode.value,
            "strict_mode": self.ai_config.strict_mode,
            "default_provider": self.ai_config.default_provider.value,
            "default_model": self.ai_config.default_model,
            "ollama_host": self.ai_config.ollama_host,
            "azure_endpoint": self.ai_config.azure_endpoint,
            "azure_deployment": self.ai_config.azure_deployment,
        }

    def get_provider_stats(self) -> Dict[str, Any]:
        """
        Get AI provider usage statistics.

        Returns:
            Dict with call counts, costs, and savings
        """
        return self._provider_router.get_stats()

    def get_provider_costs(self) -> Dict[str, float]:
        """
        Get accumulated costs per provider.

        Returns:
            Dict mapping provider name to cost in USD
        """
        return self._provider_router.get_costs()

    def get_savings_vs_cloud(self) -> float:
        """
        Get estimated savings from using Ollama vs cloud.

        Returns:
            Estimated savings in USD
        """
        stats = self._provider_router.get_stats()
        return stats.get("savings_vs_cloud", 0.0)

    async def close(self) -> None:
        """Close system."""
        if self.orchestrator and hasattr(self.orchestrator, 'shutdown'):
            await self.orchestrator.shutdown()


# Global orchestrator instance
real_orchestrator = RealAgentOrchestrator()


async def initialize_agents() -> None:
    """Initialize the agent system."""
    await real_orchestrator.initialize()


async def get_agent_orchestrator() -> RealAgentOrchestrator:
    """Get the agent orchestrator."""
    if not real_orchestrator._initialized:
        await real_orchestrator.initialize()
    return real_orchestrator