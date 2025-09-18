"""
🎭 Convergio - UNIFIED Agent Orchestrator
Single orchestrator that handles all use cases
"""

import asyncio
import structlog
import os
from typing import Any, Dict, Optional, List

from src.core.config import get_settings
from src.core.redis import get_redis_client
from src.agents.orchestrators.unified import UnifiedOrchestrator
from src.agents.orchestrators.base import OrchestratorRegistry
from src.agents.services.redis_state_manager import RedisStateManager  
from src.services.unified_cost_tracker import unified_cost_tracker
from src.agents.memory.autogen_memory_system import AutoGenMemorySystem
from src.agents.observability.otel_observer import OtelAutoGenObserver

logger = structlog.get_logger()


class RealAgentOrchestrator:
    """REAL Agent Orchestrator using the UnifiedOrchestrator directly."""
    
    def __init__(self):
        """Initialize with REAL components."""
        self.settings = get_settings()
        
        # Use the UnifiedOrchestrator directly
        self.orchestrator: UnifiedOrchestrator = None
        self.registry = OrchestratorRegistry()
        
        # Use absolute path for agent definitions
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.agents_directory: str = os.path.join(backend_dir, "src", "agents", "definitions")
        
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the REAL agent system."""
        try:
            logger.info("🚀 Initializing REAL Agent System with UnifiedOrchestrator")
            
            # Ensure Redis is initialized
            try:
                redis_client = get_redis_client()
            except RuntimeError as e:
                if "Redis not initialized" in str(e):
                    logger.info("🔄 Redis not initialized, initializing now...")
                    from core.redis import init_redis
                    await init_redis()
                    redis_client = get_redis_client()
                else:
                    raise
            
            # Initialize the UnifiedOrchestrator directly
            self.orchestrator = UnifiedOrchestrator()
            
            # Initialize with agents directory
            init_ok = await self.orchestrator.initialize(
                agents_dir=self.agents_directory,
                enable_rag=True,
                enable_safety=True
            )
            if not init_ok:
                raise RuntimeError("UnifiedOrchestrator failed to initialize")
            
            self._initialized = True
            logger.info("✅ REAL Agent System initialized successfully")
            
        except Exception as e:
            logger.error("❌ Failed to initialize REAL Agent System", error=str(e))
            raise
    
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
        
        # Reinitialize the unified orchestrator
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