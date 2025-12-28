"""
🤖 Swarm Coordination API
Advanced agent coordination with swarm intelligence patterns and self-organizing capabilities
"""

from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
import structlog

from ..agents.services.swarm_coordinator import (
    swarm_coordinator, 
    SwarmRole
)
try:
    from ..agents.services.agent_loader import agent_loader
except ImportError:
    # Fallback to alternative import
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from ..agents.services.agent_loader import agent_loader

logger = structlog.get_logger()
router = APIRouter()

# Request/Response Models
class SwarmTaskRequest(BaseModel):
    description: str = Field(..., description="Task description")
    priority: Optional[int] = Field(5, description="Task priority (1-10)")
    estimated_duration: Optional[int] = Field(None, description="Estimated duration in minutes")
    required_expertise: Optional[List[str]] = Field([], description="Required expertise areas")
    user_context: Optional[Dict[str, Any]] = Field({}, description="Additional user context")

class SwarmTaskResponse(BaseModel):
    task_id: str
    description: str
    complexity: str
    assigned_agents: List[str]
    coordination_pattern: Optional[str]
    status: str
    estimated_duration: int
    priority: int

class SwarmExecutionRequest(BaseModel):
    task_id: str
    execute_immediately: bool = True

class SwarmStatusResponse(BaseModel):
    total_agents: int
    active_tasks: int
    completed_tasks: int
    agent_utilization: Dict[str, Any]
    coordination_patterns: List[str]
    system_status: str

class AgentRegistrationResponse(BaseModel):
    agents_registered: int
    swarm_roles_assigned: Dict[str, int]
    coordination_ready: bool

@router.get("/status", response_model=SwarmStatusResponse)
async def get_swarm_status():
    """Get comprehensive swarm coordination system status"""
    try:
        status = await swarm_coordinator.get_swarm_status()
        return SwarmStatusResponse(**status)
    except Exception as e:
        logger.error("Failed to get swarm status", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get swarm status: {str(e)}")

@router.post("/initialize")
async def initialize_swarm_coordination():
    """Initialize swarm coordination with all available agents"""
    try:
        # Get agents from the agent management API instead of direct loader access
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:9000/api/v1/agent-management/agents")
            if not response.is_success:
                # Fallback: use agent_loader directly
                try:
                    agents_metadata = agent_loader.agent_metadata
                except Exception as loader_error:
                    logger.error("Failed to access agent loader", error=str(loader_error))
                    raise HTTPException(status_code=500, detail="Cannot access agent data")
            else:
                agents_data = response.json()
                agents_metadata = {}
                for agent in agents_data.get('agents', []):
                    agents_metadata[agent['key']] = {
                        'name': agent.get('name', agent['key']),
                        'description': agent.get('description', ''),
                        'expertise_areas': agent.get('expertise_areas', []),
                        'tools': agent.get('tools', [])
                    }
        
        registered_count = 0
        role_counts = {role.value: 0 for role in SwarmRole}
        
        for agent_key, agent_data in agents_metadata.items():
            try:
                swarm_agent = swarm_coordinator.register_agent({
                    'key': agent_key,
                    'name': agent_data.get('name', agent_key),
                    'description': agent_data.get('description', ''),
                    'expertise_areas': agent_data.get('expertise_areas', []),
                    'tools': agent_data.get('tools', [])
                })
                
                registered_count += 1
                role_counts[swarm_agent.role.value] += 1
                
            except Exception as agent_error:
                logger.warning(f"Failed to register agent {agent_key} in swarm", error=str(agent_error))
                continue
        
        coordination_ready = registered_count >= 3  # Need at least 3 agents for coordination
        
        logger.info("Swarm coordination initialized", 
                   agents_registered=registered_count,
                   role_distribution=role_counts)
        
        return AgentRegistrationResponse(
            agents_registered=registered_count,
            swarm_roles_assigned=role_counts,
            coordination_ready=coordination_ready
        )
        
    except Exception as e:
        logger.error("Failed to initialize swarm coordination", error=str(e))
        raise HTTPException(status_code=500, detail=f"Swarm initialization failed: {str(e)}")

@router.post("/tasks", response_model=SwarmTaskResponse)
async def create_swarm_task(request: SwarmTaskRequest):
    """Create a new swarm coordination task"""
    try:
        # Create task in swarm coordinator
        task = await swarm_coordinator.create_swarm_task(
            request.description,
            request.user_context
        )
        
        # Override with explicit values if provided
        if request.priority:
            task.priority = request.priority
        if request.estimated_duration:
            task.estimated_duration = request.estimated_duration
        if request.required_expertise:
            task.required_expertise = request.required_expertise
        
        # Assign optimal swarm immediately
        assigned_agents = await swarm_coordinator.assign_optimal_swarm(task.task_id)
        
        return SwarmTaskResponse(
            task_id=task.task_id,
            description=task.description,
            complexity=task.complexity.name,
            assigned_agents=[agent.name for agent in assigned_agents],
            coordination_pattern=task.coordination_pattern,
            status=task.status,
            estimated_duration=task.estimated_duration,
            priority=task.priority
        )
        
    except Exception as e:
        logger.error("Failed to create swarm task", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create swarm task: {str(e)}")

@router.get("/tasks/{task_id}")
async def get_swarm_task(task_id: str):
    """Get details of a specific swarm task"""
    try:
        task = swarm_coordinator.active_tasks.get(task_id)
        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        # Get assigned agent details
        assigned_agent_details = []
        for agent_key in task.assigned_agents:
            agent = swarm_coordinator.agents.get(agent_key)
            if agent:
                assigned_agent_details.append({
                    'key': agent.agent_key,
                    'name': agent.name,
                    'role': agent.role.value,
                    'current_load': agent.current_load,
                    'success_rate': agent.success_rate
                })
        
        return {
            'task_id': task.task_id,
            'description': task.description,
            'complexity': task.complexity.name,
            'coordination_pattern': task.coordination_pattern,
            'status': task.status,
            'priority': task.priority,
            'estimated_duration': task.estimated_duration,
            'created_at': task.created_at.isoformat(),
            'started_at': task.started_at.isoformat() if task.started_at else None,
            'completed_at': task.completed_at.isoformat() if task.completed_at else None,
            'required_expertise': task.required_expertise,
            'required_tools': task.required_tools,
            'assigned_agents': assigned_agent_details
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get swarm task", task_id=task_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get task: {str(e)}")

@router.post("/tasks/{task_id}/execute")
async def execute_swarm_task(task_id: str, background_tasks: BackgroundTasks):
    """Execute a swarm coordination task"""
    try:
        task = swarm_coordinator.active_tasks.get(task_id)
        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        if task.status not in ['pending', 'assigned']:
            raise HTTPException(status_code=400, detail=f"Task {task_id} is not in executable state (status: {task.status})")
        
        # Execute task in background
        background_tasks.add_task(swarm_coordinator.execute_swarm_task, task_id)
        
        return {
            'message': f'Swarm task {task_id} execution started',
            'task_id': task_id,
            'assigned_agents': task.assigned_agents,
            'coordination_pattern': task.coordination_pattern,
            'estimated_duration': task.estimated_duration
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to execute swarm task", task_id=task_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to execute task: {str(e)}")

@router.get("/tasks")
async def list_swarm_tasks(status_filter: Optional[str] = None):
    """List all swarm tasks with optional status filtering"""
    try:
        all_tasks = list(swarm_coordinator.active_tasks.values())
        
        if status_filter:
            all_tasks = [task for task in all_tasks if task.status == status_filter]
        
        task_summaries = []
        for task in all_tasks:
            task_summaries.append({
                'task_id': task.task_id,
                'description': task.description[:100] + '...' if len(task.description) > 100 else task.description,
                'complexity': task.complexity.name,
                'status': task.status,
                'priority': task.priority,
                'assigned_agents_count': len(task.assigned_agents),
                'coordination_pattern': task.coordination_pattern,
                'created_at': task.created_at.isoformat()
            })
        
        return {
            'tasks': task_summaries,
            'total_count': len(task_summaries),
            'status_filter': status_filter
        }
        
    except Exception as e:
        logger.error("Failed to list swarm tasks", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list tasks: {str(e)}")

@router.get("/agents")
async def list_swarm_agents():
    """List all agents registered in swarm coordination"""
    try:
        agents_info = []
        
        for agent_key, agent in swarm_coordinator.agents.items():
            agents_info.append({
                'key': agent.agent_key,
                'name': agent.name,
                'role': agent.role.value,
                'expertise_areas': agent.expertise_areas,
                'tools_count': len(agent.tools),
                'current_load': agent.current_load,
                'success_rate': agent.success_rate,
                'avg_response_time': agent.avg_response_time,
                'is_available': agent.is_available,
                'coordination_score': agent.coordination_score,
                'last_active': agent.last_active.isoformat()
            })
        
        # Group by roles
        role_distribution = {}
        for agent in agents_info:
            role = agent['role']
            if role not in role_distribution:
                role_distribution[role] = []
            role_distribution[role].append(agent)
        
        return {
            'agents': agents_info,
            'total_count': len(agents_info),
            'role_distribution': role_distribution,
            'available_count': sum(1 for a in agents_info if a['is_available'])
        }
        
    except Exception as e:
        logger.error("Failed to list swarm agents", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list agents: {str(e)}")

@router.get("/coordination-patterns")
async def get_coordination_patterns():
    """Get available coordination patterns and their descriptions"""
    try:
        patterns = {}
        for pattern_name, pattern_info in swarm_coordinator.coordination_patterns.items():
            patterns[pattern_name] = {
                'name': pattern_name,
                'description': pattern_info['description'],
                'best_for': pattern_info['best_for'],
                'coordination_overhead': pattern_info['coordination_overhead']
            }
        
        return {
            'patterns': patterns,
            'total_patterns': len(patterns),
            'recommended_usage': {
                'simple_tasks': 'sequential',
                'parallel_analysis': 'parallel', 
                'complex_projects': 'hierarchical',
                'creative_work': 'swarm',
                'production_chains': 'assembly_line'
            }
        }
        
    except Exception as e:
        logger.error("Failed to get coordination patterns", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get patterns: {str(e)}")

@router.post("/agents/{agent_key}/update-status")
async def update_agent_status(agent_key: str, is_available: bool, current_load: Optional[float] = None):
    """Update agent availability and load status"""
    try:
        agent = swarm_coordinator.agents.get(agent_key)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_key} not found in swarm")
        
        agent.is_available = is_available
        if current_load is not None:
            agent.current_load = max(0.0, min(1.0, current_load))  # Clamp between 0-1
        
        logger.info("Updated agent status in swarm", 
                   agent_key=agent_key, 
                   is_available=is_available, 
                   current_load=agent.current_load)
        
        return {
            'message': f'Agent {agent_key} status updated',
            'agent_name': agent.name,
            'is_available': agent.is_available,
            'current_load': agent.current_load
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update agent status", agent_key=agent_key, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to update agent status: {str(e)}")

@router.delete("/tasks/{task_id}")
async def cancel_swarm_task(task_id: str):
    """Cancel a swarm coordination task"""
    try:
        task = swarm_coordinator.active_tasks.get(task_id)
        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        if task.status == 'completed':
            raise HTTPException(status_code=400, detail=f"Cannot cancel completed task {task_id}")
        
        # Free up assigned agents
        for agent_key in task.assigned_agents:
            agent = swarm_coordinator.agents.get(agent_key)
            if agent:
                agent.current_load = max(0.0, agent.current_load - 0.2)
        
        # Remove task
        del swarm_coordinator.active_tasks[task_id]
        
        logger.info("Cancelled swarm task", task_id=task_id)
        
        return {
            'message': f'Task {task_id} cancelled successfully',
            'freed_agents': len(task.assigned_agents)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to cancel swarm task", task_id=task_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to cancel task: {str(e)}")

# Health check for swarm coordination
@router.get("/health")
async def swarm_coordination_health():
    """Health check for swarm coordination system"""
    try:
        status = await swarm_coordinator.get_swarm_status()
        
        health_status = "healthy"
        if status.get('system_status') != 'operational':
            health_status = "degraded"
        elif status.get('total_agents', 0) < 3:
            health_status = "limited"  # Need minimum agents for coordination
            
        return {
            'status': health_status,
            'total_agents': status.get('total_agents', 0),
            'active_tasks': status.get('active_tasks', 0),
            'system_operational': status.get('system_status') == 'operational',
            'timestamp': swarm_coordinator.task_counter  # Simple counter as timestamp
        }
        
    except Exception as e:
        logger.error("Swarm coordination health check failed", error=str(e))
        return {
            'status': 'unhealthy',
            'error': str(e)
        }