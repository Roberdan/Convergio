"""
Project Journey Service
CRM-inspired project journey tracking and analytics
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from uuid import UUID
import structlog

from sqlalchemy import select, update, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..core.database import get_async_session
from ..models.project_orchestration import (
    ProjectOrchestration, ProjectJourneyStage, ProjectTouchpoint,
    JourneyStage, TouchpointType
)
from ..api.schemas.project_orchestration import (
    ProjectJourneyAnalyticsResponse
)

logger = structlog.get_logger()


class ProjectJourneyService:
    """
    CRM-inspired project journey tracking and analytics service
    Provides customer journey-style insights for project progression
    """
    
    def __init__(self):
        self.satisfaction_weights = {
            "deliverable_quality": 0.3,
            "timeline_adherence": 0.25,
            "cost_efficiency": 0.2,
            "stakeholder_feedback": 0.15,
            "team_collaboration": 0.1
        }
    
    async def get_project_journey_analytics(
        self,
        orchestration_id: UUID,
        db: Optional[AsyncSession] = None
    ) -> ProjectJourneyAnalyticsResponse:
        """Get comprehensive CRM-style journey analytics"""
        
        if db is None:
            async with get_async_session() as db:
                return await self._get_journey_analytics_impl(orchestration_id, db)
        else:
            return await self._get_journey_analytics_impl(orchestration_id, db)
    
    async def _get_journey_analytics_impl(
        self,
        orchestration_id: UUID,
        db: AsyncSession
    ) -> ProjectJourneyAnalyticsResponse:
        """Implementation of journey analytics"""
        
        # Get orchestration with journey stages
        stmt = (
            select(ProjectOrchestration)
            .options(selectinload(ProjectOrchestration.journey_stages))
            .where(ProjectOrchestration.id == orchestration_id)
        )
        result = await db.execute(stmt)
        orchestration = result.scalar_one_or_none()
        
        if not orchestration:
            raise ValueError(f"Orchestration {orchestration_id} not found")
        
        # Get journey stages ordered by stage order
        journey_stages = sorted(orchestration.journey_stages, key=lambda x: x.stage_order)
        
        # Calculate journey analytics
        stage_progression = await self._analyze_stage_progression(journey_stages)
        stage_duration_analysis = await self._analyze_stage_durations(journey_stages)
        bottleneck_analysis = await self._identify_bottlenecks(journey_stages)
        
        # Get touchpoint analytics
        touchpoint_summary = await self._get_touchpoint_summary(orchestration_id, db)
        interaction_frequency = await self._calculate_interaction_frequency(orchestration_id, db)
        satisfaction_trends = await self._get_satisfaction_trends(orchestration_id, db)
        
        # Predictive analytics
        risk_factors = await self._identify_risk_factors(orchestration, journey_stages)
        success_probability = await self._calculate_success_probability(orchestration, journey_stages)
        recommended_interventions = await self._recommend_interventions(orchestration, journey_stages, risk_factors)
        
        # Calculate completion percentage and estimated completion
        completion_percentage = self._calculate_completion_percentage(journey_stages)
        estimated_completion_date = self._estimate_completion_date(journey_stages, orchestration.journey_start_date)
        
        return ProjectJourneyAnalyticsResponse(
            orchestration_id=str(orchestration_id),
            current_stage=orchestration.current_stage,
            completion_percentage=completion_percentage,
            estimated_completion_date=estimated_completion_date,
            stage_progression=stage_progression,
            stage_duration_analysis=stage_duration_analysis,
            bottleneck_analysis=bottleneck_analysis,
            touchpoint_summary=touchpoint_summary,
            interaction_frequency=interaction_frequency,
            satisfaction_trends=satisfaction_trends,
            risk_factors=risk_factors,
            success_probability=success_probability,
            recommended_interventions=recommended_interventions
        )
    
    async def track_stage_transition(
        self,
        orchestration_id: UUID,
        from_stage: JourneyStage,
        to_stage: JourneyStage,
        transition_reason: str,
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """Track transition between journey stages"""
        
        if db is None:
            async with get_async_session() as db:
                return await self._track_stage_transition_impl(
                    orchestration_id, from_stage, to_stage, transition_reason, db
                )
        else:
            return await self._track_stage_transition_impl(
                orchestration_id, from_stage, to_stage, transition_reason, db
            )
    
    async def _track_stage_transition_impl(
        self,
        orchestration_id: UUID,
        from_stage: JourneyStage,
        to_stage: JourneyStage,
        transition_reason: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Implementation of stage transition tracking"""
        
        transition_time = datetime.utcnow()
        
        # Complete the current stage
        if from_stage:
            from_stage_stmt = (
                update(ProjectJourneyStage)
                .where(and_(
                    ProjectJourneyStage.orchestration_id == orchestration_id,
                    ProjectJourneyStage.stage_name == from_stage
                ))
                .values(
                    status='completed',
                    end_date=transition_time,
                    progress_percentage=100.0,
                    updated_at=transition_time
                )
            )
            await db.execute(from_stage_stmt)
        
        # Start the new stage
        to_stage_stmt = (
            update(ProjectJourneyStage)
            .where(and_(
                ProjectJourneyStage.orchestration_id == orchestration_id,
                ProjectJourneyStage.stage_name == to_stage
            ))
            .values(
                status='active',
                start_date=transition_time,
                progress_percentage=0.0,
                updated_at=transition_time
            )
        )
        await db.execute(to_stage_stmt)
        
        # Update orchestration current stage
        orchestration_stmt = (
            update(ProjectOrchestration)
            .where(ProjectOrchestration.id == orchestration_id)
            .values(
                current_stage=to_stage,
                updated_at=transition_time
            )
        )
        await db.execute(orchestration_stmt)
        
        # Record transition as touchpoint
        from ..services.pm_orchestrator_service import PMOrchestratorService
        pm_service = PMOrchestratorService()
        
        await pm_service._create_touchpoint(
            orchestration_id=orchestration_id,
            touchpoint_type=TouchpointType.MILESTONE_REVIEW,
            title=f"Stage Transition: {from_stage} → {to_stage}",
            summary=f"Transition reason: {transition_reason}",
            participants=["system"],
            db=db
        )
        
        await db.commit()
        
        return {
            "orchestration_id": str(orchestration_id),
            "from_stage": from_stage.value if from_stage else None,
            "to_stage": to_stage.value,
            "transition_time": transition_time.isoformat(),
            "transition_reason": transition_reason,
            "success": True
        }
    
    async def calculate_satisfaction_score(
        self,
        orchestration_id: UUID,
        stage_name: Optional[JourneyStage] = None,
        db: Optional[AsyncSession] = None
    ) -> float:
        """Calculate satisfaction score for stage or overall project"""
        
        if db is None:
            async with get_async_session() as db:
                return await self._calculate_satisfaction_score_impl(orchestration_id, stage_name, db)
        else:
            return await self._calculate_satisfaction_score_impl(orchestration_id, stage_name, db)
    
    async def _calculate_satisfaction_score_impl(
        self,
        orchestration_id: UUID,
        stage_name: Optional[JourneyStage],
        db: AsyncSession
    ) -> float:
        """Implementation of satisfaction score calculation"""
        
        # Get touchpoints for scoring
        touchpoint_query = select(ProjectTouchpoint).where(
            ProjectTouchpoint.orchestration_id == orchestration_id
        )
        
        if stage_name:
            touchpoint_query = touchpoint_query.where(
                ProjectTouchpoint.related_stage == stage_name
            )
        
        result = await db.execute(touchpoint_query)
        touchpoints = result.scalars().all()
        
        if not touchpoints:
            return 0.5  # Neutral score if no touchpoints
        
        # Calculate weighted satisfaction score
        total_weighted_score = 0.0
        total_weight = 0.0
        
        for touchpoint in touchpoints:
            # Weight touchpoints by impact level
            weight = self._get_touchpoint_weight(touchpoint.impact_level)
            satisfaction = touchpoint.satisfaction_score if touchpoint.satisfaction_score is not None else 0.5
            
            total_weighted_score += satisfaction * weight
            total_weight += weight
        
        return total_weighted_score / total_weight if total_weight > 0 else 0.5
    
    # Private helper methods
    
    async def _analyze_stage_progression(self, journey_stages: List) -> List[Dict[str, Any]]:
        """Analyze stage progression patterns"""
        
        progression = []
        for stage in journey_stages:
            stage_data = {
                "stage_name": stage.stage_name.value,
                "stage_order": stage.stage_order,
                "status": stage.status,
                "progress_percentage": stage.progress_percentage,
                "start_date": stage.start_date.isoformat() if stage.start_date else None,
                "end_date": stage.end_date.isoformat() if stage.end_date else None,
                "estimated_duration_days": stage.estimated_duration_days,
                "actual_duration_days": stage.actual_duration_days,
                "efficiency_score": stage.efficiency_score,
                "satisfaction_score": stage.satisfaction_score,
                "primary_agents": stage.primary_agents,
                "deliverables_count": len(stage.actual_deliverables) if stage.actual_deliverables else 0,
                "blockers_count": len(stage.blockers) if stage.blockers else 0
            }
            progression.append(stage_data)
        
        return progression
    
    async def _analyze_stage_durations(self, journey_stages: List) -> Dict[str, Any]:
        """Analyze duration patterns across stages"""
        
        completed_stages = [s for s in journey_stages if s.status == 'completed' and s.actual_duration_days]
        
        if not completed_stages:
            return {"message": "No completed stages to analyze"}
        
        durations = [s.actual_duration_days for s in completed_stages]
        estimated_durations = [s.estimated_duration_days for s in completed_stages if s.estimated_duration_days]
        
        analysis = {
            "average_duration": sum(durations) / len(durations),
            "min_duration": min(durations),
            "max_duration": max(durations),
            "total_completed_stages": len(completed_stages),
        }
        
        if estimated_durations:
            actual_vs_estimated = [
                (s.actual_duration_days / s.estimated_duration_days) 
                for s in completed_stages if s.estimated_duration_days
            ]
            analysis["duration_accuracy"] = sum(actual_vs_estimated) / len(actual_vs_estimated)
            analysis["on_time_delivery_rate"] = len([r for r in actual_vs_estimated if r <= 1.0]) / len(actual_vs_estimated)
        
        return analysis
    
    async def _identify_bottlenecks(self, journey_stages: List) -> List[str]:
        """Identify potential bottlenecks in the journey"""
        
        bottlenecks = []
        
        for stage in journey_stages:
            # Check for stages taking longer than estimated
            if (stage.status == 'active' and stage.start_date and stage.estimated_duration_days and
                (datetime.utcnow() - stage.start_date).days > stage.estimated_duration_days * 1.2):
                bottlenecks.append(f"Stage '{stage.stage_name.value}' is significantly overdue")
            
            # Check for stages with low progress
            if stage.status == 'active' and stage.progress_percentage < 20:
                bottlenecks.append(f"Stage '{stage.stage_name.value}' has low progress ({stage.progress_percentage}%)")
            
            # Check for stages with blockers
            if stage.blockers and len(stage.blockers) > 0:
                bottlenecks.append(f"Stage '{stage.stage_name.value}' has {len(stage.blockers)} active blockers")
            
            # Check for stages with low satisfaction
            if stage.satisfaction_score and stage.satisfaction_score < 0.6:
                bottlenecks.append(f"Stage '{stage.stage_name.value}' has low satisfaction ({stage.satisfaction_score:.2f})")
        
        return bottlenecks
    
    async def _get_touchpoint_summary(self, orchestration_id: UUID, db: AsyncSession) -> Dict[str, int]:
        """Get summary of touchpoints by type"""
        
        stmt = (
            select(ProjectTouchpoint.touchpoint_type, func.count(ProjectTouchpoint.id))
            .where(ProjectTouchpoint.orchestration_id == orchestration_id)
            .group_by(ProjectTouchpoint.touchpoint_type)
        )
        
        result = await db.execute(stmt)
        summary = {}
        
        for touchpoint_type, count in result:
            summary[touchpoint_type.value] = count
        
        return summary
    
    async def _calculate_interaction_frequency(self, orchestration_id: UUID, db: AsyncSession) -> Dict[str, float]:
        """Calculate interaction frequency patterns"""
        
        # Get touchpoints from last 30 days
        since_date = datetime.utcnow() - timedelta(days=30)
        
        stmt = (
            select(ProjectTouchpoint)
            .where(and_(
                ProjectTouchpoint.orchestration_id == orchestration_id,
                ProjectTouchpoint.interaction_date >= since_date
            ))
            .order_by(ProjectTouchpoint.interaction_date)
        )
        
        result = await db.execute(stmt)
        touchpoints = result.scalars().all()
        
        if len(touchpoints) < 2:
            return {"daily_average": 0.0, "weekly_average": 0.0}
        
        # Calculate frequencies
        total_days = (datetime.utcnow() - since_date).days
        daily_average = len(touchpoints) / total_days if total_days > 0 else 0
        weekly_average = daily_average * 7
        
        # Calculate interaction patterns by day of week
        day_patterns = {}
        for touchpoint in touchpoints:
            day_name = touchpoint.interaction_date.strftime('%A')
            day_patterns[day_name] = day_patterns.get(day_name, 0) + 1
        
        return {
            "daily_average": daily_average,
            "weekly_average": weekly_average,
            "day_patterns": day_patterns,
            "total_interactions_30_days": len(touchpoints)
        }
    
    async def _get_satisfaction_trends(self, orchestration_id: UUID, db: AsyncSession) -> List[Dict[str, Any]]:
        """Get satisfaction trends over time"""
        
        stmt = (
            select(ProjectTouchpoint)
            .where(and_(
                ProjectTouchpoint.orchestration_id == orchestration_id,
                ProjectTouchpoint.satisfaction_score.isnot(None)
            ))
            .order_by(ProjectTouchpoint.interaction_date)
        )
        
        result = await db.execute(stmt)
        touchpoints = result.scalars().all()
        
        trends = []
        for touchpoint in touchpoints:
            trends.append({
                "date": touchpoint.interaction_date.isoformat(),
                "satisfaction_score": touchpoint.satisfaction_score,
                "touchpoint_type": touchpoint.touchpoint_type.value,
                "impact_level": touchpoint.impact_level
            })
        
        return trends
    
    async def _identify_risk_factors(self, orchestration, journey_stages: List) -> List[str]:
        """Identify risk factors for project success"""
        
        risks = []
        
        # Check overall project health
        if orchestration.ai_efficiency_score < 0.7:
            risks.append("Low AI efficiency score indicates coordination issues")
        
        if orchestration.agent_collaboration_score < 0.6:
            risks.append("Poor agent collaboration may impact delivery quality")
        
        if orchestration.satisfaction_score < 0.6:
            risks.append("Low stakeholder satisfaction requires attention")
        
        # Check stage-specific risks
        active_stages = [s for s in journey_stages if s.status == 'active']
        for stage in active_stages:
            if stage.progress_percentage < 30 and stage.start_date:
                days_since_start = (datetime.utcnow() - stage.start_date).days
                if days_since_start > (stage.estimated_duration_days or 7) * 0.5:
                    risks.append(f"Stage '{stage.stage_name.value}' is behind schedule")
        
        # Check resource allocation
        if orchestration.cost_per_deliverable > 1000:  # Threshold
            risks.append("High cost per deliverable may indicate resource inefficiency")
        
        return risks
    
    async def _calculate_success_probability(self, orchestration, journey_stages: List) -> float:
        """Calculate probability of successful project completion"""
        
        factors = []
        
        # Factor 1: Overall efficiency (30% weight)
        efficiency_factor = orchestration.ai_efficiency_score * 0.3
        factors.append(efficiency_factor)
        
        # Factor 2: Collaboration quality (25% weight)
        collaboration_factor = orchestration.agent_collaboration_score * 0.25
        factors.append(collaboration_factor)
        
        # Factor 3: Satisfaction score (20% weight)
        satisfaction_factor = orchestration.satisfaction_score * 0.2
        factors.append(satisfaction_factor)
        
        # Factor 4: Stage progression (15% weight)
        completed_stages = len([s for s in journey_stages if s.status == 'completed'])
        total_stages = len(journey_stages)
        progression_factor = (completed_stages / total_stages if total_stages > 0 else 0) * 0.15
        factors.append(progression_factor)
        
        # Factor 5: Timeline adherence (10% weight)
        on_time_stages = len([
            s for s in journey_stages 
            if s.status == 'completed' and s.actual_duration_days and s.estimated_duration_days
            and s.actual_duration_days <= s.estimated_duration_days
        ])
        completed_with_estimates = len([
            s for s in journey_stages 
            if s.status == 'completed' and s.estimated_duration_days
        ])
        timeline_factor = (
            (on_time_stages / completed_with_estimates if completed_with_estimates > 0 else 0.5) * 0.1
        )
        factors.append(timeline_factor)
        
        return min(sum(factors), 1.0)  # Cap at 1.0
    
    async def _recommend_interventions(
        self, 
        orchestration, 
        journey_stages: List, 
        risk_factors: List[str]
    ) -> List[str]:
        """Recommend interventions based on analysis"""
        
        interventions = []
        
        # Address efficiency issues
        if orchestration.ai_efficiency_score < 0.7:
            interventions.append("Review agent assignments and optimize coordination patterns")
            interventions.append("Implement more frequent check-ins and status updates")
        
        # Address collaboration issues
        if orchestration.agent_collaboration_score < 0.6:
            interventions.append("Facilitate agent coordination meetings")
            interventions.append("Review and clarify agent roles and responsibilities")
        
        # Address satisfaction issues
        if orchestration.satisfaction_score < 0.6:
            interventions.append("Conduct stakeholder feedback sessions")
            interventions.append("Adjust project approach based on stakeholder concerns")
        
        # Address stage-specific issues
        blocked_stages = [s for s in journey_stages if s.blockers and len(s.blockers) > 0]
        if blocked_stages:
            interventions.append("Prioritize resolution of identified blockers")
            interventions.append("Escalate critical blockers to project leadership")
        
        # Address timeline issues
        delayed_stages = [
            s for s in journey_stages if s.status == 'active' and s.start_date and s.estimated_duration_days
            and (datetime.utcnow() - s.start_date).days > s.estimated_duration_days
        ]
        if delayed_stages:
            interventions.append("Review and adjust timelines for delayed stages")
            interventions.append("Consider additional resources for critical path activities")
        
        return interventions
    
    def _calculate_completion_percentage(self, journey_stages: List) -> float:
        """Calculate overall completion percentage"""
        
        if not journey_stages:
            return 0.0
        
        total_weight = sum(stage.stage_order for stage in journey_stages)
        completed_weight = sum(
            stage.stage_order * (stage.progress_percentage / 100.0)
            for stage in journey_stages
        )
        
        return (completed_weight / total_weight * 100.0) if total_weight > 0 else 0.0
    
    def _estimate_completion_date(self, journey_stages: List, start_date: datetime) -> Optional[datetime]:
        """Estimate project completion date based on stage progress"""
        
        if not journey_stages or not start_date:
            return None
        
        remaining_stages = [s for s in journey_stages if s.status in ['pending', 'active']]
        if not remaining_stages:
            # All stages completed
            return datetime.utcnow()
        
        # Calculate remaining duration based on estimated durations
        remaining_duration = 0
        for stage in remaining_stages:
            if stage.status == 'active':
                # For active stage, calculate remaining time
                estimated_remaining = (stage.estimated_duration_days or 7) * (1 - stage.progress_percentage / 100.0)
                remaining_duration += estimated_remaining
            else:
                # For pending stages, use full estimated duration
                remaining_duration += stage.estimated_duration_days or 7
        
        return datetime.utcnow() + timedelta(days=remaining_duration)
    
    def _get_touchpoint_weight(self, impact_level: str) -> float:
        """Get weight for touchpoint based on impact level"""
        
        weights = {
            "low": 0.5,
            "medium": 1.0,
            "high": 1.5,
            "critical": 2.0
        }
        
        return weights.get(impact_level, 1.0)