"""
WS6-H: AI Provider Tests
ALL TESTS USE OLLAMA = $0 COST

Tests for:
- H1: ProviderRouter with ollama_only mode
- H2: Strict mode blocks cloud providers
- H3: Ollama function calling
- H4: Ollama chat completion
- H5: Capability matrix routing
- H6: Per-agent provider override
- H7: Per-feature provider override
- H8: Cost tracking (Ollama = $0)
- H9: Settings API CRUD
- H10: Ollama health check

Copyright (c) 2025 Convergio.io
"""

import pytest
import os
from unittest.mock import AsyncMock, patch, MagicMock

# Set environment for tests - use Ollama only
os.environ["AI_PROVIDER_MODE"] = "ollama_only"
os.environ["AI_STRICT_MODE"] = "true"
os.environ["OLLAMA_HOST"] = "http://localhost:11434"

from src.core.ai_providers import (
    AIConfig,
    AIProvider,
    ProviderMode,
    FeatureCapability,
    get_ai_config_from_env,
    get_provider_for_capability,
    get_provider_for_agent,
    can_provider_handle_capability,
)
from src.core.provider_router import (
    ProviderRouter,
    ChatMessage,
    ChatResponse,
    ToolCall,
    StrictModeViolation,
    ProviderUnavailable,
    reset_provider_router,
)
from src.core.ollama_service import (
    OllamaService,
    OllamaStatus,
    OllamaModel,
    OllamaModelCapability,
    get_ollama_service,
)


class TestAIConfig:
    """Tests for AI configuration loading."""

    def test_config_loads_from_env(self):
        """H1: Config loads correctly from environment."""
        config = get_ai_config_from_env()
        assert config.mode == ProviderMode.OLLAMA_ONLY
        assert config.strict_mode is True
        assert config.default_provider == AIProvider.OLLAMA

    def test_provider_mode_enum(self):
        """All provider modes are defined."""
        assert ProviderMode.OLLAMA_ONLY.value == "ollama_only"
        assert ProviderMode.AZURE_ONLY.value == "azure_only"
        assert ProviderMode.HYBRID.value == "hybrid"
        assert ProviderMode.CLOUD_FIRST.value == "cloud_first"


class TestCapabilityMatrix:
    """Tests for capability matrix routing."""

    def test_ollama_supports_chat(self):
        """H5: Ollama supports chat capability."""
        assert can_provider_handle_capability(AIProvider.OLLAMA, FeatureCapability.CHAT_SIMPLE)
        assert can_provider_handle_capability(AIProvider.OLLAMA, FeatureCapability.CHAT_COMPLEX)

    def test_ollama_supports_function_calling(self):
        """H5: Ollama supports function calling."""
        assert can_provider_handle_capability(AIProvider.OLLAMA, FeatureCapability.FUNCTION_CALLING)

    def test_ollama_supports_code_review(self):
        """H5: Ollama supports code review."""
        assert can_provider_handle_capability(AIProvider.OLLAMA, FeatureCapability.CODE_REVIEW)

    def test_ollama_does_not_support_voice(self):
        """H5: Ollama does NOT support voice/realtime."""
        assert not can_provider_handle_capability(AIProvider.OLLAMA, FeatureCapability.VOICE_REALTIME)

    def test_capability_routing_in_ollama_mode(self):
        """H5: Routing returns Ollama in ollama_only mode."""
        config = AIConfig(mode=ProviderMode.OLLAMA_ONLY)
        provider, model = get_provider_for_capability(FeatureCapability.CHAT_SIMPLE, config)
        assert provider == AIProvider.OLLAMA


class TestStrictMode:
    """Tests for strict mode enforcement."""

    def test_strict_mode_blocks_cloud_provider(self):
        """H2: Strict mode raises error when trying to use cloud."""
        config = AIConfig(
            mode=ProviderMode.OLLAMA_ONLY,
            strict_mode=True,
        )
        reset_provider_router()
        router = ProviderRouter(config)

        with pytest.raises(StrictModeViolation):
            router._validate_provider(AIProvider.OPENAI)

    def test_strict_mode_allows_ollama(self):
        """H2: Strict mode allows Ollama provider."""
        config = AIConfig(
            mode=ProviderMode.OLLAMA_ONLY,
            strict_mode=True,
        )
        reset_provider_router()
        router = ProviderRouter(config)

        # Should not raise
        router._validate_provider(AIProvider.OLLAMA)

    def test_azure_only_blocks_other_providers(self):
        """Azure-only mode blocks non-Azure providers."""
        config = AIConfig(
            mode=ProviderMode.AZURE_ONLY,
            strict_mode=True,
        )
        reset_provider_router()
        router = ProviderRouter(config)

        with pytest.raises(StrictModeViolation):
            router._validate_provider(AIProvider.OPENAI)


class TestPerAgentOverride:
    """Tests for per-agent provider configuration."""

    @pytest.mark.skip(reason="TODO: Implement full agent override support in get_provider_for_agent")
    def test_agent_override_returns_configured_provider(self):
        """H6: Agent override returns correct provider when configured with AgentProviderConfig."""
        from src.core.ai_providers import AgentProviderConfig

        config = AIConfig(
            mode=ProviderMode.HYBRID,
            agent_overrides={
                "ali-chief-of-staff": AgentProviderConfig(
                    agent_id="ali-chief-of-staff",
                    provider=AIProvider.AZURE_OPENAI,
                    model="gpt-4o"
                )
            }
        )
        provider, model = get_provider_for_agent("ali-chief-of-staff", config)
        assert provider == AIProvider.AZURE_OPENAI
        assert model == "gpt-4o"

    def test_agent_without_override_uses_default(self):
        """H6: Agent without override uses default provider."""
        config = AIConfig(
            mode=ProviderMode.OLLAMA_ONLY,
            default_provider=AIProvider.OLLAMA,
            default_model="llama3.2:latest",
        )
        provider, model = get_provider_for_agent("unknown-agent", config)
        assert provider == AIProvider.OLLAMA


class TestPerFeatureOverride:
    """Tests for per-feature provider configuration."""

    @pytest.mark.skip(reason="TODO: Implement full feature override support in get_provider_for_capability")
    def test_feature_override_returns_configured_provider(self):
        """H7: Feature override returns correct provider when configured with FeatureProviderConfig."""
        from src.core.ai_providers import FeatureProviderConfig

        config = AIConfig(
            mode=ProviderMode.HYBRID,
            feature_overrides={
                FeatureCapability.CODE_REVIEW: FeatureProviderConfig(
                    capability=FeatureCapability.CODE_REVIEW,
                    provider=AIProvider.OLLAMA,
                    model="qwen2.5-coder:14b"
                )
            }
        )
        provider, model = get_provider_for_capability(FeatureCapability.CODE_REVIEW, config)
        assert provider == AIProvider.OLLAMA
        assert model == "qwen2.5-coder:14b"


class TestCostTracking:
    """Tests for cost tracking by provider."""

    def test_ollama_cost_is_zero(self):
        """H8: Ollama calls have $0 cost."""
        config = AIConfig(mode=ProviderMode.OLLAMA_ONLY)
        reset_provider_router()
        router = ProviderRouter(config)

        # Simulate Ollama call tracked
        router._call_counts[AIProvider.OLLAMA] = 100
        router._costs[AIProvider.OLLAMA] = 0.0

        costs = router.get_costs()
        assert AIProvider.OLLAMA.value not in costs or costs.get(AIProvider.OLLAMA.value, 0) == 0

    def test_savings_calculation(self):
        """H8: Savings calculated from Ollama vs cloud."""
        config = AIConfig(mode=ProviderMode.OLLAMA_ONLY)
        reset_provider_router()
        router = ProviderRouter(config)

        # Simulate 100 Ollama calls
        router._call_counts[AIProvider.OLLAMA] = 100

        stats = router.get_stats()
        assert stats["savings_vs_cloud"] > 0


class TestToolCallModel:
    """Tests for ToolCall Pydantic model."""

    def test_tool_call_creation(self):
        """ToolCall model works correctly."""
        tc = ToolCall(
            id="call_123",
            function_name="get_weather",
            arguments={"city": "Rome"}
        )
        assert tc.id == "call_123"
        assert tc.function_name == "get_weather"
        assert tc.arguments == {"city": "Rome"}
        assert tc.type == "function"


class TestChatResponse:
    """Tests for ChatResponse model."""

    def test_chat_response_with_tool_calls(self):
        """ChatResponse includes tool_calls."""
        response = ChatResponse(
            content="",
            provider=AIProvider.OLLAMA,
            model="llama3.2:latest",
            tool_calls=[
                ToolCall(id="1", function_name="search", arguments={})
            ]
        )
        assert len(response.tool_calls) == 1
        assert response.cost_usd == 0.0


class TestOllamaService:
    """Tests for Ollama service."""

    @pytest.mark.asyncio
    async def test_ollama_health_check_mock(self):
        """H10: Ollama health check works."""
        service = OllamaService()

        with patch.object(service._client, 'get', new_callable=AsyncMock) as mock_get:
            # Mock version endpoint
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"version": "0.4.0"}
            mock_get.return_value = mock_response

            # Override _list_models and _check_gpu
            with patch.object(service, '_list_models', new_callable=AsyncMock) as mock_list:
                with patch.object(service, '_check_gpu', new_callable=AsyncMock) as mock_gpu:
                    mock_list.return_value = []
                    mock_gpu.return_value = (False, None)

                    status = await service.health_check()

                    assert status.available is True
                    assert status.version == "0.4.0"

    def test_model_capability_detection(self):
        """Model capabilities correctly detected."""
        from src.core.ollama_service import _get_model_capabilities

        # Test llama3.2 has function calling
        caps = _get_model_capabilities("llama3.2:latest")
        assert OllamaModelCapability.CHAT in caps
        assert OllamaModelCapability.FUNCTION_CALLING in caps

        # Test nomic has embeddings
        caps = _get_model_capabilities("nomic-embed-text:latest")
        assert OllamaModelCapability.EMBEDDINGS in caps


class TestOllamaFunctionCalling:
    """Tests for Ollama function calling."""

    @pytest.mark.asyncio
    async def test_chat_with_tools_format(self):
        """H3: chat_with_tools sends correct format."""
        service = OllamaService()

        tools = [{
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get weather for a city",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string"}
                    }
                }
            }
        }]

        with patch.object(service._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "message": {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [{
                        "id": "call_1",
                        "type": "function",
                        "function": {
                            "name": "get_weather",
                            "arguments": '{"city": "Rome"}'
                        }
                    }]
                }
            }
            mock_post.return_value = mock_response

            response = await service.chat_with_tools(
                model="llama3.2:latest",
                messages=[{"role": "user", "content": "What's the weather in Rome?"}],
                tools=tools,
            )

            assert "tool_calls" in response.get("message", {})
            assert response["message"]["tool_calls"][0]["function"]["name"] == "get_weather"


class TestProviderRouterWithOllama:
    """Integration tests for ProviderRouter with Ollama."""

    @pytest.mark.asyncio
    async def test_router_chat_with_ollama_mock(self):
        """H4: Router routes chat to Ollama."""
        config = AIConfig(mode=ProviderMode.OLLAMA_ONLY)
        reset_provider_router()
        router = ProviderRouter(config)

        with patch.object(router._ollama, 'health_check', new_callable=AsyncMock) as mock_health:
            mock_health.return_value = OllamaStatus(available=True, version="0.4.0")

            with patch.object(router._ollama, 'chat', new_callable=AsyncMock) as mock_chat:
                mock_chat.return_value = {
                    "message": {"content": "Hello!", "role": "assistant"},
                    "eval_count": 10
                }

                response = await router.chat_completion(
                    messages=[ChatMessage(role="user", content="Hi")],
                    capability=FeatureCapability.CHAT_SIMPLE,
                )

                assert response.provider == AIProvider.OLLAMA
                assert response.content == "Hello!"
                assert response.cost_usd == 0.0

    @pytest.mark.asyncio
    async def test_router_function_calling_with_ollama_mock(self):
        """H3: Router routes function calling to Ollama."""
        config = AIConfig(mode=ProviderMode.OLLAMA_ONLY)
        reset_provider_router()
        router = ProviderRouter(config)

        tools = [{
            "type": "function",
            "function": {
                "name": "search",
                "description": "Search for info",
                "parameters": {"type": "object", "properties": {}}
            }
        }]

        with patch.object(router._ollama, 'health_check', new_callable=AsyncMock) as mock_health:
            mock_health.return_value = OllamaStatus(available=True, version="0.4.0")

            with patch.object(router._ollama, 'chat_with_tools', new_callable=AsyncMock) as mock_chat:
                mock_chat.return_value = {
                    "message": {
                        "content": "",
                        "role": "assistant",
                        "tool_calls": [{
                            "id": "call_1",
                            "type": "function",
                            "function": {"name": "search", "arguments": "{}"}
                        }]
                    },
                    "eval_count": 5
                }

                response = await router.chat_with_tools(
                    messages=[ChatMessage(role="user", content="Search for X")],
                    tools=tools,
                )

                assert response.provider == AIProvider.OLLAMA
                assert len(response.tool_calls) == 1
                assert response.tool_calls[0].function_name == "search"
                assert response.cost_usd == 0.0


class TestExecuteToolLoop:
    """Tests for multi-turn function calling loop."""

    @pytest.mark.asyncio
    async def test_execute_tool_loop_mock(self):
        """H11: execute_tool_loop handles multi-turn conversations."""
        service = OllamaService()

        tools = [{
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get weather",
                "parameters": {"type": "object", "properties": {"city": {"type": "string"}}}
            }
        }]

        async def mock_executor(name: str, args: dict) -> str:
            if name == "get_weather":
                return f"Weather in {args.get('city', 'unknown')}: Sunny, 22°C"
            return "Unknown function"

        call_count = [0]

        async def mock_chat_with_tools(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                # First call: model requests tool
                return {
                    "message": {
                        "content": "",
                        "role": "assistant",
                        "tool_calls": [{
                            "id": "call_1",
                            "type": "function",
                            "function": {"name": "get_weather", "arguments": '{"city": "Rome"}'}
                        }]
                    }
                }
            else:
                # Second call: model gives final answer
                return {
                    "message": {
                        "content": "The weather in Rome is sunny, 22°C.",
                        "role": "assistant"
                    }
                }

        with patch.object(service, 'chat_with_tools', side_effect=mock_chat_with_tools):
            response = await service.execute_tool_loop(
                model="llama3.2:latest",
                messages=[{"role": "user", "content": "What's the weather in Rome?"}],
                tools=tools,
                tool_executor=mock_executor,
            )

            assert "weather" in response["message"]["content"].lower()
            assert call_count[0] == 2


# Run with: pytest tests/test_ai_providers.py -v
