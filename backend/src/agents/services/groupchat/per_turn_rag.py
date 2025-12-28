"""
Per-Turn RAG Injection - Injects context at every conversation turn
Ensures RAG context is updated and injected before each agent turn, not just at conversation start.
"""

from typing import Dict, Any, Optional, List, AsyncGenerator
from datetime import datetime
import hashlib

import structlog

# Conditional imports for framework compatibility
try:
    from autogen_agentchat.messages import TextMessage
    from autogen_agentchat.teams import SelectorGroupChat
    AUTOGEN_AVAILABLE = True
except ImportError:
    # Fallback for Agent Framework migration
    TextMessage = None
    SelectorGroupChat = None
    AUTOGEN_AVAILABLE = False

from .rag import AdvancedRAGProcessor
from src.agents.utils.tracing import start_span
from .conflict_detector import detect_conflicts

logger = structlog.get_logger()


class PerTurnRAGInjector:
    """Injects RAG context before each turn in the conversation"""
    
    def __init__(
        self,
        rag_processor: AdvancedRAGProcessor,
        memory_system: Any,
        settings: Any
    ):
        self.rag_processor = rag_processor
        self.memory_system = memory_system
        self.settings = settings
        
        # Cache to avoid redundant context generation
        self.context_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl_seconds = 60  # Cache context for 1 minute
        
        # Track turns for context evolution
        self.turn_history: Dict[str, List[Dict[str, Any]]] = {}
        # Shared scratchpad per conversation (append-only)
        self.scratchpad: Dict[str, List[str]] = {}
        
        logger.info("📚 Per-turn RAG injector initialized")
    
    async def inject_context_for_turn(
        self,
        conversation_id: str,
        user_id: str,
        agent_name: str,
        turn_number: int,
        current_message: str,
        conversation_history: List[Dict[str, Any]]
    ) -> str:
        """
        Inject RAG context for a specific turn
        
        Returns enhanced message with relevant context
        """
        
        if not self.settings.rag_in_loop_enabled:
            return current_message
        
        with start_span("rag.per_turn_injection", {
            "conversation_id": conversation_id,
            "turn": turn_number,
            "agent": agent_name
        }):
            try:
                # Generate cache key
                cache_key = self._generate_cache_key(
                    conversation_id, user_id, agent_name, turn_number, current_message
                )
                
                # Check cache
                if cache_key in self.context_cache:
                    cached = self.context_cache[cache_key]
                    if (datetime.utcnow() - cached["timestamp"]).seconds < self.cache_ttl_seconds:
                        logger.debug("Using cached context", turn=turn_number, agent=agent_name)
                        return cached["enhanced_message"]
                
                # Build fresh context
                context = await self._build_turn_context(
                    user_id=user_id,
                    agent_name=agent_name,
                    turn_number=turn_number,
                    current_message=current_message,
                    conversation_history=conversation_history
                )
                
                # Conflict detection over recent history
                conflicts = detect_conflicts(conversation_history, window=6)
                if conflicts:
                    context.setdefault("insights", []).append(
                        f"Detected {len(conflicts)} potential conflicts across recent turns"
                    )
                
                # Enhance message with context
                enhanced_message = self._enhance_message_with_context(
                    current_message, context, turn_number, agent_name
                )
                
                # Append to shared scratchpad (append-only)
                self.scratchpad.setdefault(conversation_id, []).append(
                    f"Turn {turn_number} · {agent_name}: {current_message[:160]}"
                )
                
                # Cache result
                self.context_cache[cache_key] = {
                    "enhanced_message": enhanced_message,
                    "timestamp": datetime.utcnow(),
                    "context": context
                }
                
                # Track turn
                self._track_turn(conversation_id, turn_number, agent_name, context)
                
                logger.info(
                    "💉 Injected per-turn context",
                    turn=turn_number,
                    agent=agent_name,
                    context_items=len(context.get("facts", [])),
                    history_items=len(context.get("history", []))
                )
                
                return enhanced_message
                
            except Exception as e:
                logger.warning(
                    "Failed to inject per-turn context",
                    turn=turn_number,
                    agent=agent_name,
                    error=str(e)
                )
                return current_message
    
    async def _build_turn_context(
        self,
        user_id: str,
        agent_name: str,
        turn_number: int,
        current_message: str,
        conversation_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Build context specific to this turn"""
        
        # Determine context window based on turn number
        context_window = min(5, turn_number)  # Look back at most 5 turns
        recent_history = conversation_history[-context_window:] if conversation_history else []
        
        # Build query combining current message and recent context
        query_parts = [current_message]
        for entry in recent_history:
            if "content" in entry:
                query_parts.append(entry["content"][:200])  # Limit each to 200 chars
        
        combined_query = " ".join(query_parts)
        
        # Get memory context with turn-specific parameters
        memory_context = await self.rag_processor.build_memory_context(
            user_id=user_id,
            agent_id=agent_name,
            query=combined_query,
            limit=self.settings.rag_max_facts,
            similarity_threshold=self.settings.rag_similarity_threshold,
            # Adjust weights based on turn number
            recency_weight=0.4 if turn_number > 3 else 0.3,
            importance_weight=0.4,
            relevance_weight=0.2 if turn_number > 3 else 0.3,
            # Include more history in later turns
            include_conversation_history=(turn_number > 1),
            include_knowledge_base=True
        )
        
        context = {
            "facts": [],
            "history": [],
            "insights": []
        }
        
        if memory_context and memory_context.content:
            # Parse memory context
            context = self._parse_memory_context(memory_context.content)
            
            # Add turn-specific insights
            if turn_number > 3:
                context["insights"].append(
                    f"Note: This is turn {turn_number} of the conversation. Consider summarizing key points."
                )
            
            # Add agent-specific context
            context["agent_context"] = self._get_agent_specific_context(agent_name)
        
        return context
    
    def _parse_memory_context(self, content: str) -> Dict[str, Any]:
        """Parse memory context into structured format"""
        
        context = {
            "facts": [],
            "history": [],
            "insights": []
        }
        
        lines = content.split("\n")
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if "fact" in line.lower() or "knowledge" in line.lower():
                current_section = "facts"
            elif "history" in line.lower() or "previous" in line.lower():
                current_section = "history"
            elif "insight" in line.lower() or "note" in line.lower():
                current_section = "insights"
            elif current_section and line.startswith("-"):
                context[current_section].append(line[1:].strip())
            elif current_section:
                context[current_section].append(line)
        
        return context
    
    def _get_agent_specific_context(self, agent_name: str) -> Dict[str, Any]:
        """Get context specific to the agent's role"""
        
        agent_contexts = {
            "ali_chief_of_staff": {
                "focus": "strategic alignment and coordination",
                "consider": ["priorities", "resources", "timeline", "dependencies"]
            },
            "amy_cfo": {
                "focus": "financial implications and budgeting",
                "consider": ["costs", "ROI", "budget", "financial risks"]
            },
            "luca_security_expert": {
                "focus": "security and compliance",
                "consider": ["risks", "vulnerabilities", "compliance", "data protection"]
            },
            "domik_mckinsey_strategic_decision_maker": {
                "focus": "strategic analysis and recommendations",
                "consider": ["market dynamics", "competitive positioning", "opportunities"]
            },
            "diana_performance_dashboard": {
                "focus": "metrics and performance tracking",
                "consider": ["KPIs", "trends", "benchmarks", "insights"]
            },
            "wanda_workflow_orchestrator": {
                "focus": "process optimization and coordination",
                "consider": ["workflows", "efficiency", "automation", "integration"]
            }
        }
        
        return agent_contexts.get(agent_name, {
            "focus": "general assistance",
            "consider": ["user needs", "clarity", "accuracy"]
        })
    
    def _enhance_message_with_context(
        self,
        message: str,
        context: Dict[str, Any],
        turn_number: int,
        agent_name: str
    ) -> str:
        """Enhance message with retrieved context"""
        
        enhanced_parts = []
        
        # Add original message
        enhanced_parts.append(message)
        
        # Add relevant facts
        if context.get("facts"):
            enhanced_parts.append("\n📌 Relevant Context:")
            for fact in context["facts"][:3]:  # Limit to top 3 facts
                enhanced_parts.append(f"- {fact}")
        
        # Add conversation history insights
        if context.get("history") and turn_number > 1:
            enhanced_parts.append("\n📜 Previous Discussion Points:")
            for item in context["history"][:2]:  # Limit to 2 history items
                enhanced_parts.append(f"- {item}")
        
        # Add turn-specific insights
        if context.get("insights"):
            enhanced_parts.append("\n💡 Considerations:")
            for insight in context["insights"]:
                enhanced_parts.append(f"- {insight}")
        
        # Add agent-specific guidance
        agent_context = context.get("agent_context", {})
        if agent_context:
            enhanced_parts.append(f"\n🎯 Focus Area: {agent_context.get('focus', 'general')}")
            if agent_context.get("consider"):
                enhanced_parts.append(f"Consider: {', '.join(agent_context['consider'])}")
        
        return "\n".join(enhanced_parts)
    
    def _generate_cache_key(
        self,
        conversation_id: str,
        user_id: str,
        agent_name: str,
        turn_number: int,
        message: str
    ) -> str:
        """Generate cache key for context"""
        
        key_parts = [
            conversation_id,
            user_id,
            agent_name,
            str(turn_number),
            message[:100]  # First 100 chars of message
        ]
        
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _track_turn(
        self,
        conversation_id: str,
        turn_number: int,
        agent_name: str,
        context: Dict[str, Any]
    ):
        """Track turn for analysis"""
        
        if conversation_id not in self.turn_history:
            self.turn_history[conversation_id] = []
        
        self.turn_history[conversation_id].append({
            "turn": turn_number,
            "agent": agent_name,
            "timestamp": datetime.utcnow(),
            "context_facts": len(context.get("facts", [])),
            "context_history": len(context.get("history", [])),
            "context_insights": len(context.get("insights", []))
        })
        
        # Keep only last 50 turns per conversation
        if len(self.turn_history[conversation_id]) > 50:
            self.turn_history[conversation_id] = self.turn_history[conversation_id][-50:]
    
    def clear_cache(self, conversation_id: Optional[str] = None):
        """Clear context cache"""
        
        if conversation_id:
            # Clear specific conversation
            keys_to_remove = [
                key for key in self.context_cache.keys()
                if conversation_id in key
            ]
            for key in keys_to_remove:
                del self.context_cache[key]
            
            if conversation_id in self.turn_history:
                del self.turn_history[conversation_id]
        else:
            # Clear all
            self.context_cache.clear()
            self.turn_history.clear()
        
        logger.info("Cleared RAG cache", conversation_id=conversation_id)

    def _init_scratchpad(self, conversation_id: str) -> None:
        if conversation_id not in self.scratchpad:
            self.scratchpad[conversation_id] = {
                "constraints": [],
                "assumptions": [],
                "decisions": []
            }

    def _update_scratchpad(self, conversation_id: str, agent_name: str, turn_number: int, message: str) -> None:
        pad = self.scratchpad.get(conversation_id)
        if not pad:
            return
        # Heuristics: collect lines starting with markers or containing key words
        lowered = message.lower()
        if any(k in lowered for k in ["must", "require", "constraint", "deadline", "sla"]):
            pad["constraints"].append({"turn": turn_number, "agent": agent_name, "text": message[:200]})
        if any(k in lowered for k in ["assume", "we think", "likely", "hypothesis"]):
            pad["assumptions"].append({"turn": turn_number, "agent": agent_name, "text": message[:200]})
        if any(k in lowered for k in ["decide", "we will", "let's", "decision"]):
            pad["decisions"].append({"turn": turn_number, "agent": agent_name, "text": message[:200]})

        # Keep scratchpad bounded
        for key in ("constraints", "assumptions", "decisions"):
            if len(pad[key]) > 10:
                pad[key] = pad[key][-10:]

    def _detect_conflicts(self, conversation_id: str) -> List[str]:
        """Lightweight conflict detector over recent turns"""
        history = self.turn_history.get(conversation_id, [])
        if len(history) < 2:
            return []
        last_two = history[-2:]
        a = (last_two[0].get("content") or "").lower()
        b = (last_two[1].get("content") or "").lower()
        conflicts = []
        # Naive polarity check
        keywords = ["feasible", "secure", "available", "supported", "ready", "blocked"]
        for kw in keywords:
            if (kw in a and f"not {kw}" in b) or (f"not {kw}" in a and kw in b):
                conflicts.append(f"Potential conflict on '{kw}' between last two turns")
        return conflicts

    def _attach_scratchpad(self, message: str, conversation_id: str, conflicts: List[str]) -> str:
        pad = self.scratchpad.get(conversation_id, {})
        parts = [message]
        if pad:
            parts.append("\n🗒️ Scratchpad:")
            if pad.get("constraints"):
                parts.append("- Constraints: " + "; ".join(x["text"] for x in pad["constraints"][-3:]))
            if pad.get("assumptions"):
                parts.append("- Assumptions: " + "; ".join(x["text"] for x in pad["assumptions"][-3:]))
            if pad.get("decisions"):
                parts.append("- Decisions: " + "; ".join(x["text"] for x in pad["decisions"][-3:]))
        if conflicts:
            parts.append("\n⚠️ Potential Conflicts: " + "; ".join(conflicts))
        return "\n".join(parts)
    
    def get_turn_metrics(self, conversation_id: str) -> Dict[str, Any]:
        """Get metrics for turns in a conversation"""
        
        if conversation_id not in self.turn_history:
            return {}
        
        turns = self.turn_history[conversation_id]
        
        if not turns:
            return {}
        
        return {
            "total_turns": len(turns),
            "unique_agents": len(set(t["agent"] for t in turns)),
            "avg_facts_per_turn": sum(t["context_facts"] for t in turns) / len(turns),
            "avg_history_per_turn": sum(t["context_history"] for t in turns) / len(turns),
            "turns_with_insights": sum(1 for t in turns if t["context_insights"] > 0)
        }


class RAGEnhancedGroupChat(SelectorGroupChat):
    """Extended GroupChat with per-turn RAG injection"""
    
    def __init__(self, *args, rag_injector: Optional[PerTurnRAGInjector] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.rag_injector = rag_injector
        self.conversation_id = str(datetime.utcnow().timestamp())
        self.user_id = "default"
        self.turn_count = 0
        
    async def run_stream(
        self,
        task: str,
        *,
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> AsyncGenerator[Any, None]:
        """Override run_stream to inject RAG context per turn"""
        
        if conversation_id:
            self.conversation_id = conversation_id
        if user_id:
            self.user_id = user_id
        
        # Track conversation history
        conversation_history = []
        
        async for message in super().run_stream(task=task):
            self.turn_count += 1
            
            # If we have a RAG injector and the message is from an agent
            if self.rag_injector and hasattr(message, 'source') and hasattr(message, 'content'):
                # Inject context for this turn
                enhanced_content = await self.rag_injector.inject_context_for_turn(
                    conversation_id=self.conversation_id,
                    user_id=self.user_id,
                    agent_name=message.source,
                    turn_number=self.turn_count,
                    current_message=message.content,
                    conversation_history=conversation_history
                )
                
                # Update message with enhanced content
                message.content = enhanced_content
                
                # Track history
                conversation_history.append({
                    "turn": self.turn_count,
                    "agent": message.source,
                    "content": message.content[:500]  # Store first 500 chars
                })
            
            yield message


# Global per-turn RAG injector
_per_turn_rag_injector: Optional[PerTurnRAGInjector] = None


def initialize_per_turn_rag(
    rag_processor: AdvancedRAGProcessor,
    memory_system: Any,
    settings: Any
) -> PerTurnRAGInjector:
    """Initialize global per-turn RAG injector"""
    global _per_turn_rag_injector
    _per_turn_rag_injector = PerTurnRAGInjector(rag_processor, memory_system, settings)
    return _per_turn_rag_injector


def get_per_turn_rag_injector() -> Optional[PerTurnRAGInjector]:
    """Get global per-turn RAG injector"""
    return _per_turn_rag_injector


__all__ = [
    "PerTurnRAGInjector",
    "RAGEnhancedGroupChat",
    "initialize_per_turn_rag",
    "get_per_turn_rag_injector"
]