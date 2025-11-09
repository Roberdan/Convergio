"""
Compatibility Layer for AutoGen to Agent Framework Migration
Provides gradual migration path while maintaining backward compatibility
"""

# Export compatibility utilities
from .agent_adapter import AgentAdapter
from .message_adapter import MessageAdapter
from .workflow_adapter import WorkflowAdapter

__all__ = [
    'AgentAdapter',
    'MessageAdapter',
    'WorkflowAdapter',
]
