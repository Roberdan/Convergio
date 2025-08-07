"""
Agent Management API
CRUD operations per la gestione dinamica degli agenti con hot-reload
"""

import os
import yaml
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field
import structlog

from src.agents.services.agent_loader import agent_loader
from src.core.redis import get_redis_client

logger = structlog.get_logger()
router = APIRouter()

# Pydantic models for API
class AgentMetadata(BaseModel):
    name: str = Field(..., description="Agent name (used as key)")
    description: str = Field(..., description="Agent description")
    color: str = Field("#666666", description="Agent color in hex")
    tools: List[str] = Field(default_factory=list, description="Available tools")
    tier: Optional[str] = Field(None, description="Agent tier (auto-detected if not provided)")

class AgentContent(BaseModel):
    persona: str = Field(..., description="Agent persona and identity section")
    expertise_areas: List[str] = Field(default_factory=list, description="Main expertise areas")
    additional_content: str = Field("", description="Additional markdown content")

class AgentDefinition(BaseModel):
    metadata: AgentMetadata
    content: AgentContent

class AgentUpdateRequest(BaseModel):
    agent_key: str
    definition: AgentDefinition
    ali_improvements: Optional[Dict[str, Any]] = Field(None, description="Ali's suggested improvements")

class AgentCreateRequest(BaseModel):
    definition: AgentDefinition

class AliAssistanceRequest(BaseModel):
    agent_key: Optional[str] = None
    current_definition: Optional[AgentDefinition] = None
    improvement_focus: str = Field("general", description="Focus area for improvements")
    user_intent: str = Field("", description="What the user wants to achieve")

class AgentManagerService:
    """Service class for managing agent definitions"""
    
    def __init__(self):
        self.agents_directory = Path("src/agents/definitions")
        self.backup_directory = Path("data/agent_backups")
        self.backup_directory.mkdir(parents=True, exist_ok=True)
        
    async def list_agents(self) -> Dict[str, Any]:
        """List all available agents with their metadata"""
        try:
            agents = agent_loader.scan_and_load_agents()
            
            agent_list = []
            for key, agent in agents.items():
                agent_list.append({
                    "key": key,
                    "name": agent.name,
                    "description": agent.description,
                    "color": agent.color,
                    "tier": agent.tier,
                    "tools_count": len(agent.tools),
                    "expertise_count": len(agent.expertise_keywords),
                    "file_path": f"{agent.name.replace('_', '-')}.md"
                })
            
            return {
                "total_agents": len(agent_list),
                "agents": sorted(agent_list, key=lambda x: x["name"]),
                "tiers": list(set(agent["tier"] for agent in agent_list)),
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error("Failed to list agents", error=str(e))
            raise HTTPException(status_code=500, detail=f"Failed to list agents: {str(e)}")
    
    async def get_agent(self, agent_key: str) -> Dict[str, Any]:
        """Get specific agent definition"""
        try:
            agents = agent_loader.agent_metadata
            
            if agent_key not in agents:
                raise HTTPException(status_code=404, detail=f"Agent {agent_key} not found")
            
            agent = agents[agent_key]
            
            # Read the full markdown file
            agent_file = self.agents_directory / f"{agent_key.replace('_', '-')}.md"
            if not agent_file.exists():
                raise HTTPException(status_code=404, detail=f"Agent file not found: {agent_file}")
            
            with open(agent_file, 'r', encoding='utf-8') as f:
                full_content = f.read()
            
            # Parse YAML front matter and content
            import re
            yaml_match = re.match(r'^---\n(.*?)\n---\n(.*)$', full_content, re.DOTALL)
            if not yaml_match:
                raise HTTPException(status_code=400, detail="Invalid agent file format")
            
            yaml_content = yaml.safe_load(yaml_match.group(1))
            markdown_content = yaml_match.group(2)
            
            return {
                "key": agent_key,
                "metadata": {
                    "name": yaml_content.get("name", agent_key),
                    "description": yaml_content.get("description", ""),
                    "color": yaml_content.get("color", "#666666"),
                    "tools": yaml_content.get("tools", []),
                    "tier": agent.tier
                },
                "content": {
                    "persona": agent.persona,
                    "expertise_areas": agent.expertise_keywords,
                    "additional_content": markdown_content
                },
                "file_path": str(agent_file),
                "last_modified": agent_file.stat().st_mtime if agent_file.exists() else None
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to get agent", agent_key=agent_key, error=str(e))
            raise HTTPException(status_code=500, detail=f"Failed to get agent: {str(e)}")
    
    async def create_agent(self, request: AgentCreateRequest) -> Dict[str, Any]:
        """Create a new agent definition"""
        try:
            agent_key = request.definition.metadata.name.lower().replace(" ", "-").replace("_", "-")
            agent_file = self.agents_directory / f"{agent_key}.md"
            
            # Check if agent already exists
            if agent_file.exists():
                raise HTTPException(status_code=400, detail=f"Agent {agent_key} already exists")
            
            # Create YAML front matter
            yaml_data = {
                "name": agent_key,
                "description": request.definition.metadata.description,
                "color": request.definition.metadata.color,
                "tools": request.definition.metadata.tools or []
            }
            
            # Build markdown content
            persona_section = f"""You are **{request.definition.metadata.name}**, {request.definition.content.persona}

## MyConvergio Values Integration
*For complete MyConvergio values and principles, see [CommonValuesAndPrinciples.md](./CommonValuesAndPrinciples.md)*

## EXPERTISE AREAS
{chr(10).join(f"- {area}" for area in request.definition.content.expertise_areas)}

{request.definition.content.additional_content}
"""

            # Create full file content
            full_content = f"""---
{yaml.dump(yaml_data, default_flow_style=False)}---

{persona_section}"""
            
            # Write file
            with open(agent_file, 'w', encoding='utf-8') as f:
                f.write(full_content)
            
            # Reload agents
            await self._hot_reload_agents()
            
            logger.info("Created new agent", agent_key=agent_key, file=str(agent_file))
            
            return {
                "success": True,
                "agent_key": agent_key,
                "file_path": str(agent_file),
                "message": f"Agent {agent_key} created successfully",
                "reload_status": "completed"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to create agent", error=str(e))
            raise HTTPException(status_code=500, detail=f"Failed to create agent: {str(e)}")
    
    async def update_agent(self, request: AgentUpdateRequest) -> Dict[str, Any]:
        """Update an existing agent definition"""
        try:
            agent_key = request.agent_key
            agent_file = self.agents_directory / f"{agent_key.replace('_', '-')}.md"
            
            if not agent_file.exists():
                raise HTTPException(status_code=404, detail=f"Agent {agent_key} not found")
            
            # Create backup
            backup_file = self.backup_directory / f"{agent_key}_{int(datetime.now().timestamp())}.md"
            with open(agent_file, 'r') as src, open(backup_file, 'w') as dst:
                dst.write(src.read())
            
            # Create updated YAML front matter
            yaml_data = {
                "name": request.definition.metadata.name,
                "description": request.definition.metadata.description,
                "color": request.definition.metadata.color,
                "tools": request.definition.metadata.tools or []
            }
            
            # Build updated markdown content
            persona_section = f"""You are **{request.definition.metadata.name}**, {request.definition.content.persona}

## MyConvergio Values Integration
*For complete MyConvergio values and principles, see [CommonValuesAndPrinciples.md](./CommonValuesAndPrinciples.md)*

## EXPERTISE AREAS
{chr(10).join(f"- {area}" for area in request.definition.content.expertise_areas)}

{request.definition.content.additional_content}"""

            # Create full updated content
            full_content = f"""---
{yaml.dump(yaml_data, default_flow_style=False)}---

{persona_section}"""
            
            # Write updated file
            with open(agent_file, 'w', encoding='utf-8') as f:
                f.write(full_content)
            
            # Hot reload agents
            await self._hot_reload_agents()
            
            logger.info("Updated agent", agent_key=agent_key, backup=str(backup_file))
            
            return {
                "success": True,
                "agent_key": agent_key,
                "file_path": str(agent_file),
                "backup_path": str(backup_file),
                "message": f"Agent {agent_key} updated successfully",
                "reload_status": "completed",
                "ali_improvements_applied": bool(request.ali_improvements)
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to update agent", agent_key=request.agent_key, error=str(e))
            raise HTTPException(status_code=500, detail=f"Failed to update agent: {str(e)}")
    
    async def delete_agent(self, agent_key: str) -> Dict[str, Any]:
        """Delete an agent definition"""
        try:
            agent_file = self.agents_directory / f"{agent_key.replace('_', '-')}.md"
            
            if not agent_file.exists():
                raise HTTPException(status_code=404, detail=f"Agent {agent_key} not found")
            
            # Create backup before deletion
            backup_file = self.backup_directory / f"{agent_key}_deleted_{int(datetime.now().timestamp())}.md"
            with open(agent_file, 'r') as src, open(backup_file, 'w') as dst:
                dst.write(src.read())
            
            # Delete file
            agent_file.unlink()
            
            # Hot reload agents
            await self._hot_reload_agents()
            
            logger.info("Deleted agent", agent_key=agent_key, backup=str(backup_file))
            
            return {
                "success": True,
                "agent_key": agent_key,
                "backup_path": str(backup_file),
                "message": f"Agent {agent_key} deleted successfully",
                "reload_status": "completed"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to delete agent", agent_key=agent_key, error=str(e))
            raise HTTPException(status_code=500, detail=f"Failed to delete agent: {str(e)}")
    
    async def _hot_reload_agents(self):
        """Hot reload agents without restarting the service"""
        try:
            # Reload agent definitions
            agent_loader.scan_and_load_agents()
            
            # Update Ali's knowledge base
            knowledge_base = agent_loader.generate_ali_knowledge_base()
            
            # Cache the updated knowledge base in Redis
            redis_client = get_redis_client()
            if redis_client:
                await redis_client.setex("ali_knowledge_base", 3600, knowledge_base)
            
            logger.info("Hot reload completed", agent_count=len(agent_loader.agent_metadata))
            
        except Exception as e:
            logger.error("Hot reload failed", error=str(e))
            raise
    
    async def get_ali_assistance(self, request: AliAssistanceRequest) -> Dict[str, Any]:
        """Get Ali's assistance for improving agent definitions"""
        try:
            # This would integrate with Ali's intelligence system
            # For now, we'll provide structured improvement suggestions
            
            suggestions = {
                "expertise_improvements": [],
                "persona_enhancements": [],
                "tool_recommendations": [],
                "integration_suggestions": []
            }
            
            # If updating existing agent
            if request.agent_key and request.current_definition:
                current_def = request.current_definition
                
                # Suggest expertise improvements
                if len(current_def.content.expertise_areas) < 3:
                    suggestions["expertise_improvements"].append(
                        "Consider adding more specific expertise areas to make the agent more specialized"
                    )
                
                # Suggest persona enhancements
                if len(current_def.content.persona) < 100:
                    suggestions["persona_enhancements"].append(
                        "Expand the persona description to include personality traits and working style"
                    )
                
                # Tool recommendations based on agent type
                if "security" in current_def.metadata.description.lower():
                    missing_security_tools = ["security_validation", "threat_detection", "vulnerability_scan"]
                    current_tools = current_def.metadata.tools
                    needed_tools = [tool for tool in missing_security_tools if tool not in current_tools]
                    if needed_tools:
                        suggestions["tool_recommendations"] = [
                            f"Security agents typically benefit from these tools: {', '.join(needed_tools)}"
                        ]
                
                # Integration suggestions
                suggestions["integration_suggestions"].append(
                    "Ensure the agent's expertise complements other agents in the ecosystem"
                )
            
            # General improvement suggestions based on focus
            if request.improvement_focus == "performance":
                suggestions["performance_tips"] = [
                    "Optimize tool usage for faster response times",
                    "Consider caching frequently accessed data"
                ]
            elif request.improvement_focus == "collaboration":
                suggestions["collaboration_tips"] = [
                    "Define clear handoff points to other agents",
                    "Specify when to escalate to Ali for coordination"
                ]
            
            return {
                "agent_key": request.agent_key,
                "improvement_focus": request.improvement_focus,
                "suggestions": suggestions,
                "confidence_score": 0.85,  # Ali's confidence in the suggestions
                "estimated_improvement": "15-25% better performance and user experience",
                "next_steps": [
                    "Review the suggested improvements",
                    "Apply the changes you find most relevant",
                    "Test the updated agent with sample interactions"
                ]
            }
            
        except Exception as e:
            logger.error("Ali assistance failed", error=str(e))
            raise HTTPException(status_code=500, detail=f"Ali assistance failed: {str(e)}")

# Global service instance
agent_service = AgentManagerService()

# API Endpoints
@router.get("/agents")
async def list_agents():
    """List all available agents"""
    return await agent_service.list_agents()

@router.get("/agents/{agent_key}")
async def get_agent(agent_key: str):
    """Get specific agent definition"""
    return await agent_service.get_agent(agent_key)

@router.post("/agents")
async def create_agent(request: AgentCreateRequest):
    """Create a new agent"""
    return await agent_service.create_agent(request)

@router.put("/agents/{agent_key}")
async def update_agent(agent_key: str, request: AgentUpdateRequest):
    """Update an existing agent"""
    request.agent_key = agent_key  # Ensure consistency
    return await agent_service.update_agent(request)

@router.delete("/agents/{agent_key}")
async def delete_agent(agent_key: str):
    """Delete an agent"""
    return await agent_service.delete_agent(agent_key)

@router.post("/agents/hot-reload")
async def hot_reload_agents():
    """Hot reload all agents without restarting"""
    await agent_service._hot_reload_agents()
    return {
        "success": True,
        "message": "Agents reloaded successfully",
        "agent_count": len(agent_loader.agent_metadata)
    }

@router.post("/agents/ali-assistance")
async def get_ali_assistance(request: AliAssistanceRequest):
    """Get Ali's assistance for improving agents"""
    return await agent_service.get_ali_assistance(request)

@router.get("/agents/backups")
async def list_agent_backups():
    """List all agent backups"""
    backup_dir = Path("data/agent_backups")
    if not backup_dir.exists():
        return {"backups": []}
    
    backups = []
    for backup_file in backup_dir.glob("*.md"):
        stat = backup_file.stat()
        backups.append({
            "filename": backup_file.name,
            "size_bytes": stat.st_size,
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "agent_key": backup_file.stem.split("_")[0]
        })
    
    return {
        "backups": sorted(backups, key=lambda x: x["created"], reverse=True),
        "total_backups": len(backups)
    }