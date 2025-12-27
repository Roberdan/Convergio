"""
Unified Orchestrator Adapters
Provides compatibility interfaces for all existing orchestrator use cases
Now uses Agent Framework via RealAgentOrchestrator
"""

from typing import Dict, List, Any, Optional, AsyncGenerator
from datetime import datetime
from .redis_state_manager import RedisStateManager
from src.services.unified_cost_tracker import unified_cost_tracker
from uuid import UUID
import structlog

logger = structlog.get_logger()

# Use RealAgentOrchestrator which wraps AgentFrameworkOrchestrator
def get_unified_orchestrator():
    """Get the global orchestrator instance (now using Agent Framework)"""
    from src.agents.orchestrator import real_orchestrator
    return real_orchestrator

# ===================== ALI SWARM ORCHESTRATOR ADAPTER =====================

class AliSwarmOrchestrator:
    """Compatibility adapter for AliSwarmOrchestrator using Agent Framework"""

    def __init__(self, state_manager: RedisStateManager = None, cost_tracker=None, agents_directory: str = None):
        """Initialize adapter with Agent Framework backend"""
        self.orchestrator = get_unified_orchestrator()
        self.state_manager = state_manager
        self.cost_tracker = cost_tracker or unified_cost_tracker
        self.agents_directory = agents_directory
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize using Agent Framework orchestrator"""
        if not self.orchestrator._initialized:
            await self.orchestrator.initialize()
        self._initialized = True

    async def orchestrate_conversation(
        self,
        message: str,
        user_id: str,
        conversation_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Orchestrate using Agent Framework"""
        return await self.orchestrator.orchestrate(
            message=message,
            user_id=user_id,
            conversation_id=conversation_id,
            context=context
        )

# ===================== STREAMING ORCHESTRATOR ADAPTER =====================

class StreamingOrchestrator:
    """Compatibility adapter for StreamingOrchestrator using Agent Framework"""

    def __init__(self):
        self.orchestrator = get_unified_orchestrator()
        self.active_sessions = {}
        self._initialized = False
        self.memory_system = None  # For compatibility with tests

    async def initialize(self):
        """Initialize streaming orchestrator with Agent Framework"""
        if not self.orchestrator._initialized:
            await self.orchestrator.initialize()
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
    """Compatibility adapter for GraphFlowOrchestrator using Agent Framework"""

    def __init__(self):
        self.orchestrator = get_unified_orchestrator()
        self._initialized = False
        self.executions: Dict[str, Any] = {}  # Track workflow executions
        self.workflows: Dict[str, Any] = {}   # Store workflow definitions

    async def initialize(self) -> None:
        """Initialize using Agent Framework"""
        if not self.orchestrator._initialized:
            await self.orchestrator.initialize()
        self._initialized = True
    
    async def generate_workflow(self, prompt: str) -> Dict[str, Any]:
        """Generate workflow from prompt"""
        if not self._initialized:
            await self.initialize()
        return await self.orchestrator.generate_workflow(prompt)
    
    async def execute_workflow(
        self,
        workflow_id: str,
        user_request: str = "",
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        input_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Execute workflow by ID and return execution_id"""
        import uuid
        if not self._initialized:
            await self.initialize()

        execution_id = str(uuid.uuid4())

        # Create execution record
        from types import SimpleNamespace
        execution = SimpleNamespace(
            execution_id=execution_id,
            workflow_id=workflow_id,
            user_id=user_id,
            status="running",
            started_at=datetime.utcnow(),
            completed_at=None,
            current_step=None,
            results=None,
            error_message=None
        )
        self.executions[execution_id] = execution

        return execution_id

    async def get_workflow_status(self, execution_id: str) -> Optional[Any]:
        """Get workflow execution status"""
        return self.executions.get(execution_id)

    async def cancel_workflow(self, execution_id: str) -> bool:
        """Cancel a running workflow"""
        if execution_id in self.executions:
            self.executions[execution_id].status = "cancelled"
            return True
        return False
    
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

    async def list_available_workflows(self) -> List[Dict[str, Any]]:
        """List available workflows - compatibility method for API"""
        # Return a list of available workflow templates
        return [
            {
                "id": "strategic_analysis",
                "name": "Strategic Analysis",
                "description": "Multi-agent strategic analysis workflow",
                "agents": ["ali_chief_of_staff", "domik_mckinsey_strategic_decision_maker"],
                "category": "strategy"
            },
            {
                "id": "financial_review",
                "name": "Financial Review",
                "description": "Financial analysis and reporting workflow",
                "agents": ["amy_cfo", "diana_performance_dashboard"],
                "category": "finance"
            },
            {
                "id": "security_audit",
                "name": "Security Audit",
                "description": "Security assessment and recommendations",
                "agents": ["luca_security_expert"],
                "category": "security"
            },
            {
                "id": "market_research",
                "name": "Market Research",
                "description": "Market analysis and competitive intelligence",
                "agents": ["fiona_market_analyst", "sofia_marketing_strategist"],
                "category": "research"
            }
        ]

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