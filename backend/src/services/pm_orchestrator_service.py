"""
PM Orchestrator Service
AI-orchestrated project management using UnifiedOrchestrator patterns
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from uuid import UUID
import structlog

from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..agents.services.unified_orchestrator_adapter import get_unified_orchestrator
from ..services.unified_cost_tracker import unified_cost_tracker
from ..services.realtime_streaming_service import publish_orchestration_update
from ..core.database import get_async_session
from ..core.config import get_settings

from ..models.project import Project
from ..models.project_orchestration import (
    ProjectOrchestration, ProjectAgentAssignment, ProjectJourneyStage,
    ProjectTouchpoint, ProjectConversation, AgentCollaborationMetric,
    OrchestrationStatus, JourneyStage, TouchpointType, AgentRole
)
from ..api.schemas.project_orchestration import (
    EnhancedProjectCreateRequest, ProjectOrchestrationResponse,
    ProjectOrchestrationDetailResponse, AgentAssignmentResponse, JourneyStageResponse, TouchpointResponse
)

logger = structlog.get_logger()


class PMOrchestratorService:
    """
    Enhanced PM service using orchestrator patterns from UnifiedOrchestrator
    Transforms traditional project management into AI-orchestrated workflows
    """
    
    def __init__(self):
        self.unified_orchestrator = get_unified_orchestrator()
        self.settings = get_settings()
        self.cost_tracker = unified_cost_tracker
        
        # Agent assignment logic mapping
        self.project_type_agents = {
            "web_development": ["baccio-tech-architect", "davide-project-manager", "luca-security"],
            "data_analysis": ["amy-cfo", "diana-performance-dashboard", "ali-chief-of-staff"],
            "marketing_campaign": ["sofia-social-media", "amy-cfo", "davide-project-manager"],
            "enterprise_transformation": ["ali-chief-of-staff", "antonio-strategy", "marcus-pm"],
            "product_development": ["baccio-tech-architect", "diana-performance-dashboard", "marcus-pm"],
            "ai_implementation": ["ali-chief-of-staff", "baccio-tech-architect", "luca-security"],
            "compliance_audit": ["luca-security", "amy-cfo", "antonio-strategy"],
            "customer_support": ["sofia-social-media", "diana-performance-dashboard", "davide-project-manager"]
        }
        
        # Journey stage configurations
        self.default_journey_stages = [
            {"stage": JourneyStage.DISCOVERY, "order": 1, "estimated_duration": 5},
            {"stage": JourneyStage.PLANNING, "order": 2, "estimated_duration": 10},
            {"stage": JourneyStage.EXECUTION, "order": 3, "estimated_duration": 30},
            {"stage": JourneyStage.VALIDATION, "order": 4, "estimated_duration": 7},
            {"stage": JourneyStage.DELIVERY, "order": 5, "estimated_duration": 3},
            {"stage": JourneyStage.CLOSURE, "order": 6, "estimated_duration": 2}
        ]
    
    async def create_orchestrated_project(
        self, 
        request: EnhancedProjectCreateRequest,
        user_id: Optional[str] = None,
        db: Optional[AsyncSession] = None
    ) -> ProjectOrchestrationDetailResponse:
        """Create project with AI orchestration"""
        
        if db is None:
            async with get_async_session() as db:
                return await self._create_orchestrated_project_impl(request, user_id, db)
        else:
            return await self._create_orchestrated_project_impl(request, user_id, db)
    
    async def _create_orchestrated_project_impl(
        self,
        request: EnhancedProjectCreateRequest,
        user_id: Optional[str],
        db: AsyncSession
    ) -> ProjectOrchestrationDetailResponse:
        """Implementation of orchestrated project creation"""
        
        try:
            # 1. Create base project
            project = Project(
                name=request.name,
                description=request.description,
                status='planning',
                start_date=datetime.utcnow(),
                end_date=datetime.utcnow() + timedelta(days=request.timeline_days or 90),
                budget=request.budget or 0.0,
                tags=request.tags,
                custom_fields=request.custom_fields
            )
            
            db.add(project)
            await db.flush()  # Get project ID
            
            # 2. Determine primary agent if not specified
            primary_agent = request.primary_agent
            if not primary_agent:
                primary_agent = await self._determine_primary_agent(request.project_type, request.requirements)
            
            # 3. Create orchestration record
            orchestration = ProjectOrchestration(
                project_id=project.id,
                orchestration_enabled=True,
                primary_agent=primary_agent,
                coordination_pattern=request.orchestration_config.coordination_pattern,
                auto_agent_assignment=request.orchestration_config.auto_agent_assignment,
                real_time_monitoring=request.orchestration_config.real_time_monitoring,
                orchestration_status=OrchestrationStatus.INITIALIZING,
                current_stage=JourneyStage.DISCOVERY,
                orchestration_config=request.orchestration_config.dict(),
                context_data=request.context,
                constraints=request.constraints,
                success_criteria=request.success_criteria
            )
            
            db.add(orchestration)
            await db.flush()  # Get orchestration ID
            
            # 4. Initialize journey stages
            await self._initialize_journey_stages(orchestration.id, db)
            
            # 5. Auto-assign agents if enabled
            if request.orchestration_config.auto_agent_assignment:
                await self._auto_assign_agents(orchestration.id, request.project_type, request.requirements, db)
            
            # 6. Initialize AI orchestration
            orchestration_result = await self._initialize_ai_orchestration(
                orchestration, request, user_id
            )
            
            # 7. Create initial touchpoint
            await self._create_touchpoint(
                orchestration.id,
                TouchpointType.AGENT_INTERACTION,
                "Project Initialization",
                f"AI orchestration initialized for {request.name}",
                [primary_agent],
                db
            )
            
            # 8. Update orchestration status
            orchestration.orchestration_status = OrchestrationStatus.ACTIVE
            orchestration.active_conversation_id = orchestration_result.get("conversation_id")
            
            await db.commit()
            
            # 9. Publish real-time update
            await publish_orchestration_update(
                orchestration_id=str(orchestration.id),
                update_type="orchestration_created",
                data={
                    "project_name": request.name,
                    "primary_agent": primary_agent,
                    "orchestration_status": "active",
                    "current_stage": "discovery"
                }
            )
            
            # 10. Return detailed response
            return await self._get_orchestration_detail(orchestration.id, db)
            
        except Exception as e:
            await db.rollback()
            logger.error("Failed to create orchestrated project", error=str(e), project_name=request.name)
            raise
    
    async def get_orchestration_status(
        self, 
        orchestration_id: UUID,
        db: Optional[AsyncSession] = None
    ) -> ProjectOrchestrationDetailResponse:
        """Get comprehensive orchestration status"""
        
        if db is None:
            async with get_async_session() as db:
                return await self._get_orchestration_detail(orchestration_id, db)
        else:
            return await self._get_orchestration_detail(orchestration_id, db)
    
    async def _get_orchestration_detail(
        self,
        orchestration_id: UUID,
        db: AsyncSession
    ) -> ProjectOrchestrationDetailResponse:
        """Get detailed orchestration information with relationships"""
        
        # Get orchestration with all relationships
        stmt = (
            select(ProjectOrchestration)
            .options(
                selectinload(ProjectOrchestration.agent_assignments),
                selectinload(ProjectOrchestration.journey_stages),
                selectinload(ProjectOrchestration.touchpoints).limit(10),  # Recent touchpoints
                selectinload(ProjectOrchestration.conversations).limit(5)   # Active conversations
            )
            .where(ProjectOrchestration.id == orchestration_id)
        )
        
        result = await db.execute(stmt)
        orchestration = result.scalar_one_or_none()
        
        if not orchestration:
            raise ValueError(f"Orchestration {orchestration_id} not found")
        
        # Convert to response models
        agent_assignments = [
            AgentAssignmentResponse.from_orm(assignment) 
            for assignment in orchestration.agent_assignments
        ]
        
        journey_stages = [
            JourneyStageResponse.from_orm(stage) 
            for stage in sorted(orchestration.journey_stages, key=lambda x: x.stage_order)
        ]
        
        recent_touchpoints = [
            TouchpointResponse.from_orm(touchpoint) 
            for touchpoint in sorted(orchestration.touchpoints, key=lambda x: x.interaction_date, reverse=True)[:5]
        ]
        
        active_conversations = [
            self._convert_conversation_to_response(conv) 
            for conv in orchestration.conversations if conv.status == 'active'
        ]
        
        # Create detailed response
        base_response = ProjectOrchestrationResponse.from_orm(orchestration)
        
        return ProjectOrchestrationDetailResponse(
            **base_response.dict(),
            agent_assignments=agent_assignments,
            journey_stages=journey_stages,
            recent_touchpoints=recent_touchpoints,
            active_conversations=active_conversations
        )
    
    async def update_journey_stage(
        self,
        orchestration_id: UUID,
        stage_name: JourneyStage,
        status: str,
        progress_percentage: float,
        notes: Optional[str] = None,
        deliverables: Optional[List[str]] = None,
        db: Optional[AsyncSession] = None
    ) -> JourneyStageResponse:
        """Update journey stage progress"""
        
        if db is None:
            async with get_async_session() as db:
                return await self._update_journey_stage_impl(
                    orchestration_id, stage_name, status, progress_percentage, 
                    notes, deliverables, db
                )
        else:
            return await self._update_journey_stage_impl(
                orchestration_id, stage_name, status, progress_percentage, 
                notes, deliverables, db
            )
    
    async def _update_journey_stage_impl(
        self,
        orchestration_id: UUID,
        stage_name: JourneyStage,
        status: str,
        progress_percentage: float,
        notes: Optional[str],
        deliverables: Optional[List[str]],
        db: AsyncSession
    ) -> JourneyStageResponse:
        """Implementation of journey stage update"""
        
        # Get the stage
        stmt = select(ProjectJourneyStage).where(
            and_(
                ProjectJourneyStage.orchestration_id == orchestration_id,
                ProjectJourneyStage.stage_name == stage_name
            )
        )
        result = await db.execute(stmt)
        stage = result.scalar_one_or_none()
        
        if not stage:
            raise ValueError(f"Journey stage {stage_name} not found for orchestration {orchestration_id}")
        
        # Update stage
        stage.status = status
        stage.progress_percentage = progress_percentage
        stage.updated_at = datetime.utcnow()
        
        if notes:
            stage.stage_notes = notes
        
        if deliverables:
            stage.actual_deliverables = deliverables
        
        # If completing stage, set end date
        if status == 'completed' and not stage.end_date:
            stage.end_date = datetime.utcnow()
            stage.actual_duration_days = (stage.end_date - stage.start_date).days if stage.start_date else None
        
        # If starting stage, set start date
        if status == 'active' and not stage.start_date:
            stage.start_date = datetime.utcnow()
        
        # Update orchestration current stage if this is the active stage
        if status == 'active':
            orchestration_stmt = (
                update(ProjectOrchestration)
                .where(ProjectOrchestration.id == orchestration_id)
                .values(current_stage=stage_name, updated_at=datetime.utcnow())
            )
            await db.execute(orchestration_stmt)
        
        await db.commit()
        
        # Publish real-time stage update
        await publish_orchestration_update(
            orchestration_id=str(orchestration_id),
            update_type="stage_updated",
            data={
                "stage_name": stage_name.value,
                "status": status,
                "progress_percentage": progress_percentage,
                "notes": notes,
                "deliverables_count": len(deliverables) if deliverables else 0
            }
        )
        
        return JourneyStageResponse.from_orm(stage)
    
    async def create_touchpoint(
        self,
        orchestration_id: UUID,
        touchpoint_type: TouchpointType,
        title: str,
        summary: Optional[str] = None,
        participants: Optional[List[str]] = None,
        duration_minutes: Optional[int] = None,
        key_decisions: Optional[List[str]] = None,
        action_items: Optional[List[str]] = None,
        db: Optional[AsyncSession] = None
    ) -> TouchpointResponse:
        """Create a new project touchpoint"""
        
        if db is None:
            async with get_async_session() as db:
                return await self._create_touchpoint(
                    orchestration_id, touchpoint_type, title, summary,
                    participants, duration_minutes, key_decisions, action_items, db
                )
        else:
            return await self._create_touchpoint(
                orchestration_id, touchpoint_type, title, summary,
                participants, duration_minutes, key_decisions, action_items, db
            )
    
    async def _create_touchpoint(
        self,
        orchestration_id: UUID,
        touchpoint_type: TouchpointType,
        title: str,
        summary: Optional[str],
        participants: Optional[List[str]],
        duration_minutes: Optional[int],
        key_decisions: Optional[List[str]],
        action_items: Optional[List[str]],
        db: AsyncSession
    ) -> TouchpointResponse:
        """Implementation of touchpoint creation"""
        
        touchpoint = ProjectTouchpoint(
            orchestration_id=orchestration_id,
            touchpoint_type=touchpoint_type,
            title=title,
            summary=summary or "",
            initiated_by=participants[0] if participants else "system",
            participants=participants or [],
            duration_minutes=duration_minutes,
            key_decisions=key_decisions or [],
            action_items=action_items or [],
            interaction_date=datetime.utcnow()
        )
        
        db.add(touchpoint)
        
        # Update touchpoint count in orchestration
        orchestration_stmt = (
            update(ProjectOrchestration)
            .where(ProjectOrchestration.id == orchestration_id)
            .values(
                touchpoint_count=ProjectOrchestration.touchpoint_count + 1,
                updated_at=datetime.utcnow()
            )
        )
        await db.execute(orchestration_stmt)
        
        await db.commit()
        await db.refresh(touchpoint)
        
        # Publish real-time touchpoint update
        await publish_orchestration_update(
            orchestration_id=str(orchestration_id),
            update_type="touchpoint_created",
            data={
                "touchpoint_type": touchpoint_type.value,
                "title": title,
                "participants": participants or [],
                "duration_minutes": duration_minutes,
                "satisfaction_score": touchpoint.satisfaction_score
            }
        )
        
        return TouchpointResponse.from_orm(touchpoint)
    
    async def optimize_project(
        self,
        orchestration_id: UUID,
        optimization_type: str = "all",
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """Use AI to optimize project performance"""
        
        if db is None:
            async with get_async_session() as db:
                return await self._optimize_project_impl(orchestration_id, optimization_type, db)
        else:
            return await self._optimize_project_impl(orchestration_id, optimization_type, db)
    
    async def _optimize_project_impl(
        self,
        orchestration_id: UUID,
        optimization_type: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Implementation of project optimization"""
        
        # Get current project state
        orchestration = await db.get(ProjectOrchestration, orchestration_id)
        if not orchestration:
            raise ValueError(f"Orchestration {orchestration_id} not found")
        
        # Get performance metrics
        performance_data = await self._get_performance_metrics(orchestration_id, db)
        
        # Get agent collaboration data
        collaboration_data = await self._get_collaboration_metrics(orchestration_id, db)
        
        # Create optimization prompt
        optimization_prompt = f"""
        Analyze the current project performance and provide optimization recommendations:
        
        Project: {orchestration.project.name if orchestration.project else 'Unknown'}
        Current Stage: {orchestration.current_stage}
        Orchestration Status: {orchestration.orchestration_status}
        
        Performance Metrics:
        - AI Efficiency Score: {orchestration.ai_efficiency_score}
        - Collaboration Score: {orchestration.agent_collaboration_score}
        - Cost per Deliverable: ${orchestration.cost_per_deliverable}
        - Satisfaction Score: {orchestration.satisfaction_score}
        
        Agent Performance: {json.dumps(performance_data, indent=2)}
        Collaboration Analysis: {json.dumps(collaboration_data, indent=2)}
        
        Optimization Focus: {optimization_type}
        
        Provide specific recommendations for:
        1. Agent reassignments for better efficiency
        2. Process improvements to reduce bottlenecks
        3. Cost optimization opportunities
        4. Timeline acceleration possibilities
        5. Quality improvement measures
        
        Format response as structured JSON with recommendations and predicted impacts.
        """
        
        # Use UnifiedOrchestrator for optimization analysis
        try:
            result = await self.unified_orchestrator.orchestrate(
                message=optimization_prompt,
                user_id="system",
                conversation_id=f"optimization_{orchestration_id}",
                context={
                    "type": "project_optimization",
                    "orchestration_id": str(orchestration_id),
                    "optimization_type": optimization_type
                }
            )
            
            # Update last optimization timestamp
            orchestration.last_optimization = datetime.utcnow()
            await db.commit()
            
            return {
                "orchestration_id": str(orchestration_id),
                "optimization_type": optimization_type,
                "analysis_result": result,
                "current_performance": performance_data,
                "recommendations": result.get("recommendations", []),
                "predicted_improvements": result.get("improvements", {}),
                "analysis_date": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Optimization analysis failed", error=str(e), orchestration_id=str(orchestration_id))
            return {
                "orchestration_id": str(orchestration_id),
                "optimization_type": optimization_type,
                "error": f"Optimization analysis failed: {str(e)}",
                "analysis_date": datetime.utcnow().isoformat()
            }
    
    # Helper methods
    
    async def _determine_primary_agent(self, project_type: str, requirements: List[str]) -> str:
        """Determine the best primary agent for the project"""
        
        # Get agents for project type
        potential_agents = self.project_type_agents.get(project_type, ["ali-chief-of-staff"])

        # For now, return the first agent
        return potential_agents[0] if potential_agents else "ali-chief-of-staff"
    
    async def _initialize_journey_stages(self, orchestration_id: UUID, db: AsyncSession):
        """Initialize default journey stages for the project"""
        
        stages = []
        for stage_config in self.default_journey_stages:
            stage = ProjectJourneyStage(
                orchestration_id=orchestration_id,
                stage_name=stage_config["stage"],
                stage_order=stage_config["order"],
                estimated_duration_days=stage_config["estimated_duration"],
                status='pending',
                expected_deliverables=self._get_default_deliverables(stage_config["stage"])
            )
            stages.append(stage)
        
        # Set first stage as active
        if stages:
            stages[0].status = 'active'
            stages[0].start_date = datetime.utcnow()
        
        db.add_all(stages)
    
    async def _auto_assign_agents(
        self, 
        orchestration_id: UUID, 
        project_type: str, 
        requirements: List[str], 
        db: AsyncSession
    ):
        """Automatically assign agents based on project type and requirements"""
        
        agents_to_assign = self.project_type_agents.get(project_type, ["ali-chief-of-staff"])
        
        assignments = []
        for i, agent_name in enumerate(agents_to_assign):
            role = AgentRole.PRIMARY if i == 0 else AgentRole.CONTRIBUTOR
            
            assignment = ProjectAgentAssignment(
                orchestration_id=orchestration_id,
                agent_name=agent_name,
                agent_role=role,
                assignment_reason=f"Auto-assigned for {project_type} project",
                active=True
            )
            assignments.append(assignment)
        
        db.add_all(assignments)
    
    async def _initialize_ai_orchestration(
        self,
        orchestration: ProjectOrchestration,
        request: EnhancedProjectCreateRequest,
        user_id: Optional[str]
    ) -> Dict[str, Any]:
        """Initialize AI orchestration for the project"""
        
        initialization_prompt = f"""
        Initialize AI orchestration for project: {request.name}
        
        Project Details:
        - Type: {request.project_type}
        - Description: {request.description}
        - Requirements: {', '.join(request.requirements)}
        - Constraints: {', '.join(request.constraints)}
        - Budget: ${request.budget or 'Not specified'}
        - Timeline: {request.timeline_days or 'Not specified'} days
        
        Primary Agent: {orchestration.primary_agent}
        Coordination Pattern: {orchestration.coordination_pattern}
        
        Please:
        1. Acknowledge project initialization
        2. Outline the orchestration approach
        3. Identify key coordination points
        4. Suggest initial tasks and priorities
        5. Highlight potential risks and mitigation strategies
        """
        
        try:
            result = await self.unified_orchestrator.orchestrate(
                message=initialization_prompt,
                user_id=user_id or "system",
                conversation_id=f"init_{orchestration.id}",
                context={
                    "type": "project_initialization",
                    "orchestration_id": str(orchestration.id),
                    "project_type": request.project_type
                }
            )
            
            return {
                "success": True,
                "conversation_id": f"init_{orchestration.id}",
                "orchestration_result": result
            }
            
        except Exception as e:
            logger.error("AI orchestration initialization failed", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_default_deliverables(self, stage: JourneyStage) -> List[str]:
        """Get default deliverables for a journey stage"""
        
        deliverables_map = {
            JourneyStage.DISCOVERY: [
                "Requirements document",
                "Stakeholder analysis",
                "Risk assessment",
                "Success criteria definition"
            ],
            JourneyStage.PLANNING: [
                "Project plan",
                "Resource allocation",
                "Timeline with milestones",
                "Budget breakdown"
            ],
            JourneyStage.EXECUTION: [
                "Implementation deliverables",
                "Progress reports",
                "Quality checkpoints",
                "Issue resolution logs"
            ],
            JourneyStage.VALIDATION: [
                "Testing results",
                "Quality assurance report",
                "Stakeholder approval",
                "Performance metrics"
            ],
            JourneyStage.DELIVERY: [
                "Final deliverable",
                "Documentation",
                "Training materials",
                "Handover package"
            ],
            JourneyStage.CLOSURE: [
                "Project retrospective",
                "Lessons learned",
                "Final report",
                "Knowledge transfer"
            ]
        }
        
        return deliverables_map.get(stage, [])
    
    async def _get_performance_metrics(self, orchestration_id: UUID, db: AsyncSession) -> Dict[str, Any]:
        """Get current performance metrics for the orchestration"""
        
        # Get agent assignments with performance data
        stmt = select(ProjectAgentAssignment).where(
            ProjectAgentAssignment.orchestration_id == orchestration_id
        )
        result = await db.execute(stmt)
        assignments = result.scalars().all()
        
        agent_performance = {}
        for assignment in assignments:
            agent_performance[assignment.agent_name] = {
                "tasks_completed": assignment.tasks_completed,
                "efficiency_score": assignment.efficiency_score,
                "collaboration_score": assignment.collaboration_score,
                "cost_incurred": assignment.cost_incurred
            }
        
        return {
            "agent_performance": agent_performance,
            "total_agents": len(assignments),
            "active_agents": len([a for a in assignments if a.active])
        }
    
    async def _get_collaboration_metrics(self, orchestration_id: UUID, db: AsyncSession) -> Dict[str, Any]:
        """Get agent collaboration metrics"""
        
        # Get collaboration metrics
        stmt = select(AgentCollaborationMetric).where(
            AgentCollaborationMetric.orchestration_id == orchestration_id
        )
        result = await db.execute(stmt)
        metrics = result.scalars().all()
        
        collaboration_data = {}
        for metric in metrics:
            pair_key = f"{metric.primary_agent}-{metric.secondary_agent}" if metric.secondary_agent else metric.primary_agent
            collaboration_data[pair_key] = {
                "synergy_score": metric.synergy_score,
                "conflict_score": metric.conflict_score,
                "efficiency_multiplier": metric.efficiency_multiplier
            }
        
        return {
            "collaboration_pairs": collaboration_data,
            "total_collaborations": len(metrics)
        }
    
    def _convert_conversation_to_response(self, conversation: ProjectConversation) -> Dict[str, Any]:
        """Convert conversation model to response format"""
        
        return {
            "id": str(conversation.id),
            "conversation_id": conversation.conversation_id,
            "topic": conversation.topic,
            "purpose": conversation.purpose,
            "participants": conversation.participants,
            "status": conversation.status,
            "message_count": conversation.message_count,
            "efficiency_score": conversation.efficiency_score,
            "total_cost": conversation.total_cost,
            "start_time": conversation.start_time,
            "end_time": conversation.end_time
        }