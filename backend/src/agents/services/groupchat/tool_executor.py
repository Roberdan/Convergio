"""
Tool Executor for GroupChat
Ensures tool calls from agents are properly executed
"""

import json
import structlog
from typing import Any, Dict, List, Optional

# Optional AutoGen import
try:
    from autogen_agentchat.messages import TextMessage
except ImportError:
    class TextMessage:  # type: ignore
        """Fallback TextMessage when AutoGen not available"""
        def __init__(self, content: str = "", source: str = ""):
            self.content = content
            self.source = source

from ...tools.smart_tool_selector import SmartToolSelector
from ...tools.web_search_tool import WebSearchTool, WebSearchArgs
from ..observability.telemetry import get_telemetry, TelemetryContext
try:
    from ..decision_engine import DecisionPlan
except Exception:
    DecisionPlan = None  # type: ignore

logger = structlog.get_logger()


class GroupChatToolExecutor:
    """Executes tool calls emitted by agents in GroupChat"""

    def __init__(
        self,
        execution_plan: Optional["DecisionPlan"] = None,
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> None:
        self.selector = SmartToolSelector()
        self.web_search = WebSearchTool()
        self.tool_call_count = 0
        self.tool_results: List[Dict[str, Any]] = []
        self.execution_plan = execution_plan
        self.conversation_id = conversation_id or ""
        self.user_id = user_id or ""
        self._plan: Dict[str, Any] = {}

    async def should_use_web_search(self, message: str) -> bool:
        """Determine if this message needs web search"""
        if self.execution_plan and (
            (hasattr(self.execution_plan, "web_first") and self.execution_plan.web_first)
            or ("web_search" in getattr(self.execution_plan, "tools", []))
        ):
            return True
        return self.selector.should_use_web_search(message, threshold=0.6)

    def set_decision_plan(self, plan: Optional[Dict[str, Any]] = None) -> None:
        """Optionally provide a DecisionPlan dict to guide execution order"""
        self._plan = plan or {}

    async def inject_web_search_if_needed(self, message: str) -> Optional[str]:
        """
        Analyze message and inject web search results if needed.
        This is called BEFORE the agent processes the message.
        """
        # If DecisionPlan explicitly requests web first, honor it
        plan = getattr(self, "_plan", {}) or {}
        plan_tools = plan.get("tools", [])
        force_web = "web_search" in plan_tools and plan.get("sources", [""])[:1] == ["web"]

        if not force_web and not await self.should_use_web_search(message):
            return None

        try:
            logger.info("🌐 Injecting web search for query", query=message[:100])
            telemetry = get_telemetry()
            if telemetry and self.conversation_id:
                telemetry_context = TelemetryContext(conversation_id=self.conversation_id, user_id=self.user_id)
                with telemetry.trace_tool_call("web_search", telemetry_context):
                    pass

            # Execute web search
            args = WebSearchArgs(
                query=message,
                max_results=3,
                search_type="general"
            )
            result = await self.web_search.run(args)

            # Parse result
            search_data = json.loads(result) if isinstance(result, str) else result

            # Format as context for the agent
            if "results" in search_data and search_data["results"]:
                context = f"\n\n📊 Real-time Web Search Results:\n{search_data['results']}\n\n"
                logger.info("✅ Web search injected successfully")
                return context
            else:
                logger.warning("Web search returned no results")
                return None

        except Exception as e:
            logger.error(f"Failed to inject web search: {e}")
            return None
    
    async def execute_tool_calls(self, tool_calls: List[Dict[str, Any]]) -> List[str]:
        """
        Execute a list of tool calls and return results.
        
        Args:
            tool_calls: List of tool call dictionaries with structure:
                {"function": {"name": "tool_name", "arguments": "{json}"}}
        
        Returns:
            List of tool execution results as strings
        """
        results = []
        
        for tool_call in tool_calls:
            try:
                self.tool_call_count += 1
                
                function = tool_call.get("function", {})
                tool_name = function.get("name")
                raw_args = function.get("arguments", "{}")
                
                logger.info(f"🔧 Executing tool: {tool_name}", args=raw_args[:100])
                telemetry = get_telemetry()
                telemetry_context = None
                if telemetry and self.conversation_id:
                    telemetry_context = TelemetryContext(conversation_id=self.conversation_id, user_id=self.user_id)
                    with telemetry.trace_tool_call(tool_name or "unknown", telemetry_context):
                        pass
                
                # Parse arguments
                try:
                    args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                except:
                    args = {}
                
                # Execute based on tool name
                if tool_name == "web_search":
                    if telemetry and telemetry_context:
                        telemetry.record_tool_invoked("web_search", telemetry_context)
                    result = await self._execute_web_search(args)
                elif tool_name == "query_talents":
                    if telemetry and telemetry_context:
                        telemetry.record_tool_invoked("query_talents", telemetry_context)
                    result = await self._execute_talents_query(args)
                elif tool_name == "vector_search":
                    if telemetry and telemetry_context:
                        telemetry.record_tool_invoked("vector_search", telemetry_context)
                    result = await self._execute_vector_search(args)
                elif tool_name == "business_intelligence":
                    if telemetry and telemetry_context:
                        telemetry.record_tool_invoked("business_intelligence", telemetry_context)
                    result = await self._execute_business_intelligence(args)
                else:
                    result = f"Tool '{tool_name}' not recognized"
                
                results.append(result)
                self.tool_results.append({
                    "tool": tool_name,
                    "args": args,
                    "result": result
                })
                
            except Exception as e:
                logger.error(f"Tool execution failed: {e}")
                results.append(f"Error executing tool: {str(e)}")
        
        return results
    
    async def _execute_web_search(self, args: Dict[str, Any]) -> str:
        """Execute web search tool"""
        try:
            search_args = WebSearchArgs(
                query=args.get("query", ""),
                max_results=args.get("max_results", 5),
                search_type=args.get("search_type", "general")
            )
            result = await self.web_search.run(search_args)
            logger.info("✅ Web search completed successfully")
            return result
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return f"Web search error: {str(e)}"
    
    async def _execute_talents_query(self, args: Dict[str, Any]) -> str:
        """Execute talents query tool"""
        try:
            from ..tools.convergio_tools import TalentsQueryTool, TalentsQueryArgs
            tool = TalentsQueryTool()
            query_args = TalentsQueryArgs(
                query_type=args.get("query_type", "count")
            )
            result = await tool.run(query_args)
            return result
        except Exception as e:
            return f"Talents query error: {str(e)}"
    
    async def _execute_vector_search(self, args: Dict[str, Any]) -> str:
        """Execute vector search tool"""
        try:
            from ..tools.convergio_tools import VectorSearchTool, VectorSearchArgs
            tool = VectorSearchTool()
            search_args = VectorSearchArgs(
                query=args.get("query", ""),
                top_k=args.get("top_k", 5)
            )
            result = await tool.run(search_args)
            return result
        except Exception as e:
            return f"Vector search error: {str(e)}"
    
    async def _execute_business_intelligence(self, args: Dict[str, Any]) -> str:
        """Execute business intelligence tool"""
        try:
            from ..tools.convergio_tools import BusinessIntelligenceTool, BusinessIntelligenceArgs
            tool = BusinessIntelligenceTool()
            bi_args = BusinessIntelligenceArgs(
                focus_area=args.get("focus_area", "overview")
            )
            result = await tool.run(bi_args)
            return result
        except Exception as e:
            return f"Business intelligence error: {str(e)}"
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get tool execution metrics"""
        return {
            "total_calls": self.tool_call_count,
            "results": self.tool_results,
            "unique_tools": list(set(r["tool"] for r in self.tool_results))
        }