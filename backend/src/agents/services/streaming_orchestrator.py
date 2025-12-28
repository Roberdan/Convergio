"""
STREAMING ORCHESTRATOR - Compatibility Wrapper
Uses the UnifiedOrchestrator for all functionality
"""

# Import compatibility adapter
from .unified_orchestrator_adapter import StreamingOrchestrator as _StreamingOrchestrator

# Re-export for backward compatibility
StreamingOrchestrator = _StreamingOrchestrator