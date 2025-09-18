"""
Turn-by-Turn Speaker Selection Integration
Integrates intelligent speaker selection into each turn of GroupChat execution
"""

import asyncio
from typing import List, Dict, Any, Optional, Sequence, Callable
from datetime import datetime
import structlog

from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage, ChatMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient

from .selection_policy import (
    IntelligentSpeakerSelector,
    SelectionContext,
    MissionPhase,
    ExpertiseDomain
)
from .selection_metrics import record_selection_metrics, get_selection_history
from src.agents.utils.tracing import start_span
from src.agents.utils.config import get_settings

logger = structlog.get_logger()


class TurnByTurnSelectorGroupChat(SelectorGroupChat):
    """
    Extended SelectorGroupChat with turn-by-turn intelligent speaker selection.
    Overrides the default selection mechanism to use our intelligent policy.
    """
    
    def __init__(
        self,
        participants: Sequence[AssistantAgent],
        model_client: OpenAIChatCompletionClient,
        selector: Optional[IntelligentSpeakerSelector] = None,
        enable_intelligent_selection: bool = True,
        **kwargs
    ):
        super().__init__(
            participants=participants,
            model_client=model_client,
            **kwargs
        )
        
        # Initialize intelligent selector
        self.intelligent_selector = selector or IntelligentSpeakerSelector()
        self.enable_intelligent_selection = enable_intelligent_selection
        self.turn_count = 0
        self.conversation_history = []
        self.current_phase = MissionPhase.DISCOVERY
        self.previous_speakers = []
        self.settings = get_settings()
        
        # Performance tracking
        self.selection_times = []
        self.selection_scores = []
        
        logger.info(
            "🎯 TurnByTurnSelectorGroupChat initialized",
            intelligent_selection=enable_intelligent_selection,
            num_participants=len(participants)
        )
    
    async def select_speaker(
        self,
        messages: Sequence[ChatMessage]
    ) -> AssistantAgent:
        """
        Override speaker selection to use intelligent policy per turn.
        This method is called at each turn to determine the next speaker.
        """
        
        self.turn_count += 1
        
        with start_span("speaker_selection.turn_by_turn", {
            "turn": self.turn_count,
            "intelligent_enabled": self.enable_intelligent_selection
        }):
            # If intelligent selection is disabled, use default
            if not self.enable_intelligent_selection or not self.settings.speaker_policy_enabled:
                logger.debug(f"Turn {self.turn_count}: Using default selection")
                return await super().select_speaker(messages)
            
            try:
                # Extract message content
                last_message = messages[-1] if messages else None
                message_content = ""
                if last_message and hasattr(last_message, 'content'):
                    message_content = last_message.content
                
                # Build selection context
                context = self._build_selection_context(message_content, messages)
                
                # Use intelligent selector to choose next speaker
                start_time = datetime.utcnow()
                selected_agent = await self._intelligent_select(context)
                selection_time = (datetime.utcnow() - start_time).total_seconds()
                
                # Track performance
                self.selection_times.append(selection_time)
                self.previous_speakers.append(selected_agent.name)
                
                # Record metrics
                await self._record_selection_metrics(
                    selected_agent.name,
                    context,
                    selection_time
                )
                
                logger.info(
                    f"🎯 Turn {self.turn_count}: Selected {selected_agent.name}",
                    phase=context.current_mission_phase.value,
                    selection_time_ms=int(selection_time * 1000)
                )
                
                return selected_agent
                
            except Exception as e:
                logger.error(
                    f"Turn {self.turn_count}: Intelligent selection failed",
                    error=str(e)
                )
                # Fallback to default selection
                return await super().select_speaker(messages)
    
    def _build_selection_context(
        self,
        message_content: str,
        messages: Sequence[ChatMessage]
    ) -> SelectionContext:
        """Build comprehensive context for selection decision"""
        
        # Update conversation history
        self.conversation_history = [
            {
                "turn": i,
                "speaker": msg.source if hasattr(msg, 'source') else "unknown",
                "content": msg.content[:200] if hasattr(msg, 'content') else "",
                "timestamp": datetime.utcnow().isoformat()
            }
            for i, msg in enumerate(messages[-10:])  # Last 10 messages
        ]
        
        # Detect mission phase from conversation
        self.current_phase = self._detect_mission_phase(message_content, self.conversation_history)
        
        # Calculate conversation complexity
        complexity = self._calculate_complexity(message_content, len(messages))
        
        # Determine required expertise
        required_expertise = self._extract_required_expertise(message_content)
        
        # Calculate urgency
        urgency = self._calculate_urgency(message_content)
        
        return SelectionContext(
            message_content=message_content,
            conversation_history=self.conversation_history,
            current_mission_phase=self.current_phase,
            previous_speakers=self.previous_speakers[-5:],  # Last 5 speakers
            conversation_complexity=complexity,
            urgency_level=urgency,
            required_expertise=required_expertise,
            collaboration_needed=self._needs_collaboration(message_content),
            user_preferences={}
        )
    
    async def _intelligent_select(self, context: SelectionContext) -> AssistantAgent:
        """Use intelligent selector to choose the best agent"""
        
        # Get agent scores from intelligent selector
        agent_scores = {}
        
        for participant in self.participants:
            if participant.name in self.intelligent_selector.agent_capabilities:
                score = await self.intelligent_selector.score_agent(
                    agent_name=participant.name,
                    context=context
                )
                agent_scores[participant.name] = score
        
        # Apply turn-based adjustments
        agent_scores = self._apply_turn_adjustments(agent_scores, context)
        
        # Select highest scoring agent
        if agent_scores:
            best_agent_name = max(agent_scores, key=agent_scores.get)
            best_score = agent_scores[best_agent_name]
            
            # Track score
            self.selection_scores.append(best_score)
            
            # Find and return the agent
            for participant in self.participants:
                if participant.name == best_agent_name:
                    logger.debug(
                        f"Selected {best_agent_name} with score {best_score:.2f}",
                        all_scores=agent_scores
                    )
                    return participant
        
        # Fallback to first participant
        logger.warning("No agent scored, using fallback")
        return self.participants[0]
    
    def _apply_turn_adjustments(
        self,
        agent_scores: Dict[str, float],
        context: SelectionContext
    ) -> Dict[str, float]:
        """Apply turn-specific adjustments to agent scores"""
        
        adjusted_scores = agent_scores.copy()
        
        # Penalize recent speakers to encourage diversity
        for agent_name in adjusted_scores:
            if agent_name in context.previous_speakers:
                recency_index = context.previous_speakers.index(agent_name)
                penalty = 0.2 * (1 - recency_index / len(context.previous_speakers))
                adjusted_scores[agent_name] *= (1 - penalty)
        
        # Boost scores based on turn number and phase
        if self.turn_count <= 3:
            # Early turns: boost discovery/analysis agents
            for agent_name in adjusted_scores:
                cap = self.intelligent_selector.agent_capabilities.get(agent_name)
                if cap and cap.mission_phase_relevance.get(MissionPhase.DISCOVERY, 0) > 0.7:
                    adjusted_scores[agent_name] *= 1.2
        
        elif self.turn_count > 10:
            # Later turns: boost execution/monitoring agents
            for agent_name in adjusted_scores:
                cap = self.intelligent_selector.agent_capabilities.get(agent_name)
                if cap and cap.mission_phase_relevance.get(MissionPhase.EXECUTION, 0) > 0.7:
                    adjusted_scores[agent_name] *= 1.15
        
        # Apply urgency boost
        if context.urgency_level > 0.7:
            for agent_name in adjusted_scores:
                cap = self.intelligent_selector.agent_capabilities.get(agent_name)
                if cap and cap.avg_response_time < 2.0:  # Fast responders
                    adjusted_scores[agent_name] *= 1.1
        
        return adjusted_scores
    
    def _detect_mission_phase(
        self,
        message: str,
        history: List[Dict[str, Any]]
    ) -> MissionPhase:
        """Detect current mission phase from conversation"""
        
        message_lower = message.lower()
        
        # Phase detection keywords
        phase_keywords = {
            MissionPhase.DISCOVERY: ["explore", "understand", "investigate", "research", "identify"],
            MissionPhase.ANALYSIS: ["analyze", "evaluate", "assess", "review", "examine"],
            MissionPhase.STRATEGY: ["strategy", "plan", "roadmap", "approach", "design"],
            MissionPhase.EXECUTION: ["implement", "execute", "deploy", "launch", "deliver"],
            MissionPhase.MONITORING: ["monitor", "track", "measure", "observe", "report"],
            MissionPhase.OPTIMIZATION: ["optimize", "improve", "enhance", "refine", "tune"]
        }
        
        # Count keyword matches
        phase_scores = {}
        for phase, keywords in phase_keywords.items():
            score = sum(1 for keyword in keywords if keyword in message_lower)
            phase_scores[phase] = score
        
        # Consider conversation progression
        if self.turn_count <= 3:
            phase_scores[MissionPhase.DISCOVERY] += 2
        elif self.turn_count <= 6:
            phase_scores[MissionPhase.ANALYSIS] += 2
        elif self.turn_count <= 10:
            phase_scores[MissionPhase.STRATEGY] += 1
        else:
            phase_scores[MissionPhase.EXECUTION] += 1
        
        # Return phase with highest score
        if phase_scores:
            return max(phase_scores, key=phase_scores.get)
        
        return self.current_phase  # Keep current if no clear indication
    
    def _calculate_complexity(self, message: str, num_messages: int) -> float:
        """Calculate conversation complexity (0.0-1.0)"""
        
        complexity = 0.0
        
        # Message length complexity
        if len(message) > 500:
            complexity += 0.2
        if len(message) > 1000:
            complexity += 0.2
        
        # Conversation depth
        if num_messages > 10:
            complexity += 0.2
        if num_messages > 20:
            complexity += 0.1
        
        # Technical terms
        technical_terms = ["api", "integration", "architecture", "implementation", "algorithm",
                          "optimization", "infrastructure", "deployment", "security", "compliance"]
        technical_count = sum(1 for term in technical_terms if term in message.lower())
        complexity += min(0.3, technical_count * 0.05)
        
        return min(1.0, complexity)
    
    def _calculate_urgency(self, message: str) -> float:
        """Calculate urgency level (0.0-1.0)"""
        
        urgency = 0.0
        message_lower = message.lower()
        
        # Urgency indicators
        if any(word in message_lower for word in ["urgent", "asap", "immediately", "critical"]):
            urgency += 0.5
        if any(word in message_lower for word in ["deadline", "today", "now", "quickly"]):
            urgency += 0.3
        if any(word in message_lower for word in ["important", "priority", "needed"]):
            urgency += 0.2
        
        return min(1.0, urgency)
    
    def _extract_required_expertise(self, message: str) -> set[ExpertiseDomain]:
        """Extract required expertise domains from message"""
        
        required = set()
        message_lower = message.lower()
        
        # Domain keyword mapping
        domain_keywords = {
            ExpertiseDomain.FINANCE: ["revenue", "cost", "budget", "financial", "roi", "profit"],
            ExpertiseDomain.STRATEGY: ["strategy", "vision", "roadmap", "planning", "goals"],
            ExpertiseDomain.TECHNOLOGY: ["technical", "api", "system", "software", "infrastructure"],
            ExpertiseDomain.SECURITY: ["security", "risk", "compliance", "vulnerability", "threat"],
            ExpertiseDomain.ANALYTICS: ["metrics", "data", "analysis", "insights", "dashboard"],
            ExpertiseDomain.OPERATIONS: ["process", "workflow", "efficiency", "operations"],
            ExpertiseDomain.MARKETING: ["marketing", "campaign", "brand", "customer", "market"],
            ExpertiseDomain.SALES: ["sales", "revenue", "pipeline", "deals", "targets"]
        }
        
        for domain, keywords in domain_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                required.add(domain)
        
        return required
    
    def _needs_collaboration(self, message: str) -> bool:
        """Determine if the message requires multi-agent collaboration"""
        
        collaboration_indicators = [
            "collaborate", "together", "coordinate", "team", "joint",
            "multiple", "various", "cross-functional", "integrate"
        ]
        
        return any(indicator in message.lower() for indicator in collaboration_indicators)
    
    async def _record_selection_metrics(
        self,
        selected_agent: str,
        context: SelectionContext,
        selection_time: float
    ):
        """Record detailed selection metrics"""
        
        metrics = {
            "turn": self.turn_count,
            "selected_agent": selected_agent,
            "phase": context.current_mission_phase.value,
            "complexity": context.conversation_complexity,
            "urgency": context.urgency_level,
            "selection_time_ms": int(selection_time * 1000),
            "required_expertise": [e.value for e in context.required_expertise],
            "collaboration_needed": context.collaboration_needed,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Record using existing metrics system
        await record_selection_metrics(
            conversation_id=f"turn_{self.turn_count}",
            agent_name=selected_agent,
            score=self.selection_scores[-1] if self.selection_scores else 0.0,
            reason=f"Phase: {context.current_mission_phase.value}",
            metadata=metrics
        )
    
    def get_selection_performance(self) -> Dict[str, Any]:
        """Get performance metrics for the selection process"""
        
        if not self.selection_times:
            return {}
        
        avg_time = sum(self.selection_times) / len(self.selection_times)
        avg_score = sum(self.selection_scores) / len(self.selection_scores) if self.selection_scores else 0
        
        # Calculate speaker diversity
        unique_speakers = len(set(self.previous_speakers))
        diversity_score = unique_speakers / len(self.previous_speakers) if self.previous_speakers else 0
        
        return {
            "total_turns": self.turn_count,
            "avg_selection_time_ms": int(avg_time * 1000),
            "avg_selection_score": avg_score,
            "speaker_diversity": diversity_score,
            "unique_speakers": unique_speakers,
            "selection_times_p95": sorted(self.selection_times)[int(len(self.selection_times) * 0.95)] if len(self.selection_times) > 1 else avg_time,
            "current_phase": self.current_phase.value
        }


# Extension to IntelligentSpeakerSelector for scoring
async def score_agent(self, agent_name: str, context: SelectionContext) -> float:
    """Score an agent for the given context"""
    
    if agent_name not in self.agent_capabilities:
        return 0.0
    
    capability = self.agent_capabilities[agent_name]
    score = 0.0
    
    # Phase relevance (25%)
    phase_score = capability.mission_phase_relevance.get(context.current_mission_phase, 0.5)
    score += phase_score * 0.25
    
    # Expertise match (30%)
    expertise_match = len(capability.expertise_domains.intersection(context.required_expertise))
    expertise_score = min(1.0, expertise_match / max(1, len(context.required_expertise)))
    score += expertise_score * 0.30
    
    # Keyword relevance (20%)
    message_words = set(context.message_content.lower().split())
    keyword_match = len(capability.specialization_keywords.intersection(message_words))
    keyword_score = min(1.0, keyword_match / max(1, len(capability.specialization_keywords)))
    score += keyword_score * 0.20
    
    # Complexity handling (10%)
    complexity_score = 1.0 if capability.complexity_handling >= context.conversation_complexity else 0.5
    score += complexity_score * 0.10
    
    # Historical performance (10%)
    score += capability.response_quality_history * 0.10
    
    # Urgency factor (5%)
    if context.urgency_level > 0.7 and capability.avg_response_time < 2.0:
        score += 0.05
    
    return score


# Monkey-patch the scoring method to IntelligentSpeakerSelector
IntelligentSpeakerSelector.score_agent = score_agent


def create_turn_by_turn_groupchat(
    participants: List[AssistantAgent],
    model_client: OpenAIChatCompletionClient,
    max_turns: int,
    enable_intelligent_selection: bool = True,
    selector: Optional[IntelligentSpeakerSelector] = None
) -> TurnByTurnSelectorGroupChat:
    """Factory function to create turn-by-turn selector group chat"""
    
    return TurnByTurnSelectorGroupChat(
        participants=participants,
        model_client=model_client,
        max_turns=max_turns,
        selector=selector,
        enable_intelligent_selection=enable_intelligent_selection,
        allow_repeated_speaker=False
    )


__all__ = [
    "TurnByTurnSelectorGroupChat",
    "create_turn_by_turn_groupchat"
]