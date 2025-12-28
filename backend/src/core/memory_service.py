"""
Unified Memory Service
Single source of truth for all memory operations using PostgreSQL + pgvector
Redis is used only as a cache layer with 15-minute TTL
"""

import json
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

import structlog
import redis.asyncio as redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from ai_clients import batch_create_embeddings, get_embedding
from vector_utils import VectorOperations

logger = structlog.get_logger()


class MemoryType(Enum):
    """Types of memory storage"""
    CONVERSATION = "conversation"      # Full conversation history
    CONTEXT = "context"                # Important context/facts
    KNOWLEDGE = "knowledge"            # Learned knowledge
    RELATIONSHIPS = "relationships"    # Agent-to-agent interactions
    PREFERENCES = "preferences"        # User preferences
    DOCUMENT = "document"              # Document embeddings
    

@dataclass
class UnifiedMemory:
    """Unified memory entry for all memory types"""
    id: str
    memory_type: MemoryType
    content: str
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = None
    user_id: Optional[str] = None
    agent_id: Optional[str] = None
    conversation_id: Optional[str] = None
    document_id: Optional[str] = None
    importance_score: float = 0.5
    access_count: int = 0
    created_at: datetime = None
    last_accessed: datetime = None
    expires_at: Optional[datetime] = None
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
        if self.last_accessed is None:
            self.last_accessed = self.created_at
        if self.metadata is None:
            self.metadata = {}
        if isinstance(self.memory_type, str):
            self.memory_type = MemoryType(self.memory_type)


class UnifiedMemoryService:
    """
    Unified memory service with PostgreSQL as single source of truth.
    Redis is used only for caching with short TTL.
    """
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis = redis_client
        self.cache_ttl = 900  # 15 minutes cache TTL
        self.similarity_threshold = 0.7
        self.max_results = 10
        
        # Initialize Redis if not provided
        if not self.redis:
            try:
                self.redis = redis.from_url(
                    "redis://localhost:6379/0",
                    encoding="utf-8",
                    decode_responses=True
                )
            except Exception as e:
                logger.warning(f"Redis not available, caching disabled: {e}")
        
        logger.info("✅ Unified Memory Service initialized")
    
    async def store_memory(
        self,
        session: AsyncSession,
        memory: UnifiedMemory,
        generate_embedding: bool = True
    ) -> UnifiedMemory:
        """
        Store a memory entry in PostgreSQL.
        
        Args:
            session: Database session
            memory: Memory entry to store
            generate_embedding: Whether to generate embedding
        
        Returns:
            Stored memory with ID
        """
        
        # Generate embedding if needed
        if generate_embedding and not memory.embedding:
            memory.embedding = await get_embedding(memory.content)
        
        # Prepare data for insertion
        insert_data = {
            'id': memory.id,
            'memory_type': memory.memory_type.value,
            'content': memory.content,
            'embedding': VectorOperations.convert_to_pgvector(memory.embedding) if memory.embedding else None,
            'metadata': json.dumps(memory.metadata) if memory.metadata else '{}',
            'user_id': memory.user_id,
            'agent_id': memory.agent_id,
            'conversation_id': memory.conversation_id,
            'document_id': memory.document_id,
            'importance_score': memory.importance_score,
            'access_count': memory.access_count,
            'created_at': memory.created_at,
            'last_accessed': memory.last_accessed,
            'expires_at': memory.expires_at
        }
        
        # Use UPSERT to handle duplicates
        stmt = insert(text("memories")).values(**insert_data)
        stmt = stmt.on_conflict_do_update(
            index_elements=['id'],
            set_={
                'content': stmt.excluded.content,
                'embedding': stmt.excluded.embedding,
                'metadata': stmt.excluded.metadata,
                'importance_score': stmt.excluded.importance_score,
                'access_count': stmt.excluded.access_count + 1,
                'last_accessed': datetime.now(timezone.utc)
            }
        )
        
        try:
            await session.execute(stmt)
            await session.commit()
            
            # Invalidate cache for this memory type
            await self._invalidate_cache(memory.memory_type, memory.user_id)
            
            logger.info(
                f"✅ Stored memory: {memory.id} "
                f"(type: {memory.memory_type.value}, user: {memory.user_id})"
            )
            
            return memory
            
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            await session.rollback()
            raise
    
    async def batch_store_memories(
        self,
        session: AsyncSession,
        memories: List[UnifiedMemory],
        generate_embeddings: bool = True
    ) -> int:
        """
        Store multiple memories efficiently.
        
        Args:
            session: Database session
            memories: List of memories to store
            generate_embeddings: Whether to generate embeddings
        
        Returns:
            Number of memories stored
        """
        
        if not memories:
            return 0
        
        # Generate embeddings in batch if needed
        if generate_embeddings:
            texts = [m.content for m in memories if not m.embedding]
            if texts:
                embeddings = await batch_create_embeddings(texts)
                
                # Assign embeddings to memories
                embedding_idx = 0
                for memory in memories:
                    if not memory.embedding and embedding_idx < len(embeddings):
                        memory.embedding = embeddings[embedding_idx]
                        embedding_idx += 1
        
        # Store all memories
        stored = 0
        for memory in memories:
            try:
                await self.store_memory(session, memory, generate_embedding=False)
                stored += 1
            except Exception as e:
                logger.error(f"Failed to store memory {memory.id}: {e}")
        
        logger.info(f"✅ Batch stored {stored}/{len(memories)} memories")
        return stored
    
    async def search_memories(
        self,
        session: AsyncSession,
        query: str,
        memory_types: Optional[List[MemoryType]] = None,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        limit: int = None,
        use_cache: bool = True
    ) -> List[UnifiedMemory]:
        """
        Search memories using vector similarity.
        
        Args:
            session: Database session
            query: Search query
            memory_types: Filter by memory types
            user_id: Filter by user
            conversation_id: Filter by conversation
            limit: Maximum results
            use_cache: Whether to use Redis cache
        
        Returns:
            List of relevant memories
        """
        
        # Check cache first
        cache_key = self._get_cache_key(query, memory_types, user_id)
        if use_cache and self.redis:
            cached = await self._get_cached_results(cache_key)
            if cached:
                logger.info(f"✅ Cache hit for memory search: {cache_key}")
                return cached
        
        # Generate query embedding
        query_embedding = await get_embedding(query)
        
        # Build filters
        filters = {}
        if user_id:
            filters['user_id'] = user_id
        if conversation_id:
            filters['conversation_id'] = conversation_id
        
        # Search using vector similarity
        results = await VectorOperations.similarity_search(
            session,
            query_embedding,
            table_name="memories",
            vector_column="embedding",
            limit=limit or self.max_results,
            threshold=self.similarity_threshold,
            metadata_filters=filters
        )
        
        # Convert to UnifiedMemory objects
        memories = []
        for row in results:
            memory = UnifiedMemory(
                id=row['id'],
                memory_type=MemoryType(row['memory_type']),
                content=row['content'],
                metadata=json.loads(row.get('metadata', '{}')),
                user_id=row.get('user_id'),
                agent_id=row.get('agent_id'),
                conversation_id=row.get('conversation_id'),
                document_id=row.get('document_id'),
                importance_score=row.get('importance_score', 0.5),
                access_count=row.get('access_count', 0),
                created_at=row.get('created_at'),
                last_accessed=row.get('last_accessed')
            )
            memories.append(memory)
        
        # Cache results
        if use_cache and self.redis:
            await self._cache_results(cache_key, memories)
        
        # Update access counts
        await self._update_access_counts(session, [m.id for m in memories])
        
        logger.info(f"✅ Found {len(memories)} relevant memories")
        return memories
    
    async def get_conversation_context(
        self,
        session: AsyncSession,
        conversation_id: str,
        limit: int = 20
    ) -> List[UnifiedMemory]:
        """
        Get recent conversation context.
        
        Args:
            session: Database session
            conversation_id: Conversation ID
            limit: Maximum messages to retrieve
        
        Returns:
            List of conversation memories
        """
        
        query = text("""
            SELECT * FROM memories
            WHERE conversation_id = :conv_id
                AND memory_type = :mem_type
            ORDER BY created_at DESC
            LIMIT :limit
        """)
        
        result = await session.execute(
            query,
            {
                'conv_id': conversation_id,
                'mem_type': MemoryType.CONVERSATION.value,
                'limit': limit
            }
        )
        
        memories = []
        for row in result:
            memory = UnifiedMemory(
                id=row.id,
                memory_type=MemoryType.CONVERSATION,
                content=row.content,
                metadata=json.loads(row.metadata or '{}'),
                user_id=row.user_id,
                conversation_id=row.conversation_id,
                created_at=row.created_at
            )
            memories.append(memory)
        
        # Reverse to get chronological order
        memories.reverse()
        
        return memories
    
    async def migrate_from_redis(
        self,
        session: AsyncSession,
        redis_source: redis.Redis,
        batch_size: int = 100
    ) -> int:
        """
        Migrate existing Redis memories to PostgreSQL.
        
        Args:
            session: Database session
            redis_source: Redis client with existing data
            batch_size: Batch size for migration
        
        Returns:
            Number of memories migrated
        """
        
        logger.info("🔄 Starting Redis to PostgreSQL memory migration...")
        
        migrated = 0
        
        try:
            # Get all memory keys from Redis
            pattern = "memory:*"
            cursor = 0
            
            while True:
                cursor, keys = await redis_source.scan(
                    cursor, 
                    match=pattern, 
                    count=batch_size
                )
                
                if not keys:
                    if cursor == 0:
                        break
                    continue
                
                # Process batch of keys
                memories_batch = []
                
                for key in keys:
                    try:
                        # Get data from Redis
                        data = await redis_source.get(key)
                        if not data:
                            continue
                        
                        # Parse JSON data
                        memory_data = json.loads(data)
                        
                        # Create UnifiedMemory object
                        memory = UnifiedMemory(
                            id=memory_data.get('id', str(uuid.uuid4())),
                            memory_type=MemoryType(memory_data.get('memory_type', 'context')),
                            content=memory_data.get('content', ''),
                            metadata=memory_data.get('metadata', {}),
                            user_id=memory_data.get('user_id'),
                            agent_id=memory_data.get('agent_id'),
                            conversation_id=memory_data.get('conversation_id'),
                            importance_score=memory_data.get('importance_score', 0.5),
                            created_at=datetime.fromisoformat(memory_data['created_at']) 
                                      if 'created_at' in memory_data else datetime.now(timezone.utc)
                        )
                        
                        memories_batch.append(memory)
                        
                    except Exception as e:
                        logger.error(f"Failed to parse Redis memory {key}: {e}")
                        continue
                
                # Store batch in PostgreSQL
                if memories_batch:
                    stored = await self.batch_store_memories(
                        session, 
                        memories_batch,
                        generate_embeddings=True
                    )
                    migrated += stored
                    logger.info(f"Migrated batch: {stored} memories")
                
                if cursor == 0:
                    break
            
            logger.info(f"✅ Migration complete: {migrated} memories migrated")
            return migrated
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise
    
    async def cleanup_expired_memories(
        self,
        session: AsyncSession,
        retention_days: int = 30
    ) -> int:
        """
        Clean up old memories based on retention policy.
        
        Args:
            session: Database session
            retention_days: Days to retain memories
        
        Returns:
            Number of memories deleted
        """
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
        
        query = text("""
            DELETE FROM memories
            WHERE (expires_at IS NOT NULL AND expires_at < :now)
               OR (created_at < :cutoff AND importance_score < 0.5)
            RETURNING id
        """)
        
        result = await session.execute(
            query,
            {
                'now': datetime.now(timezone.utc),
                'cutoff': cutoff_date
            }
        )
        
        deleted_ids = [row[0] for row in result]
        await session.commit()
        
        if deleted_ids:
            logger.info(f"🗑️ Cleaned up {len(deleted_ids)} expired memories")
        
        return len(deleted_ids)
    
    # Cache helper methods
    
    def _get_cache_key(
        self,
        query: str,
        memory_types: Optional[List[MemoryType]],
        user_id: Optional[str]
    ) -> str:
        """Generate cache key for search results"""
        key_parts = [
            "memory_search",
            hashlib.md5(query.encode()).hexdigest()[:8],
            user_id or "all",
            ",".join([mt.value for mt in memory_types]) if memory_types else "all"
        ]
        return ":".join(key_parts)
    
    async def _get_cached_results(self, cache_key: str) -> Optional[List[UnifiedMemory]]:
        """Get cached search results"""
        if not self.redis:
            return None
        
        try:
            cached = await self.redis.get(cache_key)
            if cached:
                data = json.loads(cached)
                memories = [
                    UnifiedMemory(**item) for item in data
                ]
                return memories
        except Exception as e:
            logger.debug(f"Cache get failed: {e}")
        
        return None
    
    async def _cache_results(self, cache_key: str, memories: List[UnifiedMemory]):
        """Cache search results"""
        if not self.redis:
            return
        
        try:
            data = [asdict(m) for m in memories]
            # Convert enums to strings for JSON serialization
            for item in data:
                if 'memory_type' in item:
                    item['memory_type'] = item['memory_type'].value
                # Convert datetime to ISO format
                for date_field in ['created_at', 'last_accessed', 'expires_at']:
                    if date_field in item and item[date_field]:
                        item[date_field] = item[date_field].isoformat()
            
            await self.redis.setex(
                cache_key,
                self.cache_ttl,
                json.dumps(data)
            )
        except Exception as e:
            logger.debug(f"Cache set failed: {e}")
    
    async def _invalidate_cache(
        self,
        memory_type: MemoryType,
        user_id: Optional[str] = None
    ):
        """Invalidate cache for memory type"""
        if not self.redis:
            return
        
        try:
            pattern = f"memory_search:*:{user_id or '*'}:*{memory_type.value}*"
            cursor = 0
            
            while True:
                cursor, keys = await self.redis.scan(cursor, match=pattern)
                if keys:
                    await self.redis.delete(*keys)
                if cursor == 0:
                    break
        except Exception as e:
            logger.debug(f"Cache invalidation failed: {e}")
    
    async def _update_access_counts(
        self,
        session: AsyncSession,
        memory_ids: List[str]
    ):
        """Update access counts for memories"""
        if not memory_ids:
            return
        
        try:
            query = text("""
                UPDATE memories
                SET access_count = access_count + 1,
                    last_accessed = :now
                WHERE id = ANY(:ids)
            """)
            
            await session.execute(
                query,
                {
                    'ids': memory_ids,
                    'now': datetime.now(timezone.utc)
                }
            )
            await session.commit()
        except Exception as e:
            logger.debug(f"Failed to update access counts: {e}")


# Singleton instance
_memory_service = None


def get_memory_service() -> UnifiedMemoryService:
    """Get singleton memory service"""
    global _memory_service
    if _memory_service is None:
        _memory_service = UnifiedMemoryService()
    return _memory_service