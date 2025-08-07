#!/usr/bin/env python3
"""
Test script for Agent Loader System
Verifica che il sistema possa caricare tutti i 41 agenti correttamente
"""

import asyncio
import pytest
import sys
import os
from pathlib import Path

from src.agents.services.agent_loader import DynamicAgentLoader
import structlog

# Setup basic logging
structlog.configure(
    processors=[structlog.dev.ConsoleRenderer()],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

@pytest.mark.asyncio
async def test_agent_loader():
    """Test the agent loader system"""
    
    logger.info("🧪 TESTING AGENT LOADER SYSTEM")
    
    # Initialize agent loader
    agents_directory = "src/agents/definitions"
    loader = DynamicAgentLoader(agents_directory)
    
    try:
        # Test 1: Scan and load all agents
        logger.info("📁 Test 1: Scanning agent definitions directory")
        agents = loader.scan_and_load_agents()
        
        if not agents:
            logger.error("❌ No agents loaded!")
            return False
        
        logger.info(f"✅ Loaded {len(agents)} agents successfully")
        
        # Test 2: Verify agent metadata
        logger.info("📋 Test 2: Verifying agent metadata")
        
        strategic_agents = []
        technology_agents = []
        other_agents = []
        
        for key, agent in agents.items():
            if "Strategic" in agent.tier:
                strategic_agents.append(agent.name)
            elif "Technology" in agent.tier:
                technology_agents.append(agent.name)
            else:
                other_agents.append(agent.name)
                
        logger.info(f"📊 Agent breakdown:")
        logger.info(f"   Strategic Leadership: {len(strategic_agents)}")
        logger.info(f"   Technology & Engineering: {len(technology_agents)}")
        logger.info(f"   Other specializations: {len(other_agents)}")
        
        # Test 3: Generate Ali knowledge base
        logger.info("🧠 Test 3: Generating Ali knowledge base")
        knowledge_base = loader.generate_ali_knowledge_base()
        
        if len(knowledge_base) < 1000:  # Should be substantial
            logger.warning("⚠️ Knowledge base seems too small")
        else:
            logger.info(f"✅ Knowledge base generated ({len(knowledge_base)} characters)")
            
        # Test 4: Check specific key agents
        logger.info("🔍 Test 4: Checking key agents")
        key_agents_to_check = [
            "ali_chief_of_staff",
            "satya_board_of_directors", 
            "baccio_tech_architect",
            "luca_security_expert"
        ]
        
        missing_agents = []
        for agent_key in key_agents_to_check:
            if agent_key not in agents:
                missing_agents.append(agent_key)
            else:
                agent = agents[agent_key]
                logger.info(f"   ✅ {agent.name}: {agent.description[:60]}...")
        
        if missing_agents:
            logger.error(f"❌ Missing key agents: {missing_agents}")
            return False
            
        # Test 5: Verify agent definitions have required fields
        logger.info("📝 Test 5: Validating agent definition completeness")
        
        incomplete_agents = []
        for key, agent in agents.items():
            if not agent.name or not agent.description or not agent.persona:
                incomplete_agents.append(key)
                
        if incomplete_agents:
            logger.warning(f"⚠️ Incomplete agent definitions: {incomplete_agents}")
        else:
            logger.info("✅ All agent definitions complete")
            
        # Final summary
        logger.info("🎯 AGENT LOADER TEST RESULTS:")
        logger.info(f"   Total agents loaded: {len(agents)}")
        logger.info(f"   Key agents verified: {len(key_agents_to_check) - len(missing_agents)}/{len(key_agents_to_check)}")
        logger.info(f"   Knowledge base size: {len(knowledge_base)} chars")
        logger.info(f"   Complete definitions: {len(agents) - len(incomplete_agents)}/{len(agents)}")
        
        success = len(missing_agents) == 0 and len(agents) >= 40
        if success:
            logger.info("✅ AGENT LOADER SYSTEM: ALL TESTS PASSED")
        else:
            logger.error("❌ AGENT LOADER SYSTEM: SOME TESTS FAILED")
            
        return success
        
    except Exception as e:
        logger.error(f"❌ Agent loader test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_agent_loader())
    sys.exit(0 if result else 1)