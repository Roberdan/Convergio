"""
Orchestration Cost Tracking Service
Integrates cost tracking with AI orchestration activities for budget management and optimization
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from uuid import UUID
import structlog

from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_async_session
from ..models.project_orchestration import (
    ProjectOrchestration, ProjectAgentAssignment
)
from ..services.unified_cost_tracker import unified_cost_tracker
from ..services.realtime_streaming_service import publish_orchestration_update

logger = structlog.get_logger()


class OrchestrationCostTracker:
    """
    Tracks and manages costs for AI orchestration activities
    Integrates with the existing unified_cost_tracker for comprehensive cost management
    """
    
    def __init__(self):
        self.cost_tracker = unified_cost_tracker
        
        # Cost categories for orchestration
        self.cost_categories = {
            "agent_operations": "AI agent execution and processing",
            "conversation_costs": "Multi-agent conversation costs",
            "optimization_analysis": "Performance optimization analysis",
            "real_time_streaming": "Real-time updates and monitoring",
            "storage_costs": "Data storage for orchestration state",
            "api_calls": "External API calls made by agents"
        }
        
        # Cost optimization thresholds
        self.cost_thresholds = {
            "warning": 0.8,  # 80% of budget
            "critical": 0.95,  # 95% of budget
            "emergency": 1.0   # 100% of budget
        }
    
    async def track_orchestration_costs(
        self,
        orchestration_id: UUID,
        cost_category: str,
        amount: float,
        description: str,
        metadata: Optional[Dict[str, Any]] = None,
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """Track costs for orchestration activities"""
        
        if db is None:
            async with get_async_session() as db:
                return await self._track_costs_impl(orchestration_id, cost_category, amount, description, metadata, db)
        else:
            return await self._track_costs_impl(orchestration_id, cost_category, amount, description, metadata, db)
    
    async def _track_costs_impl(
        self,
        orchestration_id: UUID,
        cost_category: str,
        amount: float,
        description: str,
        metadata: Optional[Dict[str, Any]],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Implementation of cost tracking"""
        
        try:
            # Get orchestration details
            orchestration = await db.get(ProjectOrchestration, orchestration_id)
            if not orchestration:
                raise ValueError(f"Orchestration {orchestration_id} not found")
            
            # Record cost using unified cost tracker
            cost_record = await self.cost_tracker.record_cost(
                provider="orchestration",
                model_name=f"orchestration_{cost_category}",
                cost_amount=amount,
                input_tokens=0,  # Not applicable for orchestration costs
                output_tokens=0,
                conversation_id=str(orchestration_id),
                user_id="system",
                metadata={
                    "orchestration_id": str(orchestration_id),
                    "cost_category": cost_category,
                    "description": description,
                    "project_id": str(orchestration.project_id),
                    **(metadata or {})
                }
            )
            
            # Update orchestration cost tracking
            await self._update_orchestration_costs(orchestration, amount, cost_category, db)
            
            # Check budget thresholds
            budget_status = await self._check_budget_thresholds(orchestration, db)
            
            # Publish real-time cost update
            await publish_orchestration_update(
                orchestration_id=str(orchestration_id),
                update_type="cost_update",
                data={
                    "cost_category": cost_category,
                    "amount": amount,
                    "description": description,
                    "total_cost": orchestration.cost_per_deliverable * max(orchestration.touchpoint_count, 1),
                    "budget_status": budget_status
                }
            )
            
            logger.info("Orchestration cost tracked",
                       orchestration_id=str(orchestration_id),
                       cost_category=cost_category,
                       amount=amount)
            
            return {
                "success": True,
                "cost_record_id": cost_record.get("id") if cost_record else None,
                "orchestration_id": str(orchestration_id),
                "cost_category": cost_category,
                "amount": amount,
                "total_orchestration_cost": orchestration.cost_per_deliverable * max(orchestration.touchpoint_count, 1),
                "budget_status": budget_status,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Failed to track orchestration cost", 
                        error=str(e), 
                        orchestration_id=str(orchestration_id))
            raise
    
    async def get_orchestration_cost_summary(
        self,
        orchestration_id: UUID,
        period_days: int = 30,
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """Get comprehensive cost summary for orchestration"""
        
        if db is None:
            async with get_async_session() as db:
                return await self._get_cost_summary_impl(orchestration_id, period_days, db)
        else:
            return await self._get_cost_summary_impl(orchestration_id, period_days, db)
    
    async def _get_cost_summary_impl(
        self,
        orchestration_id: UUID,
        period_days: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Implementation of cost summary retrieval"""
        
        # Get orchestration details
        orchestration = await db.get(ProjectOrchestration, orchestration_id)
        if not orchestration:
            raise ValueError(f"Orchestration {orchestration_id} not found")
        
        # Get costs from unified cost tracker
        since_date = datetime.utcnow() - timedelta(days=period_days)
        
        try:
            cost_records = await self.cost_tracker.get_costs_by_conversation(
                conversation_id=str(orchestration_id),
                since=since_date
            )
        except Exception as e:
            logger.warning("Failed to get costs from unified tracker", error=str(e))
            cost_records = []
        
        # Analyze costs by category
        cost_by_category = {}
        total_cost = 0.0
        
        for record in cost_records:
            metadata = record.get("metadata", {})
            category = metadata.get("cost_category", "unknown")
            amount = record.get("cost_amount", 0.0)
            
            if category not in cost_by_category:
                cost_by_category[category] = {
                    "total": 0.0,
                    "count": 0,
                    "average": 0.0,
                    "description": self.cost_categories.get(category, "Unknown category")
                }
            
            cost_by_category[category]["total"] += amount
            cost_by_category[category]["count"] += 1
            total_cost += amount
        
        # Calculate averages
        for category_data in cost_by_category.values():
            category_data["average"] = category_data["total"] / max(category_data["count"], 1)
        
        # Get agent-specific costs
        agent_costs = await self._get_agent_costs(orchestration_id, db)
        
        # Calculate cost efficiency metrics
        efficiency_metrics = await self._calculate_cost_efficiency(orchestration, total_cost, db)
        
        # Budget analysis
        budget_analysis = await self._analyze_budget_status(orchestration, total_cost)
        
        return {
            "orchestration_id": str(orchestration_id),
            "period_days": period_days,
            "total_cost": total_cost,
            "cost_by_category": cost_by_category,
            "agent_costs": agent_costs,
            "efficiency_metrics": efficiency_metrics,
            "budget_analysis": budget_analysis,
            "cost_trends": await self._calculate_cost_trends(cost_records),
            "optimization_opportunities": await self._identify_cost_optimizations(cost_by_category, agent_costs),
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
    
    async def optimize_costs(
        self,
        orchestration_id: UUID,
        optimization_targets: List[str] = None,
        constraints: Dict[str, Any] = None,
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """Generate cost optimization recommendations"""
        
        if db is None:
            async with get_async_session() as db:
                return await self._optimize_costs_impl(orchestration_id, optimization_targets, constraints, db)
        else:
            return await self._optimize_costs_impl(orchestration_id, optimization_targets, constraints, db)
    
    async def _optimize_costs_impl(
        self,
        orchestration_id: UUID,
        optimization_targets: Optional[List[str]],
        constraints: Optional[Dict[str, Any]],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Implementation of cost optimization"""
        
        # Get comprehensive cost summary
        cost_summary = await self._get_cost_summary_impl(orchestration_id, 30, db)
        
        # Analyze optimization opportunities
        optimizations = []
        potential_savings = 0.0
        
        # Agent cost optimization
        agent_costs = cost_summary.get("agent_costs", {})
        high_cost_agents = [
            agent for agent, data in agent_costs.items()
            if data.get("cost_per_task", 0) > 50  # $50 per task threshold
        ]
        
        if high_cost_agents:
            optimizations.append({
                "type": "agent_optimization",
                "target": high_cost_agents,
                "description": f"Optimize high-cost agents: {', '.join(high_cost_agents)}",
                "potential_savings": sum(agent_costs[agent]["total_cost"] * 0.2 for agent in high_cost_agents),
                "implementation": "Review agent assignments and efficiency"
            })
            potential_savings += sum(agent_costs[agent]["total_cost"] * 0.2 for agent in high_cost_agents)
        
        # Category-based optimization
        cost_by_category = cost_summary.get("cost_by_category", {})
        high_cost_categories = [
            category for category, data in cost_by_category.items()
            if data.get("total", 0) > cost_summary.get("total_cost", 0) * 0.3  # >30% of total
        ]
        
        if high_cost_categories:
            optimizations.append({
                "type": "category_optimization",
                "target": high_cost_categories,
                "description": f"Optimize high-cost categories: {', '.join(high_cost_categories)}",
                "potential_savings": sum(cost_by_category[cat]["total"] * 0.15 for cat in high_cost_categories),
                "implementation": "Review and optimize processes in these categories"
            })
            potential_savings += sum(cost_by_category[cat]["total"] * 0.15 for cat in high_cost_categories)
        
        # Frequency-based optimization
        conversation_frequency = len(cost_summary.get("cost_trends", {}).get("daily_costs", []))
        if conversation_frequency > 10:  # More than 10 cost events per day
            optimizations.append({
                "type": "frequency_optimization",
                "target": "conversation_frequency",
                "description": "Reduce excessive conversation frequency",
                "potential_savings": cost_summary.get("total_cost", 0) * 0.1,
                "implementation": "Implement smarter conversation batching"
            })
            potential_savings += cost_summary.get("total_cost", 0) * 0.1
        
        return {
            "orchestration_id": str(orchestration_id),
            "optimization_targets": optimization_targets or ["all"],
            "current_total_cost": cost_summary.get("total_cost", 0),
            "optimization_opportunities": optimizations,
            "total_potential_savings": potential_savings,
            "savings_percentage": (potential_savings / max(cost_summary.get("total_cost", 1), 1)) * 100,
            "implementation_priority": self._prioritize_optimizations(optimizations),
            "constraints": constraints or {},
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
    
    async def set_budget_alerts(
        self,
        orchestration_id: UUID,
        budget_limit: float,
        alert_thresholds: Dict[str, float] = None,
        notification_settings: Dict[str, Any] = None,
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """Set up budget alerts for orchestration"""
        
        if db is None:
            async with get_async_session() as db:
                return await self._set_budget_alerts_impl(orchestration_id, budget_limit, alert_thresholds, notification_settings, db)
        else:
            return await self._set_budget_alerts_impl(orchestration_id, budget_limit, alert_thresholds, notification_settings, db)
    
    async def _set_budget_alerts_impl(
        self,
        orchestration_id: UUID,
        budget_limit: float,
        alert_thresholds: Optional[Dict[str, float]],
        notification_settings: Optional[Dict[str, Any]],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Implementation of budget alert setup"""
        
        # Get or create orchestration
        orchestration = await db.get(ProjectOrchestration, orchestration_id)
        if not orchestration:
            raise ValueError(f"Orchestration {orchestration_id} not found")
        
        # Update orchestration config with budget settings
        config = orchestration.orchestration_config or {}
        config["budget_settings"] = {
            "budget_limit": budget_limit,
            "alert_thresholds": alert_thresholds or self.cost_thresholds,
            "notification_settings": notification_settings or {"enabled": True, "channels": ["real_time"]},
            "created_at": datetime.utcnow().isoformat()
        }
        
        orchestration.orchestration_config = config
        await db.commit()
        
        logger.info("Budget alerts configured",
                   orchestration_id=str(orchestration_id),
                   budget_limit=budget_limit)
        
        return {
            "success": True,
            "orchestration_id": str(orchestration_id),
            "budget_limit": budget_limit,
            "alert_thresholds": alert_thresholds or self.cost_thresholds,
            "notification_settings": notification_settings or {"enabled": True},
            "timestamp": datetime.utcnow().isoformat()
        }
    
    # Helper methods
    
    async def _update_orchestration_costs(
        self,
        orchestration: ProjectOrchestration,
        amount: float,
        category: str,
        db: AsyncSession
    ):
        """Update orchestration cost fields"""
        
        # Update cost per deliverable (simplified calculation)
        deliverable_count = max(orchestration.touchpoint_count, 1)
        current_total = orchestration.cost_per_deliverable * deliverable_count
        new_total = current_total + amount
        orchestration.cost_per_deliverable = new_total / deliverable_count
        
        await db.commit()
    
    async def _check_budget_thresholds(
        self,
        orchestration: ProjectOrchestration,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Check if orchestration is approaching budget limits"""
        
        config = orchestration.orchestration_config or {}
        budget_settings = config.get("budget_settings", {})
        budget_limit = budget_settings.get("budget_limit")
        
        if not budget_limit:
            return {"status": "no_budget_set"}
        
        current_cost = orchestration.cost_per_deliverable * max(orchestration.touchpoint_count, 1)
        usage_percentage = current_cost / budget_limit
        
        thresholds = budget_settings.get("alert_thresholds", self.cost_thresholds)
        
        if usage_percentage >= thresholds.get("emergency", 1.0):
            status = "emergency"
        elif usage_percentage >= thresholds.get("critical", 0.95):
            status = "critical"
        elif usage_percentage >= thresholds.get("warning", 0.8):
            status = "warning"
        else:
            status = "normal"
        
        return {
            "status": status,
            "budget_limit": budget_limit,
            "current_cost": current_cost,
            "usage_percentage": usage_percentage,
            "remaining_budget": budget_limit - current_cost
        }
    
    async def _get_agent_costs(
        self,
        orchestration_id: UUID,
        db: AsyncSession
    ) -> Dict[str, Dict[str, Any]]:
        """Get cost breakdown by agent"""
        
        # Get agent assignments
        stmt = select(ProjectAgentAssignment).where(
            ProjectAgentAssignment.orchestration_id == orchestration_id
        )
        result = await db.execute(stmt)
        assignments = result.scalars().all()
        
        agent_costs = {}
        
        for assignment in assignments:
            tasks_completed = max(assignment.tasks_completed, 1)
            agent_costs[assignment.agent_name] = {
                "total_cost": assignment.cost_incurred,
                "cost_per_task": assignment.cost_incurred / tasks_completed,
                "tasks_completed": assignment.tasks_completed,
                "efficiency_score": assignment.efficiency_score,
                "cost_efficiency_score": 1 - min(assignment.cost_incurred / (tasks_completed * 100), 1)
            }
        
        return agent_costs
    
    async def _calculate_cost_efficiency(
        self,
        orchestration: ProjectOrchestration,
        total_cost: float,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Calculate cost efficiency metrics"""
        
        # Get journey stages to calculate deliverable efficiency
        stmt = select(func.count()).select_from(
            db.query(ProjectOrchestration).join("journey_stages").filter(
                ProjectOrchestration.id == orchestration.id
            ).filter(text("status = 'completed'"))
        )
        
        try:
            completed_stages = await db.scalar(stmt) or 0
        except Exception:
            completed_stages = 0
        
        total_stages = 6  # Default journey stages
        
        return {
            "cost_per_stage": total_cost / max(completed_stages, 1),
            "cost_per_touchpoint": total_cost / max(orchestration.touchpoint_count, 1),
            "efficiency_ratio": orchestration.ai_efficiency_score / max(total_cost / 1000, 0.1),  # Per $1000
            "completion_efficiency": completed_stages / total_stages if total_stages > 0 else 0,
            "budget_efficiency": 1 - min(total_cost / 10000, 1)  # Assuming $10k reference
        }
    
    async def _analyze_budget_status(
        self,
        orchestration: ProjectOrchestration,
        total_cost: float
    ) -> Dict[str, Any]:
        """Analyze current budget status"""
        
        config = orchestration.orchestration_config or {}
        budget_settings = config.get("budget_settings", {})
        budget_limit = budget_settings.get("budget_limit", 0)
        
        if budget_limit == 0:
            return {
                "status": "no_budget_set",
                "message": "No budget limit configured"
            }
        
        usage_percentage = total_cost / budget_limit
        remaining = budget_limit - total_cost
        
        return {
            "status": "within_budget" if usage_percentage < 1.0 else "over_budget",
            "budget_limit": budget_limit,
            "total_spent": total_cost,
            "remaining_budget": remaining,
            "usage_percentage": usage_percentage,
            "days_remaining_at_current_rate": max(remaining / max(total_cost / 30, 1), 0) if remaining > 0 else 0
        }
    
    async def _calculate_cost_trends(self, cost_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate cost trends and patterns"""
        
        if not cost_records:
            return {"message": "No cost records available"}
        
        # Group by day
        daily_costs = {}
        for record in cost_records:
            date_key = record.get("created_at", "").split("T")[0]  # Get date part
            if date_key:
                daily_costs[date_key] = daily_costs.get(date_key, 0) + record.get("cost_amount", 0)
        
        # Calculate trend
        costs_list = list(daily_costs.values())
        if len(costs_list) > 1:
            recent_avg = sum(costs_list[-7:]) / min(len(costs_list), 7)  # Last 7 days
            overall_avg = sum(costs_list) / len(costs_list)
            trend = "increasing" if recent_avg > overall_avg * 1.1 else "decreasing" if recent_avg < overall_avg * 0.9 else "stable"
        else:
            trend = "insufficient_data"
        
        return {
            "daily_costs": daily_costs,
            "trend": trend,
            "average_daily_cost": sum(costs_list) / max(len(costs_list), 1),
            "peak_cost_day": max(daily_costs.items(), key=lambda x: x[1]) if daily_costs else None
        }
    
    async def _identify_cost_optimizations(
        self,
        cost_by_category: Dict[str, Any],
        agent_costs: Dict[str, Any]
    ) -> List[str]:
        """Identify specific cost optimization opportunities"""
        
        optimizations = []
        
        # Category-based optimizations
        if cost_by_category:
            highest_category = max(cost_by_category.items(), key=lambda x: x[1].get("total", 0))
            if highest_category[1].get("total", 0) > 100:  # $100 threshold
                optimizations.append(f"Focus on reducing {highest_category[0]} costs (${highest_category[1]['total']:.2f})")
        
        # Agent-based optimizations
        if agent_costs:
            inefficient_agents = [
                agent for agent, data in agent_costs.items()
                if data.get("cost_efficiency_score", 1) < 0.6
            ]
            if inefficient_agents:
                optimizations.append(f"Improve cost efficiency for agents: {', '.join(inefficient_agents)}")
        
        return optimizations
    
    def _prioritize_optimizations(self, optimizations: List[Dict[str, Any]]) -> List[str]:
        """Prioritize optimization opportunities by potential impact"""
        
        # Sort by potential savings
        sorted_optimizations = sorted(
            optimizations,
            key=lambda x: x.get("potential_savings", 0),
            reverse=True
        )
        
        return [opt["type"] for opt in sorted_optimizations]


# Global cost tracker instance
orchestration_cost_tracker = OrchestrationCostTracker()


async def get_orchestration_cost_tracker() -> OrchestrationCostTracker:
    """Get the global orchestration cost tracker instance"""
    return orchestration_cost_tracker


# Helper functions for easy integration
async def track_agent_cost(orchestration_id: UUID, agent_name: str, amount: float, description: str):
    """Helper to track agent-specific costs"""
    tracker = await get_orchestration_cost_tracker()
    return await tracker.track_orchestration_costs(
        orchestration_id=orchestration_id,
        cost_category="agent_operations",
        amount=amount,
        description=description,
        metadata={"agent_name": agent_name}
    )


async def track_conversation_cost(orchestration_id: UUID, conversation_id: str, amount: float):
    """Helper to track conversation costs"""
    tracker = await get_orchestration_cost_tracker()
    return await tracker.track_orchestration_costs(
        orchestration_id=orchestration_id,
        cost_category="conversation_costs",
        amount=amount,
        description=f"Multi-agent conversation {conversation_id}",
        metadata={"conversation_id": conversation_id}
    )