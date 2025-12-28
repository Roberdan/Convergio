"""
Workflow Patterns - Predefined workflow templates
Common workflow patterns ready to use
"""

from typing import Dict, List, Any, Callable, Optional
import structlog

try:
    from agent_framework import Workflow, ChatAgent
    AGENT_FRAMEWORK_AVAILABLE = True
except ImportError:
    AGENT_FRAMEWORK_AVAILABLE = False
    Workflow = None
    ChatAgent = None

from .workflow_builder import WorkflowBuilder

logger = structlog.get_logger()


def create_sequential_workflow(
    agents: List[ChatAgent],
    names: Optional[List[str]] = None
) -> Workflow:
    """
    Create a sequential workflow where agents execute one after another.

    Args:
        agents: List of ChatAgent instances in execution order
        names: Optional custom names for nodes

    Returns:
        Configured Workflow
    """
    if not AGENT_FRAMEWORK_AVAILABLE:
        raise ImportError("Agent Framework not available")

    builder = WorkflowBuilder()

    # Create agent executors
    node_handlers = []

    for i, agent in enumerate(agents):
        node_name = names[i] if names and i < len(names) else f"agent_{i}"

        async def executor(context: Dict[str, Any], ag=agent) -> Dict[str, Any]:
            from agent_framework.messages import ChatMessage

            message = context.get("message", "")
            msg = ChatMessage(role="user", content=message)
            result = await ag.run(task=msg)

            # Extract response
            if hasattr(result, "messages"):
                for m in reversed(result.messages):
                    if hasattr(m, "role") and m.role == "assistant":
                        context["response"] = m.content
                        break

            context.setdefault("agents_executed", []).append(ag.name)
            return context

        node_handlers.append((node_name, executor))

    # Build sequential chain
    builder.add_sequential_chain(node_handlers)

    logger.info("Sequential workflow created", agents=len(agents))
    return builder.build()


def create_parallel_workflow(
    agents: List[ChatAgent],
    aggregation_strategy: str = "concatenate"
) -> Workflow:
    """
    Create a parallel workflow where all agents execute simultaneously.

    Args:
        agents: List of ChatAgent instances
        aggregation_strategy: How to combine results ("concatenate", "vote", "synthesize")

    Returns:
        Configured Workflow
    """
    if not AGENT_FRAMEWORK_AVAILABLE:
        raise ImportError("Agent Framework not available")

    builder = WorkflowBuilder()

    # Start node
    async def start_node(context: Dict[str, Any]) -> Dict[str, Any]:
        context["agent_responses"] = {}
        context["agents_executed"] = []
        return context

    builder.add_node("start", start_node)

    # Add agents in parallel
    for agent in agents:
        async def agent_executor(context: Dict[str, Any], ag=agent) -> Dict[str, Any]:
            from agent_framework.messages import ChatMessage

            message = context.get("message", "")
            msg = ChatMessage(role="user", content=message)
            result = await ag.run(task=msg)

            # Extract response
            response = ""
            if hasattr(result, "messages"):
                for m in reversed(result.messages):
                    if hasattr(m, "role") and m.role == "assistant":
                        response = m.content
                        break

            context["agent_responses"][ag.name] = response
            context["agents_executed"].append(ag.name)
            return context

        builder.add_node(agent.name, agent_executor)
        builder.add_edge("start", agent.name)

    # Aggregation node
    async def aggregate_node(context: Dict[str, Any]) -> Dict[str, Any]:
        responses = context.get("agent_responses", {})

        if aggregation_strategy == "concatenate":
            combined = "\n\n---\n\n".join(responses.values())
            context["response"] = combined

        elif aggregation_strategy == "vote":
            # Simple voting - most common response wins
            from collections import Counter
            counts = Counter(responses.values())
            context["response"] = counts.most_common(1)[0][0]

        elif aggregation_strategy == "synthesize":
            # Placeholder for synthesis (could use Ali)
            context["response"] = "\n\n".join(
                f"**{name}**: {resp}" for name, resp in responses.items()
            )

        return context

    builder.add_node("aggregate", aggregate_node)

    # Connect all agents to aggregation
    for agent in agents:
        builder.add_edge(agent.name, "aggregate")

    logger.info("Parallel workflow created", agents=len(agents))
    return builder.build()


def create_conditional_workflow(
    condition_fn: Callable,
    true_agents: List[ChatAgent],
    false_agents: List[ChatAgent]
) -> Workflow:
    """
    Create a conditional workflow that branches based on a condition.

    Args:
        condition_fn: Function that evaluates condition from context
        true_agents: Agents to execute if condition is True
        false_agents: Agents to execute if condition is False

    Returns:
        Configured Workflow
    """
    if not AGENT_FRAMEWORK_AVAILABLE:
        raise ImportError("Agent Framework not available")

    builder = WorkflowBuilder()

    # Evaluation node
    async def evaluate_node(context: Dict[str, Any]) -> Dict[str, Any]:
        result = await condition_fn(context)
        context["condition_result"] = result
        return context

    builder.add_node("evaluate", evaluate_node)

    # Create branches
    create_sequential_workflow(true_agents, [f"true_{i}" for i in range(len(true_agents))])
    create_sequential_workflow(false_agents, [f"false_{i}" for i in range(len(false_agents))])

    # Add conditional routing
    async def routing_fn(context: Dict[str, Any]) -> str:
        return "true_branch" if context.get("condition_result") else "false_branch"

    builder.add_conditional(
        "evaluate",
        routing_fn,
        {"true_branch": "true_0", "false_branch": "false_0"}
    )

    logger.info("Conditional workflow created")
    return builder.build()


def create_human_in_loop_workflow(
    agents: List[ChatAgent],
    approval_required: bool = True,
    approval_threshold: float = 0.8
) -> Workflow:
    """
    Create a workflow with human-in-the-loop approval steps.

    Args:
        agents: List of ChatAgent instances
        approval_required: Whether human approval is required
        approval_threshold: Confidence threshold for auto-approval

    Returns:
        Configured Workflow
    """
    if not AGENT_FRAMEWORK_AVAILABLE:
        raise ImportError("Agent Framework not available")

    builder = WorkflowBuilder()

    # Agent execution
    for i, agent in enumerate(agents):
        async def agent_executor(context: Dict[str, Any], ag=agent) -> Dict[str, Any]:
            from agent_framework.messages import ChatMessage

            message = context.get("message", "")
            msg = ChatMessage(role="user", content=message)
            result = await ag.run(task=msg)

            # Extract response
            if hasattr(result, "messages"):
                for m in reversed(result.messages):
                    if hasattr(m, "role") and m.role == "assistant":
                        context["response"] = m.content
                        break

            context.setdefault("agents_executed", []).append(ag.name)

            # Simulate confidence score
            context["confidence"] = 0.9  # Placeholder

            return context

        builder.add_node(f"agent_{i}", agent_executor)

        # Approval check node
        async def approval_node(context: Dict[str, Any]) -> Dict[str, Any]:
            confidence = context.get("confidence", 0.0)

            if not approval_required or confidence >= approval_threshold:
                context["approved"] = True
            else:
                # In real implementation, this would wait for human approval
                context["requires_human_approval"] = True
                context["approved"] = False  # Placeholder

            return context

        builder.add_node(f"approval_{i}", approval_node)

        # Connect agent to approval
        builder.add_edge(f"agent_{i}", f"approval_{i}")

        # Conditional based on approval
        if i < len(agents) - 1:
            async def approval_decision(context: Dict[str, Any]) -> str:
                return "approved" if context.get("approved") else "rejected"

            builder.add_conditional(
                f"approval_{i}",
                approval_decision,
                {"approved": f"agent_{i+1}", "rejected": "end"}
            )

    # End node
    async def end_node(context: Dict[str, Any]) -> Dict[str, Any]:
        context["workflow_complete"] = True
        return context

    builder.add_node("end", end_node)

    logger.info("Human-in-the-loop workflow created", agents=len(agents))
    return builder.build()


def create_retry_workflow(
    agent: ChatAgent,
    max_retries: int = 3,
    retry_condition_fn: Optional[Callable] = None
) -> Workflow:
    """
    Create a workflow with retry logic.

    Args:
        agent: ChatAgent to execute with retries
        max_retries: Maximum number of retry attempts
        retry_condition_fn: Optional function to determine if retry is needed

    Returns:
        Configured Workflow
    """
    if not AGENT_FRAMEWORK_AVAILABLE:
        raise ImportError("Agent Framework not available")

    builder = WorkflowBuilder()

    # Execution node
    async def execute_node(context: Dict[str, Any]) -> Dict[str, Any]:
        from agent_framework.messages import ChatMessage

        message = context.get("message", "")
        msg = ChatMessage(role="user", content=message)

        try:
            result = await agent.run(task=msg)

            if hasattr(result, "messages"):
                for m in reversed(result.messages):
                    if hasattr(m, "role") and m.role == "assistant":
                        context["response"] = m.content
                        break

            context["success"] = True
            context["retry_count"] = context.get("retry_count", 0)

        except Exception as e:
            context["success"] = False
            context["error"] = str(e)
            context["retry_count"] = context.get("retry_count", 0) + 1

        return context

    builder.add_node("execute", execute_node)

    # Retry decision node
    async def retry_decision_fn(context: Dict[str, Any]) -> str:
        retry_count = context.get("retry_count", 0)
        success = context.get("success", False)

        if success:
            return "success"
        elif retry_count >= max_retries:
            return "max_retries"
        else:
            # Check custom retry condition if provided
            if retry_condition_fn and not await retry_condition_fn(context):
                return "no_retry"
            return "retry"

    builder.add_conditional(
        "execute",
        retry_decision_fn,
        {
            "retry": "execute",
            "success": "end",
            "max_retries": "end",
            "no_retry": "end"
        }
    )

    # End node
    async def end_node(context: Dict[str, Any]) -> Dict[str, Any]:
        context["workflow_complete"] = True
        return context

    builder.add_node("end", end_node)

    logger.info("Retry workflow created", max_retries=max_retries)
    return builder.build()
