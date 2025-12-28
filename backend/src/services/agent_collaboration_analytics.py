"""
Agent Collaboration Analytics Service
Tracks agent performance, collaboration patterns, and optimization opportunities
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
from uuid import UUID
import structlog

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_async_session
from ..models.project_orchestration import (
    ProjectAgentAssignment, ProjectTouchpoint, ProjectConversation
)

logger = structlog.get_logger()


class AgentCollaborationAnalytics:
    """Analytics for agent collaboration and performance optimization"""
    
    def __init__(self):
        self.performance_weights = {
            "task_completion_rate": 0.25,
            "efficiency_score": 0.20,
            "collaboration_quality": 0.20,
            "cost_efficiency": 0.15,
            "quality_score": 0.15,
            "response_time": 0.05
        }
    
    async def analyze_agent_performance(
        self,
        orchestration_id: UUID,
        analysis_period_days: int = 30,
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """Comprehensive agent performance analysis"""
        
        if db is None:
            async with get_async_session() as db:
                return await self._analyze_performance_impl(orchestration_id, analysis_period_days, db)
        else:
            return await self._analyze_performance_impl(orchestration_id, analysis_period_days, db)
    
    async def _analyze_performance_impl(
        self,
        orchestration_id: UUID,
        analysis_period_days: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Implementation of agent performance analysis"""
        
        # Get agent assignments for the orchestration
        stmt = (
            select(ProjectAgentAssignment)
            .where(and_(
                ProjectAgentAssignment.orchestration_id == orchestration_id,
                ProjectAgentAssignment.active
            ))
        )
        result = await db.execute(stmt)
        assignments = result.scalars().all()
        
        if not assignments:
            return {"message": "No active agent assignments found"}
        
        # Calculate performance metrics for each agent
        agent_performance = {}
        
        for assignment in assignments:
            performance = await self._calculate_individual_performance(assignment, analysis_period_days)
            agent_performance[assignment.agent_name] = performance
        
        # Calculate team-level metrics
        team_metrics = self._calculate_team_metrics(agent_performance)
        
        # Identify top performers and improvement opportunities
        rankings = self._rank_agents(agent_performance)
        recommendations = self._generate_performance_recommendations(agent_performance, rankings)
        
        return {
            "orchestration_id": str(orchestration_id),
            "analysis_period_days": analysis_period_days,
            "agent_performance": agent_performance,
            "team_metrics": team_metrics,
            "rankings": rankings,
            "recommendations": recommendations,
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
    
    async def analyze_collaboration_patterns(
        self,
        orchestration_id: UUID,
        analysis_period_days: int = 30,
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """Analyze collaboration patterns between agents"""
        
        if db is None:
            async with get_async_session() as db:
                return await self._analyze_collaboration_impl(orchestration_id, analysis_period_days, db)
        else:
            return await self._analyze_collaboration_impl(orchestration_id, analysis_period_days, db)
    
    async def _analyze_collaboration_impl(
        self,
        orchestration_id: UUID,
        analysis_period_days: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Implementation of collaboration pattern analysis"""
        
        # Get agent assignments
        assignments_stmt = select(ProjectAgentAssignment).where(
            ProjectAgentAssignment.orchestration_id == orchestration_id
        )
        assignments_result = await db.execute(assignments_stmt)
        assignments = assignments_result.scalars().all()
        
        agent_names = [a.agent_name for a in assignments]
        
        # Get conversations and touchpoints
        conversations_stmt = select(ProjectConversation).where(
            ProjectConversation.orchestration_id == orchestration_id
        )
        conversations_result = await db.execute(conversations_stmt)
        conversations = conversations_result.scalars().all()
        
        touchpoints_stmt = select(ProjectTouchpoint).where(
            ProjectTouchpoint.orchestration_id == orchestration_id
        )
        touchpoints_result = await db.execute(touchpoints_stmt)
        touchpoints = touchpoints_result.scalars().all()
        
        # Build collaboration matrix
        collaboration_matrix = self._build_collaboration_matrix(agent_names, conversations, touchpoints)
        
        # Analyze synergies and conflicts
        synergy_analysis = self._analyze_agent_synergies(collaboration_matrix, assignments)
        conflict_analysis = self._analyze_conflicts(conversations, touchpoints)
        
        # Generate insights
        insights = self._generate_collaboration_insights(collaboration_matrix, synergy_analysis, conflict_analysis)
        
        return {
            "orchestration_id": str(orchestration_id),
            "collaboration_matrix": collaboration_matrix,
            "synergy_analysis": synergy_analysis,
            "conflict_analysis": conflict_analysis,
            "insights": insights,
            "recommendations": self._generate_collaboration_recommendations(insights),
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
    
    async def optimize_agent_assignments(
        self,
        orchestration_id: UUID,
        optimization_goals: List[str] = None,
        constraints: Dict[str, Any] = None,
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """Generate optimized agent assignment recommendations"""
        
        if db is None:
            async with get_async_session() as db:
                return await self._optimize_assignments_impl(orchestration_id, optimization_goals, constraints, db)
        else:
            return await self._optimize_assignments_impl(orchestration_id, optimization_goals, constraints, db)
    
    async def _optimize_assignments_impl(
        self,
        orchestration_id: UUID,
        optimization_goals: Optional[List[str]],
        constraints: Optional[Dict[str, Any]],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Implementation of agent assignment optimization"""
        
        # Get current assignments
        assignments_stmt = select(ProjectAgentAssignment).where(
            and_(
                ProjectAgentAssignment.orchestration_id == orchestration_id,
                ProjectAgentAssignment.active
            )
        )
        assignments_result = await db.execute(assignments_stmt)
        current_assignments = assignments_result.scalars().all()
        
        # Get performance data
        performance_data = await self._analyze_performance_impl(orchestration_id, 30, db)
        
        # Generate optimization recommendations
        optimization_results = self._generate_optimization_recommendations(
            current_assignments=current_assignments,
            performance_data=performance_data,
            optimization_goals=optimization_goals or ["efficiency", "collaboration", "cost"],
            constraints=constraints or {}
        )
        
        return {
            "orchestration_id": str(orchestration_id),
            "optimization_goals": optimization_goals,
            "recommendations": optimization_results,
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
    
    # Helper methods
    
    async def _calculate_individual_performance(
        self,
        assignment: ProjectAgentAssignment,
        period_days: int
    ) -> Dict[str, Any]:
        """Calculate comprehensive performance metrics for individual agent"""
        
        # Task completion metrics
        completion_rate = (
            assignment.tasks_completed / max(assignment.tasks_assigned, 1)
            if assignment.tasks_assigned > 0 else 0
        )
        
        # Cost efficiency
        cost_per_task = (
            assignment.cost_incurred / max(assignment.tasks_completed, 1)
            if assignment.tasks_completed > 0 else 0
        )
        
        # Calculate weighted performance score
        weighted_score = (
            completion_rate * self.performance_weights["task_completion_rate"] +
            assignment.efficiency_score * self.performance_weights["efficiency_score"] +
            assignment.collaboration_score * self.performance_weights["collaboration_quality"] +
            (1 - min(cost_per_task / 100, 1)) * self.performance_weights["cost_efficiency"] +
            assignment.quality_score * self.performance_weights["quality_score"] +
            0.9 * self.performance_weights["response_time"]  # Assume good response time
        )
        
        return {
            "agent_name": assignment.agent_name,
            "role": assignment.agent_role.value,
            "task_completion_rate": completion_rate,
            "efficiency_score": assignment.efficiency_score,
            "collaboration_score": assignment.collaboration_score,
            "quality_score": assignment.quality_score,
            "cost_per_task": cost_per_task,
            "weighted_performance_score": weighted_score,
            "tasks_completed": assignment.tasks_completed,
            "tasks_assigned": assignment.tasks_assigned,
            "total_cost": assignment.cost_incurred
        }
    
    def _calculate_team_metrics(self, agent_performance: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate team-level performance metrics"""
        
        if not agent_performance:
            return {}
        
        agents = list(agent_performance.values())
        
        return {
            "team_size": len(agents),
            "average_efficiency": sum(a["efficiency_score"] for a in agents) / len(agents),
            "average_collaboration": sum(a["collaboration_score"] for a in agents) / len(agents),
            "average_quality": sum(a["quality_score"] for a in agents) / len(agents),
            "total_tasks_completed": sum(a["tasks_completed"] for a in agents),
            "total_cost": sum(a["total_cost"] for a in agents),
            "team_performance_score": sum(a["weighted_performance_score"] for a in agents) / len(agents)
        }
    
    def _rank_agents(self, agent_performance: Dict[str, Any]) -> Dict[str, Any]:
        """Rank agents by various performance criteria"""
        
        if not agent_performance:
            return {}
        
        agents = list(agent_performance.values())
        
        # Sort by different criteria
        by_performance = sorted(agents, key=lambda x: x["weighted_performance_score"], reverse=True)
        by_efficiency = sorted(agents, key=lambda x: x["efficiency_score"], reverse=True)
        by_collaboration = sorted(agents, key=lambda x: x["collaboration_score"], reverse=True)
        
        return {
            "top_performers": [a["agent_name"] for a in by_performance[:3]],
            "most_efficient": [a["agent_name"] for a in by_efficiency[:3]],
            "best_collaborators": [a["agent_name"] for a in by_collaboration[:3]],
            "needs_improvement": [a["agent_name"] for a in by_performance if a["weighted_performance_score"] < 0.6]
        }
    
    def _generate_performance_recommendations(
        self,
        agent_performance: Dict[str, Any],
        rankings: Dict[str, Any]
    ) -> List[str]:
        """Generate actionable performance improvement recommendations"""
        
        recommendations = []
        
        # Identify improvement opportunities
        low_performers = rankings.get("needs_improvement", [])
        if low_performers:
            recommendations.append(f"Focus on coaching for agents: {', '.join(low_performers)}")
        
        # Cost optimization
        agents = list(agent_performance.values())
        high_cost_agents = [a for a in agents if a["cost_per_task"] > 100]
        if high_cost_agents:
            agent_names = [a["agent_name"] for a in high_cost_agents]
            recommendations.append(f"Review cost efficiency for: {', '.join(agent_names)}")
        
        # Task load balancing
        task_counts = [a["tasks_completed"] for a in agents]
        if len(task_counts) > 1 and (max(task_counts) - min(task_counts)) > 10:
            recommendations.append("Consider rebalancing task assignments")
        
        return recommendations
    
    def _build_collaboration_matrix(
        self,
        agent_names: List[str],
        conversations: List,
        touchpoints: List
    ) -> Dict[str, Dict[str, float]]:
        """Build collaboration matrix showing interaction strengths"""
        
        matrix = {}
        for agent1 in agent_names:
            matrix[agent1] = {}
            for agent2 in agent_names:
                if agent1 != agent2:
                    # Calculate collaboration strength based on shared conversations and touchpoints
                    strength = 0.0
                    
                    # Check conversations
                    for conv in conversations:
                        participants = conv.participants or []
                        if agent1 in participants and agent2 in participants:
                            strength += (conv.efficiency_score or 0.5) * 0.7
                    
                    # Check touchpoints
                    for touchpoint in touchpoints:
                        participants = touchpoint.participants or []
                        if agent1 in participants and agent2 in participants:
                            strength += (touchpoint.productivity_score or 0.5) * 0.3
                    
                    matrix[agent1][agent2] = min(strength, 1.0)  # Cap at 1.0
                else:
                    matrix[agent1][agent2] = 0.0
        
        return matrix
    
    def _analyze_agent_synergies(
        self,
        collaboration_matrix: Dict[str, Dict[str, float]],
        assignments: List
    ) -> Dict[str, Any]:
        """Analyze synergies between agent pairs"""
        
        synergies = {}
        agent_performance = {a.agent_name: a.efficiency_score for a in assignments}
        
        for agent1, collaborations in collaboration_matrix.items():
            for agent2, strength in collaborations.items():
                if strength > 0.3:  # Only consider meaningful collaborations
                    individual_performance = (
                        agent_performance.get(agent1, 0.5) + 
                        agent_performance.get(agent2, 0.5)
                    ) / 2
                    
                    synergy_score = strength * individual_performance
                    pair_key = f"{min(agent1, agent2)}-{max(agent1, agent2)}"
                    
                    if pair_key not in synergies:
                        synergies[pair_key] = {
                            "agents": [agent1, agent2],
                            "collaboration_strength": strength,
                            "synergy_score": synergy_score
                        }
        
        top_synergies = sorted(
            synergies.values(),
            key=lambda x: x["synergy_score"],
            reverse=True
        )[:5]
        
        return {
            "all_synergies": synergies,
            "top_synergistic_pairs": top_synergies
        }
    
    def _analyze_conflicts(self, conversations: List, touchpoints: List) -> Dict[str, Any]:
        """Analyze potential conflicts and resolution patterns"""
        
        conflicts = []
        
        # Look for low-quality interactions
        for conv in conversations:
            if (conv.collaboration_quality and conv.collaboration_quality < 0.5):
                conflicts.append({
                    "type": "conversation",
                    "participants": conv.participants,
                    "quality_score": conv.collaboration_quality
                })
        
        for touchpoint in touchpoints:
            if (touchpoint.satisfaction_score and touchpoint.satisfaction_score < 0.4):
                conflicts.append({
                    "type": "touchpoint",
                    "participants": touchpoint.participants,
                    "satisfaction_score": touchpoint.satisfaction_score
                })
        
        return {
            "total_conflicts": len(conflicts),
            "conflict_rate": len(conflicts) / max(len(conversations) + len(touchpoints), 1)
        }
    
    def _generate_collaboration_insights(
        self,
        collaboration_matrix: Dict[str, Dict[str, float]],
        synergy_analysis: Dict[str, Any],
        conflict_analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate actionable collaboration insights"""
        
        insights = []
        
        # Synergy insights
        top_pairs = synergy_analysis.get("top_synergistic_pairs", [])
        if top_pairs:
            best_pair = top_pairs[0]
            insights.append(
                f"Strongest collaboration between {best_pair['agents'][0]} and {best_pair['agents'][1]}"
            )
        
        # Conflict insights
        conflict_rate = conflict_analysis.get("conflict_rate", 0)
        if conflict_rate > 0.2:
            insights.append(f"High conflict rate detected ({conflict_rate:.1%})")
        
        return insights
    
    def _generate_collaboration_recommendations(self, insights: List[str]) -> List[str]:
        """Generate collaboration improvement recommendations"""
        
        recommendations = [
            "Establish clear communication protocols between agents",
            "Monitor collaboration metrics weekly",
            "Implement feedback loops for continuous improvement"
        ]
        
        for insight in insights:
            if "strongest collaboration" in insight.lower():
                recommendations.append("Leverage high-performing pairs for critical tasks")
            elif "conflict rate" in insight.lower():
                recommendations.append("Implement conflict resolution protocols")
        
        return recommendations
    
    def _generate_optimization_recommendations(
        self,
        current_assignments: List,
        performance_data: Dict[str, Any],
        optimization_goals: List[str],
        constraints: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate agent assignment optimization recommendations"""
        
        recommendations = {
            "reassignments": [],
            "role_changes": [],
            "justifications": []
        }
        
        agent_performance = performance_data.get("agent_performance", {})
        
        # Identify underperforming agents
        for assignment in current_assignments:
            performance = agent_performance.get(assignment.agent_name, {})
            
            if performance.get("weighted_performance_score", 0.5) < 0.6:
                recommendations["role_changes"].append({
                    "agent_name": assignment.agent_name,
                    "current_role": assignment.agent_role.value,
                    "suggested_role": "observer",
                    "reason": "Below performance threshold"
                })
                recommendations["justifications"].append(
                    f"Agent {assignment.agent_name} needs performance improvement"
                )
        
        return recommendations


# Global analytics instance
agent_analytics = AgentCollaborationAnalytics()


async def get_agent_analytics() -> AgentCollaborationAnalytics:
    """Get the global agent analytics instance"""
    return agent_analytics