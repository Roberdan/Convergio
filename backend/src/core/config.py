"""
🔧 Convergio - Configuration Management
Environment-based settings with validation and type safety
"""

import os
from pathlib import Path

# Proactively load environment from backend/.env and root .env if present
try:
    from dotenv import load_dotenv
    # Resolve repository root (…/convergio)
    # __file__ = …/backend/src/core/config.py → parents[3] = repo root
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

from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

def _get_default_cors_origins() -> str:
    """Get default CORS origins with configurable host and ports"""
    host = os.getenv("DEFAULT_HOST", "localhost")
    frontend_port = os.getenv("FRONTEND_PORT", "4000")
    backend_port = os.getenv("BACKEND_PORT", "9000")
    admin_port = os.getenv("ADMIN_PORT", "9001")
    
    # Support both localhost and 127.0.0.1 for compatibility
    origins = [
        f"http://{host}:{frontend_port}",
        f"http://{host}:{backend_port}", 
        f"http://{host}:{admin_port}",
        f"http://127.0.0.1:{frontend_port}",
        f"http://127.0.0.1:{backend_port}",
        f"http://127.0.0.1:{admin_port}"
    ]
    return ",".join(origins)


class Settings(BaseSettings):
    """Application settings with environment variable loading"""
    
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
    DEBUG: bool = Field(default=False, description="Debug mode")
    BASE_URL: str = Field(default="http://localhost:9000", description="Base application URL")
    
    # API Configuration
    API_V1_PREFIX: str = Field(default="/api/v1", description="API version 1 prefix") 
    PROJECT_NAME: str = Field(default="Convergio", description="Project name")
    PROJECT_VERSION: str = Field(default="2.0.0", description="Project version")
    
    # Application version from VERSION file
    @property
    def app_version(self) -> str:
        """Get application version from VERSION file"""
        try:
            # Read VERSION at repository root
            version_file = Path(__file__).resolve().parents[3] / "VERSION"
            if version_file.exists():
                return version_file.read_text().strip()
            return self.PROJECT_VERSION
        except Exception:
            return self.PROJECT_VERSION
    
    # Build number (simple implementation)
    @property
    def build_number(self) -> str:
        """Get build number"""
        try:
            # Prefer explicit environment variable
            env_build = os.environ.get("BUILD") or os.environ.get("BUILD_NUMBER")
            if env_build:
                return str(env_build).strip()
            # Prefer BUILD file at repo root; fall back to VERSION
            repo_root = Path(__file__).resolve().parents[3]
            build_file = repo_root / "BUILD"
            if build_file.exists():
                return build_file.read_text().strip()
            version_file = repo_root / "VERSION"
            if version_file.exists():
                return version_file.read_text().strip()
            # Last resort: short git SHA or dev-build
            import subprocess
            result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                capture_output=True, text=True, timeout=2
            )
            if result.returncode == 0:
                return f"git-{result.stdout.strip()}"
            return "dev-build"
        except Exception:
            return "dev-build"
    
    # Environment alias for compatibility
    @property 
    def environment(self) -> str:
        """Get environment (alias for ENVIRONMENT)"""
        return self.ENVIRONMENT
    
    # Debug alias for compatibility  
    @property
    def debug(self) -> bool:
        """Debug mode alias"""
        return self.DEBUG
    
    # ================================
    # 🔌 SERVER CONFIGURATION  
    # ================================
    
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=9000, description="Server port (no conflicts)")
    WORKERS: int = Field(default=1, description="Number of worker processes")
    
    # ================================
    # 🗄️ DATABASE CONFIGURATION
    # ================================
    
    # PostgreSQL (Shared with original Convergio)
    POSTGRES_HOST: str = Field(default="localhost", description="PostgreSQL host")
    POSTGRES_PORT: int = Field(default=5432, description="PostgreSQL port")  
    POSTGRES_DB: str = Field(default="convergio_db", description="PostgreSQL database")
    POSTGRES_USER: str = Field(default="postgres", description="PostgreSQL user")
    POSTGRES_PASSWORD: str = Field(default="postgres", description="PostgreSQL password")
    
    # Connection settings
    DB_POOL_SIZE: int = Field(default=20, description="Database connection pool size")
    DB_POOL_OVERFLOW: int = Field(default=30, description="Database pool overflow")
    DB_POOL_TIMEOUT: int = Field(default=30, description="Database pool timeout")
    DB_POOL_RECYCLE: int = Field(default=3600, description="Database pool recycle time")
    
    # Alias for compatibility
    @property
    def db_port(self) -> int:
        """Database port alias"""
        return self.POSTGRES_PORT
    
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
    # 🚀 REDIS CONFIGURATION
    # ================================
    
    REDIS_HOST: str = Field(default="localhost", description="Redis host")
    REDIS_PORT: int = Field(default=6379, description="Redis port")
    REDIS_DB: int = Field(default=1, description="Redis database (different from original)")  
    REDIS_PASSWORD: Optional[str] = Field(default=None, description="Redis password")
    REDIS_POOL_SIZE: int = Field(default=20, description="Redis connection pool size")
    
    @property
    def REDIS_URL(self) -> str:
        """Redis connection URL"""
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # Aliases for compatibility
    @property
    def redis_port(self) -> int:
        """Redis port alias"""
        return self.REDIS_PORT
    
    @property
    def redis_db(self) -> int:
        """Redis database alias"""
        return self.REDIS_DB
    
    # ================================
    # 🔐 SECURITY CONFIGURATION
    # ================================
    
    # JWT Configuration (RS256 - same as original)
    JWT_ALGORITHM: str = Field(default="RS256", description="JWT algorithm")
    JWT_TOKEN_EXPIRY: int = Field(default=86400, description="JWT token expiry (24h)")  
    JWT_REFRESH_EXPIRY: int = Field(default=2592000, description="JWT refresh expiry (30d)")
    JWT_ISSUER: str = Field(default="convergio.io", description="JWT issuer")
    JWT_AUDIENCE: str = Field(default="convergio.io", description="JWT audience")
    JWT_SECRET: str = Field(default="your-super-secret-jwt-key-here-change-in-production", description="JWT secret key")
    
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
    
    # CORS settings - configurable via environment
    CORS_ALLOWED_ORIGINS: str = Field(
        default_factory=lambda: _get_default_cors_origins(),
        description="CORS allowed origins (comma-separated)"
    )
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convert CORS origins string to list"""
        return [origin.strip() for origin in self.CORS_ALLOWED_ORIGINS.split(",")]
    
    # Trusted hosts (production)  
    TRUSTED_HOSTS: str = Field(
        default="localhost,127.0.0.1,*.convergio.io",
        description="Trusted hosts for production (comma-separated)"
    )
    
    @property
    def trusted_hosts_list(self) -> List[str]:
        """Convert trusted hosts string to list"""
        return [host.strip() for host in self.TRUSTED_HOSTS.split(",")]
    
    # ================================
    # 🤖 AI CONFIGURATION
    # ================================
    
    # OpenAI API
    OPENAI_API_KEY: str = Field(description="OpenAI API key")
    OPENAI_MODEL: str = Field(default="gpt-4o-mini", description="Default OpenAI model")
    OPENAI_MAX_TOKENS: int = Field(default=2048, description="OpenAI max tokens")
    
    # Default AI Model (general configuration)
    default_ai_model: str = Field(default="gpt-4o-mini", description="Default AI model for general use")
    
    # Anthropic API  
    ANTHROPIC_API_KEY: str = Field(description="Anthropic API key")
    ANTHROPIC_MODEL: str = Field(default="claude-3-sonnet-20240229", description="Default Anthropic model")
    
    # Perplexity API
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
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=100, description="Rate limit per minute")
    RATE_LIMIT_BURST: int = Field(default=200, description="Rate limit burst")
    
    # ================================
    # � COST MANAGEMENT
    # ================================
    
    # Max allowed cost per conversation in USD (test-friendly default)
    MAX_CONVERSATION_COST: float = Field(default=5.0, description="Maximum allowed cost per conversation (USD)")
    
    # ================================
    # �🔧 FEATURE FLAGS
    # ================================
    
    ENABLE_DOCS: bool = Field(default=True, description="Enable API documentation")
    ENABLE_VECTOR_SEARCH: bool = Field(default=True, description="Enable vector search")
    ENABLE_AI_AGENTS: bool = Field(default=True, description="Enable AI agents")
    ENABLE_BACKGROUND_TASKS: bool = Field(default=True, description="Enable background tasks")
    
    # ================================
    # 📂 PATHS & DIRECTORIES
    # ================================
    
    BASE_DIR: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent)
    SECRETS_DIR: Path = Field(default_factory=lambda: Path("secrets"))
    LOGS_DIR: Path = Field(default_factory=lambda: Path("logs"))
    UPLOADS_DIR: Path = Field(default_factory=lambda: Path("uploads"))
    
    # ================================
    # ✅ VALIDATORS
    # ================================
    
    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v):
        """Validate environment name"""
        allowed = ["development", "staging", "production", "test"] 
        if v not in allowed:
            raise ValueError(f"Environment must be one of: {allowed}")
        return v
    
    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level"""
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed:
            raise ValueError(f"Log level must be one of: {allowed}")
        return v.upper()
    
    @field_validator("JWT_ALGORITHM")
    @classmethod
    def validate_jwt_algorithm(cls, v):
        """Validate JWT algorithm"""
        if v != "RS256":
            raise ValueError("Only RS256 algorithm is supported for security")
        return v
    


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings"""
    return Settings()


# Global settings instance for easy importing
settings = get_settings()


def get_project_root() -> Path:
    """Get project root directory"""
    # __file__ = …/backend/src/core/config.py → parents[3] = repo root
    return Path(__file__).resolve().parents[3]


def ensure_directories(settings: Settings) -> None:
    """Ensure required directories exist"""
    directories = [
        settings.SECRETS_DIR,
        settings.LOGS_DIR, 
        settings.UPLOADS_DIR,
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
