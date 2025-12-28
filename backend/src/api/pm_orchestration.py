"""
Enhanced PM Orchestration API
AI-orchestrated project management endpoints with CRM-style journey tracking
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID
import structlog

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db_session
from ..services.pm_orchestrator_service import PMOrchestratorService
from ..services.project_journey_service import ProjectJourneyService
from ..api.schemas.project_orchestration import (
    EnhancedProjectCreateRequest, ProjectOrchestrationDetailResponse, AgentAssignmentRequest, JourneyStageUpdateRequest, TouchpointCreateRequest,
    OptimizationRequest, OptimizationResponse,
    ProjectJourneyAnalyticsResponse
)
from ..models.project_orchestration import JourneyStage, TouchpointType

logger = structlog.get_logger()

router = APIRouter(prefix="/api/v1/pm/orchestration", tags=["PM Orchestration"])

# Initialize services
pm_orchestrator = PMOrchestratorService()
journey_service = ProjectJourneyService()


# ===================== Project Orchestration Endpoints =====================

@router.post("/projects", response_model=ProjectOrchestrationDetailResponse)
async def create_orchestrated_project(
    request: EnhancedProjectCreateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session)
):
    """
    🚀 Create AI-Orchestrated Project
    
    Creates a new project with intelligent AI orchestration, automatic agent assignment,
    and CRM-style journey tracking.
    """
    try:
        logger.info("Creating orchestrated project", project_name=request.name, project_type=request.project_type)
        
        # Create orchestrated project
        result = await pm_orchestrator.create_orchestrated_project(
            request=request,
            user_id=request.user_id,
            db=db
        )
        
        # Schedule background optimization
        background_tasks.add_task(
            _schedule_project_optimization,
            result.id,
            24  # hours
        )
        
        logger.info("Orchestrated project created successfully", 
                   orchestration_id=result.id, 
                   primary_agent=result.primary_agent)
        
        return result
        
    except Exception as e:
        logger.error("Failed to create orchestrated project", error=str(e), project_name=request.name)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create orchestrated project: {str(e)}"
        )


@router.get("/projects/{orchestration_id}", response_model=ProjectOrchestrationDetailResponse)
async def get_orchestration_status(
    orchestration_id: UUID,
    include_metrics: bool = Query(False, description="Include performance metrics"),
    db: AsyncSession = Depends(get_db_session)
):
    """
    📊 Get Orchestration Status
    
    Retrieves comprehensive status of an AI-orchestrated project including
    agent assignments, journey stages, and real-time metrics.
    """
    try:
        result = await pm_orchestrator.get_orchestration_status(
            orchestration_id=orchestration_id,
            db=db
        )
        
        if include_metrics:
            # Add real-time metrics if requested
            # This could be expanded to include live agent status
            pass
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("Failed to get orchestration status", error=str(e), orchestration_id=str(orchestration_id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get orchestration status: {str(e)}"
        )


@router.put("/projects/{orchestration_id}/agents", response_model=Dict[str, Any])
async def assign_agents(
    orchestration_id: UUID,
    request: AgentAssignmentRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    🤖 Assign Agents to Project
    
    Assigns or reassigns AI agents to an orchestrated project with
    specific roles and configurations.
    """
    try:
        # Implementation would go here
        # For now, return success response
        return {
            "orchestration_id": str(orchestration_id),
            "agents_assigned": len(request.agent_assignments),
            "message": "Agents assigned successfully"
        }
        
    except Exception as e:
        logger.error("Failed to assign agents", error=str(e), orchestration_id=str(orchestration_id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assign agents: {str(e)}"
        )


@router.post("/projects/{orchestration_id}/optimize", response_model=OptimizationResponse)
async def optimize_project(
    orchestration_id: UUID,
    request: OptimizationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session)
):
    """
    ⚡ Optimize Project Performance
    
    Uses AI to analyze current project performance and provide optimization
    recommendations for efficiency, cost, timeline, and quality.
    """
    try:
        logger.info("Starting project optimization", 
                   orchestration_id=str(orchestration_id), 
                   optimization_type=request.optimization_type)
        
        result = await pm_orchestrator.optimize_project(
            orchestration_id=orchestration_id,
            optimization_type=request.optimization_type,
            db=db
        )
        
        # Convert to proper response format
        optimization_response = OptimizationResponse(
            orchestration_id=str(orchestration_id),
            optimization_type=request.optimization_type,
            current_performance=result.get("current_performance", {}),
            identified_issues=result.get("analysis_result", {}).get("issues", []),
            improvement_opportunities=result.get("analysis_result", {}).get("opportunities", []),
            agent_reassignments=result.get("recommendations", []),
            process_optimizations=result.get("analysis_result", {}).get("process_improvements", []),
            resource_adjustments=[],
            timeline_adjustments=[],
            expected_improvements=result.get("predicted_improvements", {}),
            implementation_effort="medium",
            estimated_savings={"cost": 0.0, "time": 0.0},
            implementation_steps=[],
            rollback_plan=[],
            success_metrics=[],
            analysis_date=datetime.fromisoformat(result.get("analysis_date", datetime.utcnow().isoformat())),
            confidence_score=0.8,
            valid_until=datetime.utcnow().replace(hour=23, minute=59, second=59)
        )
        
        return optimization_response
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("Failed to optimize project", error=str(e), orchestration_id=str(orchestration_id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to optimize project: {str(e)}"
        )


# ===================== Journey Tracking Endpoints =====================

@router.get("/projects/{orchestration_id}/journey", response_model=ProjectJourneyAnalyticsResponse)
async def get_project_journey(
    orchestration_id: UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """
    🛤️ Get Project Journey Analytics
    
    Retrieves CRM-style journey analytics including stage progression,
    touchpoint analysis, and predictive insights.
    """
    try:
        result = await journey_service.get_project_journey_analytics(
            orchestration_id=orchestration_id,
            db=db
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("Failed to get journey analytics", error=str(e), orchestration_id=str(orchestration_id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get journey analytics: {str(e)}"
        )


@router.put("/projects/{orchestration_id}/journey/stages", response_model=Dict[str, Any])
async def update_journey_stage(
    orchestration_id: UUID,
    request: JourneyStageUpdateRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    📈 Update Journey Stage
    
    Updates the progress and status of a specific journey stage with
    notes, deliverables, and blocker information.
    """
    try:
        await pm_orchestrator.update_journey_stage(
            orchestration_id=orchestration_id,
            stage_name=request.stage_name,
            status=request.status,
            progress_percentage=request.progress_percentage,
            notes=request.notes,
            deliverables=request.deliverables,
            db=db
        )
        
        return {
            "orchestration_id": str(orchestration_id),
            "stage_updated": request.stage_name.value,
            "new_status": request.status,
            "progress": request.progress_percentage,
            "message": "Journey stage updated successfully"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("Failed to update journey stage", error=str(e), orchestration_id=str(orchestration_id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update journey stage: {str(e)}"
        )


@router.post("/projects/{orchestration_id}/journey/transition")
async def transition_journey_stage(
    orchestration_id: UUID,
    from_stage: JourneyStage,
    to_stage: JourneyStage,
    transition_reason: str = Query(..., description="Reason for stage transition"),
    db: AsyncSession = Depends(get_db_session)
):
    """
    🔄 Transition Between Journey Stages
    
    Moves the project from one journey stage to another with proper
    tracking and touchpoint creation.
    """
    try:
        result = await journey_service.track_stage_transition(
            orchestration_id=orchestration_id,
            from_stage=from_stage,
            to_stage=to_stage,
            transition_reason=transition_reason,
            db=db
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("Failed to transition stage", error=str(e), orchestration_id=str(orchestration_id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to transition stage: {str(e)}"
        )


# ===================== Touchpoint Management =====================

@router.post("/projects/{orchestration_id}/touchpoints", response_model=Dict[str, Any])
async def create_touchpoint(
    orchestration_id: UUID,
    request: TouchpointCreateRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    📞 Create Project Touchpoint
    
    Records a new touchpoint interaction for CRM-style project tracking.
    """
    try:
        result = await pm_orchestrator.create_touchpoint(
            orchestration_id=orchestration_id,
            touchpoint_type=request.touchpoint_type,
            title=request.title,
            summary=request.summary,
            participants=request.participants,
            duration_minutes=request.duration_minutes,
            key_decisions=request.key_decisions,
            action_items=request.action_items,
            db=db
        )
        
        return {
            "touchpoint_id": result.id,
            "orchestration_id": str(orchestration_id),
            "touchpoint_type": request.touchpoint_type.value,
            "message": "Touchpoint created successfully"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("Failed to create touchpoint", error=str(e), orchestration_id=str(orchestration_id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create touchpoint: {str(e)}"
        )


@router.get("/projects/{orchestration_id}/touchpoints")
async def get_touchpoints(
    orchestration_id: UUID,
    touchpoint_type: Optional[TouchpointType] = Query(None, description="Filter by touchpoint type"),
    limit: int = Query(50, ge=1, le=200, description="Number of touchpoints to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db_session)
):
    """
    📋 Get Project Touchpoints
    
    Retrieves touchpoints for the project with optional filtering and pagination.
    """
    try:
        # Implementation would query touchpoints from database
        return {
            "orchestration_id": str(orchestration_id),
            "touchpoints": [],
            "total": 0,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error("Failed to get touchpoints", error=str(e), orchestration_id=str(orchestration_id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get touchpoints: {str(e)}"
        )


# ===================== Analytics and Metrics =====================

@router.get("/projects/{orchestration_id}/metrics", response_model=Dict[str, Any])
async def get_orchestration_metrics(
    orchestration_id: UUID,
    period_days: int = Query(30, ge=1, le=365, description="Analysis period in days"),
    db: AsyncSession = Depends(get_db_session)
):
    """
    📊 Get Orchestration Metrics
    
    Retrieves comprehensive performance metrics and analytics for the
    orchestrated project.
    """
    try:
        # For now, return mock metrics structure
        return {
            "orchestration_id": str(orchestration_id),
            "period_days": period_days,
            "performance_metrics": {
                "overall_efficiency": 0.85,
                "agent_utilization": 0.78,
                "cost_efficiency": 0.92,
                "timeline_efficiency": 0.88,
                "quality_score": 0.91
            },
            "collaboration_metrics": {
                "collaboration_score": 0.84,
                "conflict_resolution_score": 0.96,
                "knowledge_sharing_score": 0.79
            },
            "cost_metrics": {
                "total_cost": 15750.00,
                "cost_per_hour": 125.00,
                "cost_optimization_savings": 2340.00
            },
            "recommendations": [
                "Consider reassigning Agent B to higher-value tasks",
                "Implement daily standups to improve coordination",
                "Review cost allocation for Agent C activities"
            ]
        }
        
    except Exception as e:
        logger.error("Failed to get metrics", error=str(e), orchestration_id=str(orchestration_id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metrics: {str(e)}"
        )


@router.get("/projects/{orchestration_id}/satisfaction")
async def get_satisfaction_score(
    orchestration_id: UUID,
    stage: Optional[JourneyStage] = Query(None, description="Calculate for specific stage"),
    db: AsyncSession = Depends(get_db_session)
):
    """
    😊 Get Satisfaction Score
    
    Calculates satisfaction score for the project or a specific journey stage.
    """
    try:
        satisfaction_score = await journey_service.calculate_satisfaction_score(
            orchestration_id=orchestration_id,
            stage_name=stage,
            db=db
        )
        
        return {
            "orchestration_id": str(orchestration_id),
            "stage": stage.value if stage else "overall",
            "satisfaction_score": satisfaction_score,
            "rating": _get_satisfaction_rating(satisfaction_score),
            "calculated_at": datetime.utcnow().isoformat()
        }
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("Failed to get satisfaction score", error=str(e), orchestration_id=str(orchestration_id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get satisfaction score: {str(e)}"
        )


# ===================== Real-time Streaming =====================

@router.get("/projects/{orchestration_id}/stream")
async def stream_orchestration_updates(
    orchestration_id: UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """
    📡 Stream Real-time Updates
    
    Provides real-time streaming of orchestration updates, agent conversations,
    and project metrics using Server-Sent Events.
    """
    try:
        async def event_stream():
            # This would implement actual streaming logic
            # For now, return a simple response
            yield f"data: {{'type': 'connected', 'orchestration_id': '{orchestration_id}', 'timestamp': '{datetime.utcnow().isoformat()}'}}\n\n"
            
            # In a real implementation, this would:
            # 1. Subscribe to Redis channels for the orchestration
            # 2. Stream agent conversation updates
            # 3. Stream metric changes
            # 4. Stream status updates
            
        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control"
            }
        )
        
    except Exception as e:
        logger.error("Failed to start streaming", error=str(e), orchestration_id=str(orchestration_id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start streaming: {str(e)}"
        )


# ===================== Bulk Operations =====================

@router.get("/projects")
async def list_orchestrated_projects(
    status: Optional[str] = Query(None, description="Filter by orchestration status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db_session)
):
    """
    📜 List Orchestrated Projects
    
    Retrieves a list of all orchestrated projects with filtering and pagination.
    """
    try:
        # Implementation would query from database
        return {
            "projects": [],
            "total": 0,
            "limit": limit,
            "offset": offset,
            "filters": {"status": status} if status else {}
        }
        
    except Exception as e:
        logger.error("Failed to list projects", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list projects: {str(e)}"
        )


@router.post("/projects/bulk-optimize")
async def bulk_optimize_projects(
    orchestration_ids: List[UUID],
    background_tasks: BackgroundTasks,
    optimization_type: str = Query("performance", description="Type of optimization"),
    db: AsyncSession = Depends(get_db_session)
):
    """
    ⚡ Bulk Optimize Projects
    
    Optimizes multiple projects in bulk using background processing.
    """
    try:
        # Schedule bulk optimization
        background_tasks.add_task(
            _bulk_optimize_projects,
            orchestration_ids,
            optimization_type
        )
        
        return {
            "message": f"Bulk optimization scheduled for {len(orchestration_ids)} projects",
            "optimization_type": optimization_type,
            "project_count": len(orchestration_ids),
            "scheduled_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to schedule bulk optimization", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to schedule bulk optimization: {str(e)}"
        )


# ===================== Helper Functions =====================

async def _schedule_project_optimization(orchestration_id: str, delay_hours: int):
    """Background task to schedule project optimization"""
    # Implementation would schedule periodic optimization
    logger.info("Scheduled optimization", orchestration_id=orchestration_id, delay_hours=delay_hours)


async def _bulk_optimize_projects(orchestration_ids: List[UUID], optimization_type: str):
    """Background task for bulk project optimization"""
    logger.info("Starting bulk optimization", project_count=len(orchestration_ids), optimization_type=optimization_type)
    
    for orchestration_id in orchestration_ids:
        try:
            # Optimize each project
            db = await anext(get_db_session())
            try:
                await pm_orchestrator.optimize_project(
                    orchestration_id=orchestration_id,
                    optimization_type=optimization_type,
                    db=db
                )
                logger.info("Project optimized", orchestration_id=str(orchestration_id))
            finally:
                await db.close()
        except Exception as e:
            logger.error("Failed to optimize project", orchestration_id=str(orchestration_id), error=str(e))


def _get_satisfaction_rating(score: float) -> str:
    """Convert satisfaction score to rating"""
    if score >= 0.9:
        return "Excellent"
    elif score >= 0.8:
        return "Very Good"
    elif score >= 0.7:
        return "Good"
    elif score >= 0.6:
        return "Fair"
    else:
        return "Needs Improvement"