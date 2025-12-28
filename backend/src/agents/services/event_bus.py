"""
Event Bus System for Ali Proactive & Insight Engine
Real-time event processing and pattern detection
"""

import asyncio
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
import uuid
from asyncio import Queue

import structlog

logger = structlog.get_logger()


class EventType(str, Enum):
    # User events
    USER_LOGIN = "user.login"
    USER_ACTION = "user.action"
    USER_ERROR = "user.error"
    
    # Agent events
    AGENT_STARTED = "agent.started"
    AGENT_COMPLETED = "agent.completed"
    AGENT_FAILED = "agent.failed"
    AGENT_DECISION = "agent.decision"
    
    # Task events
    TASK_CREATED = "task.created"
    TASK_UPDATED = "task.updated"
    TASK_COMPLETED = "task.completed"
    TASK_BLOCKED = "task.blocked"
    
    # Workflow events
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_STEP = "workflow.step"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"
    
    # System events
    SYSTEM_PERFORMANCE = "system.performance"
    SYSTEM_ERROR = "system.error"
    SYSTEM_ALERT = "system.alert"
    
    # Insight events
    INSIGHT_GENERATED = "insight.generated"
    PATTERN_DETECTED = "pattern.detected"
    RECOMMENDATION_MADE = "recommendation.made"


class EventPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Event:
    """System event with metadata"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: EventType = EventType.USER_ACTION
    priority: EventPriority = EventPriority.MEDIUM
    timestamp: datetime = field(default_factory=datetime.utcnow)
    source: str = ""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "priority": self.priority,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "data": self.data,
            "metadata": self.metadata
        }


@dataclass
class EventPattern:
    """Pattern definition for event detection"""
    id: str
    name: str
    description: str
    event_types: List[EventType]
    time_window: timedelta
    min_occurrences: int = 1
    max_occurrences: Optional[int] = None
    conditions: Dict[str, Any] = field(default_factory=dict)
    
    def matches(self, events: List[Event]) -> bool:
        """Check if events match this pattern"""
        if len(events) < self.min_occurrences:
            return False
        
        if self.max_occurrences and len(events) > self.max_occurrences:
            return False
        
        # Check time window
        if events:
            time_span = events[-1].timestamp - events[0].timestamp
            if time_span > self.time_window:
                return False
        
        # Check event types
        event_types = {e.type for e in events}
        required_types = set(self.event_types)
        if not required_types.issubset(event_types):
            return False
        
        # Additional condition checks
        for condition_key, condition_value in self.conditions.items():
            if not self._check_condition(events, condition_key, condition_value):
                return False
        
        return True
    
    def _check_condition(self, events: List[Event], key: str, value: Any) -> bool:
        """Check specific condition against events"""
        # Implement custom condition logic
        if key == "min_priority":
            priorities = [e.priority for e in events]
            return any(p == value for p in priorities)
        
        if key == "same_user":
            user_ids = {e.user_id for e in events if e.user_id}
            return len(user_ids) == 1
        
        return True


class EventBus:
    """Central event bus for system-wide event processing"""
    
    def __init__(self):
        self.subscribers: Dict[EventType, List[Callable]] = defaultdict(list)
        self.event_queue: Queue = Queue()
        self.event_history: deque = deque(maxlen=10000)
        self.patterns: Dict[str, EventPattern] = {}
        self.pattern_subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self.running = False
        self._processor_task = None
        
        # Event buffers for pattern detection
        self.event_buffers: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
        # Metrics
        self.metrics = {
            "events_processed": 0,
            "patterns_detected": 0,
            "insights_generated": 0,
            "errors": 0
        }
    
    async def start(self):
        """Start the event bus processor"""
        if not self.running:
            self.running = True
            self._processor_task = asyncio.create_task(self._process_events())
            logger.info("🚌 Event bus started")
    
    async def stop(self):
        """Stop the event bus processor"""
        self.running = False
        if self._processor_task:
            await self._processor_task
            logger.info("🛑 Event bus stopped")
    
    async def publish(self, event: Event):
        """Publish an event to the bus"""
        await self.event_queue.put(event)
        logger.debug(f"📢 Event published: {event.type}", event_id=event.id)
    
    def subscribe(self, event_type: EventType, handler: Callable):
        """Subscribe to specific event type"""
        self.subscribers[event_type].append(handler)
        logger.debug(f"📡 Subscribed to {event_type}")
    
    def unsubscribe(self, event_type: EventType, handler: Callable):
        """Unsubscribe from event type"""
        if handler in self.subscribers[event_type]:
            self.subscribers[event_type].remove(handler)
    
    def register_pattern(self, pattern: EventPattern):
        """Register a new event pattern for detection"""
        self.patterns[pattern.id] = pattern
        logger.info(f"🎯 Pattern registered: {pattern.name}")
    
    def subscribe_to_pattern(self, pattern_id: str, handler: Callable):
        """Subscribe to pattern detection events"""
        self.pattern_subscribers[pattern_id].append(handler)
    
    async def _process_events(self):
        """Main event processing loop"""
        while self.running:
            try:
                # Get next event with timeout
                event = await asyncio.wait_for(
                    self.event_queue.get(),
                    timeout=1.0
                )
                
                # Add to history
                self.event_history.append(event)
                self.metrics["events_processed"] += 1
                
                # Process subscribers
                await self._notify_subscribers(event)
                
                # Check patterns
                await self._check_patterns(event)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"❌ Error processing event: {e}")
                self.metrics["errors"] += 1
    
    async def _notify_subscribers(self, event: Event):
        """Notify all subscribers of an event"""
        handlers = self.subscribers.get(event.type, [])
        
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"❌ Error in event handler: {e}")
    
    async def _check_patterns(self, event: Event):
        """Check if event triggers any patterns"""
        # Add event to relevant buffers
        for pattern_id, pattern in self.patterns.items():
            if event.type in pattern.event_types:
                self.event_buffers[pattern_id].append(event)
                
                # Get recent events within time window
                recent_events = self._get_recent_events(
                    self.event_buffers[pattern_id],
                    pattern.time_window
                )
                
                # Check if pattern matches
                if pattern.matches(recent_events):
                    await self._handle_pattern_match(pattern, recent_events)
    
    def _get_recent_events(self, buffer: deque, time_window: timedelta) -> List[Event]:
        """Get events within time window from buffer"""
        cutoff_time = datetime.utcnow() - time_window
        return [e for e in buffer if e.timestamp >= cutoff_time]
    
    async def _handle_pattern_match(self, pattern: EventPattern, events: List[Event]):
        """Handle when a pattern is detected"""
        self.metrics["patterns_detected"] += 1
        
        # Create pattern detection event
        pattern_event = Event(
            type=EventType.PATTERN_DETECTED,
            priority=EventPriority.HIGH,
            source="event_bus",
            data={
                "pattern_id": pattern.id,
                "pattern_name": pattern.name,
                "matched_events": [e.id for e in events],
                "event_count": len(events)
            }
        )
        
        # Notify pattern subscribers
        handlers = self.pattern_subscribers.get(pattern.id, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(pattern_event, events)
                else:
                    handler(pattern_event, events)
            except Exception as e:
                logger.error(f"❌ Error in pattern handler: {e}")
        
        logger.info(f"🎯 Pattern detected: {pattern.name}", 
                   pattern_id=pattern.id,
                   event_count=len(events))
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get event bus metrics"""
        return {
            **self.metrics,
            "queue_size": self.event_queue.qsize(),
            "history_size": len(self.event_history),
            "active_patterns": len(self.patterns),
            "subscribers": sum(len(handlers) for handlers in self.subscribers.values())
        }
    
    def get_event_history(self, 
                         event_type: Optional[EventType] = None,
                         user_id: Optional[str] = None,
                         since: Optional[datetime] = None,
                         limit: int = 100) -> List[Event]:
        """Get filtered event history"""
        events = list(self.event_history)
        
        if event_type:
            events = [e for e in events if e.type == event_type]
        
        if user_id:
            events = [e for e in events if e.user_id == user_id]
        
        if since:
            events = [e for e in events if e.timestamp >= since]
        
        return events[-limit:]


# Global event bus instance
event_bus = EventBus()


# Pre-defined patterns
def register_default_patterns():
    """Register default event patterns"""
    
    # High error rate pattern
    event_bus.register_pattern(EventPattern(
        id="high_error_rate",
        name="High Error Rate",
        description="Multiple errors in short time",
        event_types=[EventType.USER_ERROR, EventType.SYSTEM_ERROR],
        time_window=timedelta(minutes=5),
        min_occurrences=5,
        conditions={"min_priority": EventPriority.HIGH}
    ))
    
    # Workflow failure pattern
    event_bus.register_pattern(EventPattern(
        id="workflow_failures",
        name="Repeated Workflow Failures",
        description="Multiple workflow failures for same user",
        event_types=[EventType.WORKFLOW_FAILED],
        time_window=timedelta(minutes=30),
        min_occurrences=3,
        conditions={"same_user": True}
    ))
    
    # Task blockage pattern
    event_bus.register_pattern(EventPattern(
        id="task_blockage",
        name="Task Blockage Pattern",
        description="Multiple tasks getting blocked",
        event_types=[EventType.TASK_BLOCKED],
        time_window=timedelta(hours=1),
        min_occurrences=5
    ))
    
    # Agent failure cascade
    event_bus.register_pattern(EventPattern(
        id="agent_cascade_failure",
        name="Agent Cascade Failure",
        description="Multiple agent failures in succession",
        event_types=[EventType.AGENT_FAILED],
        time_window=timedelta(minutes=10),
        min_occurrences=3
    ))
    
    logger.info("📊 Default patterns registered")


# Initialize on import
async def initialize_event_bus():
    """Initialize and start the event bus"""
    await event_bus.start()
    register_default_patterns()
    return event_bus