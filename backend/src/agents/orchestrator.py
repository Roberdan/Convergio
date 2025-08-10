"""
🎭 Convergio - REAL Agent Orchestrator Integration
Complete integration of the original agents service with AutoGen
"""

import asyncio
import structlog
from typing import Any, Dict, Optional

from src.core.config import get_settings
from src.core.redis import get_redis_client
from .services.autogen_groupchat_orchestrator import ModernGroupChatOrchestrator, GroupChatResult
from .services.redis_state_manager import RedisStateManager  
from .services.cost_tracker import CostTracker
from .memory.autogen_memory_system import AutoGenMemorySystem
from .observability.otel_observer import OtelAutoGenObserver

logger = structlog.get_logger()


class RealAgentOrchestrator:
    """REAL Agent Orchestrator using the complete original agents system."""
    
    def __init__(self):
        """Initialize with REAL components."""
        self.settings = get_settings()
        
        # Use the REAL ModernGroupChatOrchestrator from agents service
        self.state_manager: RedisStateManager = None
        self.cost_tracker: CostTracker = None
        self.orchestrator: ModernGroupChatOrchestrator = None
        self.memory_system: AutoGenMemorySystem = None
        
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the REAL agent system."""
        try:
            logger.info("🚀 Initializing REAL Agent System (Complete Migration)")
            
            # Get Redis client from Convergio core
            redis_client = get_redis_client()
            redis_url = self.settings.REDIS_URL
            
            # Initialize REAL components from agents service
            self.state_manager = RedisStateManager(redis_url)
            self.cost_tracker = CostTracker(self.state_manager)
            
            # Initialize Memory System with Redis persistence  
            self.memory_system = AutoGenMemorySystem()
            # Memory system is initialized in constructor - no initialize() method
            
            # Initialize the REAL ModernGroupChatOrchestrator with memory
            self.orchestrator = ModernGroupChatOrchestrator(
                state_manager=self.state_manager,
                cost_tracker=self.cost_tracker,
                agents_directory="src/agents/definitions",  # All 50+ agents
                memory_system=self.memory_system,  # Add memory system
                observers=[OtelAutoGenObserver()],
            )
            
            # Initialize services
            await self.state_manager.initialize()
            await self.orchestrator.initialize()
            
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
    ) -> GroupChatResult:
        """Orchestrate conversation using REAL agent system."""
        
        if not self._initialized:
            await self.initialize()
        
        logger.info("🎭 REAL Agent Conversation",
                   user_id=user_id,
                   message_preview=message[:100])
        
        # Use the REAL orchestrator
        result = await self.orchestrator.orchestrate_conversation(
            message=message,
            user_id=user_id,
            conversation_id=conversation_id,
            context=context or {}
        )
        
        logger.info("✅ REAL Agent Conversation completed",
                   agents_used=len(result.agents_used),
                   cost_usd=result.cost_breakdown.get("total_cost_usd", 0))
        
        return result
    
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
        
        if debug_mode:
            # Enhanced logging for debug mode
            logger.info("🔍 Debug mode enabled - detailed agent interaction logging")
        
        # Use orchestrator to handle the specific agent interaction
        # The orchestrator will route to the appropriate agent
        result = await self.orchestrator.orchestrate_conversation(
            message=f"Agent {agent_name}: {message}",
            user_id="debug_user",
            conversation_id=conversation_id,
            context={"debug_mode": debug_mode, "target_agent": agent_name}
        )
        
        return {
            "agent_name": agent_name,
            "conversation_id": conversation_id,
            "debug_mode": debug_mode,
            "result": result,
            "agents_used": result.agents_used,
            "cost": result.cost_breakdown
        }
    
    async def get_available_agents(self) -> Dict[str, Any]:
        """Get all available agents from REAL system."""
        if not self._initialized:
            await self.initialize()
        
        return await self.orchestrator.get_ecosystem_status()
    
    async def reload_agents(self) -> Dict[str, Any]:
        """Reload agents in REAL system."""
        if not self._initialized:
            await self.initialize()
        
        return await self.orchestrator.reload_agents()
    
    def is_healthy(self) -> bool:
        """Check if REAL system is healthy."""
        return (self._initialized and 
                self.orchestrator is not None and
                self.orchestrator.is_healthy())
    
    async def close(self) -> None:
        """Close REAL system."""
        if self.state_manager:
            await self.state_manager.close()


# Global REAL orchestrator instance
real_orchestrator = RealAgentOrchestrator()


async def initialize_agents() -> None:
    """Initialize the REAL agent system."""
    await real_orchestrator.initialize()


async def get_agent_orchestrator() -> RealAgentOrchestrator:
    """Get the REAL agent orchestrator."""
    if not real_orchestrator._initialized:
        await real_orchestrator.initialize()
    return real_orchestrator