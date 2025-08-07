"""
Component Serialization System for AutoGen Agents
Save and restore agent states, configurations, and conversation contexts
"""

import json
import pickle
import base64
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import structlog
from uuid import uuid4
import asyncio

from src.core.config import settings
from src.core.redis import get_redis_client
from src.agents.services.agent_loader import agent_loader

logger = structlog.get_logger()

@dataclass
class SerializedComponent:
    """Represents a serialized component"""
    component_id: str
    component_type: str  # 'agent', 'conversation', 'workflow', 'memory'
    name: str
    serialized_data: str
    serialization_format: str  # 'json', 'pickle', 'base64'
    created_at: datetime
    version: str
    metadata: Dict[str, Any]
    checksum: str

@dataclass
class SerializationSnapshot:
    """Complete system snapshot"""
    snapshot_id: str
    snapshot_name: str
    created_at: datetime
    components: List[SerializedComponent]
    system_metadata: Dict[str, Any]
    total_size_bytes: int

class ComponentSerializer:
    """Manages serialization and deserialization of AutoGen components"""
    
    def __init__(self):
        self.serialized_components: Dict[str, SerializedComponent] = {}
        self.snapshots: Dict[str, SerializationSnapshot] = {}
        self.redis_client = None
        self.serialization_dir = Path("data/serialization")
        
    async def initialize(self):
        """Initialize the component serializer"""
        logger.info("💾 Initializing Component Serializer")
        
        # Initialize Redis connection
        self.redis_client = get_redis_client()
        
        # Create serialization directory
        self.serialization_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing serialized components
        await self._load_serialized_components()
        
        logger.info(f"✅ Component Serializer initialized with {len(self.serialized_components)} components")

    async def _load_serialized_components(self):
        """Load existing serialized components from storage"""
        
        try:
            # Load from Redis
            if self.redis_client:
                keys = await self.redis_client.keys("serialized_component:*")
                for key in keys:
                    component_data = await self.redis_client.get(key)
                    if component_data:
                        component_dict = json.loads(component_data)
                        # Convert datetime string back to datetime
                        component_dict['created_at'] = datetime.fromisoformat(component_dict['created_at'])
                        component = SerializedComponent(**component_dict)
                        self.serialized_components[component.component_id] = component
            
            # Load snapshots
            snapshot_keys = await self.redis_client.keys("serialization_snapshot:*") if self.redis_client else []
            for key in snapshot_keys:
                snapshot_data = await self.redis_client.get(key)
                if snapshot_data:
                    snapshot_dict = json.loads(snapshot_data)
                    # Convert datetime and component data
                    snapshot_dict['created_at'] = datetime.fromisoformat(snapshot_dict['created_at'])
                    
                    # Reconstruct components
                    components = []
                    for comp_data in snapshot_dict['components']:
                        comp_data['created_at'] = datetime.fromisoformat(comp_data['created_at'])
                        components.append(SerializedComponent(**comp_data))
                    
                    snapshot_dict['components'] = components
                    snapshot = SerializationSnapshot(**snapshot_dict)
                    self.snapshots[snapshot.snapshot_id] = snapshot
                    
            logger.info(f"💾 Loaded {len(self.serialized_components)} components and {len(self.snapshots)} snapshots")
            
        except Exception as e:
            logger.warning(f"⚠️ Could not load serialized components: {e}")

    async def serialize_agent_configuration(
        self,
        agent_name: str,
        include_state: bool = True
    ) -> SerializedComponent:
        """Serialize an agent's configuration and state"""
        
        try:
            # Get agent configuration
            agent_config = await agent_loader.get_agent_config(agent_name)
            if not agent_config:
                raise ValueError(f"Agent {agent_name} not found")
            
            # Prepare serialization data
            serialization_data = {
                "agent_name": agent_name,
                "agent_config": agent_config,
                "serialized_at": datetime.utcnow().isoformat(),
                "include_state": include_state
            }
            
            # Add state data if requested
            if include_state:
                # Get conversation history from memory system
                from src.agents.memory.autogen_memory_system import AutoGenMemorySystem
                memory_system = AutoGenMemorySystem()
                
                try:
                    # Get recent conversations
                    conversation_history = await memory_system.get_conversation_history(
                        agent_name=agent_name,
                        limit=50
                    )
                    serialization_data["conversation_history"] = conversation_history
                    
                    # Get agent memory context
                    memory_context = await memory_system.get_memory_context(
                        agent_name=agent_name,
                        context_type="agent_state"
                    )
                    serialization_data["memory_context"] = memory_context
                    
                except Exception as e:
                    logger.warning(f"⚠️ Could not include state for {agent_name}: {e}")
                    serialization_data["state_error"] = str(e)
            
            # Serialize to JSON
            serialized_json = json.dumps(serialization_data, indent=2, default=str)
            
            # Calculate checksum
            import hashlib
            checksum = hashlib.md5(serialized_json.encode()).hexdigest()
            
            # Create serialized component
            component = SerializedComponent(
                component_id=str(uuid4()),
                component_type="agent",
                name=agent_name,
                serialized_data=serialized_json,
                serialization_format="json",
                created_at=datetime.utcnow(),
                version="1.0",
                metadata={
                    "include_state": include_state,
                    "agent_type": agent_config.get("type", "unknown"),
                    "serialization_size": len(serialized_json)
                },
                checksum=checksum
            )
            
            # Store component
            self.serialized_components[component.component_id] = component
            await self._save_component_to_storage(component)
            
            logger.info(f"💾 Serialized agent {agent_name} (ID: {component.component_id})")
            return component
            
        except Exception as e:
            logger.error(f"❌ Failed to serialize agent {agent_name}: {e}")
            raise

    async def serialize_conversation_context(
        self,
        conversation_id: str,
        agent_name: str,
        messages: List[Dict[str, Any]]
    ) -> SerializedComponent:
        """Serialize a conversation context"""
        
        try:
            # Prepare conversation data
            conversation_data = {
                "conversation_id": conversation_id,
                "agent_name": agent_name,
                "messages": messages,
                "message_count": len(messages),
                "serialized_at": datetime.utcnow().isoformat(),
                "conversation_metadata": {
                    "first_message_time": messages[0].get("timestamp") if messages else None,
                    "last_message_time": messages[-1].get("timestamp") if messages else None
                }
            }
            
            # Serialize to JSON
            serialized_json = json.dumps(conversation_data, indent=2, default=str)
            
            # Calculate checksum
            import hashlib
            checksum = hashlib.md5(serialized_json.encode()).hexdigest()
            
            # Create serialized component
            component = SerializedComponent(
                component_id=str(uuid4()),
                component_type="conversation",
                name=f"{agent_name}_conversation_{conversation_id}",
                serialized_data=serialized_json,
                serialization_format="json",
                created_at=datetime.utcnow(),
                version="1.0",
                metadata={
                    "conversation_id": conversation_id,
                    "agent_name": agent_name,
                    "message_count": len(messages),
                    "serialization_size": len(serialized_json)
                },
                checksum=checksum
            )
            
            # Store component
            self.serialized_components[component.component_id] = component
            await self._save_component_to_storage(component)
            
            logger.info(f"💾 Serialized conversation {conversation_id} for {agent_name}")
            return component
            
        except Exception as e:
            logger.error(f"❌ Failed to serialize conversation {conversation_id}: {e}")
            raise

    async def serialize_workflow_state(
        self,
        workflow_id: str,
        workflow_data: Dict[str, Any]
    ) -> SerializedComponent:
        """Serialize a workflow state"""
        
        try:
            # Prepare workflow serialization data
            serialization_data = {
                "workflow_id": workflow_id,
                "workflow_data": workflow_data,
                "serialized_at": datetime.utcnow().isoformat(),
                "workflow_type": workflow_data.get("type", "unknown")
            }
            
            # Use pickle for complex workflow objects
            serialized_pickle = pickle.dumps(serialization_data)
            serialized_base64 = base64.b64encode(serialized_pickle).decode()
            
            # Calculate checksum
            import hashlib
            checksum = hashlib.md5(serialized_pickle).hexdigest()
            
            # Create serialized component
            component = SerializedComponent(
                component_id=str(uuid4()),
                component_type="workflow",
                name=f"workflow_{workflow_id}",
                serialized_data=serialized_base64,
                serialization_format="pickle_base64",
                created_at=datetime.utcnow(),
                version="1.0",
                metadata={
                    "workflow_id": workflow_id,
                    "workflow_type": workflow_data.get("type", "unknown"),
                    "serialization_size": len(serialized_base64)
                },
                checksum=checksum
            )
            
            # Store component
            self.serialized_components[component.component_id] = component
            await self._save_component_to_storage(component)
            
            logger.info(f"💾 Serialized workflow {workflow_id}")
            return component
            
        except Exception as e:
            logger.error(f"❌ Failed to serialize workflow {workflow_id}: {e}")
            raise

    async def deserialize_component(
        self,
        component_id: str
    ) -> Dict[str, Any]:
        """Deserialize a component and return its data"""
        
        try:
            component = self.serialized_components.get(component_id)
            if not component:
                raise ValueError(f"Component {component_id} not found")
            
            # Deserialize based on format
            if component.serialization_format == "json":
                deserialized_data = json.loads(component.serialized_data)
            
            elif component.serialization_format == "pickle_base64":
                serialized_bytes = base64.b64decode(component.serialized_data.encode())
                deserialized_data = pickle.loads(serialized_bytes)
            
            else:
                raise ValueError(f"Unsupported serialization format: {component.serialization_format}")
            
            # Verify checksum
            import hashlib
            if component.serialization_format == "json":
                current_checksum = hashlib.md5(component.serialized_data.encode()).hexdigest()
            else:
                current_checksum = hashlib.md5(base64.b64decode(component.serialized_data.encode())).hexdigest()
            
            if current_checksum != component.checksum:
                logger.warning(f"⚠️ Checksum mismatch for component {component_id}")
            
            logger.info(f"💾 Deserialized component {component_id} ({component.component_type})")
            return deserialized_data
            
        except Exception as e:
            logger.error(f"❌ Failed to deserialize component {component_id}: {e}")
            raise

    async def create_system_snapshot(
        self,
        snapshot_name: str,
        include_agents: bool = True,
        include_conversations: bool = True,
        include_workflows: bool = True
    ) -> SerializationSnapshot:
        """Create a complete system snapshot"""
        
        try:
            snapshot_components = []
            total_size = 0
            
            # Serialize agents if requested
            if include_agents:
                all_agents = await agent_loader.get_all_agents()
                for agent_name in all_agents.keys():
                    try:
                        component = await self.serialize_agent_configuration(
                            agent_name=agent_name,
                            include_state=True
                        )
                        snapshot_components.append(component)
                        total_size += len(component.serialized_data)
                    except Exception as e:
                        logger.warning(f"⚠️ Could not serialize agent {agent_name} for snapshot: {e}")
            
            # Include existing conversations if requested
            if include_conversations:
                conversation_components = [
                    comp for comp in self.serialized_components.values()
                    if comp.component_type == "conversation"
                ]
                snapshot_components.extend(conversation_components)
                total_size += sum(len(comp.serialized_data) for comp in conversation_components)
            
            # Include workflows if requested
            if include_workflows:
                workflow_components = [
                    comp for comp in self.serialized_components.values()
                    if comp.component_type == "workflow"
                ]
                snapshot_components.extend(workflow_components)
                total_size += sum(len(comp.serialized_data) for comp in workflow_components)
            
            # Create snapshot
            snapshot = SerializationSnapshot(
                snapshot_id=str(uuid4()),
                snapshot_name=snapshot_name,
                created_at=datetime.utcnow(),
                components=snapshot_components,
                system_metadata={
                    "include_agents": include_agents,
                    "include_conversations": include_conversations,
                    "include_workflows": include_workflows,
                    "total_components": len(snapshot_components),
                    "snapshot_version": "1.0"
                },
                total_size_bytes=total_size
            )
            
            # Store snapshot
            self.snapshots[snapshot.snapshot_id] = snapshot
            await self._save_snapshot_to_storage(snapshot)
            
            logger.info(f"📸 Created system snapshot '{snapshot_name}' with {len(snapshot_components)} components")
            return snapshot
            
        except Exception as e:
            logger.error(f"❌ Failed to create system snapshot: {e}")
            raise

    async def restore_from_snapshot(
        self,
        snapshot_id: str,
        restore_agents: bool = True,
        restore_conversations: bool = True,
        restore_workflows: bool = True
    ) -> Dict[str, Any]:
        """Restore system from a snapshot"""
        
        try:
            snapshot = self.snapshots.get(snapshot_id)
            if not snapshot:
                raise ValueError(f"Snapshot {snapshot_id} not found")
            
            restoration_results = {
                "snapshot_id": snapshot_id,
                "snapshot_name": snapshot.snapshot_name,
                "restored_components": [],
                "failed_restorations": [],
                "restoration_summary": {}
            }
            
            for component in snapshot.components:
                try:
                    # Check if we should restore this component type
                    should_restore = (
                        (component.component_type == "agent" and restore_agents) or
                        (component.component_type == "conversation" and restore_conversations) or
                        (component.component_type == "workflow" and restore_workflows)
                    )
                    
                    if not should_restore:
                        continue
                    
                    # Deserialize component
                    restored_data = await self.deserialize_component(component.component_id)
                    
                    # Perform component-specific restoration
                    restoration_result = await self._restore_component(component, restored_data)
                    
                    restoration_results["restored_components"].append({
                        "component_id": component.component_id,
                        "component_type": component.component_type,
                        "name": component.name,
                        "restoration_result": restoration_result
                    })
                    
                except Exception as e:
                    logger.error(f"❌ Failed to restore component {component.component_id}: {e}")
                    restoration_results["failed_restorations"].append({
                        "component_id": component.component_id,
                        "component_type": component.component_type,
                        "name": component.name,
                        "error": str(e)
                    })
            
            # Generate restoration summary
            restoration_results["restoration_summary"] = {
                "total_components": len(snapshot.components),
                "restored_successfully": len(restoration_results["restored_components"]),
                "failed_restorations": len(restoration_results["failed_restorations"]),
                "restoration_time": datetime.utcnow().isoformat()
            }
            
            logger.info(f"🔄 Restored {len(restoration_results['restored_components'])} components from snapshot '{snapshot.snapshot_name}'")
            return restoration_results
            
        except Exception as e:
            logger.error(f"❌ Failed to restore from snapshot {snapshot_id}: {e}")
            raise

    async def _restore_component(
        self,
        component: SerializedComponent,
        restored_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Restore a specific component based on its type"""
        
        if component.component_type == "agent":
            # For agents, we mainly restore configuration
            # The actual agent instantiation would be handled by the orchestrator
            return {
                "type": "agent_configuration",
                "agent_name": restored_data.get("agent_name"),
                "config_restored": True,
                "state_included": restored_data.get("include_state", False)
            }
        
        elif component.component_type == "conversation":
            # For conversations, restore to memory system
            try:
                from src.agents.memory.autogen_memory_system import AutoGenMemorySystem
                memory_system = AutoGenMemorySystem()
                
                agent_name = restored_data.get("agent_name")
                messages = restored_data.get("messages", [])
                
                # Store conversation history
                for message in messages:
                    if message.get("role") == "user":
                        await memory_system.store_conversation(
                            agent_name=agent_name,
                            user_id=message.get("user_id", "restored_user"),
                            user_message=message.get("content", ""),
                            agent_response="",
                            context=message.get("context", {})
                        )
                
                return {
                    "type": "conversation_restored",
                    "agent_name": agent_name,
                    "messages_restored": len(messages)
                }
            except Exception as e:
                return {
                    "type": "conversation_restoration_failed",
                    "error": str(e)
                }
        
        elif component.component_type == "workflow":
            # For workflows, we would need to recreate them in the GraphFlow orchestrator
            return {
                "type": "workflow_data_restored",
                "workflow_id": restored_data.get("workflow_id"),
                "note": "Workflow data restored but not automatically restarted"
            }
        
        else:
            return {
                "type": "unknown_component_type",
                "component_type": component.component_type
            }

    async def _save_component_to_storage(self, component: SerializedComponent):
        """Save component to Redis storage"""
        
        try:
            if self.redis_client:
                component_dict = asdict(component)
                component_dict['created_at'] = component.created_at.isoformat()
                
                await self.redis_client.setex(
                    f"serialized_component:{component.component_id}",
                    86400 * 30,  # 30 days TTL
                    json.dumps(component_dict, default=str)
                )
        except Exception as e:
            logger.warning(f"⚠️ Could not save component to storage: {e}")

    async def _save_snapshot_to_storage(self, snapshot: SerializationSnapshot):
        """Save snapshot to Redis storage"""
        
        try:
            if self.redis_client:
                snapshot_dict = asdict(snapshot)
                snapshot_dict['created_at'] = snapshot.created_at.isoformat()
                
                # Convert components to dictionaries
                snapshot_dict['components'] = [
                    {
                        **asdict(comp),
                        'created_at': comp.created_at.isoformat()
                    }
                    for comp in snapshot.components
                ]
                
                await self.redis_client.setex(
                    f"serialization_snapshot:{snapshot.snapshot_id}",
                    86400 * 90,  # 90 days TTL
                    json.dumps(snapshot_dict, default=str)
                )
        except Exception as e:
            logger.warning(f"⚠️ Could not save snapshot to storage: {e}")

    async def list_components(self, component_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all serialized components with optional type filter"""
        
        components = []
        for component in self.serialized_components.values():
            if component_type and component.component_type != component_type:
                continue
                
            components.append({
                "component_id": component.component_id,
                "component_type": component.component_type,
                "name": component.name,
                "created_at": component.created_at.isoformat(),
                "size_bytes": len(component.serialized_data),
                "format": component.serialization_format,
                "version": component.version,
                "metadata": component.metadata
            })
        
        return sorted(components, key=lambda x: x["created_at"], reverse=True)

    async def list_snapshots(self) -> List[Dict[str, Any]]:
        """List all system snapshots"""
        
        snapshots = []
        for snapshot in self.snapshots.values():
            snapshots.append({
                "snapshot_id": snapshot.snapshot_id,
                "snapshot_name": snapshot.snapshot_name,
                "created_at": snapshot.created_at.isoformat(),
                "component_count": len(snapshot.components),
                "total_size_bytes": snapshot.total_size_bytes,
                "system_metadata": snapshot.system_metadata
            })
        
        return sorted(snapshots, key=lambda x: x["created_at"], reverse=True)

    async def delete_component(self, component_id: str) -> bool:
        """Delete a serialized component"""
        
        try:
            if component_id in self.serialized_components:
                del self.serialized_components[component_id]
                
                # Remove from Redis
                if self.redis_client:
                    await self.redis_client.delete(f"serialized_component:{component_id}")
                
                logger.info(f"💾 Deleted serialized component {component_id}")
                return True
            else:
                return False
        except Exception as e:
            logger.error(f"❌ Failed to delete component {component_id}: {e}")
            return False

    async def delete_snapshot(self, snapshot_id: str) -> bool:
        """Delete a system snapshot"""
        
        try:
            if snapshot_id in self.snapshots:
                del self.snapshots[snapshot_id]
                
                # Remove from Redis
                if self.redis_client:
                    await self.redis_client.delete(f"serialization_snapshot:{snapshot_id}")
                
                logger.info(f"📸 Deleted snapshot {snapshot_id}")
                return True
            else:
                return False
        except Exception as e:
            logger.error(f"❌ Failed to delete snapshot {snapshot_id}: {e}")
            return False

# Global component serializer instance
component_serializer = ComponentSerializer()