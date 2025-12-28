"""
Proactive Actions System - Ali's automated intervention system
Automatically takes actions based on insights and patterns
"""

from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import uuid
import asyncio
from collections import deque

import structlog

from ..event_bus import Event, EventType, EventPriority, event_bus
from ..insight_engine import Insight, InsightType, InsightSeverity, insight_engine
from ..ali_swarm_orchestrator import AliSwarmOrchestrator

logger = structlog.get_logger()


class ActionType(str, Enum):
    NOTIFY = "notify"
    EXECUTE_AGENT = "execute_agent"
    SCALE_RESOURCES = "scale_resources"
    ROLLBACK = "rollback"
    OPTIMIZE = "optimize"
    HEAL = "heal"
    PREVENT = "prevent"
    ESCALATE = "escalate"


class ActionStatus(str, Enum):
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ProactiveAction:
    """Represents a proactive action to be taken"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: ActionType = ActionType.NOTIFY
    status: ActionStatus = ActionStatus.PENDING
    insight_id: Optional[str] = None
    title: str = ""
    description: str = ""
    target: Dict[str, Any] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)
    requires_approval: bool = False
    auto_execute: bool = True
    priority: int = 5
    scheduled_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "status": self.status,
            "insight_id": self.insight_id,
            "title": self.title,
            "description": self.description,
            "target": self.target,
            "parameters": self.parameters,
            "requires_approval": self.requires_approval,
            "priority": self.priority,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "result": self.result,
            "error": self.error
        }


@dataclass
class ActionPolicy:
    """Policy for determining when to take actions"""
    id: str
    name: str
    description: str
    insight_types: List[InsightType]
    severity_threshold: InsightSeverity
    action_generator: Callable[[Insight], Optional[ProactiveAction]]
    enabled: bool = True
    max_actions_per_hour: int = 10
    cooldown: timedelta = timedelta(minutes=15)
    last_action: Optional[datetime] = None
    action_count: int = 0
    
    def can_act(self, insight: Insight) -> bool:
        """Check if policy can generate action for insight"""
        if not self.enabled:
            return False
        
        # Check insight type
        if insight.type not in self.insight_types:
            return False
        
        # Check severity threshold
        severity_order = [
            InsightSeverity.INFO,
            InsightSeverity.SUCCESS,
            InsightSeverity.WARNING,
            InsightSeverity.CRITICAL
        ]
        
        if severity_order.index(insight.severity) < severity_order.index(self.severity_threshold):
            return False
        
        # Check rate limiting
        if self.last_action:
            elapsed = datetime.utcnow() - self.last_action
            if elapsed < self.cooldown:
                return False
        
        # Check action count limit
        if self.action_count >= self.max_actions_per_hour:
            # Reset count if hour has passed
            if self.last_action and (datetime.utcnow() - self.last_action) > timedelta(hours=1):
                self.action_count = 0
            else:
                return False
        
        return True
    
    def generate_action(self, insight: Insight) -> Optional[ProactiveAction]:
        """Generate action from insight if policy allows"""
        if not self.can_act(insight):
            return None
        
        action = self.action_generator(insight)
        if action:
            self.last_action = datetime.utcnow()
            self.action_count += 1
            action.insight_id = insight.id
        
        return action


class ProactiveActionsManager:
    """Manages proactive actions based on insights"""
    
    def __init__(self, orchestrator: Optional[AliSwarmOrchestrator] = None):
        self.orchestrator = orchestrator
        self.policies: Dict[str, ActionPolicy] = {}
        self.action_queue: asyncio.Queue = asyncio.Queue()
        self.action_history: deque = deque(maxlen=1000)
        self.running = False
        self._executor_task = None
        
        # Metrics
        self.metrics = {
            "actions_created": 0,
            "actions_executed": 0,
            "actions_completed": 0,
            "actions_failed": 0,
            "approvals_pending": 0
        }
        
        # Initialize default policies
        self._register_default_policies()
        
        # Subscribe to insights
        insight_engine.subscribe_to_insights(self._handle_insight)
    
    async def start(self):
        """Start the proactive actions manager"""
        if not self.running:
            self.running = True
            self._executor_task = asyncio.create_task(self._execute_actions())
            logger.info("🚀 Proactive actions manager started")
    
    async def stop(self):
        """Stop the proactive actions manager"""
        self.running = False
        if self._executor_task:
            await self._executor_task
            logger.info("🛑 Proactive actions manager stopped")
    
    def register_policy(self, policy: ActionPolicy):
        """Register a new action policy"""
        self.policies[policy.id] = policy
        logger.info(f"📝 Action policy registered: {policy.name}")
    
    async def _handle_insight(self, insight: Insight):
        """Handle new insight and generate actions"""
        # Check all policies
        for policy in self.policies.values():
            try:
                action = policy.generate_action(insight)
                if action:
                    await self.queue_action(action)
            except Exception as e:
                logger.error(f"❌ Error generating action from policy {policy.name}: {e}")
    
    async def queue_action(self, action: ProactiveAction):
        """Queue an action for execution"""
        await self.action_queue.put(action)
        self.metrics["actions_created"] += 1
        
        # Publish event
        await event_bus.publish(Event(
            type=EventType.RECOMMENDATION_MADE,
            priority=EventPriority.MEDIUM,
            source="proactive_actions",
            data=action.to_dict()
        ))
        
        logger.info(f"📋 Action queued: {action.title}", action_type=action.type)
    
    async def _execute_actions(self):
        """Main action execution loop"""
        while self.running:
            try:
                # Get next action with timeout
                action = await asyncio.wait_for(
                    self.action_queue.get(),
                    timeout=1.0
                )
                
                # Check if approval required
                if action.requires_approval and not action.auto_execute:
                    self.metrics["approvals_pending"] += 1
                    logger.info(f"⏸️ Action requires approval: {action.title}")
                    continue
                
                # Execute action
                await self._execute_action(action)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"❌ Error in action executor: {e}")
    
    async def _execute_action(self, action: ProactiveAction):
        """Execute a specific action"""
        action.status = ActionStatus.EXECUTING
        action.executed_at = datetime.utcnow()
        self.metrics["actions_executed"] += 1
        
        try:
            # Route to appropriate handler
            handlers = {
                ActionType.NOTIFY: self._handle_notify,
                ActionType.EXECUTE_AGENT: self._handle_execute_agent,
                ActionType.SCALE_RESOURCES: self._handle_scale_resources,
                ActionType.ROLLBACK: self._handle_rollback,
                ActionType.OPTIMIZE: self._handle_optimize,
                ActionType.HEAL: self._handle_heal,
                ActionType.PREVENT: self._handle_prevent,
                ActionType.ESCALATE: self._handle_escalate
            }
            
            handler = handlers.get(action.type)
            if handler:
                result = await handler(action)
                action.result = result
                action.status = ActionStatus.COMPLETED
                action.completed_at = datetime.utcnow()
                self.metrics["actions_completed"] += 1
                
                logger.info(f"✅ Action completed: {action.title}")
            else:
                raise ValueError(f"Unknown action type: {action.type}")
                
        except Exception as e:
            action.status = ActionStatus.FAILED
            action.error = str(e)
            self.metrics["actions_failed"] += 1
            logger.error(f"❌ Action failed: {action.title} - {e}")
        
        finally:
            self.action_history.append(action)
    
    async def _handle_notify(self, action: ProactiveAction) -> Dict[str, Any]:
        """Send notification"""
        # In real implementation, would send to notification service
        logger.info(f"📢 Notification: {action.description}")
        return {"notified": True, "timestamp": datetime.utcnow().isoformat()}
    
    async def _handle_execute_agent(self, action: ProactiveAction) -> Dict[str, Any]:
        """Execute an AI agent"""
        if not self.orchestrator:
            raise ValueError("Orchestrator not available")
        
        agent_name = action.parameters.get("agent_name", "ali_chief_of_staff")
        prompt = action.parameters.get("prompt", action.description)
        
        # Execute agent via orchestrator
        result = await self.orchestrator.process_request(prompt)
        
        return {
            "agent": agent_name,
            "execution_result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _handle_scale_resources(self, action: ProactiveAction) -> Dict[str, Any]:
        """Scale system resources"""
        scale_factor = action.parameters.get("scale_factor", 1.5)
        resource_type = action.parameters.get("resource_type", "compute")
        
        logger.info(f"📈 Scaling {resource_type} by {scale_factor}x")
        
        # In real implementation, would call cloud scaling APIs
        return {
            "scaled": True,
            "resource_type": resource_type,
            "scale_factor": scale_factor
        }
    
    async def _handle_rollback(self, action: ProactiveAction) -> Dict[str, Any]:
        """Perform rollback"""
        version = action.parameters.get("target_version")
        component = action.parameters.get("component")
        
        logger.info(f"↩️ Rolling back {component} to version {version}")
        
        # In real implementation, would trigger rollback procedures
        return {
            "rollback": True,
            "component": component,
            "version": version
        }
    
    async def _handle_optimize(self, action: ProactiveAction) -> Dict[str, Any]:
        """Optimize system performance"""
        optimization_type = action.parameters.get("type", "general")
        
        logger.info(f"⚡ Running {optimization_type} optimization")
        
        # In real implementation, would run optimization procedures
        return {
            "optimized": True,
            "type": optimization_type,
            "improvements": {"response_time": -20, "resource_usage": -15}
        }
    
    async def _handle_heal(self, action: ProactiveAction) -> Dict[str, Any]:
        """Self-healing action"""
        issue_type = action.parameters.get("issue_type")
        
        logger.info(f"🩹 Self-healing for {issue_type}")
        
        # In real implementation, would run healing procedures
        return {
            "healed": True,
            "issue_type": issue_type,
            "actions_taken": ["restart_service", "clear_cache", "reset_connections"]
        }
    
    async def _handle_prevent(self, action: ProactiveAction) -> Dict[str, Any]:
        """Preventive action"""
        risk_type = action.parameters.get("risk_type")
        
        logger.info(f"🛡️ Preventing {risk_type}")
        
        # In real implementation, would apply preventive measures
        return {
            "prevented": True,
            "risk_type": risk_type,
            "measures_applied": ["rate_limiting", "resource_reservation", "backup_creation"]
        }
    
    async def _handle_escalate(self, action: ProactiveAction) -> Dict[str, Any]:
        """Escalate to human operator"""
        escalation_level = action.parameters.get("level", "L1")
        urgency = action.parameters.get("urgency", "medium")
        
        logger.info(f"📞 Escalating to {escalation_level} support with {urgency} urgency")
        
        # In real implementation, would create support ticket
        return {
            "escalated": True,
            "level": escalation_level,
            "urgency": urgency,
            "ticket_id": str(uuid.uuid4())
        }
    
    def _register_default_policies(self):
        """Register default action policies"""
        
        # Critical risk auto-mitigation
        def critical_risk_action(insight: Insight) -> ProactiveAction:
            return ProactiveAction(
                type=ActionType.HEAL,
                title=f"Auto-healing: {insight.title}",
                description=f"Automatically addressing: {insight.description}",
                parameters={"issue_type": "critical_risk"},
                auto_execute=True,
                priority=10
            )
        
        self.register_policy(ActionPolicy(
            id="critical_risk_mitigation",
            name="Critical Risk Mitigation",
            description="Automatically mitigate critical risks",
            insight_types=[InsightType.RISK, InsightType.ANOMALY],
            severity_threshold=InsightSeverity.CRITICAL,
            action_generator=critical_risk_action,
            max_actions_per_hour=5
        ))
        
        # Performance optimization
        def performance_action(insight: Insight) -> ProactiveAction:
            return ProactiveAction(
                type=ActionType.OPTIMIZE,
                title="Performance Optimization",
                description=insight.description,
                parameters={"type": "performance"},
                auto_execute=True,
                priority=7
            )
        
        self.register_policy(ActionPolicy(
            id="performance_optimization",
            name="Performance Auto-Optimization",
            description="Automatically optimize performance issues",
            insight_types=[InsightType.PERFORMANCE],
            severity_threshold=InsightSeverity.WARNING,
            action_generator=performance_action,
            cooldown=timedelta(hours=1)
        ))
        
        # Bottleneck resolution
        def bottleneck_action(insight: Insight) -> ProactiveAction:
            return ProactiveAction(
                type=ActionType.EXECUTE_AGENT,
                title="Deploy Agent to Resolve Bottleneck",
                description=f"Deploying agent to address: {insight.description}",
                parameters={
                    "agent_name": "wanda_workflow_orchestrator",
                    "prompt": f"Resolve bottleneck: {insight.description}"
                },
                auto_execute=True,
                priority=8
            )
        
        self.register_policy(ActionPolicy(
            id="bottleneck_resolution",
            name="Bottleneck Auto-Resolution",
            description="Deploy agents to resolve bottlenecks",
            insight_types=[InsightType.BOTTLENECK],
            severity_threshold=InsightSeverity.WARNING,
            action_generator=bottleneck_action
        ))
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get proactive actions metrics"""
        return {
            **self.metrics,
            "queue_size": self.action_queue.qsize(),
            "active_policies": len([p for p in self.policies.values() if p.enabled]),
            "total_policies": len(self.policies)
        }


# Global instance
proactive_manager = ProactiveActionsManager()


async def initialize_proactive_actions(orchestrator: Optional[AliSwarmOrchestrator] = None):
    """Initialize and start proactive actions"""
    global proactive_manager
    proactive_manager = ProactiveActionsManager(orchestrator)
    await proactive_manager.start()
    return proactive_manager