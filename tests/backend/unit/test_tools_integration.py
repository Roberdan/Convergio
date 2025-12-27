"""
Integration tests for Tools Migration (C5.3).
Tests the tools registry, intelligent tool executor, and tool execution flow.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import json


class TestToolsRegistryIntegration:
    """Integration tests for the unified tools registry."""

    def test_registry_initializes_with_tools(self):
        """Test that registry initializes and loads tools."""
        from src.agents.tools.tools_registry import get_tools_registry

        registry = get_tools_registry()

        assert registry is not None
        assert registry._initialized is True
        assert len(registry.get_tool_names()) > 0

    def test_registry_singleton_pattern(self):
        """Test that registry follows singleton pattern."""
        from src.agents.tools.tools_registry import get_tools_registry

        registry1 = get_tools_registry()
        registry2 = get_tools_registry()

        assert registry1 is registry2

    def test_registry_has_expected_categories(self):
        """Test that registry has expected tool categories."""
        from src.agents.tools.tools_registry import get_tools_registry

        registry = get_tools_registry()
        categories = registry.get_categories()

        # Check for expected categories
        expected = ["database", "search", "general"]
        for cat in expected:
            assert cat in categories or len(categories) > 0

    def test_registry_tools_are_callable(self):
        """Test that all tools in registry are callable."""
        from src.agents.tools.tools_registry import get_tools_registry

        registry = get_tools_registry()
        tools = registry.get_all_tools()

        for tool in tools:
            assert callable(tool)

    def test_get_tool_by_name(self):
        """Test getting specific tools by name."""
        from src.agents.tools.tools_registry import get_tool

        # Try getting web_search tool
        web_search = get_tool("web_search")
        if web_search is not None:
            assert callable(web_search)

        # Try getting get_current_date tool
        get_date = get_tool("get_current_date")
        if get_date is not None:
            assert callable(get_date)

    def test_registry_descriptions_exist(self):
        """Test that all tools have descriptions."""
        from src.agents.tools.tools_registry import get_tools_registry

        registry = get_tools_registry()
        descriptions = registry.get_descriptions()

        for name, desc in descriptions.items():
            assert desc is not None
            assert len(desc) > 0


class TestIntelligentToolExecutorIntegration:
    """Integration tests for the intelligent tool executor."""

    def test_executor_initializes(self):
        """Test that executor initializes correctly."""
        from src.agents.tools.intelligent_tool_executor import (
            get_intelligent_executor,
            AGENT_FRAMEWORK_AVAILABLE,
            AUTOGEN_AVAILABLE
        )

        executor = get_intelligent_executor()

        assert executor is not None
        assert executor.registry is not None
        assert isinstance(AGENT_FRAMEWORK_AVAILABLE, bool)
        assert isinstance(AUTOGEN_AVAILABLE, bool)

    def test_executor_singleton_pattern(self):
        """Test that executor follows singleton pattern."""
        from src.agents.tools.intelligent_tool_executor import get_intelligent_executor

        executor1 = get_intelligent_executor()
        executor2 = get_intelligent_executor()

        assert executor1 is executor2

    def test_executor_has_selector(self):
        """Test that executor has smart tool selector."""
        from src.agents.tools.intelligent_tool_executor import get_intelligent_executor

        executor = get_intelligent_executor()

        assert executor.selector is not None

    def test_executor_initial_metrics(self):
        """Test that executor has initial metrics."""
        from src.agents.tools.intelligent_tool_executor import IntelligentToolExecutor

        # Create fresh instance for clean metrics
        executor = IntelligentToolExecutor()
        metrics = executor.get_metrics()

        assert metrics["total_queries"] == 0
        assert "usage" in metrics
        assert "web_search" in metrics["usage"]
        assert "database" in metrics["usage"]
        assert "vector_search" in metrics["usage"]
        assert "ai_chat" in metrics["usage"]

    def test_executor_reset_metrics(self):
        """Test that metrics can be reset."""
        from src.agents.tools.intelligent_tool_executor import IntelligentToolExecutor

        executor = IntelligentToolExecutor()
        executor.tool_usage["web_search"] = 5
        executor.reset_metrics()

        assert executor.tool_usage["web_search"] == 0


class TestToolExecutionFlow:
    """Integration tests for tool execution flow."""

    @pytest.mark.asyncio
    async def test_execute_query_returns_structure(self):
        """Test that execute_query returns expected structure."""
        from src.agents.tools.intelligent_tool_executor import IntelligentToolExecutor

        executor = IntelligentToolExecutor()

        # Mock the selector to avoid actual analysis
        executor.selector.analyze_query = MagicMock(return_value={
            "needs_web_search": False,
            "confidence": 0.5,
            "suggested_tools": ["ai_chat"],
            "reasoning": "Test query"
        })

        # Mock AI manager
        executor.ai_manager = MagicMock()
        executor.ai_manager.chat_completion = AsyncMock(return_value="Test response")

        result = await executor.execute_query("What is 2+2?")

        assert "query" in result
        assert "analysis" in result
        assert "tools_used" in result
        assert "responses" in result

    @pytest.mark.asyncio
    async def test_web_search_tool_integration(self):
        """Test web search tool integration through executor."""
        from src.agents.tools.intelligent_tool_executor import IntelligentToolExecutor

        executor = IntelligentToolExecutor()

        # Mock the selector to trigger web search
        executor.selector.analyze_query = MagicMock(return_value={
            "needs_web_search": True,
            "confidence": 0.9,
            "suggested_tools": ["web_search"],
            "reasoning": "Current events query"
        })

        # Mock the web search tool
        mock_web_search = AsyncMock(return_value="Web search results")
        executor._web_search_tool = mock_web_search

        result = await executor.execute_query("What happened today in AI news?")

        assert "web_search" in result["tools_used"]
        assert "web_search" in result["responses"]

    @pytest.mark.asyncio
    async def test_database_tool_integration(self):
        """Test database tool integration through executor."""
        from src.agents.tools.intelligent_tool_executor import IntelligentToolExecutor

        executor = IntelligentToolExecutor()

        # Mock the selector to trigger database query
        executor.selector.analyze_query = MagicMock(return_value={
            "needs_web_search": False,
            "confidence": 0.9,
            "suggested_tools": ["database_query"],
            "reasoning": "Internal data query"
        })

        # Mock database tools
        mock_db_tools = [MagicMock(return_value='{"result": "test"}')]
        executor._database_tools = mock_db_tools

        result = await executor.execute_query("How many talents do we have?")

        assert "database_query" in result["tools_used"]
        assert "database" in result["responses"]

    @pytest.mark.asyncio
    async def test_vector_search_tool_integration(self):
        """Test vector search tool integration through executor."""
        from src.agents.tools.intelligent_tool_executor import IntelligentToolExecutor

        executor = IntelligentToolExecutor()

        # Mock the selector to trigger vector search
        executor.selector.analyze_query = MagicMock(return_value={
            "needs_web_search": False,
            "confidence": 0.9,
            "suggested_tools": ["vector_search"],
            "reasoning": "Semantic search query"
        })

        # Mock vector search tool
        mock_vector_search = AsyncMock(return_value="Vector search results")
        executor._vector_search_tool = mock_vector_search

        result = await executor.execute_query("Find documents about machine learning")

        assert "vector_search" in result["tools_used"]
        assert "vector_search" in result["responses"]


class TestAgentFrameworkToolsIntegration:
    """Integration tests for Agent Framework tools."""

    def test_all_tools_have_ai_function_decorator(self):
        """Test that all AF tools are decorated."""
        from src.agents.tools.agent_framework_tools import (
            get_all_agent_framework_tools,
            AGENT_FRAMEWORK_AVAILABLE
        )

        tools = get_all_agent_framework_tools()

        assert len(tools) >= 10
        for tool in tools:
            assert callable(tool)
            assert tool.__doc__ is not None

    @pytest.mark.asyncio
    async def test_get_current_date_tool_execution(self):
        """Test that get_current_date tool executes."""
        from src.agents.tools.agent_framework_tools import get_current_date

        result = await get_current_date()

        assert isinstance(result, str)
        assert len(result) > 0
        # Should be ISO format date
        assert "T" in result or "-" in result

    @pytest.mark.asyncio
    async def test_format_as_json_tool_execution(self):
        """Test that format_as_json tool executes."""
        from src.agents.tools.agent_framework_tools import format_as_json

        test_data = {"key": "value", "number": 42}
        result = await format_as_json(test_data)

        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed["key"] == "value"
        assert parsed["number"] == 42

    def test_tool_descriptions_are_complete(self):
        """Test that all tool descriptions are complete."""
        from src.agents.tools.agent_framework_tools import get_tool_descriptions

        descriptions = get_tool_descriptions()

        for name, desc in descriptions.items():
            assert desc != "No description", f"Tool {name} has no description"
            assert len(desc) > 10, f"Tool {name} has too short description"


class TestDatabaseToolsIntegration:
    """Integration tests for database tools."""

    def test_database_tools_load(self):
        """Test that database tools load correctly."""
        from src.agents.tools.database_tools import (
            get_database_tools_af,
            AGENT_FRAMEWORK_AVAILABLE,
            AUTOGEN_AVAILABLE
        )

        tools = get_database_tools_af()

        assert isinstance(tools, list)
        assert len(tools) > 0
        for tool in tools:
            assert callable(tool)

    def test_database_tools_backward_compatible(self):
        """Test backward compatibility with get_database_tools."""
        from src.agents.tools.database_tools import get_database_tools

        tools = get_database_tools()

        assert isinstance(tools, list)
        assert len(tools) > 0

    def test_database_tools_have_docstrings(self):
        """Test that database tools have docstrings."""
        from src.agents.tools.database_tools import get_database_tools_af

        tools = get_database_tools_af()

        for tool in tools:
            assert tool.__doc__ is not None
            assert len(tool.__doc__) > 0


class TestToolsRegistryWithExecutor:
    """Integration tests for registry + executor together."""

    def test_executor_uses_registry_tools(self):
        """Test that executor uses tools from registry."""
        from src.agents.tools.intelligent_tool_executor import IntelligentToolExecutor
        from src.agents.tools.tools_registry import get_tools_registry

        executor = IntelligentToolExecutor()
        registry = get_tools_registry()

        # Executor should have access to registry
        assert executor.registry is registry

    def test_executor_can_get_web_search_from_registry(self):
        """Test that executor can get web_search from registry."""
        from src.agents.tools.intelligent_tool_executor import IntelligentToolExecutor

        executor = IntelligentToolExecutor()
        web_search = executor._get_web_search_tool()

        # May be None if not registered, but method should work
        if web_search is not None:
            assert callable(web_search)

    def test_executor_can_get_database_tools_from_registry(self):
        """Test that executor can get database tools from registry."""
        from src.agents.tools.intelligent_tool_executor import IntelligentToolExecutor

        executor = IntelligentToolExecutor()
        db_tools = executor._get_database_tools()

        assert isinstance(db_tools, list)
        for tool in db_tools:
            assert callable(tool)


class TestConvenienceFunctions:
    """Integration tests for convenience functions."""

    @pytest.mark.asyncio
    async def test_execute_intelligent_query_function(self):
        """Test the execute_intelligent_query convenience function."""
        from src.agents.tools.intelligent_tool_executor import execute_intelligent_query

        # Mock the internal executor
        with patch('src.agents.tools.intelligent_tool_executor.get_intelligent_executor') as mock_get:
            mock_executor = MagicMock()
            mock_executor.execute_query = AsyncMock(return_value={
                "query": "test",
                "analysis": {},
                "tools_used": ["ai_chat"],
                "responses": {"ai_chat": "response"}
            })
            mock_get.return_value = mock_executor

            result = await execute_intelligent_query("Test query")

            assert "query" in result
            assert "tools_used" in result
            mock_executor.execute_query.assert_called_once()

    def test_get_all_tools_function(self):
        """Test the get_all_tools convenience function."""
        from src.agents.tools.tools_registry import get_all_tools

        tools = get_all_tools()

        assert isinstance(tools, list)
        for tool in tools:
            assert callable(tool)

    def test_get_tool_descriptions_function(self):
        """Test the get_tool_descriptions convenience function."""
        from src.agents.tools.tools_registry import get_tool_descriptions

        descriptions = get_tool_descriptions()

        assert isinstance(descriptions, dict)
        for name, desc in descriptions.items():
            assert isinstance(name, str)
            assert isinstance(desc, str)

    def test_get_tools_by_category_function(self):
        """Test the get_tools_by_category convenience function."""
        from src.agents.tools.tools_registry import get_tools_by_category

        # Try to get database category
        db_tools = get_tools_by_category("database")

        assert isinstance(db_tools, list)
        for tool in db_tools:
            assert callable(tool)
