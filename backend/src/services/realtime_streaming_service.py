"""
Real-time Streaming Service
WebSocket and Server-Sent Events for live project updates and agent conversations
"""

import asyncio
import json
import redis.asyncio as redis
from datetime import datetime
from typing import Dict, List, Any, Optional, AsyncGenerator, Set
from uuid import UUID
import structlog

from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy import select

from ..core.config import get_settings
from ..core.database import get_async_session
from ..models.project_orchestration import (
    ProjectOrchestration, JourneyStage
)

logger = structlog.get_logger()


class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        # Active connections by orchestration ID
        self.connections: Dict[str, Set[WebSocket]] = {}
        # Connection metadata
        self.connection_info: Dict[WebSocket, Dict[str, Any]] = {}
        
    async def connect(self, websocket: WebSocket, orchestration_id: str, user_id: Optional[str] = None):
        """Accept new WebSocket connection"""
        await websocket.accept()
        
        if orchestration_id not in self.connections:
            self.connections[orchestration_id] = set()
        
        self.connections[orchestration_id].add(websocket)
        self.connection_info[websocket] = {
            "orchestration_id": orchestration_id,
            "user_id": user_id,
            "connected_at": datetime.utcnow(),
            "last_activity": datetime.utcnow()
        }
        
        logger.info("WebSocket connected", 
                   orchestration_id=orchestration_id, 
                   user_id=user_id,
                   total_connections=len(self.connections.get(orchestration_id, [])))
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        if websocket in self.connection_info:
            orchestration_id = self.connection_info[websocket]["orchestration_id"]
            user_id = self.connection_info[websocket].get("user_id")
            
            # Remove from connections
            if orchestration_id in self.connections:
                self.connections[orchestration_id].discard(websocket)
                if not self.connections[orchestration_id]:
                    del self.connections[orchestration_id]
            
            # Remove connection info
            del self.connection_info[websocket]
            
            logger.info("WebSocket disconnected",
                       orchestration_id=orchestration_id,
                       user_id=user_id,
                       remaining_connections=len(self.connections.get(orchestration_id, [])))
    
    async def send_to_orchestration(self, orchestration_id: str, message: Dict[str, Any]):
        """Send message to all connections for an orchestration"""
        if orchestration_id not in self.connections:
            return
        
        disconnected = []
        message_json = json.dumps(message)
        
        for websocket in self.connections[orchestration_id].copy():
            try:
                await websocket.send_text(message_json)
                # Update last activity
                if websocket in self.connection_info:
                    self.connection_info[websocket]["last_activity"] = datetime.utcnow()
            except WebSocketDisconnect:
                disconnected.append(websocket)
            except Exception as e:
                logger.error("Failed to send WebSocket message", error=str(e))
                disconnected.append(websocket)
        
        # Clean up disconnected websockets
        for websocket in disconnected:
            self.disconnect(websocket)
    
    async def send_to_user(self, orchestration_id: str, user_id: str, message: Dict[str, Any]):
        """Send message to specific user's connections"""
        if orchestration_id not in self.connections:
            return
        
        message_json = json.dumps(message)
        
        for websocket in self.connections[orchestration_id]:
            if (websocket in self.connection_info and 
                self.connection_info[websocket].get("user_id") == user_id):
                try:
                    await websocket.send_text(message_json)
                except (WebSocketDisconnect, Exception):
                    self.disconnect(websocket)
    
    def get_connection_count(self, orchestration_id: str) -> int:
        """Get number of active connections for orchestration"""
        return len(self.connections.get(orchestration_id, []))
    
    def get_connected_users(self, orchestration_id: str) -> List[str]:
        """Get list of connected user IDs for orchestration"""
        if orchestration_id not in self.connections:
            return []
        
        users = set()
        for websocket in self.connections[orchestration_id]:
            if websocket in self.connection_info:
                user_id = self.connection_info[websocket].get("user_id")
                if user_id:
                    users.add(user_id)
        
        return list(users)


class RealtimeStreamingService:
    """
    Real-time streaming service for PM orchestration updates
    Handles WebSocket connections, Redis pub/sub, and SSE streams
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.connection_manager = ConnectionManager()
        self.redis_client: Optional[redis.Redis] = None
        self.subscribers: Dict[str, asyncio.Task] = {}
        
    async def initialize(self):
        """Initialize Redis connection and pub/sub"""
        try:
            self.redis_client = redis.Redis(
                host=getattr(self.settings, 'REDIS_HOST', 'localhost'),
                port=getattr(self.settings, 'REDIS_PORT', 6379),
                db=getattr(self.settings, 'REDIS_DB', 0),
                decode_responses=True
            )
            
            # Test connection
            await self.redis_client.ping()
            logger.info("Redis connection established for streaming service")
            
        except Exception as e:
            logger.error("Failed to connect to Redis", error=str(e))
            # Fallback to in-memory streaming without persistence
            self.redis_client = None
    
    async def publish_orchestration_update(
        self,
        orchestration_id: str,
        update_type: str,
        data: Dict[str, Any],
        target_user: Optional[str] = None
    ):
        """Publish orchestration update to all subscribers"""
        
        message = {
            "type": "orchestration_update",
            "orchestration_id": orchestration_id,
            "update_type": update_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
            "sequence_number": await self._get_sequence_number(orchestration_id)
        }
        
        # Send via WebSocket
        if target_user:
            await self.connection_manager.send_to_user(orchestration_id, target_user, message)
        else:
            await self.connection_manager.send_to_orchestration(orchestration_id, message)
        
        # Publish to Redis for persistence and cross-instance communication
        if self.redis_client:
            channel = f"orchestration:{orchestration_id}"
            try:
                await self.redis_client.publish(channel, json.dumps(message))
            except Exception as e:
                logger.error("Failed to publish to Redis", error=str(e))
    
    async def publish_agent_conversation(
        self,
        orchestration_id: str,
        conversation_id: str,
        participant: str,
        message_content: str,
        message_type: str = "text",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Publish agent conversation update"""
        
        message = {
            "type": "agent_conversation",
            "orchestration_id": orchestration_id,
            "conversation_id": conversation_id,
            "participant": participant,
            "message_type": message_type,
            "content": message_content,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.connection_manager.send_to_orchestration(orchestration_id, message)
        
        # Publish to Redis
        if self.redis_client:
            channel = f"conversation:{conversation_id}"
            try:
                await self.redis_client.publish(channel, json.dumps(message))
            except Exception as e:
                logger.error("Failed to publish conversation to Redis", error=str(e))
    
    async def publish_metrics_update(
        self,
        orchestration_id: str,
        metrics: Dict[str, Any]
    ):
        """Publish real-time metrics update"""
        
        await self.publish_orchestration_update(
            orchestration_id=orchestration_id,
            update_type="metrics",
            data={
                "metrics": metrics,
                "updated_fields": list(metrics.keys())
            }
        )
    
    async def publish_stage_transition(
        self,
        orchestration_id: str,
        from_stage: Optional[JourneyStage],
        to_stage: JourneyStage,
        transition_reason: str
    ):
        """Publish journey stage transition"""
        
        await self.publish_orchestration_update(
            orchestration_id=orchestration_id,
            update_type="stage_transition",
            data={
                "from_stage": from_stage.value if from_stage else None,
                "to_stage": to_stage.value,
                "transition_reason": transition_reason,
                "transition_time": datetime.utcnow().isoformat()
            }
        )
    
    async def publish_touchpoint_created(
        self,
        orchestration_id: str,
        touchpoint_data: Dict[str, Any]
    ):
        """Publish new touchpoint creation"""
        
        await self.publish_orchestration_update(
            orchestration_id=orchestration_id,
            update_type="touchpoint_created",
            data=touchpoint_data
        )
    
    async def publish_agent_assignment(
        self,
        orchestration_id: str,
        agent_name: str,
        assignment_type: str,  # assigned, unassigned, role_changed
        assignment_data: Dict[str, Any]
    ):
        """Publish agent assignment change"""
        
        await self.publish_orchestration_update(
            orchestration_id=orchestration_id,
            update_type="agent_assignment",
            data={
                "agent_name": agent_name,
                "assignment_type": assignment_type,
                "assignment_data": assignment_data
            }
        )
    
    async def publish_cost_update(
        self,
        orchestration_id: str,
        cost_data: Dict[str, Any]
    ):
        """Publish cost tracking update"""
        
        await self.publish_orchestration_update(
            orchestration_id=orchestration_id,
            update_type="cost_update",
            data=cost_data
        )
    
    async def handle_websocket_connection(
        self,
        websocket: WebSocket,
        orchestration_id: str,
        user_id: Optional[str] = None
    ):
        """Handle WebSocket connection lifecycle"""
        
        await self.connection_manager.connect(websocket, orchestration_id, user_id)
        
        try:
            # Send initial connection confirmation
            await websocket.send_text(json.dumps({
                "type": "connection_established",
                "orchestration_id": orchestration_id,
                "timestamp": datetime.utcnow().isoformat(),
                "connection_count": self.connection_manager.get_connection_count(orchestration_id)
            }))
            
            # Send current orchestration state
            await self._send_current_state(websocket, orchestration_id)
            
            # Keep connection alive and handle incoming messages
            while True:
                try:
                    # Wait for messages from client
                    message = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                    await self._handle_client_message(websocket, orchestration_id, message)
                    
                except asyncio.TimeoutError:
                    # Send heartbeat
                    await websocket.send_text(json.dumps({
                        "type": "heartbeat",
                        "timestamp": datetime.utcnow().isoformat()
                    }))
                    
        except WebSocketDisconnect:
            logger.info("WebSocket disconnected normally", orchestration_id=orchestration_id)
        except Exception as e:
            logger.error("WebSocket connection error", error=str(e), orchestration_id=orchestration_id)
        finally:
            self.connection_manager.disconnect(websocket)
    
    async def generate_sse_stream(
        self,
        orchestration_id: str,
        user_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """Generate Server-Sent Events stream"""
        
        # Send initial connection event
        yield f"data: {json.dumps({'type': 'connected', 'orchestration_id': orchestration_id, 'timestamp': datetime.utcnow().isoformat()})}\n\n"
        
        # Subscribe to Redis updates if available
        if self.redis_client:
            pubsub = self.redis_client.pubsub()
            await pubsub.subscribe(f"orchestration:{orchestration_id}")
            
            try:
                async for message in pubsub.listen():
                    if message["type"] == "message":
                        try:
                            data = json.loads(message["data"])
                            yield f"data: {json.dumps(data)}\n\n"
                        except json.JSONDecodeError:
                            continue
            except Exception as e:
                logger.error("SSE stream error", error=str(e))
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
            finally:
                await pubsub.unsubscribe(f"orchestration:{orchestration_id}")
                await pubsub.close()
        else:
            # Fallback: periodic state updates without Redis
            while True:
                try:
                    await asyncio.sleep(5)  # Send updates every 5 seconds
                    yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': datetime.utcnow().isoformat()})}\n\n"
                except Exception as e:
                    logger.error("SSE heartbeat error", error=str(e))
                    break
    
    async def _send_current_state(self, websocket: WebSocket, orchestration_id: str):
        """Send current orchestration state to newly connected client"""
        
        try:
            async with get_async_session() as db:
                # Get orchestration with current state
                stmt = select(ProjectOrchestration).where(
                    ProjectOrchestration.id == UUID(orchestration_id)
                )
                result = await db.execute(stmt)
                orchestration = result.scalar_one_or_none()
                
                if orchestration:
                    current_state = {
                        "type": "current_state",
                        "orchestration_status": orchestration.orchestration_status.value,
                        "current_stage": orchestration.current_stage.value,
                        "ai_efficiency_score": orchestration.ai_efficiency_score,
                        "agent_collaboration_score": orchestration.agent_collaboration_score,
                        "satisfaction_score": orchestration.satisfaction_score,
                        "touchpoint_count": orchestration.touchpoint_count,
                        "last_updated": orchestration.updated_at.isoformat()
                    }
                    
                    await websocket.send_text(json.dumps(current_state))
                    
        except Exception as e:
            logger.error("Failed to send current state", error=str(e))
    
    async def _handle_client_message(
        self,
        websocket: WebSocket,
        orchestration_id: str,
        message: str
    ):
        """Handle incoming message from WebSocket client"""
        
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "subscribe_conversations":
                # Client wants to subscribe to specific conversation updates
                conversation_id = data.get("conversation_id")
                if conversation_id:
                    # Add subscription logic here
                    await websocket.send_text(json.dumps({
                        "type": "subscription_confirmed",
                        "subscription": "conversations",
                        "conversation_id": conversation_id
                    }))
            
            elif message_type == "request_metrics":
                # Client requesting current metrics
                await self._send_current_metrics(websocket, orchestration_id)
            
            elif message_type == "ping":
                # Client ping
                await websocket.send_text(json.dumps({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                }))
                
        except json.JSONDecodeError:
            logger.warning("Invalid JSON received from WebSocket client")
        except Exception as e:
            logger.error("Error handling client message", error=str(e))
    
    async def _send_current_metrics(self, websocket: WebSocket, orchestration_id: str):
        """Send current metrics to client"""
        
        # This would fetch and send current metrics
        # For now, send mock metrics
        metrics = {
            "type": "current_metrics",
            "orchestration_id": orchestration_id,
            "metrics": {
                "active_agents": 3,
                "completed_tasks": 15,
                "current_cost": 2500.0,
                "efficiency_score": 0.87
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await websocket.send_text(json.dumps(metrics))
    
    async def _get_sequence_number(self, orchestration_id: str) -> int:
        """Get next sequence number for orchestration updates"""
        
        if self.redis_client:
            try:
                key = f"seq:{orchestration_id}"
                return await self.redis_client.incr(key)
            except Exception:
                pass
        
        # Fallback to timestamp-based sequence
        return int(datetime.utcnow().timestamp() * 1000)
    
    async def cleanup(self):
        """Cleanup resources"""
        
        # Close all WebSocket connections
        for orchestration_id in list(self.connection_manager.connections.keys()):
            for websocket in list(self.connection_manager.connections[orchestration_id]):
                try:
                    await websocket.close()
                except Exception:
                    pass
        
        # Close Redis connection
        if self.redis_client:
            try:
                await self.redis_client.close()
            except Exception:
                pass
        
        logger.info("Realtime streaming service cleaned up")


# Global instance
realtime_service = RealtimeStreamingService()


async def get_realtime_service() -> RealtimeStreamingService:
    """Get the global realtime streaming service instance"""
    if realtime_service.redis_client is None:
        await realtime_service.initialize()
    return realtime_service


# Event publishing helpers for use in other services
async def publish_orchestration_update(orchestration_id: str, update_type: str, data: Dict[str, Any]):
    """Helper to publish orchestration updates"""
    service = await get_realtime_service()
    await service.publish_orchestration_update(orchestration_id, update_type, data)


async def publish_agent_conversation(
    orchestration_id: str,
    conversation_id: str,
    participant: str,
    message_content: str,
    message_type: str = "text"
):
    """Helper to publish agent conversations"""
    service = await get_realtime_service()
    await service.publish_agent_conversation(
        orchestration_id, conversation_id, participant, message_content, message_type
    )


async def publish_metrics_update(orchestration_id: str, metrics: Dict[str, Any]):
    """Helper to publish metrics updates"""
    service = await get_realtime_service()
    await service.publish_metrics_update(orchestration_id, metrics)