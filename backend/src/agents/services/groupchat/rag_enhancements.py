"""
RAG Enhancements - Advanced features for Task 2
Implements per-agent filters, dynamic thresholds, semantic deduplication, and caching
"""

import asyncio
import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple, Set
from dataclasses import dataclass, field
from collections import defaultdict
import numpy as np

import structlog
import redis.asyncio as redis
from sentence_transformers import SentenceTransformer

from src.agents.utils.config import get_settings

logger = structlog.get_logger()


@dataclass
class DynamicThreshold:
    """Dynamic threshold configuration that adapts to context"""
    base_threshold: float = 0.5
    context_multiplier: float = 1.0
    agent_multiplier: float = 1.0
    turn_decay: float = 0.95  # Decay per turn for older context
    min_threshold: float = 0.3
    max_threshold: float = 0.9
    
    def calculate(self, turn_number: int = 0, agent_type: str = None) -> float:
        """Calculate dynamic threshold based on context"""
        threshold = self.base_threshold * self.context_multiplier
        
        # Apply agent-specific multiplier
        if agent_type:
            agent_multipliers = {
                "strategic": 1.2,  # Higher threshold for strategic agents
                "operational": 1.0,
                "technical": 1.1,
                "financial": 1.15
            }
            threshold *= agent_multipliers.get(agent_type, self.agent_multiplier)
        
        # Apply turn decay for older context
        threshold *= (self.turn_decay ** turn_number)
        
        # Clamp to min/max
        return max(self.min_threshold, min(threshold, self.max_threshold))


@dataclass
class PerAgentFilter:
    """Agent-specific filtering configuration"""
    agent_name: str
    agent_type: str  # strategic, operational, technical, financial
    max_facts: int = 5
    required_memory_types: List[str] = field(default_factory=list)
    excluded_memory_types: List[str] = field(default_factory=list)
    keyword_priorities: Dict[str, float] = field(default_factory=dict)
    recency_weight: float = 0.3
    importance_weight: float = 0.4
    relevance_weight: float = 0.3
    
    def apply_filter(self, contexts: List[Any]) -> List[Any]:
        """Apply agent-specific filtering to contexts"""
        filtered = []
        
        for context in contexts:
            # Check memory type filters
            if context.memory_type.value in self.excluded_memory_types:
                continue
            if self.required_memory_types and context.memory_type.value not in self.required_memory_types:
                continue
            
            # Apply keyword priority boost
            boost = 1.0
            for keyword, priority in self.keyword_priorities.items():
                if keyword.lower() in context.content.lower():
                    boost *= priority
            
            # Adjust composite score with boost
            context.composite_score *= boost
            filtered.append(context)
        
        # Sort by adjusted score and limit
        filtered.sort(key=lambda c: c.composite_score, reverse=True)
        return filtered[:self.max_facts]


class SemanticDeduplicator:
    """Advanced deduplication using semantic similarity"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.similarity_threshold = 0.85
        
    async def deduplicate(self, contexts: List[Any]) -> List[Any]:
        """Remove semantically similar contexts"""
        if not contexts:
            return []
        
        # Extract content for embedding
        contents = [c.content for c in contexts]
        
        # Generate embeddings
        embeddings = self.model.encode(contents, convert_to_numpy=True)
        
        # Calculate similarity matrix
        unique_indices = []
        seen_clusters = set()
        
        for i, emb_i in enumerate(embeddings):
            if i in seen_clusters:
                continue
            
            unique_indices.append(i)
            
            # Find similar contexts
            for j in range(i + 1, len(embeddings)):
                if j in seen_clusters:
                    continue
                
                # Cosine similarity
                similarity = np.dot(emb_i, embeddings[j]) / (
                    np.linalg.norm(emb_i) * np.linalg.norm(embeddings[j])
                )
                
                if similarity > self.similarity_threshold:
                    seen_clusters.add(j)
        
        return [contexts[i] for i in unique_indices]


class IntelligentRAGCache:
    """Redis-based intelligent caching for RAG queries"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis = redis_client
        self.cache_ttl = 300  # 5 minutes default
        self.max_cache_size = 1000
        self.cache_stats = defaultdict(int)
        
    async def initialize(self):
        """Initialize Redis connection if not provided"""
        if not self.redis:
            settings = get_settings()
            self.redis = await redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
    
    def _generate_cache_key(
        self, 
        user_id: str, 
        query: str, 
        agent_id: Optional[str] = None,
        memory_types: Optional[List[str]] = None
    ) -> str:
        """Generate cache key for RAG query"""
        components = [
            user_id,
            hashlib.md5(query.lower().encode()).hexdigest()[:8],
            agent_id or "any",
            "-".join(sorted(memory_types or []))
        ]
        return f"rag:cache:{':'.join(components)}"
    
    async def get(
        self,
        user_id: str,
        query: str,
        agent_id: Optional[str] = None,
        memory_types: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """Retrieve cached RAG result"""
        if not self.redis:
            return None
        
        key = self._generate_cache_key(user_id, query, agent_id, memory_types)
        
        try:
            cached = await self.redis.get(key)
            if cached:
                self.cache_stats["hits"] += 1
                logger.debug(f"RAG cache hit for key: {key}")
                return json.loads(cached)
            else:
                self.cache_stats["misses"] += 1
                return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    async def set(
        self,
        user_id: str,
        query: str,
        result: Dict[str, Any],
        agent_id: Optional[str] = None,
        memory_types: Optional[List[str]] = None,
        ttl: Optional[int] = None
    ):
        """Store RAG result in cache"""
        if not self.redis:
            return
        
        key = self._generate_cache_key(user_id, query, agent_id, memory_types)
        
        try:
            await self.redis.setex(
                key,
                ttl or self.cache_ttl,
                json.dumps(result)
            )
            self.cache_stats["writes"] += 1
            logger.debug(f"RAG result cached for key: {key}")
        except Exception as e:
            logger.error(f"Cache set error: {e}")
    
    async def invalidate_user_cache(self, user_id: str):
        """Invalidate all cache entries for a user"""
        if not self.redis:
            return
        
        pattern = f"rag:cache:{user_id}:*"
        try:
            async for key in self.redis.scan_iter(match=pattern):
                await self.redis.delete(key)
            logger.info(f"Invalidated cache for user: {user_id}")
        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")
    
    async def warm_cache(self, common_queries: List[Tuple[str, str, Optional[str]]]):
        """Pre-warm cache with common queries"""
        logger.info(f"Warming cache with {len(common_queries)} queries")
        
        for user_id, query, agent_id in common_queries:
            # This would typically call the RAG processor
            # For now, we'll just mark it as a warming operation
            self.cache_stats["warm_attempts"] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = self.cache_stats["hits"] / total if total > 0 else 0
        
        return {
            "hits": self.cache_stats["hits"],
            "misses": self.cache_stats["misses"],
            "writes": self.cache_stats["writes"],
            "hit_rate": hit_rate,
            "warm_attempts": self.cache_stats["warm_attempts"]
        }


class RAGQualityMonitor:
    """Monitor and track RAG quality metrics"""
    
    def __init__(self):
        self.metrics = defaultdict(list)
        self.thresholds = {
            "min_relevance": 0.5,
            "min_coverage": 0.6,
            "max_latency_ms": 1000
        }
    
    async def track_retrieval(
        self,
        query: str,
        contexts_retrieved: int,
        avg_score: float,
        latency_ms: float,
        cache_hit: bool = False
    ):
        """Track RAG retrieval metrics"""
        self.metrics["retrievals"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "query_length": len(query),
            "contexts_retrieved": contexts_retrieved,
            "avg_score": avg_score,
            "latency_ms": latency_ms,
            "cache_hit": cache_hit
        })
        
        # Check thresholds
        if avg_score < self.thresholds["min_relevance"]:
            logger.warning(
                f"Low relevance score: {avg_score:.2f}",
                query=query[:50]
            )
        
        if latency_ms > self.thresholds["max_latency_ms"]:
            logger.warning(
                f"High retrieval latency: {latency_ms}ms",
                query=query[:50]
            )
    
    async def track_agent_filter_effectiveness(
        self,
        agent_name: str,
        pre_filter_count: int,
        post_filter_count: int,
        avg_score_improvement: float
    ):
        """Track per-agent filter effectiveness"""
        self.metrics["agent_filters"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "agent_name": agent_name,
            "pre_filter_count": pre_filter_count,
            "post_filter_count": post_filter_count,
            "reduction_ratio": 1 - (post_filter_count / pre_filter_count) if pre_filter_count > 0 else 0,
            "avg_score_improvement": avg_score_improvement
        })
    
    def get_quality_report(self) -> Dict[str, Any]:
        """Generate quality report"""
        retrievals = self.metrics["retrievals"][-100:]  # Last 100
        
        if not retrievals:
            return {"status": "no_data"}
        
        return {
            "total_retrievals": len(retrievals),
            "avg_latency_ms": sum(r["latency_ms"] for r in retrievals) / len(retrievals),
            "avg_score": sum(r["avg_score"] for r in retrievals) / len(retrievals),
            "cache_hit_rate": sum(1 for r in retrievals if r["cache_hit"]) / len(retrievals),
            "avg_contexts": sum(r["contexts_retrieved"] for r in retrievals) / len(retrievals),
            "threshold_violations": {
                "low_relevance": sum(1 for r in retrievals if r["avg_score"] < self.thresholds["min_relevance"]),
                "high_latency": sum(1 for r in retrievals if r["latency_ms"] > self.thresholds["max_latency_ms"])
            }
        }


# Agent filter registry
AGENT_FILTERS = {
    "ali_chief_of_staff": PerAgentFilter(
        agent_name="ali_chief_of_staff",
        agent_type="strategic",
        max_facts=7,
        required_memory_types=["conversation", "knowledge"],
        keyword_priorities={"strategy": 1.5, "plan": 1.3, "goal": 1.2},
        importance_weight=0.5,
        relevance_weight=0.3
    ),
    "amy_cfo": PerAgentFilter(
        agent_name="amy_cfo",
        agent_type="financial",
        max_facts=5,
        required_memory_types=["knowledge", "context"],
        excluded_memory_types=["relationships"],
        keyword_priorities={"revenue": 1.5, "cost": 1.4, "budget": 1.3, "financial": 1.2},
        importance_weight=0.4,
        relevance_weight=0.4
    ),
    "diana_performance_dashboard": PerAgentFilter(
        agent_name="diana_performance_dashboard",
        agent_type="operational",
        max_facts=6,
        keyword_priorities={"metrics": 1.5, "performance": 1.4, "kpi": 1.3, "data": 1.2},
        recency_weight=0.5,
        relevance_weight=0.3
    ),
    "luca_security_expert": PerAgentFilter(
        agent_name="luca_security_expert",
        agent_type="technical",
        max_facts=4,
        required_memory_types=["knowledge", "context"],
        keyword_priorities={"security": 2.0, "vulnerability": 1.8, "risk": 1.5, "threat": 1.5},
        importance_weight=0.6,
        relevance_weight=0.3
    ),
    "wanda_workflow_orchestrator": PerAgentFilter(
        agent_name="wanda_workflow_orchestrator",
        agent_type="operational",
        max_facts=5,
        keyword_priorities={"workflow": 1.5, "process": 1.3, "automation": 1.2},
        recency_weight=0.4,
        importance_weight=0.3
    )
}


def get_agent_filter(agent_name: str) -> Optional[PerAgentFilter]:
    """Get agent-specific filter configuration"""
    return AGENT_FILTERS.get(agent_name)


__all__ = [
    "DynamicThreshold",
    "PerAgentFilter",
    "SemanticDeduplicator",
    "IntelligentRAGCache",
    "RAGQualityMonitor",
    "AGENT_FILTERS",
    "get_agent_filter"
]