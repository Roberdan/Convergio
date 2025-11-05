"""
Agent Framework Loader - Creates ChatAgent instances from markdown definitions
Extends DynamicAgentLoader to support Microsoft Agent Framework
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import structlog

try:
    from agent_framework import ChatAgent
    from agent_framework.openai import OpenAIChatClient
    from agent_framework.azure import AzureOpenAIChatClient
    AGENT_FRAMEWORK_AVAILABLE = True
except ImportError:
    AGENT_FRAMEWORK_AVAILABLE = False
    ChatAgent = None
    OpenAIChatClient = None
    AzureOpenAIChatClient = None

from src.agents.services.agent_loader import DynamicAgentLoader, AgentMetadata
from src.core.agent_framework_config import get_agent_framework_config

logger = structlog.get_logger()


class AgentFrameworkLoader(DynamicAgentLoader):
    """
    Enhanced agent loader that creates ChatAgent instances for Agent Framework.

    Extends DynamicAgentLoader to support both AutoGen (legacy) and Agent Framework (new).
    """

    def __init__(self, agents_directory: str, enable_hot_reload: bool = True):
        super().__init__(agents_directory, enable_hot_reload)

        if not AGENT_FRAMEWORK_AVAILABLE:
            logger.warning("Agent Framework not available, falling back to AutoGen")
            self.framework = "autogen"
        else:
            self.framework = "agent_framework"
            logger.info("Agent Framework loader initialized")

        self.config = get_agent_framework_config()

    def create_chat_agents(
        self,
        chat_client: Any,
        tools: List[Any] = None
    ) -> Dict[str, ChatAgent]:
        """
        Create ChatAgent instances from loaded metadata.

        Args:
            chat_client: Agent Framework ChatClient (OpenAI, Azure, etc.)
            tools: List of tools decorated with @ai_function

        Returns:
            Dictionary of ChatAgent instances
        """
        if not AGENT_FRAMEWORK_AVAILABLE:
            logger.error("Agent Framework not installed")
            raise ImportError(
                "Microsoft Agent Framework not installed. "
                "Install with: pip install agent-framework --pre"
            )

        agents = {}

        for key, metadata in self.agent_metadata.items():
            try:
                # Build instructions (equivalent to system_message)
                instructions = self._build_instructions(metadata)

                # Special handling for Ali - add knowledge base
                if metadata.key == "ali_chief_of_staff":
                    try:
                        kb = self.generate_ali_knowledge_base()
                        instructions = f"{instructions}\n\n---\nALI KNOWLEDGE BASE:\n{kb}"
                    except Exception as e:
                        logger.warning(f"Failed to build Ali knowledge base: {e}")

                # Create ChatAgent using the chat_client's create_agent method
                # This is the correct pattern according to Microsoft Agent Framework examples
                agent = chat_client.create_agent(
                    name=metadata.key,
                    instructions=instructions,
                    tools=tools or [],
                    # Note: Some config options may not be directly supported
                    # Agent Framework handles max_iterations at workflow level
                )

                agents[key] = agent

                logger.debug(
                    "Created ChatAgent",
                    name=metadata.name,
                    class_name=metadata.class_name,
                    tools_count=len(tools or []),
                    max_iterations=self.config.default_max_iterations
                )

            except Exception as e:
                logger.error(
                    f"Failed to create ChatAgent: {metadata.name}",
                    error=str(e)
                )
                continue

        logger.info(
            "ChatAgents created",
            total=len(agents),
            tools_count=len(tools or []),
            framework="Agent Framework"
        )

        return agents

    def _build_instructions(self, metadata: AgentMetadata) -> str:
        """
        Build comprehensive instructions for ChatAgent.

        Args:
            metadata: Agent metadata from markdown file

        Returns:
            Complete instructions string
        """
        return f"""You are {metadata.class_name}, an expert agent in the Convergio ecosystem.

SPECIALIZATION: {metadata.description}

PERSONA & IDENTITY:
{metadata.persona}

EXPERTISE AREAS: {', '.join(metadata.expertise_keywords)}
TIER: {metadata.tier}
AVAILABLE TOOLS: {', '.join(metadata.tools) if metadata.tools else 'Standard communication tools'}

🚨 MANDATORY: Follow the Intelligent Decision Framework from CommonValuesAndPrinciples.md:
1. ANALYZE user intent to understand their true goal
2. DECIDE data sources: Convergio DB/Vector for internal data, AI for analysis, or both
3. RESPOND autonomously or escalate to Ali if cross-functional
4. CITE your data sources and provide confidence levels

OPERATIONAL GUIDELINES:
- Use REAL DATA from Convergio DB/Vector when available
- Use AI intelligence for strategic analysis and recommendations
- NEVER give generic responses - always use real data or intelligent AI
- Ask for clarification if intent is unclear
- Escalate to Ali for cross-functional needs
- Always provide professional, accurate, and helpful responses aligned with Convergio values
- Focus on delivering actionable insights and solutions within your area of expertise
- Collaborate effectively with other agents when needed
- Maintain the highest standards of quality and professionalism
- If a request is outside your expertise, suggest the appropriate specialist agent

MULTI-TURN CAPABILITIES:
- You can engage in multi-turn conversations by default
- Continue tool execution until you have a complete answer
- Don't stop after a single tool call - iterate as needed
- Maximum {self.config.default_max_iterations} iterations per conversation

Remember: You are part of a coordinated ecosystem of 48+ specialist agents working together to empower every person and organization to achieve more."""

    def create_hybrid_agents(
        self,
        chat_client: Any,
        model_client: Any,
        tools: List[Any] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Create both AutoGen and Agent Framework agents for gradual migration.

        Args:
            chat_client: Agent Framework ChatClient
            model_client: AutoGen model client
            tools: List of tools

        Returns:
            Dictionary containing both agent types
        """
        result = {
            "agent_framework": {},
            "autogen": {},
            "metadata": self.agent_metadata
        }

        # Create Agent Framework agents if available
        if AGENT_FRAMEWORK_AVAILABLE:
            try:
                af_tools = self._convert_tools_for_agent_framework(tools)
                result["agent_framework"] = self.create_chat_agents(
                    chat_client,
                    af_tools
                )
                logger.info(f"Created {len(result['agent_framework'])} Agent Framework agents")
            except Exception as e:
                logger.error(f"Failed to create Agent Framework agents: {e}")

        # Create AutoGen agents as fallback
        try:
            result["autogen"] = self.create_autogen_agents(
                model_client,
                tools
            )
            logger.info(f"Created {len(result['autogen'])} AutoGen agents")
        except Exception as e:
            logger.error(f"Failed to create AutoGen agents: {e}")

        return result

    def _convert_tools_for_agent_framework(self, tools: List[Any]) -> List[Any]:
        """
        Convert AutoGen tools to Agent Framework format.

        Args:
            tools: List of AutoGen FunctionTool instances

        Returns:
            List of Agent Framework tools
        """
        # For now, assume tools are already @ai_function decorated
        # In Phase 4, we'll fully migrate tool definitions
        if not tools:
            return []

        converted_tools = []

        for tool in tools:
            # If tool is already AF-compatible, keep it
            if hasattr(tool, "__name__") and hasattr(tool, "__annotations__"):
                converted_tools.append(tool)
            else:
                # Log incompatible tool
                logger.warning(
                    f"Tool {tool} may not be compatible with Agent Framework, skipping"
                )

        return converted_tools

    def get_chat_client(self, provider: str = "openai") -> Any:
        """
        Get appropriate chat client for Agent Framework.

        Args:
            provider: Model provider (openai, azure, etc.)

        Returns:
            ChatClient instance
        """
        if not AGENT_FRAMEWORK_AVAILABLE:
            raise ImportError("Agent Framework not available")

        if provider.lower() == "openai":
            # OpenAIChatClient constructor according to Microsoft examples
            # It auto-reads from OPENAI_API_KEY env var if not provided
            client_kwargs = {}
            if hasattr(self.config, 'api_key') and self.config.api_key:
                client_kwargs['api_key'] = self.config.api_key
            if hasattr(self.config, 'model_name') and self.config.model_name:
                client_kwargs['model'] = self.config.model_name

            return OpenAIChatClient(**client_kwargs)

        elif provider.lower() == "azure":
            # AzureOpenAIChatClient uses Azure CLI credentials by default
            from azure.identity import AzureCliCredential
            return AzureOpenAIChatClient(credential=AzureCliCredential())

        else:
            raise ValueError(f"Unsupported provider: {provider}")


# Global instance
_backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
agent_framework_loader = AgentFrameworkLoader(
    os.path.join(_backend_dir, "agents", "definitions")
)
