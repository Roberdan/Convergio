"""
CONVERGIO 2029 - COST TRACKER
Tracking costi OpenAI integrato con AutoGen
"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import structlog

from .redis_state_manager import RedisStateManager

logger = structlog.get_logger()

# OpenAI pricing per 1K tokens (as of 2025)
OPENAI_PRICING = {
    "gpt-4o": {"input": 0.005, "output": 0.015},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    "text-embedding-3-small": {"input": 0.00002, "output": 0.0},
    "text-embedding-3-large": {"input": 0.00013, "output": 0.0},
}

# Anthropic pricing per 1K tokens
ANTHROPIC_PRICING = {
    "claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015},
    "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
    "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
}


class CostTracker:
    """Cost tracking service for AI model usage."""
    
    def __init__(self, state_manager: RedisStateManager):
        """Initialize cost tracker."""
        self.state_manager = state_manager
        self.cost_limit_usd = 50.0  # Default daily limit
        
    def set_cost_limit(self, limit_usd: float) -> None:
        """Set daily cost limit."""
        self.cost_limit_usd = limit_usd
        logger.info("Cost limit updated", limit_usd=limit_usd)
    
    async def calculate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        provider: str = "openai"
    ) -> Dict[str, Any]:
        """Calculate cost for token usage."""
        try:
            pricing_table = OPENAI_PRICING if provider == "openai" else ANTHROPIC_PRICING
            
            if model not in pricing_table:
                logger.warning("Unknown model for cost calculation", model=model, provider=provider)
                # Use default pricing for unknown models
                input_cost_per_1k = 0.001
                output_cost_per_1k = 0.002
            else:
                pricing = pricing_table[model]
                input_cost_per_1k = pricing["input"]
                output_cost_per_1k = pricing["output"]
            
            # Calculate costs
            input_cost = (input_tokens / 1000) * input_cost_per_1k
            output_cost = (output_tokens / 1000) * output_cost_per_1k
            total_cost = input_cost + output_cost
            
            cost_breakdown = {
                "model": model,
                "provider": provider,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "input_cost_usd": round(input_cost, 6),
                "output_cost_usd": round(output_cost, 6),
                "total_cost_usd": round(total_cost, 6),
                "pricing": {
                    "input_per_1k": input_cost_per_1k,
                    "output_per_1k": output_cost_per_1k
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.debug(
                "Cost calculated",
                model=model,
                total_tokens=input_tokens + output_tokens,
                total_cost_usd=total_cost
            )
            
            return cost_breakdown
            
        except Exception as e:
            logger.error("Failed to calculate cost", error=str(e), model=model)
            return {
                "model": model,
                "provider": provider,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "input_cost_usd": 0.0,
                "output_cost_usd": 0.0,
                "total_cost_usd": 0.0,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def track_conversation_cost(
        self,
        conversation_id: str,
        cost_breakdown: Dict[str, Any]
    ) -> None:
        """Track cost for a specific conversation."""
        try:
            # Store cost in Redis via state manager
            await self.state_manager.track_cost(
                conversation_id=conversation_id,
                model=cost_breakdown["model"],
                tokens_used=cost_breakdown["total_tokens"],
                cost_usd=cost_breakdown["total_cost_usd"]
            )
            
            # Check if we're approaching daily limit
            daily_summary = await self.state_manager.get_daily_cost_summary()
            daily_cost = daily_summary["total_cost_usd"]
            
            if daily_cost > self.cost_limit_usd * 0.8:  # 80% of limit
                logger.warning(
                    "Approaching daily cost limit",
                    daily_cost_usd=daily_cost,
                    limit_usd=self.cost_limit_usd,
                    percentage=round((daily_cost / self.cost_limit_usd) * 100, 1)
                )
            
            if daily_cost > self.cost_limit_usd:
                logger.error(
                    "Daily cost limit exceeded",
                    daily_cost_usd=daily_cost,
                    limit_usd=self.cost_limit_usd
                )
                # Note: In production, you might want to disable or throttle the service
            
        except Exception as e:
            logger.error("Failed to track conversation cost", error=str(e))
    
    async def get_conversation_costs(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get all costs for a conversation."""
        try:
            # Get conversation to extract cost data from messages
            conversation = await self.state_manager.get_conversation(conversation_id)
            if not conversation:
                return []
            
            costs = []
            for message in conversation.get("messages", []):
                if message.get("role") == "assistant" and "cost_breakdown" in message.get("metadata", {}):
                    costs.append(message["metadata"]["cost_breakdown"])
            
            return costs
            
        except Exception as e:
            logger.error("Failed to get conversation costs", error=str(e))
            return []
    
    async def get_daily_summary(self, date: Optional[str] = None) -> Dict[str, Any]:
        """Get daily cost summary."""
        try:
            summary = await self.state_manager.get_daily_cost_summary(date)
            
            # Add additional metrics
            summary.update({
                "daily_limit_usd": self.cost_limit_usd,
                "limit_usage_percentage": round(
                    (summary["total_cost_usd"] / self.cost_limit_usd) * 100, 1
                ) if self.cost_limit_usd > 0 else 0,
                "remaining_budget_usd": max(0, self.cost_limit_usd - summary["total_cost_usd"]),
                "status": self._get_budget_status(summary["total_cost_usd"])
            })
            
            return summary
            
        except Exception as e:
            logger.error("Failed to get daily summary", error=str(e))
            return {
                "date": date or datetime.utcnow().strftime("%Y-%m-%d"),
                "total_tokens": 0,
                "total_cost_usd": 0.0,
                "error": str(e)
            }
    
    async def get_weekly_summary(self) -> Dict[str, Any]:
        """Get weekly cost summary."""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=7)
            
            daily_summaries = []
            total_cost = 0.0
            total_tokens = 0
            
            current_date = start_date
            while current_date <= end_date:
                date_str = current_date.strftime("%Y-%m-%d")
                daily_summary = await self.get_daily_summary(date_str)
                daily_summaries.append(daily_summary)
                total_cost += daily_summary["total_cost_usd"]
                total_tokens += daily_summary["total_tokens"]
                current_date += timedelta(days=1)
            
            weekly_limit = self.cost_limit_usd * 7
            
            return {
                "period": {
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d")
                },
                "total_cost_usd": round(total_cost, 2),
                "total_tokens": total_tokens,
                "weekly_limit_usd": weekly_limit,
                "average_daily_cost_usd": round(total_cost / 7, 2),
                "daily_summaries": daily_summaries,
                "status": self._get_budget_status(total_cost, weekly_limit)
            }
            
        except Exception as e:
            logger.error("Failed to get weekly summary", error=str(e))
            return {"error": str(e)}
    
    async def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive cost summary."""
        try:
            daily = await self.get_daily_summary()
            weekly = await self.get_weekly_summary()
            
            return {
                "daily": daily,
                "weekly": weekly,
                "pricing_tables": {
                    "openai": OPENAI_PRICING,
                    "anthropic": ANTHROPIC_PRICING
                },
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Failed to get cost summary", error=str(e))
            return {"error": str(e)}
    
    def _get_budget_status(self, current_cost: float, limit: Optional[float] = None) -> str:
        """Get budget status based on current cost."""
        if limit is None:
            limit = self.cost_limit_usd
        
        if limit <= 0:
            return "no_limit"
        
        percentage = (current_cost / limit) * 100
        
        if percentage >= 100:
            return "exceeded"
        elif percentage >= 80:
            return "warning"
        elif percentage >= 50:
            return "moderate"
        else:
            return "healthy"
    
    async def check_budget_limits(self, conversation_id: str) -> Dict[str, Any]:
        """Check if conversation can proceed based on budget limits."""
        try:
            daily_summary = await self.get_daily_summary()
            
            can_proceed = daily_summary["total_cost_usd"] < self.cost_limit_usd
            
            return {
                "can_proceed": can_proceed,
                "current_cost_usd": daily_summary["total_cost_usd"],
                "daily_limit_usd": self.cost_limit_usd,
                "remaining_budget_usd": daily_summary["remaining_budget_usd"],
                "status": daily_summary["status"],
                "reason": "Daily budget limit exceeded" if not can_proceed else "Budget OK"
            }
            
        except Exception as e:
            logger.error("Failed to check budget limits", error=str(e))
            return {
                "can_proceed": True,  # Default to allowing if check fails
                "error": str(e)
            }