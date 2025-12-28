"""
GRAPHFLOW ORCHESTRATOR - Compatibility Wrapper
Uses the UnifiedOrchestrator for all functionality
"""

# Import compatibility adapter
from .unified_orchestrator_adapter import GraphFlowOrchestrator as _GraphFlowOrchestrator

# Re-export for backward compatibility
GraphFlowOrchestrator = _GraphFlowOrchestrator