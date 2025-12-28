"""
Enhanced Selection Metrics - Comprehensive tracking and KPI measurement
Tracks detailed selection rationale, turn reduction, and decision quality
"""

import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from collections import defaultdict
import statistics

import structlog

logger = structlog.get_logger()


@dataclass
class SelectionDecision:
    """Detailed record of a single selection decision"""
    timestamp: datetime
    turn_number: int
    conversation_id: str
    selected_agent: str
    selection_rationale: Dict[str, Any]
    scoring_factors: Dict[str, float]
    candidate_scores: Dict[str, float]
    decision_time_ms: float
    mission_phase: str
    message_intent: str
    previous_speakers: List[str]
    rag_hints: List[str]
    success_indicator: Optional[bool] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class ConversationMetrics:
    """Metrics for a complete conversation"""
    conversation_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_turns: int = 0
    unique_speakers: int = 0
    speaker_distribution: Dict[str, int] = field(default_factory=dict)
    avg_selection_time_ms: float = 0.0
    turn_reduction_percentage: float = 0.0
    baseline_turns: Optional[int] = None
    quality_score: float = 0.0
    cost_reduction: float = 0.0
    decisions: List[SelectionDecision] = field(default_factory=list)


class EnhancedSelectionMetrics:
    """Advanced metrics tracking for speaker selection with KPI measurement"""
    
    def __init__(self):
        self.conversations: Dict[str, ConversationMetrics] = {}
        self.global_metrics = {
            "total_selections": 0,
            "avg_selection_time_ms": 0.0,
            "turn_reduction_rate": 0.0,
            "quality_scores": [],
            "agent_effectiveness": defaultdict(lambda: {"selections": 0, "quality": []})
        }
        self.baseline_turns_by_type = {
            "simple_query": 3,
            "analysis": 8,
            "strategy": 12,
            "complex_workflow": 20
        }
        
    async def record_selection(
        self,
        conversation_id: str,
        turn_number: int,
        selected_agent: str,
        selection_rationale: Dict[str, Any],
        scoring_factors: Dict[str, float],
        candidate_scores: Dict[str, float],
        decision_time_ms: float,
        mission_phase: str,
        message_intent: str,
        previous_speakers: List[str],
        rag_hints: Optional[List[str]] = None
    ) -> None:
        """Record a detailed selection decision"""
        
        # Create conversation metrics if not exists
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = ConversationMetrics(
                conversation_id=conversation_id,
                start_time=datetime.utcnow()
            )
        
        conv_metrics = self.conversations[conversation_id]
        
        # Create decision record
        decision = SelectionDecision(
            timestamp=datetime.utcnow(),
            turn_number=turn_number,
            conversation_id=conversation_id,
            selected_agent=selected_agent,
            selection_rationale=selection_rationale,
            scoring_factors=scoring_factors,
            candidate_scores=candidate_scores,
            decision_time_ms=decision_time_ms,
            mission_phase=mission_phase,
            message_intent=message_intent,
            previous_speakers=previous_speakers,
            rag_hints=rag_hints or []
        )
        
        # Update conversation metrics
        conv_metrics.decisions.append(decision)
        conv_metrics.total_turns = turn_number
        conv_metrics.speaker_distribution[selected_agent] = \
            conv_metrics.speaker_distribution.get(selected_agent, 0) + 1
        conv_metrics.unique_speakers = len(conv_metrics.speaker_distribution)
        
        # Calculate average selection time
        selection_times = [d.decision_time_ms for d in conv_metrics.decisions]
        conv_metrics.avg_selection_time_ms = statistics.mean(selection_times)
        
        # Update global metrics
        self.global_metrics["total_selections"] += 1
        self.global_metrics["agent_effectiveness"][selected_agent]["selections"] += 1
        
        # Log detailed decision
        logger.info(
            "📊 Selection decision recorded",
            conversation_id=conversation_id,
            turn=turn_number,
            selected=selected_agent,
            time_ms=decision_time_ms,
            phase=mission_phase,
            top_score=max(candidate_scores.values()) if candidate_scores else 0
        )
    
    async def evaluate_conversation_quality(
        self,
        conversation_id: str,
        resolution_achieved: bool,
        user_satisfaction: Optional[float] = None,
        conversation_type: str = "analysis"
    ) -> Dict[str, Any]:
        """Evaluate conversation quality and calculate KPIs"""
        
        if conversation_id not in self.conversations:
            return {"error": "Conversation not found"}
        
        conv_metrics = self.conversations[conversation_id]
        conv_metrics.end_time = datetime.utcnow()
        
        # Calculate turn reduction
        baseline = self.baseline_turns_by_type.get(conversation_type, 10)
        conv_metrics.baseline_turns = baseline
        conv_metrics.turn_reduction_percentage = \
            ((baseline - conv_metrics.total_turns) / baseline * 100) if baseline > 0 else 0
        
        # Calculate quality score
        quality_factors = {
            "resolution": 0.4 if resolution_achieved else 0.0,
            "efficiency": min(0.3 * (baseline / max(conv_metrics.total_turns, 1)), 0.3),
            "diversity": min(0.2 * (conv_metrics.unique_speakers / 5), 0.2),  # Max 5 agents
            "satisfaction": (user_satisfaction * 0.1) if user_satisfaction else 0.0
        }
        
        conv_metrics.quality_score = sum(quality_factors.values())
        
        # Calculate cost reduction (assuming cost per turn)
        cost_per_turn = 0.10  # $0.10 per turn estimate
        expected_cost = baseline * cost_per_turn
        actual_cost = conv_metrics.total_turns * cost_per_turn
        conv_metrics.cost_reduction = expected_cost - actual_cost
        
        # Update global metrics
        self.global_metrics["quality_scores"].append(conv_metrics.quality_score)
        self.global_metrics["turn_reduction_rate"] = \
            statistics.mean([c.turn_reduction_percentage for c in self.conversations.values()])
        
        return {
            "conversation_id": conversation_id,
            "total_turns": conv_metrics.total_turns,
            "baseline_turns": baseline,
            "turn_reduction": f"{conv_metrics.turn_reduction_percentage:.1f}%",
            "quality_score": f"{conv_metrics.quality_score:.2f}",
            "cost_saved": f"${conv_metrics.cost_reduction:.2f}",
            "unique_speakers": conv_metrics.unique_speakers,
            "avg_selection_time": f"{conv_metrics.avg_selection_time_ms:.1f}ms"
        }
    
    def get_kpi_dashboard(self) -> Dict[str, Any]:
        """Generate KPI dashboard data"""
        
        total_conversations = len(self.conversations)
        if total_conversations == 0:
            return {"status": "no_data"}
        
        # Calculate aggregate KPIs
        avg_turn_reduction = statistics.mean([
            c.turn_reduction_percentage for c in self.conversations.values()
            if c.turn_reduction_percentage > 0
        ]) if self.conversations else 0
        
        avg_quality = statistics.mean(self.global_metrics["quality_scores"]) \
            if self.global_metrics["quality_scores"] else 0
        
        total_cost_saved = sum(c.cost_reduction for c in self.conversations.values())
        
        # Agent performance analysis
        agent_performance = {}
        for agent, data in self.global_metrics["agent_effectiveness"].items():
            agent_performance[agent] = {
                "selections": data["selections"],
                "selection_rate": data["selections"] / self.global_metrics["total_selections"] \
                    if self.global_metrics["total_selections"] > 0 else 0,
                "avg_quality": statistics.mean(data["quality"]) if data["quality"] else 0
            }
        
        # Time-based trends
        recent_conversations = sorted(
            self.conversations.values(),
            key=lambda c: c.start_time,
            reverse=True
        )[:10]
        
        recent_trend = {
            "turn_reduction": [c.turn_reduction_percentage for c in recent_conversations],
            "quality": [c.quality_score for c in recent_conversations],
            "timestamps": [c.start_time.isoformat() for c in recent_conversations]
        }
        
        return {
            "summary": {
                "total_conversations": total_conversations,
                "total_selections": self.global_metrics["total_selections"],
                "avg_turn_reduction": f"{avg_turn_reduction:.1f}%",
                "avg_quality_score": f"{avg_quality:.2f}",
                "total_cost_saved": f"${total_cost_saved:.2f}",
                "target_achievement": "✅" if avg_turn_reduction >= 10 else "❌"
            },
            "agent_performance": agent_performance,
            "recent_trend": recent_trend,
            "selection_time_distribution": {
                "p50": self._calculate_percentile([d.decision_time_ms 
                    for c in self.conversations.values() 
                    for d in c.decisions], 50),
                "p95": self._calculate_percentile([d.decision_time_ms 
                    for c in self.conversations.values() 
                    for d in c.decisions], 95),
                "p99": self._calculate_percentile([d.decision_time_ms 
                    for c in self.conversations.values() 
                    for d in c.decisions], 99)
            }
        }
    
    def _calculate_percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile value"""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    async def export_metrics(self, output_path: str) -> None:
        """Export metrics to JSON file"""
        
        export_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "dashboard": self.get_kpi_dashboard(),
            "conversations": [
                {
                    "id": conv.conversation_id,
                    "metrics": {
                        "turns": conv.total_turns,
                        "reduction": conv.turn_reduction_percentage,
                        "quality": conv.quality_score,
                        "cost_saved": conv.cost_reduction
                    },
                    "decisions": [d.to_dict() for d in conv.decisions[:5]]  # First 5 decisions
                }
                for conv in list(self.conversations.values())[:20]  # Last 20 conversations
            ]
        }
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"📊 Metrics exported to {output_path}")


# Global metrics instance
_metrics_instance: Optional[EnhancedSelectionMetrics] = None


def get_enhanced_metrics() -> EnhancedSelectionMetrics:
    """Get or create global metrics instance"""
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = EnhancedSelectionMetrics()
    return _metrics_instance


__all__ = [
    "SelectionDecision",
    "ConversationMetrics",
    "EnhancedSelectionMetrics",
    "get_enhanced_metrics"
]