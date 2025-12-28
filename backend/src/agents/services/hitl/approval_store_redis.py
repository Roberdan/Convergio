"""
HITL Approval Store with Redis Persistence
Complete implementation with Redis backing, risk thresholds, and audit trail
"""

import json
import uuid
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import structlog

import redis.asyncio as redis

logger = structlog.get_logger()


class ApprovalStatus(Enum):
    """Approval status states"""
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class RiskLevel(Enum):
    """Risk levels for automatic approval triggering"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RiskThreshold:
    """Risk threshold configuration"""
    level: RiskLevel
    cost_threshold: float = 100.0  # Dollar amount
    data_sensitivity: List[str] = field(default_factory=list)  # PII, Financial, etc
    action_types: List[str] = field(default_factory=list)  # delete, modify_production, etc
    auto_pause: bool = False
    require_approval: bool = False
    timeout_minutes: int = 60


@dataclass
class ApprovalRequest:
    """Complete approval request with metadata"""
    approval_id: str
    conversation_id: str
    user_id: str
    agent_id: Optional[str]
    status: ApprovalStatus
    risk_level: RiskLevel
    action_type: str
    action_description: str
    payload: Dict[str, Any]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime]
    approved_by: Optional[str] = None
    denied_by: Optional[str] = None
    approval_rationale: Optional[str] = None
    audit_trail: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Redis storage"""
        data = asdict(self)
        data['status'] = self.status.value
        data['risk_level'] = self.risk_level.value
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        if self.expires_at:
            data['expires_at'] = self.expires_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ApprovalRequest':
        """Create from dictionary retrieved from Redis"""
        data['status'] = ApprovalStatus(data['status'])
        data['risk_level'] = RiskLevel(data['risk_level'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        if data.get('expires_at'):
            data['expires_at'] = datetime.fromisoformat(data['expires_at'])
        return cls(**data)


class RedisApprovalStore:
    """Redis-backed approval store with complete HITL functionality"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis = redis_client
        self.key_prefix = "approval:"
        self.index_prefix = "approval_index:"
        self.audit_prefix = "audit:"
        self.risk_thresholds = self._init_risk_thresholds()
        self.pause_callbacks = {}
        self.resume_callbacks = {}
        
    def _init_risk_thresholds(self) -> Dict[RiskLevel, RiskThreshold]:
        """Initialize default risk thresholds"""
        return {
            RiskLevel.LOW: RiskThreshold(
                level=RiskLevel.LOW,
                cost_threshold=10.0,
                auto_pause=False,
                require_approval=False
            ),
            RiskLevel.MEDIUM: RiskThreshold(
                level=RiskLevel.MEDIUM,
                cost_threshold=100.0,
                data_sensitivity=["PII"],
                auto_pause=False,
                require_approval=False,
                timeout_minutes=120
            ),
            RiskLevel.HIGH: RiskThreshold(
                level=RiskLevel.HIGH,
                cost_threshold=1000.0,
                data_sensitivity=["PII", "Financial"],
                action_types=["delete", "modify_production"],
                auto_pause=True,
                require_approval=True,
                timeout_minutes=60
            ),
            RiskLevel.CRITICAL: RiskThreshold(
                level=RiskLevel.CRITICAL,
                cost_threshold=5000.0,
                data_sensitivity=["PII", "Financial", "Health"],
                action_types=["delete", "modify_production", "access_sensitive"],
                auto_pause=True,
                require_approval=True,
                timeout_minutes=30
            )
        }
    
    async def initialize(self, redis_url: str = "redis://localhost:6379"):
        """Initialize Redis connection"""
        if not self.redis:
            self.redis = await redis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True
            )
        logger.info("✅ Redis Approval Store initialized")
    
    async def assess_risk(
        self,
        action_type: str,
        payload: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> Tuple[RiskLevel, bool]:
        """Assess risk level and determine if approval needed"""
        
        # Extract risk factors
        cost = metadata.get("estimated_cost", 0)
        data_types = metadata.get("data_sensitivity", [])
        
        # Determine risk level
        risk_level = RiskLevel.LOW
        
        for level, threshold in self.risk_thresholds.items():
            if cost >= threshold.cost_threshold:
                risk_level = level
            
            if any(dt in threshold.data_sensitivity for dt in data_types):
                risk_level = max(risk_level, level, key=lambda x: list(RiskLevel).index(x))
            
            if action_type in threshold.action_types:
                risk_level = max(risk_level, level, key=lambda x: list(RiskLevel).index(x))
        
        # Check if approval required
        threshold = self.risk_thresholds[risk_level]
        
        return risk_level, threshold.require_approval
    
    async def create_approval(
        self,
        conversation_id: str,
        user_id: str,
        agent_id: str,
        action_type: str,
        action_description: str,
        payload: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> ApprovalRequest:
        """Create new approval request with risk assessment"""
        
        metadata = metadata or {}
        
        # Assess risk
        risk_level, require_approval = await self.assess_risk(
            action_type, payload, metadata
        )
        
        if not require_approval:
            logger.info(f"✅ Auto-approved low-risk action: {action_type}")
            return None
        
        # Create approval request
        approval_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        threshold = self.risk_thresholds[risk_level]
        expires_at = now + timedelta(minutes=threshold.timeout_minutes)
        
        approval = ApprovalRequest(
            approval_id=approval_id,
            conversation_id=conversation_id,
            user_id=user_id,
            agent_id=agent_id,
            status=ApprovalStatus.PENDING,
            risk_level=risk_level,
            action_type=action_type,
            action_description=action_description,
            payload=payload,
            metadata=metadata,
            created_at=now,
            updated_at=now,
            expires_at=expires_at,
            audit_trail=[{
                "timestamp": now.isoformat(),
                "action": "created",
                "user": user_id,
                "details": f"Approval requested for {action_type}"
            }]
        )
        
        # Store in Redis
        await self._store_approval(approval)
        
        # Create indexes for querying
        await self._index_approval(approval)
        
        # Trigger pause if needed
        if threshold.auto_pause:
            await self._pause_conversation(conversation_id, approval_id)
        
        # Log audit entry
        await self._log_audit(
            approval_id,
            "approval_requested",
            user_id,
            {
                "risk_level": risk_level.value,
                "action_type": action_type,
                "auto_pause": threshold.auto_pause
            }
        )
        
        logger.info(
            "🔐 Approval requested",
            approval_id=approval_id,
            risk_level=risk_level.value,
            action=action_type
        )
        
        return approval
    
    async def _store_approval(self, approval: ApprovalRequest):
        """Store approval in Redis"""
        if self.redis:
            key = f"{self.key_prefix}{approval.approval_id}"
            data = json.dumps(approval.to_dict())
            
            # Set with expiration (7 days)
            await self.redis.setex(key, 604800, data)
    
    async def _index_approval(self, approval: ApprovalRequest):
        """Create indexes for efficient querying"""
        if self.redis:
            # Index by conversation
            conv_key = f"{self.index_prefix}conversation:{approval.conversation_id}"
            await self.redis.sadd(conv_key, approval.approval_id)
            await self.redis.expire(conv_key, 604800)
            
            # Index by user
            user_key = f"{self.index_prefix}user:{approval.user_id}"
            await self.redis.sadd(user_key, approval.approval_id)
            await self.redis.expire(user_key, 604800)
            
            # Index by status
            status_key = f"{self.index_prefix}status:{approval.status.value}"
            await self.redis.sadd(status_key, approval.approval_id)
            await self.redis.expire(status_key, 604800)
    
    async def get_approval(self, approval_id: str) -> Optional[ApprovalRequest]:
        """Get approval by ID"""
        if self.redis:
            key = f"{self.key_prefix}{approval_id}"
            data = await self.redis.get(key)
            
            if data:
                approval_dict = json.loads(data)
                return ApprovalRequest.from_dict(approval_dict)
        
        return None
    
    async def list_approvals(
        self,
        status: Optional[ApprovalStatus] = None,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        limit: int = 100
    ) -> List[ApprovalRequest]:
        """List approvals with filters"""
        
        approval_ids = set()
        
        if self.redis:
            # Get approval IDs based on filters
            if status:
                status_key = f"{self.index_prefix}status:{status.value}"
                ids = await self.redis.smembers(status_key)
                approval_ids.update(ids) if approval_ids else approval_ids.update(ids)
            
            if user_id:
                user_key = f"{self.index_prefix}user:{user_id}"
                ids = await self.redis.smembers(user_key)
                approval_ids = approval_ids.intersection(ids) if approval_ids else set(ids)
            
            if conversation_id:
                conv_key = f"{self.index_prefix}conversation:{conversation_id}"
                ids = await self.redis.smembers(conv_key)
                approval_ids = approval_ids.intersection(ids) if approval_ids else set(ids)
            
            # If no filters, get all pending
            if not approval_ids and not any([status, user_id, conversation_id]):
                status_key = f"{self.index_prefix}status:{ApprovalStatus.PENDING.value}"
                approval_ids = await self.redis.smembers(status_key)
            
            # Retrieve approvals
            approvals = []
            for approval_id in list(approval_ids)[:limit]:
                approval = await self.get_approval(approval_id)
                if approval:
                    approvals.append(approval)
            
            # Sort by created_at descending
            approvals.sort(key=lambda a: a.created_at, reverse=True)
            
            return approvals
        
        return []
    
    async def approve(
        self,
        approval_id: str,
        approved_by: str,
        rationale: Optional[str] = None
    ) -> Optional[ApprovalRequest]:
        """Approve an approval request"""
        
        approval = await self.get_approval(approval_id)
        if not approval:
            return None
        
        if approval.status != ApprovalStatus.PENDING:
            logger.warning(f"Cannot approve non-pending approval: {approval_id}")
            return None
        
        # Update approval
        approval.status = ApprovalStatus.APPROVED
        approval.approved_by = approved_by
        approval.approval_rationale = rationale
        approval.updated_at = datetime.utcnow()
        
        # Add audit trail
        approval.audit_trail.append({
            "timestamp": approval.updated_at.isoformat(),
            "action": "approved",
            "user": approved_by,
            "rationale": rationale
        })
        
        # Update in Redis
        await self._store_approval(approval)
        await self._update_indexes(approval)
        
        # Resume conversation if paused
        await self._resume_conversation(approval.conversation_id, approval_id)
        
        # Log audit
        await self._log_audit(
            approval_id,
            "approved",
            approved_by,
            {"rationale": rationale}
        )
        
        logger.info(f"✅ Approval approved: {approval_id}")
        
        return approval
    
    async def deny(
        self,
        approval_id: str,
        denied_by: str,
        rationale: Optional[str] = None
    ) -> Optional[ApprovalRequest]:
        """Deny an approval request"""
        
        approval = await self.get_approval(approval_id)
        if not approval:
            return None
        
        if approval.status != ApprovalStatus.PENDING:
            logger.warning(f"Cannot deny non-pending approval: {approval_id}")
            return None
        
        # Update approval
        approval.status = ApprovalStatus.DENIED
        approval.denied_by = denied_by
        approval.approval_rationale = rationale
        approval.updated_at = datetime.utcnow()
        
        # Add audit trail
        approval.audit_trail.append({
            "timestamp": approval.updated_at.isoformat(),
            "action": "denied",
            "user": denied_by,
            "rationale": rationale
        })
        
        # Update in Redis
        await self._store_approval(approval)
        await self._update_indexes(approval)
        
        # Resume conversation (will handle denial)
        await self._resume_conversation(approval.conversation_id, approval_id)
        
        # Log audit
        await self._log_audit(
            approval_id,
            "denied",
            denied_by,
            {"rationale": rationale}
        )
        
        logger.info(f"❌ Approval denied: {approval_id}")
        
        return approval
    
    async def _update_indexes(self, approval: ApprovalRequest):
        """Update status index when approval changes"""
        if self.redis:
            # Remove from old status index
            for status in ApprovalStatus:
                if status != approval.status:
                    old_key = f"{self.index_prefix}status:{status.value}"
                    await self.redis.srem(old_key, approval.approval_id)
            
            # Add to new status index
            new_key = f"{self.index_prefix}status:{approval.status.value}"
            await self.redis.sadd(new_key, approval.approval_id)
            await self.redis.expire(new_key, 604800)
    
    async def _pause_conversation(self, conversation_id: str, approval_id: str):
        """Pause conversation pending approval"""
        
        if self.redis:
            pause_key = f"conversation:pause:{conversation_id}"
            await self.redis.set(pause_key, approval_id)
            await self.redis.expire(pause_key, 3600)  # 1 hour
        
        # Call pause callback if registered
        if conversation_id in self.pause_callbacks:
            await self.pause_callbacks[conversation_id](approval_id)
        
        logger.info(f"⏸️ Conversation paused: {conversation_id}")
    
    async def _resume_conversation(self, conversation_id: str, approval_id: str):
        """Resume conversation after approval decision"""
        
        if self.redis:
            pause_key = f"conversation:pause:{conversation_id}"
            await self.redis.delete(pause_key)
        
        # Call resume callback if registered
        if conversation_id in self.resume_callbacks:
            approval = await self.get_approval(approval_id)
            await self.resume_callbacks[conversation_id](approval)
        
        logger.info(f"▶️ Conversation resumed: {conversation_id}")
    
    def register_pause_callback(self, conversation_id: str, callback):
        """Register callback for conversation pause"""
        self.pause_callbacks[conversation_id] = callback
    
    def register_resume_callback(self, conversation_id: str, callback):
        """Register callback for conversation resume"""
        self.resume_callbacks[conversation_id] = callback
    
    async def check_timeouts(self):
        """Check for expired approvals and timeout them"""
        
        if self.redis:
            # Get all pending approvals
            pending_approvals = await self.list_approvals(status=ApprovalStatus.PENDING)
            
            now = datetime.utcnow()
            for approval in pending_approvals:
                if approval.expires_at and now > approval.expires_at:
                    # Timeout the approval
                    approval.status = ApprovalStatus.TIMEOUT
                    approval.updated_at = now
                    approval.audit_trail.append({
                        "timestamp": now.isoformat(),
                        "action": "timeout",
                        "details": "Approval request expired"
                    })
                    
                    await self._store_approval(approval)
                    await self._update_indexes(approval)
                    
                    # Resume conversation with timeout status
                    await self._resume_conversation(approval.conversation_id, approval.approval_id)
                    
                    logger.warning(f"⏰ Approval timeout: {approval.approval_id}")
    
    async def _log_audit(
        self,
        approval_id: str,
        action: str,
        user_id: str,
        metadata: Dict[str, Any]
    ):
        """Log audit trail entry"""
        
        if self.redis:
            audit_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "approval_id": approval_id,
                "action": action,
                "user_id": user_id,
                "metadata": metadata
            }
            
            # Store in audit list
            audit_key = f"{self.audit_prefix}{approval_id}"
            await self.redis.rpush(audit_key, json.dumps(audit_entry))
            await self.redis.expire(audit_key, 2592000)  # 30 days
    
    async def get_audit_trail(self, approval_id: str) -> List[Dict[str, Any]]:
        """Get complete audit trail for approval"""
        
        if self.redis:
            audit_key = f"{self.audit_prefix}{approval_id}"
            entries = await self.redis.lrange(audit_key, 0, -1)
            
            return [json.loads(entry) for entry in entries]
        
        return []
    
    async def cleanup_old_approvals(self, days: int = 30):
        """Clean up old completed approvals"""
        
        if self.redis:
            cutoff = datetime.utcnow() - timedelta(days=days)
            
            # Get all non-pending approvals
            for status in [ApprovalStatus.APPROVED, ApprovalStatus.DENIED, ApprovalStatus.TIMEOUT]:
                approvals = await self.list_approvals(status=status)
                
                for approval in approvals:
                    if approval.updated_at < cutoff:
                        # Delete approval and indexes
                        await self.redis.delete(f"{self.key_prefix}{approval.approval_id}")
                        
                        # Clean indexes
                        conv_key = f"{self.index_prefix}conversation:{approval.conversation_id}"
                        await self.redis.srem(conv_key, approval.approval_id)
                        
                        user_key = f"{self.index_prefix}user:{approval.user_id}"
                        await self.redis.srem(user_key, approval.approval_id)
                        
                        status_key = f"{self.index_prefix}status:{approval.status.value}"
                        await self.redis.srem(status_key, approval.approval_id)
                        
                        logger.info(f"🗑️ Cleaned old approval: {approval.approval_id}")


# Backward compatibility wrapper
class ApprovalStore(RedisApprovalStore):
    """Backward compatible approval store"""
    
    def request_approval(
        self,
        request_id: str,
        user_id: str,
        action: str,
        metadata: Dict[str, Any]
    ) -> Any:
        """Legacy API for backward compatibility"""
        
        # Run async method in sync context
        loop = asyncio.new_event_loop()
        try:
            approval = loop.run_until_complete(
                self.create_approval(
                    conversation_id=request_id,
                    user_id=user_id,
                    agent_id="legacy",
                    action_type=action,
                    action_description=f"Legacy action: {action}",
                    payload=metadata,
                    metadata=metadata
                )
            )
            return approval
        finally:
            loop.close()


__all__ = [
    "RedisApprovalStore",
    "ApprovalStore",
    "ApprovalRequest",
    "ApprovalStatus",
    "RiskLevel",
    "RiskThreshold"
]