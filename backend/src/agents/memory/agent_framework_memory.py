"""
Agent Framework Memory System
Persistent conversation memory with RAG integration.
Supports both Agent Framework and AutoGen message formats.
"""

import json
import asyncio
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict, field
from enum import Enum

import structlog

# Redis import with fallback
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

# Agent Framework imports with fallback
try:
    from agent_framework.messages import TextMessage as AFTextMessage
    AGENT_FRAMEWORK_AVAILABLE = True
except ImportError:
    AGENT_FRAMEWORK_AVAILABLE = False
    AFTextMessage = None

# AutoGen imports with fallback
try:
    from autogen_agentchat.messages import TextMessage as AutoGenTextMessage
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False
    AutoGenTextMessage = None

# Optional vector search
try:
    from ..tools.vector_search_client import embed_text, search_similar
    VECTOR_SEARCH_AVAILABLE = True
except ImportError:
    VECTOR_SEARCH_AVAILABLE = False
    embed_text = None
    search_similar = None

logger = structlog.get_logger()


class MemoryType(Enum):
    """Types of memory storage."""
    CONVERSATION = "conversation"
    CONTEXT = "context"
    KNOWLEDGE = "knowledge"
    RELATIONSHIPS = "relationships"
    PREFERENCES = "preferences"


@dataclass
class MemoryMessage:
    """Unified message format for memory storage.

    Works with both Agent Framework and AutoGen message formats.
    """
    id: str
    role: str  # 'user', 'assistant', 'system'
    content: str
    source: str  # agent key or 'user'
    timestamp: datetime = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryMessage":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            role=data["role"],
            content=data["content"],
            source=data["source"],
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else None,
            metadata=data.get("metadata", {})
        )

    @classmethod
    def from_agent_framework(cls, msg: Any) -> "MemoryMessage":
        """Convert from Agent Framework message."""
        return cls(
            id=getattr(msg, 'id', hashlib.md5(str(msg).encode()).hexdigest()[:8]),
            role="assistant" if getattr(msg, 'source', '') != 'user' else "user",
            content=getattr(msg, 'content', str(msg)),
            source=getattr(msg, 'source', 'unknown')
        )

    @classmethod
    def from_autogen(cls, msg: Any) -> "MemoryMessage":
        """Convert from AutoGen message."""
        return cls(
            id=getattr(msg, 'id', hashlib.md5(str(msg).encode()).hexdigest()[:8]),
            role="assistant" if getattr(msg, 'source', '') != 'user' else "user",
            content=getattr(msg, 'content', str(msg)),
            source=getattr(msg, 'source', 'unknown')
        )


@dataclass
class MemoryEntry:
    """Individual memory entry with metadata."""
    id: str
    memory_type: MemoryType
    content: str
    agent_id: str
    user_id: str
    conversation_id: str
    embedding: Optional[List[float]] = None
    importance_score: float = 0.5
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

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "memory_type": self.memory_type.value,
            "content": self.content,
            "agent_id": self.agent_id,
            "user_id": self.user_id,
            "conversation_id": self.conversation_id,
            "embedding": self.embedding,
            "importance_score": self.importance_score,
            "access_count": self.access_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
            "metadata": self.metadata
        }


@dataclass
class ConversationMemory:
    """Complete conversation memory with context."""
    conversation_id: str
    user_id: str
    agent_ids: List[str]
    messages: List[MemoryMessage]
    context_summary: str = ""
    key_facts: List[str] = field(default_factory=list)
    topic_tags: List[str] = field(default_factory=list)
    created_at: datetime = None
    last_updated: datetime = None
    total_tokens: int = 0

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
        if self.last_updated is None:
            self.last_updated = self.created_at

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "conversation_id": self.conversation_id,
            "user_id": self.user_id,
            "agent_ids": self.agent_ids,
            "messages": [m.to_dict() for m in self.messages],
            "context_summary": self.context_summary,
            "key_facts": self.key_facts,
            "topic_tags": self.topic_tags,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "total_tokens": self.total_tokens
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationMemory":
        """Create from dictionary."""
        return cls(
            conversation_id=data["conversation_id"],
            user_id=data["user_id"],
            agent_ids=data.get("agent_ids", []),
            messages=[MemoryMessage.from_dict(m) for m in data.get("messages", [])],
            context_summary=data.get("context_summary", ""),
            key_facts=data.get("key_facts", []),
            topic_tags=data.get("topic_tags", []),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            last_updated=datetime.fromisoformat(data["last_updated"]) if data.get("last_updated") else None,
            total_tokens=data.get("total_tokens", 0)
        )


class AgentFrameworkMemory:
    """Memory system for Agent Framework with dual-framework support.

    Provides:
    - Conversation storage and retrieval
    - Context management
    - RAG-based memory search (when available)
    - Redis persistence (when available)
    - In-memory fallback when Redis not available
    """

    def __init__(self, redis_client: Optional[Any] = None):
        """Initialize memory system.

        Args:
            redis_client: Optional Redis client. If None, uses in-memory storage.
        """
        self.redis = redis_client
        self.use_redis = REDIS_AVAILABLE and redis_client is not None

        # In-memory fallback storage
        self._conversations: Dict[str, ConversationMemory] = {}
        self._context: Dict[str, List[MemoryEntry]] = {}

        # Configuration
        self.memory_retention_days = 30
        self.max_conversation_length = 100
        self.similarity_threshold = 0.8

        # Key prefixes for Redis
        self.CONVERSATION_PREFIX = "af_memory:conversation"
        self.CONTEXT_PREFIX = "af_memory:context"

        logger.info(
            "AgentFrameworkMemory initialized",
            redis_enabled=self.use_redis,
            vector_search_enabled=VECTOR_SEARCH_AVAILABLE
        )

    async def store_message(
        self,
        conversation_id: str,
        message: Union[MemoryMessage, Any],
        agent_id: str,
        user_id: str
    ) -> str:
        """Store a message in conversation memory.

        Args:
            conversation_id: Unique conversation identifier
            message: Message to store (MemoryMessage, AF message, or AutoGen message)
            agent_id: Agent that participated
            user_id: User in the conversation

        Returns:
            Message ID
        """
        # Convert to unified format if needed
        if isinstance(message, MemoryMessage):
            mem_message = message
        elif AGENT_FRAMEWORK_AVAILABLE and AFTextMessage and isinstance(message, AFTextMessage):
            mem_message = MemoryMessage.from_agent_framework(message)
        elif AUTOGEN_AVAILABLE and AutoGenTextMessage and isinstance(message, AutoGenTextMessage):
            mem_message = MemoryMessage.from_autogen(message)
        else:
            # Generic conversion
            mem_message = MemoryMessage(
                id=hashlib.md5(str(message).encode()).hexdigest()[:8],
                role="assistant",
                content=str(message),
                source=agent_id
            )

        # Get or create conversation
        conversation = await self.get_conversation(conversation_id)
        if conversation is None:
            conversation = ConversationMemory(
                conversation_id=conversation_id,
                user_id=user_id,
                agent_ids=[agent_id],
                messages=[]
            )

        # Add message
        conversation.messages.append(mem_message)
        if agent_id not in conversation.agent_ids:
            conversation.agent_ids.append(agent_id)
        conversation.last_updated = datetime.now(timezone.utc)

        # Trim if too long
        if len(conversation.messages) > self.max_conversation_length:
            conversation.messages = conversation.messages[-self.max_conversation_length:]

        # Store
        await self._store_conversation(conversation)

        logger.debug(
            "Message stored",
            conversation_id=conversation_id,
            message_id=mem_message.id
        )

        return mem_message.id

    async def get_conversation(
        self,
        conversation_id: str
    ) -> Optional[ConversationMemory]:
        """Retrieve a conversation by ID.

        Args:
            conversation_id: Conversation to retrieve

        Returns:
            ConversationMemory or None if not found
        """
        if self.use_redis:
            try:
                key = f"{self.CONVERSATION_PREFIX}:{conversation_id}"
                data = await self.redis.get(key)
                if data:
                    return ConversationMemory.from_dict(json.loads(data))
            except Exception as e:
                logger.warning(f"Redis get failed: {e}")

        return self._conversations.get(conversation_id)

    async def get_conversation_history(
        self,
        conversation_id: str,
        limit: int = 10
    ) -> List[MemoryMessage]:
        """Get recent messages from a conversation.

        Args:
            conversation_id: Conversation to retrieve
            limit: Maximum number of messages

        Returns:
            List of messages (most recent last)
        """
        conversation = await self.get_conversation(conversation_id)
        if conversation is None:
            return []
        return conversation.messages[-limit:]

    async def search_memories(
        self,
        query: str,
        user_id: str,
        limit: int = 5
    ) -> List[MemoryEntry]:
        """Search memories using semantic similarity.

        Args:
            query: Search query
            user_id: User to search for
            limit: Maximum results

        Returns:
            List of relevant memory entries
        """
        if not VECTOR_SEARCH_AVAILABLE or embed_text is None:
            logger.debug("Vector search not available, returning empty")
            return []

        try:
            results = await search_similar(query, top_k=limit)
            return [
                MemoryEntry(
                    id=r.get("id", ""),
                    memory_type=MemoryType.CONTEXT,
                    content=r.get("content", ""),
                    agent_id="",
                    user_id=user_id,
                    conversation_id="",
                    metadata=r.get("metadata", {})
                )
                for r in results
            ]
        except Exception as e:
            logger.error(f"Memory search failed: {e}")
            return []

    async def add_context(
        self,
        conversation_id: str,
        context: str,
        importance: float = 0.5
    ) -> str:
        """Add context/fact to memory.

        Args:
            conversation_id: Associated conversation
            context: Context content
            importance: Importance score (0-1)

        Returns:
            Memory entry ID
        """
        entry_id = hashlib.md5(f"{conversation_id}:{context}".encode()).hexdigest()[:12]

        entry = MemoryEntry(
            id=entry_id,
            memory_type=MemoryType.CONTEXT,
            content=context,
            agent_id="system",
            user_id="",
            conversation_id=conversation_id,
            importance_score=importance
        )

        if conversation_id not in self._context:
            self._context[conversation_id] = []
        self._context[conversation_id].append(entry)

        logger.debug(f"Context added: {entry_id}")
        return entry_id

    async def get_context(
        self,
        conversation_id: str,
        limit: int = 10
    ) -> List[MemoryEntry]:
        """Get context entries for a conversation.

        Args:
            conversation_id: Conversation to get context for
            limit: Maximum entries

        Returns:
            List of context entries sorted by importance
        """
        entries = self._context.get(conversation_id, [])
        # Sort by importance descending
        sorted_entries = sorted(entries, key=lambda e: e.importance_score, reverse=True)
        return sorted_entries[:limit]

    async def clear_conversation(self, conversation_id: str) -> bool:
        """Clear a conversation from memory.

        Args:
            conversation_id: Conversation to clear

        Returns:
            True if cleared, False if not found
        """
        cleared = False

        if self.use_redis:
            try:
                key = f"{self.CONVERSATION_PREFIX}:{conversation_id}"
                result = await self.redis.delete(key)
                cleared = result > 0
            except Exception as e:
                logger.warning(f"Redis delete failed: {e}")

        if conversation_id in self._conversations:
            del self._conversations[conversation_id]
            cleared = True

        if conversation_id in self._context:
            del self._context[conversation_id]

        return cleared

    async def _store_conversation(self, conversation: ConversationMemory) -> None:
        """Store conversation to persistent storage."""
        # Always store in memory
        self._conversations[conversation.conversation_id] = conversation

        # Also store in Redis if available
        if self.use_redis:
            try:
                key = f"{self.CONVERSATION_PREFIX}:{conversation.conversation_id}"
                data = json.dumps(conversation.to_dict())
                await self.redis.set(
                    key,
                    data,
                    ex=self.memory_retention_days * 24 * 3600
                )
            except Exception as e:
                logger.warning(f"Redis store failed: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get memory system statistics."""
        return {
            "conversations_in_memory": len(self._conversations),
            "context_entries": sum(len(v) for v in self._context.values()),
            "redis_enabled": self.use_redis,
            "vector_search_enabled": VECTOR_SEARCH_AVAILABLE,
            "agent_framework_available": AGENT_FRAMEWORK_AVAILABLE,
            "autogen_available": AUTOGEN_AVAILABLE
        }


# Global memory instance
_memory_instance: Optional[AgentFrameworkMemory] = None


def get_memory_system(
    redis_client: Optional[Any] = None
) -> AgentFrameworkMemory:
    """Get the global memory system instance."""
    global _memory_instance
    if _memory_instance is None:
        _memory_instance = AgentFrameworkMemory(redis_client=redis_client)
    return _memory_instance


__all__ = [
    "AgentFrameworkMemory",
    "MemoryMessage",
    "MemoryEntry",
    "ConversationMemory",
    "MemoryType",
    "get_memory_system",
    "AGENT_FRAMEWORK_AVAILABLE",
    "AUTOGEN_AVAILABLE",
    "REDIS_AVAILABLE",
    "VECTOR_SEARCH_AVAILABLE",
]
