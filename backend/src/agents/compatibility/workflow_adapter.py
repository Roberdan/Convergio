"""
Workflow Adapter - Provides compatibility between AutoGen teams and Agent Framework workflows
"""

from typing import Any, Dict, List, Optional, Callable
import structlog

logger = structlog.get_logger()


class WorkflowAdapter:
    """
    Adapter to provide compatibility between AutoGen GroupChat/Team patterns
    and Agent Framework Workflow during migration.
    """

    def __init__(self):
        self.agents: Dict[str, Any] = {}
        self.workflow: Optional[Any] = None
        self.framework: str = "autogen"  # Start with autogen

    def add_agent(self, name: str, agent: Any):
        """Add agent to workflow (works for both frameworks)"""
        self.agents[name] = agent
        logger.debug(f"Added agent to workflow: {name}")

    def get_agent(self, name: str) -> Optional[Any]:
        """Get agent by name"""
        return self.agents.get(name)

    def create_autogen_groupchat(
        self, max_rounds: int = 10, termination_markers: Optional[List[str]] = None
    ) -> Any:
        """
        Create AutoGen RoundRobinGroupChat from agents.

        Args:
            max_rounds: Maximum conversation rounds
            termination_markers: List of termination strings

        Returns:
            AutoGen RoundRobinGroupChat instance
        """
        try:
            from autogen_agentchat.teams import RoundRobinGroupChat
            from autogen_agentchat.conditions import (
                MaxMessageTermination,
                TextMentionTermination,
            )

            if not self.agents:
                raise ValueError("No agents added to workflow")

            # Build termination condition
            termination = MaxMessageTermination(max_rounds)

            if termination_markers:
                for marker in termination_markers:
                    termination = termination | TextMentionTermination(marker)

            # Create GroupChat
            group_chat = RoundRobinGroupChat(
                participants=list(self.agents.values()),
                termination_condition=termination,
                max_turns=max_rounds,
            )

            self.framework = "autogen"
            logger.info(
                f"Created AutoGen GroupChat with {len(self.agents)} agents",
                max_rounds=max_rounds,
            )

            return group_chat

        except ImportError:
            logger.error("AutoGen not installed")
            raise
        except Exception as e:
            logger.error(f"Failed to create AutoGen GroupChat: {e}")
            raise

    def create_agent_framework_workflow(self) -> Any:
        """
        Create Agent Framework Workflow from agents.

        Returns:
            Agent Framework Workflow instance
        """
        try:
            from agent_framework import Workflow

            if not self.agents:
                raise ValueError("No agents added to workflow")

            # Create workflow
            workflow = Workflow()

            # Add agents as executors
            for name, agent in self.agents.items():
                workflow.add_executor(name, agent)

            # Add routing logic (simplified for now)
            workflow.add_executor("router", self._default_router)

            # Define basic edges
            workflow.add_edge("start", "router")

            self.workflow = workflow
            self.framework = "agent_framework"

            logger.info(
                f"Created Agent Framework Workflow with {len(self.agents)} agents"
            )

            return workflow

        except ImportError:
            logger.error("Agent Framework not installed")
            raise
        except Exception as e:
            logger.error(f"Failed to create Agent Framework Workflow: {e}")
            raise

    async def _default_router(self, context: Dict[str, Any]) -> str:
        """
        Default routing function for workflows.

        Args:
            context: Execution context

        Returns:
            Name of next agent to execute
        """
        # Simple round-robin routing
        agent_names = list(self.agents.keys())
        if not agent_names:
            return "END"

        current_index = context.get("current_agent_index", 0)
        next_index = (current_index + 1) % len(agent_names)

        context["current_agent_index"] = next_index

        return agent_names[next_index]

    async def execute(self, message: str, **kwargs) -> Any:
        """
        Execute workflow with message (framework-agnostic).

        Args:
            message: Input message
            **kwargs: Additional arguments

        Returns:
            Execution result
        """
        if self.framework == "autogen":
            return await self._execute_autogen(message, **kwargs)
        elif self.framework == "agent_framework":
            return await self._execute_agent_framework(message, **kwargs)
        else:
            raise ValueError(f"Unknown framework: {self.framework}")

    async def _execute_autogen(self, message: str, **kwargs) -> Any:
        """Execute using AutoGen GroupChat"""
        from autogen_agentchat.messages import TextMessage

        if not hasattr(self, "group_chat") or not self.group_chat:
            self.group_chat = self.create_autogen_groupchat()

        task = TextMessage(content=message, source="user")
        result = await self.group_chat.run(task=task)

        return result

    async def _execute_agent_framework(self, message: str, **kwargs) -> Any:
        """Execute using Agent Framework Workflow"""
        if not self.workflow:
            self.workflow = self.create_agent_framework_workflow()

        # Execute workflow
        result = await self.workflow.run(input_data={"message": message})

        return result

    def get_stats(self) -> Dict[str, Any]:
        """Get workflow statistics"""
        return {
            "framework": self.framework,
            "agent_count": len(self.agents),
            "agents": list(self.agents.keys()),
        }

    def __repr__(self) -> str:
        return f"WorkflowAdapter(framework={self.framework}, agents={len(self.agents)})"
