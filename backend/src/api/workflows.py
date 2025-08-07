"""
Workflows API - GraphFlow Business Process Automation
FastAPI endpoints for managing and executing business workflows
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import structlog

from src.agents.services.graphflow_orchestrator import get_graphflow_orchestrator
from src.core.logging import get_logger

logger = get_logger()
router = APIRouter()

# Pydantic models
class WorkflowExecutionRequest(BaseModel):
    workflow_id: str = Field(..., description="ID of the workflow to execute")
    user_request: str = Field(..., description="The business request to process")
    user_id: Optional[str] = Field(None, description="User ID making the request")
    context: Optional[Dict[str, Any]] = Field(default={}, description="Additional context for the workflow")

class WorkflowExecutionResponse(BaseModel):
    execution_id: str = Field(..., description="Unique ID for tracking this workflow execution")
    workflow_id: str = Field(..., description="ID of the workflow being executed")
    status: str = Field(..., description="Current status of the execution")
    started_at: datetime = Field(..., description="When the workflow execution started")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")

class WorkflowStatusResponse(BaseModel):
    execution_id: str
    workflow_id: str
    status: str
    progress_percentage: float
    current_step: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    results: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

class WorkflowListResponse(BaseModel):
    workflows: List[Dict[str, Any]]
    total_count: int

@router.on_event("startup")
async def startup_workflows():
    """Initialize GraphFlow orchestrator on startup"""
    try:
        orchestrator = get_graphflow_orchestrator()
        await orchestrator.initialize()
        logger.info("✅ Workflows API initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize workflows API: {e}")

@router.get("/", response_model=WorkflowListResponse)
async def list_workflows():
    """
    List all available business workflows
    """
    try:
        orchestrator = get_graphflow_orchestrator()
        workflows = await orchestrator.list_available_workflows()
        
        return WorkflowListResponse(
            workflows=workflows,
            total_count=len(workflows)
        )
    except Exception as e:
        logger.error(f"❌ Error listing workflows: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list workflows: {str(e)}")

@router.post("/execute", response_model=WorkflowExecutionResponse)
async def execute_workflow(
    request: WorkflowExecutionRequest,
    background_tasks: BackgroundTasks
):
    """
    Execute a business workflow asynchronously
    """
    try:
        orchestrator = get_graphflow_orchestrator()
        
        # Validate workflow exists
        available_workflows = await orchestrator.list_available_workflows()
        workflow_ids = [w["workflow_id"] for w in available_workflows]
        
        if request.workflow_id not in workflow_ids:
            raise HTTPException(
                status_code=404, 
                detail=f"Workflow {request.workflow_id} not found. Available: {workflow_ids}"
            )
        
        logger.info(f"🚀 Executing workflow", 
                   workflow_id=request.workflow_id,
                   user_id=request.user_id)
        
        # Execute workflow asynchronously
        execution_id = await orchestrator.execute_workflow(
            workflow_id=request.workflow_id,
            user_request=request.user_request,
            user_id=request.user_id,
            context=request.context
        )
        
        return WorkflowExecutionResponse(
            execution_id=execution_id,
            workflow_id=request.workflow_id,
            status="started",
            started_at=datetime.utcnow(),
            estimated_completion=None
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error executing workflow: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to execute workflow: {str(e)}")

@router.get("/execution/{execution_id}", response_model=WorkflowStatusResponse)
async def get_workflow_status(execution_id: str):
    """
    Get current status and results of a workflow execution
    """
    try:
        orchestrator = get_graphflow_orchestrator()
        execution = await orchestrator.get_workflow_status(execution_id)
        
        if not execution:
            raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")
        
        # Calculate progress percentage based on status
        progress_map = {
            "pending": 0.0,
            "running": 50.0,  # Could be more sophisticated based on completed steps
            "completed": 100.0,
            "failed": 100.0,
            "cancelled": 100.0
        }
        
        return WorkflowStatusResponse(
            execution_id=execution_id,
            workflow_id=execution.workflow_id,
            status=execution.status,
            progress_percentage=progress_map.get(execution.status, 0.0),
            current_step=execution.current_step,
            started_at=execution.started_at,
            completed_at=execution.completed_at,
            results=execution.results,
            error_message=execution.error_message
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting workflow status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get workflow status: {str(e)}")

@router.post("/execution/{execution_id}/cancel")
async def cancel_workflow(execution_id: str):
    """
    Cancel a running workflow execution
    """
    try:
        orchestrator = get_graphflow_orchestrator()
        success = await orchestrator.cancel_workflow(execution_id)
        
        if not success:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot cancel execution {execution_id} - not found or not running"
            )
        
        return {"message": f"Workflow execution {execution_id} cancelled successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error cancelling workflow: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel workflow: {str(e)}")

@router.get("/{workflow_id}/details")
async def get_workflow_details(workflow_id: str):
    """
    Get detailed information about a specific workflow
    """
    try:
        orchestrator = get_graphflow_orchestrator()
        workflows = await orchestrator.list_available_workflows()
        workflow = next((w for w in workflows if w["workflow_id"] == workflow_id), None)
        
        if not workflow:
            raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")
        
        # Get workflow definition from orchestrator
        workflow_def = orchestrator.workflows.get(workflow_id)
        if workflow_def:
            detailed_info = {
                **workflow,
                "steps": [
                    {
                        "step_id": step.step_id,
                        "agent_name": step.agent_name,
                        "step_type": step.step_type,
                        "description": step.description
                    }
                    for step in workflow_def.steps
                ],
                "expected_duration_minutes": workflow_def.expected_duration_minutes,
                "complexity": workflow_def.complexity
            }
            return detailed_info
        else:
            return workflow
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting workflow details: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get workflow details: {str(e)}")

@router.get("/executions/recent")
async def get_recent_executions(limit: int = 10, user_id: Optional[str] = None):
    """
    Get recent workflow executions with optional user filtering
    """
    try:
        orchestrator = get_graphflow_orchestrator()
        # Get all executions from orchestrator
        all_executions = list(orchestrator.executions.values())
        
        # Filter by user_id if provided
        if user_id:
            all_executions = [e for e in all_executions if e.user_id == user_id]
        
        # Sort by start time (most recent first) and limit
        recent_executions = sorted(
            all_executions,
            key=lambda x: x.started_at,
            reverse=True
        )[:limit]
        
        # Convert to API response format
        executions_data = [
            {
                "execution_id": ex.execution_id,
                "workflow_id": ex.workflow_id,
                "status": ex.status,
                "started_at": ex.started_at.isoformat(),
                "completed_at": ex.completed_at.isoformat() if ex.completed_at else None,
                "user_id": ex.user_id
            }
            for ex in recent_executions
        ]
        
        return {"executions": executions_data, "total": len(executions_data)}
    except Exception as e:
        logger.error(f"❌ Error getting recent executions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get recent executions: {str(e)}")

@router.post("/test-execute")
async def test_workflow_execution():
    """
    Test endpoint for workflow execution with sample data
    """
    try:
        orchestrator = get_graphflow_orchestrator()
        # Use strategic analysis workflow for testing
        execution_id = await orchestrator.execute_workflow(
            workflow_id="strategic-analysis-001",
            user_request="Analyze our Q4 2024 expansion strategy into the European market. Consider financial implications, technical requirements, and potential risks.",
            user_id="test-user",
            context={
                "current_markets": ["North America", "Asia-Pacific"],
                "budget_range": "$2M-$5M",
                "timeline": "Q1-Q2 2025",
                "priority": "high"
            }
        )
        
        return {
            "message": "Test workflow execution started",
            "execution_id": execution_id,
            "test_workflow": "strategic-analysis-001"
        }
    except Exception as e:
        logger.error(f"❌ Test workflow execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Test execution failed: {str(e)}")

# Health check for workflows
@router.get("/health")
async def workflows_health():
    """Health check for workflows system"""
    try:
        orchestrator = get_graphflow_orchestrator()
        workflows = await orchestrator.list_available_workflows()
        return {
            "status": "healthy",
            "available_workflows": len(workflows),
            "active_executions": len(orchestrator.executions),
            "message": "GraphFlow workflows system operational"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "message": "GraphFlow workflows system error"
        }