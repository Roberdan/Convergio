"""
🔥 UNIFIED COST TRACKER - Consolidated Cost Tracking System
Consolidates all cost tracking functionality into one clean, efficient system.

Replaces:
- agents/services/cost_tracker.py
- services/cost_tracking_service.py  
- services/real_cost_tracker.py
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

import httpx
import structlog
# Use absolute imports so pytest with python_paths=backend/src can import correctly
from src.agents.utils.config import get_settings
from sqlalchemy import and_, func, select

from src.agents.services.redis_state_manager import RedisStateManager
from src.core.database import get_async_session, get_async_read_session
from src.models.cost_tracking import (
    CostTracking
)

logger = structlog.get_logger()


@dataclass
class RealCostResult:
    """Result from real API cost tracking"""
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_usd: float
    request_id: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class CostBreakdown:
    """Structured cost breakdown"""
    total_cost_usd: float
    input_cost_usd: float
    output_cost_usd: float
    input_tokens: int
    output_tokens: int
    total_tokens: int
    provider: str
    model: str
    currency: str = "USD"


class UnifiedCostTracker:
    """
    🔥 UNIFIED COST TRACKER
    
    Single, consolidated cost tracking system that handles:
    - Real-time API cost tracking from actual responses
    - Database persistence for historical data
    - Redis caching for performance
    - Multi-provider support (OpenAI, Anthropic, Perplexity)
    - Session and daily cost summaries
    """
    
    def __init__(self, redis_manager: Optional[RedisStateManager] = None):
        self.redis_manager = redis_manager
        self.session_costs: List[RealCostResult] = []
        
        # Real pricing from August 2025 (per 1k tokens)
        self.pricing = {
            "openai": {
                "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
                "gpt-4o": {"input": 0.005, "output": 0.015},
                "gpt-4": {"input": 0.03, "output": 0.06},
                "gpt-4-turbo": {"input": 0.01, "output": 0.03},
                "gpt-3.5-turbo": {"input": 0.001, "output": 0.002},
                "text-embedding-ada-002": {"input": 0.0001, "output": 0},
                "text-embedding-3-small": {"input": 0.00002, "output": 0},
                "text-embedding-3-large": {"input": 0.00013, "output": 0}
            },
            "anthropic": {
                "claude-3-5-sonnet": {"input": 0.003, "output": 0.015},
                "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
                "claude-3-opus": {"input": 0.015, "output": 0.075}
            },
            "perplexity": {
                "llama-3.1-sonar-small-128k-online": {"input": 0.0002, "output": 0.0002},
                "llama-3.1-sonar-large-128k-online": {"input": 0.001, "output": 0.001}
            }
        }
        
        # Cache keys
        self.cache_prefix = "unified_cost:"
    
    def _get_pricing(self, provider: str, model: str) -> Dict[str, float]:
        """Get pricing for provider/model combination"""
        provider_pricing = self.pricing.get(provider.lower(), {})
        
        # Try exact model match first
        if model in provider_pricing:
            return provider_pricing[model]
        
        # Try partial matches for model variants
        for pricing_model, pricing in provider_pricing.items():
            if model.startswith(pricing_model) or pricing_model in model:
                return pricing
        
        # Fallback to default pricing
        if provider.lower() == "openai":
            return self.pricing["openai"]["gpt-4o-mini"]
        elif provider.lower() == "anthropic":
            return self.pricing["anthropic"]["claude-3-haiku"]
        else:
            return {"input": 0.001, "output": 0.002}  # Generic fallback
    
    def calculate_cost(self, provider: str, model: str, input_tokens: int, output_tokens: int) -> CostBreakdown:
        """Calculate cost breakdown for API call"""
        pricing = self._get_pricing(provider, model)
        
        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]
        total_cost = input_cost + output_cost
        
        return CostBreakdown(
            total_cost_usd=total_cost,
            input_cost_usd=input_cost,
            output_cost_usd=output_cost,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            provider=provider,
            model=model
        )
    
    async def track_api_call(
        self,
        session_id: str,
        conversation_id: str,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        agent_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        turn_id: Optional[str] = None,
        request_type: str = "chat",
        response_time_ms: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Track a real API call with database persistence
        
        This is the main entry point for tracking costs from actual API responses
        """
        try:
            # Calculate cost breakdown
            cost_breakdown = self.calculate_cost(provider, model, input_tokens, output_tokens)
            
            # Create real cost result for session tracking
            result = RealCostResult(
                provider=provider,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                cost_usd=cost_breakdown.total_cost_usd
            )
            
            # Add to session costs
            self.session_costs.append(result)
            
            # Persist to database
            async with get_async_session() as db:
                cost_record = CostTracking(
                    session_id=session_id,
                    conversation_id=conversation_id,
                    provider=provider,
                    model=model,
                    agent_id=agent_id,
                    agent_name=agent_name,
                    turn_id=turn_id,
                    request_type=request_type,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    total_tokens=input_tokens + output_tokens,
                    input_cost_usd=cost_breakdown.input_cost_usd,
                    output_cost_usd=cost_breakdown.output_cost_usd,
                    total_cost_usd=cost_breakdown.total_cost_usd,
                    response_time_ms=response_time_ms,
                    request_metadata=metadata or {},
                    created_at=datetime.utcnow()
                )
                
                db.add(cost_record)
                await db.commit()
                
                logger.info(
                    f"💰 Cost tracked: ${cost_breakdown.total_cost_usd:.4f}",
                    provider=provider,
                    model=model,
                    tokens=input_tokens + output_tokens,
                    session_id=session_id
                )
            
            # Update cache totals
            await self._update_cache_totals(cost_breakdown.total_cost_usd, session_id)
            
            # Get session and daily totals
            session_total = await self._get_session_total(session_id)
            daily_total = await self._get_daily_total()
            
            return {
                "success": True,
                "cost_breakdown": {
                    "total_cost_usd": cost_breakdown.total_cost_usd,
                    "input_cost_usd": cost_breakdown.input_cost_usd,
                    "output_cost_usd": cost_breakdown.output_cost_usd,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": input_tokens + output_tokens,
                    "provider": provider,
                    "model": model,
                    "currency": "USD"
                },
                "session_total": session_total,
                "daily_total": daily_total
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to track API call: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def track_openai_response(self, model: str, response: Any) -> Optional[RealCostResult]:
        """Track cost from OpenAI API response object"""
        try:
            # Extract usage from OpenAI response
            usage = response.usage if hasattr(response, 'usage') else None
            
            if usage:
                input_tokens = usage.prompt_tokens
                output_tokens = usage.completion_tokens
                cost_breakdown = self.calculate_cost("openai", model, input_tokens, output_tokens)
                
                result = RealCostResult(
                    provider="openai",
                    model=model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    total_tokens=input_tokens + output_tokens,
                    cost_usd=cost_breakdown.total_cost_usd,
                    request_id=getattr(response, 'id', None)
                )
                
                self.session_costs.append(result)
                logger.info(f"💰 OpenAI cost tracked: ${cost_breakdown.total_cost_usd:.4f} ({model}, {input_tokens + output_tokens} tokens)")
                return result
            else:
                logger.warning("⚠️ No usage data in OpenAI response")
                return None
                
        except Exception as e:
            logger.error(f"❌ Failed to track OpenAI cost: {e}")
            return None
    
    async def track_anthropic_response(self, model: str, response: Any) -> Optional[RealCostResult]:
        """Track cost from Anthropic API response object"""
        try:
            # Extract usage from Anthropic response
            usage = response.usage if hasattr(response, 'usage') else None
            
            if usage:
                input_tokens = usage.input_tokens
                output_tokens = usage.output_tokens
                cost_breakdown = self.calculate_cost("anthropic", model, input_tokens, output_tokens)
                
                result = RealCostResult(
                    provider="anthropic",
                    model=model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    total_tokens=input_tokens + output_tokens,
                    cost_usd=cost_breakdown.total_cost_usd,
                    request_id=getattr(response, 'id', None)
                )
                
                self.session_costs.append(result)
                logger.info(f"💰 Anthropic cost tracked: ${cost_breakdown.total_cost_usd:.4f} ({model}, {input_tokens + output_tokens} tokens)")
                return result
            else:
                logger.warning("⚠️ No usage data in Anthropic response")
                return None
                
        except Exception as e:
            logger.error(f"❌ Failed to track Anthropic cost: {e}")
            return None
    
    async def get_openai_usage_api(self, api_key: str, start_date: str = None) -> Optional[Dict[str, Any]]:
        """Get REAL usage data from OpenAI Usage API"""
        try:
            url = "https://api.openai.com/v1/usage"
            
            params = {}
            if start_date:
                params["start_date"] = start_date
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(url, headers=headers, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info("✅ Retrieved real OpenAI usage data")
                    return data
                else:
                    logger.warning(f"⚠️ OpenAI usage API returned {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Failed to get OpenAI usage: {e}")
            return None
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current session costs"""
        if not self.session_costs:
            return {"total_cost_usd": 0, "total_tokens": 0, "calls": 0}
        
        total_cost = sum(c.cost_usd for c in self.session_costs)
        total_tokens = sum(c.total_tokens for c in self.session_costs)
        
        by_provider = {}
        by_model = {}
        
        for cost in self.session_costs:
            # By provider
            if cost.provider not in by_provider:
                by_provider[cost.provider] = {"cost": 0, "tokens": 0, "calls": 0}
            by_provider[cost.provider]["cost"] += cost.cost_usd
            by_provider[cost.provider]["tokens"] += cost.total_tokens
            by_provider[cost.provider]["calls"] += 1
            
            # By model
            if cost.model not in by_model:
                by_model[cost.model] = {"cost": 0, "tokens": 0, "calls": 0}
            by_model[cost.model]["cost"] += cost.cost_usd
            by_model[cost.model]["tokens"] += cost.total_tokens
            by_model[cost.model]["calls"] += 1
        
        return {
            "total_cost_usd": round(total_cost, 4),
            "total_tokens": total_tokens,
            "total_calls": len(self.session_costs),
            "by_provider": by_provider,
            "by_model": by_model,
            "session_start": min(c.timestamp for c in self.session_costs) if self.session_costs else None,
            "last_updated": datetime.utcnow()
        }
    
    def clear_session(self):
        """Clear current session costs"""
        self.session_costs.clear()
        logger.info("🧹 Session costs cleared")
    
    async def get_realtime_overview(self) -> Dict[str, Any]:
        """Get REAL-time cost overview with DATABASE TOTALS + CURRENT SESSION DETAIL"""
        try:
            # Check if database is initialized
            from core.database import get_async_read_session_factory
            from core.database import init_db
            await init_db()
            async_read_session_factory = get_async_read_session_factory()
            if async_read_session_factory is None:
                logger.warning("⚠️ Database not initialized yet, returning empty overview")
                return {
                    "total_cost_usd": 0.0,
                    "today_cost_usd": 0.0,
                    "total_interactions": 0,
                    "total_tokens": 0,
                    "budget_utilization": 0.0,
                    "daily_budget_usd": 50.0,
                    "status": "initializing",
                    "service_breakdown": {},
                    "provider_breakdown": {},
                    "model_breakdown": {},
                    "service_details": {},
                    "model_details": {},
                    "session_summary": {"total_cost_usd": 0, "total_tokens": 0, "total_calls": 0},
                    "last_updated": datetime.utcnow().isoformat()
                }

            async with get_async_read_session() as db:
                # 1. GET TOTAL HISTORIC COSTS FROM DATABASE (ALL TIME)
                total_query = select(
                    func.sum(CostTracking.total_cost_usd).label('total_cost'),
                    func.sum(CostTracking.total_tokens).label('total_tokens'),
                    func.count(CostTracking.id).label('total_calls')
                )
                total_result = await db.execute(total_query)
                totals = total_result.first()
                
                total_historic_cost = float(totals.total_cost or 0)
                total_historic_tokens = int(totals.total_tokens or 0)  
                total_historic_calls = int(totals.total_calls or 0)
                
                # 2. GET TODAY'S COSTS FROM DATABASE
                today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                today_query = select(
                    func.sum(CostTracking.total_cost_usd).label('today_cost'),
                    func.sum(CostTracking.total_tokens).label('today_tokens'),
                    func.count(CostTracking.id).label('today_calls')
                ).where(CostTracking.created_at >= today_start)
                
                today_result = await db.execute(today_query)
                today_totals = today_result.first()
                
                today_historic_cost = float(today_totals.today_cost or 0)
                today_historic_tokens = int(today_totals.today_tokens or 0)
                today_historic_calls = int(today_totals.today_calls or 0)
                
                # 3. GET SERVICE BREAKDOWN FROM DATABASE (TODAY)
                service_query = select(
                    CostTracking.provider,
                    func.sum(CostTracking.total_cost_usd).label('provider_cost'),
                    func.sum(CostTracking.total_tokens).label('provider_tokens'),
                    func.count(CostTracking.id).label('provider_calls')
                ).where(
                    CostTracking.created_at >= today_start
                ).group_by(CostTracking.provider)
                
                service_result = await db.execute(service_query)
                service_breakdown = {}
                
                for row in service_result:
                    service_breakdown[row.provider] = {
                        "cost_usd": float(row.provider_cost),
                        "tokens": int(row.provider_tokens), 
                        "calls": int(row.provider_calls),
                        "avg_cost_per_call": float(row.provider_cost) / int(row.provider_calls) if int(row.provider_calls) > 0 else 0
                    }
                
                # 4. GET MODEL BREAKDOWN FROM DATABASE (TODAY)
                model_query = select(
                    CostTracking.model,
                    CostTracking.provider,
                    func.sum(CostTracking.total_cost_usd).label('model_cost'),
                    func.sum(CostTracking.total_tokens).label('model_tokens'),
                    func.count(CostTracking.id).label('model_calls')
                ).where(
                    CostTracking.created_at >= today_start
                ).group_by(CostTracking.model, CostTracking.provider)
                
                model_result = await db.execute(model_query)
                model_breakdown = {}
                
                for row in model_result:
                    model_key = f"{row.provider}/{row.model}"
                    model_breakdown[model_key] = {
                        "cost_usd": float(row.model_cost),
                        "tokens": int(row.model_tokens),
                        "calls": int(row.model_calls),
                        "provider": row.provider
                    }
            
            # 5. GET CURRENT SESSION SUMMARY
            session_summary = self.get_session_summary()
            
            # 6. CALCULATE BUDGET UTILIZATION
            daily_budget = getattr(get_settings(), 'DAILY_BUDGET_USD', 50.0)  # Default $50/day
            budget_utilization = (today_historic_cost / daily_budget) * 100 if daily_budget > 0 else 0.0
            
            # 7. COMBINE ALL DATA FOR COMPREHENSIVE OVERVIEW
            return {
                # TOTALS FROM DATABASE (ALL TIME)
                "total_cost_usd": total_historic_cost,
                "total_tokens": total_historic_tokens,
                "total_interactions": total_historic_calls,
                
                # TODAY FROM DATABASE  
                "today_cost_usd": today_historic_cost,
                "today_tokens": today_historic_tokens,
                "today_interactions": today_historic_calls,
                
                # BUDGET INFORMATION
                "budget_utilization": budget_utilization,
                "daily_budget_usd": daily_budget,
                
                # SERVICE BREAKDOWN (TODAY FROM DATABASE)
                "service_breakdown": service_breakdown,
                "provider_breakdown": {k: v["cost_usd"] for k, v in service_breakdown.items()},
                "model_breakdown": {k: v["cost_usd"] for k, v in model_breakdown.items()},
                
                # DETAILED SERVICE INFO 
                "service_details": service_breakdown,
                "model_details": model_breakdown,
                
                # CURRENT SESSION (IN-MEMORY)
                "session_summary": session_summary,
                
                "status": "active",
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get realtime overview: {e}")
            return {
                "total_cost_usd": 0.0,
                "today_cost_usd": 0.0,
                "total_interactions": 0,
                "total_tokens": 0,
                "budget_utilization": 0.0,
                "daily_budget_usd": 50.0,
                "status": "error",
                "error": str(e),
                "service_breakdown": {},
                "provider_breakdown": {},
                "model_breakdown": {},
                "session_summary": {"total_cost_usd": 0, "total_tokens": 0, "total_calls": 0},
                "last_updated": datetime.utcnow().isoformat()
            }
    
    async def _update_cache_totals(self, cost_usd: float, session_id: str):
        """Update cached cost totals"""
        if not self.redis_manager:
            return
        
        try:
            # Update daily total
            today_key = f"{self.cache_prefix}daily:{datetime.utcnow().strftime('%Y-%m-%d')}"
            await self.redis_manager.increment_counter(today_key, cost_usd)
            
            # Update session total
            session_key = f"{self.cache_prefix}session:{session_id}"
            await self.redis_manager.increment_counter(session_key, cost_usd)
            
            # Update system total
            system_key = f"{self.cache_prefix}total"
            await self.redis_manager.increment_counter(system_key, cost_usd)
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to update cache totals: {e}")
    
    async def _get_session_total(self, session_id: str) -> float:
        """Get total cost for session"""
        if not self.redis_manager:
            return 0.0
        
        try:
            session_key = f"{self.cache_prefix}session:{session_id}"
            return await self.redis_manager.get_counter(session_key) or 0.0
        except Exception:
            return 0.0
    
    async def _get_daily_total(self) -> float:
        """Get total cost for today"""
        if not self.redis_manager:
            return 0.0
        
        try:
            today_key = f"{self.cache_prefix}daily:{datetime.utcnow().strftime('%Y-%m-%d')}"
            return await self.redis_manager.get_counter(today_key) or 0.0
        except Exception:
            return 0.0
    
    async def get_session_details(self, session_id: str) -> Dict[str, Any]:
        """Get detailed cost breakdown for a session"""
        try:
            async with get_async_read_session() as db:
                query = select(CostTracking).where(CostTracking.session_id == session_id)
                result = await db.execute(query)
                records = result.scalars().all()
                
                if not records:
                    return {"error": f"No cost data found for session {session_id}"}
                
                total_cost = sum(r.total_cost_usd for r in records)
                total_tokens = sum(r.total_tokens for r in records)
                
                calls = []
                for record in records:
                    calls.append({
                        "timestamp": record.created_at.isoformat(),
                        "provider": record.provider,
                        "model": record.model,
                        "agent_id": record.agent_id,
                        "agent_name": record.agent_name,
                        "input_tokens": record.input_tokens,
                        "output_tokens": record.output_tokens,
                        "total_tokens": record.total_tokens,
                        "cost_usd": record.total_cost_usd,
                        "response_time_ms": record.response_time_ms
                    })
                
                return {
                    "session_id": session_id,
                    "total_cost_usd": total_cost,
                    "total_tokens": total_tokens,
                    "total_calls": len(records),
                    "total_interactions": len(records),  # Alias for backwards compatibility
                    "calls": calls,
                    "generated_at": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"❌ Failed to get session details: {e}")
            return {"error": str(e)}
    
    async def get_agent_costs(self, agent_id: str, days: int = 7) -> Dict[str, Any]:
        """Get cost analysis for specific agent"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            async with get_async_read_session() as db:
                query = select(CostTracking).where(
                    and_(
                        CostTracking.agent_id == agent_id,
                        CostTracking.created_at >= start_date
                    )
                )
                result = await db.execute(query)
                records = result.scalars().all()
                
                if not records:
                    return {
                        "agent_id": agent_id,
                        "period_days": days,
                        "total_cost_usd": 0,
                        "total_tokens": 0,
                        "total_calls": 0,
                        "model_breakdown": {},
                        "daily_breakdown": {},
                        "generated_at": datetime.utcnow().isoformat()
                    }
                
                total_cost = sum(r.total_cost_usd for r in records)
                total_tokens = sum(r.total_tokens for r in records)
                
                # Model breakdown
                model_breakdown = {}
                for record in records:
                    if record.model not in model_breakdown:
                        model_breakdown[record.model] = {"cost": 0, "tokens": 0, "calls": 0}
                    model_breakdown[record.model]["cost"] += record.total_cost_usd
                    model_breakdown[record.model]["tokens"] += record.total_tokens
                    model_breakdown[record.model]["calls"] += 1
                
                # Daily breakdown
                daily_breakdown = {}
                for record in records:
                    date_key = record.created_at.date().isoformat()
                    if date_key not in daily_breakdown:
                        daily_breakdown[date_key] = {"cost": 0, "tokens": 0, "calls": 0}
                    daily_breakdown[date_key]["cost"] += record.total_cost_usd
                    daily_breakdown[date_key]["tokens"] += record.total_tokens
                    daily_breakdown[date_key]["calls"] += 1
                
                return {
                    "agent_id": agent_id,
                    "period_days": days,
                    "total_cost_usd": total_cost,
                    "total_tokens": total_tokens,
                    "total_calls": len(records),
                    "model_breakdown": model_breakdown,
                    "daily_breakdown": daily_breakdown,
                    "generated_at": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"❌ Failed to get agent costs: {e}")
            return {"error": str(e)}


# Global instance
unified_cost_tracker = UnifiedCostTracker()