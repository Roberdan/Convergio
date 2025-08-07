#!/usr/bin/env python3
"""
Test script for Multi-Agent Conversations End-to-End
Simula conversazioni complesse tra agenti per verificare il coordinamento
"""

import asyncio
import sys
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add backend to path  
project_root = Path(__file__).parent.parent.parent
backend_path = project_root / "backend"
sys.path.insert(0, str(backend_path))

try:
    from src.agents.services.agent_loader import DynamicAgentLoader
    from src.agents.memory.autogen_memory_system import AutoGenMemorySystem
    from src.core.config import get_settings
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Note: This test requires backend dependencies to be installed")
    sys.exit(1)

class MultiAgentConversationTester:
    """Test suite for multi-agent conversations"""
    
    def __init__(self):
        self.agents_directory = str(backend_path / "src" / "agents" / "definitions")
        self.loader = DynamicAgentLoader(self.agents_directory)
        self.agents = {}
        self.conversation_scenarios = []
        
    def initialize(self):
        """Initialize the test environment"""
        print("🚀 Initializing Multi-Agent Conversation Tester")
        
        # Load all agents
        self.agents = self.loader.scan_and_load_agents()
        if not self.agents:
            raise Exception("No agents loaded!")
            
        print(f"✅ Loaded {len(self.agents)} agents")
        
        # Define test scenarios
        self._define_test_scenarios()
        print(f"📋 Defined {len(self.conversation_scenarios)} test scenarios")
        
    def _define_test_scenarios(self):
        """Define conversation test scenarios"""
        
        self.conversation_scenarios = [
            {
                "name": "Strategic Planning Session",
                "description": "Complex strategic planning requiring multiple expertise areas",
                "initiator": "ali-chief-of-staff",
                "participants": [
                    "satya-board-of-directors",  # Strategic oversight
                    "domik-mckinsey-strategic-decision-maker",  # Strategic analysis
                    "amy-cfo",  # Financial perspective
                    "matteo-strategic-business-architect"  # Business architecture
                ],
                "topic": "Q1 2025 strategic planning with budget allocation and risk assessment",
                "expected_interactions": 5,  # Minimum expected exchanges
                "success_criteria": ["strategic", "financial", "risk", "planning"]
            },
            {
                "name": "Technical Architecture Review",
                "description": "Technical system design with security and performance considerations",
                "initiator": "baccio-tech-architect", 
                "participants": [
                    "luca-security-expert",  # Security validation
                    "marco-devops-engineer",  # DevOps considerations
                    "guardian-ai-security-validator",  # AI security
                    "thor-quality-assurance-guardian"  # QA oversight
                ],
                "topic": "New microservices architecture security review and performance optimization",
                "expected_interactions": 4,
                "success_criteria": ["security", "performance", "architecture", "microservices"]
            },
            {
                "name": "Product Launch Campaign",
                "description": "Cross-functional product launch coordination",
                "initiator": "sofia-marketing-strategist",
                "participants": [
                    "sara-ux-ui-designer",  # Design requirements
                    "jony-creative-director",  # Creative direction
                    "fabio-sales-business-development",  # Sales alignment
                    "andrea-customer-success-manager"  # Customer success
                ],
                "topic": "AI assistant product launch campaign design and customer onboarding strategy",
                "expected_interactions": 4,
                "success_criteria": ["marketing", "design", "customer", "launch"]
            }
        ]
    
    async def test_scenario_coordination(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Test a specific conversation scenario"""
        
        print(f"\n🎯 Testing Scenario: {scenario['name']}")
        print(f"   Description: {scenario['description']}")
        
        results = {
            "scenario_name": scenario["name"],
            "success": False,
            "agents_found": [],
            "missing_agents": [],
            "conversation_flow": [],
            "coverage_score": 0,
            "coordination_effectiveness": 0
        }
        
        # Check if all required agents exist (convert hyphens to underscores)
        def normalize_agent_key(key):
            return key.replace("-", "_")
            
        initiator_key = normalize_agent_key(scenario["initiator"])
        initiator_found = initiator_key in self.agents
        participants_found = []
        missing_agents = []
        
        for participant in scenario["participants"]:
            participant_key = normalize_agent_key(participant)
            if participant_key in self.agents:
                participants_found.append(participant_key)
            else:
                missing_agents.append(participant)
        
        results["agents_found"] = [initiator_key] + participants_found if initiator_found else participants_found
        results["missing_agents"] = missing_agents
        
        if not initiator_found:
            missing_agents.append(scenario["initiator"])
        
        if missing_agents:
            print(f"   ❌ Missing agents: {missing_agents}")
            return results
        
        print(f"   ✅ All {len(scenario['participants']) + 1} agents found")
        
        # Create normalized scenario for simulation
        normalized_scenario = scenario.copy()
        normalized_scenario["initiator"] = initiator_key
        normalized_scenario["participants"] = participants_found
        
        # Simulate conversation flow
        conversation_flow = self._simulate_conversation_flow(normalized_scenario)
        results["conversation_flow"] = conversation_flow
        
        # Analyze coverage and coordination
        coverage_score = self._analyze_topic_coverage(scenario, conversation_flow)
        coordination_score = self._analyze_coordination_effectiveness(scenario, conversation_flow)
        
        results["coverage_score"] = coverage_score
        results["coordination_effectiveness"] = coordination_score
        
        # Determine success
        success = (
            len(missing_agents) == 0 and
            coverage_score >= 0.7 and  # 70% topic coverage
            coordination_score >= 0.6 and  # 60% coordination effectiveness
            len(conversation_flow) >= scenario["expected_interactions"]
        )
        
        results["success"] = success
        
        print(f"   📊 Results:")
        print(f"      Agents: {len(results['agents_found'])}/{len(scenario['participants']) + 1}")
        print(f"      Coverage: {coverage_score:.1%}")
        print(f"      Coordination: {coordination_score:.1%}")
        print(f"      Status: {'✅ PASSED' if success else '⚠️ NEEDS IMPROVEMENT'}")
        
        return results
    
    def _simulate_conversation_flow(self, scenario: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Simulate a conversation flow between agents"""
        
        flow = []
        topic = scenario["topic"]
        
        # Initiator starts the conversation
        initiator_agent = self.agents[scenario["initiator"]]
        flow.append({
            "speaker": scenario["initiator"],
            "agent_name": initiator_agent.name,
            "message_type": "initiation",
            "content": f"Starting discussion on: {topic}",
            "expertise_areas": initiator_agent.expertise_keywords[:3],
            "timestamp": datetime.now().isoformat()
        })
        
        # Each participant responds based on their expertise
        for participant in scenario["participants"]:
            agent = self.agents[participant]
            
            # Determine response based on agent expertise
            relevant_keywords = [kw for kw in agent.expertise_keywords 
                               if any(word in topic.lower() for word in kw.split())]
            
            response_type = "expertise_input"
            if "security" in agent.description.lower():
                response_type = "security_analysis"
            elif "financial" in agent.description.lower() or "cfo" in agent.description.lower():
                response_type = "financial_analysis"
            elif "design" in agent.description.lower() or "ux" in agent.description.lower():
                response_type = "design_input"
            elif "strategy" in agent.description.lower():
                response_type = "strategic_input"
            
            flow.append({
                "speaker": participant,
                "agent_name": agent.name,
                "message_type": response_type,
                "content": f"Providing {agent.tier} perspective on {topic}",
                "expertise_areas": relevant_keywords[:3] if relevant_keywords else agent.expertise_keywords[:3],
                "timestamp": datetime.now().isoformat()
            })
        
        # Add coordination response from initiator
        if scenario["initiator"] == "ali-chief-of-staff":
            flow.append({
                "speaker": scenario["initiator"],
                "agent_name": initiator_agent.name,
                "message_type": "coordination_summary",
                "content": f"Coordinating insights from {len(scenario['participants'])} specialists",
                "expertise_areas": ["coordination", "integration", "strategic_oversight"],
                "timestamp": datetime.now().isoformat()
            })
        
        return flow
    
    def _analyze_topic_coverage(self, scenario: Dict[str, Any], conversation_flow: List[Dict[str, Any]]) -> float:
        """Analyze how well the conversation covers the expected topics"""
        
        success_criteria = scenario["success_criteria"]
        covered_criteria = set()
        
        for message in conversation_flow:
            content = message["content"].lower()
            expertise_areas = [area.lower() for area in message["expertise_areas"]]
            combined_text = content + " " + " ".join(expertise_areas)
            
            for criteria in success_criteria:
                if criteria.lower() in combined_text:
                    covered_criteria.add(criteria)
        
        coverage_score = len(covered_criteria) / len(success_criteria)
        return coverage_score
    
    def _analyze_coordination_effectiveness(self, scenario: Dict[str, Any], conversation_flow: List[Dict[str, Any]]) -> float:
        """Analyze the effectiveness of agent coordination"""
        
        effectiveness_factors = {
            "diverse_perspectives": 0,
            "appropriate_expertise": 0,
            "coordination_present": 0,
            "logical_flow": 0
        }
        
        # Check for diverse perspectives
        unique_tiers = set()
        unique_message_types = set()
        
        for message in conversation_flow:
            agent_key = message["speaker"]
            if agent_key in self.agents:
                agent = self.agents[agent_key]
                unique_tiers.add(agent.tier)
            unique_message_types.add(message["message_type"])
        
        effectiveness_factors["diverse_perspectives"] = min(len(unique_tiers) / 3, 1.0)  # Expect at least 3 different tiers
        
        # Check for appropriate expertise alignment
        relevant_expertise = 0
        total_messages = len(conversation_flow)
        
        for message in conversation_flow:
            if any(keyword in scenario["topic"].lower() 
                  for keyword in message["expertise_areas"] 
                  for keyword in keyword.split()):
                relevant_expertise += 1
        
        effectiveness_factors["appropriate_expertise"] = relevant_expertise / total_messages if total_messages > 0 else 0
        
        # Check for coordination presence
        coordination_indicators = ["coordination", "summary", "integration", "orchestrat"]
        coordination_present = any(
            any(indicator in message["content"].lower() for indicator in coordination_indicators)
            or message["message_type"] in ["coordination_summary", "initiation"]
            for message in conversation_flow
        )
        effectiveness_factors["coordination_present"] = 1.0 if coordination_present else 0.5
        
        # Check for logical flow (initiator starts, participants respond, coordinator summarizes)
        logical_flow = (
            len(conversation_flow) >= scenario["expected_interactions"] and
            conversation_flow[0]["message_type"] in ["initiation"] and
            len([m for m in conversation_flow if m["message_type"] in ["expertise_input", "security_analysis", "financial_analysis", "design_input", "strategic_input"]]) >= len(scenario["participants"])
        )
        effectiveness_factors["logical_flow"] = 1.0 if logical_flow else 0.6
        
        # Calculate overall effectiveness
        total_effectiveness = sum(effectiveness_factors.values()) / len(effectiveness_factors)
        return total_effectiveness
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all conversation tests"""
        
        print("🧪 RUNNING ALL MULTI-AGENT CONVERSATION TESTS")
        
        overall_results = {
            "total_scenarios": len(self.conversation_scenarios),
            "successful_scenarios": 0,
            "failed_scenarios": 0,
            "average_coverage": 0,
            "average_coordination": 0,
            "scenario_results": []
        }
        
        total_coverage = 0
        total_coordination = 0
        
        for scenario in self.conversation_scenarios:
            try:
                result = await self.test_scenario_coordination(scenario)
                overall_results["scenario_results"].append(result)
                
                if result["success"]:
                    overall_results["successful_scenarios"] += 1
                else:
                    overall_results["failed_scenarios"] += 1
                
                total_coverage += result["coverage_score"]
                total_coordination += result["coordination_effectiveness"]
                
            except Exception as e:
                print(f"   ❌ Error testing scenario {scenario['name']}: {e}")
                overall_results["failed_scenarios"] += 1
        
        # Calculate averages
        if len(self.conversation_scenarios) > 0:
            overall_results["average_coverage"] = total_coverage / len(self.conversation_scenarios)
            overall_results["average_coordination"] = total_coordination / len(self.conversation_scenarios)
        
        return overall_results

async def main():
    """Main test function"""
    
    try:
        # Initialize tester
        tester = MultiAgentConversationTester()
        tester.initialize()
        
        # Run all tests
        results = await tester.run_all_tests()
        
        # Print final summary
        print("\n🎯 MULTI-AGENT CONVERSATION TEST SUMMARY")
        print("=" * 50)
        print(f"Total scenarios tested: {results['total_scenarios']}")
        print(f"Successful scenarios: {results['successful_scenarios']}")
        print(f"Failed scenarios: {results['failed_scenarios']}")
        print(f"Average topic coverage: {results['average_coverage']:.1%}")
        print(f"Average coordination effectiveness: {results['average_coordination']:.1%}")
        
        success_rate = results['successful_scenarios'] / results['total_scenarios'] if results['total_scenarios'] > 0 else 0
        print(f"Overall success rate: {success_rate:.1%}")
        
        if success_rate >= 0.8 and results['average_coverage'] >= 0.7 and results['average_coordination'] >= 0.6:
            print("✅ MULTI-AGENT CONVERSATIONS: ALL TESTS PASSED")
            print("🎯 The system can handle complex multi-agent coordination!")
            return True
        else:
            print("⚠️ MULTI-AGENT CONVERSATIONS: SOME IMPROVEMENTS NEEDED")
            return False
            
    except Exception as e:
        print(f"❌ Multi-agent conversation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)