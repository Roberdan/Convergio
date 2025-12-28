"""
ALI SWARM ORCHESTRATOR - Compatibility Wrapper
Uses the UnifiedOrchestrator for all functionality
"""

# Import compatibility adapter
from .unified_orchestrator_adapter import AliSwarmOrchestrator as _AliSwarmOrchestrator

# Re-export for backward compatibility  
AliSwarmOrchestrator = _AliSwarmOrchestrator