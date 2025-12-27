"""
Unit tests for AgentFrameworkStreamer (H4).
Tests streaming functionality with mock, AF, and AutoGen backends.
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock, patch


class TestStreamingImports:
    """Tests for module imports."""

    def test_module_imports_successfully(self):
        """Test that streaming module imports without error."""
        from src.agents.services.streaming import agent_framework_runner
        assert agent_framework_runner is not None

    def test_framework_flags_exist(self):
        """Test that framework availability flags exist."""
        from src.agents.services.streaming.agent_framework_runner import (
            AGENT_FRAMEWORK_AVAILABLE,
            AUTOGEN_AVAILABLE
        )
        assert isinstance(AGENT_FRAMEWORK_AVAILABLE, bool)
        assert isinstance(AUTOGEN_AVAILABLE, bool)

    def test_streamer_class_exists(self):
        """Test that AgentFrameworkStreamer class exists."""
        from src.agents.services.streaming.agent_framework_runner import AgentFrameworkStreamer
        assert AgentFrameworkStreamer is not None


class TestStreamingEventType:
    """Tests for StreamingEventType enum."""

    def test_event_types_exist(self):
        """Test that all event types are defined."""
        from src.agents.services.streaming.agent_framework_runner import StreamingEventType

        assert StreamingEventType.DELTA is not None
        assert StreamingEventType.MESSAGE is not None
        assert StreamingEventType.TOOL_CALL is not None
        assert StreamingEventType.TOOL_RESULT is not None
        assert StreamingEventType.HANDOFF is not None
        assert StreamingEventType.FINAL is not None
        assert StreamingEventType.ERROR is not None
        assert StreamingEventType.HEARTBEAT is not None
        assert StreamingEventType.STATUS is not None

    def test_event_type_values(self):
        """Test event type string values."""
        from src.agents.services.streaming.agent_framework_runner import StreamingEventType

        assert StreamingEventType.DELTA.value == "delta"
        assert StreamingEventType.FINAL.value == "final"
        assert StreamingEventType.ERROR.value == "error"


class TestStreamingConfig:
    """Tests for StreamingConfig dataclass."""

    def test_config_default_values(self):
        """Test default configuration values."""
        from src.agents.services.streaming.agent_framework_runner import StreamingConfig

        config = StreamingConfig()

        assert config.window_size == 10
        assert config.max_buffer_size == 50
        assert config.heartbeat_interval == 30.0
        assert config.chunk_delay == 0.0
        assert config.adaptive_delay is True
        assert config.framework == "auto"

    def test_config_custom_values(self):
        """Test custom configuration values."""
        from src.agents.services.streaming.agent_framework_runner import StreamingConfig

        config = StreamingConfig(
            window_size=20,
            max_buffer_size=100,
            heartbeat_interval=60.0,
            chunk_delay=0.1,
            adaptive_delay=False,
            framework="mock"
        )

        assert config.window_size == 20
        assert config.max_buffer_size == 100
        assert config.heartbeat_interval == 60.0
        assert config.chunk_delay == 0.1
        assert config.adaptive_delay is False
        assert config.framework == "mock"


class TestStreamEvent:
    """Tests for StreamEvent dataclass."""

    def test_event_creation(self):
        """Test basic event creation."""
        from src.agents.services.streaming.agent_framework_runner import (
            StreamEvent,
            StreamingEventType
        )

        event = StreamEvent(
            event_type=StreamingEventType.DELTA,
            content="Hello",
            stream_id="test123"
        )

        assert event.event_type == StreamingEventType.DELTA
        assert event.content == "Hello"
        assert event.stream_id == "test123"

    def test_event_default_timestamp(self):
        """Test that timestamp is set by default."""
        from src.agents.services.streaming.agent_framework_runner import (
            StreamEvent,
            StreamingEventType
        )

        event = StreamEvent(
            event_type=StreamingEventType.MESSAGE,
            content="Test"
        )

        assert event.timestamp is not None
        assert isinstance(event.timestamp, datetime)

    def test_event_default_metadata(self):
        """Test that metadata defaults to empty dict."""
        from src.agents.services.streaming.agent_framework_runner import (
            StreamEvent,
            StreamingEventType
        )

        event = StreamEvent(
            event_type=StreamingEventType.DELTA,
            content="Test"
        )

        assert event.metadata == {}

    def test_event_to_dict(self):
        """Test event serialization."""
        from src.agents.services.streaming.agent_framework_runner import (
            StreamEvent,
            StreamingEventType
        )

        event = StreamEvent(
            event_type=StreamingEventType.DELTA,
            content="Hello World",
            stream_id="stream123",
            metadata={"key": "value"}
        )

        data = event.to_dict()

        assert data["event_type"] == "delta"
        assert data["content"] == "Hello World"
        assert data["stream_id"] == "stream123"
        assert data["metadata"] == {"key": "value"}
        assert "timestamp" in data


class TestAgentFrameworkStreamerInit:
    """Tests for AgentFrameworkStreamer initialization."""

    def test_streamer_initializes(self):
        """Test streamer initializes without error."""
        from src.agents.services.streaming.agent_framework_runner import AgentFrameworkStreamer

        streamer = AgentFrameworkStreamer()

        assert streamer is not None
        assert streamer.config is not None

    def test_streamer_with_custom_config(self):
        """Test streamer with custom configuration."""
        from src.agents.services.streaming.agent_framework_runner import (
            AgentFrameworkStreamer,
            StreamingConfig
        )

        config = StreamingConfig(framework="mock", chunk_delay=0.1)
        streamer = AgentFrameworkStreamer(config=config)

        assert streamer.config.framework == "mock"
        assert streamer.config.chunk_delay == 0.1

    def test_streamer_determines_framework(self):
        """Test that streamer determines framework automatically."""
        from src.agents.services.streaming.agent_framework_runner import AgentFrameworkStreamer

        streamer = AgentFrameworkStreamer()

        # Framework should be one of: agent_framework, autogen, or mock
        assert streamer.framework in ["agent_framework", "autogen", "mock"]

    def test_streamer_explicit_framework(self):
        """Test streamer with explicit framework selection."""
        from src.agents.services.streaming.agent_framework_runner import (
            AgentFrameworkStreamer,
            StreamingConfig
        )

        config = StreamingConfig(framework="mock")
        streamer = AgentFrameworkStreamer(config=config)

        assert streamer.framework == "mock"

    def test_streamer_active_streams_empty(self):
        """Test that active streams is empty on init."""
        from src.agents.services.streaming.agent_framework_runner import AgentFrameworkStreamer

        streamer = AgentFrameworkStreamer()

        assert len(streamer.active_streams) == 0


class TestMockStreaming:
    """Tests for mock streaming functionality."""

    @pytest.mark.asyncio
    async def test_mock_streaming_basic(self):
        """Test basic mock streaming."""
        from src.agents.services.streaming.agent_framework_runner import (
            AgentFrameworkStreamer,
            StreamingConfig,
            StreamingEventType
        )

        config = StreamingConfig(framework="mock")
        streamer = AgentFrameworkStreamer(config=config)

        events = []
        async for event in streamer.stream_response(None, "Hello test"):
            events.append(event)

        # Should have STATUS, multiple DELTAs, and FINAL
        assert len(events) >= 3
        assert events[0].event_type == StreamingEventType.STATUS
        assert events[-1].event_type == StreamingEventType.FINAL

    @pytest.mark.asyncio
    async def test_mock_streaming_delta_events(self):
        """Test that mock streaming produces delta events."""
        from src.agents.services.streaming.agent_framework_runner import (
            AgentFrameworkStreamer,
            StreamingConfig,
            StreamingEventType
        )

        config = StreamingConfig(framework="mock")
        streamer = AgentFrameworkStreamer(config=config)

        delta_events = []
        async for event in streamer.stream_response(None, "Test message"):
            if event.event_type == StreamingEventType.DELTA:
                delta_events.append(event)

        assert len(delta_events) > 0
        # Each delta should have content
        for event in delta_events:
            assert event.content is not None

    @pytest.mark.asyncio
    async def test_mock_streaming_stream_id(self):
        """Test that all events have stream ID."""
        from src.agents.services.streaming.agent_framework_runner import (
            AgentFrameworkStreamer,
            StreamingConfig
        )

        config = StreamingConfig(framework="mock")
        streamer = AgentFrameworkStreamer(config=config)

        stream_ids = set()
        async for event in streamer.stream_response(None, "Test"):
            stream_ids.add(event.stream_id)

        # All events should have same stream ID
        assert len(stream_ids) == 1
        assert "" not in stream_ids  # Should not be empty


class TestStreamManagement:
    """Tests for stream management."""

    @pytest.mark.asyncio
    async def test_active_streams_during_streaming(self):
        """Test that stream is tracked while active."""
        from src.agents.services.streaming.agent_framework_runner import (
            AgentFrameworkStreamer,
            StreamingConfig
        )

        config = StreamingConfig(framework="mock")
        streamer = AgentFrameworkStreamer(config=config)

        # Start streaming but don't consume all events
        gen = streamer.stream_response(None, "Test")
        event = await gen.__anext__()

        # Stream should be active
        assert len(streamer.active_streams) == 1

        # Consume remaining events
        async for _ in gen:
            pass

        # Stream should be cleaned up
        assert len(streamer.active_streams) == 0

    @pytest.mark.asyncio
    async def test_cancel_stream(self):
        """Test stream cancellation."""
        from src.agents.services.streaming.agent_framework_runner import (
            AgentFrameworkStreamer,
            StreamingConfig
        )

        config = StreamingConfig(framework="mock")
        streamer = AgentFrameworkStreamer(config=config)

        # Start streaming
        gen = streamer.stream_response(None, "Test")
        event = await gen.__anext__()
        stream_id = event.stream_id

        # Cancel it (cancel_stream is async)
        result = await streamer.cancel_stream(stream_id)

        assert result is True
        assert stream_id not in streamer.active_streams

    @pytest.mark.asyncio
    async def test_cancel_nonexistent_stream(self):
        """Test cancelling nonexistent stream."""
        from src.agents.services.streaming.agent_framework_runner import (
            AgentFrameworkStreamer,
            StreamingConfig
        )

        config = StreamingConfig(framework="mock")
        streamer = AgentFrameworkStreamer(config=config)

        result = await streamer.cancel_stream("nonexistent")

        assert result is False

    def test_get_active_streams(self):
        """Test getting active streams."""
        from src.agents.services.streaming.agent_framework_runner import AgentFrameworkStreamer

        streamer = AgentFrameworkStreamer()

        streams = streamer.get_active_streams()

        assert isinstance(streams, set)


class TestStreamerStats:
    """Tests for streamer statistics."""

    def test_get_stats(self):
        """Test getting streamer stats."""
        from src.agents.services.streaming.agent_framework_runner import AgentFrameworkStreamer

        streamer = AgentFrameworkStreamer()

        stats = streamer.get_stats()

        assert "framework" in stats
        assert "active_streams" in stats
        assert "agent_framework_available" in stats
        assert "autogen_available" in stats
        assert "config" in stats

    def test_stats_config_values(self):
        """Test that stats include config values."""
        from src.agents.services.streaming.agent_framework_runner import (
            AgentFrameworkStreamer,
            StreamingConfig
        )

        config = StreamingConfig(window_size=25, heartbeat_interval=45.0)
        streamer = AgentFrameworkStreamer(config=config)

        stats = streamer.get_stats()

        assert stats["config"]["window_size"] == 25
        assert stats["config"]["heartbeat_interval"] == 45.0


class TestConvenienceFunction:
    """Tests for convenience function."""

    @pytest.mark.asyncio
    async def test_stream_agent_response(self):
        """Test convenience streaming function."""
        from src.agents.services.streaming.agent_framework_runner import (
            stream_agent_response,
            StreamingConfig,
            StreamingEventType
        )

        config = StreamingConfig(framework="mock")
        events = []

        async for event in stream_agent_response(None, "Test", config=config):
            events.append(event)

        assert len(events) >= 3
        assert events[0].event_type == StreamingEventType.STATUS
        assert events[-1].event_type == StreamingEventType.FINAL


class TestErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_streaming_error_yields_error_event(self):
        """Test that streaming errors produce error events."""
        from src.agents.services.streaming.agent_framework_runner import (
            AgentFrameworkStreamer,
            StreamingConfig,
            StreamingEventType
        )

        # Use a mock agent that raises an error
        mock_agent = MagicMock()
        mock_agent.run_stream = AsyncMock(side_effect=Exception("Test error"))

        config = StreamingConfig(framework="agent_framework")
        streamer = AgentFrameworkStreamer(config=config)

        # Patch AGENT_FRAMEWORK_AVAILABLE to True
        with patch.object(
            streamer, '_stream_with_agent_framework',
            side_effect=Exception("Framework error")
        ):
            # Force framework to agent_framework
            streamer.framework = "agent_framework"

            events = []
            async for event in streamer.stream_response(mock_agent, "Test"):
                events.append(event)

            # Should have error event
            error_events = [e for e in events if e.event_type == StreamingEventType.ERROR]
            assert len(error_events) > 0


class TestModuleExports:
    """Tests for module exports."""

    def test_all_exports_accessible(self):
        """Test that all exports are accessible."""
        from src.agents.services.streaming.agent_framework_runner import (
            AgentFrameworkStreamer,
            StreamingConfig,
            StreamEvent,
            StreamingEventType,
            stream_agent_response,
            AGENT_FRAMEWORK_AVAILABLE,
            AUTOGEN_AVAILABLE
        )

        assert AgentFrameworkStreamer is not None
        assert StreamingConfig is not None
        assert StreamEvent is not None
        assert StreamingEventType is not None
        assert stream_agent_response is not None
        assert isinstance(AGENT_FRAMEWORK_AVAILABLE, bool)
        assert isinstance(AUTOGEN_AVAILABLE, bool)
