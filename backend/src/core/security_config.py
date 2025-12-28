"""
🔐 Convergio - Security Configuration Manager
Generate secure defaults and validate security configurations
"""

import os
import secrets
import string
from pathlib import Path
from typing import Dict, List
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import structlog

logger = structlog.get_logger(__name__)

class SecurityConfigManager:
    """Manage security configurations and generate secure defaults"""
    
    def __init__(self):
        self.logger = structlog.get_logger(__name__)
        self.project_root = Path(__file__).resolve().parents[3]
        self.secrets_dir = self.project_root / "backend" / "secrets"
        
    def generate_secure_jwt_secret(self, length: int = 64) -> str:
        """Generate a cryptographically secure JWT secret"""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*+-=[]{}|;:,.<>?"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def generate_secure_password(self, length: int = 32) -> str:
        """Generate a secure password for services"""
        # Ensure at least one character from each category
        upper = string.ascii_uppercase
        lower = string.ascii_lowercase
        digits = string.digits
        special = "!@#$%^&*+-=[]{}|;:,.<>?"
        
        password = [
            secrets.choice(upper),
            secrets.choice(lower), 
            secrets.choice(digits),
            secrets.choice(special)
        ]
        
        # Fill the rest randomly
        all_chars = upper + lower + digits + special
        for _ in range(length - 4):
            password.append(secrets.choice(all_chars))
        
        # Shuffle to avoid predictable patterns
        secrets.SystemRandom().shuffle(password)
        return ''.join(password)
    
    def generate_rsa_keypair(self, key_size: int = 2048) -> tuple[str, str]:
        """Generate RSA private/public key pair for JWT signing"""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
        )
        
        # Private key in PEM format
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')
        
        # Public key in PEM format
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')
        
        return private_pem, public_pem
    
    def setup_jwt_keys(self, force_regenerate: bool = False) -> Dict[str, str]:
        """Setup JWT RSA keys"""
        jwt_dir = self.secrets_dir / "jwt"
        jwt_dir.mkdir(parents=True, exist_ok=True)
        
        private_key_path = jwt_dir / "key_active.pem"
        public_key_path = jwt_dir / "key_active.pub.pem"
        
        # Check if keys already exist
        if not force_regenerate and private_key_path.exists() and public_key_path.exists():
            self.logger.info("JWT keys already exist, skipping generation")
            return {
                "JWT_PRIVATE_KEY_PATH": str(private_key_path),
                "JWT_PUBLIC_KEY_PATH": str(public_key_path)
            }
        
        # Generate new keypair
        self.logger.info("Generating new RSA keypair for JWT signing")
        private_pem, public_pem = self.generate_rsa_keypair()
        
        # Save keys with secure permissions
        private_key_path.write_text(private_pem)
        private_key_path.chmod(0o600)  # Owner read-write only
        
        public_key_path.write_text(public_pem)
        public_key_path.chmod(0o644)  # Owner read-write, group/other read
        
        self.logger.info("JWT RSA keypair generated successfully")
        
        return {
            "JWT_PRIVATE_KEY_PATH": str(private_key_path),
            "JWT_PUBLIC_KEY_PATH": str(public_key_path)
        }
    
    def get_secure_cors_origins(self, environment: str) -> str:
        """Get secure CORS origins for environment"""
        if environment == "production":
            # In production, only allow specific domains
            return "https://app.convergio.io,https://admin.convergio.io"
        elif environment == "staging":
            return "https://staging.convergio.io,https://staging-admin.convergio.io"
        else:
            # Development - configurable host and ports
            host = os.getenv("DEFAULT_HOST", "localhost")
            frontend_port = os.getenv("FRONTEND_PORT", "4000")
            api_port = os.getenv("API_PORT", "3000")
            backend_port = os.getenv("BACKEND_PORT", "8000")
            return f"http://{host}:{api_port},http://{host}:{frontend_port},http://{host}:{backend_port}"
    
    def get_secure_trusted_hosts(self, environment: str) -> str:
        """Get secure trusted hosts for environment"""
        if environment == "production":
            return "convergio.io,*.convergio.io,app.convergio.io"
        elif environment == "staging":
            return "staging.convergio.io,*.staging.convergio.io"
        else:
            return "localhost,127.0.0.1"
    
    def validate_production_security(self, config: Dict[str, str]) -> List[str]:
        """Validate production security configuration"""
        errors = []
        
        # Check JWT secret strength
        jwt_secret = config.get("JWT_SECRET", "")
        if len(jwt_secret) < 32:
            errors.append("JWT_SECRET must be at least 32 characters long")
        
        # Check for weak/default passwords
        weak_patterns = ["password", "admin", "secret", "changeme", "default"]
        for key, value in config.items():
            if "PASSWORD" in key.upper():
                if any(weak in value.lower() for weak in weak_patterns):
                    errors.append(f"{key} contains weak password pattern")
        
        # Check CORS configuration
        cors_origins = config.get("CORS_ALLOWED_ORIGINS", "")
        if "*" in cors_origins:
            errors.append("Wildcard CORS origins not allowed in production")
        
        # Check for localhost references in production
        for key, value in config.items():
            if "localhost" in value.lower() and key in ["POSTGRES_HOST", "REDIS_HOST", "BASE_URL"]:
                errors.append(f"{key} should not use localhost in production")
        
        # Check HTTPS enforcement
        base_url = config.get("BASE_URL", "")
        if base_url and not base_url.startswith("https://"):
            errors.append("BASE_URL must use HTTPS in production")
        
        return errors
    
    def generate_development_config(self) -> Dict[str, str]:
        """Generate secure development configuration"""
        config = {
            "ENVIRONMENT": "development",
            "DEBUG": "false",  # Even in dev, start with false
            "JWT_SECRET": self.generate_secure_jwt_secret(),
            "POSTGRES_HOST": "localhost",
            "POSTGRES_PORT": "5432",
            "POSTGRES_DB": "convergio_dev",
            "POSTGRES_USER": "convergio_dev",
            "POSTGRES_PASSWORD": self.generate_secure_password(16),
            "REDIS_HOST": "localhost", 
            "REDIS_PORT": "6379",
            "REDIS_DB": "1",
            "REDIS_PASSWORD": self.generate_secure_password(16),
            "CORS_ALLOWED_ORIGINS": self.get_secure_cors_origins("development"),
            "TRUSTED_HOSTS": self.get_secure_trusted_hosts("development"),
            "RATE_LIMITING_ENABLED": "true",
            "BASE_URL": "http://localhost:9000"
        }
        
        # Add JWT key paths
        jwt_config = self.setup_jwt_keys()
        config.update(jwt_config)
        
        return config
    
    def generate_production_template(self) -> Dict[str, str]:
        """Generate production configuration template"""
        config = {
            "ENVIRONMENT": "production",
            "DEBUG": "false", 
            "JWT_SECRET": "{{ CHANGE_ME_64_CHAR_SECRET }}",
            "POSTGRES_HOST": "{{ PRODUCTION_DB_HOST }}",
            "POSTGRES_PORT": "5432",
            "POSTGRES_DB": "{{ PRODUCTION_DB_NAME }}",
            "POSTGRES_USER": "{{ PRODUCTION_DB_USER }}",
            "POSTGRES_PASSWORD": "{{ PRODUCTION_DB_PASSWORD }}",
            "REDIS_HOST": "{{ PRODUCTION_REDIS_HOST }}",
            "REDIS_PORT": "6379", 
            "REDIS_DB": "0",
            "REDIS_PASSWORD": "{{ PRODUCTION_REDIS_PASSWORD }}",
            "CORS_ALLOWED_ORIGINS": "{{ PRODUCTION_DOMAINS }}",
            "TRUSTED_HOSTS": "{{ PRODUCTION_DOMAINS }}",
            "RATE_LIMITING_ENABLED": "true",
            "BASE_URL": "https://{{ PRODUCTION_DOMAIN }}",
            "OPENAI_API_KEY": "{{ OPENAI_API_KEY }}",
            "ANTHROPIC_API_KEY": "{{ ANTHROPIC_API_KEY }}"
        }
        
        return config
    
    def setup_secure_development_environment(self) -> None:
        """Setup secure development environment"""
        env_file = self.project_root / "backend" / ".env"
        
        # Don't overwrite existing .env
        if env_file.exists():
            self.logger.info("Development .env already exists, skipping generation")
            return
        
        config = self.generate_development_config()
        
        # Write .env file
        env_content = []
        env_content.append("# Convergio Development Configuration")
        env_content.append("# Generated automatically with secure defaults")
        env_content.append("")
        
        for key, value in config.items():
            env_content.append(f"{key}={value}")
        
        env_file.write_text('\n'.join(env_content))
        env_file.chmod(0o600)  # Secure permissions
        
        self.logger.info("Secure development .env generated", path=str(env_file))
    
    def create_production_env_template(self) -> None:
        """Create production environment template"""
        template_file = self.project_root / "backend" / ".env.production.template"
        
        config = self.generate_production_template()
        
        content = []
        content.append("# Convergio Production Configuration Template")
        content.append("# Replace all {{ PLACEHOLDER }} values with actual production values")
        content.append("")
        content.append("# SECURITY CHECKLIST:")
        content.append("# - All passwords are strong and unique")
        content.append("# - JWT_SECRET is 64+ characters random")
        content.append("# - No localhost references")
        content.append("# - HTTPS enforced")
        content.append("# - CORS restricted to production domains")
        content.append("")
        
        for key, value in config.items():
            content.append(f"{key}={value}")
        
        template_file.write_text('\n'.join(content))
        
        self.logger.info("Production .env template created", path=str(template_file))

# Global security manager instance
security_manager = SecurityConfigManager()

def initialize_secure_defaults() -> None:
    """Initialize secure defaults for development"""
    security_manager.setup_secure_development_environment()
    security_manager.create_production_env_template()
    security_manager.setup_jwt_keys()

def validate_security_config(config_dict: Dict[str, str], environment: str) -> None:
    """Validate security configuration"""
    if environment == "production":
        errors = security_manager.validate_production_security(config_dict)
        if errors:
            error_msg = f"Production security validation failed: {'; '.join(errors)}"
            raise ValueError(error_msg)
    
    logger.info("✅ Security configuration validated", environment=environment)