"""
Workflow Builder - Fluent API for building complex workflows
"""

from typing import Dict, List, Any, Optional, Callable
import structlog

try:
    from agent_framework import Workflow
    AGENT_FRAMEWORK_AVAILABLE = True
except ImportError:
    AGENT_FRAMEWORK_AVAILABLE = False
    Workflow = None

logger = structlog.get_logger()


class WorkflowBuilder:
    """
    Fluent builder for creating complex workflows.

    Example:
        workflow = (WorkflowBuilder()
            .add_node("start", start_handler)
            .add_node("process", process_handler)
            .add_edge("start", "process")
            .add_conditional("process", decision_fn, {"yes": "approve", "no": "reject"})
            .build())
    """

    def __init__(self):
        if not AGENT_FRAMEWORK_AVAILABLE:
            raise ImportError("Agent Framework not available")

        self.workflow = Workflow()
        self.nodes: Dict[str, Callable] = {}
        self.edges: List[tuple] = []
        self.conditional_edges: List[tuple] = []

        logger.info("Workflow Builder initialized")

    def add_node(
        self,
        name: str,
        handler: Callable,
        description: Optional[str] = None
    ) -> "WorkflowBuilder":
        """
        Add a node to the workflow.

        Args:
            name: Node name (unique identifier)
            handler: Async function to execute at this node
            description: Optional description

        Returns:
            Self for chaining
        """
        self.nodes[name] = handler
        self.workflow.add_executor(name, handler)

        logger.debug("Node added", name=name, description=description)
        return self

    def add_edge(self, from_node: str, to_node: str) -> "WorkflowBuilder":
        """
        Add an unconditional edge between nodes.

        Args:
            from_node: Source node name
            to_node: Destination node name

        Returns:
            Self for chaining
        """
        self.edges.append((from_node, to_node))
        self.workflow.add_edge(from_node, to_node)

        logger.debug("Edge added", from_node=from_node, to_node=to_node)
        return self

    def add_conditional(
        self,
        from_node: str,
        decision_function: Callable,
        destinations: Dict[str, str]
    ) -> "WorkflowBuilder":
        """
        Add conditional edges based on decision function.

        Args:
            from_node: Source node name
            decision_function: Function that returns destination key
            destinations: Mapping of decision results to node names

        Returns:
            Self for chaining
        """
        self.conditional_edges.append((from_node, decision_function, destinations))
        self.workflow.add_conditional_edges(from_node, decision_function, destinations)

        logger.debug(
            "Conditional edges added",
            from_node=from_node,
            destinations=list(destinations.keys())
        )
        return self

    def add_parallel_nodes(
        self,
        node_handlers: Dict[str, Callable],
        join_node: Optional[str] = None
    ) -> "WorkflowBuilder":
        """
        Add multiple nodes that execute in parallel.

        Args:
            node_handlers: Dictionary of node names to handlers
            join_node: Optional node where all parallel branches join

        Returns:
            Self for chaining
        """
        for name, handler in node_handlers.items():
            self.add_node(name, handler)

        if join_node:
            for name in node_handlers.keys():
                self.add_edge(name, join_node)

        logger.debug("Parallel nodes added", count=len(node_handlers))
        return self

    def add_sequential_chain(
        self,
        node_handlers: List[tuple]
    ) -> "WorkflowBuilder":
        """
        Add a sequential chain of nodes.

        Args:
            node_handlers: List of (name, handler) tuples in order

        Returns:
            Self for chaining
        """
        for i, (name, handler) in enumerate(node_handlers):
            self.add_node(name, handler)

            if i > 0:
                prev_name = node_handlers[i-1][0]
                self.add_edge(prev_name, name)

        logger.debug("Sequential chain added", length=len(node_handlers))
        return self

    def add_loop(
        self,
        nodes: List[str],
        condition_fn: Callable,
        exit_node: str
    ) -> "WorkflowBuilder":
        """
        Add a loop structure to the workflow.

        Args:
            nodes: List of node names in the loop
            condition_fn: Function to determine continue/exit
            exit_node: Node to jump to when exiting loop

        Returns:
            Self for chaining
        """
        # Create loop edges
        for i in range(len(nodes) - 1):
            self.add_edge(nodes[i], nodes[i+1])

        # Add conditional back to start or exit
        self.add_conditional(
            nodes[-1],
            condition_fn,
            {"continue": nodes[0], "exit": exit_node}
        )

        logger.debug("Loop added", nodes=nodes, exit_node=exit_node)
        return self

    def add_error_handler(
        self,
        error_node: str,
        handler: Callable
    ) -> "WorkflowBuilder":
        """
        Add an error handling node.

        Args:
            error_node: Name of error handler node
            handler: Error handling function

        Returns:
            Self for chaining
        """
        self.add_node(error_node, handler)

        # In a real implementation, this would configure error handling
        logger.debug("Error handler added", error_node=error_node)
        return self

    def build(self) -> Workflow:
        """
        Build and return the final workflow.

        Returns:
            Configured Workflow instance
        """
        logger.info(
            "Workflow built",
            nodes=len(self.nodes),
            edges=len(self.edges),
            conditional_edges=len(self.conditional_edges)
        )

        return self.workflow

    def visualize(self) -> str:
        """
        Generate a text visualization of the workflow.

        Returns:
            ASCII diagram of workflow
        """
        lines = ["Workflow Visualization", "=" * 50, ""]

        # List nodes
        lines.append("Nodes:")
        for name in self.nodes.keys():
            lines.append(f"  - {name}")

        lines.append("")

        # List edges
        lines.append("Edges:")
        for from_node, to_node in self.edges:
            lines.append(f"  {from_node} → {to_node}")

        lines.append("")

        # List conditional edges
        if self.conditional_edges:
            lines.append("Conditional Edges:")
            for from_node, _, destinations in self.conditional_edges:
                for key, to_node in destinations.items():
                    lines.append(f"  {from_node} --[{key}]--> {to_node}")

        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """
        Export workflow structure as dictionary.

        Returns:
            Dictionary representation of workflow
        """
        return {
            "nodes": list(self.nodes.keys()),
            "edges": [{"from": f, "to": t} for f, t in self.edges],
            "conditional_edges": [
                {
                    "from": f,
                    "destinations": d
                }
                for f, _, d in self.conditional_edges
            ]
        }
