"""
WebSocket connection management for agents
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import structlog
from fastapi import WebSocket

logger = structlog.get_logger()


class ConnectionManager:
    """Manages WebSocket connections for agent communication"""
    
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
    
    async def connect(
        self, 
        websocket: WebSocket, 
        client_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Accept and track a new WebSocket connection"""
        await websocket.accept()
        
        if client_id not in self.active_connections:
            self.active_connections[client_id] = []
        
        self.active_connections[client_id].append(websocket)
        
        # Store metadata
        self.connection_metadata[websocket] = {
            "client_id": client_id,
            "connected_at": datetime.now().isoformat(),
            **(metadata or {})
        }
        
        logger.info(f"✅ WebSocket connected: {client_id}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        # Find and remove from active connections
        for client_id, connections in self.active_connections.items():
            if websocket in connections:
                connections.remove(websocket)
                
                # Clean up empty lists
                if not connections:
                    del self.active_connections[client_id]
                
                logger.info(f"❌ WebSocket disconnected: {client_id}")
                break
        
        # Remove metadata
        if websocket in self.connection_metadata:
            del self.connection_metadata[websocket]
    
    async def send_message(
        self,
        websocket: WebSocket,
        message: Dict[str, Any]
    ):
        """Send a message to a specific WebSocket"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            self.disconnect(websocket)
    
    async def send_to_client(
        self,
        client_id: str,
        message: Dict[str, Any]
    ):
        """Send a message to all connections for a client"""
        if client_id in self.active_connections:
            disconnected = []
            
            for websocket in self.active_connections[client_id]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to send to client {client_id}: {e}")
                    disconnected.append(websocket)
            
            # Clean up disconnected sockets
            for ws in disconnected:
                self.disconnect(ws)
    
    async def broadcast(
        self,
        message: Dict[str, Any],
        exclude: Optional[List[str]] = None
    ):
        """Broadcast a message to all connected clients"""
        exclude = exclude or []
        
        for client_id, connections in self.active_connections.items():
            if client_id not in exclude:
                await self.send_to_client(client_id, message)
    
    def get_active_clients(self) -> List[str]:
        """Get list of active client IDs"""
        return list(self.active_connections.keys())
    
    def get_connection_count(self) -> int:
        """Get total number of active connections"""
        return sum(len(conns) for conns in self.active_connections.values())
    
    def get_client_metadata(self, client_id: str) -> List[Dict[str, Any]]:
        """Get metadata for all connections of a client"""
        metadata = []
        
        if client_id in self.active_connections:
            for ws in self.active_connections[client_id]:
                if ws in self.connection_metadata:
                    metadata.append(self.connection_metadata[ws])
        
        return metadata


# Global connection manager instance
connection_manager = ConnectionManager()


class StreamingManager:
    """Manages streaming responses for agent conversations"""
    
    def __init__(self):
        self.active_streams: Dict[str, Dict[str, Any]] = {}
    
    async def start_stream(
        self,
        stream_id: str,
        websocket: WebSocket,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Start a new streaming session"""
        self.active_streams[stream_id] = {
            "websocket": websocket,
            "started_at": datetime.now().isoformat(),
            "chunks_sent": 0,
            "metadata": metadata or {}
        }
        
        logger.info(f"🔄 Stream started: {stream_id}")
    
    async def send_chunk(
        self,
        stream_id: str,
        chunk: str,
        agent_name: Optional[str] = None
    ):
        """Send a chunk of streaming response"""
        if stream_id not in self.active_streams:
            logger.warning(f"Stream not found: {stream_id}")
            return
        
        stream = self.active_streams[stream_id]
        
        try:
            message = {
                "type": "chunk",
                "content": chunk,
                "agent": agent_name,
                "chunk_index": stream["chunks_sent"]
            }
            
            await stream["websocket"].send_json(message)
            stream["chunks_sent"] += 1
            
        except Exception as e:
            logger.error(f"Failed to send chunk: {e}")
            await self.end_stream(stream_id, error=str(e))
    
    async def end_stream(
        self,
        stream_id: str,
        complete: bool = True,
        error: Optional[str] = None
    ):
        """End a streaming session"""
        if stream_id not in self.active_streams:
            return
        
        stream = self.active_streams[stream_id]
        
        try:
            message = {
                "type": "complete" if complete else "error",
                "chunks_sent": stream["chunks_sent"],
                "duration": (
                    datetime.now() - 
                    datetime.fromisoformat(stream["started_at"])
                ).total_seconds()
            }
            
            if error:
                message["error"] = error
            
            await stream["websocket"].send_json(message)
            
        except Exception as e:
            logger.error(f"Failed to end stream: {e}")
        
        finally:
            del self.active_streams[stream_id]
            logger.info(f"✅ Stream ended: {stream_id}")
    
    def get_active_streams(self) -> List[str]:
        """Get list of active stream IDs"""
        return list(self.active_streams.keys())


# Global streaming manager instance
streaming_manager = StreamingManager()