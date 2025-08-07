"""
Digital Signatures System for Agent Validation
Cryptographic validation to ensure agent integrity and authenticity
"""

import hashlib
import json
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import structlog
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
import jwt
from pathlib import Path

from src.core.config import settings
from src.core.redis import get_redis_client

logger = structlog.get_logger()

@dataclass
class AgentSignature:
    """Represents a cryptographic signature for an agent"""
    agent_name: str
    signature_hash: str
    public_key_fingerprint: str
    signed_at: datetime
    expires_at: datetime
    agent_definition_hash: str
    signature_algorithm: str
    metadata: Dict[str, Any]

@dataclass
class SignedAgent:
    """Complete signed agent definition"""
    agent_name: str
    agent_definition: Dict[str, Any]
    signature: AgentSignature
    is_verified: bool
    verification_timestamp: Optional[datetime] = None

class DigitalSignatureManager:
    """Manages digital signatures for AI agents"""
    
    def __init__(self):
        self.signatures_cache: Dict[str, AgentSignature] = {}
        self.private_key = None
        self.public_key = None
        self.redis_client = None
        
    async def initialize(self):
        """Initialize the digital signature system"""
        logger.info("🔐 Initializing Digital Signature Manager")
        
        # Initialize Redis connection
        self.redis_client = get_redis_client()
        
        # Load or generate RSA key pair
        await self._initialize_cryptographic_keys()
        
        # Load existing signatures
        await self._load_signatures_cache()
        
        logger.info("✅ Digital Signature Manager initialized")

    async def _initialize_cryptographic_keys(self):
        """Initialize RSA key pair for signing"""
        
        signatures_dir = Path("secrets/signatures")
        signatures_dir.mkdir(parents=True, exist_ok=True)
        
        private_key_path = signatures_dir / "agent_signing_key.pem"
        public_key_path = signatures_dir / "agent_public_key.pem"
        
        try:
            # Try to load existing keys
            if private_key_path.exists() and public_key_path.exists():
                with open(private_key_path, 'rb') as f:
                    self.private_key = serialization.load_pem_private_key(
                        f.read(),
                        password=None,
                        backend=default_backend()
                    )
                
                with open(public_key_path, 'rb') as f:
                    self.public_key = serialization.load_pem_public_key(
                        f.read(),
                        backend=default_backend()
                    )
                
                logger.info("🔑 Loaded existing cryptographic keys")
            else:
                # Generate new key pair
                self.private_key = rsa.generate_private_key(
                    public_exponent=65537,
                    key_size=2048,
                    backend=default_backend()
                )
                self.public_key = self.private_key.public_key()
                
                # Save keys to disk
                with open(private_key_path, 'wb') as f:
                    f.write(self.private_key.private_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PrivateFormat.PKCS8,
                        encryption_algorithm=serialization.NoEncryption()
                    ))
                
                with open(public_key_path, 'wb') as f:
                    f.write(self.public_key.public_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PublicFormat.SubjectPublicKeyInfo
                    ))
                
                logger.info("🔑 Generated new cryptographic key pair")
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize cryptographic keys: {e}")
            raise

    async def _load_signatures_cache(self):
        """Load existing signatures from Redis cache"""
        
        try:
            if self.redis_client:
                keys = await self.redis_client.keys("agent_signature:*")
                for key in keys:
                    signature_data = await self.redis_client.get(key)
                    if signature_data:
                        signature_dict = json.loads(signature_data)
                        # Convert datetime strings back to datetime objects
                        signature_dict['signed_at'] = datetime.fromisoformat(signature_dict['signed_at'])
                        signature_dict['expires_at'] = datetime.fromisoformat(signature_dict['expires_at'])
                        
                        signature = AgentSignature(**signature_dict)
                        self.signatures_cache[signature.agent_name] = signature
                
                logger.info(f"🔐 Loaded {len(self.signatures_cache)} agent signatures from cache")
        except Exception as e:
            logger.warning(f"⚠️ Could not load signatures cache: {e}")

    async def sign_agent(
        self,
        agent_name: str,
        agent_definition: Dict[str, Any],
        validity_days: int = 365
    ) -> AgentSignature:
        """Create a digital signature for an agent definition"""
        
        try:
            # Create agent definition hash
            definition_json = json.dumps(agent_definition, sort_keys=True)
            definition_hash = hashlib.sha256(definition_json.encode()).hexdigest()
            
            # Create signature payload
            now = datetime.utcnow()
            expires_at = now + timedelta(days=validity_days)
            
            signature_payload = {
                "agent_name": agent_name,
                "agent_definition_hash": definition_hash,
                "signed_at": now.isoformat(),
                "expires_at": expires_at.isoformat(),
                "signature_algorithm": "RSA-SHA256"
            }
            
            # Sign the payload
            payload_json = json.dumps(signature_payload, sort_keys=True)
            signature_bytes = self.private_key.sign(
                payload_json.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            # Create signature hash
            signature_hash = base64.b64encode(signature_bytes).decode()
            
            # Create public key fingerprint
            public_key_bytes = self.public_key.public_bytes(
                encoding=serialization.Encoding.DER,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            public_key_fingerprint = hashlib.sha256(public_key_bytes).hexdigest()[:16]
            
            # Create signature object
            signature = AgentSignature(
                agent_name=agent_name,
                signature_hash=signature_hash,
                public_key_fingerprint=public_key_fingerprint,
                signed_at=now,
                expires_at=expires_at,
                agent_definition_hash=definition_hash,
                signature_algorithm="RSA-SHA256",
                metadata={
                    "signed_by": "convergio_signature_manager",
                    "version": "1.0",
                    "environment": settings.environment
                }
            )
            
            # Cache signature
            self.signatures_cache[agent_name] = signature
            await self._save_signature_to_redis(signature)
            
            logger.info(f"🔐 Created digital signature for agent {agent_name}")
            return signature
            
        except Exception as e:
            logger.error(f"❌ Failed to sign agent {agent_name}: {e}")
            raise

    async def verify_agent_signature(
        self,
        agent_name: str,
        agent_definition: Dict[str, Any],
        signature: Optional[AgentSignature] = None
    ) -> Tuple[bool, str]:
        """Verify an agent's digital signature"""
        
        try:
            # Get signature if not provided
            if not signature:
                signature = self.signatures_cache.get(agent_name)
                if not signature:
                    return False, f"No signature found for agent {agent_name}"
            
            # Check if signature has expired
            if datetime.utcnow() > signature.expires_at:
                return False, f"Signature for agent {agent_name} has expired"
            
            # Verify agent definition hash
            definition_json = json.dumps(agent_definition, sort_keys=True)
            current_hash = hashlib.sha256(definition_json.encode()).hexdigest()
            
            if current_hash != signature.agent_definition_hash:
                return False, f"Agent definition hash mismatch for {agent_name}"
            
            # Reconstruct signature payload
            signature_payload = {
                "agent_name": signature.agent_name,
                "agent_definition_hash": signature.agent_definition_hash,
                "signed_at": signature.signed_at.isoformat(),
                "expires_at": signature.expires_at.isoformat(),
                "signature_algorithm": signature.signature_algorithm
            }
            
            # Verify signature
            payload_json = json.dumps(signature_payload, sort_keys=True)
            signature_bytes = base64.b64decode(signature.signature_hash.encode())
            
            try:
                self.public_key.verify(
                    signature_bytes,
                    payload_json.encode(),
                    padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH
                    ),
                    hashes.SHA256()
                )
                
                logger.info(f"✅ Agent signature verified for {agent_name}")
                return True, "Signature verified successfully"
                
            except Exception as verify_error:
                logger.warning(f"❌ Signature verification failed for {agent_name}: {verify_error}")
                return False, f"Invalid signature for agent {agent_name}"
                
        except Exception as e:
            logger.error(f"❌ Signature verification error for {agent_name}: {e}")
            return False, f"Verification error: {str(e)}"

    async def create_signed_agent(
        self,
        agent_name: str,
        agent_definition: Dict[str, Any]
    ) -> SignedAgent:
        """Create a complete signed agent with verification"""
        
        # Create signature
        signature = await self.sign_agent(agent_name, agent_definition)
        
        # Verify signature
        is_verified, verification_message = await self.verify_agent_signature(
            agent_name, agent_definition, signature
        )
        
        signed_agent = SignedAgent(
            agent_name=agent_name,
            agent_definition=agent_definition,
            signature=signature,
            is_verified=is_verified,
            verification_timestamp=datetime.utcnow() if is_verified else None
        )
        
        logger.info(f"🔐 Created signed agent {agent_name} - verified: {is_verified}")
        return signed_agent

    async def get_agent_signature(self, agent_name: str) -> Optional[AgentSignature]:
        """Get signature for an agent"""
        return self.signatures_cache.get(agent_name)

    async def list_signed_agents(self) -> List[Dict[str, Any]]:
        """List all signed agents with their signature status"""
        
        signed_agents = []
        for agent_name, signature in self.signatures_cache.items():
            is_expired = datetime.utcnow() > signature.expires_at
            
            signed_agents.append({
                "agent_name": agent_name,
                "signed_at": signature.signed_at.isoformat(),
                "expires_at": signature.expires_at.isoformat(),
                "is_expired": is_expired,
                "signature_algorithm": signature.signature_algorithm,
                "public_key_fingerprint": signature.public_key_fingerprint,
                "metadata": signature.metadata
            })
        
        return signed_agents

    async def revoke_agent_signature(self, agent_name: str) -> bool:
        """Revoke an agent's signature"""
        
        try:
            if agent_name in self.signatures_cache:
                del self.signatures_cache[agent_name]
                
                # Remove from Redis
                if self.redis_client:
                    await self.redis_client.delete(f"agent_signature:{agent_name}")
                
                logger.info(f"🔐 Revoked signature for agent {agent_name}")
                return True
            else:
                logger.warning(f"⚠️ No signature found to revoke for agent {agent_name}")
                return False
        except Exception as e:
            logger.error(f"❌ Failed to revoke signature for {agent_name}: {e}")
            return False

    async def _save_signature_to_redis(self, signature: AgentSignature):
        """Save signature to Redis for persistence"""
        
        try:
            if self.redis_client:
                signature_dict = asdict(signature)
                # Convert datetime objects to ISO strings
                signature_dict['signed_at'] = signature.signed_at.isoformat()
                signature_dict['expires_at'] = signature.expires_at.isoformat()
                
                await self.redis_client.setex(
                    f"agent_signature:{signature.agent_name}",
                    86400 * 365,  # 1 year TTL
                    json.dumps(signature_dict)
                )
        except Exception as e:
            logger.warning(f"⚠️ Could not save signature to Redis: {e}")

    async def create_agent_jwt_token(
        self,
        agent_name: str,
        signature: AgentSignature,
        validity_minutes: int = 60
    ) -> str:
        """Create a JWT token for agent authentication"""
        
        now = datetime.utcnow()
        expires_at = now + timedelta(minutes=validity_minutes)
        
        payload = {
            "agent_name": agent_name,
            "signature_hash": signature.signature_hash[:16],  # Short hash for JWT
            "public_key_fingerprint": signature.public_key_fingerprint,
            "iat": now,
            "exp": expires_at,
            "iss": "convergio_signature_manager",
            "aud": "convergio_agents"
        }
        
        # Use the same private key for JWT signing
        private_key_pem = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        token = jwt.encode(payload, private_key_pem, algorithm="RS256")
        return token

    async def verify_agent_jwt_token(self, token: str) -> Tuple[bool, Dict[str, Any]]:
        """Verify an agent JWT token"""
        
        try:
            # Use public key for JWT verification
            public_key_pem = self.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            payload = jwt.decode(
                token,
                public_key_pem,
                algorithms=["RS256"],
                audience="convergio_agents",
                issuer="convergio_signature_manager"
            )
            
            return True, payload
        except jwt.ExpiredSignatureError:
            return False, {"error": "Token has expired"}
        except jwt.InvalidTokenError as e:
            return False, {"error": f"Invalid token: {str(e)}"}
        except Exception as e:
            return False, {"error": f"Token verification error: {str(e)}"}

# Global digital signature manager instance
signature_manager = DigitalSignatureManager()