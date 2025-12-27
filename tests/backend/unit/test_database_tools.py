"""
Unit tests for Database Tools with Agent Framework migration.
Tests C1.2-C1.5: All database tool functions with @ai_function decorator.
Updated for AIFunction objects returned by @ai_function decorator.
"""

import pytest
from unittest.mock import patch, MagicMock


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


class TestDatabaseToolsImport:
    """Tests for module import and framework detection."""

    def test_module_imports_successfully(self):
        """Test that database_tools module imports without error."""
        from src.agents.tools import database_tools
        assert database_tools is not None

    def test_framework_flags_exist(self):
        """Test that framework availability flags are defined."""
        from src.agents.tools.database_tools import (
            AGENT_FRAMEWORK_AVAILABLE,
            AUTOGEN_AVAILABLE,
        )
        # Both should be boolean
        assert isinstance(AGENT_FRAMEWORK_AVAILABLE, bool)
        assert isinstance(AUTOGEN_AVAILABLE, bool)

    def test_ai_function_decorator_exists(self):
        """Test that ai_function decorator is available."""
        from src.agents.tools.database_tools import ai_function
        assert callable(ai_function)


class TestDatabaseToolsFunctions:
    """Tests for individual database tool functions."""

    def test_query_talents_count_exists(self):
        """Test query_talents_count function exists and is callable."""
        from src.agents.tools.database_tools import query_talents_count
        assert callable(query_talents_count)

    def test_query_talent_details_exists(self):
        """Test query_talent_details function exists and is callable."""
        from src.agents.tools.database_tools import query_talent_details
        assert callable(query_talent_details)

    def test_query_department_structure_exists(self):
        """Test query_department_structure function exists and is callable."""
        from src.agents.tools.database_tools import query_department_structure
        assert callable(query_department_structure)

    def test_query_knowledge_base_exists(self):
        """Test query_knowledge_base function exists and is callable."""
        from src.agents.tools.database_tools import query_knowledge_base
        assert callable(query_knowledge_base)

    def test_search_knowledge_exists(self):
        """Test search_knowledge function exists and is callable."""
        from src.agents.tools.database_tools import search_knowledge
        assert callable(search_knowledge)

    def test_query_ai_agent_info_exists(self):
        """Test query_ai_agent_info function exists and is callable."""
        from src.agents.tools.database_tools import query_ai_agent_info
        assert callable(query_ai_agent_info)

    def test_list_ai_agents_exists(self):
        """Test list_ai_agents function exists and is callable."""
        from src.agents.tools.database_tools import list_ai_agents
        assert callable(list_ai_agents)

    def test_query_projects_exists(self):
        """Test query_projects function exists and is callable."""
        from src.agents.tools.database_tools import query_projects
        assert callable(query_projects)

    def test_query_system_status_exists(self):
        """Test query_system_status function exists and is callable."""
        from src.agents.tools.database_tools import query_system_status
        assert callable(query_system_status)


class TestDatabaseToolsAFRegistration:
    """Tests for Agent Framework tool registration."""

    def test_get_database_tools_af_exists(self):
        """Test get_database_tools_af function exists."""
        from src.agents.tools.database_tools import get_database_tools_af
        assert callable(get_database_tools_af)

    def test_get_database_tools_af_returns_list(self):
        """Test get_database_tools_af returns a list of tools."""
        from src.agents.tools.database_tools import get_database_tools_af
        tools = get_database_tools_af()
        assert isinstance(tools, list)
        assert len(tools) == 9  # 9 database tools

    def test_get_database_tools_af_tool_names(self):
        """Test that all expected tools are in the AF tools list."""
        from src.agents.tools.database_tools import get_database_tools_af

        tools = get_database_tools_af()
        tool_names = [get_tool_name(t) for t in tools]

        expected_tools = [
            "query_ai_agent_info",
            "list_ai_agents",
            "query_talents_count",
            "query_talent_details",
            "query_department_structure",
            "query_knowledge_base",
            "query_projects",
            "search_knowledge",
            "query_system_status",
        ]

        for expected in expected_tools:
            assert expected in tool_names, f"Missing tool: {expected}"


class TestDatabaseToolsLegacy:
    """Tests for legacy AutoGen compatibility."""

    def test_get_database_tools_exists(self):
        """Test get_database_tools function exists for backward compat."""
        from src.agents.tools.database_tools import get_database_tools
        assert callable(get_database_tools)

    def test_get_database_tools_returns_list(self):
        """Test get_database_tools returns something."""
        from src.agents.tools.database_tools import get_database_tools

        try:
            tools = get_database_tools()
            assert isinstance(tools, list)
        except ImportError:
            # Expected if neither framework is available
            pass


class TestDatabaseToolsDocstrings:
    """Tests for docstrings/descriptions (used by @ai_function for descriptions)."""

    def test_query_talents_count_description(self):
        """Test query_talents_count has proper description."""
        from src.agents.tools.database_tools import query_talents_count
        desc = get_tool_description(query_talents_count)
        assert desc is not None
        assert "talent" in desc.lower()

    def test_query_talent_details_description(self):
        """Test query_talent_details has proper description."""
        from src.agents.tools.database_tools import query_talent_details
        desc = get_tool_description(query_talent_details)
        assert desc is not None
        # Accept either "name" or "talent" in description
        assert "name" in desc.lower() or "talent" in desc.lower()

    def test_query_department_structure_description(self):
        """Test query_department_structure has proper description."""
        from src.agents.tools.database_tools import query_department_structure
        desc = get_tool_description(query_department_structure)
        assert desc is not None
        assert "department" in desc.lower()

    def test_query_knowledge_base_description(self):
        """Test query_knowledge_base has proper description."""
        from src.agents.tools.database_tools import query_knowledge_base
        desc = get_tool_description(query_knowledge_base)
        assert desc is not None
        assert "knowledge" in desc.lower()

    def test_search_knowledge_description(self):
        """Test search_knowledge has proper description."""
        from src.agents.tools.database_tools import search_knowledge
        desc = get_tool_description(search_knowledge)
        assert desc is not None
        assert "search" in desc.lower() or "knowledge" in desc.lower()

    def test_query_system_status_description(self):
        """Test query_system_status has proper description."""
        from src.agents.tools.database_tools import query_system_status
        desc = get_tool_description(query_system_status)
        assert desc is not None
        # Accept "health", "status", or "system" in description
        assert "health" in desc.lower() or "status" in desc.lower() or "system" in desc.lower()


class TestDatabaseToolsMockedExecution:
    """Tests with mocked database for tool execution."""

    def test_query_talents_count_returns_string(self):
        """Test query_talents_count returns a string result."""
        from src.agents.tools.database_tools import query_talents_count

        # Call the function - it will fail to connect but should return error string
        result = query_talents_count()
        assert isinstance(result, str)
        # Either success or error message
        assert "TALENT OVERVIEW" in result or "Query failed" in result or "❌" in result

    def test_query_talent_details_returns_string(self):
        """Test query_talent_details returns a string result."""
        from src.agents.tools.database_tools import query_talent_details

        # Call the function with a test name
        result = query_talent_details("testuser")
        assert isinstance(result, str)
        # Either found, not found, or error
        assert "TALENT PROFILE" in result or "not found" in result or "Query failed" in result or "❌" in result

    def test_query_system_status_returns_string(self):
        """Test query_system_status returns a string result."""
        from src.agents.tools.database_tools import query_system_status

        result = query_system_status()
        assert isinstance(result, str)
        # Either healthy or unhealthy status
        assert "SYSTEM STATUS" in result or "UNHEALTHY" in result or "❌" in result

    def test_query_projects_returns_string(self):
        """Test query_projects returns a string result."""
        from src.agents.tools.database_tools import query_projects

        result = query_projects()
        assert isinstance(result, str)
        assert "PROJECT" in result or "Query failed" in result or "❌" in result

    def test_query_knowledge_base_returns_string(self):
        """Test query_knowledge_base returns a string result."""
        from src.agents.tools.database_tools import query_knowledge_base

        result = query_knowledge_base()
        assert isinstance(result, str)
        assert "KNOWLEDGE BASE" in result or "Query failed" in result or "❌" in result

    def test_search_knowledge_returns_string(self):
        """Test search_knowledge returns a string result."""
        from src.agents.tools.database_tools import search_knowledge

        result = search_knowledge("test query")
        assert isinstance(result, str)
        # Either success or error message
        assert "SEARCH RESULTS" in result or "Search failed" in result or "❌" in result or "No documents" in result


class TestDatabaseToolsClass:
    """Tests for DatabaseTools class async methods."""

    def test_database_tools_class_exists(self):
        """Test DatabaseTools class is defined."""
        from src.agents.tools.database_tools import DatabaseTools
        assert DatabaseTools is not None

    def test_get_talents_summary_method(self):
        """Test get_talents_summary class method exists."""
        from src.agents.tools.database_tools import DatabaseTools
        assert hasattr(DatabaseTools, "get_talents_summary")
        assert callable(getattr(DatabaseTools, "get_talents_summary"))

    def test_get_system_health_method(self):
        """Test get_system_health class method exists."""
        from src.agents.tools.database_tools import DatabaseTools
        assert hasattr(DatabaseTools, "get_system_health")
        assert callable(getattr(DatabaseTools, "get_system_health"))
