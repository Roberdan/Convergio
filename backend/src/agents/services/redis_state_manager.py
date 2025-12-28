"""
CONVERGIO 2029 - REDIS STATE MANAGER
AutoGen conversation state management with Redis
"""

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import redis.asyncio as redis
import structlog
from redis.asyncio import ConnectionPool

logger = structlog.get_logger()


class RedisStateManager:
    """Redis-based state management for AutoGen conversations."""
    
    def __init__(self, redis_url: str, ttl_seconds: int = 3600):
        """Initialize Redis state manager."""
        self.redis_url = redis_url
        self.ttl_seconds = ttl_seconds
        self.pool: Optional[ConnectionPool] = None
        self.redis_client: Optional[redis.Redis] = None
        
    async def initialize(self) -> None:
        """Initialize Redis connection."""
        try:
            self.pool = ConnectionPool.from_url(
                self.redis_url,
                max_connections=20,
                decode_responses=True
            )
            self.redis_client = redis.Redis(connection_pool=self.pool)
            
            # Test connection
            await self.redis_client.ping()
            logger.info("Redis connection established", url=self.redis_url)
            
        except Exception as e:
            logger.error("Failed to initialize Redis", error=str(e))
            raise
    
    async def close(self) -> None:
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.aclose()
        if self.pool:
            await self.pool.aclose()
        logger.info("Redis connection closed")
    
    async def health_check(self) -> bool:
        """Check Redis health."""
        try:
            if not self.redis_client:
                return False
            await self.redis_client.ping()
            return True
        except Exception as e:
            logger.error("Redis health check failed", error=str(e))
            return False
    
    # Conversation State Management
    
    async def create_conversation(self, user_id: str, agent_type: str) -> str:
        """Create a new conversation."""
        conversation_id = str(uuid.uuid4())
        
        conversation_data = {
            "conversation_id": conversation_id,
            "user_id": user_id,
            "agent_type": agent_type,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "status": "active",
            "messages": [],
            "metadata": {
                "total_tokens": 0,
                "total_cost_usd": 0.0,
                "turn_count": 0
            }
        }
        
        # Store conversation
        await self._set_conversation(conversation_id, conversation_data)
        
        # Add to user's conversation list
        await self._add_to_user_conversations(user_id, conversation_id)
        
        logger.info(
            "Conversation created",
            conversation_id=conversation_id,
            user_id=user_id,
            agent_type=agent_type
        )
        
        return conversation_id
    
    async def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation by ID."""
        try:
            data = await self.redis_client.get(f"conversation:{conversation_id}")
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error("Failed to get conversation", error=str(e), conversation_id=conversation_id)
            return None
    
    async def update_conversation(
        self,
        conversation_id: str,
        message: str,
        response: str,
        role: str = "user",
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update conversation with new message and response."""
        conversation = await self.get_conversation(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        # Add user message
        conversation["messages"].append({
            "role": role,
            "content": message,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        })
        
        # Add agent response
        conversation["messages"].append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.utcnow().isoformat(),
            "agent_type": conversation["agent_type"],
            "metadata": metadata or {}
        })
        
        # Update conversation metadata
        conversation["updated_at"] = datetime.utcnow().isoformat()
        conversation["metadata"]["turn_count"] += 1
        
        if metadata:
            if "tokens_used" in metadata:
                conversation["metadata"]["total_tokens"] += metadata["tokens_used"]
            if "cost_usd" in metadata:
                conversation["metadata"]["total_cost_usd"] += metadata["cost_usd"]
        
        await self._set_conversation(conversation_id, conversation)
        
        logger.info(
            "Conversation updated",
            conversation_id=conversation_id,
            turn_count=conversation["metadata"]["turn_count"]
        )
    
    async def get_user_conversations(self, user_id: str, limit: int = 50) -> List[str]:
        """Get user's conversation IDs."""
        try:
            conversation_ids = await self.redis_client.lrange(
                f"user_conversations:{user_id}", 0, limit - 1
            )
            return conversation_ids or []
        except Exception as e:
            logger.error("Failed to get user conversations", error=str(e), user_id=user_id)
            return []
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation."""
        try:
            # Get conversation first to get user_id
            conversation = await self.get_conversation(conversation_id)
            if not conversation:
                return False
            
            user_id = conversation["user_id"]
            
            # Delete conversation data
            await self.redis_client.delete(f"conversation:{conversation_id}")
            
            # Remove from user's conversation list
            await self.redis_client.lrem(f"user_conversations:{user_id}", 0, conversation_id)
            
            logger.info("Conversation deleted", conversation_id=conversation_id)
            return True
            
        except Exception as e:
            logger.error("Failed to delete conversation", error=str(e), conversation_id=conversation_id)
            return False
    
    # Agent State Management
    
    async def save_agent_state(
        self,
        conversation_id: str,
        agent_name: str,
        state_data: Dict[str, Any]
    ) -> None:
        """Save agent state for a conversation."""
        key = f"agent_state:{conversation_id}:{agent_name}"
        state_data["updated_at"] = datetime.utcnow().isoformat()
        
        await self.redis_client.setex(
            key,
            self.ttl_seconds,
            json.dumps(state_data, default=str)
        )
        
        logger.debug(
            "Agent state saved",
            conversation_id=conversation_id,
            agent_name=agent_name
        )
    
    async def get_agent_state(
        self,
        conversation_id: str,
        agent_name: str
    ) -> Optional[Dict[str, Any]]:
        """Get agent state for a conversation."""
        try:
            key = f"agent_state:{conversation_id}:{agent_name}"
            data = await self.redis_client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(
                "Failed to get agent state",
                error=str(e),
                conversation_id=conversation_id,
                agent_name=agent_name
            )
            return None
    
    # Cost Tracking
    
    async def track_cost(
        self,
        conversation_id: str,
        model: str,
        tokens_used: int,
        cost_usd: float
    ) -> None:
        """Track conversation costs."""
        cost_data = {
            "conversation_id": conversation_id,
            "model": model,
            "tokens_used": tokens_used,
            "cost_usd": cost_usd,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Store individual cost record
        key = f"cost:{conversation_id}:{datetime.utcnow().isoformat()}"
        await self.redis_client.setex(
            key,
            self.ttl_seconds,
            json.dumps(cost_data)
        )
        
        # Update daily cost aggregate
        today = datetime.utcnow().strftime("%Y-%m-%d")
        daily_key = f"daily_cost:{today}"
        
        await self.redis_client.hincrby(daily_key, "total_tokens", tokens_used)
        await self.redis_client.hincrbyfloat(daily_key, "total_cost_usd", cost_usd)
        await self.redis_client.expire(daily_key, 86400 * 7)  # Keep for 7 days
        
        logger.debug(
            "Cost tracked",
            conversation_id=conversation_id,
            cost_usd=cost_usd,
            tokens_used=tokens_used
        )
    
    async def get_daily_cost_summary(self, date: Optional[str] = None) -> Dict[str, Any]:
        """Get daily cost summary."""
        if not date:
            date = datetime.utcnow().strftime("%Y-%m-%d")
        
        key = f"daily_cost:{date}"
        summary = await self.redis_client.hgetall(key)
        
        return {
            "date": date,
            "total_tokens": int(summary.get("total_tokens", 0)),
            "total_cost_usd": float(summary.get("total_cost_usd", 0.0))
        }
    
    # Helper methods
    
    async def _set_conversation(self, conversation_id: str, data: Dict[str, Any]) -> None:
        """Set conversation data with TTL."""
        await self.redis_client.setex(
            f"conversation:{conversation_id}",
            self.ttl_seconds,
            json.dumps(data, default=str)
        )
    
    async def _add_to_user_conversations(self, user_id: str, conversation_id: str) -> None:
        """Add conversation to user's list."""
        await self.redis_client.lpush(f"user_conversations:{user_id}", conversation_id)
        await self.redis_client.expire(f"user_conversations:{user_id}", self.ttl_seconds)
    
    # Cache Management
    
    async def store_conversation(self, conversation_id: str, conversation_data: Dict[str, Any]) -> None:
        """Store conversation data in Redis."""
        try:
            if not self.redis_client:
                raise RuntimeError("Redis client not initialized")
            
            # Store conversation data
            key = f"conversation:{conversation_id}"
            await self.redis_client.setex(
                key,
                self.ttl_seconds,
                json.dumps(conversation_data, default=str)
            )
            
            logger.info("Conversation stored", conversation_id=conversation_id)
            
        except Exception as e:
            logger.error("Failed to store conversation", error=str(e))
            raise

    async def clear_expired_conversations(self) -> int:
        """Clear expired conversations (cleanup task)."""
        try:
            # Get all conversation keys
            keys = await self.redis_client.keys("conversation:*")
            expired_count = 0
            
            for key in keys:
                ttl = await self.redis_client.ttl(key)
                if ttl == -1:  # No TTL set
                    await self.redis_client.expire(key, self.ttl_seconds)
                elif ttl == -2:  # Key doesn't exist
                    expired_count += 1
            
            logger.info("Cleanup completed", expired_conversations=expired_count)
            return expired_count
            
        except Exception as e:
            logger.error("Failed to cleanup conversations", error=str(e))
            return 0