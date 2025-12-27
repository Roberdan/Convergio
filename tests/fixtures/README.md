# Agent Framework Test Fixtures

This directory contains pytest fixtures for testing Microsoft Agent Framework components in Convergio.

## Overview

The fixtures provide mock implementations of Agent Framework components, enabling unit testing without requiring actual Agent Framework installation or API calls.

## Available Fixtures

### Core Fixtures

#### `mock_chat_agent`
Factory fixture that creates mock ChatAgent instances.

```python
def test_my_agent(mock_chat_agent):
    agent = mock_chat_agent("ali", system_message="You are Ali")
    assert agent.name == "ali"

@pytest.mark.asyncio
async def test_agent_run(mock_chat_agent):
    agent = mock_chat_agent("test_agent")
    response = await agent.run("Hello")
    assert "test_agent" in response.lower()
```

#### `mock_workflow`
Factory fixture that creates mock Workflow instances.

```python
@pytest.mark.asyncio
async def test_workflow(mock_workflow):
    workflow = mock_workflow(
        outputs=["Step 1", "Step 2"],
        final_state={"completed": True}
    )
    result = await workflow.run("test input")
    assert result.get_outputs() == ["Step 1", "Step 2"]
```

#### `mock_agent_framework_client`
Factory fixture that creates mock chat clients (OpenAI, Azure, etc.).

```python
@pytest.mark.asyncio
async def test_client(mock_agent_framework_client):
    client = mock_agent_framework_client("openai", model="gpt-4")
    response = await client.create(messages=[...])
    assert response["role"] == "assistant"
```

#### `af_orchestrator`
Fully initialized AgentFrameworkOrchestrator for integration testing.

```python
@pytest.mark.asyncio
async def test_orchestration(af_orchestrator):
    result = await af_orchestrator.orchestrate("Hello")
    assert "response" in result
    assert result["duration_seconds"] >= 0
```

### Supporting Fixtures

#### `mock_workflow_builder`
Mock WorkflowBuilder with chainable methods.

```python
def test_builder(mock_workflow_builder):
    builder = mock_workflow_builder
    workflow = (builder
                .set_start_executor(my_executor)
                .add_edge(executor1, executor2)
                .build())
```

#### `mock_workflow_context`
Mock WorkflowContext with state management.

```python
@pytest.mark.asyncio
async def test_context(mock_workflow_context):
    ctx = mock_workflow_context
    await ctx.set_shared_state("key", "value")
    value = await ctx.get_shared_state("key")
    assert value == "value"
```

#### `mock_agent_executor`
Factory for creating mock AgentExecutor instances.

```python
@pytest.mark.asyncio
async def test_executor(mock_chat_agent, mock_agent_executor):
    agent = mock_chat_agent("test")
    executor = mock_agent_executor(agent)
    response = await executor.execute(request)
```

### Utility Fixtures

#### `agent_framework_available`
Boolean indicating if Agent Framework is installed.

```python
def test_conditional(agent_framework_available):
    if not agent_framework_available:
        pytest.skip("Agent Framework not installed")
    # Test code that requires AF
```

#### `skip_if_no_agent_framework`
Automatically skips tests if Agent Framework is not installed.

```python
def test_requires_af(skip_if_no_agent_framework):
    from agent_framework import ChatAgent
    # This test only runs if AF is installed
```

#### `agent_framework_examples`
Dictionary of example code snippets for documentation.

```python
def test_examples(agent_framework_examples):
    assert "basic_agent" in agent_framework_examples
    print(agent_framework_examples["workflow"])
```

## Usage Examples

### Basic Unit Test

```python
import pytest

def test_agent_creation(mock_chat_agent):
    """Test creating a mock agent"""
    agent = mock_chat_agent("test_agent", description="Test description")

    assert agent.name == "test_agent"
    assert agent.description == "Test description"
    assert hasattr(agent, "run")

@pytest.mark.asyncio
async def test_agent_execution(mock_chat_agent):
    """Test agent execution"""
    agent = mock_chat_agent("ali")
    response = await agent.run("What can you help with?")

    assert isinstance(response, str)
    assert len(response) > 0
```

### Testing Workflows

```python
import pytest

@pytest.mark.asyncio
async def test_workflow_execution(mock_workflow):
    """Test workflow with custom outputs"""
    workflow = mock_workflow(
        outputs=["Analysis complete", "Report generated"],
        final_state={"status": "completed", "steps": 2}
    )

    result = await workflow.run("Generate report")

    outputs = result.get_outputs()
    assert len(outputs) == 2
    assert "Analysis" in outputs[0]

    state = result.get_final_state()
    assert state["status"] == "completed"
    assert state["steps"] == 2

@pytest.mark.asyncio
async def test_workflow_streaming(mock_workflow):
    """Test workflow streaming"""
    workflow = mock_workflow(outputs=["chunk1", "chunk2", "chunk3"])

    chunks = []
    async for chunk in workflow.run_stream("test"):
        chunks.append(chunk)

    assert chunks == ["chunk1", "chunk2", "chunk3"]
```

### Testing Orchestrator

```python
import pytest

@pytest.mark.asyncio
@pytest.mark.skipif(
    not AGENT_FRAMEWORK_AVAILABLE,
    reason="Agent Framework not installed"
)
async def test_orchestrator(af_orchestrator):
    """Test complete orchestration"""
    result = await af_orchestrator.orchestrate(
        message="Analyze sales data",
        context={"test_mode": True}
    )

    assert "response" in result
    assert "agents_used" in result
    assert "duration_seconds" in result
    assert result["execution_mode"] == "workflow"
```

### Testing with Multiple Components

```python
import pytest

@pytest.mark.asyncio
async def test_full_stack(
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
        outputs=["Ali's response", "Amy's response"],
        final_state={"agents_used": ["ali", "amy"]}
    )

    # Test orchestration
    result = await workflow.run("Complex task")

    assert len(result.get_outputs()) == 2
    assert result.get_final_state()["agents_used"] == ["ali", "amy"]
```

## Fixture Registration

The fixtures are automatically registered via `pytest_plugins` in `/Users/roberdan/GitHub/convergio/tests/conftest.py`:

```python
pytest_plugins = [
    "fixtures.agent_framework",
]
```

This makes all fixtures available to all tests without explicit imports.

## Fallback Behavior

All fixtures are designed to work whether or not Agent Framework is installed:

- **With Agent Framework**: Fixtures use proper specs from `agent_framework` module
- **Without Agent Framework**: Fixtures use generic mocks that simulate the same behavior

Tests that absolutely require Agent Framework should use:
- `@pytest.mark.skipif(not AGENT_FRAMEWORK_AVAILABLE, reason="...")` decorator
- `skip_if_no_agent_framework` fixture
- `agent_framework_available` fixture with conditional logic

## Async Support

All fixtures are compatible with `pytest-asyncio`. Use the `@pytest.mark.asyncio` decorator for async tests:

```python
@pytest.mark.asyncio
async def test_async_operation(mock_chat_agent):
    agent = mock_chat_agent("test")
    result = await agent.run("test message")
    assert result is not None
```

## Running Tests Without Backend Server

For pure unit tests that don't need the backend server, set the environment variable:

```bash
AUTO_START_TEST_SERVER=false pytest tests/backend/unit/test_agent_framework_fixtures.py
```

## Test Organization

```
tests/
├── fixtures/
│   ├── __init__.py              # Exports all fixtures
│   ├── agent_framework.py       # Agent Framework fixtures
│   └── README.md                # This file
├── backend/
│   └── unit/
│       └── test_agent_framework_fixtures.py  # Fixture validation tests
└── conftest.py                  # Registers fixtures globally
```

## Best Practices

1. **Use factory fixtures for customization**: `mock_chat_agent()`, `mock_workflow()`, etc.
2. **Test with mocks first**: Validate logic with mocks before integration testing
3. **Skip appropriately**: Use skip decorators for tests requiring actual AF
4. **Keep tests isolated**: Each test should be independent
5. **Document fixtures**: Add docstrings to custom fixtures
6. **Validate behavior**: Write tests that verify the fixtures work correctly

## Troubleshooting

### Import Errors

If you get import errors, ensure:
- `tests/` directory is in Python path (handled by conftest.py)
- Fixtures are registered in `pytest_plugins` in conftest.py

### Fixture Not Found

If pytest can't find a fixture:
- Check it's exported in `fixtures/__init__.py`
- Verify it's listed in `pytest_plugins` in `tests/conftest.py`
- Try running with `-v` to see fixture registration

### Agent Framework Tests Skipping

If tests skip unexpectedly:
- Check `AGENT_FRAMEWORK_AVAILABLE` flag
- Install Agent Framework: `pip install agent-framework --pre`
- Remove skip decorators if they're not needed

## Contributing

When adding new fixtures:

1. Add the fixture function to `agent_framework.py`
2. Export it in `__init__.py`
3. Add tests to `test_agent_framework_fixtures.py`
4. Document usage in this README
5. Ensure fallback behavior when AF not installed

## Related Files

- `/Users/roberdan/GitHub/convergio/backend/src/agents/orchestrators/agent_framework_orchestrator.py` - Implementation being tested
- `/Users/roberdan/GitHub/convergio/backend/src/core/agent_framework_config.py` - Configuration
- `/Users/roberdan/GitHub/convergio/tests/conftest.py` - Global test configuration
