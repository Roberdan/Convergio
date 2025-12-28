"""
Orchestrator conversation handlers extracted for file size hygiene.
Implements conversation flow and direct agent conversation using the orchestrator instance.
"""

from datetime import datetime
from typing import Any, Dict, Optional, List
import structlog

import json

from .metrics import extract_agents_used, estimate_cost, serialize_chat_history
from .rag import build_memory_context as default_build_memory_context
from .types import GroupChatResult
from .intelligent_router import IntelligentAgentRouter


logger = structlog.get_logger()


async def _execute_tool_call(tool_call: dict) -> str:
    """Execute a single tool call dict emitted by the model and return a string result.
    Expected shape (AutoGen function-call style):
      { "function": { "name": "tool_name", "arguments": "{json}" } }
    """
    try:
        fn = (tool_call or {}).get("function", {})
        name = fn.get("name")
        raw_args = fn.get("arguments")
        args = {}
        if isinstance(raw_args, str) and raw_args.strip():
            try:
                args = json.loads(raw_args)
            except Exception:
                # Some providers send already-parsed args or invalid JSON; fall back to empty
                args = {}
        elif isinstance(raw_args, dict):
            args = raw_args

        # Import tool arg models and tools lazily to minimize import cost
        from ..tools.web_search_tool import WebSearchTool, WebSearchArgs, WebBrowseTool, WebBrowseArgs
        from ..tools.convergio_tools import (
            VectorSearchTool, VectorSearchArgs,
            TalentsQueryTool, TalentsQueryArgs,
            EngagementAnalyticsTool, EngagementAnalyticsArgs,
            BusinessIntelligenceTool, BusinessIntelligenceArgs,
        )

        # Dispatch by tool name
        if name == "web_search":
            tool = WebSearchTool()
            return await tool.run(WebSearchArgs(**{**{"query": "", "max_results": 5, "search_type": "general"}, **args}))
        if name == "web_browse":
            tool = WebBrowseTool()
            return await tool.run(WebBrowseArgs(**{**{"url": "", "action": "read"}, **args}))
        if name == "vector_search":
            tool = VectorSearchTool()
            return await tool.run(VectorSearchArgs(**{**{"query": "", "top_k": 5}, **args}))
        if name == "query_talents":
            tool = TalentsQueryTool()
            return await tool.run(TalentsQueryArgs(**{**{"query_type": "count"}, **args}))
        if name == "engagement_analytics":
            tool = EngagementAnalyticsTool()
            return await tool.run(EngagementAnalyticsArgs(**{**{"analysis_type": "summary"}, **args}))
        if name == "business_intelligence":
            tool = BusinessIntelligenceTool()
            return await tool.run(BusinessIntelligenceArgs(**{**{"focus_area": "overview"}, **args}))

        logger.warning("Unknown tool call received", tool_name=name)
        return f"Tool '{name}' not supported or not available"
    except Exception as e:
        logger.error("Tool execution failed", error=str(e))
        return f"Error executing tool: {str(e)}"


async def orchestrate_conversation_impl(
    orchestrator,
    message: str,
    user_id: str,
    conversation_id: Optional[str],
    context: Optional[Dict[str, Any]],
    max_rounds: int,
    run_groupchat_stream_func,
    build_memory_context_func=default_build_memory_context,
) -> GroupChatResult:
    """Run a GroupChat conversation and return a structured result."""
    if not orchestrator.is_healthy():
        raise RuntimeError("Orchestrator not initialized")

    start_time = datetime.now()
    run_metadata = {
        "conversation_id": conversation_id,
        "user_id": user_id,
        "mode": "groupchat",
        "context": context or {},
    }

    # Check if we should use single agent routing
    router = IntelligentAgentRouter()
    if router.should_use_single_agent(message):
        # Select the best single agent for this query
        all_agents = list(orchestrator.agents.values())
        best_agent = router.select_best_agent(message, all_agents, context)
        
        if best_agent:
            logger.info(f"🎯 Single agent routing to {best_agent.name}")
            # Direct execution with single agent
            return await direct_agent_conversation_impl(
                orchestrator, 
                best_agent.name, 
                message, 
                user_id, 
                conversation_id, 
                context
            )
    
    # Compute DecisionPlan if available
    try:
        if getattr(orchestrator.settings, 'decision_engine_enabled', False) and hasattr(orchestrator, 'decision_engine'):
            plan = orchestrator.decision_engine.plan(message, context or {})
            run_metadata["plan"] = plan.__dict__
    except Exception:
        pass

    # Execute the GroupChat stream for multi-agent scenarios
    chat_messages, full_response = await run_groupchat_stream_func(
        orchestrator.group_chat,
        task=message,
        observers=getattr(orchestrator, "observers", None),
        metadata={**run_metadata, "execution_plan": getattr(orchestrator, "_last_decision_plan", None)},
        hard_timeout_seconds=getattr(orchestrator.settings, 'autogen_timeout_seconds', 120),
        termination_markers=None,
        max_events=None,
        execution_plan=getattr(orchestrator, "_last_decision_plan", None),
    )

    duration = (datetime.now() - start_time).total_seconds()
    
    # Extract agents from messages or metadata
    agents_used = []
    for msg in chat_messages:
        # Check for metadata message with agents info
        if hasattr(msg, 'agents_involved'):
            agents_used = msg.agents_involved
            logger.info("📊 Found agents metadata", agents=agents_used)
            break
    
    # Fallback to extracting from message sources
    if not agents_used:
        agents_used = extract_agents_used(chat_messages)
        logger.info("📊 Extracted agents from messages", agents=agents_used)
    
    cost_breakdown = estimate_cost(chat_messages)

    # Final observer end notification
    try:
        observers = getattr(orchestrator, "observers", None)
        if observers:
            summary = {
                "total_messages": len(chat_messages),
                "agents_used": agents_used,
                "response_preview": (full_response[:120] if isinstance(full_response, str) else ""),
                "duration_seconds": duration,
                "cost_breakdown": cost_breakdown,
                "turn_count": len(chat_messages),
            }
            for obs in observers:
                try:
                    await obs.on_conversation_end(summary, run_metadata)
                except Exception:
                    pass
    except Exception:
        pass

    try:
        # Wrap messages into a simple object that mimics a chat result shape
        chat_result_wrapper = type("ChatResultWrapper", (object,), {"messages": chat_messages})()
        await store_conversation_impl(orchestrator, conversation_id or "", user_id, chat_result_wrapper, cost_breakdown)
    except Exception:
        pass

    return GroupChatResult(
        response=full_response or "",
        agents_used=agents_used,
        turn_count=len(chat_messages),
        duration_seconds=duration,
        cost_breakdown=cost_breakdown,
        timestamp=datetime.now().isoformat(),
        conversation_summary="Conversation completed.",
        routing_decisions=["groupchat"],
    )


async def direct_agent_conversation_impl(
    orchestrator, agent_name: str, message: str, user_id: str, conversation_id: str, context: Optional[Dict[str, Any]]
) -> GroupChatResult:
    start_time = datetime.now()
    tool_calls_detected = False
    try:
        agent = orchestrator.agents[agent_name]
        logger.info("🎯 Direct agent conversation starting", agent=agent_name, conversation_id=conversation_id, user_id=user_id)

        # Notify observers start
        run_metadata = {
            "conversation_id": conversation_id,
            "user_id": user_id,
            "mode": "direct-agent",
            "agent_name": agent_name,
            "context": context or {},
        }
        try:
            observers = getattr(orchestrator, "observers", None)
            if observers:
                for obs in observers:
                    await obs.on_conversation_start({**run_metadata, "task": message})
        except Exception:
            pass

        # Stream the direct agent; execute tool calls inline when encountered
        parts: List[str] = []
        try:
            async for response in agent.run_stream(task=message):
                # Try common shapes
                content = getattr(response, 'content', None)
                if isinstance(content, str):
                    parts.append(content)
                elif isinstance(content, list):
                    tool_calls_detected = True
                    for tool_call in content:
                        try:
                            result = await _execute_tool_call(tool_call)
                            if result:
                                parts.append(result)
                        except Exception as e:
                            logger.warning("Tool call execution failed", error=str(e))
                elif hasattr(response, 'messages') and response.messages:
                    for msg in response.messages:
                        mcontent = getattr(msg, 'content', None)
                        if isinstance(mcontent, str):
                            parts.append(mcontent)
                        elif isinstance(mcontent, list):
                            tool_calls_detected = True
                            for tool_call in mcontent:
                                try:
                                    result = await _execute_tool_call(tool_call)
                                    if result:
                                        parts.append(result)
                                except Exception as e:
                                    logger.warning("Tool call execution failed", error=str(e))
        except Exception as e:
            logger.warning("Direct agent streaming error", agent=agent_name, error=str(e))

        response_content = "\n\n".join([p for p in parts if p]).strip()

        # If we detected tool calls or got an empty response, try GroupChat fallback which has robust tool execution
        if tool_calls_detected or not response_content:
            try:
                from .runner import run_groupchat_stream
                logger.info("🔄 Routing via GroupChat as fallback for direct-agent tool execution", agent=agent_name)
                _, full_response = await run_groupchat_stream(
                    orchestrator.group_chat,
                    task=message,
                    observers=getattr(orchestrator, "observers", None),
                    metadata={**run_metadata, "mode": "direct-agent-fallback"},
                    hard_timeout_seconds=getattr(orchestrator.settings, 'autogen_timeout_seconds', 120),
                    termination_markers=None,
                    max_events=None,
                )
                if full_response:
                    response_content = full_response
            except Exception as e:
                logger.error("❌ GroupChat fallback failed", agent=agent_name, error=str(e))

        duration = (datetime.now() - start_time).total_seconds()

        # Notify observers end
        try:
            observers = getattr(orchestrator, "observers", None)
            if observers:
                summary = {
                    "total_messages": 1,
                    "agents_used": [agent_name],
                    "response_preview": response_content[:120] if isinstance(response_content, str) else "",
                    "duration_seconds": duration,
                    "cost_breakdown": {"total_cost": 0.01},
                    "turn_count": 1,
                }
                for obs in observers:
                    try:
                        await obs.on_conversation_end(summary, run_metadata)
                    except Exception:
                        pass
        except Exception:
            pass

        return GroupChatResult(
            response=response_content or "",
            agents_used=[agent_name],  # Only the agent that responded, not "user"
            turn_count=1,
            duration_seconds=duration,
            cost_breakdown={
                "total_cost": 0.01,
                "estimated_tokens": int(len(message + (response_content or "")) * 0.75),
                "cost_per_1k_tokens": 0.01,
                "currency": "USD",
            },
            timestamp=datetime.now().isoformat(),
            conversation_summary=f"Direct conversation with {agent_name}",
            routing_decisions=["direct-agent" + ("+fallback" if tool_calls_detected else "")],
        )
    except Exception as e:
        logger.error("❌ Direct agent conversation failed", agent=agent_name, error=str(e), exc_info=True)
        duration = (datetime.now() - start_time).total_seconds()
        return GroupChatResult(
            response=f"Sorry, I'm having trouble connecting with {agent_name}. Please try again later. Error: {str(e)}",
            agents_used=["system"],
            turn_count=0,
            duration_seconds=duration,
            cost_breakdown={"total_cost": 0.0, "estimated_tokens": 0},
            timestamp=datetime.now().isoformat(),
            conversation_summary="Direct conversation failed",
            routing_decisions=[f"Failed to route to {agent_name}"],
        )


async def generate_conversation_summary_impl(orchestrator, chat_result) -> str:
    if hasattr(chat_result, 'messages') and chat_result.messages:
        messages = [msg.content for msg in chat_result.messages if hasattr(msg, 'content')]
        return f"Conversation with {len(messages)} messages completed successfully."
    return "Conversation completed."


async def store_conversation_impl(orchestrator, conversation_id: str, user_id: str, chat_result, cost_breakdown: Dict[str, Any]) -> None:
    try:
        conversation_data = {
            "conversation_id": conversation_id,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "cost_breakdown": cost_breakdown,
            "chat_history": serialize_chat_history(getattr(chat_result, 'messages', [])),
            "status": "completed",
        }
        await orchestrator.state_manager.store_conversation(conversation_id, conversation_data)
    except Exception as e:
        logger.error("❌ Failed to store conversation", error=str(e))

