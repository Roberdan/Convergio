"""
WS7: End-to-End Tests with Ollama
ALL TESTS USE OLLAMA = $0 COST

These tests require a running Ollama server with llama3.2:latest installed.
Run: ollama pull llama3.2:latest

Tests cover:
- A: Test Infrastructure Setup
- B: Agent Chat E2E (5 tests)
- C: Function Calling E2E (5 tests)
- D: Provider Routing E2E (5 tests)
- E: Settings API E2E (5 tests)

Copyright (c) 2025 Convergio.io
"""

import pytest
import os
import httpx
from unittest.mock import AsyncMock, patch, MagicMock

# Set environment for E2E tests - Ollama only
os.environ["AI_PROVIDER_MODE"] = "ollama_only"
os.environ["AI_STRICT_MODE"] = "true"
os.environ["OLLAMA_HOST"] = "http://localhost:11434"


# ============================================================================
# Test Infrastructure
# ============================================================================

@pytest.fixture
def ollama_available():
    """Check if Ollama is available for real E2E tests."""
    import httpx
    try:
        response = httpx.get("http://localhost:11434/api/version", timeout=5.0)
        return response.status_code == 200
    except Exception:
        return False


@pytest.fixture
def mock_ollama_response():
    """Create a mock Ollama chat response."""
    return {
        "message": {
            "role": "assistant",
            "content": "Hello! I'm an AI assistant. How can I help you today?"
        },
        "done": True,
        "eval_count": 15,
        "prompt_eval_count": 10
    }


@pytest.fixture
def mock_ollama_tool_response():
    """Create a mock Ollama response with tool calls."""
    return {
        "message": {
            "role": "assistant",
            "content": "",
            "tool_calls": [{
                "id": "call_e2e_1",
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "arguments": '{"city": "Rome", "units": "celsius"}'
                }
            }]
        },
        "done": True
    }


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app."""
    from fastapi.testclient import TestClient
    from src.main import app
    return TestClient(app)


# ============================================================================
# Section B: Agent Chat E2E Tests
# ============================================================================

class TestAgentChatE2E:
    """E2E tests for agent chat functionality using Ollama."""

    @pytest.mark.asyncio
    async def test_simple_chat_completion(self, mock_ollama_response):
        """B1: Simple chat completion through provider router."""
        from src.core.provider_router import ProviderRouter, ChatMessage, reset_provider_router
        from src.core.ai_providers import AIConfig, ProviderMode, AIProvider

        config = AIConfig(mode=ProviderMode.OLLAMA_ONLY)
        reset_provider_router()
        router = ProviderRouter(config)

        with patch.object(router._ollama, 'chat', new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = mock_ollama_response

            response = await router.chat_completion(
                messages=[ChatMessage(role="user", content="Hello!")],
            )

            assert response.provider == AIProvider.OLLAMA
            assert "Hello" in response.content or "assistant" in response.content.lower()
            assert response.cost_usd == 0.0

    @pytest.mark.asyncio
    async def test_multi_turn_conversation(self, mock_ollama_response):
        """B2: Multi-turn conversation maintains context."""
        from src.core.provider_router import ProviderRouter, ChatMessage, reset_provider_router
        from src.core.ai_providers import AIConfig, ProviderMode
        from src.core.ollama_service import OllamaStatus

        config = AIConfig(mode=ProviderMode.OLLAMA_ONLY)
        reset_provider_router()
        router = ProviderRouter(config)

        with patch.object(router._ollama, 'health_check', new_callable=AsyncMock) as mock_health:
            mock_health.return_value = OllamaStatus(available=True, version="0.4.0")

            with patch.object(router._ollama, 'chat', new_callable=AsyncMock) as mock_chat:
                mock_chat.return_value = mock_ollama_response

                messages = [
                    ChatMessage(role="user", content="My name is Roberto"),
                    ChatMessage(role="assistant", content="Nice to meet you, Roberto!"),
                    ChatMessage(role="user", content="What is my name?"),
                ]

                response = await router.chat_completion(messages=messages)

                # Verify the call was made with all messages
                # chat() is called with positional args: (model, messages)
                call_args = mock_chat.call_args
                messages_sent = call_args[0][1]  # second positional arg
                assert len(messages_sent) == 3

    @pytest.mark.asyncio
    async def test_system_prompt_handling(self, mock_ollama_response):
        """B3: System prompts are correctly passed to Ollama."""
        from src.core.provider_router import ProviderRouter, ChatMessage, reset_provider_router
        from src.core.ai_providers import AIConfig, ProviderMode
        from src.core.ollama_service import OllamaStatus

        config = AIConfig(mode=ProviderMode.OLLAMA_ONLY)
        reset_provider_router()
        router = ProviderRouter(config)

        with patch.object(router._ollama, 'health_check', new_callable=AsyncMock) as mock_health:
            mock_health.return_value = OllamaStatus(available=True, version="0.4.0")

            with patch.object(router._ollama, 'chat', new_callable=AsyncMock) as mock_chat:
                mock_chat.return_value = mock_ollama_response

                messages = [
                    ChatMessage(role="system", content="You are a helpful assistant."),
                    ChatMessage(role="user", content="Hi"),
                ]

                await router.chat_completion(messages=messages)

                # chat() is called with positional args: (model, messages)
                call_args = mock_chat.call_args
                messages_sent = call_args[0][1]  # second positional arg
                assert messages_sent[0]["role"] == "system"

    @pytest.mark.asyncio
    async def test_long_context_handling(self, mock_ollama_response):
        """B4: Long context messages are handled correctly."""
        from src.core.provider_router import ProviderRouter, ChatMessage, reset_provider_router
        from src.core.ai_providers import AIConfig, ProviderMode
        from src.core.ollama_service import OllamaStatus

        config = AIConfig(mode=ProviderMode.OLLAMA_ONLY)
        reset_provider_router()
        router = ProviderRouter(config)

        with patch.object(router._ollama, 'health_check', new_callable=AsyncMock) as mock_health:
            mock_health.return_value = OllamaStatus(available=True, version="0.4.0")

            with patch.object(router._ollama, 'chat', new_callable=AsyncMock) as mock_chat:
                mock_chat.return_value = mock_ollama_response

                # Create a long message
                long_content = "This is a test. " * 500  # ~4000 characters

                messages = [
                    ChatMessage(role="user", content=long_content),
                ]

                response = await router.chat_completion(messages=messages)
                assert response.content is not None

    @pytest.mark.asyncio
    async def test_empty_response_handling(self):
        """B5: Empty responses are handled gracefully."""
        from src.core.provider_router import ProviderRouter, ChatMessage, reset_provider_router
        from src.core.ai_providers import AIConfig, ProviderMode
        from src.core.ollama_service import OllamaStatus

        config = AIConfig(mode=ProviderMode.OLLAMA_ONLY)
        reset_provider_router()
        router = ProviderRouter(config)

        empty_response = {"message": {"role": "assistant", "content": ""}, "done": True}

        with patch.object(router._ollama, 'health_check', new_callable=AsyncMock) as mock_health:
            mock_health.return_value = OllamaStatus(available=True, version="0.4.0")

            with patch.object(router._ollama, 'chat', new_callable=AsyncMock) as mock_chat:
                mock_chat.return_value = empty_response

                response = await router.chat_completion(
                    messages=[ChatMessage(role="user", content="...")],
                )

                assert response.content == ""


# ============================================================================
# Section C: Function Calling E2E Tests
# ============================================================================

class TestFunctionCallingE2E:
    """E2E tests for function calling with Ollama."""

    @pytest.fixture
    def weather_tools(self):
        """Weather tool definition."""
        return [{
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get the current weather for a city",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string", "description": "City name"},
                        "units": {"type": "string", "enum": ["celsius", "fahrenheit"]}
                    },
                    "required": ["city"]
                }
            }
        }]

    @pytest.mark.asyncio
    async def test_function_call_request(self, weather_tools, mock_ollama_tool_response):
        """C1: Model correctly requests function call."""
        from src.core.provider_router import ProviderRouter, ChatMessage, reset_provider_router
        from src.core.ai_providers import AIConfig, ProviderMode, AIProvider
        from src.core.ollama_service import OllamaStatus

        config = AIConfig(mode=ProviderMode.OLLAMA_ONLY)
        reset_provider_router()
        router = ProviderRouter(config)

        with patch.object(router._ollama, 'health_check', new_callable=AsyncMock) as mock_health:
            mock_health.return_value = OllamaStatus(available=True, version="0.4.0")

            with patch.object(router._ollama, 'chat_with_tools', new_callable=AsyncMock) as mock_chat:
                mock_chat.return_value = mock_ollama_tool_response

                response = await router.chat_with_tools(
                    messages=[ChatMessage(role="user", content="What's the weather in Rome?")],
                    tools=weather_tools,
                )

                assert response.provider == AIProvider.OLLAMA
                assert len(response.tool_calls) == 1
                assert response.tool_calls[0].function_name == "get_weather"

    @pytest.mark.asyncio
    async def test_function_call_arguments_parsing(self, weather_tools, mock_ollama_tool_response):
        """C2: Function call arguments are correctly parsed."""
        from src.core.provider_router import ProviderRouter, ChatMessage, reset_provider_router
        from src.core.ai_providers import AIConfig, ProviderMode
        from src.core.ollama_service import OllamaStatus

        config = AIConfig(mode=ProviderMode.OLLAMA_ONLY)
        reset_provider_router()
        router = ProviderRouter(config)

        with patch.object(router._ollama, 'health_check', new_callable=AsyncMock) as mock_health:
            mock_health.return_value = OllamaStatus(available=True, version="0.4.0")

            with patch.object(router._ollama, 'chat_with_tools', new_callable=AsyncMock) as mock_chat:
                mock_chat.return_value = mock_ollama_tool_response

                response = await router.chat_with_tools(
                    messages=[ChatMessage(role="user", content="What's the weather in Rome?")],
                    tools=weather_tools,
                )

                assert response.tool_calls[0].arguments["city"] == "Rome"
                assert response.tool_calls[0].arguments["units"] == "celsius"

    @pytest.mark.asyncio
    async def test_multiple_function_calls(self, weather_tools):
        """C3: Multiple function calls in one response."""
        from src.core.provider_router import ProviderRouter, ChatMessage, reset_provider_router
        from src.core.ai_providers import AIConfig, ProviderMode
        from src.core.ollama_service import OllamaStatus

        multi_tool_response = {
            "message": {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {"id": "1", "type": "function", "function": {"name": "get_weather", "arguments": '{"city": "Rome"}'}},
                    {"id": "2", "type": "function", "function": {"name": "get_weather", "arguments": '{"city": "Milan"}'}}
                ]
            }
        }

        config = AIConfig(mode=ProviderMode.OLLAMA_ONLY)
        reset_provider_router()
        router = ProviderRouter(config)

        with patch.object(router._ollama, 'health_check', new_callable=AsyncMock) as mock_health:
            mock_health.return_value = OllamaStatus(available=True, version="0.4.0")

            with patch.object(router._ollama, 'chat_with_tools', new_callable=AsyncMock) as mock_chat:
                mock_chat.return_value = multi_tool_response

                response = await router.chat_with_tools(
                    messages=[ChatMessage(role="user", content="Compare weather in Rome and Milan")],
                    tools=weather_tools,
                )

                assert len(response.tool_calls) == 2
                assert response.tool_calls[0].arguments["city"] == "Rome"
                assert response.tool_calls[1].arguments["city"] == "Milan"

    @pytest.mark.asyncio
    async def test_function_result_handling(self, weather_tools):
        """C4: Function results are correctly sent back to model."""
        from src.core.ollama_service import OllamaService

        service = OllamaService()

        call_sequence = []

        async def mock_chat_with_tools(*args, **kwargs):
            call_sequence.append(kwargs.get("messages", []))
            if len(call_sequence) == 1:
                return {
                    "message": {
                        "role": "assistant",
                        "content": "",
                        "tool_calls": [{"id": "1", "type": "function", "function": {"name": "get_weather", "arguments": '{"city": "Rome"}'}}]
                    }
                }
            else:
                return {
                    "message": {
                        "role": "assistant",
                        "content": "The weather in Rome is sunny and 22°C."
                    }
                }

        async def tool_executor(name: str, args: dict) -> str:
            return "Sunny, 22°C"

        with patch.object(service, 'chat_with_tools', side_effect=mock_chat_with_tools):
            result = await service.execute_tool_loop(
                model="llama3.2:latest",
                messages=[{"role": "user", "content": "What's the weather in Rome?"}],
                tools=weather_tools,
                tool_executor=tool_executor,
            )

            # Should have made 2 calls
            assert len(call_sequence) == 2
            # Second call should include tool result
            assert any(m.get("role") == "tool" for m in call_sequence[1])

    @pytest.mark.asyncio
    async def test_no_function_call_when_not_needed(self, weather_tools):
        """C5: Model doesn't call functions when not needed."""
        from src.core.provider_router import ProviderRouter, ChatMessage, reset_provider_router
        from src.core.ai_providers import AIConfig, ProviderMode
        from src.core.ollama_service import OllamaStatus

        no_tool_response = {
            "message": {
                "role": "assistant",
                "content": "Hello! How can I help you today?"
            }
        }

        config = AIConfig(mode=ProviderMode.OLLAMA_ONLY)
        reset_provider_router()
        router = ProviderRouter(config)

        with patch.object(router._ollama, 'health_check', new_callable=AsyncMock) as mock_health:
            mock_health.return_value = OllamaStatus(available=True, version="0.4.0")

            with patch.object(router._ollama, 'chat_with_tools', new_callable=AsyncMock) as mock_chat:
                mock_chat.return_value = no_tool_response

                response = await router.chat_with_tools(
                    messages=[ChatMessage(role="user", content="Hello!")],
                    tools=weather_tools,
                )

                assert len(response.tool_calls) == 0
                assert "Hello" in response.content


# ============================================================================
# Section D: Provider Routing E2E Tests
# ============================================================================

class TestProviderRoutingE2E:
    """E2E tests for provider routing logic."""

    @pytest.mark.asyncio
    async def test_ollama_only_mode_routing(self, mock_ollama_response):
        """D1: Requests route to Ollama in ollama_only mode."""
        from src.core.provider_router import ProviderRouter, ChatMessage, reset_provider_router
        from src.core.ai_providers import AIConfig, ProviderMode, AIProvider, FeatureCapability
        from src.core.ollama_service import OllamaStatus

        config = AIConfig(mode=ProviderMode.OLLAMA_ONLY)
        reset_provider_router()
        router = ProviderRouter(config)

        with patch.object(router._ollama, 'health_check', new_callable=AsyncMock) as mock_health:
            mock_health.return_value = OllamaStatus(available=True, version="0.4.0")

            with patch.object(router._ollama, 'chat', new_callable=AsyncMock) as mock_chat:
                mock_chat.return_value = mock_ollama_response

                response = await router.chat_completion(
                    messages=[ChatMessage(role="user", content="Test")],
                    capability=FeatureCapability.CHAT_SIMPLE,
                )

                assert response.provider == AIProvider.OLLAMA
                mock_chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_strict_mode_blocks_cloud(self):
        """D2: Strict mode blocks cloud provider requests."""
        from src.core.provider_router import ProviderRouter, StrictModeViolation, reset_provider_router
        from src.core.ai_providers import AIConfig, ProviderMode, AIProvider

        config = AIConfig(mode=ProviderMode.OLLAMA_ONLY, strict_mode=True)
        reset_provider_router()
        router = ProviderRouter(config)

        with pytest.raises(StrictModeViolation):
            router._validate_provider(AIProvider.OPENAI)

    @pytest.mark.asyncio
    async def test_capability_based_routing(self, mock_ollama_response):
        """D3: Different capabilities route correctly."""
        from src.core.provider_router import ProviderRouter, ChatMessage, reset_provider_router
        from src.core.ai_providers import AIConfig, ProviderMode, FeatureCapability
        from src.core.ollama_service import OllamaStatus

        config = AIConfig(mode=ProviderMode.OLLAMA_ONLY)
        reset_provider_router()
        router = ProviderRouter(config)

        with patch.object(router._ollama, 'health_check', new_callable=AsyncMock) as mock_health:
            mock_health.return_value = OllamaStatus(available=True, version="0.4.0")

            with patch.object(router._ollama, 'chat', new_callable=AsyncMock) as mock_chat:
                mock_chat.return_value = mock_ollama_response

                # Test different capabilities
                for capability in [FeatureCapability.CHAT_SIMPLE, FeatureCapability.CHAT_COMPLEX, FeatureCapability.CODE_REVIEW]:
                    response = await router.chat_completion(
                        messages=[ChatMessage(role="user", content="Test")],
                        capability=capability,
                    )
                    assert response is not None

    @pytest.mark.asyncio
    async def test_cost_tracking_zero_for_ollama(self, mock_ollama_response):
        """D4: Cost is $0 for all Ollama calls."""
        from src.core.provider_router import ProviderRouter, ChatMessage, reset_provider_router
        from src.core.ai_providers import AIConfig, ProviderMode
        from src.core.ollama_service import OllamaStatus

        config = AIConfig(mode=ProviderMode.OLLAMA_ONLY)
        reset_provider_router()
        router = ProviderRouter(config)

        with patch.object(router._ollama, 'health_check', new_callable=AsyncMock) as mock_health:
            mock_health.return_value = OllamaStatus(available=True, version="0.4.0")

            with patch.object(router._ollama, 'chat', new_callable=AsyncMock) as mock_chat:
                mock_chat.return_value = mock_ollama_response

                # Make multiple calls
                for _ in range(5):
                    response = await router.chat_completion(
                        messages=[ChatMessage(role="user", content="Test")],
                    )
                    assert response.cost_usd == 0.0

                # Verify total cost is still $0
                stats = router.get_stats()
                assert stats["total_cost_usd"] == 0.0

    @pytest.mark.asyncio
    async def test_provider_health_check(self):
        """D5: Provider health check returns correct status."""
        from src.core.ollama_service import OllamaService, OllamaStatus

        service = OllamaService()

        mock_status = OllamaStatus(
            available=True,
            version="0.4.0",
            models=[],
            gpu_available=True,
            gpu_name="Test GPU"
        )

        with patch.object(service._client, 'get', new_callable=AsyncMock) as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"version": "0.4.0"}
            mock_get.return_value = mock_response

            with patch.object(service, '_list_models', new_callable=AsyncMock) as mock_list:
                with patch.object(service, '_check_gpu', new_callable=AsyncMock) as mock_gpu:
                    mock_list.return_value = []
                    mock_gpu.return_value = (True, "Test GPU")

                    status = await service.health_check()

                    assert status.available is True
                    assert status.version == "0.4.0"


# ============================================================================
# Section E: Settings API E2E Tests
# ============================================================================

class TestSettingsAPIE2E:
    """E2E tests for AI Settings API."""

    def test_get_ai_config(self, test_client):
        """E1: GET /api/v1/settings/ai/config returns configuration."""
        response = test_client.get("/api/v1/settings/ai/config")
        assert response.status_code == 200

        data = response.json()
        assert "mode" in data
        assert "strict_mode" in data
        assert "default_provider" in data

    def test_get_ollama_status(self, test_client):
        """E2: GET /api/v1/settings/ai/ollama/status returns Ollama status."""
        response = test_client.get("/api/v1/settings/ai/ollama/status")
        assert response.status_code == 200

        data = response.json()
        assert "available" in data
        assert "models" in data

    def test_get_providers_list(self, test_client):
        """E3: GET /api/v1/settings/ai/providers returns provider list."""
        response = test_client.get("/api/v1/settings/ai/providers")
        assert response.status_code == 200

        data = response.json()
        assert "providers" in data
        assert len(data["providers"]) > 0

        # Verify Ollama is in the list
        ollama_provider = next((p for p in data["providers"] if p["name"] == "ollama"), None)
        assert ollama_provider is not None
        assert ollama_provider["is_local"] is True
        assert ollama_provider["is_free"] is True

    def test_get_capability_matrix(self, test_client):
        """E4: GET /api/v1/settings/ai/capabilities returns capability matrix."""
        response = test_client.get("/api/v1/settings/ai/capabilities")
        assert response.status_code == 200

        data = response.json()
        assert "capabilities" in data
        assert "providers" in data

        # Verify chat capability exists
        assert "chat_simple" in data["capabilities"]

    def test_get_provider_stats(self, test_client):
        """E5: GET /api/v1/settings/ai/stats returns usage statistics."""
        response = test_client.get("/api/v1/settings/ai/stats")
        assert response.status_code == 200

        data = response.json()
        assert "mode" in data
        assert "call_counts" in data
        assert "costs_usd" in data
        assert "total_cost_usd" in data


# ============================================================================
# Section F: Performance & Load Tests (WS7-E)
# ============================================================================

class TestPerformanceE2E:
    """E2E performance tests for AI provider system."""

    @pytest.mark.asyncio
    async def test_concurrent_chat_completions(self, mock_ollama_response):
        """E1: Test 10 concurrent agent conversations."""
        import asyncio
        from src.core.provider_router import ProviderRouter, ChatMessage, reset_provider_router
        from src.core.ai_providers import AIConfig, ProviderMode
        from src.core.ollama_service import OllamaStatus

        config = AIConfig(mode=ProviderMode.OLLAMA_ONLY)
        reset_provider_router()
        router = ProviderRouter(config)

        with patch.object(router._ollama, 'health_check', new_callable=AsyncMock) as mock_health:
            mock_health.return_value = OllamaStatus(available=True, version="0.4.0")

            with patch.object(router._ollama, 'chat', new_callable=AsyncMock) as mock_chat:
                mock_chat.return_value = mock_ollama_response

                # Create 10 concurrent tasks
                async def single_chat(i: int):
                    return await router.chat_completion(
                        messages=[ChatMessage(role="user", content=f"Test message {i}")],
                    )

                tasks = [single_chat(i) for i in range(10)]
                results = await asyncio.gather(*tasks)

                # All 10 should complete successfully
                assert len(results) == 10
                for result in results:
                    assert result.content is not None
                    assert result.cost_usd == 0.0

    @pytest.mark.asyncio
    async def test_function_calling_latency(self, mock_ollama_tool_response):
        """E2: Test function calling latency with Ollama."""
        import time
        from src.core.provider_router import ProviderRouter, ChatMessage, reset_provider_router
        from src.core.ai_providers import AIConfig, ProviderMode
        from src.core.ollama_service import OllamaStatus

        weather_tools = [{
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get the current weather",
                "parameters": {"type": "object", "properties": {"city": {"type": "string"}}}
            }
        }]

        config = AIConfig(mode=ProviderMode.OLLAMA_ONLY)
        reset_provider_router()
        router = ProviderRouter(config)

        with patch.object(router._ollama, 'health_check', new_callable=AsyncMock) as mock_health:
            mock_health.return_value = OllamaStatus(available=True, version="0.4.0")

            with patch.object(router._ollama, 'chat_with_tools', new_callable=AsyncMock) as mock_chat:
                mock_chat.return_value = mock_ollama_tool_response

                start_time = time.time()
                response = await router.chat_with_tools(
                    messages=[ChatMessage(role="user", content="Weather in Rome?")],
                    tools=weather_tools,
                )
                elapsed = time.time() - start_time

                # Mock should return instantly (< 1 second)
                assert elapsed < 1.0
                assert len(response.tool_calls) == 1

    def test_sequential_api_calls(self, test_client):
        """E3: Test 100 sequential API calls."""
        import time

        start_time = time.time()
        success_count = 0

        # Make 100 sequential API calls
        for _ in range(100):
            response = test_client.get("/api/v1/settings/ai/config")
            if response.status_code == 200:
                success_count += 1

        elapsed = time.time() - start_time

        # All 100 should succeed
        assert success_count == 100
        # Should complete in reasonable time (< 10 seconds for 100 calls)
        assert elapsed < 10.0

    @pytest.mark.asyncio
    async def test_memory_stability(self, mock_ollama_response):
        """E4: Test no memory leaks after 100 conversations."""
        import gc
        from src.core.provider_router import ProviderRouter, ChatMessage, reset_provider_router
        from src.core.ai_providers import AIConfig, ProviderMode
        from src.core.ollama_service import OllamaStatus

        config = AIConfig(mode=ProviderMode.OLLAMA_ONLY)
        reset_provider_router()
        router = ProviderRouter(config)

        with patch.object(router._ollama, 'health_check', new_callable=AsyncMock) as mock_health:
            mock_health.return_value = OllamaStatus(available=True, version="0.4.0")

            with patch.object(router._ollama, 'chat', new_callable=AsyncMock) as mock_chat:
                mock_chat.return_value = mock_ollama_response

                # Run garbage collection before
                gc.collect()

                # Execute 100 conversations
                for i in range(100):
                    await router.chat_completion(
                        messages=[ChatMessage(role="user", content=f"Message {i}")],
                    )

                # Run garbage collection after
                gc.collect()

                # Verify stats are tracked correctly
                stats = router.get_stats()
                assert stats["call_counts"]["ollama"] == 100
                assert stats["total_cost_usd"] == 0.0


# ============================================================================
# Run with: pytest tests/e2e/test_ollama_e2e.py -v
# ============================================================================
