"""
Agent Framework Streaming Runner
Unified streaming implementation supporting both Agent Framework and AutoGen.
"""

import asyncio
import json
from typing import AsyncGenerator, Dict, Any, Optional, Set, Union
from datetime import datetime
from uuid import uuid4
from dataclasses import dataclass
from enum import Enum

import structlog

# Agent Framework imports with fallback
try:
    from agent_framework import Agent
    from agent_framework.messages import TextMessage as AFTextMessage
    AGENT_FRAMEWORK_AVAILABLE = True
except ImportError:
    AGENT_FRAMEWORK_AVAILABLE = False
    Agent = None
    AFTextMessage = None

# AutoGen imports with fallback
try:
    from autogen_agentchat.agents import AssistantAgent
    from autogen_agentchat.messages import TextMessage as AutoGenTextMessage
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False
    AssistantAgent = None
    AutoGenTextMessage = None

from .response_types import StreamingResponse

logger = structlog.get_logger()


class StreamingEventType(Enum):
    """Streaming event types."""
    DELTA = "delta"
    MESSAGE = "message"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    HANDOFF = "handoff"
    FINAL = "final"
    ERROR = "error"
    HEARTBEAT = "heartbeat"
    STATUS = "status"


@dataclass
class StreamingConfig:
    """Configuration for streaming."""
    window_size: int = 10
    max_buffer_size: int = 50
    heartbeat_interval: float = 30.0
    chunk_delay: float = 0.0
    adaptive_delay: bool = True
    framework: str = "auto"  # 'auto', 'agent_framework', 'autogen', 'mock'


@dataclass
class StreamEvent:
    """A single streaming event."""
    event_type: StreamingEventType
    content: str
    metadata: Dict[str, Any] = None
    timestamp: datetime = None
    stream_id: str = ""

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "event_type": self.event_type.value,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "stream_id": self.stream_id
        }


class AgentFrameworkStreamer:
    """
    Unified streaming implementation.

    Supports:
    - Agent Framework streaming
    - AutoGen streaming (fallback)
    - Mock streaming (when no framework available)
    """

    def __init__(self, config: Optional[StreamingConfig] = None):
        """Initialize streamer.

        Args:
            config: Streaming configuration
        """
        self.config = config or StreamingConfig()
        self.active_streams: Set[str] = set()
        self.stream_buffers: Dict[str, list] = {}

        # Determine framework
        self.framework = self._determine_framework()

        logger.info(
            "AgentFrameworkStreamer initialized",
            framework=self.framework,
            agent_framework_available=AGENT_FRAMEWORK_AVAILABLE,
            autogen_available=AUTOGEN_AVAILABLE
        )

    def _determine_framework(self) -> str:
        """Determine which framework to use."""
        if self.config.framework != "auto":
            return self.config.framework

        if AGENT_FRAMEWORK_AVAILABLE:
            return "agent_framework"
        elif AUTOGEN_AVAILABLE:
            return "autogen"
        else:
            return "mock"

    async def stream_response(
        self,
        agent: Any,
        message: str,
        session: Optional[Any] = None,
        enable_tools: bool = True
    ) -> AsyncGenerator[StreamEvent, None]:
        """
        Stream agent response.

        Args:
            agent: Agent instance (AF Agent or AutoGen AssistantAgent)
            message: User message
            session: Optional session context
            enable_tools: Whether to enable tool execution

        Yields:
            StreamEvent objects
        """
        stream_id = str(uuid4())
        self.active_streams.add(stream_id)
        self.stream_buffers[stream_id] = []

        try:
            logger.info(
                "Starting streaming",
                stream_id=stream_id,
                framework=self.framework
            )

            # Yield status event
            yield StreamEvent(
                event_type=StreamingEventType.STATUS,
                content="Streaming started",
                stream_id=stream_id,
                metadata={"framework": self.framework}
            )

            if self.framework == "agent_framework":
                async for event in self._stream_with_agent_framework(
                    agent, message, stream_id
                ):
                    yield event
            elif self.framework == "autogen":
                async for event in self._stream_with_autogen(
                    agent, message, stream_id
                ):
                    yield event
            else:
                async for event in self._stream_mock(message, stream_id):
                    yield event

            # Yield final event
            yield StreamEvent(
                event_type=StreamingEventType.FINAL,
                content="Streaming complete",
                stream_id=stream_id
            )

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield StreamEvent(
                event_type=StreamingEventType.ERROR,
                content=str(e),
                stream_id=stream_id
            )
        finally:
            self.active_streams.discard(stream_id)
            if stream_id in self.stream_buffers:
                del self.stream_buffers[stream_id]

    async def _stream_with_agent_framework(
        self,
        agent: Any,
        message: str,
        stream_id: str
    ) -> AsyncGenerator[StreamEvent, None]:
        """Stream using Agent Framework."""
        if not AGENT_FRAMEWORK_AVAILABLE or Agent is None:
            yield StreamEvent(
                event_type=StreamingEventType.ERROR,
                content="Agent Framework not available",
                stream_id=stream_id
            )
            return

        try:
            # Create user message
            task = AFTextMessage(content=message, source="user") if AFTextMessage else message

            # Stream from agent
            async for chunk in agent.run_stream(task=task):
                content = getattr(chunk, 'content', str(chunk))

                yield StreamEvent(
                    event_type=StreamingEventType.DELTA,
                    content=content,
                    stream_id=stream_id,
                    metadata={
                        "source": getattr(chunk, 'source', 'agent'),
                        "framework": "agent_framework"
                    }
                )

                # Apply backpressure if needed
                if self.config.chunk_delay > 0:
                    await asyncio.sleep(self.config.chunk_delay)

        except Exception as e:
            logger.error(f"Agent Framework streaming error: {e}")
            yield StreamEvent(
                event_type=StreamingEventType.ERROR,
                content=str(e),
                stream_id=stream_id
            )

    async def _stream_with_autogen(
        self,
        agent: Any,
        message: str,
        stream_id: str
    ) -> AsyncGenerator[StreamEvent, None]:
        """Stream using AutoGen."""
        if not AUTOGEN_AVAILABLE or AssistantAgent is None:
            yield StreamEvent(
                event_type=StreamingEventType.ERROR,
                content="AutoGen not available",
                stream_id=stream_id
            )
            return

        try:
            # AutoGen run_stream expects task string
            async for chunk in agent.run_stream(task=message):
                content = getattr(chunk, 'content', str(chunk))

                # Determine event type
                event_type = StreamingEventType.DELTA
                if hasattr(chunk, '__class__'):
                    chunk_type = chunk.__class__.__name__
                    if 'ToolCall' in chunk_type:
                        event_type = StreamingEventType.TOOL_CALL
                    elif 'Handoff' in chunk_type:
                        event_type = StreamingEventType.HANDOFF

                yield StreamEvent(
                    event_type=event_type,
                    content=content,
                    stream_id=stream_id,
                    metadata={
                        "source": getattr(chunk, 'source', 'agent'),
                        "framework": "autogen"
                    }
                )

                if self.config.chunk_delay > 0:
                    await asyncio.sleep(self.config.chunk_delay)

        except Exception as e:
            logger.error(f"AutoGen streaming error: {e}")
            yield StreamEvent(
                event_type=StreamingEventType.ERROR,
                content=str(e),
                stream_id=stream_id
            )

    async def _stream_mock(
        self,
        message: str,
        stream_id: str
    ) -> AsyncGenerator[StreamEvent, None]:
        """Mock streaming for testing."""
        response = f"[Mock Response] Received: {message[:100]}"
        words = response.split()

        for i, word in enumerate(words):
            yield StreamEvent(
                event_type=StreamingEventType.DELTA,
                content=word + " ",
                stream_id=stream_id,
                metadata={"framework": "mock", "word_index": i}
            )
            await asyncio.sleep(0.05)  # Simulate streaming delay

    async def cancel_stream(self, stream_id: str) -> bool:
        """Cancel an active stream.

        Args:
            stream_id: Stream to cancel

        Returns:
            True if cancelled, False if not found
        """
        if stream_id in self.active_streams:
            self.active_streams.discard(stream_id)
            if stream_id in self.stream_buffers:
                del self.stream_buffers[stream_id]
            logger.info(f"Stream cancelled: {stream_id}")
            return True
        return False

    def get_active_streams(self) -> Set[str]:
        """Get set of active stream IDs."""
        return self.active_streams.copy()

    def get_stats(self) -> Dict[str, Any]:
        """Get streamer statistics."""
        return {
            "framework": self.framework,
            "active_streams": len(self.active_streams),
            "agent_framework_available": AGENT_FRAMEWORK_AVAILABLE,
            "autogen_available": AUTOGEN_AVAILABLE,
            "config": {
                "window_size": self.config.window_size,
                "heartbeat_interval": self.config.heartbeat_interval,
                "chunk_delay": self.config.chunk_delay
            }
        }


# Convenience function
async def stream_agent_response(
    agent: Any,
    message: str,
    config: Optional[StreamingConfig] = None
) -> AsyncGenerator[StreamEvent, None]:
    """Stream response from an agent.

    Args:
        agent: Agent to stream from
        message: User message
        config: Optional streaming configuration

    Yields:
        StreamEvent objects
    """
    streamer = AgentFrameworkStreamer(config=config)
    async for event in streamer.stream_response(agent, message):
        yield event


__all__ = [
    "AgentFrameworkStreamer",
    "StreamingConfig",
    "StreamEvent",
    "StreamingEventType",
    "stream_agent_response",
    "AGENT_FRAMEWORK_AVAILABLE",
    "AUTOGEN_AVAILABLE",
]
