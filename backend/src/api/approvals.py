"""
HITL Approvals API - Complete implementation with Redis backing
Enhanced endpoints for approval management with filtering and audit trail
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
import structlog

from ..agents.services.hitl.approval_store_redis import (
    RedisApprovalStore, ApprovalStatus
)
from ..core.redis import get_redis_client
from ..core.config import get_settings

logger = structlog.get_logger()
router = APIRouter(tags=["approvals"])

# Global store instance
_approval_store: Optional[RedisApprovalStore] = None


async def get_approval_store() -> RedisApprovalStore:
    """Get or create approval store instance"""
    global _approval_store
    
    if _approval_store is None:
        settings = get_settings()
        if not settings.hitl_enabled:
            raise HTTPException(status_code=503, detail="HITL not enabled")
        
        redis_client = await get_redis_client()
        _approval_store = RedisApprovalStore(redis_client)
        await _approval_store.initialize(settings.redis_url)
    
    return _approval_store


# Request/Response models
class ApprovalCreateRequest(BaseModel):
    """Request model for creating approval"""
    conversation_id: str
    user_id: str
    agent_id: str
    action_type: str
    action_description: str
    payload: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None


class ApprovalDecisionRequest(BaseModel):
    """Request model for approval decision"""
    decided_by: str
    rationale: Optional[str] = None


class ApprovalResponse(BaseModel):
    """Response model for approval"""
    approval_id: str
    conversation_id: str
    user_id: str
    agent_id: Optional[str]
    status: str
    risk_level: str
    action_type: str
    action_description: str
    created_at: str
    updated_at: str
    expires_at: Optional[str]
    approved_by: Optional[str]
    denied_by: Optional[str]
    approval_rationale: Optional[str]


# API Endpoints
@router.post("/", response_model=ApprovalResponse)
async def create_approval(request: ApprovalCreateRequest):
    """Create a new approval request with risk assessment"""
    try:
        store = await get_approval_store()
        
        approval = await store.create_approval(
            conversation_id=request.conversation_id,
            user_id=request.user_id,
            agent_id=request.agent_id,
            action_type=request.action_type,
            action_description=request.action_description,
            payload=request.payload,
            metadata=request.metadata
        )
        
        if approval is None:
            # Auto-approved due to low risk
            return {
                "message": "Action auto-approved due to low risk",
                "risk_level": "low",
                "status": "auto_approved"
            }
        
        return ApprovalResponse(
            approval_id=approval.approval_id,
            conversation_id=approval.conversation_id,
            user_id=approval.user_id,
            agent_id=approval.agent_id,
            status=approval.status.value,
            risk_level=approval.risk_level.value,
            action_type=approval.action_type,
            action_description=approval.action_description,
            created_at=approval.created_at.isoformat(),
            updated_at=approval.updated_at.isoformat(),
            expires_at=approval.expires_at.isoformat() if approval.expires_at else None,
            approved_by=approval.approved_by,
            denied_by=approval.denied_by,
            approval_rationale=approval.approval_rationale
        )
        
    except Exception as e:
        logger.error("❌ Failed to create approval", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create approval: {str(e)}")


@router.get("/", response_model=List[ApprovalResponse])
async def list_approvals(
    status: Optional[str] = Query(None, description="Filter by status"),
    user_id: Optional[str] = Query(None, description="Filter by user"),
    conversation_id: Optional[str] = Query(None, description="Filter by conversation"),
    limit: int = Query(100, description="Maximum number of results")
):
    """List approvals with optional filters"""
    try:
        store = await get_approval_store()
        
        # Convert status string to enum if provided
        status_enum = None
        if status:
            try:
                status_enum = ApprovalStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        approvals = await store.list_approvals(
            status=status_enum,
            user_id=user_id,
            conversation_id=conversation_id,
            limit=limit
        )
        
        return [
            ApprovalResponse(
                approval_id=ap.approval_id,
                conversation_id=ap.conversation_id,
                user_id=ap.user_id,
                agent_id=ap.agent_id,
                status=ap.status.value,
                risk_level=ap.risk_level.value,
                action_type=ap.action_type,
                action_description=ap.action_description,
                created_at=ap.created_at.isoformat(),
                updated_at=ap.updated_at.isoformat(),
                expires_at=ap.expires_at.isoformat() if ap.expires_at else None,
                approved_by=ap.approved_by,
                denied_by=ap.denied_by,
                approval_rationale=ap.approval_rationale
            )
            for ap in approvals
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("❌ Failed to list approvals", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list approvals: {str(e)}")


@router.get("/{approval_id}", response_model=ApprovalResponse)
async def get_approval(approval_id: str):
    """Get specific approval by ID"""
    try:
        store = await get_approval_store()
        
        approval = await store.get_approval(approval_id)
        if not approval:
            raise HTTPException(status_code=404, detail="Approval not found")
        
        return ApprovalResponse(
            approval_id=approval.approval_id,
            conversation_id=approval.conversation_id,
            user_id=approval.user_id,
            agent_id=approval.agent_id,
            status=approval.status.value,
            risk_level=approval.risk_level.value,
            action_type=approval.action_type,
            action_description=approval.action_description,
            created_at=approval.created_at.isoformat(),
            updated_at=approval.updated_at.isoformat(),
            expires_at=approval.expires_at.isoformat() if approval.expires_at else None,
            approved_by=approval.approved_by,
            denied_by=approval.denied_by,
            approval_rationale=approval.approval_rationale
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("❌ Failed to get approval", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get approval: {str(e)}")


@router.post("/{approval_id}/approve")
async def approve_approval(
    approval_id: str,
    request: ApprovalDecisionRequest
):
    """Approve a pending approval request"""
    try:
        store = await get_approval_store()
        
        approval = await store.approve(
            approval_id=approval_id,
            approved_by=request.decided_by,
            rationale=request.rationale
        )
        
        if not approval:
            raise HTTPException(status_code=404, detail="Approval not found or not pending")
        
        logger.info(f"✅ Approval {approval_id} approved by {request.decided_by}")
        
        return {
            "status": "success",
            "approval_id": approval_id,
            "new_status": approval.status.value,
            "approved_by": approval.approved_by,
            "message": "Approval granted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("❌ Failed to approve", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to approve: {str(e)}")


@router.post("/{approval_id}/deny")
async def deny_approval(
    approval_id: str,
    request: ApprovalDecisionRequest
):
    """Deny a pending approval request"""
    try:
        store = await get_approval_store()
        
        approval = await store.deny(
            approval_id=approval_id,
            denied_by=request.decided_by,
            rationale=request.rationale
        )
        
        if not approval:
            raise HTTPException(status_code=404, detail="Approval not found or not pending")
        
        logger.info(f"❌ Approval {approval_id} denied by {request.decided_by}")
        
        return {
            "status": "success",
            "approval_id": approval_id,
            "new_status": approval.status.value,
            "denied_by": approval.denied_by,
            "message": "Approval denied successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("❌ Failed to deny", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to deny: {str(e)}")


@router.get("/{approval_id}/audit")
async def get_audit_trail(approval_id: str):
    """Get complete audit trail for an approval"""
    try:
        store = await get_approval_store()
        
        # Get approval to verify it exists
        approval = await store.get_approval(approval_id)
        if not approval:
            raise HTTPException(status_code=404, detail="Approval not found")
        
        # Get audit trail
        audit_trail = await store.get_audit_trail(approval_id)
        
        # Combine with approval's internal audit trail
        combined_trail = approval.audit_trail + audit_trail
        
        # Sort by timestamp
        combined_trail.sort(key=lambda x: x.get('timestamp', ''))
        
        return {
            "approval_id": approval_id,
            "audit_trail": combined_trail,
            "entry_count": len(combined_trail)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("❌ Failed to get audit trail", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get audit trail: {str(e)}")


@router.post("/check-timeouts")
async def check_approval_timeouts():
    """Check and process expired approvals"""
    try:
        store = await get_approval_store()
        
        await store.check_timeouts()
        
        return {
            "status": "success",
            "message": "Timeout check completed"
        }
        
    except Exception as e:
        logger.error("❌ Failed to check timeouts", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to check timeouts: {str(e)}")


@router.post("/cleanup")
async def cleanup_old_approvals(days: int = Query(30, description="Days to keep")):
    """Clean up old completed approvals"""
    try:
        store = await get_approval_store()
        
        await store.cleanup_old_approvals(days=days)
        
        return {
            "status": "success",
            "message": f"Cleaned approvals older than {days} days"
        }
        
    except Exception as e:
        logger.error("❌ Failed to cleanup", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to cleanup: {str(e)}")


@router.get("/stats/summary")
async def get_approval_stats():
    """Get summary statistics for approvals"""
    try:
        store = await get_approval_store()
        
        # Get counts by status
        pending = await store.list_approvals(status=ApprovalStatus.PENDING)
        approved = await store.list_approvals(status=ApprovalStatus.APPROVED, limit=1000)
        denied = await store.list_approvals(status=ApprovalStatus.DENIED, limit=1000)
        timeout = await store.list_approvals(status=ApprovalStatus.TIMEOUT, limit=1000)
        
        # Calculate risk distribution for pending
        risk_distribution = {
            "low": 0,
            "medium": 0,
            "high": 0,
            "critical": 0
        }
        
        for approval in pending:
            risk_distribution[approval.risk_level.value] += 1
        
        return {
            "total_pending": len(pending),
            "total_approved": len(approved),
            "total_denied": len(denied),
            "total_timeout": len(timeout),
            "risk_distribution": risk_distribution,
            "approval_rate": len(approved) / (len(approved) + len(denied)) if (len(approved) + len(denied)) > 0 else 0
        }
        
    except Exception as e:
        logger.error("❌ Failed to get stats", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")