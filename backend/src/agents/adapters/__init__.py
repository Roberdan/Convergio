"""
Framework Adapters Package
Provides unified interface for different agent frameworks.
"""

from .framework_adapter import (
    FrameworkAdapter,
    FrameworkType,
    AgentMessage,
    AgentResponse,
    MockFrameworkAdapter,
    create_adapter,
)
from .feature_flag import (
    FrameworkFeatureFlag,
    FrameworkConfig,
    FrameworkSelection,
    get_feature_flag,
    reset_feature_flag,
    use_agent_framework,
)

# Optional adapter imports
try:
    from .autogen_adapter import AutoGenAdapter, AUTOGEN_AVAILABLE
except ImportError:
    AutoGenAdapter = None
    AUTOGEN_AVAILABLE = False

try:
    from .agent_framework_adapter import AgentFrameworkAdapter, AGENT_FRAMEWORK_AVAILABLE
except ImportError:
    AgentFrameworkAdapter = None
    AGENT_FRAMEWORK_AVAILABLE = False

__all__ = [
    # Core types
    "FrameworkAdapter",
    "FrameworkType",
    "AgentMessage",
    "AgentResponse",
    "MockFrameworkAdapter",
    "create_adapter",
    # Feature flag
    "FrameworkFeatureFlag",
    "FrameworkConfig",
    "FrameworkSelection",
    "get_feature_flag",
    "reset_feature_flag",
    "use_agent_framework",
    # Adapters
    "AutoGenAdapter",
    "AgentFrameworkAdapter",
    "AUTOGEN_AVAILABLE",
    "AGENT_FRAMEWORK_AVAILABLE",
]
