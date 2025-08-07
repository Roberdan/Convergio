"""
CONVERGIO 2029 - DYNAMIC AGENT LOADER
Auto-discovery system for MyConvergio agents from MD files
"""

import os
import re
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

import structlog
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient

logger = structlog.get_logger()

@dataclass
class AgentMetadata:
    """Agent metadata extracted from MD file."""
    name: str
    description: str
    tools: List[str]
    color: str
    persona: str
    expertise_keywords: List[str]
    tier: str
    class_name: str
    key: str

class DynamicAgentLoader:
    """Dynamic agent loader that auto-discovers agents from MD files."""
    
    def __init__(self, agents_directory: str):
        self.agents_directory = Path(agents_directory)
        self.agent_metadata: Dict[str, AgentMetadata] = {}
        self.agent_registry: Dict[str, str] = {}  # name -> description mapping
        
    def scan_and_load_agents(self) -> Dict[str, AgentMetadata]:
        """Scan directory and load all agent definitions."""
        logger.info("Scanning for agent definitions", directory=str(self.agents_directory))
        
        agent_files = list(self.agents_directory.glob("*.md"))
        excluded_files = {"CommonValuesAndPrinciples.md", "MICROSOFT_VALUES.md"}
        
        valid_agent_files = [f for f in agent_files if f.name not in excluded_files]
        
        logger.info("Found agent files", 
                   total_files=len(agent_files),
                   valid_agents=len(valid_agent_files),
                   excluded=list(excluded_files))
        
        agents = {}
        for md_file in valid_agent_files:
            try:
                agent_metadata = self._parse_agent_file(md_file)
                if agent_metadata:
                    agents[agent_metadata.key] = agent_metadata
                    logger.debug("Loaded agent", name=agent_metadata.name, tier=agent_metadata.tier)
            except Exception as e:
                logger.error("Failed to parse agent file", file=md_file.name, error=str(e))
                continue
        
        self.agent_metadata = agents
        self._build_agent_registry()
        
        logger.info("Agent loading complete", 
                   total_agents=len(agents),
                   strategic_tier=len([a for a in agents.values() if a.tier == "Strategic"]),
                   tech_tier=len([a for a in agents.values() if a.tier == "Technology"]))
        
        return agents
    
    def _parse_agent_file(self, md_file: Path) -> Optional[AgentMetadata]:
        """Parse individual agent MD file."""
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract YAML front matter
            yaml_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
            if not yaml_match:
                logger.warning("No YAML front matter found", file=md_file.name)
                return None
            
            # Parse YAML
            yaml_content = yaml_match.group(1)
            try:
                metadata = yaml.safe_load(yaml_content)
            except yaml.YAMLError as e:
                logger.error("Invalid YAML in front matter", file=md_file.name, error=str(e))
                return None
            
            # Extract required fields
            name = metadata.get('name')
            description = metadata.get('description', '')
            tools = metadata.get('tools', [])
            color = metadata.get('color', '#666666')
            
            if not name:
                logger.warning("Agent missing name field", file=md_file.name)
                return None
            
            # Extract persona from content
            persona = self._extract_persona(content)
            
            # Extract expertise keywords
            expertise_keywords = self._extract_expertise_keywords(content)
            
            # Determine tier
            tier = self._determine_tier(name, description, content)
            
            # Generate class name and key
            class_name = ''.join(word.capitalize() for word in name.replace('-', '_').split('_'))
            key = name.replace('-', '_')
            
            return AgentMetadata(
                name=name,
                description=description,
                tools=tools,
                color=color,
                persona=persona,
                expertise_keywords=expertise_keywords,
                tier=tier,
                class_name=class_name,
                key=key
            )
            
        except Exception as e:
            logger.error("Failed to parse agent file", file=md_file.name, error=str(e))
            return None
    
    def _extract_persona(self, content: str) -> str:
        """Extract agent persona from markdown content."""
        lines = content.split('\n')
        persona_lines = []
        collecting = False
        
        for line in lines:
            if line.startswith('You are **') and not collecting:
                collecting = True
                persona_lines.append(line)
            elif collecting and line.strip():
                persona_lines.append(line)
                # Stop at next section or empty line after significant content
                if line.startswith('##') and len(persona_lines) > 3:
                    break
            elif collecting and not line.strip() and len(persona_lines) > 3:
                break
        
        return '\n'.join(persona_lines) if persona_lines else ""
    
    def _extract_expertise_keywords(self, content: str) -> List[str]:
        """Extract expertise keywords from agent content."""
        keywords = set()
        
        # Extract from common sections
        expertise_patterns = [
            r'specializing in ([^,\n]+)',
            r'expertise includes?:?\s*\n?[-•]\s*([^\n]+)',
            r'expert in ([^,\n]+)',
            r'focus on ([^,\n]+)'
        ]
        
        for pattern in expertise_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                # Clean and split keywords
                clean_keywords = re.sub(r'[^\w\s,]', '', match).lower()
                keywords.update([kw.strip() for kw in clean_keywords.split(',') if kw.strip()])
        
        return list(keywords)[:10]  # Limit to top 10 keywords
    
    def _determine_tier(self, name: str, description: str, content: str) -> str:
        """Determine agent tier based on content analysis."""
        content_lower = content.lower()
        desc_lower = description.lower()
        
        # Tier classification rules
        if any(term in desc_lower for term in ['chief', 'cfo', 'strategic', 'board', 'mckinsey']):
            return "Strategic Leadership"
        elif any(term in desc_lower for term in ['technology', 'architect', 'devops', 'security', 'engineering']):
            return "Technology & Engineering"
        elif any(term in desc_lower for term in ['design', 'ux', 'ui', 'creative']):
            return "User Experience & Design"
        elif any(term in desc_lower for term in ['data', 'analytics', 'scientist']):
            return "Data & Analytics"
        elif any(term in desc_lower for term in ['project', 'program', 'manager', 'execution']):
            return "Execution & Operations"
        elif any(term in desc_lower for term in ['sales', 'business', 'hr', 'talent']):
            return "Business & People"
        elif any(term in desc_lower for term in ['legal', 'compliance', 'healthcare']):
            return "Compliance & Risk"
        else:
            return "Specialized Services"
    
    def _build_agent_registry(self):
        """Build searchable agent registry for Ali."""
        self.agent_registry = {
            agent.name: agent.description 
            for agent in self.agent_metadata.values()
        }
    
    def create_autogen_agents(self, model_client: OpenAIChatCompletionClient) -> Dict[str, AssistantAgent]:
        """Create AutoGen AssistantAgent instances from loaded metadata."""
        agents = {}
        
        for key, metadata in self.agent_metadata.items():
            try:
                # Build system message
                system_message = self._build_system_message(metadata)
                
                # Create AutoGen agent
                agent = AssistantAgent(
                    name=metadata.class_name,
                    model_client=model_client,
                    system_message=system_message
                )
                
                agents[key] = agent
                logger.debug("Created AutoGen agent", name=metadata.name, class_name=metadata.class_name)
                
            except Exception as e:
                logger.error("Failed to create AutoGen agent", name=metadata.name, error=str(e))
                continue
        
        logger.info("AutoGen agents created", total=len(agents))
        return agents
    
    def _build_system_message(self, metadata: AgentMetadata) -> str:
        """Build comprehensive system message for agent."""
        return f"""You are {metadata.class_name}, an expert agent in the MyConvergio ecosystem.

SPECIALIZATION: {metadata.description}

PERSONA & IDENTITY:
{metadata.persona}

EXPERTISE AREAS: {', '.join(metadata.expertise_keywords)}
TIER: {metadata.tier}
AVAILABLE TOOLS: {', '.join(metadata.tools) if metadata.tools else 'Standard communication tools'}

OPERATIONAL GUIDELINES:
- Always provide professional, accurate, and helpful responses aligned with MyConvergio values
- Focus on delivering actionable insights and solutions within your area of expertise  
- Collaborate effectively with other agents when needed
- Maintain the highest standards of quality and professionalism
- If a request is outside your expertise, suggest the appropriate specialist agent

Remember: You are part of a coordinated ecosystem of 40+ specialist agents working together to empower every person and organization to achieve more."""
    
    def generate_ali_knowledge_base(self) -> str:
        """Generate comprehensive knowledge base for Ali orchestrator."""
        if not self.agent_metadata:
            return "No agents loaded"
        
        # Group agents by tier
        tiers = {}
        for agent in self.agent_metadata.values():
            tier = agent.tier
            if tier not in tiers:
                tiers[tier] = []
            tiers[tier].append(agent)
        
        # Build knowledge base
        knowledge_sections = []
        
        for tier_name, tier_agents in tiers.items():
            section = f"\n### {tier_name} ({len(tier_agents)} agents)\n"
            for agent in sorted(tier_agents, key=lambda x: x.name):
                section += f"- **{agent.name}**: {agent.description}\n"
                if agent.expertise_keywords:
                    section += f"  Keywords: {', '.join(agent.expertise_keywords[:5])}\n"
            knowledge_sections.append(section)
        
        expertise_map = "\n".join(knowledge_sections)
        
        return f"""MYCONVERGIO AGENT ECOSYSTEM ({len(self.agent_metadata)} specialists)

{expertise_map}

ROUTING INTELLIGENCE:
- Use agent names (e.g., 'ali_chief_of_staff', 'satya_board_of_directors') for HandoffMessage
- Match request keywords to agent expertise areas
- Consider collaboration patterns for complex requests
- Always explain your routing decision briefly"""
    
    def get_agent_count(self) -> int:
        """Get total number of loaded agents."""
        return len(self.agent_metadata)
    
    def get_agents_by_tier(self, tier: str) -> List[AgentMetadata]:
        """Get all agents in a specific tier."""
        return [agent for agent in self.agent_metadata.values() if agent.tier == tier]
    
    def reload_agents(self) -> Dict[str, AgentMetadata]:
        """Reload all agents (useful for development/testing)."""
        logger.info("Reloading agents from directory")
        return self.scan_and_load_agents()


# Global agent loader instance - use absolute path
import os
_backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
agent_loader = DynamicAgentLoader(os.path.join(_backend_dir, "agents", "definitions"))