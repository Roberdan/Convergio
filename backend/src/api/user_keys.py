"""
🔑 User API Keys Management
Secure handling of user-provided API keys for AI services
"""

import logging
from typing import Dict, Optional
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
import hashlib
from cryptography.fernet import Fernet
import os

logger = logging.getLogger(__name__)

router = APIRouter()

# Encryption key for API keys (should be generated per installation)
ENCRYPTION_KEY = os.environ.get('API_KEY_ENCRYPTION_KEY', Fernet.generate_key().decode())
fernet = Fernet(ENCRYPTION_KEY.encode() if isinstance(ENCRYPTION_KEY, str) else ENCRYPTION_KEY)

class UserAPIKeys(BaseModel):
    """User API Keys model"""
    openai_api_key: Optional[str] = Field(None, description="OpenAI API Key")
    anthropic_api_key: Optional[str] = Field(None, description="Anthropic Claude API Key")
    default_model: Optional[str] = Field(None, description="Preferred default OpenAI model for this session")

class APIKeyStatus(BaseModel):
    """API Key validation status"""
    service: str
    is_configured: bool
    is_valid: Optional[bool] = None
    last_tested: Optional[str] = None
    value: Optional[str] = None  # Optional value field for model or notes


class UserKeysStoreResult(BaseModel):
    """Response model for storing user keys"""
    openai: bool
    anthropic: bool
    stored: bool
    default_model: Optional[str] = None

# In-memory storage for demo (in production, use Redis or database)
user_keys_storage: Dict[str, Dict[str, str]] = {}

def get_user_session_id(request: Request) -> str:
    """Get unique session ID for user (IP-based for demo)"""
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent", "")
    session_data = f"{client_ip}:{user_agent}"
    return hashlib.sha256(session_data.encode()).hexdigest()[:16]

def encrypt_api_key(api_key: str) -> str:
    """Encrypt API key for secure storage"""
    if not api_key:
        return ""
    return fernet.encrypt(api_key.encode()).decode()

def decrypt_api_key(encrypted_key: str) -> str:
    """Decrypt API key for use"""
    if not encrypted_key:
        return ""
    try:
        return fernet.decrypt(encrypted_key.encode()).decode()
    except Exception as e:
        logger.error(f"Failed to decrypt API key: {e}")
        return ""

@router.post("/user-keys", response_model=UserKeysStoreResult)
async def store_user_api_keys(
    keys: UserAPIKeys,
    request: Request
):
    """Store user-provided API keys securely"""
    try:
        session_id = get_user_session_id(request)
        
        # Encrypt and store keys
        encrypted_keys = {}
        if keys.openai_api_key:
            encrypted_keys['openai'] = encrypt_api_key(keys.openai_api_key)
        if keys.anthropic_api_key:
            encrypted_keys['anthropic'] = encrypt_api_key(keys.anthropic_api_key)
        
        # Store preferred model (validated)
        if keys.default_model:
            allowed = {"gpt-4o", "gpt-4o-mini", "gpt-5", "gpt-5-mini", "gpt-5-nano"}
            model = keys.default_model.strip()
            if model in allowed:
                encrypted_keys['model'] = model
            else:
                logger.warning(f"Ignoring unsupported model preference: {model}")
            
        user_keys_storage[session_id] = encrypted_keys
        
        logger.info(f"🔑 Stored API keys for session {session_id}: {list(encrypted_keys.keys())}")
        
        return UserKeysStoreResult(
            openai=bool(keys.openai_api_key),
            anthropic=bool(keys.anthropic_api_key),
            stored=True,
            default_model=encrypted_keys.get('model')
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to store API keys: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to store API keys securely"
        )

@router.get("/user-keys/status", response_model=Dict[str, APIKeyStatus])
async def get_api_keys_status(request: Request):
    """Get status of user's API keys"""
    try:
        session_id = get_user_session_id(request)
        stored_keys = user_keys_storage.get(session_id, {})
        
        status = {
            "openai": APIKeyStatus(
                service="OpenAI",
                is_configured=bool(stored_keys.get('openai'))
            ),
            "anthropic": APIKeyStatus(
                service="Anthropic Claude",
                is_configured=bool(stored_keys.get('anthropic'))
            )
        }
        
        # Include preferred model if set
        if stored_keys.get('model'):
            status["model"] = APIKeyStatus(
                service="OpenAI model",
                is_configured=True,
                value=stored_keys.get('model')
            )
        
        return status
        
    except Exception as e:
        logger.error(f"❌ Failed to get API keys status: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve API keys status"
        )

@router.delete("/user-keys")
async def clear_user_api_keys(request: Request):
    """Clear user's stored API keys"""
    try:
        session_id = get_user_session_id(request)
        
        if session_id in user_keys_storage:
            del user_keys_storage[session_id]
            logger.info(f"🗑️ Cleared API keys for session {session_id}")
            
        return {"cleared": True}
        
    except Exception as e:
        logger.error(f"❌ Failed to clear API keys: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to clear API keys"
        )

def get_user_api_key(request: Request, service: str) -> Optional[str]:
    """Get decrypted API key for a specific service"""
    try:
        session_id = get_user_session_id(request)
        stored_keys = user_keys_storage.get(session_id, {})
        encrypted_key = stored_keys.get(service)
        
        if encrypted_key:
            return decrypt_api_key(encrypted_key)
        return None
        
    except Exception as e:
        logger.error(f"❌ Failed to get API key for {service}: {e}")
        return None

# Preferred model helpers
def get_user_default_model(request: Request) -> Optional[str]:
    """Get user's preferred default model if configured for the session."""
    try:
        session_id = get_user_session_id(request)
        stored = user_keys_storage.get(session_id, {})
        model = stored.get('model')
        return model
    except Exception as e:
        logger.error(f"❌ Failed to get user default model: {e}")
        return None

# Test endpoints for validation
@router.post("/user-keys/test/{service}")
async def test_api_key(service: str, request: Request):
    """Test if an API key is valid"""
    try:
        api_key = get_user_api_key(request, service)
        
        if not api_key:
            raise HTTPException(
                status_code=400,
                detail=f"No {service} API key configured"
            )
        
        # Basic validation - just check format
        if service == "openai":
            is_valid = api_key.startswith("sk-") and len(api_key) > 20
        elif service == "anthropic":
            is_valid = api_key.startswith("sk-ant-") and len(api_key) > 20
        else:
            is_valid = False
            
        return {
            "service": service,
            "is_valid": is_valid,
            "message": "Valid format" if is_valid else "Invalid format"
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to test {service} API key: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to test {service} API key"
        )
