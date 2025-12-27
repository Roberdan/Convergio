"""
Test Agent Framework Fixtures
Validates that the pytest fixtures work correctly and demonstrates their usage
"""

import sys
from pathlib import Path

# Add tests directory to path for imports
TESTS_DIR = Path(__file__).resolve().parents[2]
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

import pytest
from unittest.mock import Mock
from fixtures.agent_framework import AGENT_FRAMEWORK_AVAILABLE


class TestAgentFrameworkFixtures:
    """Test suite for Agent Framework fixtures"""

    def test_mock_chat_agent_basic(self, mock_chat_agent):
        """Test basic mock ChatAgent creation"""
        agent = mock_chat_agent("test_agent")

        assert agent.name == "test_agent"
        assert agent.system_message == "Test agent"
        assert hasattr(agent, "run")
        assert hasattr(agent, "get_tools")

    @pytest.mark.asyncio
    async def test_mock_chat_agent_run(self, mock_chat_agent):
        """Test mock ChatAgent async run method"""
        agent = mock_chat_agent("ali", system_message="You are Ali")

        response = await agent.run("Hello!")

        assert "ali" in response.lower()
        assert "hello" in response.lower()

    def test_mock_chat_agent_custom(self, mock_chat_agent):
        """Test mock ChatAgent with custom properties"""
        agent = mock_chat_agent(
            "custom_agent",
            system_message="Custom system message",
            description="Custom description",
            custom_prop="custom_value"
        )

        assert agent.name == "custom_agent"
        assert agent.description == "Custom description"
        assert agent.custom_prop == "custom_value"

    @pytest.mark.asyncio
    async def test_mock_workflow_basic(self, mock_workflow):
        """Test basic mock Workflow"""
        workflow = mock_workflow()

        result = await workflow.run("test input")

        assert result is not None
        assert result.get_outputs() == ["Test output"]
        assert result.get_final_state() == {"completed": True}

    @pytest.mark.asyncio
    async def test_mock_workflow_custom_outputs(self, mock_workflow):
        """Test mock Workflow with custom outputs"""
        workflow = mock_workflow(
            outputs=["First", "Second", "Third"],
            final_state={"step": 3, "completed": True}
        )

        result = await workflow.run("test")

        outputs = result.get_outputs()
        assert len(outputs) == 3
        assert outputs[0] == "First"

        state = result.get_final_state()
        assert state["step"] == 3
        assert state["completed"] is True

    @pytest.mark.asyncio
    async def test_mock_workflow_streaming(self, mock_workflow):
        """Test mock Workflow streaming"""
        workflow = mock_workflow(outputs=["chunk1", "chunk2", "chunk3"])

        chunks = []
        async for chunk in workflow.run_stream("test"):
            chunks.append(chunk)

        assert len(chunks) == 3
        assert chunks == ["chunk1", "chunk2", "chunk3"]

    def test_mock_workflow_builder(self, mock_workflow_builder):
        """Test mock WorkflowBuilder"""
        builder = mock_workflow_builder

        # Test method chaining
        result = (builder
                  .set_start_executor(Mock())
                  .add_edge(Mock(), Mock())
                  .with_checkpointing(Mock())
                  .set_max_iterations(100))

        assert result is builder  # Should return self for chaining

        # Test build
        workflow = builder.build()
        assert workflow is not None

    @pytest.mark.asyncio
    async def test_mock_workflow_context(self, mock_workflow_context):
        """Test mock WorkflowContext state management"""
        ctx = mock_workflow_context

        # Test set/get state
        await ctx.set_shared_state("key1", "value1")
        await ctx.set_shared_state("key2", 42)

        value1 = await ctx.get_shared_state("key1")
        value2 = await ctx.get_shared_state("key2")

        assert value1 == "value1"
        assert value2 == 42

        # Test missing key
        missing = await ctx.get_shared_state("nonexistent")
        assert missing is None

    @pytest.mark.asyncio
    async def test_mock_workflow_context_messaging(self, mock_workflow_context):
        """Test mock WorkflowContext messaging methods"""
        ctx = mock_workflow_context

        # Should not raise errors
        await ctx.send_message("test message")
        await ctx.yield_output("test output")

        # Verify methods were called
        assert ctx.send_message.called
        assert ctx.yield_output.called

    def test_mock_agent_framework_client_openai(self, mock_agent_framework_client):
        """Test mock OpenAI client"""
        client = mock_agent_framework_client("openai", api_key="test-key-123")

        assert client.provider == "openai"
        assert client.api_key == "test-key-123"

    @pytest.mark.asyncio
    async def test_mock_agent_framework_client_create(self, mock_agent_framework_client):
        """Test mock client create method"""
        client = mock_agent_framework_client("openai", model="gpt-4")

        response = await client.create(
            messages=[{"role": "user", "content": "Hello"}]
        )

        assert "content" in response
        assert response["role"] == "assistant"

    def test_mock_agent_framework_client_azure(self, mock_agent_framework_client):
        """Test mock Azure client"""
        client = mock_agent_framework_client("azure", deployment="test-deployment")

        assert client.provider == "azure"
        assert client.deployment == "test-deployment"

    def test_mock_agent_executor(self, mock_chat_agent, mock_agent_executor):
        """Test mock AgentExecutor"""
        agent = mock_chat_agent("test_agent")
        executor = mock_agent_executor(agent, agent_id="exec_1")

        assert executor.agent == agent
        assert executor.id == "exec_1"

    @pytest.mark.asyncio
    async def test_mock_agent_executor_execute(self, mock_chat_agent, mock_agent_executor):
        """Test mock AgentExecutor execution"""
        agent = mock_chat_agent("test_agent")
        executor = mock_agent_executor(agent)

        response = await executor.execute(Mock())

        assert response is not None
        assert hasattr(response, "agent_run_response")
        assert "test_agent" in response.agent_run_response.text

    def test_agent_framework_available_fixture(self, agent_framework_available):
        """Test agent_framework_available fixture"""
        # Should be a boolean
        assert isinstance(agent_framework_available, bool)

        # Check consistency with module-level flag
        assert agent_framework_available == AGENT_FRAMEWORK_AVAILABLE

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not AGENT_FRAMEWORK_AVAILABLE,
        reason="Agent Framework not installed"
    )
    async def test_af_orchestrator_initialization(self, af_orchestrator):
        """Test af_orchestrator fixture initialization"""
        # This test only runs if Agent Framework is installed
        assert af_orchestrator is not None
        assert af_orchestrator.is_initialized
        assert len(af_orchestrator.agents) == 3

        # Check agents
        assert "ali_chief_of_staff" in af_orchestrator.agents
        assert "amy_ai_assistant" in af_orchestrator.agents
        assert "bob_data_analyst" in af_orchestrator.agents

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not AGENT_FRAMEWORK_AVAILABLE,
        reason="Agent Framework not installed"
    )
    async def test_af_orchestrator_orchestrate(self, af_orchestrator):
        """Test af_orchestrator orchestration"""
        result = await af_orchestrator.orchestrate(
            message="Hello, how can you help?",
            context={"test_mode": True}
        )

        assert "response" in result
        assert isinstance(result["response"], str)
        assert "duration_seconds" in result

    def test_agent_framework_examples_fixture(self, agent_framework_examples):
        """Test agent_framework_examples documentation fixture"""
        assert "basic_agent" in agent_framework_examples
        assert "workflow" in agent_framework_examples
        assert "orchestrator" in agent_framework_examples

        # Verify examples are strings
        for key, example in agent_framework_examples.items():
            assert isinstance(example, str)
            assert len(example) > 0


class TestFixtureCombinations:
    """Test combinations of fixtures working together"""

    @pytest.mark.asyncio
    async def test_agent_with_client(self, mock_chat_agent, mock_agent_framework_client):
        """Test using agent and client together"""
        client = mock_agent_framework_client("openai")
        agent = mock_chat_agent("test_agent")

        # Simulate agent using client
        agent.client = client

        response = await agent.run("test message")
        assert response is not None

    @pytest.mark.asyncio
    async def test_workflow_with_agents(self, mock_workflow, mock_chat_agent):
        """Test workflow with multiple agents"""
        agents = [
            mock_chat_agent("agent1"),
            mock_chat_agent("agent2"),
            mock_chat_agent("agent3")
        ]

        workflow = mock_workflow(outputs=[
            await agents[0].run("test"),
            await agents[1].run("test"),
            await agents[2].run("test")
        ])

        result = await workflow.run("test")
        outputs = result.get_outputs()

        assert len(outputs) == 3
        for i, output in enumerate(outputs):
            assert f"agent{i+1}" in output.lower()

    @pytest.mark.asyncio
    async def test_full_stack_mock(
        self,
        mock_chat_agent,
        mock_workflow,
        mock_agent_framework_client
    ):
        """Test complete mocked stack"""
        # Create client
        client = mock_agent_framework_client("openai", model="gpt-4")

        # Create agents
        agents = {
            "ali": mock_chat_agent("ali", system_message="You are Ali"),
            "amy": mock_chat_agent("amy", system_message="You are Amy"),
        }

        # Create workflow
        workflow = mock_workflow(
            outputs=["Response from Ali", "Response from Amy"],
            final_state={"agents_used": ["ali", "amy"], "completed": True}
        )

        # Simulate orchestration
        result = await workflow.run("Complex task")
        outputs = result.get_outputs()
        state = result.get_final_state()

        assert len(outputs) == 2
        assert state["completed"] is True
        assert len(state["agents_used"]) == 2


class TestFixtureFallbacks:
    """Test fixture behavior when Agent Framework is not available"""

    def test_mock_chat_agent_without_af(self, mock_chat_agent):
        """Test mock_chat_agent works even without Agent Framework"""
        agent = mock_chat_agent("test")

        # Should work regardless of AF availability
        assert agent.name == "test"
        assert hasattr(agent, "run")

    def test_mock_client_without_af(self, mock_agent_framework_client):
        """Test mock_agent_framework_client works without Agent Framework"""
        client = mock_agent_framework_client("openai")

        # Should create generic mock when AF not available
        assert client.provider == "openai"
        assert hasattr(client, "create")

    @pytest.mark.skipif(
        AGENT_FRAMEWORK_AVAILABLE,
        reason="Test for when AF is NOT available"
    )
    def test_af_orchestrator_skips_without_af(self):
        """Verify af_orchestrator fixture skips when AF not available"""
        # This test verifies that when AF is not installed,
        # tests using af_orchestrator are skipped rather than failing
        pytest.skip("Agent Framework not installed - expected behavior")
