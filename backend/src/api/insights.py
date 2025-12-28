"""
API endpoints for insights and proactive actions
"""

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import asyncio

from ..agents.services.insight_engine import (
    insight_engine, Insight, InsightType, InsightSeverity
)
from ..agents.services.proactive_actions import (
    proactive_manager, ProactiveAction, ActionType, ActionStatus
)
from ..agents.services.event_bus import event_bus
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1", tags=["Insights & Actions"])


# ===================== Request/Response Models =====================

class InsightResponse(BaseModel):
    id: str
    type: str
    severity: str
    title: str
    description: str
    recommendations: List[str]
    metrics: Dict[str, Any]
    timestamp: str
    confidence: float
    is_actionable: bool


class ActionRequest(BaseModel):
    insight_id: Optional[str] = None
    type: Optional[ActionType] = ActionType.NOTIFY
    title: str
    description: str
    parameters: Dict[str, Any] = {}
    auto_execute: bool = False
    priority: int = 5


class ActionResponse(BaseModel):
    id: str
    type: str
    status: str
    title: str
    description: str
    priority: int
    executed_at: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class SystemMetricsResponse(BaseModel):
    events_processed: int
    patterns_detected: int
    insights_generated: int
    actions_executed: int
    actions_completed: int
    actions_failed: int
    system_health: float
    queue_sizes: Dict[str, int]
    active_rules: int
    active_policies: int


# ===================== Insights Endpoints =====================

@router.get("/insights", response_model=List[InsightResponse])
async def get_insights(
    type: Optional[InsightType] = None,
    severity: Optional[InsightSeverity] = None,
    since_hours: int = Query(24, ge=1, le=168),
    limit: int = Query(50, ge=1, le=200)
):
    """Get recent insights"""
    since = datetime.utcnow() - timedelta(hours=since_hours)
    
    insights = insight_engine.get_insights(
        type=type,
        severity=severity,
        since=since,
        limit=limit
    )
    
    return [
        InsightResponse(
            id=i.id,
            type=i.type,
            severity=i.severity,
            title=i.title,
            description=i.description,
            recommendations=i.recommendations,
            metrics=i.metrics,
            timestamp=i.timestamp.isoformat(),
            confidence=i.confidence,
            is_actionable=i.is_actionable
        )
        for i in insights
    ]


@router.get("/insights/{insight_id}", response_model=InsightResponse)
async def get_insight(insight_id: str):
    """Get specific insight by ID"""
    insights = insight_engine.get_insights()
    
    for insight in insights:
        if insight.id == insight_id:
            return InsightResponse(
                id=insight.id,
                type=insight.type,
                severity=insight.severity,
                title=insight.title,
                description=insight.description,
                recommendations=insight.recommendations,
                metrics=insight.metrics,
                timestamp=insight.timestamp.isoformat(),
                confidence=insight.confidence,
                is_actionable=insight.is_actionable
            )
    
    raise HTTPException(status_code=404, detail="Insight not found")


# ===================== Proactive Actions Endpoints =====================

@router.get("/proactive-actions", response_model=List[ActionResponse])
async def get_actions(
    status: Optional[ActionStatus] = None,
    limit: int = Query(50, ge=1, le=200)
):
    """Get recent proactive actions"""
    actions = list(proactive_manager.action_history)
    
    if status:
        actions = [a for a in actions if a.status == status]
    
    # Sort by most recent first
    actions.sort(key=lambda a: a.executed_at or datetime.min, reverse=True)
    
    return [
        ActionResponse(
            id=a.id,
            type=a.type,
            status=a.status,
            title=a.title,
            description=a.description,
            priority=a.priority,
            executed_at=a.executed_at.isoformat() if a.executed_at else None,
            result=a.result,
            error=a.error
        )
        for a in actions[:limit]
    ]


@router.post("/proactive-actions", response_model=ActionResponse)
async def create_action(request: ActionRequest):
    """Create a new proactive action"""
    action = ProactiveAction(
        type=request.type,
        title=request.title,
        description=request.description,
        insight_id=request.insight_id,
        parameters=request.parameters,
        auto_execute=request.auto_execute,
        priority=request.priority
    )
    
    await proactive_manager.queue_action(action)
    
    return ActionResponse(
        id=action.id,
        type=action.type,
        status=action.status,
        title=action.title,
        description=action.description,
        priority=action.priority
    )


# ===================== System Metrics =====================

@router.get("/system-metrics", response_model=SystemMetricsResponse)
async def get_system_metrics():
    """Get overall system metrics"""
    
    # Gather metrics from various components
    event_metrics = event_bus.get_metrics()
    insight_metrics = insight_engine.get_metrics()
    action_metrics = proactive_manager.get_metrics()
    
    # Calculate system health score (0-100)
    system_health = 100.0
    
    # Deduct for errors
    error_rate = event_metrics.get("errors", 0) / max(event_metrics.get("events_processed", 1), 1)
    system_health -= min(error_rate * 100, 30)
    
    # Deduct for failed actions
    if action_metrics["actions_executed"] > 0:
        failure_rate = action_metrics["actions_failed"] / action_metrics["actions_executed"]
        system_health -= min(failure_rate * 50, 30)
    
    # Deduct for large queues
    queue_size = event_metrics.get("queue_size", 0)
    if queue_size > 1000:
        system_health -= 10
    elif queue_size > 500:
        system_health -= 5
    
    system_health = max(0, min(100, system_health))
    
    return SystemMetricsResponse(
        events_processed=event_metrics.get("events_processed", 0),
        patterns_detected=event_metrics.get("patterns_detected", 0),
        insights_generated=insight_metrics.get("insights_generated", 0),
        actions_executed=action_metrics.get("actions_executed", 0),
        actions_completed=action_metrics.get("actions_completed", 0),
        actions_failed=action_metrics.get("actions_failed", 0),
        system_health=system_health,
        queue_sizes={
            "events": event_metrics.get("queue_size", 0),
            "actions": action_metrics.get("queue_size", 0)
        },
        active_rules=insight_metrics.get("active_rules", 0),
        active_policies=action_metrics.get("active_policies", 0)
    )


# ===================== WebSocket for Real-Time Updates =====================

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                # Connection might be closed
                pass


manager = ConnectionManager()


@router.websocket("/ws/coach")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    
    try:
        # Send initial metrics
        metrics = await get_system_metrics()
        await websocket.send_json({
            "type": "metrics",
            "payload": metrics.dict()
        })
        
        # Subscribe to insights
        async def handle_insight(insight: Insight):
            await websocket.send_json({
                "type": "insight",
                "payload": {
                    "id": insight.id,
                    "type": insight.type,
                    "severity": insight.severity,
                    "title": insight.title,
                    "description": insight.description,
                    "recommendations": insight.recommendations,
                    "metrics": insight.metrics,
                    "timestamp": insight.timestamp.isoformat(),
                    "confidence": insight.confidence,
                    "is_actionable": insight.is_actionable
                }
            })
        
        insight_engine.subscribe_to_insights(handle_insight)
        
        # Keep connection alive
        while True:
            # Send periodic metrics updates
            await asyncio.sleep(5)
            metrics = await get_system_metrics()
            await websocket.send_json({
                "type": "metrics",
                "payload": metrics.dict()
            })
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)