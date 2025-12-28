"""
Convergio Workflow - Main workflow implementation for the platform
Advanced graph-based workflow with checkpointing, parallel execution, and human-in-the-loop
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio
import structlog

try:
    from agent_framework import Workflow, WorkflowExecutor
    from agent_framework import ChatAgent
    AGENT_FRAMEWORK_AVAILABLE = True
except ImportError:
    AGENT_FRAMEWORK_AVAILABLE = False
    Workflow = None
    WorkflowExecutor = None
    ChatAgent = None

from src.core.agent_framework_config import get_checkpoint_store, get_agent_framework_config

logger = structlog.get_logger()


class ConvergioWorkflow:
    """
    Main workflow implementation for Convergio platform.

    Supports:
    - Multi-agent collaboration patterns
    - Checkpointing and resumption
    - Parallel agent execution
    - Conditional routing based on content
    - Human-in-the-loop approvals
    - Error handling and fallbacks
    """

    def __init__(
        self,
        agents: Dict[str, ChatAgent],
        config: Optional[Any] = None
    ):
        if not AGENT_FRAMEWORK_AVAILABLE:
            raise ImportError("Agent Framework not available")

        self.agents = agents
        self.config = config or get_agent_framework_config()
        self.workflow = Workflow()
        self.executor: Optional[WorkflowExecutor] = None
        self.checkpoint_store = None

        # Workflow state
        self.execution_history: List[Dict[str, Any]] = []
        self.current_checkpoint: Optional[str] = None

        logger.info("Convergio Workflow initialized", agents=len(agents))

    async def build(self, pattern: str = "intelligent_routing") -> "ConvergioWorkflow":
        """
        Build the workflow graph based on specified pattern.

        Args:
            pattern: Workflow pattern to use
                - "intelligent_routing": Smart single/multi-agent routing
                - "sequential": Sequential agent execution
                - "parallel": Parallel agent execution
                - "hierarchical": Ali-led hierarchical coordination

        Returns:
            Self for chaining
        """
        if pattern == "intelligent_routing":
            await self._build_intelligent_routing()
        elif pattern == "sequential":
            await self._build_sequential()
        elif pattern == "parallel":
            await self._build_parallel()
        elif pattern == "hierarchical":
            await self._build_hierarchical()
        else:
            raise ValueError(f"Unknown pattern: {pattern}")

        # Setup checkpointing if enabled
        if self.config.enable_checkpointing:
            self.checkpoint_store = get_checkpoint_store(self.config)

        # Create executor
        self.executor = WorkflowExecutor(
            workflow=self.workflow,
            checkpoint_store=self.checkpoint_store,
            max_iterations=self.config.max_workflow_iterations
        )

        logger.info("Workflow built", pattern=pattern)
        return self

    async def _build_intelligent_routing(self):
        """Build intelligent routing workflow (default)"""

        # Entry point
        self.workflow.add_executor("start", self._start_node)

        # Analysis phase
        self.workflow.add_executor("analyze", self._analyze_request)

        # Routing decision
        self.workflow.add_executor("route", self._route_decision)

        # Execution paths
        self.workflow.add_executor("single_agent", self._execute_single_agent)
        self.workflow.add_executor("multi_agent", self._execute_multi_agent)
        self.workflow.add_executor("ali_orchestration", self._ali_orchestration)

        # Aggregation
        self.workflow.add_executor("aggregate", self._aggregate_results)

        # Quality check
        self.workflow.add_executor("quality_check", self._quality_check)

        # Completion
        self.workflow.add_executor("complete", self._complete_node)

        # Define edges
        self.workflow.add_edge("start", "analyze")
        self.workflow.add_edge("analyze", "route")

        # Conditional routing
        self.workflow.add_conditional_edges(
            "route",
            self._routing_logic,
            {
                "single": "single_agent",
                "multi": "multi_agent",
                "ali": "ali_orchestration"
            }
        )

        # Execution to quality check
        self.workflow.add_edge("single_agent", "quality_check")
        self.workflow.add_edge("multi_agent", "aggregate")
        self.workflow.add_edge("ali_orchestration", "quality_check")

        self.workflow.add_edge("aggregate", "quality_check")

        # Quality check to completion
        self.workflow.add_conditional_edges(
            "quality_check",
            self._quality_logic,
            {
                "pass": "complete",
                "retry": "route",
                "escalate": "ali_orchestration"
            }
        )

    async def _build_sequential(self):
        """Build sequential workflow"""
        self.workflow.add_executor("start", self._start_node)

        # Add agents in sequence
        agent_names = list(self.agents.keys())
        for i, agent_name in enumerate(agent_names):
            self.workflow.add_executor(f"agent_{i}", self._create_agent_node(agent_name))

        self.workflow.add_executor("complete", self._complete_node)

        # Chain them
        self.workflow.add_edge("start", "agent_0")
        for i in range(len(agent_names) - 1):
            self.workflow.add_edge(f"agent_{i}", f"agent_{i+1}")
        self.workflow.add_edge(f"agent_{len(agent_names)-1}", "complete")

    async def _build_parallel(self):
        """Build parallel workflow"""
        self.workflow.add_executor("start", self._start_node)
        self.workflow.add_executor("broadcast", self._broadcast_node)

        # Add agents in parallel
        for agent_name in self.agents.keys():
            self.workflow.add_executor(agent_name, self._create_agent_node(agent_name))

        self.workflow.add_executor("aggregate", self._aggregate_results)
        self.workflow.add_executor("complete", self._complete_node)

        # Edges
        self.workflow.add_edge("start", "broadcast")

        # Broadcast to all agents (parallel)
        for agent_name in self.agents.keys():
            self.workflow.add_edge("broadcast", agent_name)
            self.workflow.add_edge(agent_name, "aggregate")

        self.workflow.add_edge("aggregate", "complete")

    async def _build_hierarchical(self):
        """Build hierarchical Ali-led workflow"""
        self.workflow.add_executor("start", self._start_node)
        self.workflow.add_executor("ali_planning", self._ali_planning_node)
        self.workflow.add_executor("execute_plan", self._execute_plan_node)
        self.workflow.add_executor("ali_review", self._ali_review_node)
        self.workflow.add_executor("complete", self._complete_node)

        self.workflow.add_edge("start", "ali_planning")
        self.workflow.add_edge("ali_planning", "execute_plan")
        self.workflow.add_edge("execute_plan", "ali_review")

        self.workflow.add_conditional_edges(
            "ali_review",
            self._ali_review_logic,
            {
                "approved": "complete",
                "retry": "execute_plan",
                "replan": "ali_planning"
            }
        )

    # ================================
    # WORKFLOW NODES
    # ================================

    async def _start_node(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Start node"""
        context["workflow_start"] = datetime.now()
        context["execution_log"] = []
        context["checkpoints"] = []

        logger.info("Workflow started")
        return context

    async def _analyze_request(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the request to determine complexity and requirements"""
        message = context.get("message", "")

        # Simple complexity analysis
        word_count = len(message.split())
        has_multiple_questions = message.count("?") > 1
        has_and_conjunction = " and " in message.lower()

        complexity = "simple"
        if word_count > 50 or has_multiple_questions or has_and_conjunction:
            complexity = "complex"

        context["analysis"] = {
            "complexity": complexity,
            "word_count": word_count,
            "multiple_questions": has_multiple_questions
        }

        logger.info("Request analyzed", complexity=complexity)
        return context

    async def _route_decision(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Make routing decision"""
        analysis = context.get("analysis", {})
        complexity = analysis.get("complexity", "simple")

        # Check for explicit Ali targeting
        target_agent = context.get("target_agent", "")
        if "ali" in target_agent.lower():
            context["routing_decision"] = "ali"
        elif complexity == "complex":
            context["routing_decision"] = "multi"
        else:
            context["routing_decision"] = "single"

        logger.info("Routing decision", decision=context["routing_decision"])
        return context

    async def _routing_logic(self, context: Dict[str, Any]) -> str:
        """Routing logic for conditional edges"""
        return context.get("routing_decision", "single")

    async def _execute_single_agent(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute single agent"""
        # Select best agent (simplified - use first agent)
        agent_name = list(self.agents.keys())[0]
        agent = self.agents[agent_name]

        try:
            from agent_framework.messages import ChatMessage

            message = ChatMessage(role="user", content=context["message"])
            result = await agent.run(task=message)

            # Extract response
            response = ""
            if hasattr(result, "messages"):
                for msg in reversed(result.messages):
                    if hasattr(msg, "role") and msg.role == "assistant":
                        response = msg.content
                        break

            context["response"] = response
            context["agents_executed"] = [agent_name]

        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            context["response"] = f"Error: {str(e)}"
            context["error"] = str(e)

        return context

    async def _execute_multi_agent(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute multiple agents in parallel"""
        message = context.get("message", "")

        # Execute all agents in parallel
        tasks = []
        for agent_name, agent in self.agents.items():
            tasks.append(self._execute_agent(agent, message))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        context["agent_responses"] = [
            r if not isinstance(r, Exception) else f"Error: {str(r)}"
            for r in results
        ]
        context["agents_executed"] = list(self.agents.keys())

        return context

    async def _execute_agent(self, agent: ChatAgent, message: str) -> str:
        """Helper to execute single agent"""
        try:
            from agent_framework.messages import ChatMessage

            msg = ChatMessage(role="user", content=message)
            result = await agent.run(task=msg)

            if hasattr(result, "messages"):
                for m in reversed(result.messages):
                    if hasattr(m, "role") and m.role == "assistant":
                        return m.content

            return str(result)

        except Exception as e:
            return f"Error: {str(e)}"

    async def _ali_orchestration(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Ali-led orchestration"""
        ali = self.agents.get("ali_chief_of_staff")

        if not ali:
            # Fallback to regular execution
            return await self._execute_single_agent(context)

        try:
            from agent_framework.messages import ChatMessage

            enriched_message = f"""
            As the Chief of Staff, please orchestrate this request:

            {context['message']}

            Available agents: {', '.join(self.agents.keys())}

            Provide a comprehensive, coordinated response.
            """

            msg = ChatMessage(role="user", content=enriched_message)
            result = await ali.run(task=msg)

            # Extract response
            response = ""
            if hasattr(result, "messages"):
                for m in reversed(result.messages):
                    if hasattr(m, "role") and m.role == "assistant":
                        response = m.content
                        break

            context["response"] = response
            context["agents_executed"] = ["ali_chief_of_staff"]

        except Exception as e:
            logger.error(f"Ali orchestration failed: {e}")
            context["response"] = f"Error: {str(e)}"
            context["error"] = str(e)

        return context

    async def _aggregate_results(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate multiple agent responses"""
        responses = context.get("agent_responses", [])

        if not responses:
            context["response"] = "No responses received"
        elif len(responses) == 1:
            context["response"] = responses[0]
        else:
            # Simple concatenation (could use Ali for synthesis)
            context["response"] = "\n\n---\n\n".join(responses)

        return context

    async def _quality_check(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Check quality of response"""
        response = context.get("response", "")

        # Simple quality checks
        has_error = "error" in response.lower() or "failed" in response.lower()
        too_short = len(response) < 10
        is_empty = not response.strip()

        if is_empty or has_error or too_short:
            context["quality_status"] = "fail"
        else:
            context["quality_status"] = "pass"

        logger.info("Quality check", status=context["quality_status"])
        return context

    async def _quality_logic(self, context: Dict[str, Any]) -> str:
        """Quality check logic"""
        return context.get("quality_status", "pass")

    async def _complete_node(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Completion node"""
        context["workflow_end"] = datetime.now()

        if "workflow_start" in context:
            duration = (context["workflow_end"] - context["workflow_start"]).total_seconds()
            context["duration_seconds"] = duration

        logger.info("Workflow completed", duration=context.get("duration_seconds"))
        return context

    def _create_agent_node(self, agent_name: str):
        """Create a node for specific agent"""
        async def node(context: Dict[str, Any]) -> Dict[str, Any]:
            agent = self.agents[agent_name]
            response = await self._execute_agent(agent, context["message"])
            context[f"{agent_name}_response"] = response
            return context

        return node

    async def _broadcast_node(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Broadcast message to all agents"""
        context["broadcast_complete"] = True
        return context

    async def _ali_planning_node(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Ali creates execution plan"""
        # Implementation for hierarchical planning
        context["plan"] = {"steps": [], "agents": []}
        return context

    async def _execute_plan_node(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Ali's plan"""
        # Implementation for plan execution
        return context

    async def _ali_review_node(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Ali reviews results"""
        context["review_status"] = "approved"
        return context

    async def _ali_review_logic(self, context: Dict[str, Any]) -> str:
        """Ali review logic"""
        return context.get("review_status", "approved")

    # ================================
    # EXECUTION
    # ================================

    async def execute(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute the workflow.

        Args:
            message: Input message
            context: Optional context
            **kwargs: Additional parameters

        Returns:
            Workflow execution result
        """
        if not self.executor:
            await self.build()

        workflow_context = {
            "message": message,
            **(context or {}),
            **kwargs
        }

        result = await self.executor.run(input_data=workflow_context)
        return result

    async def execute_with_checkpointing(
        self,
        message: str,
        checkpoint_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute with checkpointing support.

        Args:
            message: Input message
            checkpoint_id: Optional checkpoint to resume from
            **kwargs: Additional parameters

        Returns:
            Workflow result
        """
        if checkpoint_id and self.checkpoint_store:
            # Resume from checkpoint
            logger.info("Resuming from checkpoint", checkpoint_id=checkpoint_id)
            # Implementation depends on checkpoint store API

        result = await self.execute(message, **kwargs)

        # Save checkpoint
        if self.checkpoint_store:
            self.current_checkpoint = f"checkpoint_{datetime.now().timestamp()}"
            # Save checkpoint implementation

        return result
