"""
CONVERGIO 2029 - DYNAMIC AGENT LOADER WITH HOT-RELOAD
Auto-discovery system for MyConvergio agents from MD files with file watching
"""

import os
import re
import yaml
import threading
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime

import structlog

# Optional autogen imports for backward compatibility
try:
    from autogen_agentchat.agents import AssistantAgent
    from autogen_ext.models.openai import OpenAIChatCompletionClient
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False
    AssistantAgent = None
    OpenAIChatCompletionClient = None

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileModifiedEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    Observer = None
    FileSystemEventHandler = object  # Base class fallback
    FileModifiedEvent = None

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
    file_hash: Optional[str] = None
    last_modified: Optional[datetime] = None
    version: str = "1.0.0"

class AgentFileWatcher(FileSystemEventHandler):
    """File watcher for agent definition files"""
    
    def __init__(self, loader: 'DynamicAgentLoader'):
        self.loader = loader
        self.debounce_timers: Dict[str, threading.Timer] = {}
        
    def on_modified(self, event):
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        if file_path.suffix == '.md':
            # Debounce file changes (wait 1 second before reloading)
            if str(file_path) in self.debounce_timers:
                self.debounce_timers[str(file_path)].cancel()
            
            timer = threading.Timer(1.0, self._reload_agent, args=[file_path])
            self.debounce_timers[str(file_path)] = timer
            timer.start()
    
    def _reload_agent(self, file_path: Path):
        """Reload a single agent file"""
        try:
            logger.info(f"🔄 Hot-reloading agent: {file_path.name}")
            
            # Store previous version for rollback
            agent_key = file_path.stem.replace('-', '_')
            previous_metadata = self.loader.agent_metadata.get(agent_key)
            
            # Parse the updated file
            new_metadata = self.loader._parse_agent_file(file_path)
            
            if new_metadata:
                # Validate the new agent definition
                if self.loader._validate_agent(new_metadata):
                    # Update the agent
                    self.loader.agent_metadata[new_metadata.key] = new_metadata
                    self.loader._build_agent_registry()
                    
                    # Trigger reload callbacks
                    for callback in self.loader.reload_callbacks:
                        try:
                            callback(new_metadata.key, new_metadata)
                        except Exception as e:
                            logger.error(f"Reload callback failed: {e}")
                    
                    logger.info(f"✅ Successfully reloaded agent: {new_metadata.name}")
                else:
                    # Rollback to previous version
                    if previous_metadata:
                        self.loader.agent_metadata[agent_key] = previous_metadata
                    logger.warning(f"⚠️ Agent validation failed, rolled back: {file_path.name}")
            else:
                logger.error(f"❌ Failed to parse agent file: {file_path.name}")
                
        except Exception as e:
            logger.error(f"Error during hot-reload: {e}")


class DynamicAgentLoader:
    """Dynamic agent loader with hot-reload support"""
    
    def __init__(self, agents_directory: str, enable_hot_reload: bool = True):
        self.agents_directory = Path(agents_directory)
        self.agent_metadata: Dict[str, AgentMetadata] = {}
        self.agent_registry: Dict[str, str] = {}  # name -> description mapping
        self.agent_backups: Dict[str, List[AgentMetadata]] = {}  # Version history
        self.reload_callbacks: List[Callable] = []
        self.enable_hot_reload = enable_hot_reload
        self.file_observer: Optional[Observer] = None
        self.watcher: Optional[AgentFileWatcher] = None
        
    def scan_and_load_agents(self) -> Dict[str, AgentMetadata]:
        """Scan directory and load all agent definitions."""
        logger.info("Scanning for agent definitions", directory=str(self.agents_directory))

        agent_files = list(self.agents_directory.glob("*.md"))
        excluded_files = {"CommonValuesAndPrinciples.md", "MICROSOFT_VALUES.md"}

        valid_agent_files = [f for f in agent_files if f.name not in excluded_files]

        logger.info(
            "Found agent files",
            total_files=len(agent_files),
            valid_agents=len(valid_agent_files),
            excluded=list(excluded_files),
        )

        agents: Dict[str, AgentMetadata] = {}
        for md_file in valid_agent_files:
            try:
                agent_metadata = self._parse_agent_file(md_file)
                if agent_metadata:
                    agents[agent_metadata.key] = agent_metadata
                    logger.debug(
                        "Loaded agent", name=agent_metadata.name, tier=agent_metadata.tier
                    )
            except Exception as e:
                logger.error("Failed to parse agent file", file=md_file.name, error=str(e))
                continue

        self.agent_metadata = agents
        self._build_agent_registry()

        logger.info(
            "Agent loading complete",
            total_agents=len(agents),
            strategic_tier=len([a for a in agents.values() if a.tier == "Strategic"]),
            tech_tier=len([a for a in agents.values() if a.tier == "Technology"]),
        )

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
            
            # Calculate file hash for change detection
            file_hash = self._calculate_file_hash(md_file)
            last_modified = datetime.fromtimestamp(md_file.stat().st_mtime)
            
            return AgentMetadata(
                name=name,
                description=description,
                tools=tools,
                color=color,
                persona=persona,
                expertise_keywords=expertise_keywords,
                tier=tier,
                class_name=class_name,
                key=key,
                file_hash=file_hash,
                last_modified=last_modified,
                version=metadata.get('version', '1.0.0')
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
        content.lower()
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
    
    def create_autogen_agents(self, model_client: Any = None, tools: List[Any] = None) -> Dict[str, Any]:
        """Create AutoGen AssistantAgent instances from loaded metadata.

        Requires AutoGen to be installed. Returns empty dict if not available.
        """
        if not AUTOGEN_AVAILABLE:
            logger.debug("Legacy AutoGen agents not created (using Agent Framework)")
            return {}

        agents = {}

        for key, metadata in self.agent_metadata.items():
            try:
                # Build system message
                system_message = self._build_system_message(metadata)

                # If this is Ali, enrich the system prompt with a knowledge base of all agents
                if metadata.key == "ali_chief_of_staff":
                    try:
                        kb = self.generate_ali_knowledge_base()
                        system_message = f"{system_message}\n\n---\nALI KNOWLEDGE BASE:\n{kb}"
                    except Exception as e:
                        logger.warning("Failed to build Ali knowledge base", error=str(e))
                
                # Create AutoGen agent WITH TOOLS from the start
                agent = AssistantAgent(
                    # Use the stable loader key as the agent name so routers and orchestrators can match reliably
                    name=metadata.key,
                    model_client=model_client,
                    system_message=system_message,
                    tools=tools or []  # Pass tools directly to constructor
                )
                
                agents[key] = agent
                logger.debug("Created AutoGen agent with tools", name=metadata.name, class_name=metadata.class_name, tools_count=len(tools or []))
                
            except Exception as e:
                logger.error("Failed to create AutoGen agent", name=metadata.name, error=str(e))
                continue
        
        logger.info("AutoGen agents created with tools", total=len(agents), tools_count=len(tools or []))
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
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate MD5 hash of file content"""
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    
    def _validate_agent(self, metadata: AgentMetadata) -> bool:
        """Validate agent metadata"""
        # Basic validation rules
        if not metadata.name or not metadata.description:
            return False
        if not metadata.persona or len(metadata.persona) < 50:
            return False
        if not metadata.tier:
            return False
        return True
    
    def start_watching(self):
        """Start file watcher for hot-reload"""
        if not self.enable_hot_reload:
            return

        if not WATCHDOG_AVAILABLE:
            logger.warning("Watchdog not available, hot-reload disabled")
            return

        if self.file_observer:
            self.stop_watching()

        self.watcher = AgentFileWatcher(self)
        self.file_observer = Observer()
        self.file_observer.schedule(
            self.watcher,
            str(self.agents_directory),
            recursive=False
        )
        self.file_observer.start()
        logger.info("Hot-reload enabled for agent definitions")
    
    def stop_watching(self):
        """Stop file watcher"""
        if self.file_observer:
            self.file_observer.stop()
            self.file_observer.join()
            self.file_observer = None
            logger.info("🛑 Hot-reload stopped")
    
    def register_reload_callback(self, callback: Callable):
        """Register callback for agent reload events"""
        self.reload_callbacks.append(callback)
    
    def get_agent_version_history(self, agent_key: str) -> List[AgentMetadata]:
        """Get version history for an agent"""
        return self.agent_backups.get(agent_key, [])
    
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
_backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
agent_loader = DynamicAgentLoader(os.path.join(_backend_dir, "agents", "definitions"))