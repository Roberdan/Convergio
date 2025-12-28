"""
GRAPHFLOW ORCHESTRATOR - Compatibility Wrapper
Uses the UnifiedOrchestrator for all functionality
"""

# Import compatibility adapter
from .unified_orchestrator_adapter import (
    GraphFlowOrchestrator as _GraphFlowOrchestrator,
    get_graphflow_orchestrator,
)

# Re-export for backward compatibility
GraphFlowOrchestrator = _GraphFlowOrchestrator

__all__ = ["GraphFlowOrchestrator", "get_graphflow_orchestrator"]