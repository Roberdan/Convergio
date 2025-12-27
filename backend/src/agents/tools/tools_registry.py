"""
Tools Registry - Unified tool registration for Agent Framework migration.
Provides a single point of access to all tools across the platform.
"""

from typing import Any, Dict, List, Callable, Optional
import structlog

logger = structlog.get_logger()


# Framework availability flags
try:
    from agent_framework import ai_function
    AGENT_FRAMEWORK_AVAILABLE = True
except ImportError:
    AGENT_FRAMEWORK_AVAILABLE = False

try:
    from autogen_core.tools import FunctionTool, BaseTool
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False
    FunctionTool = None
    BaseTool = None


class ToolsRegistry:
    """
    Unified registry for all AI agent tools.

    Supports both Agent Framework (@ai_function) and AutoGen (FunctionTool/BaseTool) patterns.
    Provides a single interface to access tools regardless of the underlying framework.
    """

    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._tool_descriptions: Dict[str, str] = {}
        self._tool_categories: Dict[str, List[str]] = {}
        self._initialized = False

    def _get_tool_name(self, tool: Callable) -> str:
        """Get name from tool (works with AIFunction and regular functions)."""
        if hasattr(tool, 'name'):
            return tool.name
        return getattr(tool, '__name__', str(tool))

    def _get_tool_description(self, tool: Callable) -> str:
        """Get description from tool (works with AIFunction and regular functions)."""
        if hasattr(tool, 'description') and tool.description:
            return tool.description
        doc = getattr(tool, '__doc__', None)
        if doc:
            return doc.strip()
        return "No description"

    def register_tool(
        self,
        tool: Callable,
        name: Optional[str] = None,
        description: Optional[str] = None,
        category: str = "general"
    ) -> None:
        """
        Register a tool function.

        Args:
            tool: The tool function (decorated with @ai_function or plain)
            name: Optional name override (defaults to function name)
            description: Optional description override (defaults to docstring)
            category: Tool category for organization
        """
        tool_name = name or self._get_tool_name(tool)
        tool_desc = description or self._get_tool_description(tool)

        self._tools[tool_name] = tool
        self._tool_descriptions[tool_name] = tool_desc

        if category not in self._tool_categories:
            self._tool_categories[category] = []
        if tool_name not in self._tool_categories[category]:
            self._tool_categories[category].append(tool_name)

        logger.debug(f"Registered tool: {tool_name}", category=category)

    def get_tool(self, name: str) -> Optional[Callable]:
        """Get a tool by name."""
        return self._tools.get(name)

    def get_all_tools(self) -> List[Callable]:
        """Get all registered tools."""
        return list(self._tools.values())

    def get_tools_by_category(self, category: str) -> List[Callable]:
        """Get all tools in a category."""
        tool_names = self._tool_categories.get(category, [])
        return [self._tools[name] for name in tool_names if name in self._tools]

    def get_tool_names(self) -> List[str]:
        """Get all tool names."""
        return list(self._tools.keys())

    def get_descriptions(self) -> Dict[str, str]:
        """Get all tool descriptions."""
        return self._tool_descriptions.copy()

    def get_categories(self) -> Dict[str, List[str]]:
        """Get tools organized by category."""
        return self._tool_categories.copy()

    def initialize(self) -> None:
        """
        Initialize the registry with all available tools.
        Loads tools from Agent Framework tools module.
        """
        if self._initialized:
            return

        logger.info("Initializing tools registry")

        try:
            # Load Agent Framework tools
            from .agent_framework_tools import get_all_agent_framework_tools

            af_tools = get_all_agent_framework_tools()
            for tool in af_tools:
                # Determine category from tool name
                name = self._get_tool_name(tool)
                name_lower = name.lower()
                if "search" in name_lower:
                    category = "search"
                elif "talent" in name_lower or "talents" in name_lower:
                    category = "database"
                elif "analytics" in name_lower or "intelligence" in name_lower:
                    category = "analytics"
                elif "date" in name_lower or "json" in name_lower:
                    category = "utility"
                else:
                    category = "general"

                self.register_tool(tool, category=category)

            logger.info(f"Loaded {len(af_tools)} Agent Framework tools")

        except ImportError as e:
            logger.warning(f"Agent Framework tools not available: {e}")

        try:
            # Load database tools
            from .database_tools import get_database_tools_af

            db_tools = get_database_tools_af()
            for tool in db_tools:
                tool_name = self._get_tool_name(tool)
                if tool_name not in self._tools:  # Avoid duplicates
                    self.register_tool(tool, category="database")

            logger.info(f"Loaded {len(db_tools)} database tools")

        except ImportError as e:
            logger.warning(f"Database tools not available: {e}")

        self._initialized = True
        logger.info(f"Tools registry initialized with {len(self._tools)} tools")

    def get_autogen_tools(self) -> List:
        """
        Get tools wrapped for AutoGen compatibility.

        Returns:
            List of FunctionTool objects for AutoGen.
        """
        if not AUTOGEN_AVAILABLE:
            raise ImportError("AutoGen is not available")

        from autogen_core.tools import FunctionTool

        autogen_tools = []
        for name, tool in self._tools.items():
            desc = self._tool_descriptions.get(name, "No description")
            autogen_tools.append(FunctionTool(func=tool, description=desc))

        return autogen_tools

    def get_agent_framework_tools(self) -> List[Callable]:
        """
        Get tools for Agent Framework.

        Returns:
            List of @ai_function decorated functions.
        """
        return list(self._tools.values())


# Global registry instance
_registry: Optional[ToolsRegistry] = None


def get_tools_registry() -> ToolsRegistry:
    """
    Get the global tools registry instance.
    Initializes on first access.
    """
    global _registry
    if _registry is None:
        _registry = ToolsRegistry()
        _registry.initialize()
    return _registry


def get_all_tools() -> List[Callable]:
    """Get all registered tools."""
    return get_tools_registry().get_all_tools()


def get_tool(name: str) -> Optional[Callable]:
    """Get a tool by name."""
    return get_tools_registry().get_tool(name)


def get_tool_descriptions() -> Dict[str, str]:
    """Get all tool descriptions."""
    return get_tools_registry().get_descriptions()


def get_tools_by_category(category: str) -> List[Callable]:
    """Get tools by category."""
    return get_tools_registry().get_tools_by_category(category)


# Export commonly used items
__all__ = [
    "ToolsRegistry",
    "get_tools_registry",
    "get_all_tools",
    "get_tool",
    "get_tool_descriptions",
    "get_tools_by_category",
    "AGENT_FRAMEWORK_AVAILABLE",
    "AUTOGEN_AVAILABLE",
]
