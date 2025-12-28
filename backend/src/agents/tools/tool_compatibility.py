"""
Tool Compatibility Layer
Provides compatibility between AutoGen tools and Agent Framework tools
"""

from typing import List, Any, Dict
import structlog

logger = structlog.get_logger()


class ToolConverter:
    """Convert between AutoGen and Agent Framework tool formats"""

    @staticmethod
    def autogen_to_agent_framework(autogen_tools: List[Any]) -> List[Any]:
        """
        Convert AutoGen FunctionTool/BaseTool to Agent Framework @ai_function.

        Args:
            autogen_tools: List of AutoGen tools

        Returns:
            List of Agent Framework compatible tools
        """
        converted = []

        for tool in autogen_tools:
            # Check if it's already an Agent Framework tool (has __name__ and __annotations__)
            if hasattr(tool, "__name__") and hasattr(tool, "__annotations__"):
                converted.append(tool)
                continue

            # Try to extract function from AutoGen tool
            if hasattr(tool, "run"):
                # It's a BaseTool, wrap its run method
                wrapped = ToolConverter._wrap_autogen_tool(tool)
                if wrapped:
                    converted.append(wrapped)
            else:
                logger.warning(f"Unknown tool format: {type(tool)}")

        logger.info(f"Converted {len(converted)} tools to Agent Framework format")
        return converted

    @staticmethod
    def _wrap_autogen_tool(tool: Any) -> Any:
        """
        Wrap an AutoGen tool's run method as an Agent Framework function.

        Args:
            tool: AutoGen BaseTool instance

        Returns:
            Wrapped function or None
        """
        try:
            # Create a wrapper function
            async def wrapped_tool(**kwargs):
                """Wrapped AutoGen tool"""
                # Extract args based on tool's args_type
                if hasattr(tool, "args_type"):
                    args_instance = tool.args_type(**kwargs)
                    return await tool.run(args_instance)
                else:
                    return await tool.run(**kwargs)

            # Set function name and docstring
            wrapped_tool.__name__ = getattr(tool, "name", "unknown_tool")
            wrapped_tool.__doc__ = getattr(tool, "description", "No description")

            # Add annotations for Agent Framework
            if hasattr(tool, "args_type"):
                # Get annotations from Pydantic model
                wrapped_tool.__annotations__ = {
                    k: v for k, v in tool.args_type.__annotations__.items()
                }

            return wrapped_tool

        except Exception as e:
            logger.error(f"Failed to wrap tool: {e}")
            return None

    @staticmethod
    def get_hybrid_toolset() -> Dict[str, List[Any]]:
        """
        Get both AutoGen and Agent Framework tools for gradual migration.

        Returns:
            Dictionary with "autogen" and "agent_framework" tool lists
        """
        result = {
            "autogen": [],
            "agent_framework": []
        }

        # Get AutoGen tools
        try:
            from src.agents.tools.web_search_tool import get_web_tools
            from src.agents.tools.database_tools import get_database_tools
            from src.agents.tools.vector_search_tool import get_vector_tools

            result["autogen"].extend(get_web_tools())
            result["autogen"].extend(get_database_tools())
            result["autogen"].extend(get_vector_tools())

            logger.info(f"Loaded {len(result['autogen'])} AutoGen tools")

        except Exception as e:
            logger.warning(f"Failed to load AutoGen tools: {e}")

        # Get Agent Framework tools
        try:
            from src.agents.tools.agent_framework_tools import get_all_agent_framework_tools

            result["agent_framework"] = get_all_agent_framework_tools()

            logger.info(f"Loaded {len(result['agent_framework'])} Agent Framework tools")

        except Exception as e:
            logger.warning(f"Failed to load Agent Framework tools: {e}")

        return result


def get_tools_for_framework(framework: str = "agent_framework") -> List[Any]:
    """
    Get appropriate tools for the specified framework.

    Args:
        framework: "autogen" or "agent_framework"

    Returns:
        List of tools
    """
    if framework == "agent_framework":
        try:
            from src.agents.tools.agent_framework_tools import get_all_agent_framework_tools
            return get_all_agent_framework_tools()
        except ImportError:
            logger.warning("Agent Framework tools not available, falling back to AutoGen")
            framework = "autogen"

    if framework == "autogen":
        from src.agents.tools.web_search_tool import get_web_tools
        from src.agents.tools.database_tools import get_database_tools
        from src.agents.tools.vector_search_tool import get_vector_tools

        tools = []
        tools.extend(get_web_tools())
        tools.extend(get_database_tools())
        tools.extend(get_vector_tools())

        return tools

    raise ValueError(f"Unknown framework: {framework}")
