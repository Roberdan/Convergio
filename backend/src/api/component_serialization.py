"""
Component Serialization API
REST endpoints for managing agent state serialization and system snapshots
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from ..agents.serialization.component_serializer import component_serializer
from ..core.logging import get_logger

logger = get_logger()
router = APIRouter()

# Pydantic models
class SerializeAgentRequest(BaseModel):
    agent_name: str = Field(..., description="Name of the agent to serialize")
    include_state: bool = Field(True, description="Include conversation history and memory state")

class SerializeConversationRequest(BaseModel):
    conversation_id: str = Field(..., description="ID of the conversation to serialize")
    agent_name: str = Field(..., description="Name of the agent in the conversation")
    messages: List[Dict[str, Any]] = Field(..., description="List of conversation messages")

class CreateSnapshotRequest(BaseModel):
    snapshot_name: str = Field(..., description="Name for the snapshot")
    include_agents: bool = Field(True, description="Include agent configurations")
    include_conversations: bool = Field(True, description="Include conversation histories")
    include_workflows: bool = Field(True, description="Include workflow states")

class RestoreSnapshotRequest(BaseModel):
    snapshot_id: str = Field(..., description="ID of the snapshot to restore")
    restore_agents: bool = Field(True, description="Restore agent configurations")
    restore_conversations: bool = Field(True, description="Restore conversation histories")
    restore_workflows: bool = Field(True, description="Restore workflow states")

class ComponentResponse(BaseModel):
    component_id: str
    component_type: str
    name: str
    created_at: datetime
    message: str

class SnapshotResponse(BaseModel):
    snapshot_id: str
    snapshot_name: str
    created_at: datetime
    component_count: int
    total_size_bytes: int
    message: str

@router.on_event("startup")
async def startup_serialization():
    """Initialize component serializer on startup"""
    try:
        await component_serializer.initialize()
        logger.info("✅ Component Serialization API initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize serialization API: {e}")

@router.post("/agent", response_model=ComponentResponse)
async def serialize_agent(request: SerializeAgentRequest):
    """
    Serialize an agent's configuration and state
    """
    try:
        logger.info(f"💾 Serializing agent {request.agent_name}")
        
        component = await component_serializer.serialize_agent_configuration(
            agent_name=request.agent_name,
            include_state=request.include_state
        )
        
        return ComponentResponse(
            component_id=component.component_id,
            component_type=component.component_type,
            name=component.name,
            created_at=component.created_at,
            message=f"Agent {request.agent_name} serialized successfully"
        )
        
    except Exception as e:
        logger.error(f"❌ Error serializing agent {request.agent_name}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to serialize agent: {str(e)}"
        )

@router.post("/conversation", response_model=ComponentResponse)
async def serialize_conversation(request: SerializeConversationRequest):
    """
    Serialize a conversation context
    """
    try:
        logger.info(f"💾 Serializing conversation {request.conversation_id} for {request.agent_name}")
        
        component = await component_serializer.serialize_conversation_context(
            conversation_id=request.conversation_id,
            agent_name=request.agent_name,
            messages=request.messages
        )
        
        return ComponentResponse(
            component_id=component.component_id,
            component_type=component.component_type,
            name=component.name,
            created_at=component.created_at,
            message=f"Conversation {request.conversation_id} serialized successfully"
        )
        
    except Exception as e:
        logger.error(f"❌ Error serializing conversation {request.conversation_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to serialize conversation: {str(e)}"
        )

@router.post("/snapshot", response_model=SnapshotResponse)
async def create_system_snapshot(request: CreateSnapshotRequest, background_tasks: BackgroundTasks):
    """
    Create a complete system snapshot
    """
    try:
        logger.info(f"📸 Creating system snapshot '{request.snapshot_name}'")
        
        snapshot = await component_serializer.create_system_snapshot(
            snapshot_name=request.snapshot_name,
            include_agents=request.include_agents,
            include_conversations=request.include_conversations,
            include_workflows=request.include_workflows
        )
        
        return SnapshotResponse(
            snapshot_id=snapshot.snapshot_id,
            snapshot_name=snapshot.snapshot_name,
            created_at=snapshot.created_at,
            component_count=len(snapshot.components),
            total_size_bytes=snapshot.total_size_bytes,
            message=f"System snapshot '{request.snapshot_name}' created successfully"
        )
        
    except Exception as e:
        logger.error(f"❌ Error creating system snapshot: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create system snapshot: {str(e)}"
        )

@router.post("/restore")
async def restore_from_snapshot(request: RestoreSnapshotRequest):
    """
    Restore system from a snapshot
    """
    try:
        logger.info(f"🔄 Restoring from snapshot {request.snapshot_id}")
        
        restoration_results = await component_serializer.restore_from_snapshot(
            snapshot_id=request.snapshot_id,
            restore_agents=request.restore_agents,
            restore_conversations=request.restore_conversations,
            restore_workflows=request.restore_workflows
        )
        
        return {
            "restoration_results": restoration_results,
            "message": f"Restoration from snapshot {request.snapshot_id} completed",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error restoring from snapshot {request.snapshot_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to restore from snapshot: {str(e)}"
        )

@router.get("/components")
async def list_components(component_type: Optional[str] = None):
    """
    List all serialized components with optional type filter
    """
    try:
        components = await component_serializer.list_components(component_type=component_type)
        
        return {
            "components": components,
            "total_count": len(components),
            "component_type_filter": component_type,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error listing components: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list components: {str(e)}"
        )

@router.get("/snapshots")
async def list_snapshots():
    """
    List all system snapshots
    """
    try:
        snapshots = await component_serializer.list_snapshots()
        
        return {
            "snapshots": snapshots,
            "total_count": len(snapshots),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error listing snapshots: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list snapshots: {str(e)}"
        )

@router.get("/component/{component_id}")
async def get_component_details(component_id: str):
    """
    Get detailed information about a specific component
    """
    try:
        if component_id not in component_serializer.serialized_components:
            raise HTTPException(
                status_code=404,
                detail=f"Component {component_id} not found"
            )
        
        component = component_serializer.serialized_components[component_id]
        
        return {
            "component_id": component.component_id,
            "component_type": component.component_type,
            "name": component.name,
            "created_at": component.created_at.isoformat(),
            "version": component.version,
            "serialization_format": component.serialization_format,
            "checksum": component.checksum,
            "metadata": component.metadata,
            "size_bytes": len(component.serialized_data)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting component details: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get component details: {str(e)}"
        )

@router.post("/component/{component_id}/deserialize")
async def deserialize_component(component_id: str):
    """
    Deserialize a component and return its data
    """
    try:
        deserialized_data = await component_serializer.deserialize_component(component_id)
        
        # Remove sensitive data before returning
        if isinstance(deserialized_data, dict):
            # Don't return full conversation histories or large data structures
            safe_data = {
                "component_id": component_id,
                "deserialization_successful": True,
                "data_type": type(deserialized_data).__name__,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Add safe metadata
            if "agent_name" in deserialized_data:
                safe_data["agent_name"] = deserialized_data["agent_name"]
            if "serialized_at" in deserialized_data:
                safe_data["originally_serialized_at"] = deserialized_data["serialized_at"]
            if "message_count" in deserialized_data:
                safe_data["message_count"] = deserialized_data["message_count"]
                
            return safe_data
        else:
            return {
                "component_id": component_id,
                "deserialization_successful": True,
                "data_type": type(deserialized_data).__name__,
                "timestamp": datetime.utcnow().isoformat()
            }
        
    except Exception as e:
        logger.error(f"❌ Error deserializing component {component_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to deserialize component: {str(e)}"
        )

@router.delete("/component/{component_id}")
async def delete_component(component_id: str):
    """
    Delete a serialized component
    """
    try:
        success = await component_serializer.delete_component(component_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Component {component_id} not found"
            )
        
        return {
            "component_id": component_id,
            "deleted": True,
            "message": f"Component {component_id} deleted successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting component {component_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete component: {str(e)}"
        )

@router.delete("/snapshot/{snapshot_id}")
async def delete_snapshot(snapshot_id: str):
    """
    Delete a system snapshot
    """
    try:
        success = await component_serializer.delete_snapshot(snapshot_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Snapshot {snapshot_id} not found"
            )
        
        return {
            "snapshot_id": snapshot_id,
            "deleted": True,
            "message": f"Snapshot {snapshot_id} deleted successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting snapshot {snapshot_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete snapshot: {str(e)}"
        )

@router.get("/stats")
async def get_serialization_stats():
    """
    Get serialization system statistics
    """
    try:
        components = await component_serializer.list_components()
        snapshots = await component_serializer.list_snapshots()
        
        # Calculate statistics
        component_types = {}
        total_size = 0
        
        for component in components:
            comp_type = component["component_type"]
            component_types[comp_type] = component_types.get(comp_type, 0) + 1
            total_size += component.get("size_bytes", 0)
        
        snapshot_total_size = sum(
            snapshot.get("total_size_bytes", 0) for snapshot in snapshots
        )
        
        return {
            "serialization_stats": {
                "total_components": len(components),
                "component_types": component_types,
                "total_snapshots": len(snapshots),
                "total_components_size_bytes": total_size,
                "total_snapshots_size_bytes": snapshot_total_size,
                "system_initialized": hasattr(component_serializer, 'redis_client') and component_serializer.redis_client is not None
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting serialization stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get serialization stats: {str(e)}"
        )

@router.get("/health")
async def serialization_health_check():
    """Health check for serialization system"""
    try:
        components = await component_serializer.list_components()
        snapshots = await component_serializer.list_snapshots()
        
        return {
            "status": "healthy",
            "serializer_initialized": hasattr(component_serializer, 'redis_client') and component_serializer.redis_client is not None,
            "total_components": len(components),
            "total_snapshots": len(snapshots),
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Component serialization system operational"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Component serialization system error"
        }