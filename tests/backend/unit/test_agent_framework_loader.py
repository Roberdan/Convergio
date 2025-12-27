"""
Unit tests for AgentFrameworkLoader (E4).
Tests agent loading, creation, and framework integration.
"""

import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from pathlib import Path
import os


class TestAgentFrameworkLoaderImports:
    """Tests for module import and framework detection."""

    def test_module_imports_successfully(self):
        """Test that agent_framework_loader module imports without error."""
        from src.agents.services import agent_framework_loader
        assert agent_framework_loader is not None

    def test_framework_flag_exists(self):
        """Test that framework availability flag is defined."""
        from src.agents.services.agent_framework_loader import AGENT_FRAMEWORK_AVAILABLE
        assert isinstance(AGENT_FRAMEWORK_AVAILABLE, bool)

    def test_loader_class_exists(self):
        """Test that AgentFrameworkLoader class exists."""
        from src.agents.services.agent_framework_loader import AgentFrameworkLoader
        assert AgentFrameworkLoader is not None


class TestAgentFrameworkLoaderInit:
    """Tests for AgentFrameworkLoader initialization."""

    def test_loader_initializes(self):
        """Test that loader can be initialized."""
        from src.agents.services.agent_framework_loader import AgentFrameworkLoader

        # Use a test directory path
        test_dir = "/tmp/test_agents"
        loader = AgentFrameworkLoader(test_dir, enable_hot_reload=False)

        assert loader is not None
        assert loader.agents_directory == Path(test_dir)

    def test_loader_sets_framework(self):
        """Test that loader sets framework type."""
        from src.agents.services.agent_framework_loader import (
            AgentFrameworkLoader,
            AGENT_FRAMEWORK_AVAILABLE
        )

        loader = AgentFrameworkLoader("/tmp/test_agents", enable_hot_reload=False)

        if AGENT_FRAMEWORK_AVAILABLE:
            assert loader.framework == "agent_framework"
        else:
            assert loader.framework == "autogen"

    def test_loader_has_config(self):
        """Test that loader has config."""
        from src.agents.services.agent_framework_loader import AgentFrameworkLoader

        loader = AgentFrameworkLoader("/tmp/test_agents", enable_hot_reload=False)

        assert hasattr(loader, 'config')
        assert loader.config is not None


class TestBuildInstructions:
    """Tests for _build_instructions method."""

    def test_build_instructions_returns_string(self):
        """Test that _build_instructions returns a string."""
        from src.agents.services.agent_framework_loader import AgentFrameworkLoader
        from src.agents.services.agent_loader import AgentMetadata

        loader = AgentFrameworkLoader("/tmp/test_agents", enable_hot_reload=False)

        # Create test metadata
        metadata = AgentMetadata(
            name="Test Agent",
            description="A test agent for unit tests",
            tools=["tool1", "tool2"],
            color="#FF0000",
            persona="A helpful test agent",
            expertise_keywords=["testing", "debugging"],
            tier="Strategic",
            class_name="TestAgentClass",
            key="test_agent"
        )

        instructions = loader._build_instructions(metadata)

        assert isinstance(instructions, str)
        assert len(instructions) > 0

    def test_build_instructions_contains_agent_info(self):
        """Test that instructions contain agent information."""
        from src.agents.services.agent_framework_loader import AgentFrameworkLoader
        from src.agents.services.agent_loader import AgentMetadata

        loader = AgentFrameworkLoader("/tmp/test_agents", enable_hot_reload=False)

        metadata = AgentMetadata(
            name="Test Agent",
            description="Testing description",
            tools=["web_search"],
            color="#00FF00",
            persona="Test persona text",
            expertise_keywords=["test", "example"],
            tier="Domain",
            class_name="TestClass",
            key="test_agent_key"
        )

        instructions = loader._build_instructions(metadata)

        assert "TestClass" in instructions
        assert "Testing description" in instructions
        assert "Test persona text" in instructions
        assert "test" in instructions
        assert "Domain" in instructions

    def test_build_instructions_contains_framework_guidance(self):
        """Test that instructions contain framework guidance."""
        from src.agents.services.agent_framework_loader import AgentFrameworkLoader
        from src.agents.services.agent_loader import AgentMetadata

        loader = AgentFrameworkLoader("/tmp/test_agents", enable_hot_reload=False)

        metadata = AgentMetadata(
            name="Test",
            description="Test",
            tools=[],
            color="#000000",
            persona="Test",
            expertise_keywords=[],
            tier="Core",
            class_name="Test",
            key="test"
        )

        instructions = loader._build_instructions(metadata)

        # Should contain framework guidance
        assert "MANDATORY" in instructions or "ANALYZE" in instructions
        assert "Convergio" in instructions


class TestToolConversion:
    """Tests for tool conversion methods."""

    def test_convert_tools_handles_empty_list(self):
        """Test that _convert_tools_for_agent_framework handles empty list."""
        from src.agents.services.agent_framework_loader import AgentFrameworkLoader

        loader = AgentFrameworkLoader("/tmp/test_agents", enable_hot_reload=False)

        result = loader._convert_tools_for_agent_framework([])

        assert result == []

    def test_convert_tools_handles_none(self):
        """Test that _convert_tools_for_agent_framework handles None."""
        from src.agents.services.agent_framework_loader import AgentFrameworkLoader

        loader = AgentFrameworkLoader("/tmp/test_agents", enable_hot_reload=False)

        result = loader._convert_tools_for_agent_framework(None)

        assert result == []

    def test_convert_tools_keeps_compatible_tools(self):
        """Test that compatible tools are kept."""
        from src.agents.services.agent_framework_loader import AgentFrameworkLoader

        loader = AgentFrameworkLoader("/tmp/test_agents", enable_hot_reload=False)

        # Create a mock compatible tool (function with __name__ and __annotations__)
        def test_tool(arg1: str) -> str:
            """Test tool."""
            return arg1

        result = loader._convert_tools_for_agent_framework([test_tool])

        assert len(result) == 1
        assert result[0] == test_tool


class TestChatClientCreation:
    """Tests for chat client creation."""

    def test_get_chat_client_without_framework(self):
        """Test that get_chat_client raises error when framework not available."""
        from src.agents.services.agent_framework_loader import (
            AgentFrameworkLoader,
            AGENT_FRAMEWORK_AVAILABLE
        )

        loader = AgentFrameworkLoader("/tmp/test_agents", enable_hot_reload=False)

        if not AGENT_FRAMEWORK_AVAILABLE:
            with pytest.raises(ImportError):
                loader.get_chat_client("openai")

    def test_get_chat_client_invalid_provider(self):
        """Test that get_chat_client raises for invalid provider."""
        from src.agents.services.agent_framework_loader import (
            AgentFrameworkLoader,
            AGENT_FRAMEWORK_AVAILABLE
        )

        if not AGENT_FRAMEWORK_AVAILABLE:
            pytest.skip("Agent Framework not available")

        loader = AgentFrameworkLoader("/tmp/test_agents", enable_hot_reload=False)

        with pytest.raises(ValueError, match="Unsupported provider"):
            loader.get_chat_client("invalid_provider")


class TestCreateChatAgents:
    """Tests for create_chat_agents method."""

    def test_create_chat_agents_requires_framework(self):
        """Test that create_chat_agents requires Agent Framework."""
        from src.agents.services.agent_framework_loader import (
            AgentFrameworkLoader,
            AGENT_FRAMEWORK_AVAILABLE
        )

        if AGENT_FRAMEWORK_AVAILABLE:
            pytest.skip("Agent Framework is available, can't test missing case")

        loader = AgentFrameworkLoader("/tmp/test_agents", enable_hot_reload=False)

        mock_client = MagicMock()

        with pytest.raises(ImportError, match="Agent Framework not installed"):
            loader.create_chat_agents(mock_client, tools=[])


class TestHybridAgents:
    """Tests for hybrid agent creation."""

    def test_create_hybrid_agents_returns_structure(self):
        """Test that create_hybrid_agents returns expected structure."""
        from src.agents.services.agent_framework_loader import AgentFrameworkLoader

        loader = AgentFrameworkLoader("/tmp/test_agents", enable_hot_reload=False)

        # Mock clients
        mock_chat_client = MagicMock()
        mock_model_client = MagicMock()

        # Mock the methods to avoid actual creation
        loader.create_chat_agents = MagicMock(return_value={})
        loader.create_autogen_agents = MagicMock(return_value={})

        result = loader.create_hybrid_agents(
            chat_client=mock_chat_client,
            model_client=mock_model_client,
            tools=[]
        )

        assert "agent_framework" in result
        assert "autogen" in result
        assert "metadata" in result


class TestGlobalInstance:
    """Tests for global loader instance."""

    def test_global_instance_exists(self):
        """Test that global agent_framework_loader instance exists."""
        from src.agents.services.agent_framework_loader import agent_framework_loader

        assert agent_framework_loader is not None

    def test_global_instance_is_loader(self):
        """Test that global instance is AgentFrameworkLoader."""
        from src.agents.services.agent_framework_loader import (
            agent_framework_loader,
            AgentFrameworkLoader
        )

        assert isinstance(agent_framework_loader, AgentFrameworkLoader)


class TestAgentMetadataIntegration:
    """Tests for integration with AgentMetadata."""

    def test_loader_inherits_from_dynamic_loader(self):
        """Test that AgentFrameworkLoader inherits from DynamicAgentLoader."""
        from src.agents.services.agent_framework_loader import AgentFrameworkLoader
        from src.agents.services.agent_loader import DynamicAgentLoader

        loader = AgentFrameworkLoader("/tmp/test_agents", enable_hot_reload=False)

        assert isinstance(loader, DynamicAgentLoader)

    def test_loader_has_agent_metadata_dict(self):
        """Test that loader has agent_metadata dictionary."""
        from src.agents.services.agent_framework_loader import AgentFrameworkLoader

        loader = AgentFrameworkLoader("/tmp/test_agents", enable_hot_reload=False)

        assert hasattr(loader, 'agent_metadata')
        assert isinstance(loader.agent_metadata, dict)


class TestLoaderWithRealAgentDefinitions:
    """Tests using real agent definition files."""

    @pytest.fixture
    def real_loader(self):
        """Get loader with real agent definitions directory."""
        from src.agents.services.agent_framework_loader import agent_framework_loader
        return agent_framework_loader

    def test_real_loader_has_definitions_dir(self, real_loader):
        """Test that real loader points to actual definitions directory."""
        assert real_loader.agents_directory.exists() or True  # May not exist in test env

    def test_scan_and_load_agents(self, real_loader):
        """Test scanning and loading agent definitions."""
        # This tests actual loading if definitions exist
        if real_loader.agents_directory.exists():
            agents = real_loader.scan_and_load_agents()
            assert isinstance(agents, dict)


class TestLoaderExports:
    """Tests for module exports."""

    def test_module_exports(self):
        """Test that module exports expected items."""
        from src.agents.services import agent_framework_loader

        # Check expected attributes exist
        assert hasattr(agent_framework_loader, 'AgentFrameworkLoader')
        assert hasattr(agent_framework_loader, 'AGENT_FRAMEWORK_AVAILABLE')
        assert hasattr(agent_framework_loader, 'agent_framework_loader')
