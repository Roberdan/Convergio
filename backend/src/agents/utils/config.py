"""
CONVERGIO 2029 - CONFIGURATION MANAGEMENT
Environment-based configuration with validation
"""

import os
import json
import subprocess
from functools import lru_cache
from typing import List
from pathlib import Path

from pydantic_settings import BaseSettings
from pydantic import Field, field_validator, model_validator


def get_version_info():
    """Get version information from VERSION file and git."""
    try:
        # Find the VERSION file in project root
        current = Path(__file__).resolve()
        while current != current.parent:
            version_file = current / "VERSION"
            if version_file.exists():
                version = version_file.read_text().strip()
                break
            current = current.parent
        else:
            version = "1.0.0"
        
        # Get build number from git
        try:
            commit_count = subprocess.check_output(
                ["git", "rev-list", "--count", "HEAD"],
                stderr=subprocess.DEVNULL,
                cwd=current
            ).decode().strip()
            
            commit_hash = subprocess.check_output(
                ["git", "rev-parse", "--short", "HEAD"],
                stderr=subprocess.DEVNULL,
                cwd=current
            ).decode().strip()
            
            build_number = f"{commit_count}-{commit_hash}"
        except:
            build_number = "dev-build"
            
        return version, build_number
    except:
        return "1.0.0", "unknown"


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application - now reads from VERSION file
    app_version: str = Field(default_factory=lambda: get_version_info()[0])
    build_number: str = Field(default_factory=lambda: get_version_info()[1])
    environment: str = Field(default="development", env="ENVIRONMENT")
    
    # Server - NO FALLBACK
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8001, env="AGENTS_PORT")
    backend_url: str = Field(..., env="BACKEND_URL")
    
    # Database Configuration (costruito dinamicamente)
    db_host: str = Field(..., env="DB_HOST")
    db_port: int = Field(..., env="DB_PORT")
    postgres_user: str = Field(..., env="POSTGRES_USER")
    postgres_password: str = Field(..., env="POSTGRES_PASSWORD")
    postgres_db: str = Field(..., env="POSTGRES_DB")
    database_url: str = ""

    # Redis Configuration (costruito dinamicamente)
    redis_host: str = Field(..., env="REDIS_HOST")
    redis_port: int = Field(..., env="REDIS_PORT")
    redis_password: str = Field(default="", env="REDIS_PASSWORD")
    redis_db: int = Field(default=0, env="REDIS_DB")
    redis_url: str = ""

    @model_validator(mode='after')
    def build_connection_strings(self) -> 'Settings':
        """Costruisce le stringhe di connessione dopo il caricamento delle variabili."""
        required_vars = {
            'POSTGRES_USER': self.postgres_user,
            'POSTGRES_PASSWORD': self.postgres_password,
            'POSTGRES_DB': self.postgres_db,
            'DB_HOST': self.db_host,
            'REDIS_HOST': self.redis_host,
            'JWT_SECRET': self.jwt_secret,
            'OPENAI_API_KEY': self.openai_api_key
        }
        missing_vars = [key for key, value in required_vars.items() if not value]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {missing_vars}")

        self.database_url = f"postgresql://{self.postgres_user}:{self.postgres_password}@"
        self.database_url += f"{self.db_host}:{self.db_port}/{self.postgres_db}"

        redis_auth = f":{self.redis_password}@" if self.redis_password else ""
        self.redis_url = f"redis://{redis_auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return self
    
    # AI Services
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    anthropic_api_key: str = Field(default="", env="ANTHROPIC_API_KEY")
    perplexity_api_key: str = Field(default="", env="PERPLEXITY_API_KEY")
    
    # AutoGen Configuration
    autogen_max_turns: int = Field(default=10, env="AUTOGEN_MAX_TURNS")
    autogen_timeout_seconds: int = Field(default=300, env="AUTOGEN_TIMEOUT_SECONDS")
    autogen_cost_limit_usd: float = Field(default=50.0, env="AUTOGEN_COST_LIMIT_USD")
    autogen_redis_state_ttl: int = Field(default=3600, env="AUTOGEN_REDIS_STATE_TTL")
    default_ai_model: str = Field(default="gpt-4o-mini", env="DEFAULT_AI_MODEL")
    
    # Security
    jwt_secret: str = Field(..., env="JWT_SECRET")
    jwt_algorithm: str = Field(default="RS256", env="JWT_ALGORITHM")
    
    # CORS and Security (environment-aware)
    cors_origins: str = Field(
        default="http://localhost:4000,http://localhost:3000,http://localhost:9001",
        env="CORS_ALLOWED_ORIGINS"
    )
    trusted_hosts: str = Field(
        default="localhost,127.0.0.1,backend,frontend",
        env="TRUSTED_HOSTS"
    )
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convert CORS origins string to list"""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    @property 
    def trusted_hosts_list(self) -> List[str]:
        """Convert trusted hosts string to list"""
        return [host.strip() for host in self.trusted_hosts.split(",")]
    
    # Monitoring
    otel_exporter_otlp_endpoint: str = Field(env="OTEL_EXPORTER_OTLP_ENDPOINT")
    otel_service_name: str = Field(default="convergio-agents2029", env="OTEL_SERVICE_NAME")
    prometheus_endpoint: str = Field(env="PROMETHEUS_ENDPOINT")
    metrics_enabled: bool = Field(default=True, env="METRICS_ENABLED")
    tracing_sample_rate: float = Field(default=0.1, env="TRACING_SAMPLE_RATE")
    
    # Rate Limiting
    rate_limit_window_ms: int = Field(default=900000, env="RATE_LIMIT_WINDOW_MS")
    rate_limit_max_requests: int = Field(default=100, env="RATE_LIMIT_MAX_REQUESTS")
    
    # Development
    debug_mode: bool = Field(default=False, env="DEBUG_MODE")
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Local AI Models (Ollama/Qwen) - Optional fields with defaults
    ollama_host: str = Field(default="", env="OLLAMA_HOST")
    ollama_api_base: str = Field(default="", env="OLLAMA_API_BASE")
    ollama_backend: str = Field(default="mlx", env="OLLAMA_BACKEND")
    ollama_max_context: int = Field(default=8192, env="OLLAMA_MAX_CONTEXT")
    qwen_api_base: str = Field(default="", env="QWEN_API_BASE")
    default_model: str = Field(default="qwen3:30b", env="DEFAULT_MODEL")
    qwen_model: str = Field(default="qwen3:30b", env="QWEN_MODEL")
    openai_api_base: str = Field(default="", env="OPENAI_API_BASE")
    openai_model: str = Field(default="qwen3:30b", env="OPENAI_MODEL")
    omp_num_threads: int = Field(default=10, env="OMP_NUM_THREADS")
    
    
    class Config:
        # Environment variables loaded manually from root .env
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env


def load_env_from_root():
    """Load environment variables from the root .env file."""
    import os
    from pathlib import Path
    
    # Find the .env file in project root
    current = Path.cwd()
    
    while current != current.parent:
        env_file = current / ".env"
        if env_file.exists():
            break
        current = current.parent
    else:
        # Fallback: try relative to agents directory (4 levels up from this file)
        agents_dir = Path(__file__).parent.parent.parent.parent
        env_file = agents_dir / ".env"
        if not env_file.exists():
            raise FileNotFoundError(f"Could not find .env file in project root")
    
    # Load .env file manually - force overwrite any existing env vars
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                # Force overwrite environment variables from .env file
                os.environ[key] = value

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    # Load environment variables from root .env
    load_env_from_root()
    return Settings()