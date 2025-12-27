"""GroupChat service package exports."""

# Core types always available
from .types import GroupChatResult

# Optional imports - these may fail if dependencies aren't available
try:
    from .initializer import initialize_model_client, initialize_agent_loader
except ImportError:
    initialize_model_client = None  # type: ignore
    initialize_agent_loader = None  # type: ignore

try:
    from .agent_factory import create_business_agents
except ImportError:
    create_business_agents = None  # type: ignore

try:
    from .selection_policy import select_key_agents
except ImportError:
    select_key_agents = None  # type: ignore

try:
    from .runner import run_groupchat_stream
except ImportError:
    run_groupchat_stream = None  # type: ignore

try:
    from .rag import build_memory_context
except ImportError:
    build_memory_context = None  # type: ignore

try:
    from .context import enhance_message_with_context
except ImportError:
    enhance_message_with_context = None  # type: ignore

try:
    from .setup import create_groupchat
except ImportError:
    create_groupchat = None  # type: ignore

try:
    from .orchestrator_conversation import orchestrate_conversation_impl, direct_agent_conversation_impl
except ImportError:
    orchestrate_conversation_impl = None  # type: ignore
    direct_agent_conversation_impl = None  # type: ignore

__all__ = [
    "GroupChatResult",
    "initialize_model_client",
    "initialize_agent_loader",
    "create_business_agents",
    "select_key_agents",
    "run_groupchat_stream",
    "build_memory_context",
    "enhance_message_with_context",
    "create_groupchat",
    "orchestrate_conversation_impl",
    "direct_agent_conversation_impl",
]


