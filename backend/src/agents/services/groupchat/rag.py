"""
RAG Helpers - Complete implementation with memory integration and quality scoring
Retrieve relevant context from memory and format as system message with advanced filtering.
"""

import hashlib
from datetime import datetime
from typing import Optional, List, Any
from dataclasses import dataclass

import structlog

# Optional AutoGen import
try:
    from autogen_agentchat.messages import TextMessage
except ImportError:
    class TextMessage:  # type: ignore
        """Fallback TextMessage when AutoGen not available"""
        def __init__(self, content: str = "", source: str = ""):
            self.content = content
            self.source = source

from ...memory.autogen_memory_system import AutoGenMemorySystem, MemoryType, MemoryEntry
from ...utils.config import get_settings
from .rag_enhancements import (
    DynamicThreshold,
    SemanticDeduplicator,
    IntelligentRAGCache,
    RAGQualityMonitor,
    get_agent_filter
)

logger = structlog.get_logger()


@dataclass
class RAGContext:
    """Structured RAG context with quality metrics"""
    content: str
    relevance_score: float
    importance_score: float
    recency_score: float
    composite_score: float
    source_agent: Optional[str]
    memory_type: MemoryType
    conversation_id: Optional[str]
    timestamp: datetime


class AdvancedRAGProcessor:
    """Advanced RAG processing with multi-factor scoring and context optimization"""
    
    def __init__(self, memory_system: Optional[AutoGenMemorySystem] = None, settings: Optional[Any] = None):
        # Accept optional settings for call sites that pass it; default to local get_settings
        self.memory_system = memory_system or AutoGenMemorySystem()
        self.settings = settings or get_settings()
        
        # Initialize enhancements
        self.dynamic_threshold = DynamicThreshold()
        self.semantic_deduplicator = SemanticDeduplicator()
        self.cache = IntelligentRAGCache()
        self.quality_monitor = RAGQualityMonitor()
        self.agent_filters = {}
        
    async def build_memory_context(
        self, 
        user_id: str, 
        agent_id: Optional[str], 
        query: str, 
        limit: int = 5,
        similarity_threshold: float = 0.0,
        include_conversation_history: bool = True,
        include_knowledge_base: bool = True,
        recency_weight: float = 0.3,
        importance_weight: float = 0.4,
        relevance_weight: float = 0.3,
        turn_number: int = 0,
        use_cache: bool = True,
        use_semantic_dedup: bool = True
    ) -> Optional[TextMessage]:
        """
        Build comprehensive memory context with multi-factor scoring
        
        Args:
            user_id: User identifier
            agent_id: Agent identifier (optional for cross-agent context)
            query: Query for semantic search
            limit: Maximum context items to return
            similarity_threshold: Minimum similarity score
            include_conversation_history: Include conversation memories
            include_knowledge_base: Include knowledge memories  
            recency_weight: Weight for recency in composite scoring
            importance_weight: Weight for importance in composite scoring
            relevance_weight: Weight for relevance in composite scoring
        """
        if not self.memory_system:
            logger.warning("No memory system available for RAG")
            return None
        
        # Check cache first
        if use_cache and self.cache:
            await self.cache.initialize()
            cached_result = await self.cache.get(
                user_id=user_id,
                query=query,
                agent_id=agent_id,
                memory_types=["conversation", "knowledge"] if include_conversation_history and include_knowledge_base else None
            )
            if cached_result:
                logger.info("Using cached RAG result", user_id=user_id)
                return TextMessage(content=cached_result.get("content", ""), source="system")
            
        try:
            start_time = datetime.utcnow()
            # Multi-type memory retrieval
            memory_types = []
            if include_conversation_history:
                memory_types.extend([MemoryType.CONVERSATION, MemoryType.CONTEXT])
            if include_knowledge_base:
                memory_types.extend([MemoryType.KNOWLEDGE, MemoryType.RELATIONSHIPS])
                
            # Retrieve memories from multiple sources
            all_contexts: List[RAGContext] = []
            
            for memory_type in memory_types:
                memories = await self.memory_system.retrieve_by_type(
                    user_id=user_id,
                    memory_type=memory_type,
                    query=query,
                    limit=limit * 2,  # Over-retrieve for filtering
                    agent_id=agent_id
                )
                
                for memory in memories:
                    context = await self._create_rag_context(
                        memory, query, recency_weight, importance_weight, relevance_weight
                    )
                    
                    # Apply dynamic threshold
                    agent_type = self._get_agent_type(agent_id) if agent_id else None
                    dynamic_threshold_value = self.dynamic_threshold.calculate(
                        turn_number=turn_number,
                        agent_type=agent_type
                    )
                    
                    if context.composite_score >= max(similarity_threshold, dynamic_threshold_value):
                        all_contexts.append(context)
            
            # Agent-specific context enhancement
            if agent_id:
                agent_contexts = await self._get_agent_specific_context(
                    user_id, agent_id, query, limit
                )
                all_contexts.extend(agent_contexts)
            
            # Apply per-agent filtering if available
            if agent_id:
                agent_filter = get_agent_filter(agent_id)
                if agent_filter:
                    pre_filter_count = len(all_contexts)
                    all_contexts = agent_filter.apply_filter(all_contexts)
                    post_filter_count = len(all_contexts)
                    
                    # Track filter effectiveness
                    if self.quality_monitor and pre_filter_count > 0:
                        avg_score_pre = sum(c.composite_score for c in all_contexts[:pre_filter_count]) / pre_filter_count
                        avg_score_post = sum(c.composite_score for c in all_contexts) / len(all_contexts) if all_contexts else 0
                        await self.quality_monitor.track_agent_filter_effectiveness(
                            agent_name=agent_id,
                            pre_filter_count=pre_filter_count,
                            post_filter_count=post_filter_count,
                            avg_score_improvement=avg_score_post - avg_score_pre
                        )
            
            # Apply semantic deduplication if enabled
            if use_semantic_dedup and self.semantic_deduplicator:
                all_contexts = await self.semantic_deduplicator.deduplicate(all_contexts)
            else:
                # Use standard deduplication
                all_contexts = await self._deduplicate_and_rank(all_contexts, limit * 2)
            
            # Final ranking and limiting
            filtered_contexts = sorted(all_contexts, key=lambda c: c.composite_score, reverse=True)[:limit]
            
            if not filtered_contexts:
                logger.info(f"No relevant context found for query: {query[:50]}...")
                return None
                
            # Format context message
            formatted_context = await self._format_context_message(filtered_contexts, query)
            
            # Log context quality metrics
            avg_score = sum(c.composite_score for c in filtered_contexts) / len(filtered_contexts)
            latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Track quality metrics
            if self.quality_monitor:
                await self.quality_monitor.track_retrieval(
                    query=query,
                    contexts_retrieved=len(filtered_contexts),
                    avg_score=avg_score,
                    latency_ms=latency_ms,
                    cache_hit=False
                )
            
            logger.info(
                "RAG context built",
                contexts_count=len(filtered_contexts),
                avg_composite_score=round(avg_score, 3),
                query_length=len(query),
                user_id=user_id,
                agent_id=agent_id,
                latency_ms=round(latency_ms, 2)
            )
            
            # Cache the result
            if use_cache and self.cache:
                await self.cache.set(
                    user_id=user_id,
                    query=query,
                    result={"content": formatted_context.content},
                    agent_id=agent_id,
                    memory_types=[mt.value for mt in memory_types]
                )
            
            return formatted_context
            
        except Exception as e:
            logger.error("Failed to build memory context", error=str(e), user_id=user_id, query=query[:50])
            return None
    
    async def _create_rag_context(
        self, 
        memory: MemoryEntry, 
        query: str,
        recency_weight: float,
        importance_weight: float, 
        relevance_weight: float
    ) -> RAGContext:
        """Create RAG context with composite scoring"""
        
        # Calculate individual scores
        relevance_score = await self._calculate_relevance_score(memory.content, query)
        importance_score = memory.importance_score
        recency_score = await self._calculate_recency_score(memory.created_at)
        
        # Composite score calculation
        composite_score = (
            relevance_score * relevance_weight +
            importance_score * importance_weight + 
            recency_score * recency_weight
        )
        
        return RAGContext(
            content=memory.content,
            relevance_score=relevance_score,
            importance_score=importance_score,
            recency_score=recency_score,
            composite_score=composite_score,
            source_agent=memory.agent_id,
            memory_type=memory.memory_type,
            conversation_id=memory.conversation_id,
            timestamp=memory.created_at
        )
    
    async def _calculate_relevance_score(self, content: str, query: str) -> float:
        """Calculate semantic relevance score using embedding similarity"""
        try:
            from ..tools.vector_search_client import embed_text, calculate_similarity
            
            content_embedding = await embed_text(content)
            query_embedding = await embed_text(query)
            
            if content_embedding and query_embedding:
                similarity = calculate_similarity(content_embedding, query_embedding)
                return max(0.0, min(1.0, similarity))
            
        except Exception as e:
            logger.warning("Failed to calculate relevance score", error=str(e))
            
        # Fallback to keyword matching
        query_words = set(query.lower().split())
        content_words = set(content.lower().split())
        overlap = len(query_words & content_words)
        return min(1.0, overlap / max(1, len(query_words)))
    
    async def _calculate_recency_score(self, created_at: datetime) -> float:
        """Calculate recency score (more recent = higher score)"""
        if not created_at:
            return 0.0
            
        now = datetime.now(created_at.tzinfo) if created_at.tzinfo else datetime.now()
        age_hours = (now - created_at).total_seconds() / 3600
        
        # Exponential decay: score = e^(-age/24) for 24-hour half-life
        import math
        return math.exp(-age_hours / 24)
    
    async def _get_agent_specific_context(
        self, user_id: str, agent_id: str, query: str, limit: int
    ) -> List[RAGContext]:
        """Get context specific to agent interactions and preferences"""
        try:
            # Get agent relationship memories
            relationships = await self.memory_system.retrieve_by_type(
                user_id=user_id,
                memory_type=MemoryType.RELATIONSHIPS,
                query=f"agent:{agent_id}",
                limit=limit,
                agent_id=agent_id
            )
            
            # Get user preferences for this agent
            preferences = await self.memory_system.retrieve_by_type(
                user_id=user_id,
                memory_type=MemoryType.PREFERENCES,
                query=f"agent:{agent_id}",
                limit=limit // 2,
                agent_id=agent_id
            )
            
            contexts = []
            for memory in relationships + preferences:
                context = await self._create_rag_context(memory, query, 0.2, 0.6, 0.2)
                contexts.append(context)
                
            return contexts
            
        except Exception as e:
            logger.warning("Failed to get agent-specific context", error=str(e), agent_id=agent_id)
            return []
    
    def _get_agent_type(self, agent_id: str) -> Optional[str]:
        """Get agent type for dynamic threshold calculation"""
        agent_types = {
            "ali_chief_of_staff": "strategic",
            "amy_cfo": "financial",
            "diana_performance_dashboard": "operational",
            "luca_security_expert": "technical",
            "wanda_workflow_orchestrator": "operational",
            "domik_mckinsey_strategic_decision_maker": "strategic"
        }
        return agent_types.get(agent_id)
    
    async def _deduplicate_and_rank(self, contexts: List[RAGContext], limit: int) -> List[RAGContext]:
        """Remove duplicates and rank by composite score"""
        
        # Deduplicate by content hash
        seen_hashes = set()
        unique_contexts = []
        
        for context in contexts:
            content_hash = hashlib.md5(context.content.lower().encode()).hexdigest()
            if content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                unique_contexts.append(context)
        
        # Sort by composite score (descending)
        unique_contexts.sort(key=lambda c: c.composite_score, reverse=True)
        
        return unique_contexts[:limit]
    
    async def _format_context_message(self, contexts: List[RAGContext], query: str) -> TextMessage:
        """Format contexts into a structured system message"""
        
        if not contexts:
            return TextMessage(content="No relevant context available.", source="system")
        
        # Group contexts by type
        by_type = {}
        for context in contexts:
            type_name = context.memory_type.value
            if type_name not in by_type:
                by_type[type_name] = []
            by_type[type_name].append(context)
        
        # Build formatted message
        message_parts = [
            f"📋 Relevant Context for: \"{query[:100]}{'...' if len(query) > 100 else ''}\"",
            ""
        ]
        
        for memory_type, type_contexts in by_type.items():
            if not type_contexts:
                continue
                
            message_parts.append(f"## {memory_type.title()} Context:")
            
            for i, context in enumerate(type_contexts[:3], 1):  # Limit per type
                score_info = f"(relevance: {context.relevance_score:.2f}, importance: {context.importance_score:.2f})"
                
                # Truncate long content
                content = context.content
                if len(content) > 300:
                    content = content[:297] + "..."
                
                message_parts.extend([
                    f"**{i}.** {content}",
                    f"   _{score_info}_",
                    ""
                ])
        
        # Add quality summary
        avg_score = sum(c.composite_score for c in contexts) / len(contexts)
        message_parts.extend([
            "---",
            f"📊 Context Quality: {avg_score:.2f}/1.0 ({len(contexts)} items)",
            ""
        ])
        
        return TextMessage(content="\n".join(message_parts), source="system")


# Legacy compatibility function
async def build_memory_context(
    memory_system, 
    user_id: str, 
    agent_id: Optional[str], 
    query: str, 
    limit: int = 5, 
    *, 
    similarity_threshold: float = 0.0
) -> Optional[TextMessage]:
    """Legacy compatibility wrapper for existing code"""
    
    if not memory_system:
        return None
        
    processor = AdvancedRAGProcessor(memory_system)
    return await processor.build_memory_context(
        user_id=user_id,
        agent_id=agent_id, 
        query=query,
        limit=limit,
        similarity_threshold=similarity_threshold
    )
