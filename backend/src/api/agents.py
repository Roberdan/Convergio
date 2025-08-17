"""
🤖 Convergio - AI Agents API
Modularized version - imports from submodules
"""

# Import the router from the modularized agents package
from agents.router import router

# Re-export for backward compatibility
__all__ = ['router']