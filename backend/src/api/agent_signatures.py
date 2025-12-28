"""
Agent Digital Signatures API
REST endpoints for managing agent cryptographic signatures and validation
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any
from pydantic import BaseModel, Field
from datetime import datetime, timedelta

from ..agents.security.digital_signatures import signature_manager
from ..agents.services.agent_loader import agent_loader
from ..core.logging import get_logger

logger = get_logger()
router = APIRouter()

# Pydantic models
class SignAgentRequest(BaseModel):
    agent_name: str = Field(..., description="Name of the agent to sign")
    validity_days: int = Field(365, description="Signature validity in days", gt=0, le=1095)
    force_resign: bool = Field(False, description="Force re-signing if signature exists")

class SignAgentResponse(BaseModel):
    agent_name: str
    signature_hash: str
    public_key_fingerprint: str
    signed_at: datetime
    expires_at: datetime
    is_verified: bool
    message: str

class VerifyAgentRequest(BaseModel):
    agent_name: str = Field(..., description="Name of the agent to verify")

class VerifyAgentResponse(BaseModel):
    agent_name: str
    is_verified: bool
    verification_message: str
    signature_exists: bool
    signature_expired: bool
    verification_timestamp: datetime

class SignedAgentListResponse(BaseModel):
    signed_agents: List[Dict[str, Any]]
    total_count: int
    expired_count: int

class AgentJWTRequest(BaseModel):
    agent_name: str = Field(..., description="Name of the agent")
    validity_minutes: int = Field(60, description="Token validity in minutes", gt=0, le=1440)

class AgentJWTResponse(BaseModel):
    agent_name: str
    token: str
    expires_at: datetime
    message: str

@router.on_event("startup")
async def startup_signatures():
    """Initialize digital signature manager on startup"""
    try:
        await signature_manager.initialize()
        logger.info("✅ Agent Signatures API initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize signatures API: {e}")

@router.post("/sign", response_model=SignAgentResponse)
async def sign_agent(request: SignAgentRequest):
    """
    Create a digital signature for an agent
    """
    try:
        # Get agent definition
        agent_config = await agent_loader.get_agent_config(request.agent_name)
        if not agent_config:
            raise HTTPException(
                status_code=404,
                detail=f"Agent {request.agent_name} not found"
            )
        
        # Check if signature already exists
        existing_signature = await signature_manager.get_agent_signature(request.agent_name)
        if existing_signature and not request.force_resign:
            # Check if signature is still valid
            if datetime.utcnow() < existing_signature.expires_at:
                raise HTTPException(
                    status_code=400,
                    detail=f"Agent {request.agent_name} already has a valid signature. Use force_resign=true to override."
                )
        
        logger.info(f"🔐 Signing agent {request.agent_name}")
        
        # Create signed agent
        signed_agent = await signature_manager.create_signed_agent(
            agent_name=request.agent_name,
            agent_definition=agent_config
        )
        
        return SignAgentResponse(
            agent_name=signed_agent.agent_name,
            signature_hash=signed_agent.signature.signature_hash[:32] + "...",  # Truncate for display
            public_key_fingerprint=signed_agent.signature.public_key_fingerprint,
            signed_at=signed_agent.signature.signed_at,
            expires_at=signed_agent.signature.expires_at,
            is_verified=signed_agent.is_verified,
            message=f"Agent {request.agent_name} signed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error signing agent {request.agent_name}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to sign agent: {str(e)}"
        )

@router.post("/verify", response_model=VerifyAgentResponse)
async def verify_agent(request: VerifyAgentRequest):
    """
    Verify an agent's digital signature
    """
    try:
        # Get agent definition
        agent_config = await agent_loader.get_agent_config(request.agent_name)
        if not agent_config:
            raise HTTPException(
                status_code=404,
                detail=f"Agent {request.agent_name} not found"
            )
        
        # Get signature
        signature = await signature_manager.get_agent_signature(request.agent_name)
        signature_exists = signature is not None
        signature_expired = signature and datetime.utcnow() > signature.expires_at
        
        if not signature:
            return VerifyAgentResponse(
                agent_name=request.agent_name,
                is_verified=False,
                verification_message="No signature found for agent",
                signature_exists=False,
                signature_expired=False,
                verification_timestamp=datetime.utcnow()
            )
        
        # Verify signature
        is_verified, verification_message = await signature_manager.verify_agent_signature(
            agent_name=request.agent_name,
            agent_definition=agent_config,
            signature=signature
        )
        
        return VerifyAgentResponse(
            agent_name=request.agent_name,
            is_verified=is_verified,
            verification_message=verification_message,
            signature_exists=signature_exists,
            signature_expired=signature_expired,
            verification_timestamp=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error verifying agent {request.agent_name}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to verify agent: {str(e)}"
        )

@router.get("/list", response_model=SignedAgentListResponse)
async def list_signed_agents():
    """
    List all signed agents with their signature status
    """
    try:
        signed_agents = await signature_manager.list_signed_agents()
        
        expired_count = sum(1 for agent in signed_agents if agent.get("is_expired", False))
        
        return SignedAgentListResponse(
            signed_agents=signed_agents,
            total_count=len(signed_agents),
            expired_count=expired_count
        )
        
    except Exception as e:
        logger.error(f"❌ Error listing signed agents: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list signed agents: {str(e)}"
        )

@router.get("/health")
async def signatures_health_check():
    """Health check for digital signatures system"""
    try:
        signed_agents = await signature_manager.list_signed_agents()
        expired_agents = [agent for agent in signed_agents if agent.get("is_expired", False)]
        
        return {
            "status": "healthy",
            "signature_manager_initialized": hasattr(signature_manager, 'private_key') and signature_manager.private_key is not None,
            "total_signed_agents": len(signed_agents),
            "expired_signatures": len(expired_agents),
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Digital signatures system operational"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Digital signatures system error"
        }

@router.get("/{agent_name}")
async def get_agent_signature(agent_name: str):
    """
    Get signature details for a specific agent
    """
    try:
        signature = await signature_manager.get_agent_signature(agent_name)
        
        if not signature:
            raise HTTPException(
                status_code=404,
                detail=f"No signature found for agent {agent_name}"
            )
        
        is_expired = datetime.utcnow() > signature.expires_at
        
        return {
            "agent_name": signature.agent_name,
            "signature_hash": signature.signature_hash[:32] + "...",  # Truncate for security
            "public_key_fingerprint": signature.public_key_fingerprint,
            "signed_at": signature.signed_at.isoformat(),
            "expires_at": signature.expires_at.isoformat(),
            "is_expired": is_expired,
            "signature_algorithm": signature.signature_algorithm,
            "metadata": signature.metadata,
            "days_until_expiry": (signature.expires_at - datetime.utcnow()).days if not is_expired else 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting signature for {agent_name}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get agent signature: {str(e)}"
        )

@router.delete("/{agent_name}")
async def revoke_agent_signature(agent_name: str):
    """
    Revoke an agent's digital signature
    """
    try:
        success = await signature_manager.revoke_agent_signature(agent_name)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"No signature found to revoke for agent {agent_name}"
            )
        
        return {
            "agent_name": agent_name,
            "message": f"Signature revoked successfully for agent {agent_name}",
            "revoked_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error revoking signature for {agent_name}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to revoke agent signature: {str(e)}"
        )

@router.post("/token", response_model=AgentJWTResponse)
async def create_agent_jwt_token(request: AgentJWTRequest):
    """
    Create a JWT token for agent authentication
    """
    try:
        # Get and verify signature first
        signature = await signature_manager.get_agent_signature(request.agent_name)
        
        if not signature:
            raise HTTPException(
                status_code=404,
                detail=f"No signature found for agent {request.agent_name}. Sign the agent first."
            )
        
        # Check if signature is expired
        if datetime.utcnow() > signature.expires_at:
            raise HTTPException(
                status_code=400,
                detail=f"Signature for agent {request.agent_name} has expired. Re-sign the agent."
            )
        
        # Create JWT token
        token = await signature_manager.create_agent_jwt_token(
            agent_name=request.agent_name,
            signature=signature,
            validity_minutes=request.validity_minutes
        )
        
        expires_at = datetime.utcnow() + timedelta(minutes=request.validity_minutes)
        
        return AgentJWTResponse(
            agent_name=request.agent_name,
            token=token,
            expires_at=expires_at,
            message=f"JWT token created for agent {request.agent_name}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating JWT token for {request.agent_name}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create JWT token: {str(e)}"
        )

@router.post("/verify-token")
async def verify_agent_jwt_token(token: str):
    """
    Verify an agent JWT token
    """
    try:
        is_valid, payload = await signature_manager.verify_agent_jwt_token(token)
        
        if not is_valid:
            return {
                "is_valid": False,
                "error": payload.get("error", "Token verification failed"),
                "verified_at": datetime.utcnow().isoformat()
            }
        
        return {
            "is_valid": True,
            "agent_name": payload.get("agent_name"),
            "signature_fingerprint": payload.get("public_key_fingerprint"),
            "issued_at": datetime.fromtimestamp(payload.get("iat", 0)).isoformat(),
            "expires_at": datetime.fromtimestamp(payload.get("exp", 0)).isoformat(),
            "verified_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error verifying JWT token: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to verify token: {str(e)}"
        )

@router.post("/sign-all-agents")
async def sign_all_available_agents():
    """
    Sign all available agents in the system
    """
    try:
        # Get all available agents
        all_agents = await agent_loader.get_all_agents()
        
        signed_agents = []
        failed_agents = []
        
        for agent_name, agent_config in all_agents.items():
            try:
                # Check if already signed and valid
                existing_signature = await signature_manager.get_agent_signature(agent_name)
                if existing_signature and datetime.utcnow() < existing_signature.expires_at:
                    signed_agents.append({
                        "agent_name": agent_name,
                        "status": "already_signed",
                        "expires_at": existing_signature.expires_at.isoformat()
                    })
                    continue
                
                # Sign the agent
                signed_agent = await signature_manager.create_signed_agent(
                    agent_name=agent_name,
                    agent_definition=agent_config
                )
                
                signed_agents.append({
                    "agent_name": agent_name,
                    "status": "newly_signed" if not existing_signature else "re_signed",
                    "expires_at": signed_agent.signature.expires_at.isoformat(),
                    "is_verified": signed_agent.is_verified
                })
                
            except Exception as e:
                logger.warning(f"⚠️ Failed to sign agent {agent_name}: {e}")
                failed_agents.append({
                    "agent_name": agent_name,
                    "error": str(e)
                })
        
        return {
            "total_agents": len(all_agents),
            "signed_successfully": len(signed_agents),
            "failed_signatures": len(failed_agents),
            "signed_agents": signed_agents,
            "failed_agents": failed_agents,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error signing all agents: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to sign all agents: {str(e)}"
        )

