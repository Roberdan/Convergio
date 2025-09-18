"""
Unified Orchestrator Adapters
Provides compatibility interfaces for all existing orchestrator use cases
"""

from typing import Dict, List, Any, Optional, AsyncGenerator
from datetime import datetime
from src.agents.orchestrators.unified import UnifiedOrchestrator
from .redis_state_manager import RedisStateManager
from src.services.unified_cost_tracker import unified_cost_tracker
from uuid import UUID
import structlog

logger = structlog.get_logger()

# Global unified orchestrator instance
_unified_orchestrator = None

def get_unified_orchestrator() -> UnifiedOrchestrator:
    """Get the global unified orchestrator instance"""
    global _unified_orchestrator
    if _unified_orchestrator is None:
        _unified_orchestrator = UnifiedOrchestrator()
    return _unified_orchestrator

# ===================== ALI SWARM ORCHESTRATOR ADAPTER =====================

class AliSwarmOrchestrator:
    """Compatibility adapter for AliSwarmOrchestrator using UnifiedOrchestrator"""
    
    def __init__(self, state_manager: RedisStateManager = None, cost_tracker=None, agents_directory: str = None):
        """Initialize adapter with UnifiedOrchestrator backend"""
        self.orchestrator = get_unified_orchestrator()
        self.state_manager = state_manager
        self.cost_tracker = cost_tracker or unified_cost_tracker
        self.agents_directory = agents_directory
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize using UnifiedOrchestrator"""
        if not self.orchestrator.is_initialized:
            if self.agents_directory:
                agents_dir = self.agents_directory
            else:
                # Use absolute path for agent definitions
                import os
                backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                agents_dir = os.path.join(backend_dir, "agents", "definitions")
            await self.orchestrator.initialize(agents_dir=agents_dir)
        self._initialized = True
    
    async def orchestrate_conversation(
        self,
        message: str,
        user_id: str,
        conversation_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Orchestrate using swarm intelligence"""
        return await self.orchestrator.orchestrate_swarm(
            message=message,
            user_id=user_id,
            conversation_id=conversation_id,
            context=context
        )

# ===================== STREAMING ORCHESTRATOR ADAPTER =====================

class StreamingOrchestrator:
    """Compatibility adapter for StreamingOrchestrator using UnifiedOrchestrator"""
    
    def __init__(self):
        self.orchestrator = get_unified_orchestrator()
        self.active_sessions = {}
        self._initialized = False
        self.memory_system = None  # For compatibility with tests
    
    async def initialize(self):
        """Initialize streaming orchestrator"""
        if not self.orchestrator.is_initialized:
            # Use absolute path for agent definitions
            import os
            backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            agents_dir = os.path.join(backend_dir, "agents", "definitions")
            await self.orchestrator.initialize(agents_dir=agents_dir)
        self._initialized = True
    
    async def create_streaming_session(
        self,
        websocket: Any,
        user_id: str,
        agent_name: str,
        session_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create streaming session"""
        if not self._initialized:
            await self.initialize()
            
        # Generate session ID and create session
        import uuid
        session_id = str(uuid.uuid4())
        
        # Create session object for tracking
        from types import SimpleNamespace
        session = SimpleNamespace(
            session_id=session_id,
            websocket=websocket,
            user_id=user_id,
            agent_name=agent_name,
            message_count=0,
            status="active",
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            context=session_context or {}
        )
        
        # Store session
        self.active_sessions[session_id] = session
        
        # Send session creation message to websocket
        session_message = {
            "event": "session_created",
            "data": {
                "session_id": session_id,
                "user_id": user_id,
                "agent_name": agent_name,
                "status": "active",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        try:
            if hasattr(websocket, 'send_json'):
                await websocket.send_json(session_message)
        except Exception as e:
            logger.warning(f"Failed to send session creation message: {e}")
        
        # Try to delegate to unified orchestrator if the method exists
        try:
            await self.orchestrator.create_streaming_session(
                websocket=websocket,
                user_id=user_id,
                agent_name=agent_name,
                session_context=session_context
            )
        except AttributeError:
            # Method doesn't exist, that's fine - we handle sessions locally
            pass
        except Exception as e:
            logger.warning(f"Failed to create streaming session in unified orchestrator: {e}")
        
        return session_id
    
    async def stream_response(
        self,
        session_id: str,
        message: str,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream response for session"""
        async for chunk in self.orchestrator.stream_response(session_id, message, **kwargs):
            yield chunk
    
    async def process_streaming_message(
        self,
        session_id: str,
        message: str,
        message_context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Process streaming message for session"""
        if not self._initialized:
            await self.initialize()
        
        # Create a mock session if it doesn't exist (for testing compatibility)
        if session_id not in self.active_sessions:
            from types import SimpleNamespace
            self.active_sessions[session_id] = SimpleNamespace(
                session_id=session_id,
                message_count=0,
                status="active",
                user_id="test_user",
                agent_name="test_agent",
                created_at=datetime.utcnow(),
                last_activity=datetime.utcnow()
            )
        
        # Update session
        session = self.active_sessions[session_id]
        session.message_count += 1
        session.last_activity = datetime.utcnow()
        session.status = "active"
        
        # Memory integration - retrieve context if memory system is available
        memory_context = []
        if self.memory_system and hasattr(self.memory_system, 'retrieve_relevant_context'):
            try:
                memory_context = await self.memory_system.retrieve_relevant_context(
                    user_id=session.user_id,
                    query=message,
                    session_id=session_id
                )
                logger.debug(f"Retrieved {len(memory_context)} memory contexts")
            except Exception as e:
                logger.warning(f"Failed to retrieve memory context: {e}")
        
        # Process the message through the unified orchestrator
        enhanced_context = message_context or {}
        if memory_context:
            enhanced_context['memory_context'] = memory_context
        
        try:
            response = await self.orchestrator.orchestrate(
                message=message,
                user_id=session.user_id,
                conversation_id=session_id,
                context=enhanced_context
            )
            
            # Memory integration - store the conversation if memory system is available
            if self.memory_system and hasattr(self.memory_system, 'store_conversation_message'):
                try:
                    await self.memory_system.store_conversation_message(
                        user_id=session.user_id,
                        session_id=session_id,
                        message=message,
                        response=response.get('response', ''),
                        agent_name=session.agent_name
                    )
                    logger.debug("Stored conversation message in memory")
                except Exception as e:
                    logger.warning(f"Failed to store conversation message: {e}")
                    
        except Exception as e:
            logger.warning(f"Failed to process streaming message: {e}")
    
    def close_session(self, session_id: str) -> None:
        """Close and remove a streaming session"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.status = "closed"
            del self.active_sessions[session_id]
    
    async def close_streaming_session(self, session_id: str) -> None:
        """Close streaming session (async version for compatibility)"""
        self.close_session(session_id)
    
    async def _send_streaming_response(self, session, response) -> None:
        """Send streaming response to websocket (for testing compatibility)"""
        if hasattr(session, 'websocket') and session.websocket:
            # Format message for websocket
            message = {
                "event": "streaming_response",
                "data": {
                    "chunk_id": getattr(response, 'chunk_id', 'unknown'),
                    "session_id": getattr(response, 'session_id', session.session_id),
                    "agent_name": getattr(response, 'agent_name', session.agent_name),
                    "chunk_type": getattr(response, 'chunk_type', 'text'),
                    "content": getattr(response, 'content', ''),
                    "timestamp": getattr(response, 'timestamp', datetime.utcnow()).isoformat()
                }
            }
            
            # Send via websocket
            try:
                if hasattr(session.websocket, 'send_json'):
                    await session.websocket.send_json(message)
                elif hasattr(session.websocket, 'send_text'):
                    import json
                    await session.websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.warning(f"Failed to send streaming response: {e}")

# ===================== GRAPHFLOW ORCHESTRATOR ADAPTER =====================

class GraphFlowOrchestrator:
    """Compatibility adapter for GraphFlowOrchestrator using UnifiedOrchestrator"""
    
    def __init__(self):
        self.orchestrator = get_unified_orchestrator()
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize using UnifiedOrchestrator"""
        if not self.orchestrator.is_initialized:
            # Use absolute path for agent definitions
            import os
            backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            agents_dir = os.path.join(backend_dir, "agents", "definitions")
            await self.orchestrator.initialize(agents_dir=agents_dir)
        self._initialized = True
    
    async def generate_workflow(self, prompt: str) -> Dict[str, Any]:
        """Generate workflow from prompt"""
        if not self._initialized:
            await self.initialize()
        return await self.orchestrator.generate_workflow(prompt)
    
    async def execute_workflow(
        self,
        workflow_id: str,
        input_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute workflow by ID"""
        if not self._initialized:
            await self.initialize()
        return await self.orchestrator.execute_workflow(workflow_id, input_data)
    
    async def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow definition"""
        if not self._initialized:
            await self.initialize()
        return await self.orchestrator.orchestrate(
            message=f"Get workflow definition for {workflow_id}",
            context={"workflow_query": True}
        )
    
    async def list_workflows(self) -> Dict[str, Any]:
        """List available workflows"""
        if not self._initialized:
            await self.initialize()
        return await self.orchestrator.orchestrate(
            message="List all available workflows",
            context={"workflow_list": True}
        )

# ===================== GLOBAL FUNCTIONS =====================

def get_graphflow_orchestrator() -> GraphFlowOrchestrator:
    """Get GraphFlow orchestrator adapter"""
    return GraphFlowOrchestrator()

def get_streaming_orchestrator() -> StreamingOrchestrator:
    """Get streaming orchestrator adapter"""
    orchestrator = StreamingOrchestrator()
    return orchestrator

def get_ali_swarm_orchestrator(**kwargs) -> AliSwarmOrchestrator:
    """Get Ali Swarm orchestrator adapter"""
    return AliSwarmOrchestrator(**kwargs)