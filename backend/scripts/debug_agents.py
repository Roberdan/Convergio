#!/usr/bin/env python3
"""
Debug script to check agent loading
"""

from src.agents.services.agent_loader import DynamicAgentLoader

def debug_agent_loader():
    loader = DynamicAgentLoader("src/agents/definitions")
    agent_metadata = loader.scan_and_load_agents()
    
    print(f"🔍 Found {len(agent_metadata)} agents:")
    for agent_name, metadata in agent_metadata.items():
        print(f"  - {agent_name}: {metadata.description}")
    
    # Check specifically for ali
    ali_variants = [name for name in agent_metadata.keys() if 'ali' in name.lower()]
    print(f"\n🎯 Ali variants found: {ali_variants}")
    
    return agent_metadata

if __name__ == "__main__":
    debug_agent_loader()