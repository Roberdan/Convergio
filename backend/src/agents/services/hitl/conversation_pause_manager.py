"""
Conversation Pause Manager - Handles pause/resume for HITL approvals
Integrates with orchestrator to control conversation flow during approvals
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, Callable, List
from dataclasses import dataclass
from enum import Enum
import structlog

import redis.asyncio as redis

from .approval_store_redis import (
    RedisApprovalStore, ApprovalRequest, ApprovalStatus
)

logger = structlog.get_logger()


class ConversationState(Enum):
    """Conversation states for pause management"""
    ACTIVE = "active"
    PAUSED = "paused"
    RESUMED = "resumed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


@dataclass
class PausedConversation:
    """Represents a paused conversation waiting for approval"""
    conversation_id: str
    approval_id: str
    paused_at: datetime
    pause_reason: str
    context_snapshot: Dict[str, Any]
    pending_message: Optional[str] = None
    resume_callback: Optional[Callable] = None
    timeout_seconds: int = 3600
    
    def is_expired(self) -> bool:
        """Check if pause has expired"""
        elapsed = (datetime.utcnow() - self.paused_at).total_seconds()
        return elapsed > self.timeout_seconds


class ConversationPauseManager:
    """Manages conversation pause/resume lifecycle for HITL approvals"""
    
    def __init__(
        self,
        approval_store: RedisApprovalStore,
        redis_client: Optional[redis.Redis] = None
    ):
        self.approval_store = approval_store
        self.redis = redis_client
        self.paused_conversations: Dict[str, PausedConversation] = {}
        self.state_callbacks: Dict[str, List[Callable]] = {
            "on_pause": [],
            "on_resume": [],
            "on_timeout": [],
            "on_cancel": []
        }
        self.key_prefix = "conversation:pause:"
        
    async def initialize(self):
        """Initialize manager and restore paused conversations from Redis"""
        if self.redis:
            # Scan for existing paused conversations
            pattern = f"{self.key_prefix}*"
            cursor = 0
            
            while True:
                cursor, keys = await self.redis.scan(cursor, match=pattern)
                
                for key in keys:
                    conversation_id = key.replace(self.key_prefix, "")
                    data = await self.redis.get(key)
                    
                    if data:
                        import json
                        pause_data = json.loads(data)
                        
                        # Restore paused conversation
                        paused = PausedConversation(
                            conversation_id=conversation_id,
                            approval_id=pause_data["approval_id"],
                            paused_at=datetime.fromisoformat(pause_data["paused_at"]),
                            pause_reason=pause_data["pause_reason"],
                            context_snapshot=pause_data["context_snapshot"],
                            pending_message=pause_data.get("pending_message"),
                            timeout_seconds=pause_data.get("timeout_seconds", 3600)
                        )
                        
                        self.paused_conversations[conversation_id] = paused
                        logger.info(f"Restored paused conversation: {conversation_id}")
                
                if cursor == 0:
                    break
        
        # Start timeout monitor
        asyncio.create_task(self._monitor_timeouts())
        
        logger.info("✅ Conversation Pause Manager initialized")
    
    async def pause_conversation(
        self,
        conversation_id: str,
        approval_id: str,
        reason: str,
        context: Dict[str, Any],
        pending_message: Optional[str] = None,
        resume_callback: Optional[Callable] = None,
        timeout_seconds: int = 3600
    ) -> bool:
        """Pause a conversation pending approval"""
        
        # Check if already paused
        if conversation_id in self.paused_conversations:
            logger.warning(f"Conversation already paused: {conversation_id}")
            return False
        
        # Create pause record
        paused = PausedConversation(
            conversation_id=conversation_id,
            approval_id=approval_id,
            paused_at=datetime.utcnow(),
            pause_reason=reason,
            context_snapshot=context,
            pending_message=pending_message,
            resume_callback=resume_callback,
            timeout_seconds=timeout_seconds
        )
        
        # Store in memory
        self.paused_conversations[conversation_id] = paused
        
        # Persist to Redis
        if self.redis:
            import json
            key = f"{self.key_prefix}{conversation_id}"
            data = {
                "approval_id": approval_id,
                "paused_at": paused.paused_at.isoformat(),
                "pause_reason": reason,
                "context_snapshot": context,
                "pending_message": pending_message,
                "timeout_seconds": timeout_seconds
            }
            
            await self.redis.setex(
                key,
                timeout_seconds,
                json.dumps(data)
            )
        
        # Register callbacks with approval store
        self.approval_store.register_resume_callback(
            conversation_id,
            lambda approval: self.resume_conversation(conversation_id, approval)
        )
        
        # Notify callbacks
        await self._notify_callbacks("on_pause", conversation_id, paused)
        
        logger.info(
            "⏸️ Conversation paused",
            conversation_id=conversation_id,
            approval_id=approval_id,
            reason=reason
        )
        
        return True
    
    async def resume_conversation(
        self,
        conversation_id: str,
        approval: ApprovalRequest
    ) -> Dict[str, Any]:
        """Resume a paused conversation after approval decision"""
        
        # Get paused conversation
        paused = self.paused_conversations.get(conversation_id)
        if not paused:
            logger.warning(f"No paused conversation found: {conversation_id}")
            return {"error": "Conversation not paused"}
        
        # Prepare resume context
        resume_context = {
            "conversation_id": conversation_id,
            "approval_id": approval.approval_id,
            "approval_status": approval.status.value,
            "approval_rationale": approval.approval_rationale,
            "paused_duration_seconds": (datetime.utcnow() - paused.paused_at).total_seconds(),
            "original_context": paused.context_snapshot,
            "pending_message": paused.pending_message
        }
        
        # Call resume callback if provided
        if paused.resume_callback:
            try:
                await paused.resume_callback(resume_context)
            except Exception as e:
                logger.error(f"Resume callback failed: {e}")
        
        # Remove from paused conversations
        del self.paused_conversations[conversation_id]
        
        # Clean up Redis
        if self.redis:
            key = f"{self.key_prefix}{conversation_id}"
            await self.redis.delete(key)
        
        # Notify callbacks
        await self._notify_callbacks("on_resume", conversation_id, resume_context)
        
        logger.info(
            "▶️ Conversation resumed",
            conversation_id=conversation_id,
            approval_status=approval.status.value,
            duration=resume_context["paused_duration_seconds"]
        )
        
        return resume_context
    
    async def cancel_pause(
        self,
        conversation_id: str,
        reason: str = "Manual cancellation"
    ) -> bool:
        """Cancel a paused conversation without approval"""
        
        paused = self.paused_conversations.get(conversation_id)
        if not paused:
            return False
        
        # Remove from paused conversations
        del self.paused_conversations[conversation_id]
        
        # Clean up Redis
        if self.redis:
            key = f"{self.key_prefix}{conversation_id}"
            await self.redis.delete(key)
        
        # Notify callbacks
        await self._notify_callbacks("on_cancel", conversation_id, {"reason": reason})
        
        logger.info(f"🛑 Conversation pause cancelled: {conversation_id}")
        
        return True
    
    async def _monitor_timeouts(self):
        """Monitor for expired pauses"""
        while True:
            try:
                expired = []
                
                for conv_id, paused in self.paused_conversations.items():
                    if paused.is_expired():
                        expired.append(conv_id)
                
                for conv_id in expired:
                    paused = self.paused_conversations[conv_id]
                    
                    # Get approval and timeout it
                    approval = await self.approval_store.get_approval(paused.approval_id)
                    if approval and approval.status == ApprovalStatus.PENDING:
                        # Timeout the approval
                        approval.status = ApprovalStatus.TIMEOUT
                        approval.updated_at = datetime.utcnow()
                        
                        # Resume with timeout status
                        await self.resume_conversation(conv_id, approval)
                        
                        # Notify callbacks
                        await self._notify_callbacks("on_timeout", conv_id, paused)
                        
                        logger.warning(f"⏰ Conversation pause timeout: {conv_id}")
                
                # Check every 30 seconds
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Error in timeout monitor: {e}")
                await asyncio.sleep(60)
    
    def register_callback(
        self,
        event: str,
        callback: Callable
    ):
        """Register callback for pause events"""
        if event in self.state_callbacks:
            self.state_callbacks[event].append(callback)
    
    async def _notify_callbacks(
        self,
        event: str,
        conversation_id: str,
        data: Any
    ):
        """Notify registered callbacks"""
        for callback in self.state_callbacks.get(event, []):
            try:
                await callback(conversation_id, data)
            except Exception as e:
                logger.error(f"Callback error for {event}: {e}")
    
    def get_paused_conversations(self) -> List[Dict[str, Any]]:
        """Get list of currently paused conversations"""
        return [
            {
                "conversation_id": conv_id,
                "approval_id": paused.approval_id,
                "paused_at": paused.paused_at.isoformat(),
                "pause_reason": paused.pause_reason,
                "elapsed_seconds": (datetime.utcnow() - paused.paused_at).total_seconds(),
                "timeout_seconds": paused.timeout_seconds,
                "will_timeout_at": (
                    paused.paused_at + timedelta(seconds=paused.timeout_seconds)
                ).isoformat()
            }
            for conv_id, paused in self.paused_conversations.items()
        ]
    
    async def handle_high_risk_action(
        self,
        conversation_id: str,
        action: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle high-risk action requiring approval"""
        
        # Create approval request
        approval = await self.approval_store.create_approval(
            conversation_id=conversation_id,
            user_id=context.get("user_id", "system"),
            agent_id=context.get("agent_id", "unknown"),
            action_type=action,
            action_description=context.get("description", f"High-risk action: {action}"),
            payload=context.get("payload", {}),
            metadata={
                "risk_factors": context.get("risk_factors", []),
                "estimated_impact": context.get("impact", "unknown"),
                "requires_approval": True
            }
        )
        
        if approval:
            # Pause conversation
            await self.pause_conversation(
                conversation_id=conversation_id,
                approval_id=approval.approval_id,
                reason=f"High-risk action requires approval: {action}",
                context=context,
                pending_message=context.get("pending_message"),
                resume_callback=context.get("resume_callback"),
                timeout_seconds=approval.risk_thresholds[approval.risk_level].timeout_minutes * 60
            )
            
            return {
                "status": "paused",
                "approval_id": approval.approval_id,
                "risk_level": approval.risk_level.value,
                "message": f"Conversation paused pending approval for {action}"
            }
        else:
            # Auto-approved (low risk)
            return {
                "status": "auto_approved",
                "message": f"Action {action} auto-approved due to low risk"
            }


# Integration helper for orchestrator
class OrchestrationIntegration:
    """Helper class to integrate pause management with orchestrator"""
    
    def __init__(
        self,
        pause_manager: ConversationPauseManager,
        orchestrator: Any
    ):
        self.pause_manager = pause_manager
        self.orchestrator = orchestrator
        
    async def wrap_with_approval(
        self,
        func: Callable,
        conversation_id: str,
        risk_assessment: Dict[str, Any]
    ) -> Any:
        """Wrap a function call with approval check"""
        
        # Check if approval needed
        if risk_assessment.get("requires_approval"):
            # Request approval and pause
            result = await self.pause_manager.handle_high_risk_action(
                conversation_id=conversation_id,
                action=risk_assessment.get("action", "unknown"),
                context={
                    **risk_assessment,
                    "resume_callback": lambda ctx: func(**ctx.get("original_context", {}))
                }
            )
            
            if result["status"] == "paused":
                # Return pause indicator
                return {"status": "paused_for_approval", **result}
        
        # Execute directly if no approval needed
        return await func()


__all__ = [
    "ConversationPauseManager",
    "PausedConversation",
    "ConversationState",
    "OrchestrationIntegration"
]