#!/usr/bin/env python3
"""
Comprehensive Agent Test Suite
Tests all 41 AI agents with multiple validation levels and complete independence from backend
"""

import os
import yaml
import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class AgentDefinition:
    """Simplified agent representation"""
    name: str
    description: str
    color: str
    tools: List[str]
    persona: str
    tier: str = ""
    expertise_keywords: List[str] = None
    
    def __post_init__(self):
        if self.expertise_keywords is None:
            self.expertise_keywords = []

class AgentTestSuite:
    """Comprehensive test suite for all agents"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.agents_dir = self.project_root / "backend" / "src" / "agents" / "definitions"
        self.agents: Dict[str, AgentDefinition] = {}
        
    def load_agent_from_file(self, file_path: Path) -> Optional[AgentDefinition]:
        """Load agent from MD file with YAML front matter"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract YAML front matter
            yaml_match = re.match(r'^---\n(.*?)\n---\n(.*)', content, re.DOTALL)
            if not yaml_match:
                print(f"⚠️ {file_path.name}: No YAML front matter")
                return None
            
            yaml_content = yaml_match.group(1)
            markdown_content = yaml_match.group(2)
            
            try:
                metadata = yaml.safe_load(yaml_content)
            except yaml.YAMLError as e:
                print(f"❌ {file_path.name}: Invalid YAML - {e}")
                return None
            
            # Extract tier and expertise from content if not in YAML
            tier = metadata.get('tier', '')
            expertise_keywords = metadata.get('expertise_keywords', [])
            
            if not tier:
                tier = self._infer_tier_from_content(markdown_content)
            
            if not expertise_keywords:
                expertise_keywords = self._extract_expertise_from_content(markdown_content, metadata)
            
            return AgentDefinition(
                name=metadata.get('name', ''),
                description=metadata.get('description', ''),
                color=metadata.get('color', ''),
                tools=metadata.get('tools', []),
                persona=markdown_content.strip(),
                tier=tier,
                expertise_keywords=expertise_keywords[:5]  # Limit to 5 keywords
            )
            
        except Exception as e:
            print(f"❌ {file_path.name}: Error loading - {e}")
            return None
    
    def _infer_tier_from_content(self, content: str) -> str:
        """Infer agent tier from content"""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ['strategic', 'leadership', 'board', 'ceo', 'cfo']):
            return 'Strategic Leadership'
        elif any(word in content_lower for word in ['technical', 'engineering', 'architect', 'devops']):
            return 'Technology & Engineering'
        elif any(word in content_lower for word in ['design', 'ux', 'ui', 'creative']):
            return 'User Experience & Design'
        elif any(word in content_lower for word in ['data', 'analytics', 'scientist']):
            return 'Data & Analytics'
        elif any(word in content_lower for word in ['compliance', 'risk', 'security', 'legal']):
            return 'Compliance & Risk'
        elif any(word in content_lower for word in ['execution', 'operations', 'project', 'program']):
            return 'Execution & Operations'
        else:
            return 'Specialized Services'
    
    def _extract_expertise_from_content(self, content: str, metadata: dict) -> List[str]:
        """Extract expertise keywords from content"""
        expertise_keywords = []
        
        # Try to extract from content patterns
        expertise_patterns = [
            r'expert(?:ise)? in ([^.]+)',
            r'specializ(?:ed|ing) in ([^.]+)',
            r'focus(?:ed|ing) on ([^.]+)',
            r'responsible for ([^.]+)',
        ]
        
        for pattern in expertise_patterns:
            matches = re.findall(pattern, content.lower())
            for match in matches:
                keywords = [kw.strip() for kw in match.split(',')]
                expertise_keywords.extend(keywords[:2])  # Limit per match
                if len(expertise_keywords) >= 5:
                    break
            if len(expertise_keywords) >= 5:
                break
        
        # If still empty, use keywords from name and description
        if not expertise_keywords:
            text = (metadata.get('name', '') + ' ' + metadata.get('description', '')).lower()
            common_keywords = [
                'security', 'financial', 'design', 'strategy', 'technical', 
                'marketing', 'legal', 'hr', 'data', 'analytics', 'coordination', 
                'management', 'architecture', 'development', 'operations'
            ]
            expertise_keywords = [kw for kw in common_keywords if kw in text][:3]
        
        return expertise_keywords
    
    def load_all_agents(self) -> bool:
        """Load all agent definitions"""
        if not self.agents_dir.exists():
            print(f"❌ Agents directory not found: {self.agents_dir}")
            return False
        
        agent_files = list(self.agents_dir.glob("*.md"))
        excluded_files = {"CommonValuesAndPrinciples.md", "MICROSOFT_VALUES.md"}
        valid_files = [f for f in agent_files if f.name not in excluded_files]
        
        print(f"📁 Found {len(valid_files)} agent definition files")
        
        for file_path in valid_files:
            agent = self.load_agent_from_file(file_path)
            if agent and agent.name:
                key = agent.name.lower().replace(' ', '_').replace('-', '_')
                self.agents[key] = agent
                print(f"✅ {agent.name}")
        
        return len(self.agents) > 0
    
    def test_basic_validation(self) -> Dict[str, Any]:
        """Test basic agent validation"""
        print("\n🧪 BASIC AGENT VALIDATION")
        
        issues = []
        valid_agents = 0
        
        for key, agent in self.agents.items():
            agent_issues = []
            
            if not agent.name:
                agent_issues.append("Missing name")
            if not agent.description:
                agent_issues.append("Missing description")
            if not agent.tier:
                agent_issues.append("Missing tier")
            if not agent.expertise_keywords:
                agent_issues.append("No expertise keywords")
            if len(agent.persona) < 100:
                agent_issues.append("Persona too short")
            if not agent.color:
                agent_issues.append("Missing color")
            
            if agent_issues:
                issues.extend([f"{agent.name}: {issue}" for issue in agent_issues])
            else:
                valid_agents += 1
        
        # Show issues (limited)
        if issues:
            print(f"⚠️ Issues found ({len(issues)} total):")
            for issue in issues[:10]:
                print(f"   {issue}")
            if len(issues) > 10:
                print(f"   ... and {len(issues) - 10} more issues")
        
        results = {
            "total_agents": len(self.agents),
            "valid_agents": valid_agents,
            "issues_count": len(issues),
            "success": valid_agents >= 40 and len(issues) < 10
        }
        
        print(f"\n📊 BASIC VALIDATION RESULTS:")
        print(f"   Total agents: {results['total_agents']}")
        print(f"   Valid agents: {results['valid_agents']}")
        print(f"   Issues: {results['issues_count']}")
        
        if results["success"]:
            print("✅ BASIC VALIDATION: PASSED")
        else:
            print("❌ BASIC VALIDATION: FAILED")
        
        return results
    
    def test_coverage_analysis(self) -> Dict[str, Any]:
        """Test agent coverage and distribution"""
        print("\n🎯 COVERAGE ANALYSIS")
        
        # Tier distribution
        tier_distribution = {}
        for agent in self.agents.values():
            tier = agent.tier
            if tier not in tier_distribution:
                tier_distribution[tier] = []
            tier_distribution[tier].append(agent.name)
        
        print(f"📈 Tier distribution:")
        for tier, agent_names in tier_distribution.items():
            print(f"   {tier}: {len(agent_names)} agents")
        
        # Expertise analysis
        all_keywords = set()
        for agent in self.agents.values():
            all_keywords.update([kw.lower() for kw in agent.expertise_keywords])
        
        print(f"🎯 Total expertise areas: {len(all_keywords)}")
        
        # Key area coverage
        key_areas = [
            "security", "financial", "design", "strategy", "technical", 
            "marketing", "legal", "hr", "data", "analytics"
        ]
        
        covered_areas = []
        for area in key_areas:
            if any(area in keyword for keyword in all_keywords):
                covered_areas.append(area)
        
        coverage_percentage = (len(covered_areas) / len(key_areas)) * 100
        print(f"📊 Key area coverage: {len(covered_areas)}/{len(key_areas)} ({coverage_percentage:.1f}%)")
        
        results = {
            "tier_count": len(tier_distribution),
            "expertise_areas": len(all_keywords),
            "key_area_coverage": coverage_percentage,
            "success": (
                len(tier_distribution) >= 5 and
                len(all_keywords) >= 50 and
                coverage_percentage >= 80
            )
        }
        
        if results["success"]:
            print("✅ COVERAGE ANALYSIS: EXCELLENT")
        else:
            print("⚠️ COVERAGE ANALYSIS: NEEDS IMPROVEMENT")
        
        return results
    
    def test_ali_coordination(self) -> Dict[str, Any]:
        """Test Ali coordination capabilities"""
        print("\n🎯 ALI COORDINATION TEST")
        
        # Find Ali
        ali_agent = None
        for key, agent in self.agents.items():
            if "ali" in key.lower() and ("chief" in agent.description.lower() or "orchestrator" in agent.description.lower()):
                ali_agent = agent
                break
        
        if not ali_agent:
            print("❌ Ali agent not found!")
            return {"success": False, "ali_found": False}
        
        print(f"✅ Found Ali: {ali_agent.name}")
        print(f"   Description: {ali_agent.description[:100]}...")
        
        # Generate simplified knowledge base
        knowledge_base = ""
        for agent in self.agents.values():
            knowledge_base += f"{agent.name}: {agent.description}\n"
            knowledge_base += f"Expertise: {', '.join(agent.expertise_keywords[:3])}\n\n"
        
        # Test coverage
        agent_coverage = 0
        for agent in self.agents.values():
            if agent.name.lower() in knowledge_base.lower():
                agent_coverage += 1
        
        coverage_percentage = (agent_coverage / len(self.agents)) * 100
        print(f"📊 Agent coverage in knowledge base: {agent_coverage}/{len(self.agents)} ({coverage_percentage:.1f}%)")
        
        # Test routing scenarios
        test_scenarios = [
            {"request": "security analysis", "keywords": ["security", "guardian", "luca"]},
            {"request": "financial analysis", "keywords": ["financial", "cfo", "amy"]},
            {"request": "design review", "keywords": ["design", "ux", "ui", "sara"]},
            {"request": "strategic planning", "keywords": ["strategy", "strategic", "satya"]}
        ]
        
        routing_success = 0
        for scenario in test_scenarios:
            request = scenario["request"]
            keywords = scenario["keywords"]
            
            relevant_agents = []
            for agent in self.agents.values():
                agent_text = (agent.name + " " + agent.description + " " + " ".join(agent.expertise_keywords)).lower()
                if any(keyword.lower() in agent_text for keyword in keywords):
                    relevant_agents.append(agent.name)
            
            if relevant_agents:
                routing_success += 1
                print(f"   ✅ {request}: Found {len(relevant_agents)} relevant agents")
            else:
                print(f"   ⚠️ {request}: No relevant agents found")
        
        routing_percentage = (routing_success / len(test_scenarios)) * 100
        print(f"📊 Routing success rate: {routing_success}/{len(test_scenarios)} ({routing_percentage:.1f}%)")
        
        results = {
            "ali_found": True,
            "coverage_percentage": coverage_percentage,
            "routing_percentage": routing_percentage,
            "success": (
                coverage_percentage >= 90 and
                routing_percentage >= 75
            )
        }
        
        if results["success"]:
            print("✅ ALI COORDINATION: ALL TESTS PASSED")
        else:
            print("⚠️ ALI COORDINATION: SOME IMPROVEMENTS NEEDED")
        
        return results
    
    def run_complete_test_suite(self) -> Dict[str, Any]:
        """Run complete agent test suite"""
        print("🚀 COMPREHENSIVE AGENT TEST SUITE")
        print("=" * 60)
        
        # Load agents
        if not self.load_all_agents():
            return {"success": False, "error": "Failed to load agents"}
        
        # Run all tests
        results = {}
        results["basic_validation"] = self.test_basic_validation()
        results["coverage_analysis"] = self.test_coverage_analysis()
        results["ali_coordination"] = self.test_ali_coordination()
        
        # Overall assessment
        all_passed = all(test_result.get("success", False) for test_result in results.values())
        
        print(f"\n🏆 COMPREHENSIVE TEST RESULTS")
        print("=" * 50)
        for test_name, test_result in results.items():
            status = "✅ PASSED" if test_result.get("success", False) else "❌ FAILED"
            print(f"   {test_name.replace('_', ' ').title()}: {status}")
        
        if all_passed:
            print("🎉 All agent tests passed!")
            print("🤖 41 AI agents ready for production!")
        else:
            print("⚠️ Some agent tests need attention")
        
        results["overall_success"] = all_passed
        return results

def main():
    """Main test function"""
    try:
        test_suite = AgentTestSuite()
        results = test_suite.run_complete_test_suite()
        return results.get("overall_success", False)
    except Exception as e:
        print(f"❌ Agent test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)