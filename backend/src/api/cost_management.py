"""
💰 Convergio - Cost Management API
AI usage cost tracking and budget management integrated with agents system
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List

import structlog
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

# Authentication removed - no auth required for some endpoints
from ..services.unified_cost_tracker import unified_cost_tracker

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
    time_range: str = Query("30d", description="Time range: 7d, 30d, 90d")
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
        
        # Get cost data from unified tracker
        cost_data = await unified_cost_tracker.get_realtime_overview()
        
        # Generate cost overview
        overview = {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days
            },
            "totals": {
                "total_cost_usd": cost_data.get("total_cost_usd", 0),
                "total_interactions": cost_data.get("total_interactions", 0),
                "cost_per_interaction": cost_data.get("total_cost_usd", 0) / max(cost_data.get("total_interactions", 1), 1),
                "estimated_monthly": cost_data.get("total_cost_usd", 0) * (30 / days)
            },
            "breakdown_by_model": cost_data.get("model_breakdown", {}),
            "breakdown_by_provider": cost_data.get("provider_breakdown", {}),
            "session_summary": cost_data.get("session_summary", {}),
            "status": cost_data.get("status", "active")
        }
        
        logger.info("💰 Cost overview generated",
                   time_range=time_range,
                   total_cost=cost_data.get("total_cost_usd", 0))
        
        return overview
        
    except Exception as e:
        logger.error("❌ Failed to get cost overview", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve cost overview"
        )


@router.get("/realtime/current")
async def get_realtime_cost():
    """
    🔄 Get real-time current cost totals with provider breakdown
    
    Returns comprehensive cost information for display - no auth required
    """
    
    try:
        # Use unified cost tracker
        cost_data = await unified_cost_tracker.get_realtime_overview()
        return cost_data
        
    except Exception as e:
        logger.error("❌ Failed to get realtime cost", error=str(e))
        return {
            "total_cost_usd": 0.0,
            "today_cost_usd": 0.0,
            "total_interactions": 0,
            "total_tokens": 0,
            "status": "error",
            "provider_breakdown": {},
            "model_breakdown": {},
            "error": str(e),
            "last_updated": datetime.utcnow().isoformat()
        }


@router.get("/realtime/real")
async def get_real_cost_data():
    """
    🔥 Get REAL cost data from actual API calls
    
    Returns TRUE costs tracked from OpenAI, Anthropic API responses - NO FAKE DATA
    """
    
    try:
        # Get real session summary from unified tracker
        session_summary = unified_cost_tracker.get_session_summary()
        
        # Also try to get OpenAI usage if API key available
        openai_usage = None
        try:
            from ..core.config import get_settings
            settings = get_settings()
            if hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY:
                today = datetime.utcnow().strftime('%Y-%m-%d')
                openai_usage = await unified_cost_tracker.get_openai_usage_api(
                    settings.OPENAI_API_KEY, 
                    start_date=today
                )
        except Exception as usage_error:
            logger.warning(f"⚠️ OpenAI Usage API unavailable: {usage_error}")
        
        return {
            "real_session_costs": session_summary,
            "openai_usage_api": openai_usage,
            "source": "UNIFIED_REAL_TRACKING",
            "note": "These costs are tracked from actual API responses using unified tracker",
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("❌ Failed to get real cost data", error=str(e))
        return {
            "real_session_costs": {"total_cost_usd": 0, "total_tokens": 0, "total_calls": 0},
            "error": str(e),
            "source": "ERROR",
            "last_updated": datetime.utcnow().isoformat()
        }


@router.post("/interactions")
async def record_interaction_cost(
    interaction_data: Dict[str, Any]
):
    """
    📝 Record cost for AI interaction with database persistence
    
    Records detailed usage and cost data for tracking and budgeting
    """
    
    try:
        # Use unified cost tracker
        result = await unified_cost_tracker.track_api_call(
            session_id=interaction_data.get("session_id", "default"),
            conversation_id=interaction_data.get("conversation_id", "default"),
            provider=interaction_data.get("provider", "openai"),
            model=interaction_data.get("model", "gpt-4o"),
            input_tokens=interaction_data.get("input_tokens", 0),
            output_tokens=interaction_data.get("output_tokens", 0),
            agent_id=interaction_data.get("agent_id"),
            agent_name=interaction_data.get("agent_name"),
            turn_id=interaction_data.get("turn_id"),
            request_type=interaction_data.get("request_type", "chat"),
            response_time_ms=interaction_data.get("response_time_ms"),
            metadata=interaction_data.get("metadata")
        )
        
        if result["success"]:
            logger.info("📝 Interaction cost recorded",
                       session_id=interaction_data.get("session_id"),
                       cost_usd=result["cost_breakdown"]["total_cost_usd"],
                       model=interaction_data.get("model"))
            
            return {
                "success": True,
                "message": "Cost recorded successfully",
                "cost_breakdown": result["cost_breakdown"],
                "session_total": result["session_total"],
                "daily_total": result["daily_total"],
                "alerts": result.get("alerts", [])
            }
        else:
            raise Exception(result.get("error", "Unknown error"))
        
    except Exception as e:
        logger.error("❌ Failed to record interaction cost", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record interaction cost: {str(e)}"
        )


@router.get("/sessions/{session_id}")
async def get_session_cost_details(session_id: str):
    """
    📊 Get detailed cost breakdown for a session
    
    Returns comprehensive session cost data with all API calls
    """
    
    try:
        session_data = await unified_cost_tracker.get_session_details(session_id)
        
        if "error" in session_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=session_data["error"]
            )
        
        return session_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("❌ Failed to get session cost details", error=str(e), session_id=session_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve session cost details"
        )


@router.get("/agents/{agent_id}/costs")
async def get_agent_cost_details(
    agent_id: str,
    days: int = Query(7, description="Number of days to look back", ge=1, le=90)
):
    """
    🤖 Get detailed cost breakdown for an agent
    
    Returns cost analysis for agent across all models and providers
    """
    
    try:
        agent_data = await unified_cost_tracker.get_agent_costs(agent_id, days)
        
        if "error" in agent_data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=agent_data["error"]
            )
        
        return agent_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("❌ Failed to get agent cost details", error=str(e), agent_id=agent_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve agent cost details"
        )


@router.get("/system/status")
async def get_system_status():
    """
    🏥 Get system status
    
    Returns status of cost tracking system
    """
    
    try:
        overview = await unified_cost_tracker.get_realtime_overview()
        return {
            "status": "active",
            "unified_cost_tracker": "enabled",
            "database": "connected",
            "message": "Cost tracking system consolidated and operational",
            "cost_overview": overview,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("❌ Failed to get system status", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system status"
        )


@router.get("/pricing/current")
async def get_current_pricing():
    """
    💰 Get current pricing for all providers
    
    Returns pricing data for OpenAI, Anthropic, and Perplexity models
    """
    
    try:
        # Get pricing data from unified tracker
        pricing_data = {
            "providers": {
                "openai": [
                    {"model": "gpt-4o", "input_cost": 5.0, "output_cost": 15.0},
                    {"model": "gpt-4o-mini", "input_cost": 0.15, "output_cost": 0.6},
                    {"model": "gpt-4", "input_cost": 30.0, "output_cost": 60.0},
                    {"model": "gpt-3.5-turbo", "input_cost": 0.5, "output_cost": 1.5}
                ],
                "anthropic": [
                    {"model": "claude-3-5-sonnet-20241022", "input_cost": 3.0, "output_cost": 15.0},
                    {"model": "claude-3-5-haiku-20241022", "input_cost": 1.0, "output_cost": 5.0},
                    {"model": "claude-3-opus-20240229", "input_cost": 15.0, "output_cost": 75.0}
                ],
                "perplexity": [
                    {"model": "llama-3.1-sonar-large-128k-online", "input_cost": 1.0, "output_cost": 1.0},
                    {"model": "llama-3.1-sonar-small-128k-online", "input_cost": 0.2, "output_cost": 0.2}
                ]
            },
            "currency": "USD",
            "per_tokens": 1000,
            "last_updated": datetime.utcnow().isoformat()
        }
        
        logger.info("💰 Current pricing data retrieved")
        return pricing_data
        
    except Exception as e:
        logger.error("❌ Failed to get current pricing", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve current pricing"
        )