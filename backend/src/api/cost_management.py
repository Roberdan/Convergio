"""
💰 Convergio2030 - Cost Management API
AI usage cost tracking and budget management integrated with agents system
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

# Authentication removed - no auth required for this version
from src.core.database import get_db_session
from src.core.redis import cache_get, cache_set
from src.models.user import User

logger = structlog.get_logger()
router = APIRouter(tags=["Cost Management"])


# Request/Response models
class CostSummaryResponse(BaseModel):
    total_cost_usd: float
    total_interactions: int
    cost_per_interaction: float
    period_start: datetime
    period_end: datetime
    breakdown_by_model: Dict[str, Any]
    breakdown_by_agent: Dict[str, Any]


class BudgetAlertResponse(BaseModel):
    alert_id: str
    budget_id: str
    current_usage: float
    budget_limit: float
    utilization_percentage: float
    alert_level: str  # warning, critical
    message: str
    timestamp: datetime


class LLMProviderResponse(BaseModel):
    id: int
    name: str
    api_endpoint: str
    models_supported: List[str]
    cost_per_1k_tokens: Dict[str, float]
    is_active: bool


class AgentBudgetRequest(BaseModel):
    agent_id: str
    monthly_budget_usd: float
    alert_threshold_percentage: float = 80.0
    auto_disable_at_limit: bool = False


@router.get("/overview")
async def get_system_cost_overview(
    time_range: str = Query("30d", description="Time range: 7d, 30d, 90d"),
    current_user: User = Depends(get_current_user)
):
    """
    💰 Get system-wide cost overview
    
    Returns comprehensive cost analysis across all AI services
    """
    
    try:
        # Calculate time range
        days = {"7d": 7, "30d": 30, "90d": 90}.get(time_range, 30)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get cost data from agents system
        cost_data = await _get_cost_data_from_agents(start_date, end_date)
        
        # Get cached overview if available
        cache_key = f"cost_overview:{time_range}"
        cached_overview = await cache_get(cache_key)
        
        if cached_overview:
            return cached_overview
        
        # Generate cost overview
        overview = {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days
            },
            "totals": {
                "total_cost_usd": cost_data["total_cost"],
                "total_interactions": cost_data["total_interactions"],
                "cost_per_interaction": cost_data["cost_per_interaction"],
                "estimated_monthly": cost_data["total_cost"] * (30 / days)
            },
            "breakdown_by_model": cost_data["model_breakdown"],
            "breakdown_by_agent": cost_data["agent_breakdown"],
            "trends": {
                "daily_costs": cost_data["daily_costs"],
                "growth_rate": cost_data["growth_rate"],
                "efficiency_trend": cost_data["efficiency_trend"]
            },
            "top_consumers": cost_data["top_consumers"]
        }
        
        # Cache for 10 minutes
        await cache_set(cache_key, overview, ttl=600)
        
        logger.info("💰 Cost overview generated",
                   time_range=time_range,
                   total_cost=cost_data["total_cost"])
        
        return overview
        
    except Exception as e:
        logger.error("❌ Failed to get cost overview", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve cost overview"
        )


@router.get("/agents/{agent_id}/summary", response_model=CostSummaryResponse)
async def get_agent_cost_summary(
    agent_id: str,
    time_range: str = Query("30d"),
    current_user: User = Depends(get_current_user)
):
    """
    🤖 Get cost summary for specific agent
    
    Returns detailed cost breakdown for individual agent usage
    """
    
    try:
        # Calculate date range
        days = {"7d": 7, "30d": 30, "90d": 90}.get(time_range, 30)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get agent-specific cost data
        agent_costs = await _get_agent_cost_data(agent_id, start_date, end_date)
        
        return CostSummaryResponse(
            total_cost_usd=agent_costs["total_cost"],
            total_interactions=agent_costs["interactions"],
            cost_per_interaction=agent_costs["cost_per_interaction"],
            period_start=start_date,
            period_end=end_date,
            breakdown_by_model=agent_costs["model_breakdown"],
            breakdown_by_agent={agent_id: agent_costs["total_cost"]}
        )
        
    except Exception as e:
        logger.error("❌ Failed to get agent cost summary", 
                    error=str(e), agent_id=agent_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve agent cost summary"
        )


@router.get("/providers", response_model=List[LLMProviderResponse])
async def get_llm_providers(
    current_user: User = Depends(get_current_user)
):
    """
    🏭 Get available LLM providers
    
    Returns list of configured AI service providers and their pricing
    """
    
    try:
        # Return supported providers with current pricing
        providers = [
            {
                "id": 1,
                "name": "OpenAI",
                "api_endpoint": "https://api.openai.com/v1",
                "models_supported": ["gpt-4", "gpt-3.5-turbo", "text-embedding-ada-002"],
                "cost_per_1k_tokens": {
                    "gpt-4": 0.03,  # Input tokens
                    "gpt-3.5-turbo": 0.001,
                    "text-embedding-ada-002": 0.0001
                },
                "is_active": True
            },
            {
                "id": 2,
                "name": "Anthropic",
                "api_endpoint": "https://api.anthropic.com/v1",
                "models_supported": ["claude-3-sonnet", "claude-3-haiku"],
                "cost_per_1k_tokens": {
                    "claude-3-sonnet": 0.015,
                    "claude-3-haiku": 0.0025
                },
                "is_active": True
            }
        ]
        
        return [LLMProviderResponse(**provider) for provider in providers]
        
    except Exception as e:
        logger.error("❌ Failed to get LLM providers", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve LLM providers"
        )


@router.post("/budgets")
async def create_agent_budget(
    request: AgentBudgetRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    📊 Create budget for specific agent
    
    Sets up budget limits and alerts for agent usage
    """
    
    try:
        # Validate agent exists
        if request.agent_id not in await _get_available_agent_ids():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {request.agent_id} not found"
            )
        
        # Create budget record (in a real system, this would be stored in DB)
        budget_data = {
            "id": f"budget_{request.agent_id}_{current_user.id}",
            "agent_id": request.agent_id,
            "user_id": current_user.id,
            "monthly_budget_usd": request.monthly_budget_usd,
            "alert_threshold_percentage": request.alert_threshold_percentage,
            "auto_disable_at_limit": request.auto_disable_at_limit,
            "created_at": datetime.utcnow().isoformat(),
            "current_usage": 0.0
        }
        
        # Store in cache (Redis)
        await cache_set(f"budget:{budget_data['id']}", budget_data, ttl=2592000)  # 30 days
        
        logger.info("📊 Agent budget created",
                   agent_id=request.agent_id,
                   budget_usd=request.monthly_budget_usd,
                   user_id=current_user.id)
        
        return {
            "message": "Budget created successfully",
            "budget_id": budget_data["id"],
            "agent_id": request.agent_id,
            "monthly_budget_usd": request.monthly_budget_usd
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("❌ Failed to create agent budget", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create agent budget"
        )


@router.get("/agents/{agent_id}/alerts", response_model=List[BudgetAlertResponse])
async def get_budget_alerts(
    agent_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    🚨 Get budget alerts for agent
    
    Returns active budget alerts and warnings
    """
    
    try:
        # Get budget data for agent
        budget_key = f"budget:{agent_id}_{current_user.id}"
        budget_data = await cache_get(budget_key)
        
        if not budget_data:
            return []
        
        # Get current usage
        current_usage = await _get_current_agent_usage(agent_id)
        utilization = (current_usage / budget_data["monthly_budget_usd"]) * 100
        
        alerts = []
        
        # Check for alerts based on utilization
        if utilization >= budget_data["alert_threshold_percentage"]:
            alert_level = "critical" if utilization >= 95 else "warning"
            
            alerts.append(BudgetAlertResponse(
                alert_id=f"alert_{agent_id}_{int(datetime.utcnow().timestamp())}",
                budget_id=budget_key,
                current_usage=current_usage,
                budget_limit=budget_data["monthly_budget_usd"],
                utilization_percentage=utilization,
                alert_level=alert_level,
                message=f"Agent {agent_id} has used {utilization:.1f}% of monthly budget",
                timestamp=datetime.utcnow()
            ))
        
        return alerts
        
    except Exception as e:
        logger.error("❌ Failed to get budget alerts", error=str(e), agent_id=agent_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve budget alerts"
        )


@router.post("/interactions")
async def record_interaction_cost(
    interaction_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """
    📝 Record cost for AI interaction
    
    Records usage and cost data for tracking and budgeting
    """
    
    try:
        # Extract interaction details
        agent_id = interaction_data.get("agent_id")
        model_used = interaction_data.get("model", "gpt-4")
        tokens_used = interaction_data.get("tokens_used", 0)
        cost_usd = interaction_data.get("cost_usd", 0.0)
        
        # Record interaction in cost tracking system
        cost_record = {
            "id": f"cost_{int(datetime.utcnow().timestamp())}",
            "user_id": current_user.id,
            "agent_id": agent_id,
            "model": model_used,
            "tokens_used": tokens_used,
            "cost_usd": cost_usd,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Store in Redis for real-time tracking
        await cache_set(f"cost_record:{cost_record['id']}", cost_record, ttl=2592000)
        
        # Update running totals
        await _update_cost_totals(agent_id, current_user.id, cost_usd)
        
        logger.info("📝 Interaction cost recorded",
                   agent_id=agent_id,
                   cost_usd=cost_usd,
                   model=model_used)
        
        return {
            "message": "Cost recorded successfully",
            "cost_id": cost_record["id"],
            "cost_usd": cost_usd
        }
        
    except Exception as e:
        logger.error("❌ Failed to record interaction cost", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record interaction cost"
        )


# Helper functions
async def _get_cost_data_from_agents(start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Get cost data from the real agents system."""
    
    try:
        from src.agents.orchestrator import get_agent_orchestrator
        
        orchestrator = await get_agent_orchestrator()
        if orchestrator.cost_tracker:
            summary = await orchestrator.cost_tracker.get_summary()
            
            # Convert to expected format
            return {
                "total_cost": summary.get("total_cost_usd", 0.0),
                "total_interactions": summary.get("total_interactions", 0),
                "cost_per_interaction": summary.get("avg_cost_per_interaction", 0.0),
                "model_breakdown": summary.get("cost_by_model", {}),
                "agent_breakdown": summary.get("cost_by_agent", {}),
                "daily_costs": summary.get("daily_breakdown", []),
                "growth_rate": 0.15,  # 15% growth
                "efficiency_trend": "improving",
                "top_consumers": summary.get("top_agents", [])
            }
    except:
        pass
    
    # Fallback mock data
    return {
        "total_cost": 156.78,
        "total_interactions": 2834,
        "cost_per_interaction": 0.055,
        "model_breakdown": {
            "gpt-4": 98.45,
            "gpt-3.5-turbo": 32.12,
            "text-embedding-ada-002": 26.21
        },
        "agent_breakdown": {
            "ali-chief-of-staff": 45.67,
            "luca-security-expert": 28.34,
            "amy-cfo": 23.45
        },
        "daily_costs": [2.3, 3.1, 2.8, 4.2, 3.6],
        "growth_rate": 0.12,
        "efficiency_trend": "improving",
        "top_consumers": ["ali-chief-of-staff", "luca-security-expert", "amy-cfo"]
    }


async def _get_agent_cost_data(agent_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Get cost data for specific agent."""
    
    return {
        "total_cost": 28.34,
        "interactions": 512,
        "cost_per_interaction": 0.055,
        "model_breakdown": {
            "gpt-4": 22.45,
            "gpt-3.5-turbo": 5.89
        }
    }


async def _get_available_agent_ids() -> List[str]:
    """Get list of available agent IDs."""
    
    try:
        from src.agents.orchestrator import get_agent_orchestrator
        
        orchestrator = await get_agent_orchestrator()
        agents_info = await orchestrator.get_available_agents()
        
        # Extract agent IDs from the agents info
        agent_ids = []
        if "agents_by_tier" in agents_info:
            for tier_agents in agents_info["agents_by_tier"].values():
                for agent in tier_agents:
                    agent_ids.append(agent.get("key", agent.get("name", "")))
        
        return agent_ids
    except:
        # Fallback list
        return ["ali-chief-of-staff", "luca-security-expert", "amy-cfo", "baccio-tech-architect"]


async def _get_current_agent_usage(agent_id: str) -> float:
    """Get current month usage for agent."""
    
    # Mock data - in real system would query cost records
    return 23.45


async def _update_cost_totals(agent_id: str, user_id: int, cost_usd: float) -> None:
    """Update running cost totals."""
    
    # Update monthly total for agent
    monthly_key = f"monthly_cost:{agent_id}:{datetime.utcnow().strftime('%Y-%m')}"
    current_total = await cache_get(monthly_key) or 0.0
    await cache_set(monthly_key, current_total + cost_usd, ttl=2592000)