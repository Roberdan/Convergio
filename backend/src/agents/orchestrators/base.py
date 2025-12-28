"""
Base Orchestrator Interface
Defines the contract for all agent orchestrators in Convergio
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, AsyncGenerator
from datetime import datetime
import structlog

# AutoGen imports with fallback
try:
    from autogen_agentchat.agents import AssistantAgent
    from autogen_agentchat.teams import BaseGroupChat
    AUTOGEN_AVAILABLE = True
except ImportError:
    AssistantAgent = None
    BaseGroupChat = None
    AUTOGEN_AVAILABLE = False

logger = structlog.get_logger()


class IAgentOrchestrator(ABC):
    """
    Abstract base class for all agent orchestrators.
    Provides a unified interface for different orchestration strategies.
    """
    
    def __init__(self, name: str = "base_orchestrator"):
        self.name = name
        self.agents: Dict[str, Any] = {}  # Any to support both AutoGen and Agent Framework agents
        self.is_initialized = False
        self.initialization_time: Optional[datetime] = None
        self.metrics = {
            "conversations_handled": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "average_response_time": 0.0
        }
    
    @abstractmethod
    async def initialize(
        self, 
        agents_dir: str,
        model_client: Optional[Any] = None,
        **kwargs
    ) -> bool:
        """
        Initialize the orchestrator with agents from the specified directory.
        
        Args:
            agents_dir: Path to directory containing agent definitions
            model_client: AI model client to use
            **kwargs: Additional orchestrator-specific parameters
        
        Returns:
            Success status
        """
        pass
    
    @abstractmethod
    async def orchestrate(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Process a message through the agent system.
        
        Args:
            message: User message to process
            context: Optional context information
            user_id: User identifier
            conversation_id: Conversation identifier
            **kwargs: Additional parameters
        
        Returns:
            Response dictionary with:
            - response: The final response text
            - agents_used: List of agents that participated
            - turn_count: Number of conversation turns
            - duration_seconds: Processing time
            - cost_breakdown: Cost analysis
        """
        pass
    
    @abstractmethod
    async def stream(
        self,
        message: str,
        websocket: Any,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Stream responses via WebSocket.
        
        Args:
            message: User message to process
            websocket: WebSocket connection
            context: Optional context
            **kwargs: Additional parameters
        
        Yields:
            Response chunks
        """
        pass
    
    @property
    @abstractmethod
    def health(self) -> Dict[str, Any]:
        """
        Get health check status.
        
        Returns:
            Health status dictionary with:
            - status: "healthy", "degraded", or "unhealthy"
            - initialized: Whether orchestrator is initialized
            - agent_count: Number of loaded agents
            - metrics: Performance metrics
            - last_activity: Timestamp of last activity
        """
        pass
    
    @abstractmethod
    async def reset(self) -> bool:
        """
        Reset the orchestrator state.
        
        Returns:
            Success status
        """
        pass
    
    # Common functionality that can be shared
    
    def get_agent(self, agent_name: str) -> Optional[AssistantAgent]:
        """Get a specific agent by name"""
        return self.agents.get(agent_name)
    
    def list_agents(self) -> List[str]:
        """Get list of available agent names"""
        return list(self.agents.keys())
    
    def update_metrics(
        self,
        tokens_used: int = 0,
        cost: float = 0.0,
        response_time: float = 0.0
    ):
        """Update orchestrator metrics"""
        self.metrics["conversations_handled"] += 1
        self.metrics["total_tokens"] += tokens_used
        self.metrics["total_cost"] += cost
        
        # Update rolling average response time
        n = self.metrics["conversations_handled"]
        avg = self.metrics["average_response_time"]
        self.metrics["average_response_time"] = (avg * (n-1) + response_time) / n
    
    def is_healthy(self) -> bool:
        """Check if orchestrator is healthy"""
        return self.is_initialized and len(self.agents) > 0


class OrchestratorRegistry:
    """
    Registry for managing multiple orchestrator implementations.
    Follows the Strategy pattern for runtime orchestrator selection.
    """
    
    _orchestrators: Dict[str, IAgentOrchestrator] = {}
    _default_orchestrator: Optional[str] = None
    
    @classmethod
    def register(
        cls,
        name: str,
        orchestrator: IAgentOrchestrator,
        set_as_default: bool = False
    ):
        """
        Register an orchestrator implementation.
        
        Args:
            name: Unique name for the orchestrator
            orchestrator: Orchestrator instance
            set_as_default: Whether to set as default
        """
        cls._orchestrators[name] = orchestrator
        
        if set_as_default or cls._default_orchestrator is None:
            cls._default_orchestrator = name
        
        logger.info(f"✅ Registered orchestrator: {name}", default=set_as_default)
    
    @classmethod
    def get(cls, name: Optional[str] = None) -> Optional[IAgentOrchestrator]:
        """
        Get an orchestrator by name.
        
        Args:
            name: Orchestrator name (uses default if None)
        
        Returns:
            Orchestrator instance or None
        """
        if name is None:
            name = cls._default_orchestrator
        
        return cls._orchestrators.get(name)
    
    @classmethod
    def list_orchestrators(cls) -> List[str]:
        """Get list of registered orchestrator names"""
        return list(cls._orchestrators.keys())
    
    @classmethod
    def get_default(cls) -> Optional[IAgentOrchestrator]:
        """Get the default orchestrator"""
        return cls.get(cls._default_orchestrator)
    
    @classmethod
    def set_default(cls, name: str) -> bool:
        """
        Set the default orchestrator.
        
        Args:
            name: Name of orchestrator to set as default
        
        Returns:
            Success status
        """
        if name in cls._orchestrators:
            cls._default_orchestrator = name
            logger.info(f"✅ Set default orchestrator: {name}")
            return True
        
        logger.error(f"❌ Orchestrator not found: {name}")
        return False
    
    @classmethod
    def clear(cls):
        """Clear all registered orchestrators"""
        cls._orchestrators.clear()
        cls._default_orchestrator = None


class BaseGroupChatOrchestrator(IAgentOrchestrator):
    """
    Base implementation for GroupChat-based orchestrators.
    Provides common functionality for AutoGen GroupChat orchestration.
    """
    
    def __init__(self, name: str = "groupchat_orchestrator"):
        super().__init__(name)
        self.group_chat: Optional[BaseGroupChat] = None
        self.model_client = None
        self.rag_processor = None
        self.safety_guardian = None
        self.observers = []
    
    async def add_rag_support(self, rag_processor):
        """Add RAG (Retrieval-Augmented Generation) support"""
        self.rag_processor = rag_processor
        logger.info("✅ RAG support added to orchestrator")
    
    async def add_safety_gates(self, safety_guardian):
        """Add AI safety gates"""
        self.safety_guardian = safety_guardian
        logger.info("✅ Safety gates added to orchestrator")
    
    async def add_observer(self, observer):
        """Add an observer for monitoring"""
        self.observers.append(observer)
        logger.info(f"✅ Observer added: {observer.__class__.__name__}")
    
    @property
    def health(self) -> Dict[str, Any]:
        """Get health status"""
        return {
            "status": "healthy" if self.is_healthy() else "unhealthy",
            "initialized": self.is_initialized,
            "agent_count": len(self.agents),
            "has_rag": self.rag_processor is not None,
            "has_safety": self.safety_guardian is not None,
            "observers": len(self.observers),
            "metrics": self.metrics,
            "initialization_time": self.initialization_time.isoformat() if self.initialization_time else None
        }
    
    async def reset(self) -> bool:
        """Reset orchestrator state"""
        try:
            # Clear conversation history if group chat exists
            if self.group_chat:
                # Reset group chat state
                pass
            
            # Reset metrics
            self.metrics = {
                "conversations_handled": 0,
                "total_tokens": 0,
                "total_cost": 0.0,
                "average_response_time": 0.0
            }
            
            logger.info(f"✅ Orchestrator {self.name} reset")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reset orchestrator: {e}")
            return False