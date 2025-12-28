"""
WebSocket and SSE Endpoints for Real-time PM Orchestration
Provides real-time updates for project orchestration, agent conversations, and metrics
"""

from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
import structlog

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db_session
from ..services.realtime_streaming_service import get_realtime_service
from ..models.project_orchestration import ProjectOrchestration

logger = structlog.get_logger()

router = APIRouter(prefix="/api/v1/pm/realtime", tags=["PM Real-time"])


# ===================== WebSocket Endpoints =====================

@router.websocket("/projects/{orchestration_id}/ws")
async def websocket_orchestration_updates(
    websocket: WebSocket,
    orchestration_id: UUID,
    user_id: Optional[str] = Query(None, description="User ID for personalized updates")
):
    """
    🔌 WebSocket for Real-time Orchestration Updates
    
    Provides real-time updates for:
    - Orchestration status changes
    - Journey stage transitions  
    - Agent assignments and performance
    - Metrics and cost updates
    - Touchpoint creation
    """
    
    streaming_service = await get_realtime_service()
    
    try:
        # Verify orchestration exists
        async with get_db_session() as db:
            orchestration = await db.get(ProjectOrchestration, orchestration_id)
            if not orchestration:
                await websocket.close(code=4004, reason="Orchestration not found")
                return
        
        logger.info("WebSocket connection established", 
                   orchestration_id=str(orchestration_id), 
                   user_id=user_id)
        
        # Handle the connection
        await streaming_service.handle_websocket_connection(
            websocket=websocket,
            orchestration_id=str(orchestration_id),
            user_id=user_id
        )
        
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected", orchestration_id=str(orchestration_id))
    except Exception as e:
        logger.error("WebSocket error", error=str(e), orchestration_id=str(orchestration_id))
        try:
            await websocket.close(code=5000, reason="Internal server error")
        except Exception:
            pass


@router.websocket("/conversations/{conversation_id}/ws")
async def websocket_conversation_stream(
    websocket: WebSocket,
    conversation_id: str,
    user_id: Optional[str] = Query(None, description="User ID for authentication")
):
    """
    💬 WebSocket for Agent Conversation Streaming
    
    Streams real-time agent conversations within a project:
    - Agent messages and responses
    - Decision points and actions
    - Tool usage and results
    - Conversation metadata
    """
    
    await get_realtime_service()
    
    try:
        await websocket.accept()
        
        # Send connection confirmation
        await websocket.send_json({
            "type": "conversation_connected",
            "conversation_id": conversation_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info("Conversation WebSocket connected", 
                   conversation_id=conversation_id, 
                   user_id=user_id)
        
        # Keep connection alive and handle messages
        while True:
            try:
                # Listen for client messages or send periodic updates
                message = await websocket.receive_text()
                
                # Echo back for testing (in production, handle specific message types)
                await websocket.send_json({
                    "type": "echo",
                    "original_message": message,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error("Conversation WebSocket error", error=str(e))
                await websocket.send_json({
                    "type": "error",
                    "message": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                })
                
    except Exception as e:
        logger.error("Failed to establish conversation WebSocket", error=str(e))
        try:
            await websocket.close(code=5000, reason="Internal server error")
        except Exception:
            pass


@router.websocket("/agents/{agent_name}/ws")
async def websocket_agent_monitoring(
    websocket: WebSocket,
    agent_name: str,
    orchestration_id: Optional[UUID] = Query(None, description="Filter by orchestration ID")
):
    """
    🤖 WebSocket for Agent Performance Monitoring
    
    Provides real-time monitoring of specific agent:
    - Task assignments and completions
    - Performance metrics
    - Collaboration activities
    - Cost and efficiency tracking
    """
    
    try:
        await websocket.accept()
        
        logger.info("Agent monitoring WebSocket connected", 
                   agent_name=agent_name, 
                   orchestration_id=str(orchestration_id) if orchestration_id else "all")
        
        # Send initial agent status
        await websocket.send_json({
            "type": "agent_status",
            "agent_name": agent_name,
            "status": "monitoring_started",
            "orchestration_id": str(orchestration_id) if orchestration_id else None,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Simulate agent monitoring updates
        import asyncio
        while True:
            await asyncio.sleep(10)  # Send updates every 10 seconds
            
            # Send mock agent performance update
            await websocket.send_json({
                "type": "agent_performance_update",
                "agent_name": agent_name,
                "metrics": {
                    "tasks_in_progress": 2,
                    "efficiency_score": 0.87,
                    "last_activity": datetime.utcnow().isoformat()
                },
                "timestamp": datetime.utcnow().isoformat()
            })
            
    except WebSocketDisconnect:
        logger.info("Agent monitoring WebSocket disconnected", agent_name=agent_name)
    except Exception as e:
        logger.error("Agent monitoring WebSocket error", error=str(e), agent_name=agent_name)


# ===================== Server-Sent Events Endpoints =====================

@router.get("/projects/{orchestration_id}/stream")
async def stream_orchestration_events(
    orchestration_id: UUID,
    user_id: Optional[str] = Query(None, description="User ID for personalized events"),
    db: AsyncSession = Depends(get_db_session)
):
    """
    📡 Server-Sent Events for Orchestration Updates
    
    Provides SSE stream for real-time orchestration updates.
    Compatible with EventSource API in browsers.
    """
    
    # Verify orchestration exists
    orchestration = await db.get(ProjectOrchestration, orchestration_id)
    if not orchestration:
        raise HTTPException(status_code=404, detail="Orchestration not found")
    
    streaming_service = await get_realtime_service()
    
    logger.info("SSE stream started", 
               orchestration_id=str(orchestration_id), 
               user_id=user_id)
    
    return StreamingResponse(
        streaming_service.generate_sse_stream(
            orchestration_id=str(orchestration_id),
            user_id=user_id
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control",
            "Access-Control-Allow-Methods": "GET, OPTIONS"
        }
    )


@router.get("/metrics/stream")
async def stream_global_metrics():
    """
    📊 Global Metrics Stream
    
    Streams real-time metrics across all active orchestrations:
    - System-wide performance metrics
    - Agent utilization statistics
    - Cost tracking summaries
    - Alert notifications
    """
    
    async def generate_global_metrics():
        """Generate global metrics stream"""
        
        # Send initial connection event
        yield f"data: {{'type': 'connected', 'timestamp': '{datetime.utcnow().isoformat()}'}}\n\n"
        
        # Send periodic global metrics
        import asyncio
        counter = 0
        
        while True:
            try:
                await asyncio.sleep(15)  # Update every 15 seconds
                counter += 1
                
                # Mock global metrics
                metrics = {
                    "type": "global_metrics",
                    "data": {
                        "active_orchestrations": 5,
                        "total_agents": 12,
                        "avg_efficiency": 0.84,
                        "total_cost_today": 15750.00,
                        "system_health": "excellent"
                    },
                    "sequence": counter,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                yield f"data: {metrics}\n\n"
                
            except Exception as e:
                error_msg = {
                    "type": "error",
                    "message": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
                yield f"data: {error_msg}\n\n"
                break
    
    return StreamingResponse(
        generate_global_metrics(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*"
        }
    )


# ===================== Real-time Control Endpoints =====================

@router.post("/projects/{orchestration_id}/broadcast")
async def broadcast_message(
    orchestration_id: UUID,
    message_data: Dict[str, Any],
    target_user: Optional[str] = Query(None, description="Target specific user"),
    db: AsyncSession = Depends(get_db_session)
):
    """
    📢 Broadcast Message to Connected Clients
    
    Sends a custom message to all connected clients for an orchestration.
    Useful for manual notifications or system announcements.
    """
    
    # Verify orchestration exists
    orchestration = await db.get(ProjectOrchestration, orchestration_id)
    if not orchestration:
        raise HTTPException(status_code=404, detail="Orchestration not found")
    
    streaming_service = await get_realtime_service()
    
    # Broadcast the message
    await streaming_service.publish_orchestration_update(
        orchestration_id=str(orchestration_id),
        update_type="custom_broadcast",
        data=message_data,
        target_user=target_user
    )
    
    logger.info("Message broadcasted", 
               orchestration_id=str(orchestration_id), 
               target_user=target_user,
               message_type=message_data.get("type", "unknown"))
    
    return {
        "success": True,
        "orchestration_id": str(orchestration_id),
        "message_type": message_data.get("type", "custom"),
        "target_user": target_user,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/projects/{orchestration_id}/connections")
async def get_active_connections(
    orchestration_id: UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """
    🔗 Get Active Connections Info
    
    Returns information about currently active WebSocket connections
    for an orchestration.
    """
    
    # Verify orchestration exists
    orchestration = await db.get(ProjectOrchestration, orchestration_id)
    if not orchestration:
        raise HTTPException(status_code=404, detail="Orchestration not found")
    
    streaming_service = await get_realtime_service()
    
    connection_count = streaming_service.connection_manager.get_connection_count(str(orchestration_id))
    connected_users = streaming_service.connection_manager.get_connected_users(str(orchestration_id))
    
    return {
        "orchestration_id": str(orchestration_id),
        "active_connections": connection_count,
        "connected_users": connected_users,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/test/simulate-update")
async def simulate_orchestration_update(
    orchestration_id: UUID,
    update_type: str = Query("test", description="Type of update to simulate"),
    db: AsyncSession = Depends(get_db_session)
):
    """
    🧪 Simulate Orchestration Update (Testing)
    
    Simulates various types of orchestration updates for testing
    the real-time streaming functionality.
    """
    
    # Verify orchestration exists
    orchestration = await db.get(ProjectOrchestration, orchestration_id)
    if not orchestration:
        raise HTTPException(status_code=404, detail="Orchestration not found")
    
    streaming_service = await get_realtime_service()
    
    # Generate different types of test updates
    test_data = {}
    
    if update_type == "stage_transition":
        test_data = {
            "from_stage": "planning",
            "to_stage": "execution", 
            "transition_reason": "Planning phase completed successfully",
            "transition_time": datetime.utcnow().isoformat()
        }
    
    elif update_type == "agent_assignment":
        test_data = {
            "agent_name": "test-agent",
            "assignment_type": "assigned",
            "role": "contributor",
            "reason": "Additional expertise required"
        }
    
    elif update_type == "metrics":
        test_data = {
            "metrics": {
                "efficiency_score": 0.92,
                "collaboration_score": 0.88,
                "cost_incurred": 1250.50
            },
            "updated_fields": ["efficiency_score", "collaboration_score", "cost_incurred"]
        }
    
    elif update_type == "touchpoint":
        test_data = {
            "touchpoint_type": "status_update",
            "title": "Weekly Progress Review",
            "participants": ["ali-chief-of-staff", "client-pm"],
            "satisfaction_score": 0.89
        }
    
    else:
        test_data = {
            "message": f"Test update of type: {update_type}",
            "test_data": True
        }
    
    # Publish the test update
    await streaming_service.publish_orchestration_update(
        orchestration_id=str(orchestration_id),
        update_type=update_type,
        data=test_data
    )
    
    logger.info("Test update simulated", 
               orchestration_id=str(orchestration_id), 
               update_type=update_type)
    
    return {
        "success": True,
        "orchestration_id": str(orchestration_id),
        "update_type": update_type,
        "test_data": test_data,
        "timestamp": datetime.utcnow().isoformat()
    }


# ===================== Health and Status Endpoints =====================

@router.get("/health")
async def get_realtime_health():
    """
    💚 Real-time Service Health Check
    
    Returns the health status of the real-time streaming service,
    including Redis connectivity and active connections.
    """
    
    try:
        streaming_service = await get_realtime_service()
        
        # Check Redis connectivity
        redis_status = "connected" if streaming_service.redis_client else "disconnected"
        
        # Get connection statistics
        total_connections = sum(
            len(connections) 
            for connections in streaming_service.connection_manager.connections.values()
        )
        
        active_orchestrations = len(streaming_service.connection_manager.connections)
        
        health_status = {
            "status": "healthy",
            "redis_status": redis_status,
            "total_connections": total_connections,
            "active_orchestrations": active_orchestrations,
            "service_uptime": "running",  # Could calculate actual uptime
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info("Health check performed", **health_status)
        return health_status
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }