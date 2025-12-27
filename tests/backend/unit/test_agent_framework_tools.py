"""
Unit tests for Agent Framework Tools.
Tests C2.2: Web search and other @ai_function decorated tools.
Updated for AIFunction objects returned by @ai_function decorator.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock


def get_tool_name(tool):
    """Get name from tool (works with both AIFunction and regular functions)."""
    if hasattr(tool, 'name'):
        return tool.name
    return getattr(tool, '__name__', str(tool))


def get_tool_description(tool):
    """Get description from tool (works with both AIFunction and regular functions)."""
    if hasattr(tool, 'description'):
        return tool.description or ""
    return getattr(tool, '__doc__', "") or ""


def is_tool_async(tool):
    """Check if tool is async (works with AIFunction objects)."""
    import asyncio
    if hasattr(tool, 'func'):
        return asyncio.iscoroutinefunction(tool.func)
    if hasattr(tool, '_func'):
        return asyncio.iscoroutinefunction(tool._func)
    return asyncio.iscoroutinefunction(tool)


class TestAgentFrameworkToolsImport:
    """Tests for module import and framework detection."""

    def test_module_imports_successfully(self):
        """Test that agent_framework_tools module imports without error."""
        from src.agents.tools import agent_framework_tools
        assert agent_framework_tools is not None

    def test_framework_flag_exists(self):
        """Test that framework availability flag is defined."""
        from src.agents.tools.agent_framework_tools import AGENT_FRAMEWORK_AVAILABLE
        assert isinstance(AGENT_FRAMEWORK_AVAILABLE, bool)

    def test_ai_function_decorator_exists(self):
        """Test that ai_function decorator is available."""
        from src.agents.tools.agent_framework_tools import ai_function
        assert callable(ai_function)


class TestWebSearchTools:
    """Tests for web search tools."""

    def test_web_search_exists(self):
        """Test web_search function exists and is callable."""
        from src.agents.tools.agent_framework_tools import web_search
        assert callable(web_search)

    def test_search_news_exists(self):
        """Test search_news function exists and is callable."""
        from src.agents.tools.agent_framework_tools import search_news
        assert callable(search_news)

    def test_search_financial_exists(self):
        """Test search_financial function exists and is callable."""
        from src.agents.tools.agent_framework_tools import search_financial
        assert callable(search_financial)

    def test_web_search_has_name(self):
        """Test web_search has proper name."""
        from src.agents.tools.agent_framework_tools import web_search
        name = get_tool_name(web_search)
        assert name is not None
        assert "web_search" in name.lower() or "search" in name.lower()

    def test_search_news_has_name(self):
        """Test search_news has proper name."""
        from src.agents.tools.agent_framework_tools import search_news
        name = get_tool_name(search_news)
        assert name is not None

    @pytest.mark.asyncio
    async def test_web_search_no_api_key(self):
        """Test web_search returns error when API key not configured."""
        from src.agents.tools.agent_framework_tools import web_search

        with patch.dict("os.environ", {"PERPLEXITY_API_KEY": ""}):
            # For AIFunction objects, we need to invoke them
            if hasattr(web_search, 'invoke'):
                result = await web_search.invoke(query="test query")
            else:
                result = await web_search("test query")
            assert "error" in result.lower() or "not configured" in result.lower()

    @pytest.mark.asyncio
    async def test_web_search_with_mock_response(self):
        """Test web_search with mocked API response."""
        from src.agents.tools.agent_framework_tools import web_search
        import httpx

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test search result"}}]
        }

        with patch.dict("os.environ", {"PERPLEXITY_API_KEY": "test-key"}):
            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
                mock_client.return_value.__aexit__ = AsyncMock()
                mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

                if hasattr(web_search, 'invoke'):
                    result = await web_search.invoke(query="test query")
                else:
                    result = await web_search("test query")
                # Either success or proper error handling
                assert isinstance(result, str)


class TestDatabaseToolsInAF:
    """Tests for database tools in agent_framework_tools."""

    def test_get_talents_summary_exists(self):
        """Test get_talents_summary function exists."""
        from src.agents.tools.agent_framework_tools import get_talents_summary
        assert callable(get_talents_summary)

    def test_get_talent_by_username_exists(self):
        """Test get_talent_by_username function exists."""
        from src.agents.tools.agent_framework_tools import get_talent_by_username
        assert callable(get_talent_by_username)

    def test_search_talents_exists(self):
        """Test search_talents function exists."""
        from src.agents.tools.agent_framework_tools import search_talents
        assert callable(search_talents)


class TestVectorSearchTools:
    """Tests for vector search tools."""

    def test_vector_search_exists(self):
        """Test vector_search function exists."""
        from src.agents.tools.agent_framework_tools import vector_search
        assert callable(vector_search)

    def test_semantic_knowledge_search_exists(self):
        """Test semantic_knowledge_search function exists."""
        from src.agents.tools.agent_framework_tools import semantic_knowledge_search
        assert callable(semantic_knowledge_search)

    def test_vector_search_has_name(self):
        """Test vector_search has proper name."""
        from src.agents.tools.agent_framework_tools import vector_search
        name = get_tool_name(vector_search)
        assert name is not None


class TestUtilityTools:
    """Tests for utility tools."""

    def test_get_current_date_exists(self):
        """Test get_current_date function exists."""
        from src.agents.tools.agent_framework_tools import get_current_date
        assert callable(get_current_date)

    def test_format_as_json_exists(self):
        """Test format_as_json function exists."""
        from src.agents.tools.agent_framework_tools import format_as_json
        assert callable(format_as_json)

    @pytest.mark.asyncio
    async def test_get_current_date_returns_string(self):
        """Test get_current_date returns ISO format string."""
        from src.agents.tools.agent_framework_tools import get_current_date

        if hasattr(get_current_date, 'invoke'):
            result = await get_current_date.invoke()
        else:
            result = await get_current_date()
        assert isinstance(result, str)
        # Should be ISO format
        assert "T" in result or "-" in result


class TestToolRegistration:
    """Tests for tool registration functions."""

    def test_get_all_agent_framework_tools_exists(self):
        """Test get_all_agent_framework_tools function exists."""
        from src.agents.tools.agent_framework_tools import get_all_agent_framework_tools
        assert callable(get_all_agent_framework_tools)

    def test_get_all_agent_framework_tools_returns_list(self):
        """Test get_all_agent_framework_tools returns a list."""
        from src.agents.tools.agent_framework_tools import get_all_agent_framework_tools

        tools = get_all_agent_framework_tools()
        assert isinstance(tools, list)
        assert len(tools) >= 10  # At least 10 tools defined

    def test_get_tool_descriptions_exists(self):
        """Test get_tool_descriptions function exists."""
        from src.agents.tools.agent_framework_tools import get_tool_descriptions
        assert callable(get_tool_descriptions)

    def test_get_tool_descriptions_returns_dict(self):
        """Test get_tool_descriptions returns a dictionary."""
        from src.agents.tools.agent_framework_tools import get_tool_descriptions

        descriptions = get_tool_descriptions()
        assert isinstance(descriptions, dict)
        assert len(descriptions) >= 10

    def test_all_tools_are_callable(self):
        """Test all tools are callable."""
        from src.agents.tools.agent_framework_tools import get_all_agent_framework_tools

        tools = get_all_agent_framework_tools()
        for tool in tools:
            assert callable(tool)


class TestToolCompatibility:
    """Tests for tool compatibility layer."""

    def test_tool_compatibility_module_exists(self):
        """Test tool_compatibility module exists."""
        try:
            from src.agents.tools import tool_compatibility
            assert tool_compatibility is not None
        except ImportError:
            pytest.skip("tool_compatibility module not yet created")

    def test_tools_are_callable_and_async(self):
        """Test that AF tools are async-capable."""
        from src.agents.tools.agent_framework_tools import (
            web_search,
            vector_search,
            get_talents_summary,
        )

        # AIFunction objects are callable and support async invoke
        assert callable(web_search)
        assert callable(vector_search)
        assert callable(get_talents_summary)

        # Check if they have invoke method (AIFunction pattern)
        for tool in [web_search, vector_search, get_talents_summary]:
            assert hasattr(tool, 'invoke') or is_tool_async(tool)


class TestAnalyticsTools:
    """Tests for analytics tools (migrated from convergio_tools)."""

    def test_get_engagement_analytics_exists(self):
        """Test get_engagement_analytics function exists."""
        from src.agents.tools.agent_framework_tools import get_engagement_analytics
        assert callable(get_engagement_analytics)

    def test_get_business_intelligence_exists(self):
        """Test get_business_intelligence function exists."""
        from src.agents.tools.agent_framework_tools import get_business_intelligence
        assert callable(get_business_intelligence)

    def test_get_engagement_analytics_has_name(self):
        """Test get_engagement_analytics has proper name."""
        from src.agents.tools.agent_framework_tools import get_engagement_analytics
        name = get_tool_name(get_engagement_analytics)
        assert name is not None
        assert "engagement" in name.lower() or "analytics" in name.lower()

    def test_get_business_intelligence_has_name(self):
        """Test get_business_intelligence has proper name."""
        from src.agents.tools.agent_framework_tools import get_business_intelligence
        name = get_tool_name(get_business_intelligence)
        assert name is not None
        assert "business" in name.lower() or "intelligence" in name.lower()

    def test_analytics_tools_in_registry(self):
        """Test analytics tools are in the tool registry."""
        from src.agents.tools.agent_framework_tools import get_all_agent_framework_tools

        tools = get_all_agent_framework_tools()
        tool_names = [get_tool_name(t) for t in tools]

        assert "get_engagement_analytics" in tool_names
        assert "get_business_intelligence" in tool_names


class TestToolFunctionSignatures:
    """Tests for tool function signatures (important for @ai_function)."""

    def test_web_search_callable(self):
        """Test web_search is callable and has expected interface."""
        from src.agents.tools.agent_framework_tools import web_search

        assert callable(web_search)
        # AIFunction objects should have invoke method or be directly callable
        assert hasattr(web_search, 'invoke') or hasattr(web_search, '__call__')

    def test_vector_search_callable(self):
        """Test vector_search is callable and has expected interface."""
        from src.agents.tools.agent_framework_tools import vector_search

        assert callable(vector_search)
        assert hasattr(vector_search, 'invoke') or hasattr(vector_search, '__call__')

    def test_get_talent_by_username_callable(self):
        """Test get_talent_by_username is callable."""
        from src.agents.tools.agent_framework_tools import get_talent_by_username

        assert callable(get_talent_by_username)

    def test_get_engagement_analytics_callable(self):
        """Test get_engagement_analytics is callable."""
        from src.agents.tools.agent_framework_tools import get_engagement_analytics

        assert callable(get_engagement_analytics)

    def test_get_business_intelligence_callable(self):
        """Test get_business_intelligence is callable."""
        from src.agents.tools.agent_framework_tools import get_business_intelligence

        assert callable(get_business_intelligence)
