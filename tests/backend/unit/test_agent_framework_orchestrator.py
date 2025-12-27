"""
Unit tests for AgentFrameworkOrchestrator (F6).
Tests orchestration, agent execution, and framework integration.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from typing import Dict, Any


class TestOrchestratorImports:
    """Tests for module import and framework detection."""

    def test_module_imports_successfully(self):
        """Test that orchestrator module imports without error."""
        from src.agents.services import agent_framework_orchestrator
        assert agent_framework_orchestrator is not None

    def test_framework_flags_exist(self):
        """Test that framework availability flags are defined."""
        from src.agents.services.agent_framework_orchestrator import (
            AGENT_FRAMEWORK_AVAILABLE,
            AUTOGEN_AVAILABLE
        )
        assert isinstance(AGENT_FRAMEWORK_AVAILABLE, bool)
        assert isinstance(AUTOGEN_AVAILABLE, bool)

    def test_orchestrator_class_exists(self):
        """Test that AgentFrameworkOrchestrator class exists."""
        from src.agents.services.agent_framework_orchestrator import AgentFrameworkOrchestrator
        assert AgentFrameworkOrchestrator is not None

    def test_config_class_exists(self):
        """Test that OrchestratorConfig class exists."""
        from src.agents.services.agent_framework_orchestrator import OrchestratorConfig
        assert OrchestratorConfig is not None

    def test_result_class_exists(self):
        """Test that AgentExecutionResult class exists."""
        from src.agents.services.agent_framework_orchestrator import AgentExecutionResult
        assert AgentExecutionResult is not None


class TestOrchestratorConfig:
    """Tests for OrchestratorConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        from src.agents.services.agent_framework_orchestrator import OrchestratorConfig

        config = OrchestratorConfig()

        assert config.max_turns == 10
        assert config.timeout_seconds == 300.0
        assert config.enable_streaming is True
        assert config.enable_tools is True
        assert config.enable_memory is True
        assert config.fallback_to_autogen is True

    def test_custom_config(self):
        """Test custom configuration values."""
        from src.agents.services.agent_framework_orchestrator import OrchestratorConfig

        config = OrchestratorConfig(
            max_turns=5,
            timeout_seconds=60.0,
            enable_streaming=False
        )

        assert config.max_turns == 5
        assert config.timeout_seconds == 60.0
        assert config.enable_streaming is False


class TestAgentExecutionResult:
    """Tests for AgentExecutionResult dataclass."""

    def test_result_creation(self):
        """Test result creation with required fields."""
        from src.agents.services.agent_framework_orchestrator import AgentExecutionResult

        result = AgentExecutionResult(
            success=True,
            agent_key="test_agent",
            response="Hello",
            messages=[{"role": "assistant", "content": "Hello"}]
        )

        assert result.success is True
        assert result.agent_key == "test_agent"
        assert result.response == "Hello"
        assert len(result.messages) == 1

    def test_result_default_values(self):
        """Test result default values."""
        from src.agents.services.agent_framework_orchestrator import AgentExecutionResult

        result = AgentExecutionResult(
            success=True,
            agent_key="test",
            response="",
            messages=[]
        )

        assert result.tokens_used == 0
        assert result.execution_time_ms == 0.0
        assert result.error is None
        assert result.metadata == {}

    def test_result_with_error(self):
        """Test result with error."""
        from src.agents.services.agent_framework_orchestrator import AgentExecutionResult

        result = AgentExecutionResult(
            success=False,
            agent_key="test",
            response="",
            messages=[],
            error="Something went wrong"
        )

        assert result.success is False
        assert result.error == "Something went wrong"


class TestOrchestratorInit:
    """Tests for AgentFrameworkOrchestrator initialization."""

    def test_orchestrator_initializes(self):
        """Test that orchestrator can be initialized."""
        from src.agents.services.agent_framework_orchestrator import AgentFrameworkOrchestrator

        orchestrator = AgentFrameworkOrchestrator()

        assert orchestrator is not None
        assert orchestrator.config is not None

    def test_orchestrator_with_custom_config(self):
        """Test orchestrator with custom configuration."""
        from src.agents.services.agent_framework_orchestrator import (
            AgentFrameworkOrchestrator,
            OrchestratorConfig
        )

        config = OrchestratorConfig(max_turns=5)
        orchestrator = AgentFrameworkOrchestrator(config=config)

        assert orchestrator.config.max_turns == 5

    def test_orchestrator_determines_framework(self):
        """Test that orchestrator determines framework correctly."""
        from src.agents.services.agent_framework_orchestrator import (
            AgentFrameworkOrchestrator,
            AGENT_FRAMEWORK_AVAILABLE,
            AUTOGEN_AVAILABLE
        )

        orchestrator = AgentFrameworkOrchestrator()

        # Should be one of these frameworks
        assert orchestrator.framework in ["agent_framework", "autogen", "mock"]

    def test_orchestrator_has_registry(self):
        """Test that orchestrator has tools registry."""
        from src.agents.services.agent_framework_orchestrator import AgentFrameworkOrchestrator

        orchestrator = AgentFrameworkOrchestrator()

        assert hasattr(orchestrator, 'registry')
        assert orchestrator.registry is not None


class TestSingleAgentExecution:
    """Tests for execute_single_agent method."""

    @pytest.mark.asyncio
    async def test_execute_returns_result(self):
        """Test that execute returns AgentExecutionResult."""
        from src.agents.services.agent_framework_orchestrator import (
            AgentFrameworkOrchestrator,
            AgentExecutionResult
        )

        orchestrator = AgentFrameworkOrchestrator()

        # Execute with a test agent (will use mock mode if no framework)
        result = await orchestrator.execute_single_agent(
            agent_key="test_agent",
            message="Hello"
        )

        assert isinstance(result, AgentExecutionResult)
        assert result.agent_key == "test_agent"

    @pytest.mark.asyncio
    async def test_execute_handles_nonexistent_agent(self):
        """Test handling of nonexistent agent."""
        from src.agents.services.agent_framework_orchestrator import AgentFrameworkOrchestrator

        orchestrator = AgentFrameworkOrchestrator()

        result = await orchestrator.execute_single_agent(
            agent_key="nonexistent_agent_xyz",
            message="Hello"
        )

        # Should still return a result (mock or error)
        assert result is not None
        assert result.agent_key == "nonexistent_agent_xyz"

    @pytest.mark.asyncio
    async def test_execute_with_conversation_id(self):
        """Test execution with conversation ID."""
        from src.agents.services.agent_framework_orchestrator import AgentFrameworkOrchestrator

        orchestrator = AgentFrameworkOrchestrator()

        result = await orchestrator.execute_single_agent(
            agent_key="test_agent",
            message="Hello",
            conversation_id="conv_123"
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_execute_measures_time(self):
        """Test that execution measures time."""
        from src.agents.services.agent_framework_orchestrator import AgentFrameworkOrchestrator

        orchestrator = AgentFrameworkOrchestrator()

        result = await orchestrator.execute_single_agent(
            agent_key="test_agent",
            message="Hello"
        )

        assert result.execution_time_ms >= 0


class TestWorkflowExecution:
    """Tests for execute_workflow method."""

    @pytest.mark.asyncio
    async def test_workflow_returns_results_list(self):
        """Test that workflow returns list of results."""
        from src.agents.services.agent_framework_orchestrator import AgentFrameworkOrchestrator

        orchestrator = AgentFrameworkOrchestrator()

        workflow = [
            {"agent_key": "agent1"},
            {"agent_key": "agent2"}
        ]

        results = await orchestrator.execute_workflow(
            workflow=workflow,
            initial_message="Start"
        )

        assert isinstance(results, list)
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_empty_workflow(self):
        """Test handling of empty workflow."""
        from src.agents.services.agent_framework_orchestrator import AgentFrameworkOrchestrator

        orchestrator = AgentFrameworkOrchestrator()

        results = await orchestrator.execute_workflow(
            workflow=[],
            initial_message="Start"
        )

        assert results == []


class TestStreamingResponse:
    """Tests for stream_response method."""

    @pytest.mark.asyncio
    async def test_stream_yields_content(self):
        """Test that streaming yields content."""
        from src.agents.services.agent_framework_orchestrator import AgentFrameworkOrchestrator

        orchestrator = AgentFrameworkOrchestrator()

        chunks = []
        async for chunk in orchestrator.stream_response(
            agent_key="test_agent",
            message="Hello"
        ):
            chunks.append(chunk)

        assert len(chunks) > 0

    @pytest.mark.asyncio
    async def test_stream_with_streaming_disabled(self):
        """Test streaming when disabled falls back to full response."""
        from src.agents.services.agent_framework_orchestrator import (
            AgentFrameworkOrchestrator,
            OrchestratorConfig
        )

        config = OrchestratorConfig(enable_streaming=False)
        orchestrator = AgentFrameworkOrchestrator(config=config)

        chunks = []
        async for chunk in orchestrator.stream_response(
            agent_key="test_agent",
            message="Hello"
        ):
            chunks.append(chunk)

        # Should still yield at least one chunk
        assert len(chunks) >= 1


class TestThreadManagement:
    """Tests for thread/conversation management."""

    def test_get_or_create_thread(self):
        """Test thread creation."""
        from src.agents.services.agent_framework_orchestrator import AgentFrameworkOrchestrator

        orchestrator = AgentFrameworkOrchestrator()

        thread1 = orchestrator._get_or_create_thread("conv_1")
        thread2 = orchestrator._get_or_create_thread("conv_1")
        thread3 = orchestrator._get_or_create_thread("conv_2")

        # Same conversation should get same thread
        assert thread1 is thread2
        # Different conversation should get different thread
        assert thread1 is not thread3

    def test_clear_thread(self):
        """Test thread clearing."""
        from src.agents.services.agent_framework_orchestrator import AgentFrameworkOrchestrator

        orchestrator = AgentFrameworkOrchestrator()

        # Create a thread
        orchestrator._get_or_create_thread("conv_1")
        assert "conv_1" in orchestrator._threads

        # Clear it
        result = orchestrator.clear_thread("conv_1")
        assert result is True
        assert "conv_1" not in orchestrator._threads

    def test_clear_nonexistent_thread(self):
        """Test clearing nonexistent thread."""
        from src.agents.services.agent_framework_orchestrator import AgentFrameworkOrchestrator

        orchestrator = AgentFrameworkOrchestrator()

        result = orchestrator.clear_thread("nonexistent")
        assert result is False


class TestCallbacks:
    """Tests for callback registration."""

    def test_register_message_callback(self):
        """Test message callback registration."""
        from src.agents.services.agent_framework_orchestrator import AgentFrameworkOrchestrator

        orchestrator = AgentFrameworkOrchestrator()

        callback = MagicMock()
        orchestrator.register_message_callback(callback)

        assert callback in orchestrator._on_message_callbacks

    def test_register_error_callback(self):
        """Test error callback registration."""
        from src.agents.services.agent_framework_orchestrator import AgentFrameworkOrchestrator

        orchestrator = AgentFrameworkOrchestrator()

        callback = MagicMock()
        orchestrator.register_error_callback(callback)

        assert callback in orchestrator._on_error_callbacks


class TestMetrics:
    """Tests for metrics collection."""

    def test_get_metrics(self):
        """Test metrics retrieval."""
        from src.agents.services.agent_framework_orchestrator import AgentFrameworkOrchestrator

        orchestrator = AgentFrameworkOrchestrator()

        metrics = orchestrator.get_metrics()

        assert "framework" in metrics
        assert "active_threads" in metrics
        assert "cached_agents" in metrics
        assert "agent_framework_available" in metrics
        assert "autogen_available" in metrics


class TestGlobalInstance:
    """Tests for global orchestrator instance."""

    def test_get_orchestrator(self):
        """Test global orchestrator getter."""
        from src.agents.services.agent_framework_orchestrator import get_orchestrator

        orchestrator = get_orchestrator()

        assert orchestrator is not None

    def test_get_orchestrator_singleton(self):
        """Test that get_orchestrator returns singleton."""
        from src.agents.services.agent_framework_orchestrator import get_orchestrator

        orch1 = get_orchestrator()
        orch2 = get_orchestrator()

        assert orch1 is orch2


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    @pytest.mark.asyncio
    async def test_execute_agent_function(self):
        """Test execute_agent convenience function."""
        from src.agents.services.agent_framework_orchestrator import execute_agent

        result = await execute_agent(
            agent_key="test_agent",
            message="Hello"
        )

        assert result is not None
        assert result.agent_key == "test_agent"


class TestModuleExports:
    """Tests for module exports."""

    def test_all_exports_exist(self):
        """Test that all exports are accessible."""
        from src.agents.services.agent_framework_orchestrator import (
            AgentFrameworkOrchestrator,
            OrchestratorConfig,
            AgentExecutionResult,
            get_orchestrator,
            execute_agent,
            AGENT_FRAMEWORK_AVAILABLE,
            AUTOGEN_AVAILABLE
        )

        assert AgentFrameworkOrchestrator is not None
        assert OrchestratorConfig is not None
        assert AgentExecutionResult is not None
        assert get_orchestrator is not None
        assert execute_agent is not None
        assert isinstance(AGENT_FRAMEWORK_AVAILABLE, bool)
        assert isinstance(AUTOGEN_AVAILABLE, bool)
