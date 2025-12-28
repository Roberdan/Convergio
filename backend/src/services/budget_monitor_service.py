"""
🚨 Budget and Credit Monitoring Service
Intelligent budget monitoring, spending limits, and credit exhaustion detection
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

import structlog
from sqlalchemy import and_, func, select

from ..core.database import get_async_session, get_async_read_session
from ..models.cost_tracking import (
    CostAlert, CostSession, CostTracking,
    DailyCostSummary
)

logger = structlog.get_logger()

class BudgetMonitorService:
    """Advanced budget monitoring with credit tracking and intelligent alerts"""
    
    def __init__(self):
        """Initialize budget monitoring service"""
        self.default_daily_limit = Decimal("50.0")
        self.default_monthly_limit = Decimal("1500.0")
        self.warning_thresholds = [50, 75, 85, 95]  # Percentage thresholds
        self.critical_threshold = 90  # Percentage for circuit breaker
        
        # Provider credit limits (estimated based on typical plans)
        self.provider_credit_limits = {
            "openai": Decimal("100.0"),  # $100 per month typical
            "anthropic": Decimal("100.0"),  # $100 per month typical
            "perplexity": Decimal("20.0")   # $20 per month typical
        }
        
        self._alert_cache = {}  # Cache to prevent duplicate alerts
    
    async def check_all_limits(self) -> Dict[str, Any]:
        """Comprehensive check of all budget limits and credit usage"""
        
        logger.info("🔍 Running comprehensive budget monitoring check")
        
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "daily_status": await self._check_daily_limits(),
            "monthly_status": await self._check_monthly_limits(),
            "provider_status": await self._check_provider_limits(),
            "session_status": await self._check_session_anomalies(),
            "predictions": await self._generate_spending_predictions(),
            "circuit_breaker": await self._check_circuit_breaker(),
            "alerts_generated": []
        }
        
        # Generate alerts based on findings
        alerts = await self._generate_comprehensive_alerts(results)
        results["alerts_generated"] = alerts
        
        logger.info("✅ Budget monitoring check completed", 
                   total_alerts=len(alerts))
        
        return results
    
    async def _check_daily_limits(self) -> Dict[str, Any]:
        """Check daily spending limits"""
        
        async with get_async_read_session() as db:
            today = datetime.utcnow().date()
            
            result = await db.execute(
                select(DailyCostSummary)
                .where(func.date(DailyCostSummary.date) == today)
            )
            daily_summary = result.scalar_one_or_none()
            
            if not daily_summary:
                return {
                    "current_spend": 0.0,
                    "daily_limit": float(self.default_daily_limit),
                    "utilization_percent": 0.0,
                    "status": "healthy",
                    "remaining_budget": float(self.default_daily_limit)
                }
            
            utilization = (daily_summary.total_cost_usd / daily_summary.daily_budget_usd) * 100
            remaining = daily_summary.daily_budget_usd - daily_summary.total_cost_usd
            
            status = "healthy"
            if utilization >= 100:
                status = "exceeded"
            elif utilization >= 90:
                status = "critical"
            elif utilization >= 75:
                status = "warning"
            elif utilization >= 50:
                status = "moderate"
            
            return {
                "current_spend": float(daily_summary.total_cost_usd),
                "daily_limit": float(daily_summary.daily_budget_usd),
                "utilization_percent": float(utilization),
                "status": status,
                "remaining_budget": float(remaining),
                "provider_breakdown": daily_summary.provider_breakdown,
                "hourly_trend": daily_summary.hourly_breakdown
            }
    
    async def _check_monthly_limits(self) -> Dict[str, Any]:
        """Check monthly spending limits"""
        
        async with get_async_read_session() as db:
            # Get current month data
            start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end_of_month = (start_of_month + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
            
            result = await db.execute(
                select(func.sum(DailyCostSummary.total_cost_usd))
                .where(
                    and_(
                        DailyCostSummary.date >= start_of_month,
                        DailyCostSummary.date <= end_of_month
                    )
                )
            )
            monthly_spend = result.scalar() or Decimal("0")
            
            # Get provider breakdown for the month
            provider_result = await db.execute(
                select(
                    func.sum(DailyCostSummary.openai_cost_usd).label("openai"),
                    func.sum(DailyCostSummary.anthropic_cost_usd).label("anthropic"),
                    func.sum(DailyCostSummary.perplexity_cost_usd).label("perplexity"),
                    func.sum(DailyCostSummary.other_cost_usd).label("other")
                )
                .where(
                    and_(
                        DailyCostSummary.date >= start_of_month,
                        DailyCostSummary.date <= end_of_month
                    )
                )
            )
            provider_totals = provider_result.first()
            
            utilization = (monthly_spend / self.default_monthly_limit) * 100
            remaining = self.default_monthly_limit - monthly_spend
            
            status = "healthy"
            if utilization >= 100:
                status = "exceeded"
            elif utilization >= 90:
                status = "critical"
            elif utilization >= 75:
                status = "warning"
            elif utilization >= 50:
                status = "moderate"
            
            return {
                "current_spend": float(monthly_spend),
                "monthly_limit": float(self.default_monthly_limit),
                "utilization_percent": float(utilization),
                "status": status,
                "remaining_budget": float(remaining),
                "provider_breakdown": {
                    "openai": float(provider_totals.openai or 0),
                    "anthropic": float(provider_totals.anthropic or 0),
                    "perplexity": float(provider_totals.perplexity or 0),
                    "other": float(provider_totals.other or 0)
                },
                "days_remaining": (end_of_month - datetime.utcnow()).days + 1
            }
    
    async def _check_provider_limits(self) -> Dict[str, Any]:
        """Check individual provider credit limits"""
        
        provider_status = {}
        
        async with get_async_read_session() as db:
            start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            for provider, credit_limit in self.provider_credit_limits.items():
                result = await db.execute(
                    select(func.sum(CostTracking.total_cost_usd))
                    .where(
                        and_(
                            CostTracking.provider == provider,
                            CostTracking.created_at >= start_of_month
                        )
                    )
                )
                provider_spend = result.scalar() or Decimal("0")
                
                utilization = (provider_spend / credit_limit) * 100
                remaining = credit_limit - provider_spend
                
                status = "healthy"
                if utilization >= 100:
                    status = "exhausted"
                elif utilization >= 95:
                    status = "critical"
                elif utilization >= 85:
                    status = "warning"
                elif utilization >= 70:
                    status = "moderate"
                
                provider_status[provider] = {
                    "current_spend": float(provider_spend),
                    "credit_limit": float(credit_limit),
                    "utilization_percent": float(utilization),
                    "status": status,
                    "remaining_credits": float(remaining),
                    "estimated_days_remaining": self._estimate_days_remaining(
                        float(provider_spend), float(credit_limit)
                    )
                }
        
        return provider_status
    
    async def _check_session_anomalies(self) -> Dict[str, Any]:
        """Check for unusual session spending patterns"""
        
        async with get_async_read_session() as db:
            # Get sessions from last 24 hours
            last_24h = datetime.utcnow() - timedelta(hours=24)
            
            result = await db.execute(
                select(CostSession)
                .where(CostSession.started_at >= last_24h)
                .order_by(CostSession.total_cost_usd.desc())
                .limit(10)
            )
            recent_sessions = result.scalars().all()
            
            # Calculate statistics
            if recent_sessions:
                costs = [float(s.total_cost_usd) for s in recent_sessions]
                avg_cost = sum(costs) / len(costs)
                max_cost = max(costs)
                
                # Detect anomalies (sessions > 3x average)
                anomalies = []
                for session in recent_sessions:
                    session_cost = float(session.total_cost_usd)
                    if session_cost > avg_cost * 3 and session_cost > 1.0:
                        anomalies.append({
                            "session_id": session.session_id,
                            "cost": session_cost,
                            "interactions": session.total_interactions,
                            "avg_cost_per_interaction": session_cost / session.total_interactions if session.total_interactions > 0 else 0,
                            "started_at": session.started_at.isoformat(),
                            "status": session.status
                        })
                
                return {
                    "total_sessions": len(recent_sessions),
                    "average_cost": avg_cost,
                    "max_cost": max_cost,
                    "anomalies_detected": len(anomalies),
                    "anomalous_sessions": anomalies[:5]  # Top 5 anomalies
                }
            else:
                return {
                    "total_sessions": 0,
                    "average_cost": 0.0,
                    "max_cost": 0.0,
                    "anomalies_detected": 0,
                    "anomalous_sessions": []
                }
    
    async def _generate_spending_predictions(self) -> Dict[str, Any]:
        """Generate spending predictions based on historical data"""
        
        async with get_async_read_session() as db:
            # Get last 7 days of data
            week_ago = datetime.utcnow().date() - timedelta(days=7)
            
            result = await db.execute(
                select(DailyCostSummary.total_cost_usd, DailyCostSummary.date)
                .where(DailyCostSummary.date >= week_ago)
                .order_by(DailyCostSummary.date)
            )
            daily_costs = result.all()
            
            if len(daily_costs) < 3:
                return {
                    "insufficient_data": True,
                    "message": "Need at least 3 days of data for predictions"
                }
            
            # Simple trend analysis
            costs = [float(row.total_cost_usd) for row in daily_costs]
            avg_daily = sum(costs) / len(costs)
            
            # Linear trend calculation
            x_vals = list(range(len(costs)))
            n = len(costs)
            sum_x = sum(x_vals)
            sum_y = sum(costs)
            sum_xy = sum(x * y for x, y in zip(x_vals, costs))
            sum_x2 = sum(x * x for x in x_vals)
            
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x) if (n * sum_x2 - sum_x * sum_x) != 0 else 0
            intercept = (sum_y - slope * sum_x) / n
            
            # Predictions
            tomorrow_prediction = intercept + slope * n
            week_prediction = sum(intercept + slope * (n + i) for i in range(1, 8))
            month_prediction = sum(intercept + slope * (n + i) for i in range(1, 31))
            
            return {
                "current_trend": "increasing" if slope > 0.01 else "decreasing" if slope < -0.01 else "stable",
                "average_daily_spend": avg_daily,
                "trend_slope": slope,
                "predictions": {
                    "tomorrow": max(0, tomorrow_prediction),
                    "next_7_days": max(0, week_prediction),
                    "next_30_days": max(0, month_prediction)
                },
                "budget_burn_rate": {
                    "daily_limit_days": float(self.default_daily_limit) / avg_daily if avg_daily > 0 else float('inf'),
                    "monthly_limit_days": float(self.default_monthly_limit) / avg_daily if avg_daily > 0 else float('inf')
                }
            }
    
    async def _check_circuit_breaker(self) -> Dict[str, Any]:
        """Check if circuit breaker should be triggered"""
        
        daily_status = await self._check_daily_limits()
        monthly_status = await self._check_monthly_limits()
        provider_status = await self._check_provider_limits()
        
        should_break = False
        reasons = []
        
        # Check daily limit
        if daily_status["utilization_percent"] >= self.critical_threshold:
            should_break = True
            reasons.append(f"Daily limit at {daily_status['utilization_percent']:.1f}%")
        
        # Check monthly limit
        if monthly_status["utilization_percent"] >= self.critical_threshold:
            should_break = True
            reasons.append(f"Monthly limit at {monthly_status['utilization_percent']:.1f}%")
        
        # Check provider limits
        for provider, status in provider_status.items():
            if status["utilization_percent"] >= 95:
                should_break = True
                reasons.append(f"{provider} credits at {status['utilization_percent']:.1f}%")
        
        return {
            "should_trigger": should_break,
            "reasons": reasons,
            "recommended_action": "suspend_api_calls" if should_break else "continue",
            "manual_override_required": should_break,
            "current_status": "CIRCUIT_OPEN" if should_break else "CIRCUIT_CLOSED"
        }
    
    async def _generate_comprehensive_alerts(self, status_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate intelligent alerts based on all monitoring results"""
        
        alerts = []
        datetime.utcnow()
        
        # Daily limit alerts
        daily = status_results["daily_status"]
        if daily["utilization_percent"] >= 95:
            alerts.append(await self._create_alert(
                "daily_critical",
                "critical",
                f"Daily budget critically exceeded: ${daily['current_spend']:.2f} of ${daily['daily_limit']:.2f} ({daily['utilization_percent']:.1f}%)"
            ))
        elif daily["utilization_percent"] >= 75:
            alerts.append(await self._create_alert(
                "daily_warning",
                "warning",
                f"Daily budget warning: ${daily['current_spend']:.2f} of ${daily['daily_limit']:.2f} ({daily['utilization_percent']:.1f}%)"
            ))
        
        # Monthly limit alerts
        monthly = status_results["monthly_status"]
        if monthly["utilization_percent"] >= 90:
            alerts.append(await self._create_alert(
                "monthly_critical",
                "critical",
                f"Monthly budget critical: ${monthly['current_spend']:.2f} of ${monthly['monthly_limit']:.2f} ({monthly['utilization_percent']:.1f}%)"
            ))
        
        # Provider credit alerts
        for provider, status in status_results["provider_status"].items():
            if status["utilization_percent"] >= 95:
                alerts.append(await self._create_alert(
                    f"provider_{provider}_exhausted",
                    "critical",
                    f"{provider.title()} credits nearly exhausted: ${status['current_spend']:.2f} of ${status['credit_limit']:.2f} ({status['utilization_percent']:.1f}%)"
                ))
            elif status["utilization_percent"] >= 85:
                alerts.append(await self._create_alert(
                    f"provider_{provider}_warning",
                    "warning",
                    f"{provider.title()} credits low: ${status['current_spend']:.2f} of ${status['credit_limit']:.2f} ({status['utilization_percent']:.1f}%)"
                ))
        
        # Session anomaly alerts
        session_status = status_results["session_status"]
        if session_status["anomalies_detected"] > 0:
            alerts.append(await self._create_alert(
                "session_anomalies",
                "warning",
                f"Detected {session_status['anomalies_detected']} high-cost sessions (avg: ${session_status['average_cost']:.2f}, max: ${session_status['max_cost']:.2f})"
            ))
        
        # Circuit breaker alerts
        circuit = status_results["circuit_breaker"]
        if circuit["should_trigger"]:
            alerts.append(await self._create_alert(
                "circuit_breaker",
                "critical",
                f"Circuit breaker triggered: {', '.join(circuit['reasons'])}"
            ))
        
        # Store alerts in database
        if alerts:
            await self._store_alerts(alerts)
        
        return alerts
    
    async def _create_alert(self, alert_type: str, severity: str, message: str) -> Dict[str, Any]:
        """Create a structured alert"""
        
        alert_id = f"{alert_type}_{datetime.utcnow().strftime('%Y%m%d_%H')}"
        
        # Check if we've already sent this alert recently (prevent spam)
        if alert_id in self._alert_cache:
            last_sent = self._alert_cache[alert_id]
            if datetime.utcnow() - last_sent < timedelta(hours=1):
                return None
        
        self._alert_cache[alert_id] = datetime.utcnow()
        
        return {
            "id": alert_id,
            "type": alert_type,
            "severity": severity,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "requires_action": severity == "critical"
        }
    
    async def _store_alerts(self, alerts: List[Dict[str, Any]]) -> None:
        """Store alerts in database"""
        
        async with get_async_session() as db:
            for alert_data in alerts:
                if alert_data is None:  # Skip cached alerts
                    continue
                    
                alert = CostAlert(
                    alert_type=alert_data["type"],
                    severity=alert_data["severity"],
                    current_value=Decimal("0"),  # Will be populated with actual values
                    threshold_value=Decimal("0"),  # Will be populated with actual values
                    message=alert_data["message"]
                )
                db.add(alert)
            
            await db.commit()
    
    def _estimate_days_remaining(self, current_spend: float, limit: float) -> int:
        """Estimate days remaining before credit exhaustion"""
        
        if current_spend <= 0:
            return 30  # Default if no spending
        
        # Get current day of month
        current_day = datetime.utcnow().day
        
        # Calculate daily average
        daily_avg = current_spend / current_day if current_day > 0 else current_spend
        
        if daily_avg <= 0:
            return 30
        
        remaining_budget = limit - current_spend
        days_remaining = int(remaining_budget / daily_avg)
        
        return max(0, min(days_remaining, 30))  # Cap at 30 days
    
    async def set_budget_limits(
        self,
        daily_limit: Optional[Decimal] = None,
        monthly_limit: Optional[Decimal] = None,
        provider_limits: Optional[Dict[str, Decimal]] = None
    ) -> Dict[str, Any]:
        """Set custom budget limits"""
        
        if daily_limit is not None:
            self.default_daily_limit = daily_limit
        
        if monthly_limit is not None:
            self.default_monthly_limit = monthly_limit
        
        if provider_limits:
            self.provider_credit_limits.update(provider_limits)
        
        return {
            "success": True,
            "updated_limits": {
                "daily_limit": float(self.default_daily_limit),
                "monthly_limit": float(self.default_monthly_limit),
                "provider_limits": {k: float(v) for k, v in self.provider_credit_limits.items()}
            }
        }
    
    async def get_budget_status_summary(self) -> Dict[str, Any]:
        """Get a concise budget status summary"""
        
        full_status = await self.check_all_limits()
        
        return {
            "overall_status": self._determine_overall_status(full_status),
            "daily_utilization": full_status["daily_status"]["utilization_percent"],
            "monthly_utilization": full_status["monthly_status"]["utilization_percent"],
            "critical_providers": [
                provider for provider, status in full_status["provider_status"].items()
                if status["utilization_percent"] >= 90
            ],
            "circuit_breaker_active": full_status["circuit_breaker"]["should_trigger"],
            "total_alerts": len(full_status["alerts_generated"]),
            "next_prediction": full_status["predictions"].get("predictions", {}).get("tomorrow", 0)
        }
    
    def _determine_overall_status(self, full_status: Dict[str, Any]) -> str:
        """Determine overall budget health status"""
        
        if full_status["circuit_breaker"]["should_trigger"]:
            return "critical"
        
        max_utilization = max([
            full_status["daily_status"]["utilization_percent"],
            full_status["monthly_status"]["utilization_percent"]
        ] + [
            status["utilization_percent"] 
            for status in full_status["provider_status"].values()
        ])
        
        if max_utilization >= 95:
            return "critical"
        elif max_utilization >= 85:
            return "warning"
        elif max_utilization >= 70:
            return "moderate"
        else:
            return "healthy"


# Global budget monitor instance
budget_monitor = BudgetMonitorService()