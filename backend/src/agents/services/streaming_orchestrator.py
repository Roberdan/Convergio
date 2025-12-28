"""
STREAMING ORCHESTRATOR - Compatibility Wrapper
Uses the UnifiedOrchestrator for all functionality
"""

# Import compatibility adapter
from .unified_orchestrator_adapter import (
    StreamingOrchestrator as _StreamingOrchestrator,
    get_streaming_orchestrator,
)

# Re-export for backward compatibility
StreamingOrchestrator = _StreamingOrchestrator

__all__ = ["StreamingOrchestrator", "get_streaming_orchestrator"]