"""
Agent Factory
Creates AssistantAgent instances with appropriate tools and system messages.
"""

from typing import Dict, Any
import structlog

# AutoGen imports with fallback
try:
    from autogen_agentchat.agents import AssistantAgent
    from autogen_ext.models.openai import OpenAIChatCompletionClient
    AUTOGEN_AVAILABLE = True
except ImportError:
    AssistantAgent = None
    OpenAIChatCompletionClient = None
    AUTOGEN_AVAILABLE = False

from ..agent_loader import DynamicAgentLoader
from .agent_instructions import optimize_agent_prompt


logger = structlog.get_logger()


def create_business_agents(
    loader: DynamicAgentLoader,
    model_client: Any,
) -> Dict[str, Any]:
    """Create business agents. Returns empty dict if AutoGen is not available."""
    if not AUTOGEN_AVAILABLE:
        logger.debug("Legacy AutoGen business agents not created (using Agent Framework)")
        return {}

    agents: Dict[str, Any] = {}

    for agent_id, metadata in loader.agent_metadata.items():
        original_prompt = loader._build_system_message(metadata)
        # Optimize prompts for conciseness
        system_message = optimize_agent_prompt(original_prompt)
        tools = _select_tools_for_agent(agent_id)
        agent = AssistantAgent(
            name=agent_id,
            model_client=model_client,
            system_message=system_message,
            tools=tools,
        )
        agents[agent_id] = agent
    logger.info("Business agents created with optimized prompts", count=len(agents))
    return agents


def _select_tools_for_agent(agent_id: str):
    """Select appropriate tool functions for each agent"""
    try:
        from ..tools.autogen_tools import (
            web_search,
            query_talents,
            business_intelligence,
            get_amy_tools,
            get_ali_tools,
            get_data_analysis_tools,
            get_market_strategy_tools,
            get_default_tools
        )
        
        # Ali gets ALL tools including web access
        if agent_id == "ali_chief_of_staff":
            return get_ali_tools()
        
        # Amy CFO needs financial tools
        if agent_id == "amy_cfo":
            logger.info("🎯 Configuring Amy CFO with web search for financial data")
            return get_amy_tools()
        
        # Diana needs performance and financial tools
        if agent_id == "diana_performance_dashboard":
            return get_amy_tools()
        
        # Project Manager needs full database access
        if agent_id == "davide-project-manager":
            return [web_search, query_talents, business_intelligence]
        
        # Market/Strategy agents need web search and business intelligence
        if any(term in agent_id.lower() for term in ["market", "strategy", "mckinsey", "investor"]):
            return get_market_strategy_tools()
        
        # Data/Analysis agents get analysis tools
        if "data" in agent_id.lower() or "analysis" in agent_id.lower():
            return get_data_analysis_tools()
        
        # Technical agents need web search for documentation
        if any(term in agent_id.lower() for term in ["tech", "architect", "security", "dev"]):
            return [web_search, business_intelligence]
        
        # Default: Give all agents basic tools
        return get_default_tools()
        
    except Exception as e:
        logger.warning("Tool selection failed", agent_id=agent_id, error=str(e))
        return []


