"""
Intelligent Tool Executor
Integrates Smart Tool Selector with Agent Framework tools.
Automatically decides when to use web search vs regular AI chat.

Supports both Agent Framework (@ai_function) and AutoGen (FunctionTool) patterns.
"""

import json
import structlog
from typing import Any, Dict, List, Optional, Callable

# Agent Framework import with fallback
try:
    from agent_framework import ai_function
    AGENT_FRAMEWORK_AVAILABLE = True
except ImportError:
    AGENT_FRAMEWORK_AVAILABLE = False

# Legacy AutoGen import for backward compatibility
try:
    from autogen_core.tools import BaseTool
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False
    BaseTool = None

from .smart_tool_selector import SmartToolSelector
from .tools_registry import get_tools_registry, get_tool
from .vector_search_client import VectorSearchClient

# Try to import AI client manager (may fail if autogen_ext not installed)
try:
    from ..ai_clients import get_ai_client_manager
    AI_CLIENTS_AVAILABLE = True
except ImportError:
    AI_CLIENTS_AVAILABLE = False
    get_ai_client_manager = None

logger = structlog.get_logger()


class IntelligentToolExecutor:
    """
    Executes tools intelligently based on query analysis.
    Automatically routes queries to appropriate tools.

    Uses the unified tools registry to access all available tools,
    supporting both Agent Framework and AutoGen patterns.
    """

    def __init__(self):
        """Initialize with tools from the registry."""
        self.selector = SmartToolSelector()
        self.registry = get_tools_registry()
        self.vector_client = None  # Initialize only when needed
        self.ai_manager = get_ai_client_manager() if AI_CLIENTS_AVAILABLE else None

        # Cache tool references for performance
        self._web_search_tool = None
        self._vector_search_tool = None
        self._database_tools = None

        # Track tool usage for metrics
        self.tool_usage = {
            "web_search": 0,
            "vector_search": 0,
            "database": 0,
            "ai_chat": 0
        }

        logger.info(
            "IntelligentToolExecutor initialized",
            agent_framework_available=AGENT_FRAMEWORK_AVAILABLE,
            autogen_available=AUTOGEN_AVAILABLE,
            ai_clients_available=AI_CLIENTS_AVAILABLE,
            registered_tools=len(self.registry.get_tool_names())
        )

    def _get_web_search_tool(self) -> Optional[Callable]:
        """Get web search tool from registry."""
        if self._web_search_tool is None:
            self._web_search_tool = get_tool("web_search")
        return self._web_search_tool

    def _get_vector_search_tool(self) -> Optional[Callable]:
        """Get vector search tool from registry."""
        if self._vector_search_tool is None:
            self._vector_search_tool = get_tool("vector_search")
        return self._vector_search_tool

    def _get_database_tools(self) -> List[Callable]:
        """Get database tools from registry."""
        if self._database_tools is None:
            self._database_tools = self.registry.get_tools_by_category("database")
        return self._database_tools
    
    async def execute_query(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        threshold: float = 0.7
    ) -> Dict[str, Any]:
        """
        Execute a query using the most appropriate tool(s).
        
        Args:
            query: The user query
            context: Optional context for the query
            threshold: Confidence threshold for tool selection
        
        Returns:
            Response with results and metadata
        """
        
        # Analyze the query
        analysis = self.selector.analyze_query(query)
        
        logger.info(
            "🧠 Query Analysis",
            query=query[:100],
            needs_web=analysis["needs_web_search"],
            confidence=f"{analysis['confidence']:.0%}",
            suggested_tools=analysis["suggested_tools"]
        )
        
        results = {
            "query": query,
            "analysis": analysis,
            "tools_used": [],
            "responses": {}
        }
        
        # Execute based on analysis
        if analysis["needs_web_search"] and analysis["confidence"] >= threshold:
            # Use web search for current/real-time info
            logger.info("🌐 Using web search for real-time data")
            self.tool_usage["web_search"] += 1
            
            web_result = await self._execute_web_search(query)
            results["tools_used"].append("web_search")
            results["responses"]["web_search"] = web_result
            
        elif "database_query" in analysis["suggested_tools"]:
            # Query internal database
            logger.info("📊 Using database query for internal data")
            self.tool_usage["database"] += 1
            
            db_result = await self._execute_database_query(query, context)
            results["tools_used"].append("database_query")
            results["responses"]["database"] = db_result
            
        elif "vector_search" in analysis["suggested_tools"]:
            # Use vector search for semantic search
            logger.info("🔍 Using vector search for semantic matching")
            self.tool_usage["vector_search"] += 1
            
            vector_result = await self._execute_vector_search(query)
            results["tools_used"].append("vector_search")
            results["responses"]["vector_search"] = vector_result
            
        else:
            # Use regular AI chat for general knowledge
            logger.info("💬 Using AI chat for general knowledge")
            self.tool_usage["ai_chat"] += 1
            
            chat_result = await self._execute_ai_chat(query, context)
            results["tools_used"].append("ai_chat")
            results["responses"]["ai_chat"] = chat_result
        
        # Log metrics
        logger.info(
            "📈 Tool Usage Metrics",
            web_search=self.tool_usage["web_search"],
            vector_search=self.tool_usage["vector_search"],
            database=self.tool_usage["database"],
            ai_chat=self.tool_usage["ai_chat"]
        )
        
        return results
    
    async def _execute_web_search(self, query: str) -> Dict[str, Any]:
        """Execute web search using the registry's web_search tool."""
        try:
            web_search = self._get_web_search_tool()

            if web_search is None:
                logger.warning("Web search tool not found in registry")
                return {"error": "Web search tool not available"}

            # Call the @ai_function decorated tool
            result = await web_search(query=query, max_results=5, search_type="general")

            # Result is already a string, try to parse if JSON
            if isinstance(result, str):
                if result.startswith("{") or result.startswith("["):
                    try:
                        return json.loads(result)
                    except json.JSONDecodeError:
                        pass
                return {"source": "web_search", "query": query, "response": result}

            return result

        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return {"error": str(e)}
    
    async def _execute_database_query(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute database query using registry's database tools."""
        try:
            # Get database tools from registry
            db_tools = self._get_database_tools()

            if not db_tools:
                logger.warning("No database tools found in registry")
                return {"error": "Database tools not available"}

            # Determine which tool to use based on query content
            query_lower = query.lower()

            # Try to find the right tool based on query keywords
            if "talent" in query_lower or "user" in query_lower:
                tool = get_tool("get_talents_summary") or get_tool("search_talents")
            elif "count" in query_lower or "how many" in query_lower:
                tool = get_tool("query_talents_count")
            elif "department" in query_lower or "structure" in query_lower:
                tool = get_tool("query_department_structure")
            elif "knowledge" in query_lower:
                tool = get_tool("query_knowledge_base") or get_tool("search_knowledge")
            else:
                # Default to first available database tool
                tool = db_tools[0] if db_tools else None

            if tool is None:
                return {"error": "No suitable database tool found for query"}

            # Execute the tool (handle both sync and async)
            import asyncio
            if asyncio.iscoroutinefunction(tool):
                result = await tool()
            else:
                result = tool()

            # Parse result
            if isinstance(result, str):
                try:
                    return json.loads(result)
                except json.JSONDecodeError:
                    return {"source": "database", "query": query, "response": result}

            return {"source": "database", "query": query, "result": result}

        except Exception as e:
            logger.error(f"Database query failed: {e}")
            return {"error": str(e)}
    
    async def _execute_vector_search(self, query: str) -> Dict[str, Any]:
        """Execute vector search using registry's vector_search tool."""
        try:
            # Try to use registry tool first
            vector_search = self._get_vector_search_tool()

            if vector_search is not None:
                # Use the @ai_function decorated tool
                result = await vector_search(query=query, top_k=5, search_type="semantic")

                if isinstance(result, str):
                    return {"source": "vector_search", "query": query, "response": result}
                return result

            # Fallback to direct vector client if tool not in registry
            if self.vector_client is None:
                try:
                    self.vector_client = VectorSearchClient()
                except Exception as init_error:
                    logger.warning(f"Could not initialize vector client: {init_error}")
                    return {
                        "source": "vector_search",
                        "query": query,
                        "error": "Vector search not configured",
                        "fallback": "Using AI chat instead"
                    }

            results = await self.vector_client.search(
                query=query,
                top_k=5
            )

            return {
                "source": "vector_search",
                "query": query,
                "results": results,
                "count": len(results)
            }

        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return {"error": str(e)}
    
    async def _execute_ai_chat(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute regular AI chat for general knowledge."""
        try:
            if self.ai_manager is None:
                return {
                    "source": "ai_chat",
                    "query": query,
                    "error": "AI client manager not available",
                    "fallback": "AI chat functionality requires autogen_ext"
                }

            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful assistant. Answer based on your training knowledge."
                },
                {
                    "role": "user",
                    "content": query
                }
            ]

            # Add context if provided
            if context:
                messages[0]["content"] += f"\n\nContext: {json.dumps(context)}"

            response = await self.ai_manager.chat_completion(
                messages=messages,
                provider="openai",
                temperature=0.7
            )

            return {
                "source": "ai_chat",
                "query": query,
                "response": response,
                "model": "gpt-4o-mini"
            }

        except Exception as e:
            logger.error(f"AI chat failed: {e}")
            return {"error": str(e)}
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get tool usage metrics"""
        total = sum(self.tool_usage.values())
        
        if total == 0:
            return {
                "total_queries": 0,
                "usage": self.tool_usage,
                "percentages": {}
            }
        
        percentages = {
            tool: (count / total) * 100
            for tool, count in self.tool_usage.items()
        }
        
        return {
            "total_queries": total,
            "usage": self.tool_usage,
            "percentages": percentages
        }
    
    def reset_metrics(self):
        """Reset usage metrics"""
        self.tool_usage = {
            "web_search": 0,
            "vector_search": 0,
            "database": 0,
            "ai_chat": 0
        }


# Global instance
_intelligent_executor = None


def get_intelligent_executor() -> IntelligentToolExecutor:
    """Get singleton intelligent executor"""
    global _intelligent_executor
    if _intelligent_executor is None:
        _intelligent_executor = IntelligentToolExecutor()
    return _intelligent_executor


# Convenience function for Agent Framework / AutoGen integration
async def execute_intelligent_query(
    query: str,
    context: Optional[Dict[str, Any]] = None,
    threshold: float = 0.7
) -> Dict[str, Any]:
    """
    Execute a query intelligently, automatically selecting the right tool.

    This is the main entry point for agents to use intelligent tool selection.
    Works with both Agent Framework and AutoGen patterns via the unified tools registry.

    Args:
        query: The user query to process
        context: Optional context for the query
        threshold: Confidence threshold for tool selection (default: 0.7)

    Returns:
        Dict containing query analysis, tools used, and responses
    """
    executor = get_intelligent_executor()
    return await executor.execute_query(query, context, threshold)


# Export framework availability for external checks
__all__ = [
    "IntelligentToolExecutor",
    "get_intelligent_executor",
    "execute_intelligent_query",
    "AGENT_FRAMEWORK_AVAILABLE",
    "AUTOGEN_AVAILABLE",
    "AI_CLIENTS_AVAILABLE",
]