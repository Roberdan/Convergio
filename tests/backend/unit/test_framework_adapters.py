"""
Unit tests for Framework Adapters (I4).
Tests adapter interface, mock adapter, and feature flags.
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock, patch
import os


class TestFrameworkAdapterImports:
    """Tests for module imports."""

    def test_module_imports_successfully(self):
        """Test that adapters module imports without error."""
        from src.agents.adapters import framework_adapter
        assert framework_adapter is not None

    def test_framework_type_enum_exists(self):
        """Test that FrameworkType enum exists."""
        from src.agents.adapters import FrameworkType
        assert FrameworkType.AGENT_FRAMEWORK is not None
        assert FrameworkType.AUTOGEN is not None
        assert FrameworkType.MOCK is not None

    def test_adapter_classes_exist(self):
        """Test that adapter classes exist."""
        from src.agents.adapters import (
            FrameworkAdapter,
            MockFrameworkAdapter,
            create_adapter
        )
        assert FrameworkAdapter is not None
        assert MockFrameworkAdapter is not None
        assert create_adapter is not None


class TestAgentMessage:
    """Tests for AgentMessage dataclass."""

    def test_message_creation(self):
        """Test basic message creation."""
        from src.agents.adapters import AgentMessage

        msg = AgentMessage(
            content="Hello",
            source="user",
            role="user"
        )

        assert msg.content == "Hello"
        assert msg.source == "user"
        assert msg.role == "user"

    def test_message_default_timestamp(self):
        """Test that timestamp is set by default."""
        from src.agents.adapters import AgentMessage

        msg = AgentMessage(content="Test", source="test")

        assert msg.timestamp is not None
        assert isinstance(msg.timestamp, datetime)

    def test_message_default_metadata(self):
        """Test that metadata defaults to empty dict."""
        from src.agents.adapters import AgentMessage

        msg = AgentMessage(content="Test", source="test")

        assert msg.metadata == {}


class TestAgentResponse:
    """Tests for AgentResponse dataclass."""

    def test_response_creation(self):
        """Test basic response creation."""
        from src.agents.adapters import AgentResponse

        resp = AgentResponse(
            content="Hello World",
            agent_name="test_agent"
        )

        assert resp.content == "Hello World"
        assert resp.agent_name == "test_agent"
        assert resp.success is True
        assert resp.error is None

    def test_response_with_error(self):
        """Test response with error."""
        from src.agents.adapters import AgentResponse

        resp = AgentResponse(
            content="Error occurred",
            agent_name="test_agent",
            success=False,
            error="Something went wrong"
        )

        assert resp.success is False
        assert resp.error == "Something went wrong"

    def test_response_with_messages(self):
        """Test response with message list."""
        from src.agents.adapters import AgentResponse, AgentMessage

        messages = [
            AgentMessage(content="Hi", source="user"),
            AgentMessage(content="Hello!", source="agent")
        ]

        resp = AgentResponse(
            content="Hello!",
            agent_name="agent",
            messages=messages
        )

        assert len(resp.messages) == 2


class TestMockFrameworkAdapter:
    """Tests for MockFrameworkAdapter."""

    @pytest.mark.asyncio
    async def test_mock_adapter_initializes(self):
        """Test mock adapter initialization."""
        from src.agents.adapters import MockFrameworkAdapter

        adapter = MockFrameworkAdapter()
        result = await adapter.initialize("/fake/path")

        assert result is True
        assert adapter.is_initialized is True

    @pytest.mark.asyncio
    async def test_mock_adapter_creates_agents(self):
        """Test that mock adapter creates test agents."""
        from src.agents.adapters import MockFrameworkAdapter

        adapter = MockFrameworkAdapter()
        await adapter.initialize("/fake/path")

        agents = adapter.list_agents()

        assert len(agents) > 0
        assert "mock_agent_1" in agents

    @pytest.mark.asyncio
    async def test_mock_adapter_execute(self):
        """Test mock adapter execution."""
        from src.agents.adapters import MockFrameworkAdapter

        adapter = MockFrameworkAdapter()
        await adapter.initialize("/fake/path")

        response = await adapter.execute("mock_agent_1", "Hello")

        assert response.success is True
        assert "Mock Response" in response.content
        assert response.agent_name == "mock_agent_1"

    @pytest.mark.asyncio
    async def test_mock_adapter_execute_unknown_agent(self):
        """Test mock adapter with unknown agent."""
        from src.agents.adapters import MockFrameworkAdapter

        adapter = MockFrameworkAdapter()
        await adapter.initialize("/fake/path")

        response = await adapter.execute("unknown_agent", "Hello")

        assert response.success is False
        assert "not found" in response.content

    @pytest.mark.asyncio
    async def test_mock_adapter_stream(self):
        """Test mock adapter streaming."""
        from src.agents.adapters import MockFrameworkAdapter

        adapter = MockFrameworkAdapter()
        await adapter.initialize("/fake/path")

        chunks = []
        async for chunk in adapter.execute_stream("mock_agent_1", "Hello"):
            chunks.append(chunk)

        assert len(chunks) > 0
        assert all(hasattr(c, "content") for c in chunks)

    @pytest.mark.asyncio
    async def test_mock_adapter_get_stats(self):
        """Test mock adapter statistics."""
        from src.agents.adapters import MockFrameworkAdapter

        adapter = MockFrameworkAdapter()
        await adapter.initialize("/fake/path")
        await adapter.execute("mock_agent_1", "Test")

        stats = adapter.get_stats()

        assert stats["calls"] == 1
        assert stats["successes"] == 1
        assert stats["initialized"] is True

    @pytest.mark.asyncio
    async def test_mock_adapter_shutdown(self):
        """Test mock adapter shutdown."""
        from src.agents.adapters import MockFrameworkAdapter

        adapter = MockFrameworkAdapter()
        await adapter.initialize("/fake/path")
        await adapter.shutdown()

        assert adapter.is_initialized is False
        assert len(adapter.agents) == 0


class TestCreateAdapter:
    """Tests for create_adapter factory function."""

    def test_create_mock_adapter(self):
        """Test creating mock adapter."""
        from src.agents.adapters import create_adapter, FrameworkType

        adapter = create_adapter(FrameworkType.MOCK)

        assert adapter is not None
        assert adapter.framework_type == FrameworkType.MOCK

    def test_create_adapter_with_name(self):
        """Test creating adapter with custom name."""
        from src.agents.adapters import create_adapter, FrameworkType

        adapter = create_adapter(FrameworkType.MOCK, name="custom_adapter")

        assert adapter.name == "custom_adapter"

    def test_create_autogen_adapter_fallback(self):
        """Test that AutoGen adapter falls back to mock when not available."""
        from src.agents.adapters import create_adapter, FrameworkType

        # This should fall back to mock if autogen not installed
        adapter = create_adapter(FrameworkType.AUTOGEN)

        assert adapter is not None
        # Either autogen adapter or mock fallback
        assert adapter.framework_type in (FrameworkType.AUTOGEN, FrameworkType.MOCK)


class TestFeatureFlagImports:
    """Tests for feature flag imports."""

    def test_feature_flag_imports(self):
        """Test feature flag module imports."""
        from src.agents.adapters.feature_flag import (
            FrameworkFeatureFlag,
            FrameworkConfig,
            FrameworkSelection,
            get_feature_flag,
            use_agent_framework
        )
        assert FrameworkFeatureFlag is not None
        assert FrameworkConfig is not None
        assert FrameworkSelection is not None


class TestFrameworkSelection:
    """Tests for FrameworkSelection enum."""

    def test_selection_values(self):
        """Test framework selection enum values."""
        from src.agents.adapters import FrameworkSelection

        assert FrameworkSelection.AGENT_FRAMEWORK.value == "agent_framework"
        assert FrameworkSelection.AUTOGEN.value == "autogen"
        assert FrameworkSelection.MOCK.value == "mock"


class TestFrameworkConfig:
    """Tests for FrameworkConfig dataclass."""

    def test_config_defaults(self):
        """Test default configuration values."""
        from src.agents.adapters.feature_flag import FrameworkConfig, FrameworkSelection

        config = FrameworkConfig()

        assert config.selection == FrameworkSelection.AGENT_FRAMEWORK_WITH_FALLBACK
        assert config.agent_framework_percentage == 100
        assert config.enable_fallback is True
        assert config.fallback_on_error is True

    def test_config_custom_values(self):
        """Test custom configuration values."""
        from src.agents.adapters.feature_flag import FrameworkConfig, FrameworkSelection

        config = FrameworkConfig(
            selection=FrameworkSelection.AUTOGEN,
            agent_framework_percentage=50,
            enable_fallback=False
        )

        assert config.selection == FrameworkSelection.AUTOGEN
        assert config.agent_framework_percentage == 50
        assert config.enable_fallback is False


class TestFrameworkFeatureFlag:
    """Tests for FrameworkFeatureFlag."""

    def test_feature_flag_initialization(self):
        """Test feature flag initialization."""
        from src.agents.adapters.feature_flag import FrameworkFeatureFlag

        flag = FrameworkFeatureFlag()

        assert flag is not None
        assert flag.config is not None

    def test_feature_flag_with_config(self):
        """Test feature flag with custom config."""
        from src.agents.adapters.feature_flag import (
            FrameworkFeatureFlag,
            FrameworkConfig,
            FrameworkSelection
        )

        config = FrameworkConfig(selection=FrameworkSelection.MOCK)
        flag = FrameworkFeatureFlag(config=config)

        assert flag.config.selection == FrameworkSelection.MOCK

    def test_get_framework_type_mock(self):
        """Test getting framework type for mock selection."""
        from src.agents.adapters.feature_flag import (
            FrameworkFeatureFlag,
            FrameworkConfig,
            FrameworkSelection
        )
        from src.agents.adapters import FrameworkType

        config = FrameworkConfig(selection=FrameworkSelection.MOCK)
        flag = FrameworkFeatureFlag(config=config)

        result = flag.get_framework_type()

        assert result == FrameworkType.MOCK

    def test_get_framework_type_autogen(self):
        """Test getting framework type for autogen selection."""
        from src.agents.adapters.feature_flag import (
            FrameworkFeatureFlag,
            FrameworkConfig,
            FrameworkSelection
        )
        from src.agents.adapters import FrameworkType

        config = FrameworkConfig(selection=FrameworkSelection.AUTOGEN)
        flag = FrameworkFeatureFlag(config=config)

        result = flag.get_framework_type()

        assert result == FrameworkType.AUTOGEN

    def test_get_framework_type_agent_framework(self):
        """Test getting framework type for AF selection."""
        from src.agents.adapters.feature_flag import (
            FrameworkFeatureFlag,
            FrameworkConfig,
            FrameworkSelection
        )
        from src.agents.adapters import FrameworkType

        config = FrameworkConfig(selection=FrameworkSelection.AGENT_FRAMEWORK)
        flag = FrameworkFeatureFlag(config=config)

        result = flag.get_framework_type()

        assert result == FrameworkType.AGENT_FRAMEWORK

    def test_force_framework(self):
        """Test forcing specific framework."""
        from src.agents.adapters.feature_flag import (
            FrameworkFeatureFlag,
            FrameworkConfig,
            FrameworkSelection
        )
        from src.agents.adapters import FrameworkType

        config = FrameworkConfig(
            selection=FrameworkSelection.AGENT_FRAMEWORK,
            force_framework="mock"
        )
        flag = FrameworkFeatureFlag(config=config)

        result = flag.get_framework_type()

        assert result == FrameworkType.MOCK

    def test_get_adapter(self):
        """Test getting adapter from feature flag."""
        from src.agents.adapters.feature_flag import (
            FrameworkFeatureFlag,
            FrameworkConfig,
            FrameworkSelection
        )

        config = FrameworkConfig(selection=FrameworkSelection.MOCK)
        flag = FrameworkFeatureFlag(config=config)

        adapter = flag.get_adapter()

        assert adapter is not None

    def test_get_stats(self):
        """Test getting feature flag stats."""
        from src.agents.adapters.feature_flag import FrameworkFeatureFlag

        flag = FrameworkFeatureFlag()

        stats = flag.get_stats()

        assert "config" in stats
        assert "stats" in stats
        assert "selection" in stats["config"]

    def test_update_percentage(self):
        """Test updating traffic percentage."""
        from src.agents.adapters.feature_flag import FrameworkFeatureFlag

        flag = FrameworkFeatureFlag()
        flag.update_percentage(50)

        assert flag.config.agent_framework_percentage == 50

    def test_update_percentage_bounds(self):
        """Test percentage is bounded 0-100."""
        from src.agents.adapters.feature_flag import FrameworkFeatureFlag

        flag = FrameworkFeatureFlag()

        flag.update_percentage(150)
        assert flag.config.agent_framework_percentage == 100

        flag.update_percentage(-10)
        assert flag.config.agent_framework_percentage == 0


class TestGlobalFeatureFlag:
    """Tests for global feature flag instance."""

    def test_get_feature_flag(self):
        """Test getting global feature flag."""
        from src.agents.adapters.feature_flag import get_feature_flag, reset_feature_flag

        # Reset first
        reset_feature_flag()

        flag = get_feature_flag()

        assert flag is not None

    def test_get_feature_flag_singleton(self):
        """Test that get_feature_flag returns singleton."""
        from src.agents.adapters.feature_flag import get_feature_flag, reset_feature_flag

        reset_feature_flag()

        flag1 = get_feature_flag()
        flag2 = get_feature_flag()

        assert flag1 is flag2

    def test_reset_feature_flag(self):
        """Test resetting feature flag."""
        from src.agents.adapters.feature_flag import get_feature_flag, reset_feature_flag

        flag1 = get_feature_flag()
        reset_feature_flag()
        flag2 = get_feature_flag()

        assert flag1 is not flag2


class TestUseAgentFramework:
    """Tests for use_agent_framework convenience function."""

    def test_use_agent_framework_mock(self):
        """Test use_agent_framework with mock selection."""
        from src.agents.adapters.feature_flag import (
            FrameworkFeatureFlag,
            FrameworkConfig,
            FrameworkSelection,
            reset_feature_flag,
            get_feature_flag
        )

        reset_feature_flag()

        # Create flag with mock selection
        import src.agents.adapters.feature_flag as ff_module
        ff_module._feature_flag = FrameworkFeatureFlag(
            FrameworkConfig(selection=FrameworkSelection.MOCK)
        )

        from src.agents.adapters.feature_flag import use_agent_framework

        result = use_agent_framework()

        assert result is False  # Mock is not AF

        reset_feature_flag()


class TestAdapterWithFallback:
    """Tests for adapter with fallback support."""

    @pytest.mark.asyncio
    async def test_get_adapter_with_fallback_mock(self):
        """Test getting adapter with fallback using mock."""
        from src.agents.adapters.feature_flag import (
            FrameworkFeatureFlag,
            FrameworkConfig,
            FrameworkSelection,
        )
        from src.agents.adapters import FrameworkType

        config = FrameworkConfig(
            selection=FrameworkSelection.MOCK,
            enable_fallback=True
        )
        flag = FrameworkFeatureFlag(config=config)

        adapter = await flag.get_adapter_with_fallback("/fake/path")

        assert adapter is not None
        assert adapter.is_initialized is True
        assert adapter.framework_type == FrameworkType.MOCK


class TestModuleExports:
    """Tests for module exports."""

    def test_all_exports_accessible(self):
        """Test that all exports are accessible."""
        from src.agents.adapters import (
            FrameworkAdapter,
            FrameworkType,
            AgentMessage,
            AgentResponse,
            MockFrameworkAdapter,
            create_adapter,
            FrameworkFeatureFlag,
            FrameworkConfig,
            FrameworkSelection,
            get_feature_flag,
            reset_feature_flag,
            use_agent_framework,
        )

        assert FrameworkAdapter is not None
        assert FrameworkType is not None
        assert AgentMessage is not None
        assert AgentResponse is not None
        assert MockFrameworkAdapter is not None
        assert create_adapter is not None
        assert FrameworkFeatureFlag is not None
        assert FrameworkConfig is not None
        assert FrameworkSelection is not None
        assert get_feature_flag is not None
        assert reset_feature_flag is not None
        assert use_agent_framework is not None
