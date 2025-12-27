"""
Unit tests for Agent Framework configuration and client initialization.
Tests B1-B4 of the Agent Framework migration.
"""

import pytest
from unittest.mock import patch, MagicMock


class TestAgentFrameworkConfig:
    """Tests for AgentFrameworkConfig model."""

    def test_default_config_values(self):
        """Test default configuration values are set correctly."""
        from src.core.agent_framework_config import AgentFrameworkConfig

        config = AgentFrameworkConfig()

        assert config.model_provider == "openai"
        assert config.model_name == "gpt-4"
        assert config.enable_checkpointing is True
        assert config.checkpoint_store == "redis"
        assert config.max_workflow_iterations == 50
        assert config.default_max_iterations == 10
        assert config.enable_tool_execution is True
        assert config.tool_timeout == 30
        assert config.concurrent_agents == 5
        assert config.enable_caching is True
        assert config.cache_ttl == 300
        assert config.enable_telemetry is True
        assert config.enable_safety_checks is True
        assert config.max_tokens_per_request == 4000
        assert config.rate_limit_per_minute == 60

    def test_custom_config_values(self):
        """Test configuration with custom values."""
        from src.core.agent_framework_config import AgentFrameworkConfig

        config = AgentFrameworkConfig(
            model_provider="azure",
            model_name="gpt-4-turbo",
            api_key="test-key",
            max_workflow_iterations=100,
            concurrent_agents=10,
        )

        assert config.model_provider == "azure"
        assert config.model_name == "gpt-4-turbo"
        assert config.api_key == "test-key"
        assert config.max_workflow_iterations == 100
        assert config.concurrent_agents == 10

    def test_get_agent_framework_config(self):
        """Test getting config from settings."""
        from src.core.agent_framework_config import get_agent_framework_config

        config = get_agent_framework_config()

        assert config is not None
        assert hasattr(config, "model_provider")
        assert hasattr(config, "model_name")


class TestAgentFrameworkClient:
    """Tests for Agent Framework client initialization."""

    @patch("src.core.agent_framework_config.logger")
    def test_get_client_openai_fallback(self, mock_logger):
        """Test OpenAI client falls back to AutoGen if AF not available."""
        from src.core.agent_framework_config import (
            AgentFrameworkConfig,
            get_agent_framework_client,
        )

        config = AgentFrameworkConfig(
            model_provider="openai",
            model_name="gpt-4",
        )

        # This should work and fall back to AutoGen if AF not installed
        try:
            client = get_agent_framework_client(config)
            assert client is not None
        except ImportError:
            # Expected if neither AF nor AutoGen is available
            pass

    @patch("src.core.agent_framework_config.logger")
    def test_get_client_unsupported_provider(self, mock_logger):
        """Test error for unsupported provider."""
        from src.core.agent_framework_config import (
            AgentFrameworkConfig,
            get_agent_framework_client,
        )

        config = AgentFrameworkConfig(
            model_provider="unsupported_provider",
        )

        with pytest.raises((ValueError, ImportError)):
            get_agent_framework_client(config)

    @pytest.mark.agent_framework
    def test_openai_client_initialization(self):
        """Test OpenAI client can be initialized with Agent Framework."""
        try:
            from agent_framework.openai import OpenAIChatClient

            # If import succeeds, Agent Framework is available
            from src.core.agent_framework_config import (
                AgentFrameworkConfig,
                get_agent_framework_client,
            )

            config = AgentFrameworkConfig(
                model_provider="openai",
                model_name="gpt-4",
                api_key="test-key",
            )

            with patch("agent_framework.openai.OpenAIChatClient") as mock_client:
                mock_client.return_value = MagicMock()
                client = get_agent_framework_client(config)
                assert client is not None

        except ImportError:
            pytest.skip("Agent Framework not installed")

    @pytest.mark.agent_framework
    def test_azure_client_initialization(self):
        """Test Azure client can be initialized with Agent Framework."""
        try:
            from agent_framework.azure import AzureOpenAIChatClient

            from src.core.agent_framework_config import (
                AgentFrameworkConfig,
                get_agent_framework_client,
            )

            config = AgentFrameworkConfig(
                model_provider="azure",
            )

            with patch("agent_framework.azure.AzureOpenAIChatClient") as mock_client:
                with patch("azure.identity.AzureCliCredential") as mock_cred:
                    mock_client.return_value = MagicMock()
                    client = get_agent_framework_client(config)
                    assert client is not None

        except ImportError:
            pytest.skip("Agent Framework Azure client not installed")


class TestCheckpointStore:
    """Tests for checkpoint store initialization."""

    def test_checkpoint_disabled(self):
        """Test checkpoint store returns None when disabled."""
        from src.core.agent_framework_config import (
            AgentFrameworkConfig,
            get_checkpoint_store,
        )

        config = AgentFrameworkConfig(enable_checkpointing=False)

        store = get_checkpoint_store(config)

        assert store is None

    @pytest.mark.agent_framework
    def test_memory_checkpoint_store(self):
        """Test in-memory checkpoint store initialization."""
        try:
            from agent_framework import InMemoryCheckpointStorage

            from src.core.agent_framework_config import (
                AgentFrameworkConfig,
                get_checkpoint_store,
            )

            config = AgentFrameworkConfig(
                enable_checkpointing=True,
                checkpoint_store="memory",
            )

            store = get_checkpoint_store(config)

            assert store is not None

        except ImportError:
            pytest.skip("Agent Framework not installed")

    def test_unknown_checkpoint_store_fallback(self):
        """Test unknown checkpoint store falls back gracefully."""
        from src.core.agent_framework_config import (
            AgentFrameworkConfig,
            get_checkpoint_store,
        )

        config = AgentFrameworkConfig(
            enable_checkpointing=True,
            checkpoint_store="unknown_store",
        )

        # Should not raise, should fall back or return None
        try:
            store = get_checkpoint_store(config)
            # Either returns a store or None, but shouldn't crash
        except ImportError:
            # Expected if Agent Framework not installed
            pass
