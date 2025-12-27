"""
Microsoft Agent Framework Test Fixtures
Provides mocks and fixtures for testing Agent Framework components

Usage:
    @pytest.mark.asyncio
    async def test_my_orchestrator(af_orchestrator):
        result = await af_orchestrator.orchestrate("Hello")
        assert result["response"]

    def test_with_mock_agent(mock_chat_agent):
        agent = mock_chat_agent("test_agent")
        assert agent.name == "test_agent"
"""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
from typing import Dict, Any, Optional, List
from datetime import datetime

# Check if Agent Framework is available
try:
    from agent_framework import (
        ChatAgent,
        Workflow,
        WorkflowBuilder,
        WorkflowContext,
        AgentExecutor,
        AgentExecutorRequest,
        AgentExecutorResponse,
        ChatMessage,
        Role,
    )
    AGENT_FRAMEWORK_AVAILABLE = True
except ImportError:
    AGENT_FRAMEWORK_AVAILABLE = False
    # Create placeholder classes for type hints
    ChatAgent = None
    Workflow = None
    WorkflowBuilder = None
    WorkflowContext = None
    AgentExecutor = None
    AgentExecutorRequest = None
    AgentExecutorResponse = None
    ChatMessage = None
    Role = None


@pytest.fixture
def mock_chat_agent():
    """
    Factory fixture that creates a mock ChatAgent.

    Returns a function that creates mock agents with customizable behavior.

    Usage:
        def test_agent(mock_chat_agent):
            agent = mock_chat_agent("ali", system_message="You are Ali")
            assert agent.name == "ali"

    Args:
        name: Agent name (default: "test_agent")
        system_message: Agent system message (default: "Test agent")
        **kwargs: Additional agent configuration

    Returns:
        Mock ChatAgent instance with async run method
    """
    def _create_mock_agent(
        name: str = "test_agent",
        system_message: str = "Test agent",
        **kwargs
    ) -> Mock:
        """Create a mock ChatAgent instance"""
        mock_agent = Mock(spec=ChatAgent if AGENT_FRAMEWORK_AVAILABLE else object)
        mock_agent.name = name
        mock_agent.system_message = system_message
        mock_agent.description = kwargs.get("description", f"Mock agent {name}")

        # Mock async run method
        async def mock_run(message: str, **run_kwargs) -> str:
            """Mock agent run that returns a test response"""
            return f"Response from {name}: {message}"

        mock_agent.run = AsyncMock(side_effect=mock_run)

        # Mock other common methods
        mock_agent.get_tools = Mock(return_value=[])
        mock_agent.reset = Mock()

        # Store kwargs for introspection
        for key, value in kwargs.items():
            setattr(mock_agent, key, value)

        return mock_agent

    return _create_mock_agent


@pytest.fixture
def mock_workflow():
    """
    Factory fixture that creates a mock Workflow.

    Returns a function that creates mock workflows with customizable behavior.

    Usage:
        @pytest.mark.asyncio
        async def test_workflow(mock_workflow):
            workflow = mock_workflow(outputs=["Final response"])
            result = await workflow.run("test input")
            assert result.get_outputs() == ["Final response"]

    Args:
        outputs: List of output strings (default: ["Test output"])
        final_state: Final workflow state (default: {})
        **kwargs: Additional workflow configuration

    Returns:
        Mock Workflow instance with async run method
    """
    def _create_mock_workflow(
        outputs: Optional[List[str]] = None,
        final_state: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Mock:
        """Create a mock Workflow instance"""
        mock_wf = Mock(spec=Workflow if AGENT_FRAMEWORK_AVAILABLE else object)

        # Default values
        if outputs is None:
            outputs = ["Test output"]
        if final_state is None:
            final_state = {"completed": True}

        # Mock WorkflowRunResult
        mock_result = Mock()
        mock_result.get_outputs = Mock(return_value=outputs)
        mock_result.get_final_state = Mock(return_value=final_state)

        # Mock async run method
        async def mock_run(message: str, **run_kwargs) -> Mock:
            """Mock workflow run that returns mock result"""
            return mock_result

        mock_wf.run = AsyncMock(side_effect=mock_run)

        # Mock async streaming method
        async def mock_run_stream(message: str, **stream_kwargs):
            """Mock workflow streaming that yields events"""
            for output in outputs:
                yield output

        mock_wf.run_stream = mock_run_stream

        # Store configuration
        mock_wf.max_iterations = kwargs.get("max_iterations", 50)
        mock_wf.checkpointing_enabled = kwargs.get("checkpointing_enabled", False)

        return mock_wf

    return _create_mock_workflow


@pytest.fixture
def mock_workflow_builder():
    """
    Fixture that creates a mock WorkflowBuilder.

    Usage:
        def test_builder(mock_workflow_builder):
            builder = mock_workflow_builder
            builder.set_start_executor(my_executor)
            workflow = builder.build()

    Returns:
        Mock WorkflowBuilder with method chaining
    """
    mock_builder = Mock(spec=WorkflowBuilder if AGENT_FRAMEWORK_AVAILABLE else object)

    # Make methods chainable (return self)
    mock_builder.set_start_executor = Mock(return_value=mock_builder)
    mock_builder.add_edge = Mock(return_value=mock_builder)
    mock_builder.with_checkpointing = Mock(return_value=mock_builder)
    mock_builder.set_max_iterations = Mock(return_value=mock_builder)

    # Build returns a mock workflow
    mock_wf = Mock(spec=Workflow if AGENT_FRAMEWORK_AVAILABLE else object)
    mock_wf.run = AsyncMock(return_value=Mock(
        get_outputs=Mock(return_value=["Test output"]),
        get_final_state=Mock(return_value={})
    ))
    mock_builder.build = Mock(return_value=mock_wf)

    return mock_builder


@pytest.fixture
def mock_workflow_context():
    """
    Fixture that creates a mock WorkflowContext.

    Usage:
        @pytest.mark.asyncio
        async def test_executor(mock_workflow_context):
            ctx = mock_workflow_context
            await ctx.set_shared_state("key", "value")
            value = await ctx.get_shared_state("key")
            assert value == "value"

    Returns:
        Mock WorkflowContext with async state management
    """
    mock_ctx = Mock(spec=WorkflowContext if AGENT_FRAMEWORK_AVAILABLE else object)

    # In-memory state storage
    state_store = {}

    async def mock_set_state(key: str, value: Any) -> None:
        """Mock set_shared_state"""
        state_store[key] = value

    async def mock_get_state(key: str) -> Any:
        """Mock get_shared_state"""
        return state_store.get(key)

    async def mock_send_message(message: Any) -> None:
        """Mock send_message"""
        pass

    async def mock_yield_output(output: str) -> None:
        """Mock yield_output"""
        pass

    mock_ctx.set_shared_state = AsyncMock(side_effect=mock_set_state)
    mock_ctx.get_shared_state = AsyncMock(side_effect=mock_get_state)
    mock_ctx.send_message = AsyncMock(side_effect=mock_send_message)
    mock_ctx.yield_output = AsyncMock(side_effect=mock_yield_output)

    return mock_ctx


@pytest.fixture
def mock_agent_framework_client():
    """
    Factory fixture that creates a mock Agent Framework chat client.

    Returns a function that creates mock clients for different providers.

    Usage:
        def test_client(mock_agent_framework_client):
            client = mock_agent_framework_client("openai")
            # Use client...

    Args:
        provider: Provider name ("openai" or "azure")
        api_key: Optional API key (default: "test-key")
        **kwargs: Additional client configuration

    Returns:
        Mock chat client instance

    Note:
        If Agent Framework is not installed, returns a generic mock.
        Tests should check AGENT_FRAMEWORK_AVAILABLE before using.
    """
    def _create_mock_client(
        provider: str = "openai",
        api_key: str = "test-key",
        **kwargs
    ) -> Mock:
        """Create a mock chat client"""
        if not AGENT_FRAMEWORK_AVAILABLE:
            # Return generic mock when AF not available
            mock_client = Mock()
            mock_client.provider = provider
            mock_client.api_key = api_key

            # Store configuration
            for key, value in kwargs.items():
                setattr(mock_client, key, value)

            mock_client.create = AsyncMock(return_value={
                "content": "Test response",
                "role": "assistant"
            })
            return mock_client

        # Try to import provider-specific client
        try:
            if provider.lower() == "openai":
                from agent_framework.openai import OpenAIChatClient
                spec_class = OpenAIChatClient
            elif provider.lower() == "azure":
                from agent_framework.azure import AzureOpenAIChatClient
                spec_class = AzureOpenAIChatClient
            else:
                spec_class = object
        except ImportError:
            spec_class = object

        mock_client = Mock(spec=spec_class)
        mock_client.provider = provider
        mock_client.api_key = api_key

        # Store configuration first (before create method)
        for key, value in kwargs.items():
            setattr(mock_client, key, value)

        # Mock create method for completions
        async def mock_create(messages, **create_kwargs):
            """Mock chat completion"""
            return {
                "content": f"Response from {provider}",
                "role": "assistant",
                "model": kwargs.get("model", "gpt-4")
            }

        mock_client.create = AsyncMock(side_effect=mock_create)

        return mock_client

    return _create_mock_client


@pytest.fixture
async def af_orchestrator(mock_chat_agent, mock_workflow):
    """
    Fixture that provides a fully initialized AgentFrameworkOrchestrator.

    Usage:
        @pytest.mark.asyncio
        async def test_orchestration(af_orchestrator):
            result = await af_orchestrator.orchestrate("Hello")
            assert "response" in result

    Provides:
        - Pre-initialized orchestrator
        - 3 mock agents (ali, amy, bob)
        - Mock workflow configured
        - Ready for testing

    Returns:
        Initialized AgentFrameworkOrchestrator instance

    Note:
        Requires Agent Framework to be installed. If not available,
        fixture will skip the test with pytest.skip().
    """
    if not AGENT_FRAMEWORK_AVAILABLE:
        pytest.skip("Agent Framework not installed - skipping test")

    # Import orchestrator
    from src.agents.orchestrators.agent_framework_orchestrator import (
        AgentFrameworkOrchestrator
    )

    # Create mock agents
    agents = {
        "ali_chief_of_staff": mock_chat_agent(
            "ali_chief_of_staff",
            system_message="You are Ali, the Chief of Staff",
            description="Executive coordinator"
        ),
        "amy_ai_assistant": mock_chat_agent(
            "amy_ai_assistant",
            system_message="You are Amy, the AI Assistant",
            description="AI assistant"
        ),
        "bob_data_analyst": mock_chat_agent(
            "bob_data_analyst",
            system_message="You are Bob, the Data Analyst",
            description="Data analysis expert"
        )
    }

    # Create orchestrator
    orchestrator = AgentFrameworkOrchestrator(name="test_orchestrator")

    # Initialize with mock agents
    agent_metadata = {
        name: {
            "name": name,
            "role": agent.description,
            "system_message": agent.system_message
        }
        for name, agent in agents.items()
    }

    # Replace workflow with mock before initialization
    # (to avoid actually building the workflow)
    original_build = orchestrator._build_workflow
    orchestrator._build_workflow = lambda: mock_workflow()

    success = await orchestrator.initialize(
        agents=agents,
        agent_metadata=agent_metadata,
        enable_safety=False  # Disable safety for tests
    )

    # Restore original method
    orchestrator._build_workflow = original_build

    assert success, "Orchestrator initialization failed"

    yield orchestrator

    # Cleanup
    orchestrator.agents.clear()
    orchestrator.agent_executors.clear()


# Utility fixtures for common test scenarios

@pytest.fixture
def agent_framework_available() -> bool:
    """
    Fixture that returns whether Agent Framework is available.

    Usage:
        def test_conditional(agent_framework_available):
            if not agent_framework_available:
                pytest.skip("Agent Framework required")
            # ... test code ...

    Returns:
        True if Agent Framework is installed, False otherwise
    """
    return AGENT_FRAMEWORK_AVAILABLE


@pytest.fixture
def skip_if_no_agent_framework():
    """
    Fixture that automatically skips tests if Agent Framework is not available.

    Usage:
        def test_requires_af(skip_if_no_agent_framework):
            # This test will be skipped if AF not installed
            from agent_framework import ChatAgent
            # ... test code ...
    """
    if not AGENT_FRAMEWORK_AVAILABLE:
        pytest.skip("Agent Framework not installed")


@pytest.fixture
def mock_agent_executor(mock_chat_agent):
    """
    Factory fixture that creates a mock AgentExecutor.

    Usage:
        def test_executor(mock_agent_executor):
            agent = mock_chat_agent("test")
            executor = mock_agent_executor(agent)

    Args:
        agent: ChatAgent instance to wrap
        agent_id: Optional ID for the executor

    Returns:
        Mock AgentExecutor instance
    """
    def _create_mock_executor(
        agent: Mock,
        agent_id: Optional[str] = None
    ) -> Mock:
        """Create a mock AgentExecutor"""
        mock_exec = Mock(spec=AgentExecutor if AGENT_FRAMEWORK_AVAILABLE else object)
        mock_exec.agent = agent
        mock_exec.id = agent_id or agent.name

        # Mock execute method
        async def mock_execute(request, **kwargs):
            """Mock executor execution"""
            response_mock = Mock(
                spec=AgentExecutorResponse if AGENT_FRAMEWORK_AVAILABLE else object
            )
            response_mock.agent_run_response = Mock(
                text=f"Response from {agent.name}"
            )
            return response_mock

        mock_exec.execute = AsyncMock(side_effect=mock_execute)

        return mock_exec

    return _create_mock_executor


# Documentation fixtures (for reference in tests)

@pytest.fixture
def agent_framework_examples() -> Dict[str, str]:
    """
    Fixture providing example code for Agent Framework usage.

    Useful for documentation tests or reference.

    Returns:
        Dictionary of example code snippets
    """
    return {
        "basic_agent": """
            from agent_framework import ChatAgent

            agent = ChatAgent(
                name="test_agent",
                system_message="You are a helpful assistant",
                model="gpt-4"
            )

            response = await agent.run("Hello!")
        """,
        "workflow": """
            from agent_framework import WorkflowBuilder, executor

            @executor(id="start")
            async def start(message: str, ctx):
                await ctx.yield_output(f"Processed: {message}")

            builder = WorkflowBuilder()
            builder.set_start_executor(start)
            workflow = builder.build()

            result = await workflow.run("test")
        """,
        "orchestrator": """
            orchestrator = AgentFrameworkOrchestrator()
            await orchestrator.initialize(agents=agents)
            result = await orchestrator.orchestrate("Hello")
        """
    }
