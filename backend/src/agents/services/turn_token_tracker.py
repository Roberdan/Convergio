"""
Per-Turn Token Usage Tracking with Timeline
Tracks token usage and costs for each turn in the conversation with detailed timeline
"""

from datetime import datetime
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field, asdict
import json
import structlog

from autogen_agentchat.messages import AgentMessage, ToolCallMessage, ToolResultMessage
from cost_tracker import CostTracker
from ..utils.tracing import start_span
from ..utils.config import get_settings

logger = structlog.get_logger()


@dataclass
class TurnTokenUsage:
    """Token usage for a single turn"""
    turn_number: int
    agent_name: str
    message_type: str  # text, tool_call, tool_result, handoff
    
    # Token counts
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    
    # Cost breakdown
    prompt_cost_usd: float
    completion_cost_usd: float
    total_cost_usd: float
    
    # Timing
    start_time: datetime
    end_time: datetime
    duration_ms: int
    
    # Content metadata
    message_length: int
    tool_calls: List[str] = field(default_factory=list)
    
    # Performance metrics
    tokens_per_second: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat()
        }


@dataclass
class ConversationTokenTimeline:
    """Complete timeline of token usage in a conversation"""
    conversation_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    
    # Turn-by-turn usage
    turns: List[TurnTokenUsage] = field(default_factory=list)
    
    # Cumulative metrics
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    
    # Agent breakdown
    agent_token_usage: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Budget tracking
    budget_limit_usd: Optional[float] = None
    budget_remaining_usd: Optional[float] = None
    budget_breach_turn: Optional[int] = None
    
    # Performance
    avg_tokens_per_turn: float = 0.0
    avg_cost_per_turn: float = 0.0
    peak_turn_tokens: Optional[int] = None
    peak_turn_number: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "conversation_id": self.conversation_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_turns": len(self.turns),
            "total_tokens": self.total_tokens,
            "total_cost_usd": self.total_cost_usd,
            "agent_breakdown": self.agent_token_usage,
            "budget": {
                "limit_usd": self.budget_limit_usd,
                "remaining_usd": self.budget_remaining_usd,
                "breach_turn": self.budget_breach_turn
            },
            "performance": {
                "avg_tokens_per_turn": self.avg_tokens_per_turn,
                "avg_cost_per_turn": self.avg_cost_per_turn,
                "peak_turn_tokens": self.peak_turn_tokens,
                "peak_turn_number": self.peak_turn_number
            },
            "timeline": [turn.to_dict() for turn in self.turns]
        }


class PerTurnTokenTracker:
    """Tracks token usage per turn with callbacks and timeline"""
    
    def __init__(
        self,
        cost_tracker: Optional[CostTracker] = None,
        budget_limit_usd: Optional[float] = None
    ):
        self.cost_tracker = cost_tracker or CostTracker()
        self.budget_limit_usd = budget_limit_usd
        self.settings = get_settings()
        
        # Active timelines
        self.timelines: Dict[str, ConversationTokenTimeline] = {}
        
        # Token callbacks
        self.token_callbacks: List[Callable] = []
        
        # Model pricing (per 1M tokens)
        self.model_pricing = {
            "gpt-4": {"prompt": 30.0, "completion": 60.0},
            "gpt-4-turbo": {"prompt": 10.0, "completion": 30.0},
            "gpt-3.5-turbo": {"prompt": 0.5, "completion": 1.5},
            "claude-3-opus": {"prompt": 15.0, "completion": 75.0},
            "claude-3-sonnet": {"prompt": 3.0, "completion": 15.0},
            "claude-3-haiku": {"prompt": 0.25, "completion": 1.25}
        }
        
        logger.info("💰 Per-turn token tracker initialized", budget_limit=budget_limit_usd)
    
    def start_conversation(
        self,
        conversation_id: str,
        budget_limit_usd: Optional[float] = None
    ) -> ConversationTokenTimeline:
        """Start tracking a new conversation"""
        
        timeline = ConversationTokenTimeline(
            conversation_id=conversation_id,
            start_time=datetime.utcnow(),
            budget_limit_usd=budget_limit_usd or self.budget_limit_usd,
            budget_remaining_usd=budget_limit_usd or self.budget_limit_usd
        )
        
        self.timelines[conversation_id] = timeline
        
        logger.info(
            "📊 Started token tracking for conversation",
            conversation_id=conversation_id,
            budget_limit=timeline.budget_limit_usd
        )
        
        return timeline
    
    async def track_turn(
        self,
        conversation_id: str,
        turn_number: int,
        agent_name: str,
        message: AgentMessage,
        model: str = "gpt-4",
        prompt_tokens: Optional[int] = None,
        completion_tokens: Optional[int] = None
    ) -> TurnTokenUsage:
        """Track token usage for a single turn"""
        
        with start_span("token_tracking.turn", {
            "conversation_id": conversation_id,
            "turn": turn_number,
            "agent": agent_name
        }):
            start_time = datetime.utcnow()
            
            # Get or create timeline
            if conversation_id not in self.timelines:
                timeline = self.start_conversation(conversation_id)
            else:
                timeline = self.timelines[conversation_id]
            
            # Estimate tokens if not provided
            if prompt_tokens is None or completion_tokens is None:
                prompt_tokens, completion_tokens = self._estimate_tokens(message)
            
            total_tokens = prompt_tokens + completion_tokens
            
            # Calculate costs
            prompt_cost, completion_cost = self._calculate_cost(
                prompt_tokens, completion_tokens, model
            )
            total_cost = prompt_cost + completion_cost
            
            # Determine message type
            message_type = self._get_message_type(message)
            
            # Extract tool calls if any
            tool_calls = []
            if isinstance(message, ToolCallMessage):
                tool_calls = [tc.name for tc in message.tool_calls] if hasattr(message, 'tool_calls') else []
            
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Create turn usage record
            turn_usage = TurnTokenUsage(
                turn_number=turn_number,
                agent_name=agent_name,
                message_type=message_type,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                prompt_cost_usd=prompt_cost,
                completion_cost_usd=completion_cost,
                total_cost_usd=total_cost,
                start_time=start_time,
                end_time=end_time,
                duration_ms=duration_ms,
                message_length=len(str(message.content)) if hasattr(message, 'content') else 0,
                tool_calls=tool_calls,
                tokens_per_second=total_tokens / (duration_ms / 1000) if duration_ms > 0 else 0
            )
            
            # Update timeline
            await self._update_timeline(timeline, turn_usage)
            
            # Check budget
            if timeline.budget_limit_usd and timeline.budget_remaining_usd:
                timeline.budget_remaining_usd -= total_cost
                if timeline.budget_remaining_usd < 0 and timeline.budget_breach_turn is None:
                    timeline.budget_breach_turn = turn_number
                    logger.warning(
                        f"⚠️ Budget breach at turn {turn_number}",
                        conversation_id=conversation_id,
                        overage=abs(timeline.budget_remaining_usd)
                    )
                    
                    # Trigger budget breach callback
                    await self._trigger_callbacks("budget_breach", conversation_id, turn_usage, timeline)
            
            # Trigger turn callbacks
            await self._trigger_callbacks("turn_complete", conversation_id, turn_usage, timeline)
            
            # Update cost tracker if available
            if self.cost_tracker and self.settings.cost_safety_enabled:
                await self.cost_tracker.track_turn_cost(
                    conversation_id=conversation_id,
                    turn_id=str(turn_number),
                    agent_name=agent_name,
                    cost_breakdown={
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "total_tokens": total_tokens,
                        "total_cost_usd": total_cost
                    }
                )
            
            logger.debug(
                f"Turn {turn_number} tracked",
                agent=agent_name,
                tokens=total_tokens,
                cost_usd=total_cost,
                duration_ms=duration_ms
            )
            
            return turn_usage
    
    async def _update_timeline(
        self,
        timeline: ConversationTokenTimeline,
        turn_usage: TurnTokenUsage
    ):
        """Update timeline with turn usage"""
        
        # Add turn
        timeline.turns.append(turn_usage)
        
        # Update cumulative metrics
        timeline.total_prompt_tokens += turn_usage.prompt_tokens
        timeline.total_completion_tokens += turn_usage.completion_tokens
        timeline.total_tokens += turn_usage.total_tokens
        timeline.total_cost_usd += turn_usage.total_cost_usd
        
        # Update agent breakdown
        if turn_usage.agent_name not in timeline.agent_token_usage:
            timeline.agent_token_usage[turn_usage.agent_name] = {
                "turns": 0,
                "total_tokens": 0,
                "total_cost_usd": 0.0,
                "avg_tokens_per_turn": 0.0
            }
        
        agent_stats = timeline.agent_token_usage[turn_usage.agent_name]
        agent_stats["turns"] += 1
        agent_stats["total_tokens"] += turn_usage.total_tokens
        agent_stats["total_cost_usd"] += turn_usage.total_cost_usd
        agent_stats["avg_tokens_per_turn"] = agent_stats["total_tokens"] / agent_stats["turns"]
        
        # Update performance metrics
        num_turns = len(timeline.turns)
        timeline.avg_tokens_per_turn = timeline.total_tokens / num_turns
        timeline.avg_cost_per_turn = timeline.total_cost_usd / num_turns
        
        # Track peak usage
        if timeline.peak_turn_tokens is None or turn_usage.total_tokens > timeline.peak_turn_tokens:
            timeline.peak_turn_tokens = turn_usage.total_tokens
            timeline.peak_turn_number = turn_usage.turn_number
    
    def _estimate_tokens(self, message: AgentMessage) -> Tuple[int, int]:
        """Estimate token counts from message"""
        
        # Rough estimation: 1 token ≈ 4 characters
        content = str(message.content) if hasattr(message, 'content') else ""
        content_tokens = len(content) // 4
        
        # Estimate based on message type
        if isinstance(message, ToolCallMessage):
            # Tool calls have overhead
            prompt_tokens = content_tokens + 50  # System prompt overhead
            completion_tokens = content_tokens
        elif isinstance(message, ToolResultMessage):
            # Tool results are typically longer
            prompt_tokens = content_tokens // 2
            completion_tokens = content_tokens
        else:
            # Regular text message
            prompt_tokens = content_tokens // 2
            completion_tokens = content_tokens // 2
        
        return max(1, prompt_tokens), max(1, completion_tokens)
    
    def _calculate_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        model: str
    ) -> Tuple[float, float]:
        """Calculate cost in USD"""
        
        # Get pricing for model
        pricing = self.model_pricing.get(model, self.model_pricing["gpt-4"])
        
        # Calculate costs (pricing is per 1M tokens)
        prompt_cost = (prompt_tokens / 1_000_000) * pricing["prompt"]
        completion_cost = (completion_tokens / 1_000_000) * pricing["completion"]
        
        return prompt_cost, completion_cost
    
    def _get_message_type(self, message: AgentMessage) -> str:
        """Determine message type"""
        
        if isinstance(message, ToolCallMessage):
            return "tool_call"
        elif isinstance(message, ToolResultMessage):
            return "tool_result"
        elif hasattr(message, 'handoff') and message.handoff:
            return "handoff"
        else:
            return "text"
    
    async def _trigger_callbacks(
        self,
        event_type: str,
        conversation_id: str,
        turn_usage: TurnTokenUsage,
        timeline: ConversationTokenTimeline
    ):
        """Trigger registered callbacks"""
        
        for callback in self.token_callbacks:
            try:
                await callback(event_type, conversation_id, turn_usage, timeline)
            except Exception as e:
                logger.error(f"Callback failed for {event_type}", error=str(e))
    
    def register_callback(self, callback: Callable):
        """Register a token usage callback"""
        self.token_callbacks.append(callback)
        logger.info(f"Registered token callback: {callback.__name__}")
    
    def end_conversation(self, conversation_id: str) -> Optional[ConversationTokenTimeline]:
        """End conversation tracking and return final timeline"""
        
        if conversation_id not in self.timelines:
            return None
        
        timeline = self.timelines[conversation_id]
        timeline.end_time = datetime.utcnow()
        
        # Calculate final statistics
        duration_seconds = (timeline.end_time - timeline.start_time).total_seconds()
        
        logger.info(
            "📊 Conversation ended",
            conversation_id=conversation_id,
            total_turns=len(timeline.turns),
            total_tokens=timeline.total_tokens,
            total_cost_usd=timeline.total_cost_usd,
            duration_seconds=duration_seconds
        )
        
        return timeline
    
    def get_timeline(self, conversation_id: str) -> Optional[ConversationTokenTimeline]:
        """Get timeline for a conversation"""
        return self.timelines.get(conversation_id)
    
    def get_turn_summary(self, conversation_id: str) -> Dict[str, Any]:
        """Get summary of token usage by turn"""
        
        timeline = self.timelines.get(conversation_id)
        if not timeline:
            return {}
        
        return {
            "conversation_id": conversation_id,
            "total_turns": len(timeline.turns),
            "total_tokens": timeline.total_tokens,
            "total_cost_usd": timeline.total_cost_usd,
            "avg_tokens_per_turn": timeline.avg_tokens_per_turn,
            "peak_turn": {
                "number": timeline.peak_turn_number,
                "tokens": timeline.peak_turn_tokens
            },
            "budget_status": {
                "limit": timeline.budget_limit_usd,
                "remaining": timeline.budget_remaining_usd,
                "breached": timeline.budget_breach_turn is not None
            },
            "by_agent": timeline.agent_token_usage
        }
    
    def export_timeline(self, conversation_id: str, output_path: Optional[str] = None) -> str:
        """Export timeline to JSON"""
        
        timeline = self.timelines.get(conversation_id)
        if not timeline:
            return "{}"
        
        timeline_json = json.dumps(timeline.to_dict(), indent=2)
        
        if output_path:
            with open(output_path, 'w') as f:
                f.write(timeline_json)
            logger.info(f"Timeline exported to {output_path}")
        
        return timeline_json
    
    async def simulate_budget_breach(
        self,
        conversation_id: str,
        turns_to_simulate: int = 10
    ) -> Dict[str, Any]:
        """Simulate token usage to predict budget breach"""
        
        timeline = self.timelines.get(conversation_id)
        if not timeline or not timeline.turns:
            return {"error": "No timeline or turns available"}
        
        # Calculate average usage from existing turns
        avg_tokens = timeline.avg_tokens_per_turn
        avg_cost = timeline.avg_cost_per_turn
        
        # Simulate future turns
        avg_tokens * turns_to_simulate
        simulated_cost = avg_cost * turns_to_simulate
        
        # Predict breach
        projected_total_cost = timeline.total_cost_usd + simulated_cost
        
        breach_info = {
            "current_cost_usd": timeline.total_cost_usd,
            "projected_cost_usd": projected_total_cost,
            "simulated_turns": turns_to_simulate,
            "will_breach": False,
            "turns_until_breach": None
        }
        
        if timeline.budget_limit_usd:
            remaining = timeline.budget_limit_usd - timeline.total_cost_usd
            if remaining > 0 and avg_cost > 0:
                turns_until_breach = int(remaining / avg_cost)
                breach_info["turns_until_breach"] = turns_until_breach
                breach_info["will_breach"] = turns_until_breach < turns_to_simulate
        
        return breach_info


# Global token tracker instance
_token_tracker: Optional[PerTurnTokenTracker] = None


def initialize_token_tracker(
    cost_tracker: Optional[CostTracker] = None,
    budget_limit_usd: Optional[float] = None
) -> PerTurnTokenTracker:
    """Initialize global token tracker"""
    global _token_tracker
    _token_tracker = PerTurnTokenTracker(cost_tracker, budget_limit_usd)
    return _token_tracker


def get_token_tracker() -> Optional[PerTurnTokenTracker]:
    """Get global token tracker"""
    return _token_tracker


# Example callback for budget monitoring
async def budget_monitor_callback(
    event_type: str,
    conversation_id: str,
    turn_usage: TurnTokenUsage,
    timeline: ConversationTokenTimeline
):
    """Example callback for monitoring budget"""
    
    if event_type == "budget_breach":
        logger.critical(
            "💸 BUDGET BREACHED",
            conversation_id=conversation_id,
            turn=turn_usage.turn_number,
            overage_usd=abs(timeline.budget_remaining_usd)
        )
        # Could trigger circuit breaker here
    
    elif event_type == "turn_complete":
        if timeline.budget_remaining_usd and timeline.budget_limit_usd:
            budget_used_pct = (1 - timeline.budget_remaining_usd / timeline.budget_limit_usd) * 100
            if budget_used_pct > 80:
                logger.warning(
                    f"⚠️ Budget usage high: {budget_used_pct:.1f}%",
                    conversation_id=conversation_id,
                    remaining_usd=timeline.budget_remaining_usd
                )


__all__ = [
    "PerTurnTokenTracker",
    "TurnTokenUsage",
    "ConversationTokenTimeline",
    "initialize_token_tracker",
    "get_token_tracker",
    "budget_monitor_callback"
]