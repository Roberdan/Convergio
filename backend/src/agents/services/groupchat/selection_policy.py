"""
Advanced Speaker Selection Policy - Intelligent agent routing with multi-factor analysis
Chooses the next speaker based on message intent, agent capabilities, conversation history,
mission phase, and dynamic expertise scoring.
"""

import asyncio
import hashlib
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any, Set
from dataclasses import dataclass
from enum import Enum

import structlog

# AutoGen imports with fallback
try:
    from autogen_agentchat.agents import AssistantAgent
    from autogen_agentchat.messages import TextMessage
    AUTOGEN_AVAILABLE = True
except ImportError:
    AssistantAgent = None
    TextMessage = None
    AUTOGEN_AVAILABLE = False

from .selection_metrics import record_selection_metrics, get_selection_history
from ...tools.vector_search_client import embed_text, calculate_similarity

logger = structlog.get_logger()


class MissionPhase(Enum):
    """Business mission phases for context-aware selection"""
    DISCOVERY = "discovery"
    ANALYSIS = "analysis"
    STRATEGY = "strategy"
    EXECUTION = "execution"
    MONITORING = "monitoring"
    OPTIMIZATION = "optimization"


class ExpertiseDomain(Enum):
    """Agent expertise domains for capability matching"""
    STRATEGY = "strategy"
    FINANCE = "finance"
    OPERATIONS = "operations"
    TECHNOLOGY = "technology"
    MARKETING = "marketing"
    SALES = "sales"
    HR = "human_resources"
    LEGAL = "legal"
    SECURITY = "security"
    ANALYTICS = "analytics"
    PRODUCT = "product"
    DESIGN = "design"


@dataclass
class AgentCapability:
    """Detailed agent capability profile"""
    agent_name: str
    expertise_domains: Set[ExpertiseDomain]
    specialization_keywords: Set[str]
    mission_phase_relevance: Dict[MissionPhase, float]  # 0.0-1.0 relevance scores
    collaboration_preferences: Set[str]  # Preferred co-agents
    complexity_handling: float  # 0.0-1.0 complexity score
    response_quality_history: float  # Historical performance score
    avg_response_time: float  # Average response time in seconds


@dataclass
class SelectionContext:
    """Complete context for speaker selection decision"""
    message_content: str
    conversation_history: List[Dict[str, Any]]
    current_mission_phase: MissionPhase
    previous_speakers: List[str]
    conversation_complexity: float
    urgency_level: float  # 0.0-1.0
    required_expertise: Set[ExpertiseDomain]
    collaboration_needed: bool
    user_preferences: Dict[str, Any]


class IntelligentSpeakerSelector:
    """Advanced speaker selection with multi-factor analysis and learning"""
    
    def __init__(self):
        self.agent_capabilities: Dict[str, AgentCapability] = {}
        self.selection_history: List[Dict[str, Any]] = []
        self.performance_tracker: Dict[str, List[float]] = {}
        self._initialize_agent_capabilities()
        
    def _initialize_agent_capabilities(self):
        """Initialize comprehensive agent capability profiles"""
        
        capabilities = {
            "ali_chief_of_staff": AgentCapability(
                agent_name="ali_chief_of_staff",
                expertise_domains={ExpertiseDomain.STRATEGY, ExpertiseDomain.OPERATIONS},
                specialization_keywords={
                    "strategy", "vision", "planning", "coordination", "leadership",
                    "roadmap", "priorities", "alignment", "execution", "oversight"
                },
                mission_phase_relevance={
                    MissionPhase.DISCOVERY: 0.9,
                    MissionPhase.ANALYSIS: 0.8,
                    MissionPhase.STRATEGY: 1.0,
                    MissionPhase.EXECUTION: 0.9,
                    MissionPhase.MONITORING: 0.8,
                    MissionPhase.OPTIMIZATION: 0.7
                },
                collaboration_preferences={
                    "domik_mckinsey_strategic_decision_maker", "wanda_workflow_orchestrator"
                },
                complexity_handling=0.95,
                response_quality_history=0.9,
                avg_response_time=15.0
            ),
            
            "amy_cfo": AgentCapability(
                agent_name="amy_cfo",
                expertise_domains={ExpertiseDomain.FINANCE, ExpertiseDomain.ANALYTICS},
                specialization_keywords={
                    "budget", "cost", "finance", "revenue", "profit", "investment",
                    "roi", "cash flow", "financial", "accounting", "valuation", "metrics"
                },
                mission_phase_relevance={
                    MissionPhase.DISCOVERY: 0.6,
                    MissionPhase.ANALYSIS: 0.9,
                    MissionPhase.STRATEGY: 0.8,
                    MissionPhase.EXECUTION: 0.7,
                    MissionPhase.MONITORING: 0.9,
                    MissionPhase.OPTIMIZATION: 0.8
                },
                collaboration_preferences={"diana_performance_dashboard", "ali_chief_of_staff"},
                complexity_handling=0.85,
                response_quality_history=0.88,
                avg_response_time=12.0
            ),
            
            "luca_security_expert": AgentCapability(
                agent_name="luca_security_expert",
                expertise_domains={ExpertiseDomain.SECURITY, ExpertiseDomain.LEGAL},
                specialization_keywords={
                    "security", "risk", "compliance", "privacy", "data protection",
                    "audit", "governance", "threat", "vulnerability", "encryption"
                },
                mission_phase_relevance={
                    MissionPhase.DISCOVERY: 0.7,
                    MissionPhase.ANALYSIS: 0.9,
                    MissionPhase.STRATEGY: 0.6,
                    MissionPhase.EXECUTION: 0.8,
                    MissionPhase.MONITORING: 0.9,
                    MissionPhase.OPTIMIZATION: 0.7
                },
                collaboration_preferences={"amy_cfo", "xavier_coordination_patterns"},
                complexity_handling=0.9,
                response_quality_history=0.92,
                avg_response_time=10.0
            ),
            
            "domik_mckinsey_strategic_decision_maker": AgentCapability(
                agent_name="domik_mckinsey_strategic_decision_maker",
                expertise_domains={ExpertiseDomain.STRATEGY, ExpertiseDomain.ANALYTICS},
                specialization_keywords={
                    "analysis", "decision", "framework", "methodology", "consulting",
                    "market", "competitive", "strategic", "business model", "growth"
                },
                mission_phase_relevance={
                    MissionPhase.DISCOVERY: 0.8,
                    MissionPhase.ANALYSIS: 1.0,
                    MissionPhase.STRATEGY: 0.95,
                    MissionPhase.EXECUTION: 0.6,
                    MissionPhase.MONITORING: 0.7,
                    MissionPhase.OPTIMIZATION: 0.8
                },
                collaboration_preferences={"ali_chief_of_staff", "socrates_first_principles_reasoning"},
                complexity_handling=0.98,
                response_quality_history=0.94,
                avg_response_time=20.0
            ),
            
            "diana_performance_dashboard": AgentCapability(
                agent_name="diana_performance_dashboard",
                expertise_domains={ExpertiseDomain.ANALYTICS, ExpertiseDomain.OPERATIONS},
                specialization_keywords={
                    "metrics", "kpi", "dashboard", "performance", "data", "analytics",
                    "reporting", "insights", "trends", "visualization", "monitoring"
                },
                mission_phase_relevance={
                    MissionPhase.DISCOVERY: 0.5,
                    MissionPhase.ANALYSIS: 0.8,
                    MissionPhase.STRATEGY: 0.6,
                    MissionPhase.EXECUTION: 0.7,
                    MissionPhase.MONITORING: 1.0,
                    MissionPhase.OPTIMIZATION: 0.9
                },
                collaboration_preferences={"amy_cfo", "wanda_workflow_orchestrator"},
                complexity_handling=0.8,
                response_quality_history=0.85,
                avg_response_time=8.0
            ),
            
            "socrates_first_principles_reasoning": AgentCapability(
                agent_name="socrates_first_principles_reasoning",
                expertise_domains={ExpertiseDomain.STRATEGY, ExpertiseDomain.ANALYTICS},
                specialization_keywords={
                    "principles", "reasoning", "logic", "philosophy", "critical thinking",
                    "assumptions", "fundamentals", "questioning", "analysis", "truth"
                },
                mission_phase_relevance={
                    MissionPhase.DISCOVERY: 1.0,
                    MissionPhase.ANALYSIS: 0.95,
                    MissionPhase.STRATEGY: 0.8,
                    MissionPhase.EXECUTION: 0.5,
                    MissionPhase.MONITORING: 0.6,
                    MissionPhase.OPTIMIZATION: 0.7
                },
                collaboration_preferences={"domik_mckinsey_strategic_decision_maker"},
                complexity_handling=0.95,
                response_quality_history=0.91,
                avg_response_time=25.0
            ),
            
            "wanda_workflow_orchestrator": AgentCapability(
                agent_name="wanda_workflow_orchestrator",
                expertise_domains={ExpertiseDomain.OPERATIONS, ExpertiseDomain.PRODUCT},
                specialization_keywords={
                    "workflow", "process", "orchestration", "coordination", "automation",
                    "efficiency", "optimization", "procedures", "integration", "systems"
                },
                mission_phase_relevance={
                    MissionPhase.DISCOVERY: 0.6,
                    MissionPhase.ANALYSIS: 0.7,
                    MissionPhase.STRATEGY: 0.7,
                    MissionPhase.EXECUTION: 1.0,
                    MissionPhase.MONITORING: 0.8,
                    MissionPhase.OPTIMIZATION: 0.9
                },
                collaboration_preferences={"ali_chief_of_staff", "xavier_coordination_patterns"},
                complexity_handling=0.87,
                response_quality_history=0.86,
                avg_response_time=14.0
            ),
            
            "xavier_coordination_patterns": AgentCapability(
                agent_name="xavier_coordination_patterns",
                expertise_domains={ExpertiseDomain.OPERATIONS, ExpertiseDomain.TECHNOLOGY},
                specialization_keywords={
                    "coordination", "patterns", "architecture", "design", "integration",
                    "scalability", "reliability", "performance", "technical", "infrastructure"
                },
                mission_phase_relevance={
                    MissionPhase.DISCOVERY: 0.7,
                    MissionPhase.ANALYSIS: 0.8,
                    MissionPhase.STRATEGY: 0.6,
                    MissionPhase.EXECUTION: 0.9,
                    MissionPhase.MONITORING: 0.8,
                    MissionPhase.OPTIMIZATION: 0.85
                },
                collaboration_preferences={"wanda_workflow_orchestrator", "luca_security_expert"},
                complexity_handling=0.9,
                response_quality_history=0.88,
                avg_response_time=16.0
            )
        }
        
        self.agent_capabilities.update(capabilities)
    
    async def select_next_speaker(
        self,
        message_text: str,
        participants: List[AssistantAgent],
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        mission_phase: MissionPhase = MissionPhase.ANALYSIS,
        urgency_level: float = 0.5,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> Tuple[AssistantAgent, Dict[str, Any]]:
        """
        Intelligent speaker selection with comprehensive analysis
        
        Returns:
            Tuple of (selected_agent, selection_rationale)
        """
        
        try:
            # Build selection context
            context = await self._build_selection_context(
                message_text, conversation_history, mission_phase, 
                participants, urgency_level, user_preferences or {}
            )
            
            # Score all available agents
            agent_scores = await self._score_agents(participants, context)
            
            # Apply selection strategy
            selected_agent, rationale = await self._apply_selection_strategy(
                agent_scores, context, participants
            )
            
            # Record selection for learning
            await self._record_selection_decision(selected_agent, rationale, context)
            
            # Log selection decision
            logger.info(
                "🎯 Intelligent speaker selected",
                selected_agent=selected_agent.name,
                selection_reason=rationale.get('primary_reason'),
                confidence_score=rationale.get('confidence_score', 0.0),
                mission_phase=mission_phase.value,
                message_length=len(message_text)
            )
            
            return selected_agent, rationale
            
        except Exception as e:
            logger.error("Failed intelligent speaker selection", error=str(e))
            
            # Fallback to simple selection
            fallback_agent = self._fallback_selection(participants, message_text)
            fallback_rationale = {
                "primary_reason": "fallback_selection",
                "confidence_score": 0.3,
                "error": str(e)
            }
            
            return fallback_agent, fallback_rationale
    
    async def _build_selection_context(
        self,
        message_text: str,
        conversation_history: Optional[List[Dict[str, Any]]],
        mission_phase: MissionPhase,
        participants: List[AssistantAgent],
        urgency_level: float,
        user_preferences: Dict[str, Any]
    ) -> SelectionContext:
        """Build comprehensive selection context"""
        
        # Analyze message content
        required_expertise = await self._analyze_required_expertise(message_text)
        conversation_complexity = await self._calculate_conversation_complexity(
            message_text, conversation_history or []
        )
        
        # Determine collaboration needs
        collaboration_needed = await self._assess_collaboration_needs(
            message_text, required_expertise
        )
        
        # Extract previous speakers
        previous_speakers = []
        if conversation_history:
            previous_speakers = [
                entry.get('agent_name', '') for entry in conversation_history[-5:]
            ]
        
        return SelectionContext(
            message_content=message_text,
            conversation_history=conversation_history or [],
            current_mission_phase=mission_phase,
            previous_speakers=previous_speakers,
            conversation_complexity=conversation_complexity,
            urgency_level=urgency_level,
            required_expertise=required_expertise,
            collaboration_needed=collaboration_needed,
            user_preferences=user_preferences
        )
    
    async def _score_agents(
        self, 
        participants: List[AssistantAgent], 
        context: SelectionContext
    ) -> Dict[str, Dict[str, float]]:
        """Score agents across multiple dimensions"""
        
        scores = {}
        
        for agent in participants:
            agent_capability = self.agent_capabilities.get(agent.name)
            if not agent_capability:
                continue
            
            # Calculate individual scores
            expertise_score = await self._calculate_expertise_score(agent_capability, context)
            phase_relevance_score = agent_capability.mission_phase_relevance.get(
                context.current_mission_phase, 0.5
            )
            complexity_score = min(1.0, agent_capability.complexity_handling / context.conversation_complexity)
            collaboration_score = await self._calculate_collaboration_score(
                agent_capability, context
            )
            performance_score = agent_capability.response_quality_history
            recency_score = await self._calculate_recency_score(agent.name, context)
            urgency_score = await self._calculate_urgency_score(agent_capability, context)
            
            # Composite scoring with weights
            composite_score = (
                expertise_score * 0.25 +
                phase_relevance_score * 0.20 +
                complexity_score * 0.15 +
                collaboration_score * 0.15 +
                performance_score * 0.10 +
                recency_score * 0.10 +
                urgency_score * 0.05
            )
            
            scores[agent.name] = {
                'expertise': expertise_score,
                'phase_relevance': phase_relevance_score,
                'complexity_handling': complexity_score,
                'collaboration': collaboration_score,
                'performance': performance_score,
                'recency': recency_score,
                'urgency': urgency_score,
                'composite': composite_score
            }
        
        return scores
    
    async def _calculate_expertise_score(
        self, capability: AgentCapability, context: SelectionContext
    ) -> float:
        """Calculate expertise relevance score"""
        
        # Domain overlap score
        domain_overlap = len(capability.expertise_domains & context.required_expertise)
        domain_score = min(1.0, domain_overlap / max(1, len(context.required_expertise)))
        
        # Keyword matching score
        message_words = set(context.message_content.lower().split())
        keyword_overlap = len(capability.specialization_keywords & message_words)
        keyword_score = min(1.0, keyword_overlap / max(1, len(capability.specialization_keywords)))
        
        # Semantic similarity score (if available)
        semantic_score = await self._calculate_semantic_similarity(
            context.message_content, capability.specialization_keywords
        )
        
        # Combined expertise score
        return (domain_score * 0.4 + keyword_score * 0.4 + semantic_score * 0.2)
    
    async def _calculate_semantic_similarity(
        self, message: str, keywords: Set[str]
    ) -> float:
        """Calculate semantic similarity using embeddings"""
        
        try:
            message_embedding = await embed_text(message)
            keywords_text = " ".join(keywords)
            keywords_embedding = await embed_text(keywords_text)
            
            if message_embedding and keywords_embedding:
                similarity = calculate_similarity(message_embedding, keywords_embedding)
                return max(0.0, min(1.0, similarity))
                
        except Exception as e:
            logger.warning("Failed semantic similarity calculation", error=str(e))
        
        return 0.0
    
    async def _calculate_collaboration_score(
        self, capability: AgentCapability, context: SelectionContext
    ) -> float:
        """Calculate collaboration effectiveness score"""
        
        if not context.collaboration_needed:
            return 0.5
        
        # Check if preferred collaborators are in recent speakers
        preferred_present = len(
            capability.collaboration_preferences & set(context.previous_speakers[-3:])
        )
        
        collaboration_score = min(1.0, preferred_present / max(1, len(capability.collaboration_preferences)))
        return collaboration_score
    
    async def _calculate_recency_score(self, agent_name: str, context: SelectionContext) -> float:
        """Calculate recency-based score (avoid repeated selections)"""
        
        recent_speakers = context.previous_speakers[-3:]
        appearances = recent_speakers.count(agent_name)
        
        # Lower score for recently active agents
        if appearances == 0:
            return 1.0
        elif appearances == 1:
            return 0.7
        elif appearances == 2:
            return 0.4
        else:
            return 0.2
    
    async def _calculate_urgency_score(
        self, capability: AgentCapability, context: SelectionContext
    ) -> float:
        """Calculate urgency handling score"""
        
        if context.urgency_level <= 0.5:
            return 1.0
            
        # Prefer agents with faster response times for urgent requests
        response_time_score = max(0.1, 1.0 - (capability.avg_response_time / 30.0))
        urgency_adjustment = 1.0 + (context.urgency_level - 0.5) * response_time_score
        
        return min(1.0, urgency_adjustment)
    
    async def _apply_selection_strategy(
        self,
        agent_scores: Dict[str, Dict[str, float]],
        context: SelectionContext,
        participants: List[AssistantAgent]
    ) -> Tuple[AssistantAgent, Dict[str, Any]]:
        """Apply selection strategy based on scores and context"""
        
        if not agent_scores:
            return participants[0], {"primary_reason": "no_scores_available"}
        
        # Sort by composite score
        sorted_agents = sorted(
            agent_scores.items(),
            key=lambda x: x[1]['composite'],
            reverse=True
        )
        
        best_agent_name = sorted_agents[0][0]
        best_scores = sorted_agents[0][1]
        
        # Find the agent object
        selected_agent = next(
            (agent for agent in participants if agent.name == best_agent_name),
            participants[0]
        )
        
        # Build detailed rationale
        rationale = {
            "primary_reason": self._determine_primary_reason(best_scores),
            "confidence_score": best_scores['composite'],
            "expertise_match": best_scores['expertise'],
            "phase_relevance": best_scores['phase_relevance'],
            "all_scores": best_scores,
            "selection_strategy": "multi_factor_composite",
            "alternatives": [
                {"agent": name, "score": scores['composite']} 
                for name, scores in sorted_agents[1:3]
            ]
        }
        
        return selected_agent, rationale
    
    def _determine_primary_reason(self, scores: Dict[str, float]) -> str:
        """Determine the primary reason for selection"""
        
        max_score = max(scores[key] for key in ['expertise', 'phase_relevance', 'performance'])
        
        if scores['expertise'] == max_score:
            return "expertise_match"
        elif scores['phase_relevance'] == max_score:
            return "mission_phase_relevance"
        elif scores['performance'] == max_score:
            return "historical_performance"
        else:
            return "composite_optimization"
    
    async def _analyze_required_expertise(self, message_text: str) -> Set[ExpertiseDomain]:
        """Analyze message to determine required expertise domains"""
        
        text = message_text.lower()
        required = set()
        
        expertise_keywords = {
            ExpertiseDomain.STRATEGY: ["strategy", "vision", "planning", "roadmap", "direction"],
            ExpertiseDomain.FINANCE: ["budget", "cost", "finance", "revenue", "profit", "investment"],
            ExpertiseDomain.OPERATIONS: ["process", "workflow", "efficiency", "operations"],
            ExpertiseDomain.TECHNOLOGY: ["technology", "technical", "system", "architecture"],
            ExpertiseDomain.MARKETING: ["marketing", "branding", "promotion", "campaign"],
            ExpertiseDomain.SALES: ["sales", "revenue", "customers", "deals", "pipeline"],
            ExpertiseDomain.HR: ["hiring", "team", "culture", "talent", "people"],
            ExpertiseDomain.LEGAL: ["legal", "compliance", "contract", "regulation"],
            ExpertiseDomain.SECURITY: ["security", "risk", "threat", "privacy", "protection"],
            ExpertiseDomain.ANALYTICS: ["data", "analytics", "metrics", "insights", "analysis"],
            ExpertiseDomain.PRODUCT: ["product", "feature", "development", "roadmap"],
            ExpertiseDomain.DESIGN: ["design", "user", "interface", "experience", "visual"]
        }
        
        for domain, keywords in expertise_keywords.items():
            if any(keyword in text for keyword in keywords):
                required.add(domain)
        
        return required if required else {ExpertiseDomain.STRATEGY}  # Default
    
    async def _calculate_conversation_complexity(
        self, message_text: str, history: List[Dict[str, Any]]
    ) -> float:
        """Calculate conversation complexity score"""
        
        # Message length factor
        length_factor = min(1.0, len(message_text) / 1000)
        
        # Technical terms factor
        technical_terms = [
            "api", "database", "algorithm", "integration", "architecture",
            "framework", "methodology", "analysis", "optimization"
        ]
        tech_count = sum(1 for term in technical_terms if term in message_text.lower())
        tech_factor = min(1.0, tech_count / 5)
        
        # Conversation depth factor
        depth_factor = min(1.0, len(history) / 10)
        
        # Question complexity factor
        question_markers = ["how", "why", "what", "when", "where", "which"]
        question_count = sum(1 for marker in question_markers if marker in message_text.lower())
        question_factor = min(1.0, question_count / 3)
        
        complexity = (length_factor + tech_factor + depth_factor + question_factor) / 4
        return max(0.1, complexity)
    
    async def _assess_collaboration_needs(
        self, message_text: str, required_expertise: Set[ExpertiseDomain]
    ) -> bool:
        """Assess if collaboration between agents is needed"""
        
        # Multiple expertise domains suggest collaboration
        if len(required_expertise) > 2:
            return True
        
        # Collaboration keywords
        collaboration_keywords = [
            "collaborate", "together", "coordination", "alignment", "cross-functional",
            "integrate", "combine", "multiple perspectives", "team effort"
        ]
        
        return any(keyword in message_text.lower() for keyword in collaboration_keywords)
    
    async def _record_selection_decision(
        self, agent: AssistantAgent, rationale: Dict[str, Any], context: SelectionContext
    ):
        """Record selection decision for learning and metrics"""
        
        selection_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "selected_agent": agent.name,
            "message_hash": hashlib.md5(context.message_content.encode()).hexdigest()[:8],
            "mission_phase": context.current_mission_phase.value,
            "rationale": rationale,
            "context_summary": {
                "complexity": context.conversation_complexity,
                "urgency": context.urgency_level,
                "expertise_domains": [domain.value for domain in context.required_expertise],
                "collaboration_needed": context.collaboration_needed
            }
        }
        
        # Record for metrics
        record_selection_metrics(selection_record)
        
        # Update internal history
        self.selection_history.append(selection_record)
        
        # Keep only recent history (last 100 selections)
        if len(self.selection_history) > 100:
            self.selection_history = self.selection_history[-100:]
    
    def _fallback_selection(self, participants: List[AssistantAgent], message_text: str) -> AssistantAgent:
        """Simple fallback selection when intelligent selection fails"""
        
        text = message_text.lower()
        by_name = {agent.name: agent for agent in participants}
        
        # Simple keyword matching fallback
        if any(word in text for word in ["budget", "cost", "finance"]):
            return by_name.get("amy_cfo", participants[0])
        elif any(word in text for word in ["security", "risk", "compliance"]):
            return by_name.get("luca_security_expert", participants[0])
        elif any(word in text for word in ["strategy", "planning", "vision"]):
            return by_name.get("ali_chief_of_staff", participants[0])
        else:
            return participants[0]


# Global intelligent selector instance
_intelligent_selector = IntelligentSpeakerSelector()


# Enhanced public API
async def intelligent_speaker_selection(
    message_text: str,
    participants: List[AssistantAgent],
    conversation_history: Optional[List[Dict[str, Any]]] = None,
    mission_phase: str = "analysis",
    urgency_level: float = 0.5,
    user_preferences: Optional[Dict[str, Any]] = None
) -> Tuple[AssistantAgent, Dict[str, Any]]:
    """Enhanced speaker selection with intelligent analysis"""
    
    phase_enum = MissionPhase(mission_phase.lower()) if mission_phase else MissionPhase.ANALYSIS
    
    return await _intelligent_selector.select_next_speaker(
        message_text=message_text,
        participants=participants,
        conversation_history=conversation_history,
        mission_phase=phase_enum,
        urgency_level=urgency_level,
        user_preferences=user_preferences
    )


# Legacy compatibility functions
def select_key_agents(all_agents: List[AssistantAgent]) -> List[AssistantAgent]:
    """Select key agents with priority scoring"""
    
    priority_scores = {
        "ali_chief_of_staff": 10,
        "domik_mckinsey_strategic_decision_maker": 9,
        "amy_cfo": 8,
        "luca_security_expert": 8,
        "socrates_first_principles_reasoning": 7,
        "diana_performance_dashboard": 7,
        "wanda_workflow_orchestrator": 6,
        "xavier_coordination_patterns": 6,
    }
    
    # Sort agents by priority score
    sorted_agents = sorted(
        all_agents,
        key=lambda agent: priority_scores.get(agent.name, 0),
        reverse=True
    )
    
    # Return top agents (up to 8)
    return sorted_agents[:8]


def pick_next_speaker(message_text: str, participants: List[AssistantAgent]) -> AssistantAgent:
    """Legacy simple speaker selection"""
    
    try:
        # Try intelligent selection first
        import asyncio
        loop = asyncio.get_event_loop()
        selected_agent, rationale = loop.run_until_complete(
            intelligent_speaker_selection(message_text, participants)
        )
        
        # Map to legacy keyword reasons for backward compatibility in metrics
        text_l = message_text.lower()
        if any(word in text_l for word in ["budget", "cost", "finance"]):
            reason = "finance_keywords"
        elif any(word in text_l for word in ["risk", "security", "compliance"]):
            reason = "security_keywords"
        elif any(word in text_l for word in ["strategy", "decision", "plan", "vision", "planning"]):
            reason = "strategy_keywords"
        else:
            reason = rationale.get("primary_reason", "intelligent_selection")

        # Record legacy-compatible metrics with mapped reason
        record_selection_metrics({
            "reason": reason,
            "picked": selected_agent.name,
            "confidence": rationale.get("confidence_score", 0.0)
        })
        
        return selected_agent
        
    except Exception as e:
        logger.warning("Intelligent selection failed, using fallback", error=str(e))
        
        # Fallback to simple keyword matching
        text = message_text.lower()
        by_name = {agent.name: agent for agent in participants}
        
        if any(word in text for word in ["budget", "cost", "finance"]):
            choice = by_name.get("amy_cfo", participants[0])
            record_selection_metrics({"reason": "finance_keywords", "picked": choice.name})
            return choice
        elif any(word in text for word in ["risk", "security", "compliance"]):
            choice = by_name.get("luca_security_expert", participants[0])
            record_selection_metrics({"reason": "security_keywords", "picked": choice.name})
            return choice
        elif any(word in text for word in ["strategy", "decision", "plan"]):
            choice = by_name.get("ali_chief_of_staff", participants[0])
            record_selection_metrics({"reason": "strategy_keywords", "picked": choice.name})
            return choice
        else:
            record_selection_metrics({"reason": "default_first", "picked": participants[0].name})
            return participants[0]


def selection_rationale(message_text: str, participants: List[AssistantAgent]) -> Dict[str, str]:
    """Legacy rationale function with enhanced analysis"""
    
    try:
        import asyncio
        loop = asyncio.get_event_loop()
        _, rationale = loop.run_until_complete(
            intelligent_speaker_selection(message_text, participants)
        )
        
        return {
            "reason": rationale.get("primary_reason", "intelligent_analysis"),
            "picked": rationale.get("selected_agent", "unknown"),
            "confidence": str(rationale.get("confidence_score", 0.0)),
            "method": "intelligent_selection"
        }
        
    except Exception:
        # Fallback to simple analysis
        text = message_text.lower()
        if any(k in text for k in ["budget", "cost", "finance"]):
            return {"reason": "finance_keywords", "picked": "amy_cfo"}
        elif any(k in text for k in ["risk", "security", "compliance"]):
            return {"reason": "security_keywords", "picked": "luca_security_expert"}
        elif any(k in text for k in ["strategy", "decision", "plan"]):
            return {"reason": "strategy_keywords", "picked": "ali_chief_of_staff"}
        else:
            return {"reason": "default_first", "picked": participants[0].name if participants else "unknown"}

