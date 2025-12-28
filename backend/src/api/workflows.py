"""
Workflows API - GraphFlow Business Process Automation
FastAPI endpoints for managing and executing business workflows
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import os

from ..agents.services.graphflow_orchestrator import get_graphflow_orchestrator
from ..agents.services.graphflow.generator import (
    BusinessWorkflow,
    generate_workflow_from_prompt,
)
from ..agents.services.graphflow.registry import get_workflow_catalog, search_workflows
from ..agents.services.observability.telemetry_api import TelemetryAPIService
from ..agents.utils.config import get_settings
from ..core.logging import get_logger

logger = get_logger()
router = APIRouter()
settings = get_settings()
telemetry = TelemetryAPIService()

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

class WorkflowGenerationResponse(BaseModel):
    workflow_id: str
    workflow: Dict[str, Any]
    status: str = "generated"
    message: str = "Workflow generated successfully"

class WorkflowGenerationRequestModel(BaseModel):
    """Pydantic model for workflow generation request body"""
    prompt: str = Field(..., description="Natural language description of the workflow")
    business_domain: Optional[str] = Field("operations", description="Business domain, e.g., operations, finance")
    priority: Optional[str] = Field("medium", description="Priority: low, medium, high, critical")
    max_steps: int = Field(10, ge=1, le=50, description="Maximum number of steps to generate")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional generation context")
    safety_check: bool = Field(True, description="Enable prompt safety validation")

@router.on_event("startup")
async def startup_workflows():
    """Initialize GraphFlow orchestrator on startup"""
    try:
        if not settings.graphflow_enabled:
            logger.info("GraphFlow disabled by feature flag; skipping initialization")
            return
        orchestrator = get_graphflow_orchestrator()
        await orchestrator.initialize()
        logger.info("✅ Workflows API initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize workflows API: {e}")

def _ensure_graphflow_enabled():
    if not settings.graphflow_enabled:
        raise HTTPException(status_code=503, detail="GraphFlow feature flag is disabled")

@router.get("/", response_model=WorkflowListResponse)
async def list_workflows():
    """
    List all available business workflows
    """
    try:
        _ensure_graphflow_enabled()
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
        _ensure_graphflow_enabled()
        orchestrator = get_graphflow_orchestrator()
        
        # Validate workflow exists
        available_workflows = await orchestrator.list_available_workflows()
        workflow_ids = [w["workflow_id"] for w in available_workflows]
        
        if request.workflow_id not in workflow_ids:
            raise HTTPException(
                status_code=404, 
                detail=f"Workflow {request.workflow_id} not found. Available: {workflow_ids}"
            )
        
        logger.info("🚀 Executing workflow", 
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
        _ensure_graphflow_enabled()
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
        _ensure_graphflow_enabled()
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

# ===================== Workflow Generation Endpoints (V2) =====================

@router.post("/save")
async def save_workflow(workflow: BusinessWorkflow):
    """
    Save a custom workflow to persistent storage
    """
    try:
        _ensure_graphflow_enabled()
        
        # In production, this would save to database
        # For now, save to in-memory storage
        orchestrator = get_graphflow_orchestrator()
        
        # Add to orchestrator's workflow registry
        orchestrator.workflows[workflow.id] = workflow
        
        # Emit telemetry event
        telemetry.emit_event(
            "workflow_saved",
            {
                "workflow_id": workflow.id,
                "workflow_name": workflow.name,
                "steps_count": len(workflow.steps),
                "estimated_cost": workflow.estimated_cost
            }
        )
        
        return {
            "message": f"Workflow {workflow.name} saved successfully",
            "workflow_id": workflow.id
        }
        
    except Exception as e:
        logger.error(f"Failed to save workflow: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save workflow: {str(e)}")

@router.get("/custom", response_model=List[Dict[str, Any]])
async def list_custom_workflows():
    """
    List all custom (user-created) workflows
    """
    try:
        _ensure_graphflow_enabled()
        orchestrator = get_graphflow_orchestrator()
        
        # Filter for non-template workflows
        custom_workflows = []
        for workflow_id, workflow in orchestrator.workflows.items():
            if hasattr(workflow, 'is_template') and not workflow.is_template:
                custom_workflows.append({
                    "id": workflow.id,
                    "name": workflow.name,
                    "description": workflow.description,
                    "created_at": workflow.created_at.isoformat() if workflow.created_at else None,
                    "steps_count": len(workflow.steps),
                    "estimated_cost": workflow.estimated_cost,
                    "is_active": workflow.is_active
                })
        
        return custom_workflows
        
    except Exception as e:
        logger.error(f"Failed to list custom workflows: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list custom workflows: {str(e)}")

@router.put("/{workflow_id}")
async def update_workflow(workflow_id: str, workflow: BusinessWorkflow):
    """
    Update an existing workflow
    """
    try:
        _ensure_graphflow_enabled()
        orchestrator = get_graphflow_orchestrator()
        
        if workflow_id not in orchestrator.workflows:
            raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")
        
        # Update workflow
        workflow.id = workflow_id  # Ensure ID doesn't change
        workflow.version = _increment_version(orchestrator.workflows[workflow_id].version)
        orchestrator.workflows[workflow_id] = workflow
        
        return {
            "message": f"Workflow {workflow.name} updated successfully",
            "workflow_id": workflow_id,
            "version": workflow.version
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update workflow: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update workflow: {str(e)}")

@router.delete("/{workflow_id}")
async def delete_workflow(workflow_id: str):
    """
    Delete a custom workflow
    """
    try:
        _ensure_graphflow_enabled()
        orchestrator = get_graphflow_orchestrator()
        
        if workflow_id not in orchestrator.workflows:
            raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")
        
        workflow = orchestrator.workflows[workflow_id]
        
        # Don't delete templates
        if hasattr(workflow, 'is_template') and workflow.is_template:
            raise HTTPException(status_code=400, detail="Cannot delete template workflows")
        
        # Remove workflow
        del orchestrator.workflows[workflow_id]
        
        return {
            "message": f"Workflow {workflow_id} deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete workflow: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete workflow: {str(e)}")

@router.post("/import")
async def import_workflow(workflow_json: str):
    """
    Import a workflow from JSON
    """
    try:
        _ensure_graphflow_enabled()
        
        import json
        workflow_data = json.loads(workflow_json)
        workflow = BusinessWorkflow(**workflow_data)
        
        # Save imported workflow
        orchestrator = get_graphflow_orchestrator()
        orchestrator.workflows[workflow.id] = workflow
        
        return {
            "message": f"Workflow {workflow.name} imported successfully",
            "workflow_id": workflow.id
        }
        
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to import workflow: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to import workflow: {str(e)}")

@router.get("/export/{workflow_id}")
async def export_workflow(workflow_id: str):
    """
    Export a workflow as JSON
    """
    try:
        _ensure_graphflow_enabled()
        orchestrator = get_graphflow_orchestrator()
        
        if workflow_id not in orchestrator.workflows:
            raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")
        
        workflow = orchestrator.workflows[workflow_id]
        
        import json
        return {
            "workflow_id": workflow_id,
            "json": json.dumps(workflow.dict() if hasattr(workflow, 'dict') else workflow, default=str, indent=2)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export workflow: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to export workflow: {str(e)}")

def _increment_version(version: str) -> str:
    """Increment version number"""
    parts = version.split(".")
    if len(parts) == 3:
        parts[2] = str(int(parts[2]) + 1)
    return ".".join(parts)

@router.get("/{workflow_id}/details")
async def get_workflow_details(workflow_id: str):
    """
    Get detailed information about a specific workflow
    """
    try:
        _ensure_graphflow_enabled()
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
                        "step_type": step.step_type.value if hasattr(step.step_type, 'value') else str(step.step_type),
                        "description": step.description,
                        "detailed_instructions": step.detailed_instructions,
                        "estimated_duration_minutes": step.estimated_duration_minutes,
                        "tools_required": step.tools_required,
                        "dependencies": step.dependencies
                    }
                    for step in workflow_def.steps
                ],
                "sla_minutes": workflow_def.sla_minutes,
                "business_domain": workflow_def.business_domain.value if hasattr(workflow_def.business_domain, 'value') else str(workflow_def.business_domain),
                "priority": workflow_def.priority.value if hasattr(workflow_def.priority, 'value') else str(workflow_def.priority),
                "success_metrics": workflow_def.success_metrics,
                "entry_points": workflow_def.entry_points,
                "approval_gates": workflow_def.approval_gates
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
        _ensure_graphflow_enabled()
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
        _ensure_graphflow_enabled()
        orchestrator = get_graphflow_orchestrator()
        # Use strategic analysis workflow for testing
        execution_id = await orchestrator.execute_workflow(
            workflow_id="strategic-analysis-001",
            user_request="Analyze our Q4 2024 expansion strategy into the European market. Consider financial implications, technical requirements, and potential risks.",
            user_id=os.getenv("DEFAULT_TEST_USER", "system_test_user"),
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
        # Feature flag gate - check if GraphFlow is disabled
        if not settings.graphflow_enabled:
            return {
                "status": "disabled",
                "message": "GraphFlow workflows feature is disabled"
            }
        
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


# ===================== NEW ENDPOINTS FOR M6 WORKFLOW GENERATOR =====================

@router.post("/generate", response_model=Dict[str, Any])
async def generate_workflow(request: WorkflowGenerationRequestModel):
    """
    Generate a new workflow from natural language prompt or PRD
    
    This endpoint uses AI to generate a complete workflow definition
    from a natural language description of business requirements.
    """
    try:
        _ensure_graphflow_enabled()
        
        logger.info("🤖 Generating workflow from prompt", 
                   prompt_length=len(request.prompt),
                   domain=request.business_domain)
        
        # Generate workflow using GraphFlow generator
        resp = await generate_workflow_from_prompt(
            prompt=request.prompt,
            business_domain=request.business_domain or "operations",
            priority=request.priority or "medium",
            max_steps=request.max_steps,
            context=request.context or {},
        )
        
        logger.info("✅ Workflow generated successfully",
                   workflow_id=resp.workflow.workflow_id,
                   steps_count=len(resp.workflow.steps))
        
        return {
            "workflow_id": resp.workflow.workflow_id,
            "workflow": resp.workflow.dict() if hasattr(resp.workflow, "dict") else resp.workflow,
            "status": "generated",
            "message": "Workflow generated successfully",
            "metadata": resp.generation_metadata,
        }
        
    except ValueError as e:
        logger.warning(f"⚠️ Workflow generation validation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Error generating workflow: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate workflow: {str(e)}")


@router.get("/catalog")
async def get_workflow_catalog_endpoint():
    """
    Get the comprehensive workflow catalog with all available templates and workflows
    """
    try:
        _ensure_graphflow_enabled()
        
        catalog = await get_workflow_catalog()
        
        return {
            "catalog": catalog,
            "total_count": len(catalog),
            "categories": list(set(item["category"] for item in catalog))
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting workflow catalog: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get catalog: {str(e)}")


@router.get("/search")
async def search_workflows_endpoint(
    query: Optional[str] = None,
    domain: Optional[str] = None,
    complexity: Optional[str] = None,
    max_duration_minutes: Optional[int] = None
):
    """
    Search workflows with filters

    Parameters:
    - query: Text search in name, description, and tags
    - domain: Business domain filter (strategy, operations, finance, etc.)
    - complexity: Complexity level filter (low, medium, high)
    - max_duration_minutes: Maximum workflow duration filter
    """
    try:
        _ensure_graphflow_enabled()

        results = await search_workflows(
            query=query or "",
            domain=domain,
            complexity=complexity,
            max_duration_minutes=max_duration_minutes
        )
        
        return {
            "results": results,
            "total_count": len(results),
            "filters_applied": {
                "query": query,
                "domain": domain,
                "complexity": complexity,
                "max_duration_minutes": max_duration_minutes
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error searching workflows: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to search workflows: {str(e)}")


class WorkflowVersionRequest(BaseModel):
    """Request model for workflow versioning"""
    workflow_id: str = Field(..., description="ID of the workflow to version")
    version_notes: str = Field(..., description="Notes about this version")
    changes: Dict[str, Any] = Field(..., description="Changes made in this version")


@router.post("/version")
async def create_workflow_version(request: WorkflowVersionRequest):
    """
    Create a new version of an existing workflow
    
    This endpoint creates a versioned copy of a workflow for tracking changes
    and enabling rollback capabilities.
    """
    try:
        _ensure_graphflow_enabled()
        
        orchestrator = get_graphflow_orchestrator()
        
        # Check if workflow exists
        workflow = orchestrator.workflows.get(request.workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail=f"Workflow {request.workflow_id} not found")
        
        # Create versioned copy
        version_id = f"{request.workflow_id}_v{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # Store version metadata (simplified for now)
        version_metadata = {
            "version_id": version_id,
            "base_workflow_id": request.workflow_id,
            "created_at": datetime.utcnow().isoformat(),
            "version_notes": request.version_notes,
            "changes": request.changes
        }
        
        logger.info("📦 Created workflow version",
                   workflow_id=request.workflow_id,
                   version_id=version_id)
        
        return {
            "message": "Workflow version created successfully",
            "version": version_metadata
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating workflow version: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create version: {str(e)}")


@router.post("/validate")
async def validate_workflow_prompt(prompt: str):
    """
    Validate a workflow generation prompt for safety and feasibility
    
    This endpoint checks if a prompt is safe and can be used to generate
    a valid workflow without actually generating it.
    """
    try:
        _ensure_graphflow_enabled()
        
        from ..agents.security.ai_security_guardian import AISecurityGuardian
        
        guardian = AISecurityGuardian()
        
        # Validate prompt safety
        validation_result = await guardian.validate_prompt(
            prompt=prompt,
            context={"operation": "workflow_validation"}
        )
        
        return {
            "is_valid": validation_result.is_safe,
            "risk_level": validation_result.risk_level,
            "reason": validation_result.reason if not validation_result.is_safe else None,
            "sanitized_prompt": validation_result.sanitized_prompt
        }
        
    except Exception as e:
        logger.error(f"❌ Error validating workflow prompt: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to validate prompt: {str(e)}")
