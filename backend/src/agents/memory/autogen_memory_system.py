"""
🧠 AutoGen Memory System - Persistent Conversation Memory & RAG Integration
Complete memory management for AutoGen agents with Redis persistence and vector embeddings
"""

import json
import asyncio
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

import structlog
import redis.asyncio as redis

# AutoGen imports with fallback
try:
    from autogen_agentchat.messages import TextMessage
    AUTOGEN_AVAILABLE = True
except ImportError:
    # Fallback TextMessage class when autogen is not available
    class TextMessage:
        """Fallback TextMessage class for when AutoGen is not installed"""
        def __init__(self, content: str = "", source: str = "", id: str = "", created_at=None):
            self.content = content
            self.source = source
            self.id = id or str(hash(content))[:8]
            self.created_at = created_at
    AUTOGEN_AVAILABLE = False

from ..tools.vector_search_client import embed_text, search_similar
from src.core.redis import get_redis_client

logger = structlog.get_logger()


class MemoryType(Enum):
    """Types of memory storage"""
    CONVERSATION = "conversation"    # Full conversation history
    CONTEXT = "context"             # Important context/facts
    KNOWLEDGE = "knowledge"         # Learned knowledge
    RELATIONSHIPS = "relationships" # Agent-to-agent interactions
    PREFERENCES = "preferences"     # User preferences and patterns


@dataclass
class MemoryEntry:
    """Individual memory entry with metadata"""
    id: str
    memory_type: MemoryType
    content: str
    agent_id: str
    user_id: str
    conversation_id: str
    embedding: Optional[List[float]] = None
    importance_score: float = 0.5  # 0.0 to 1.0
    access_count: int = 0
    created_at: datetime = None
    last_accessed: datetime = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
        if self.last_accessed is None:
            self.last_accessed = self.created_at
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ConversationMemory:
    """Complete conversation memory with context"""
    conversation_id: str
    user_id: str
    agent_ids: List[str]
    messages: List[Dict[str, Any]]
    context_summary: str
    key_facts: List[str]
    sentiment_analysis: Dict[str, float]
    topic_tags: List[str]
    created_at: datetime
    last_updated: datetime
    total_tokens: int = 0
    total_cost: float = 0.0


class AutoGenMemorySystem:
    """Advanced memory system for AutoGen agents with RAG capabilities"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis = redis_client or get_redis_client()
        self.memory_retention_days = 30  # Keep memories for 30 days
        self.max_conversation_length = 100  # Max messages per conversation
        self.similarity_threshold = 0.8  # Threshold for memory relevance
        
        # Memory key prefixes
        self.CONVERSATION_PREFIX = "memory:conversation"
        self.CONTEXT_PREFIX = "memory:context"
        self.KNOWLEDGE_PREFIX = "memory:knowledge"
        self.USER_PROFILE_PREFIX = "memory:user_profile"
        
        logger.info("🧠 AutoGen Memory System initialized with Redis persistence")
    
    async def store_conversation_message(self, 
                                       conversation_id: str,
                                       agent_id: str,
                                       user_id: str,
                                       message: TextMessage,
                                       context: Dict[str, Any] = None) -> str:
        """Store a single conversation message with context"""
        
        memory_id = f"{conversation_id}:{message.id}"
        
        # Create memory entry
        memory_entry = MemoryEntry(
            id=memory_id,
            memory_type=MemoryType.CONVERSATION,
            content=message.content,
            agent_id=agent_id,
            user_id=user_id,
            conversation_id=conversation_id,
            importance_score=self._calculate_importance_score(message.content, context),
            metadata={
                "message_id": message.id,
                "source": message.source,
                "created_at": message.created_at.isoformat() if message.created_at else None,
                "context": context or {}
            }
        )
        
        # Generate embedding for semantic search
        try:
            memory_entry.embedding = await embed_text(message.content)
        except Exception as e:
            logger.warning("Failed to generate embedding for message", error=str(e))
        
        # Store in Redis
        await self._store_memory_entry(memory_entry)
        
        # Update conversation metadata
        await self._update_conversation_metadata(conversation_id, user_id, [agent_id])
        
        logger.debug("📝 Message stored in memory", 
                    conversation_id=conversation_id,
                    agent_id=agent_id,
                    memory_id=memory_id)
        
        return memory_id
    
    async def retrieve_relevant_context(self, 
                                      query: str,
                                      user_id: str,
                                      agent_id: str = None,
                                      limit: int = 5) -> List[MemoryEntry]:
        """Retrieve relevant context using semantic similarity"""
        
        # Generate query embedding
        query_embedding = await embed_text(query)
        
        # Search for relevant memories
        relevant_memories = []
        
        # Get user's conversation history
        conversation_keys = await self.redis.keys(f"{self.CONVERSATION_PREFIX}:{user_id}:*")
        
        for key in conversation_keys:
            memory_data = await self.redis.hgetall(key)
            if not memory_data:
                continue
            
            try:
                memory_entry = self._deserialize_memory_entry(memory_data)
                
                # Filter by agent if specified
                if agent_id and memory_entry.agent_id != agent_id:
                    continue
                
                # Calculate similarity if embedding exists
                if memory_entry.embedding:
                    similarity = self._calculate_similarity(query_embedding, memory_entry.embedding)
                    
                    if similarity >= self.similarity_threshold:
                        memory_entry.metadata["similarity_score"] = similarity
                        relevant_memories.append(memory_entry)
                        
                        # Update access count
                        memory_entry.access_count += 1
                        memory_entry.last_accessed = datetime.now(timezone.utc)
                        await self._store_memory_entry(memory_entry)
                        
            except Exception as e:
                logger.warning("Failed to process memory entry", key=key, error=str(e))
        
        # Sort by relevance (similarity * importance)
        relevant_memories.sort(
            key=lambda m: m.metadata.get("similarity_score", 0) * m.importance_score,
            reverse=True
        )
        
        logger.info("🔍 Retrieved relevant context",
                   query_length=len(query),
                   user_id=user_id,
                   relevant_count=len(relevant_memories[:limit]))
        
        return relevant_memories[:limit]
    
    async def store_learned_knowledge(self,
                                    agent_id: str,
                                    user_id: str,
                                    knowledge: str,
                                    topic: str,
                                    importance: float = 0.7) -> str:
        """Store learned knowledge that can be recalled later"""
        
        knowledge_id = f"knowledge_{hashlib.md5(knowledge.encode()).hexdigest()}"
        
        memory_entry = MemoryEntry(
            id=knowledge_id,
            memory_type=MemoryType.KNOWLEDGE,
            content=knowledge,
            agent_id=agent_id,
            user_id=user_id,
            conversation_id="",
            importance_score=importance,
            metadata={
                "topic": topic,
                "learned_from": "conversation_analysis"
            }
        )
        
        # Generate embedding
        try:
            memory_entry.embedding = await embed_text(knowledge)
        except Exception as e:
            logger.warning("Failed to generate embedding for knowledge", error=str(e))
        
        # Store in Redis
        knowledge_key = f"{self.KNOWLEDGE_PREFIX}:{user_id}:{knowledge_id}"
        await self.redis.hset(knowledge_key, mapping=self._serialize_memory_entry(memory_entry))
        await self.redis.expire(knowledge_key, timedelta(days=self.memory_retention_days))
        
        logger.info("📚 Stored learned knowledge",
                   agent_id=agent_id,
                   topic=topic,
                   importance=importance)
        
        return knowledge_id
    
    async def get_conversation_summary(self, conversation_id: str) -> Optional[ConversationMemory]:
        """Get complete conversation summary with analysis"""
        
        conversation_key = f"{self.CONVERSATION_PREFIX}:summary:{conversation_id}"
        conversation_data = await self.redis.hgetall(conversation_key)
        
        if not conversation_data:
            return None
        
        try:
            return ConversationMemory(
                conversation_id=conversation_data["conversation_id"],
                user_id=conversation_data["user_id"],
                agent_ids=json.loads(conversation_data["agent_ids"]),
                messages=json.loads(conversation_data["messages"]),
                context_summary=conversation_data["context_summary"],
                key_facts=json.loads(conversation_data["key_facts"]),
                sentiment_analysis=json.loads(conversation_data["sentiment_analysis"]),
                topic_tags=json.loads(conversation_data["topic_tags"]),
                created_at=datetime.fromisoformat(conversation_data["created_at"]),
                last_updated=datetime.fromisoformat(conversation_data["last_updated"]),
                total_tokens=int(conversation_data.get("total_tokens", 0)),
                total_cost=float(conversation_data.get("total_cost", 0.0))
            )
        except Exception as e:
            logger.error("Failed to deserialize conversation memory", error=str(e))
            return None
    
    async def update_user_preferences(self,
                                    user_id: str,
                                    preferences: Dict[str, Any],
                                    agent_id: str = None) -> None:
        """Update user preferences and interaction patterns"""
        
        profile_key = f"{self.USER_PROFILE_PREFIX}:{user_id}"
        
        # Get existing profile
        existing_profile = await self.redis.hgetall(profile_key)
        
        if existing_profile:
            current_prefs = json.loads(existing_profile.get("preferences", "{}"))
        else:
            current_prefs = {}
        
        # Merge preferences
        current_prefs.update(preferences)
        
        # Store updated profile
        profile_data = {
            "user_id": user_id,
            "preferences": json.dumps(current_prefs),
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "updated_by_agent": agent_id or "system"
        }
        
        await self.redis.hset(profile_key, mapping=profile_data)
        await self.redis.expire(profile_key, timedelta(days=self.memory_retention_days * 2))  # Keep longer
        
        logger.info("👤 Updated user preferences",
                   user_id=user_id,
                   preference_count=len(current_prefs))
    
    async def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Retrieve user preferences and patterns"""
        
        profile_key = f"{self.USER_PROFILE_PREFIX}:{user_id}"
        profile_data = await self.redis.hgetall(profile_key)
        
        if not profile_data:
            return {}
        
        try:
            return json.loads(profile_data.get("preferences", "{}"))
        except Exception as e:
            logger.warning("Failed to load user preferences", user_id=user_id, error=str(e))
            return {}
    
    async def retrieve_by_type(self,
                             user_id: str,
                             memory_type: MemoryType,
                             query: str = None,
                             limit: int = 5,
                             agent_id: str = None) -> List[MemoryEntry]:
        """Retrieve memories by type - required by RAG system"""
        
        try:
            # Get memories based on type
            if memory_type == MemoryType.CONVERSATION:
                # Use existing retrieve_relevant_context method
                if query:
                    return await self.retrieve_relevant_context(
                        query=query,
                        user_id=user_id, 
                        agent_id=agent_id,
                        limit=limit
                    )
                else:
                    # Return recent conversation memories
                    return await self._get_recent_memories(user_id, memory_type, limit, agent_id)
            
            elif memory_type == MemoryType.KNOWLEDGE:
                # Search knowledge base
                knowledge_memories = []
                knowledge_keys = await self.redis.keys(f"{self.KNOWLEDGE_PREFIX}:{user_id}:*")
                
                for key in knowledge_keys[:limit]:
                    memory_data = await self.redis.hgetall(key)
                    if memory_data:
                        try:
                            memory_entry = self._deserialize_memory_entry(memory_data)
                            if not agent_id or memory_entry.agent_id == agent_id:
                                knowledge_memories.append(memory_entry)
                        except Exception as e:
                            logger.warning("Failed to deserialize knowledge memory", key=key, error=str(e))
                
                return knowledge_memories[:limit]
            
            elif memory_type == MemoryType.RELATIONSHIPS:
                # Return relationship memories (simplified - just return conversation memories for now)
                return await self._get_recent_memories(user_id, MemoryType.CONVERSATION, limit, agent_id)
            
            elif memory_type == MemoryType.PREFERENCES:
                # Convert user preferences to memory entries
                preferences = await self.get_user_preferences(user_id)
                if not preferences:
                    return []
                
                pref_memory = MemoryEntry(
                    id=f"preferences_{user_id}",
                    memory_type=MemoryType.PREFERENCES,
                    content=json.dumps(preferences),
                    agent_id=agent_id or "system",
                    user_id=user_id,
                    conversation_id="preferences",
                    importance_score=0.8,
                    metadata={"type": "user_preferences"}
                )
                return [pref_memory]
            
            else:
                # Default case - return recent memories
                return await self._get_recent_memories(user_id, memory_type, limit, agent_id)
                
        except Exception as e:
            logger.error("Failed to retrieve memories by type", 
                        memory_type=memory_type.value,
                        user_id=user_id,
                        error=str(e))
            return []
    
    async def cleanup_old_memories(self) -> int:
        """Clean up old memories based on retention policy"""
        
        cleaned_count = 0
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=self.memory_retention_days)
        
        # Get all memory keys
        all_keys = await self.redis.keys("memory:*")
        
        for key in all_keys:
            try:
                memory_data = await self.redis.hgetall(key)
                if not memory_data:
                    continue
                
                created_at_str = memory_data.get("created_at")
                if not created_at_str:
                    continue
                
                created_at = datetime.fromisoformat(created_at_str)
                
                # Check if memory is old and low importance
                if created_at < cutoff_time:
                    importance = float(memory_data.get("importance_score", 0.5))
                    access_count = int(memory_data.get("access_count", 0))
                    
                    # Keep high-importance or frequently accessed memories longer
                    if importance < 0.3 and access_count < 5:
                        await self.redis.delete(key)
                        cleaned_count += 1
                        
            except Exception as e:
                logger.warning("Error during memory cleanup", key=key, error=str(e))
        
        logger.info("🧹 Memory cleanup completed", cleaned_memories=cleaned_count)
        return cleaned_count
    
    # Private helper methods
    
    def _calculate_importance_score(self, content: str, context: Dict[str, Any] = None) -> float:
        """Calculate importance score for memory entry"""
        
        base_score = 0.5
        
        # Content-based scoring
        important_keywords = ["important", "remember", "critical", "key", "essential"]
        for keyword in important_keywords:
            if keyword.lower() in content.lower():
                base_score += 0.1
        
        # Length-based scoring (longer content might be more important)
        if len(content) > 100:
            base_score += 0.1
        
        # Context-based scoring
        if context:
            if context.get("agent_name") == "ali_chief_of_staff":
                base_score += 0.2  # Ali's messages are more important
            
            if "error" in str(context).lower():
                base_score += 0.3  # Errors are important to remember
        
        return min(base_score, 1.0)
    
    def _calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between embeddings"""
        
        if not embedding1 or not embedding2:
            return 0.0
        
        try:
            # Simple dot product for cosine similarity
            dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
            magnitude1 = sum(a * a for a in embedding1) ** 0.5
            magnitude2 = sum(b * b for b in embedding2) ** 0.5
            
            if magnitude1 == 0 or magnitude2 == 0:
                return 0.0
            
            return dot_product / (magnitude1 * magnitude2)
        except Exception as e:
            logger.warning("Failed to calculate similarity", error=str(e))
            return 0.0
    
    async def _store_memory_entry(self, memory_entry: MemoryEntry) -> None:
        """Store memory entry in Redis"""
        
        key = f"{self.CONVERSATION_PREFIX}:{memory_entry.user_id}:{memory_entry.id}"
        data = self._serialize_memory_entry(memory_entry)
        
        await self.redis.hset(key, mapping=data)
        await self.redis.expire(key, timedelta(days=self.memory_retention_days))
    
    def _serialize_memory_entry(self, memory_entry: MemoryEntry) -> Dict[str, str]:
        """Serialize memory entry for Redis storage"""
        
        data = {
            "id": memory_entry.id,
            "memory_type": memory_entry.memory_type.value,
            "content": memory_entry.content,
            "agent_id": memory_entry.agent_id,
            "user_id": memory_entry.user_id,
            "conversation_id": memory_entry.conversation_id,
            "importance_score": str(memory_entry.importance_score),
            "access_count": str(memory_entry.access_count),
            "created_at": memory_entry.created_at.isoformat(),
            "last_accessed": memory_entry.last_accessed.isoformat(),
            "metadata": json.dumps(memory_entry.metadata or {})
        }
        
        if memory_entry.embedding:
            data["embedding"] = json.dumps(memory_entry.embedding)
        
        return data
    
    def _deserialize_memory_entry(self, data: Dict[str, str]) -> MemoryEntry:
        """Deserialize memory entry from Redis data"""
        
        embedding = None
        if data.get("embedding"):
            embedding = json.loads(data["embedding"])
        
        return MemoryEntry(
            id=data["id"],
            memory_type=MemoryType(data["memory_type"]),
            content=data["content"],
            agent_id=data["agent_id"],
            user_id=data["user_id"],
            conversation_id=data["conversation_id"],
            embedding=embedding,
            importance_score=float(data["importance_score"]),
            access_count=int(data["access_count"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            last_accessed=datetime.fromisoformat(data["last_accessed"]),
            metadata=json.loads(data.get("metadata", "{}"))
        )
    
    async def _update_conversation_metadata(self, conversation_id: str, user_id: str, agent_ids: List[str]) -> None:
        """Update conversation metadata and summary"""
        
        # This would include sentiment analysis, topic extraction, etc.
        # Simplified implementation for now
        conversation_key = f"{self.CONVERSATION_PREFIX}:summary:{conversation_id}"
        
        summary_data = {
            "conversation_id": conversation_id,
            "user_id": user_id,
            "agent_ids": json.dumps(agent_ids),
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "context_summary": "Conversation in progress",
            "key_facts": json.dumps([]),
            "sentiment_analysis": json.dumps({"positive": 0.5, "neutral": 0.3, "negative": 0.2}),
            "topic_tags": json.dumps(["general"])
        }
        
        await self.redis.hset(conversation_key, mapping=summary_data)
        await self.redis.expire(conversation_key, timedelta(days=self.memory_retention_days))
    
    async def _get_recent_memories(self, 
                                 user_id: str, 
                                 memory_type: MemoryType, 
                                 limit: int, 
                                 agent_id: str = None) -> List[MemoryEntry]:
        """Get recent memories of a specific type"""
        
        memories = []
        
        # Get conversation memories
        if memory_type == MemoryType.CONVERSATION:
            conversation_keys = await self.redis.keys(f"{self.CONVERSATION_PREFIX}:{user_id}:*")
        else:
            # For other types, just use conversation keys for now
            conversation_keys = await self.redis.keys(f"{self.CONVERSATION_PREFIX}:{user_id}:*")
        
        for key in conversation_keys:
            try:
                memory_data = await self.redis.hgetall(key)
                if not memory_data:
                    continue
                
                memory_entry = self._deserialize_memory_entry(memory_data)
                
                # Filter by agent if specified
                if agent_id and memory_entry.agent_id != agent_id:
                    continue
                
                # Filter by memory type
                if memory_entry.memory_type == memory_type:
                    memories.append(memory_entry)
                    
            except Exception as e:
                logger.warning("Failed to process memory", key=key, error=str(e))
        
        # Sort by creation time (most recent first)
        memories.sort(key=lambda m: m.created_at, reverse=True)
        
        return memories[:limit]


# Global memory system instance - initialized lazily
memory_system = None

def get_memory_system():
    """Get or create the global memory system instance"""
    global memory_system
    if memory_system is None:
        memory_system = AutoGenMemorySystem()
    return memory_system