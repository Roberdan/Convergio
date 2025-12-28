"""
Agent Management API - CRUD operations for AI agents
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path
import json

from ..agents.services.agent_loader import DynamicAgentLoader
from pydantic import BaseModel

router = APIRouter(tags=["Agent Management"])

# Initialize agent loader

# Get absolute path to agent definitions
current_dir = Path(__file__).parent.parent  # Go up to src/
agent_definitions_path = current_dir / "agents" / "definitions"

agent_loader = DynamicAgentLoader(
    str(agent_definitions_path),
    enable_hot_reload=True
)

# ===================== Request/Response Models =====================

class AgentCreate(BaseModel):
    name: str
    role: str
    tier: str = "specialist"
    category: str = "technical"
    capabilities: List[str] = []
    tools: List[Dict[str, Any]] = []
    max_context_tokens: int = 8000
    temperature: float = 0.7
    model_preference: str = "gpt-4-turbo-preview"
    cost_per_interaction: float = 0.1
    system_prompt: str = ""


class AgentUpdate(BaseModel):
    role: Optional[str] = None
    tier: Optional[str] = None
    category: Optional[str] = None
    capabilities: Optional[List[str]] = None
    tools: Optional[List[Dict[str, Any]]] = None
    max_context_tokens: Optional[int] = None
    temperature: Optional[float] = None
    model_preference: Optional[str] = None
    cost_per_interaction: Optional[float] = None
    system_prompt: Optional[str] = None


class AgentResponse(BaseModel):
    id: str
    name: str
    role: str
    tier: str
    category: str
    status: str
    version: str
    capabilities: List[str]
    tools: List[Dict[str, Any]]
    cost_per_interaction: float
    max_context_tokens: int
    temperature: float
    model_preference: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# ===================== Agent CRUD Endpoints =====================

@router.get("/agents", response_model=List[AgentResponse])
async def list_agents(
    category: Optional[str] = None,
    tier: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500)
):
    """List all agents with optional filtering"""
    # Ensure agents are loaded
    if not agent_loader.agent_metadata:
        agent_loader.scan_and_load_agents()
    
    agents = agent_loader.agent_metadata
    
    result = []
    for agent_key, metadata in agents.items():
        # metadata is an AgentMetadata dataclass object
        # Apply filters
        if category and getattr(metadata, "category", "general") != category:
            continue
        if tier and metadata.tier != tier:
            continue
        if status and getattr(metadata, "status", "active") != status:
            continue
        
        # Convert tools list of strings to list of dicts
        tools_as_dicts = [{"name": tool, "enabled": True} for tool in metadata.tools]
        
        result.append(AgentResponse(
            id=agent_key,
            name=metadata.name,
            role=metadata.description,
            tier=metadata.tier,
            category=getattr(metadata, "category", "general"),
            status=getattr(metadata, "status", "active"),
            version=metadata.version,
            capabilities=getattr(metadata, "capabilities", []),
            tools=tools_as_dicts,
            cost_per_interaction=getattr(metadata, "cost_per_interaction", 0.1),
            max_context_tokens=getattr(metadata, "max_context_tokens", 8000),
            temperature=getattr(metadata, "temperature", 0.7),
            model_preference=getattr(metadata, "model_preference", "gpt-4-turbo-preview")
        ))
    
    return result[:limit]


@router.get("/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str):
    """Get specific agent by ID"""
    agent = agent_loader.get_agent(agent_id)
    
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    metadata = agent.get("metadata", {})
    
    return AgentResponse(
        id=agent_id,
        name=metadata.get("name", agent_id),
        role=metadata.get("role", ""),
        tier=metadata.get("tier", "specialist"),
        category=metadata.get("category", "general"),
        status=metadata.get("status", "active"),
        version=metadata.get("version", "1.0.0"),
        capabilities=metadata.get("capabilities", []),
        tools=metadata.get("tools", []),
        cost_per_interaction=metadata.get("cost_per_interaction", 0.1),
        max_context_tokens=metadata.get("max_context_tokens", 8000),
        temperature=metadata.get("temperature", 0.7),
        model_preference=metadata.get("model_preference", "gpt-4-turbo-preview")
    )


@router.post("/agents", response_model=AgentResponse)
async def create_agent(agent: AgentCreate):
    """Create a new agent"""
    # Generate agent ID from name
    agent_id = agent.name.lower().replace(" ", "_").replace("-", "_")
    
    # Check if agent already exists
    existing = agent_loader.get_agent(agent_id)
    if existing:
        raise HTTPException(status_code=409, detail=f"Agent {agent_id} already exists")
    
    # Create agent definition file
    agent_def = f"""---
agent_id: {agent_id}
name: {agent.name}
role: {agent.role}
tier: {agent.tier}
category: {agent.category}
version: 1.0.0
status: active
capabilities: {json.dumps(agent.capabilities)}
tools: {json.dumps(agent.tools)}
cost_per_interaction: {agent.cost_per_interaction}
max_context_tokens: {agent.max_context_tokens}
temperature: {agent.temperature}
model_preference: {agent.model_preference}
---

# {agent.name}

## System Prompt

{agent.system_prompt or f"You are {agent.name}, a {agent.role}."}
"""
    
    # Save agent definition
    agent_path = Path(f"backend/src/agents/definitions/{agent_id}.md")
    agent_path.write_text(agent_def)
    
    # Reload agents
    agent_loader.scan_and_load_agents()
    
    return AgentResponse(
        id=agent_id,
        name=agent.name,
        role=agent.role,
        tier=agent.tier,
        category=agent.category,
        status="active",
        version="1.0.0",
        capabilities=agent.capabilities,
        tools=agent.tools,
        cost_per_interaction=agent.cost_per_interaction,
        max_context_tokens=agent.max_context_tokens,
        temperature=agent.temperature,
        model_preference=agent.model_preference,
        created_at=datetime.utcnow().isoformat()
    )


@router.put("/agents/{agent_id}", response_model=AgentResponse)
async def update_agent(agent_id: str, update: AgentUpdate):
    """Update an existing agent"""
    agent = agent_loader.get_agent(agent_id)
    
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    metadata = agent.get("metadata", {})
    
    # Apply updates
    if update.role is not None:
        metadata["role"] = update.role
    if update.tier is not None:
        metadata["tier"] = update.tier
    if update.category is not None:
        metadata["category"] = update.category
    if update.capabilities is not None:
        metadata["capabilities"] = update.capabilities
    if update.tools is not None:
        metadata["tools"] = update.tools
    if update.max_context_tokens is not None:
        metadata["max_context_tokens"] = update.max_context_tokens
    if update.temperature is not None:
        metadata["temperature"] = update.temperature
    if update.model_preference is not None:
        metadata["model_preference"] = update.model_preference
    if update.cost_per_interaction is not None:
        metadata["cost_per_interaction"] = update.cost_per_interaction
    
    # Update version
    version_parts = metadata.get("version", "1.0.0").split(".")
    version_parts[2] = str(int(version_parts[2]) + 1)
    metadata["version"] = ".".join(version_parts)
    
    # Save updated agent (simplified - in production would update the .md file)
    agent_loader.agents[agent_id]["metadata"] = metadata
    
    return AgentResponse(
        id=agent_id,
        name=metadata.get("name", agent_id),
        role=metadata.get("role", ""),
        tier=metadata.get("tier", "specialist"),
        category=metadata.get("category", "general"),
        status=metadata.get("status", "active"),
        version=metadata.get("version", "1.0.0"),
        capabilities=metadata.get("capabilities", []),
        tools=metadata.get("tools", []),
        cost_per_interaction=metadata.get("cost_per_interaction", 0.1),
        max_context_tokens=metadata.get("max_context_tokens", 8000),
        temperature=metadata.get("temperature", 0.7),
        model_preference=metadata.get("model_preference", "gpt-4-turbo-preview"),
        updated_at=datetime.utcnow().isoformat()
    )


@router.delete("/agents/{agent_id}")
async def delete_agent(agent_id: str):
    """Delete an agent"""
    agent = agent_loader.get_agent(agent_id)
    
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    # Mark as deprecated instead of deleting
    metadata = agent.get("metadata", {})
    metadata["status"] = "deprecated"
    agent_loader.agents[agent_id]["metadata"] = metadata
    
    return {"message": f"Agent {agent_id} marked as deprecated"}


# ===================== Agent Operations =====================

@router.post("/agents/{agent_id}/validate")
async def validate_agent(agent_id: str):
    """Validate agent configuration"""
    agent = agent_loader.get_agent(agent_id)
    
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    # Run validation
    errors = []
    warnings = []
    metadata = agent.get("metadata", {})
    
    # Check required fields
    if not metadata.get("role"):
        errors.append("Missing required field: role")
    if not metadata.get("capabilities"):
        warnings.append("No capabilities defined")
    if metadata.get("temperature", 0.7) > 1.5:
        warnings.append("Temperature is very high, may produce inconsistent results")
    
    # Check system prompt
    system_prompt = agent.get("system_prompt", "")
    if len(system_prompt) < 50:
        warnings.append("System prompt is very short")
    if len(system_prompt) > 5000:
        warnings.append("System prompt is very long")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "message": "Validation passed" if not errors else f"Validation failed: {', '.join(errors)}"
    }


@router.post("/agents/{agent_id}/reload")
async def reload_agent(agent_id: str):
    """Hot-reload an agent"""
    agent = agent_loader.get_agent(agent_id)
    
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    # Trigger hot-reload
    agent_loader.reload_agent(agent_id)
    
    return {
        "message": f"Agent {agent_id} reloaded successfully",
        "version": agent.get("metadata", {}).get("version", "1.0.0")
    }


@router.get("/agents/{agent_id}/history")
async def get_agent_history(agent_id: str):
    """Get agent version history"""
    history = agent_loader.get_version_history(agent_id)
    
    if not history:
        raise HTTPException(status_code=404, detail=f"No history found for agent {agent_id}")
    
    return {
        "agent_id": agent_id,
        "versions": history,
        "current_version": agent_loader.get_agent(agent_id).get("metadata", {}).get("version", "1.0.0")
    }


@router.post("/agents/{agent_id}/rollback")
async def rollback_agent(agent_id: str, version: str):
    """Rollback agent to previous version"""
    success = agent_loader.rollback_agent(agent_id, version)
    
    if not success:
        raise HTTPException(status_code=400, detail=f"Failed to rollback agent {agent_id} to version {version}")
    
    return {
        "message": f"Agent {agent_id} rolled back to version {version}",
        "current_version": version
    }


# ===================== Bulk Operations =====================

@router.post("/agents/bulk/validate")
async def validate_all_agents():
    """Validate all agents"""
    agents = agent_loader.list_agents()
    results = {}
    
    for agent_id in agents:
        agent = agent_loader.get_agent(agent_id)
        metadata = agent.get("metadata", {})
        
        errors = []
        if not metadata.get("role"):
            errors.append("Missing role")
        if not agent.get("system_prompt"):
            errors.append("Missing system prompt")
        
        results[agent_id] = {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    valid_count = sum(1 for r in results.values() if r["valid"])
    
    return {
        "total": len(results),
        "valid": valid_count,
        "invalid": len(results) - valid_count,
        "results": results
    }


@router.post("/agents/bulk/reload")
async def reload_all_agents():
    """Hot-reload all agents"""
    agent_loader.scan_and_load_agents()
    
    return {
        "message": "All agents reloaded successfully",
        "agent_count": len(agent_loader.agents)
    }