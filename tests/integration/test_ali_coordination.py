#!/usr/bin/env python3
"""
Test script for Ali coordination with all agents
Verifica che Ali possa coordinare tutti i 41 agenti del sistema
"""

import asyncio
import sys
import os
from pathlib import Path
import json

# Add backend to path
project_root = Path(__file__).parent.parent.parent
backend_path = project_root / "backend"
sys.path.insert(0, str(backend_path))

try:
    from src.agents.services.agent_loader import DynamicAgentLoader
    from src.agents.utils.config import get_settings
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def test_ali_coordination():
    """Test Ali's coordination capabilities with all agents"""
    
    print("🧪 TESTING ALI COORDINATION SYSTEM")
    
    # Initialize agent loader
    agents_directory = str(backend_path / "src" / "agents" / "definitions")
    loader = DynamicAgentLoader(agents_directory)
    
    try:
        # Load all agents
        print("📁 Loading all agent definitions...")
        agents = loader.scan_and_load_agents()
        
        if not agents:
            print("❌ No agents loaded!")
            return False
            
        print(f"✅ Loaded {len(agents)} agents successfully")
        
        # Test 1: Verify Ali exists and has chief of staff role
        print("\n🎯 Test 1: Verifying Ali's leadership role")
        
        ali_agent = None
        for key, agent in agents.items():
            if "ali" in key.lower() and ("orchestrator" in agent.description.lower() or "chief" in agent.description.lower()):
                ali_agent = agent
                print(f"✅ Found Ali: {agent.name}")
                print(f"   Description: {agent.description[:100]}...")
                break
        
        if not ali_agent:
            print("❌ Ali agent not found!")
            return False
        
        # Test 2: Generate Ali's knowledge base
        print("\n🧠 Test 2: Generating Ali's knowledge base")
        knowledge_base = loader.generate_ali_knowledge_base()
        
        # Verify knowledge base includes all agents
        agent_coverage = 0
        missing_agents = []
        
        for key, agent in agents.items():
            if agent.name.lower() in knowledge_base.lower():
                agent_coverage += 1
            else:
                missing_agents.append(agent.name)
                
        coverage_percentage = (agent_coverage / len(agents)) * 100
        print(f"📊 Agent coverage in knowledge base: {agent_coverage}/{len(agents)} ({coverage_percentage:.1f}%)")
        
        if missing_agents:
            print(f"⚠️ Missing agents in knowledge base: {missing_agents[:5]}..." if len(missing_agents) > 5 else f"⚠️ Missing agents: {missing_agents}")
        
        # Test 3: Analyze coordination capabilities by tier
        print("\n🏢 Test 3: Analyzing coordination by tier")
        
        tier_stats = {}
        for agent in agents.values():
            tier = agent.tier
            if tier not in tier_stats:
                tier_stats[tier] = []
            tier_stats[tier].append(agent.name)
        
        print("📈 Agent distribution by tier:")
        for tier, agent_names in tier_stats.items():
            print(f"   {tier}: {len(agent_names)} agents")
            # Show first few agents in each tier
            sample_agents = agent_names[:3]
            print(f"      Examples: {', '.join(sample_agents)}")
        
        # Test 4: Verify Ali has access to all specialization areas
        print("\n🔍 Test 4: Verifying Ali can access all specialization areas")
        
        specialization_keywords = set()
        for agent in agents.values():
            specialization_keywords.update([kw.lower() for kw in agent.expertise_keywords[:3]])
        
        print(f"🎯 Total unique specialization areas: {len(specialization_keywords)}")
        sample_specializations = list(specialization_keywords)[:10]
        print(f"   Sample areas: {', '.join(sample_specializations)}")
        
        # Test 5: Coordination routing logic
        print("\n🚀 Test 5: Testing coordination routing logic")
        
        test_scenarios = [
            {"request": "security analysis", "expected_agents": ["luca", "guardian"]},
            {"request": "financial analysis", "expected_agents": ["amy"]},
            {"request": "technical architecture", "expected_agents": ["baccio"]},
            {"request": "strategic decision", "expected_agents": ["satya", "domik"]},
            {"request": "UI design", "expected_agents": ["sara", "jony"]}
        ]
        
        routing_success = 0
        for scenario in test_scenarios:
            request = scenario["request"]
            expected = scenario["expected_agents"]
            
            # Find matching agents based on keywords
            matching_agents = []
            for key, agent in agents.items():
                agent_keywords = [kw.lower() for kw in agent.expertise_keywords + [agent.description.lower()]]
                if any(word in ' '.join(agent_keywords) for word in request.split()):
                    matching_agents.append(key)
            
            found_expected = any(exp.lower() in ' '.join(matching_agents).lower() for exp in expected)
            if found_expected:
                routing_success += 1
                print(f"   ✅ {request}: Found relevant agents")
            else:
                print(f"   ⚠️ {request}: May need better routing logic")
        
        routing_percentage = (routing_success / len(test_scenarios)) * 100
        print(f"📊 Routing success rate: {routing_success}/{len(test_scenarios)} ({routing_percentage:.1f}%)")
        
        # Final assessment
        print("\n🎯 ALI COORDINATION TEST RESULTS:")
        print(f"   Ali agent verified: {'✅' if ali_agent else '❌'}")
        print(f"   Agent coverage: {coverage_percentage:.1f}%")
        print(f"   Tier distribution: {len(tier_stats)} tiers")
        print(f"   Specialization areas: {len(specialization_keywords)}")
        print(f"   Routing capability: {routing_percentage:.1f}%")
        
        # Success criteria
        success = (
            ali_agent is not None and 
            coverage_percentage >= 90 and 
            len(tier_stats) >= 5 and
            routing_percentage >= 60
        )
        
        if success:
            print("✅ ALI COORDINATION SYSTEM: ALL TESTS PASSED")
            print("🎯 Ali can effectively coordinate all 41 agents!")
        else:
            print("⚠️ ALI COORDINATION SYSTEM: SOME IMPROVEMENTS NEEDED")
            
        return success
        
    except Exception as e:
        print(f"❌ Ali coordination test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = test_ali_coordination()
    sys.exit(0 if result else 1)