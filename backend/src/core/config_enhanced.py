"""
🔧 Convergio - Enhanced Configuration Management
Dynamic, validated configuration with fail-fast startup and secure defaults
"""

import os
import secrets
import string
from pathlib import Path
from typing import List, Optional, Dict
from functools import lru_cache
import structlog

# Proactively load environment from backend/.env and root .env if present
try:
    from dotenv import load_dotenv
    # Resolve repository root (…/convergio)
    # __file__ = …/backend/src/core/config_enhanced.py → parents[3] = repo root
    project_root = Path(__file__).resolve().parents[3]
    backend_env = project_root / "backend" / ".env"
    root_env = project_root / ".env"
    # Load root first, then backend to allow backend/.env to override if both exist
    if root_env.exists():
        load_dotenv(dotenv_path=root_env, override=False)
    if backend_env.exists():
        load_dotenv(dotenv_path=backend_env, override=True)
except Exception:
    # Dotenv not available or load failed; rely on process env
    pass

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = structlog.get_logger(__name__)

class ConfigurationError(Exception):
    """Configuration validation error"""
    pass

class EnhancedSettings(BaseSettings):
    """Enhanced application settings with comprehensive validation and secure defaults"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    # ================================
    # 🌐 APPLICATION SETTINGS
    # ================================
    
    ENVIRONMENT: str = Field(default="development", description="Environment name")
    DEBUG: bool = Field(default=False, description="Debug mode - NEVER true in production")
    BASE_URL: str = Field(default="http://localhost:9000", description="Base application URL")
    
    # API Configuration with dynamic defaults
    API_V1_PREFIX: str = Field(default="/api/v1", description="API version 1 prefix") 
    PROJECT_NAME: str = Field(default="Convergio", description="Project name")
    PROJECT_VERSION: str = Field(default="2.0.0", description="Project version")
    
    # ================================
    # 🔌 SERVER CONFIGURATION  
    # ================================
    
    HOST: str = Field(default="0.0.0.0", description="Server host - configurable for all environments")
    PORT: int = Field(default=9000, description="Server port")
    WORKERS: int = Field(default=1, description="Number of worker processes")
    
    # ================================
    # 🗄️ DATABASE CONFIGURATION - All configurable
    # ================================
    
    # PostgreSQL - No hardcoded defaults in production
    POSTGRES_HOST: str = Field(description="PostgreSQL host - REQUIRED")
    POSTGRES_PORT: int = Field(default=5432, description="PostgreSQL port")  
    POSTGRES_DB: str = Field(description="PostgreSQL database - REQUIRED")
    POSTGRES_USER: str = Field(description="PostgreSQL user - REQUIRED")
    POSTGRES_PASSWORD: str = Field(description="PostgreSQL password - REQUIRED")
    
    # Connection settings
    DB_POOL_SIZE: int = Field(default=20, description="Database connection pool size")
    DB_POOL_OVERFLOW: int = Field(default=30, description="Database pool overflow")
    DB_POOL_TIMEOUT: int = Field(default=30, description="Database pool timeout")
    DB_POOL_RECYCLE: int = Field(default=3600, description="Database pool recycle time")
    
    @property
    def DATABASE_URL(self) -> str:
        """Async PostgreSQL database URL"""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
    
    @property 
    def DATABASE_URL_SYNC(self) -> str:
        """Sync PostgreSQL database URL (for migrations)"""
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
    
    # ================================
    # 🚀 REDIS CONFIGURATION - All configurable
    # ================================
    
    REDIS_HOST: str = Field(description="Redis host - REQUIRED")
    REDIS_PORT: int = Field(default=6379, description="Redis port")
    REDIS_DB: int = Field(default=1, description="Redis database")  
    REDIS_PASSWORD: Optional[str] = Field(default=None, description="Redis password")
    REDIS_POOL_SIZE: int = Field(default=20, description="Redis connection pool size")
    
    @property
    def REDIS_URL(self) -> str:
        """Redis connection URL"""
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # ================================
    # 🔐 SECURITY CONFIGURATION - Secure by default
    # ================================
    
    # JWT Configuration - Secure generation
    JWT_ALGORITHM: str = Field(default="RS256", description="JWT algorithm - Only RS256 allowed")
    JWT_TOKEN_EXPIRY: int = Field(default=86400, description="JWT token expiry (24h)")  
    JWT_REFRESH_EXPIRY: int = Field(default=2592000, description="JWT refresh expiry (30d)")
    JWT_ISSUER: str = Field(default="convergio.io", description="JWT issuer")
    JWT_AUDIENCE: str = Field(default="convergio.io", description="JWT audience")
    
    # NO DEFAULT JWT SECRET - Must be provided or generated
    JWT_SECRET: str = Field(description="JWT secret key - GENERATED SECURELY")
    
    # RSA Keys for JWT signing
    JWT_PRIVATE_KEY_PATH: str = Field(
        default="secrets/jwt/key_active.pem", 
        description="JWT RSA private key path"
    )
    JWT_PUBLIC_KEY_PATH: str = Field(
        default="secrets/jwt/key_active.pub.pem",
        description="JWT RSA public key path"  
    )
    
    # Password hashing
    BCRYPT_ROUNDS: int = Field(default=12, description="Bcrypt rounds for password hashing")
    
    # CORS settings - Environment specific
    CORS_ALLOWED_ORIGINS: str = Field(
        description="CORS allowed origins (comma-separated) - REQUIRED for security"
    )
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convert CORS origins string to list"""
        return [origin.strip() for origin in self.CORS_ALLOWED_ORIGINS.split(",")]
    
    # Trusted hosts (production)  
    TRUSTED_HOSTS: str = Field(
        default="localhost,127.0.0.1",
        description="Trusted hosts (comma-separated)"
    )
    
    @property
    def trusted_hosts_list(self) -> List[str]:
        """Convert trusted hosts string to list"""
        return [host.strip() for host in self.TRUSTED_HOSTS.split(",")]
    
    # ================================
    # 🤖 AI CONFIGURATION - All required
    # ================================
    
    # OpenAI API - REQUIRED
    OPENAI_API_KEY: str = Field(description="OpenAI API key - REQUIRED")
    OPENAI_MODEL: str = Field(default="gpt-4o-mini", description="Default OpenAI model")
    OPENAI_MAX_TOKENS: int = Field(default=2048, description="OpenAI max tokens")
    
    # Anthropic API - REQUIRED
    ANTHROPIC_API_KEY: str = Field(description="Anthropic API key - REQUIRED")
    ANTHROPIC_MODEL: str = Field(default="claude-3-sonnet-20240229", description="Default Anthropic model")
    
    # Perplexity API - Optional but validated if provided
    PERPLEXITY_API_KEY: Optional[str] = Field(default=None, description="Perplexity API key")
    PERPLEXITY_MODEL: str = Field(default="sonar", description="Default Perplexity model")
    
    # Vector Search
    VECTOR_DIMENSION: int = Field(default=1536, description="Vector embedding dimension")
    VECTOR_INDEX_TYPE: str = Field(default="HNSW", description="Vector index type")
    
    # ================================
    # 📊 MONITORING & LOGGING
    # ================================
    
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FORMAT: str = Field(default="json", description="Log format (json/console)")
    
    # Metrics
    METRICS_ENABLED: bool = Field(default=True, description="Enable Prometheus metrics")
    PROMETHEUS_ENDPOINT: str = Field(default="", description="Prometheus endpoint URL")
    
    # Observability
    OTEL_EXPORTER_OTLP_ENDPOINT: str = Field(default="", description="OpenTelemetry OTLP endpoint")
    
    # ================================
    # 🚦 RATE LIMITING - Enhanced configuration
    # ================================
    
    RATE_LIMITING_ENABLED: bool = Field(default=True, description="Enable rate limiting by default")
    RATE_LIMIT_PER_MINUTE: int = Field(default=100, description="Rate limit per minute")
    RATE_LIMIT_BURST: int = Field(default=200, description="Rate limit burst")
    
    # Per-endpoint rate limits
    RATE_LIMITS: Dict[str, Dict[str, int]] = Field(
        default={
            "auth": {"per_minute": 5, "burst": 10},
            "api": {"per_minute": 100, "burst": 200}, 
            "admin": {"per_minute": 10, "burst": 20},
            "public": {"per_minute": 1000, "burst": 2000}
        },
        description="Rate limits per endpoint type"
    )
    
    # ================================
    # 💰 COST MANAGEMENT
    # ================================
    
    MAX_CONVERSATION_COST: float = Field(default=5.0, description="Maximum allowed cost per conversation (USD)")
    
    # ================================
    # 🏁 FEATURE FLAGS
    # ================================
    
    ENABLE_DOCS: bool = Field(default=True, description="Enable API documentation")
    ENABLE_VECTOR_SEARCH: bool = Field(default=True, description="Enable vector search")
    ENABLE_AI_AGENTS: bool = Field(default=True, description="Enable AI agents")
    ENABLE_BACKGROUND_TASKS: bool = Field(default=True, description="Enable background tasks")
    
    # ================================
    # ✅ COMPREHENSIVE VALIDATORS
    # ================================
    
    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v):
        """Validate environment name"""
        allowed = ["development", "staging", "production", "test"] 
        if v not in allowed:
            raise ConfigurationError(f"Environment must be one of: {allowed}")
        return v
    
    @field_validator("DEBUG")
    @classmethod 
    def validate_debug_for_production(cls, v, info):
        """Ensure debug is False in production"""
        if info.data.get("ENVIRONMENT") == "production" and v:
            raise ConfigurationError("DEBUG must be False in production environment")
        return v
    
    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level"""
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed:
            raise ConfigurationError(f"Log level must be one of: {allowed}")
        return v.upper()
    
    @field_validator("JWT_ALGORITHM")
    @classmethod
    def validate_jwt_algorithm(cls, v):
        """Validate JWT algorithm"""
        if v != "RS256":
            raise ConfigurationError("Only RS256 algorithm is supported for security")
        return v
    
    @field_validator("JWT_SECRET")
    @classmethod
    def validate_jwt_secret(cls, v, info):
        """Validate JWT secret strength"""
        if not v or len(v) < 32:
            raise ConfigurationError("JWT_SECRET must be at least 32 characters long")
        
        # In production, no default/weak secrets allowed
        if info.data.get("ENVIRONMENT") == "production":
            weak_secrets = [
                "your-super-secret-jwt-key-here-change-in-production",
                "change-me",
                "secret",
                "password"
            ]
            if v.lower() in [s.lower() for s in weak_secrets]:
                raise ConfigurationError("Weak JWT_SECRET detected in production environment")
        
        return v
    
    @field_validator("CORS_ALLOWED_ORIGINS")
    @classmethod
    def validate_cors_origins(cls, v, info):
        """Validate CORS origins for security"""
        origins = [origin.strip() for origin in v.split(",")]
        
        # In production, wildcard origins are not allowed
        if info.data.get("ENVIRONMENT") == "production":
            if "*" in origins:
                raise ConfigurationError("Wildcard CORS origins not allowed in production")
        
        # Validate origin format
        for origin in origins:
            if not origin.startswith(("http://", "https://")) and origin != "*":
                raise ConfigurationError(f"Invalid CORS origin format: {origin}")
        
        return v
    
    @model_validator(mode='after')
    def validate_production_security(self):
        """Comprehensive production security validation"""
        if self.ENVIRONMENT == "production":
            errors = []
            
            # Ensure secure database connection
            if "localhost" in self.POSTGRES_HOST:
                errors.append("Production should not use localhost for database")
            
            # Ensure secure Redis connection  
            if "localhost" in self.REDIS_HOST:
                errors.append("Production should not use localhost for Redis")
                
            # Require HTTPS in production BASE_URL
            if not self.BASE_URL.startswith("https://"):
                errors.append("Production BASE_URL must use HTTPS")
                
            # Require Redis password in production
            if not self.REDIS_PASSWORD:
                errors.append("Redis password required in production")
            
            if errors:
                raise ConfigurationError(f"Production security violations: {'; '.join(errors)}")
        
        return self

class DynamicConfigurationManager:
    """Dynamic configuration manager with secure default generation"""
    
    def __init__(self):
        self.logger = structlog.get_logger(__name__)
        self.settings: Optional[EnhancedSettings] = None
    
    def generate_secure_defaults(self) -> Dict[str, str]:
        """Generate secure defaults for development environments"""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        
        # Get configurable host for multi-environment support
        default_host = os.getenv("DEFAULT_HOST", "localhost")
        frontend_port = os.getenv("FRONTEND_PORT", "4000")
        api_port = os.getenv("API_PORT", "3000")
        
        defaults = {
            "JWT_SECRET": ''.join(secrets.choice(alphabet) for _ in range(64)),
            "POSTGRES_HOST": default_host,
            "POSTGRES_DB": "convergio_dev",
            "POSTGRES_USER": "convergio_user", 
            "POSTGRES_PASSWORD": ''.join(secrets.choice(alphabet) for _ in range(32)),
            "REDIS_HOST": default_host,
            "CORS_ALLOWED_ORIGINS": f"http://{default_host}:{frontend_port},http://{default_host}:{api_port}",
        }
        
        return defaults
    
    def validate_required_vars(self) -> bool:
        """Validate all required environment variables are present"""
        try:
            # Try to create settings - will raise if validation fails
            self.settings = EnhancedSettings()
            self.logger.info("✅ Configuration validation successful")
            return True
        except Exception as e:
            self.logger.error(f"❌ Configuration validation failed: {e}")
            return False
    
    def get_settings(self) -> EnhancedSettings:
        """Get validated settings or fail fast"""
        if not self.settings:
            if not self.validate_required_vars():
                raise ConfigurationError("Configuration validation failed - cannot start application")
        
        return self.settings
    
    def setup_development_defaults(self) -> None:
        """Setup secure defaults for development and test environments.

        Ensures the app can boot in local/test runs without requiring full
        production-grade configuration. We also set placeholder AI keys so
        health checks mark services as disabled instead of failing.
        """
        env = os.getenv("ENVIRONMENT", "development").lower()
        if env in ("development", "test"):
            defaults = self.generate_secure_defaults()

            # Required fields without safe library defaults
            required_overrides = {
                # Provide permissive CORS in non-production to simplify tests/dev
                "CORS_ALLOWED_ORIGINS": os.getenv("CORS_ALLOWED_ORIGINS", "*"),
                # AI API keys as placeholders so health check treats them as disabled
                # and avoids making outbound calls during tests
                "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", "sk-..."),
                "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY", "sk-ant-..."),
                # Commonly referenced base URL/port
                "HOST": os.getenv("HOST", "0.0.0.0"),
                "PORT": os.getenv("PORT", os.getenv("BACKEND_PORT", "9000")),
            }

            # Merge defaults with overrides; env vars remain authoritative
            for key, value in {**defaults, **required_overrides}.items():
                if not os.getenv(key):
                    os.environ[key] = str(value)
                    self.logger.info(f"Generated default for {key}")

# Global configuration manager instance
config_manager = DynamicConfigurationManager()

@lru_cache()
def get_enhanced_settings() -> EnhancedSettings:
    """Get cached enhanced application settings with fail-fast validation"""
    return config_manager.get_settings()

def initialize_configuration() -> EnhancedSettings:
    """Initialize configuration with fail-fast behavior"""
    logger.info("🔧 Initializing enhanced configuration system...")
    
    # Setup development defaults if needed
    config_manager.setup_development_defaults()
    
    # Validate configuration or fail
    if not config_manager.validate_required_vars():
        logger.error("❌ Configuration validation failed - terminating startup")
        exit(1)
    
    settings = config_manager.get_settings()
    logger.info("✅ Enhanced configuration system initialized successfully")
    
    return settings