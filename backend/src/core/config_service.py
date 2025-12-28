"""
Centralized Configuration Service
Single source of truth for all configuration with hot-reload support
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import hashlib
from dataclasses import dataclass
from enum import Enum
import asyncio
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

import structlog

logger = structlog.get_logger()


class ConfigType(Enum):
    """Configuration types"""
    AGENTS = "agents"
    MODELS = "models"
    FEATURES = "features"
    SECURITY = "security"
    DATABASE = "database"
    REDIS = "redis"
    API_KEYS = "api_keys"
    LIMITS = "limits"


@dataclass
class ModelConfig:
    """Model configuration"""
    provider: str
    model_id: str
    api_key_env: str
    base_url: Optional[str] = None
    max_tokens: int = 1000
    temperature: float = 0.7
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    timeout: int = 30
    retry_attempts: int = 3
    cost_per_1k_tokens: float = 0.0


@dataclass
class AgentConfig:
    """Agent configuration"""
    id: str
    name: str
    description: str
    model: str
    system_message: str
    capabilities: List[str]
    tools: List[str]
    max_turns: int = 10
    temperature: float = 0.7
    enabled: bool = True
    priority: int = 5


@dataclass
class FeatureFlag:
    """Feature flag configuration"""
    name: str
    enabled: bool
    description: str
    rollout_percentage: float = 100.0
    conditions: Optional[Dict[str, Any]] = None
    expires_at: Optional[datetime] = None


class ConfigurationService:
    """
    Centralized configuration management with hot-reload support.
    """
    
    def __init__(self, config_dir: Optional[str] = None):
        self.config_dir = Path(config_dir or os.getenv("CONFIG_DIR", "./config"))
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self._config_cache: Dict[str, Any] = {}
        self._file_hashes: Dict[str, str] = {}
        self._observers: List[Any] = []
        self._reload_callbacks: List[Any] = []
        
        # Initialize configuration
        self._load_all_configs()
        
        # Start file watcher for hot-reload
        self._start_file_watcher()
        
        logger.info(f"✅ Configuration service initialized from {self.config_dir}")
    
    def _load_all_configs(self):
        """Load all configuration files"""
        
        # Load YAML configs
        for yaml_file in self.config_dir.glob("*.yaml"):
            self._load_yaml_config(yaml_file)
        
        for yaml_file in self.config_dir.glob("*.yml"):
            self._load_yaml_config(yaml_file)
        
        # Load JSON configs
        for json_file in self.config_dir.glob("*.json"):
            self._load_json_config(json_file)
        
        # Load environment-specific configs
        env = os.getenv("ENVIRONMENT", "development")
        env_config = self.config_dir / f"{env}.yaml"
        if env_config.exists():
            self._load_yaml_config(env_config)
        
        # Load from environment variables
        self._load_env_configs()
    
    def _load_yaml_config(self, file_path: Path):
        """Load YAML configuration file"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                config = yaml.safe_load(content)
                
                # Store with file name as key
                key = file_path.stem
                self._config_cache[key] = config
                
                # Store file hash for change detection
                self._file_hashes[str(file_path)] = hashlib.md5(content.encode()).hexdigest()
                
                logger.info(f"📄 Loaded config: {key}")
                
        except Exception as e:
            logger.error(f"Failed to load {file_path}: {e}")
    
    def _load_json_config(self, file_path: Path):
        """Load JSON configuration file"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                config = json.loads(content)
                
                key = file_path.stem
                self._config_cache[key] = config
                self._file_hashes[str(file_path)] = hashlib.md5(content.encode()).hexdigest()
                
                logger.info(f"📄 Loaded config: {key}")
                
        except Exception as e:
            logger.error(f"Failed to load {file_path}: {e}")
    
    def _load_env_configs(self):
        """Load configuration from environment variables"""
        
        # API Keys
        api_keys = {}
        for key, value in os.environ.items():
            if key.endswith("_API_KEY"):
                provider = key.replace("_API_KEY", "").lower()
                api_keys[provider] = value
        
        if api_keys:
            self._config_cache["api_keys"] = api_keys
        
        # Database configuration
        if os.getenv("DATABASE_URL"):
            self._config_cache["database"] = {
                "url": os.getenv("DATABASE_URL"),
                "pool_size": int(os.getenv("DB_POOL_SIZE", "20")),
                "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "40")),
                "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", "30"))
            }
        
        # Redis configuration
        if os.getenv("REDIS_URL"):
            self._config_cache["redis"] = {
                "url": os.getenv("REDIS_URL"),
                "max_connections": int(os.getenv("REDIS_MAX_CONNECTIONS", "50")),
                "decode_responses": True
            }
    
    def _start_file_watcher(self):
        """Start watching configuration files for changes"""
        
        class ConfigFileHandler(FileSystemEventHandler):
            def __init__(self, service):
                self.service = service
            
            def on_modified(self, event):
                if not event.is_directory:
                    file_path = Path(event.src_path)
                    if file_path.suffix in ['.yaml', '.yml', '.json']:
                        self.service._handle_config_change(file_path)
        
        try:
            event_handler = ConfigFileHandler(self)
            observer = Observer()
            observer.schedule(event_handler, str(self.config_dir), recursive=False)
            observer.start()
            self._observers.append(observer)
            
            logger.info("🔄 Hot-reload enabled for configuration files")
            
        except Exception as e:
            logger.warning(f"Could not enable hot-reload: {e}")
    
    def _handle_config_change(self, file_path: Path):
        """Handle configuration file change"""
        
        # Check if file content actually changed
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                new_hash = hashlib.md5(content.encode()).hexdigest()
                
                old_hash = self._file_hashes.get(str(file_path))
                if old_hash == new_hash:
                    return  # No actual change
                
                logger.info(f"🔄 Config file changed: {file_path.name}")
                
                # Reload the specific config
                if file_path.suffix in ['.yaml', '.yml']:
                    self._load_yaml_config(file_path)
                elif file_path.suffix == '.json':
                    self._load_json_config(file_path)
                
                # Trigger reload callbacks
                asyncio.create_task(self._trigger_reload_callbacks(file_path.stem))
                
        except Exception as e:
            logger.error(f"Error handling config change: {e}")
    
    async def _trigger_reload_callbacks(self, config_key: str):
        """Trigger callbacks for configuration reload"""
        for callback in self._reload_callbacks:
            try:
                await callback(config_key, self._config_cache.get(config_key))
            except Exception as e:
                logger.error(f"Reload callback failed: {e}")
    
    def register_reload_callback(self, callback):
        """Register a callback for configuration reloads"""
        self._reload_callbacks.append(callback)
    
    # ==================== Configuration Access Methods ====================
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key"""
        
        # Support nested keys with dot notation
        if '.' in key:
            parts = key.split('.')
            value = self._config_cache
            
            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part)
                    if value is None:
                        return default
                else:
                    return default
            
            return value
        
        return self._config_cache.get(key, default)
    
    def get_model_config(self, model_id: str) -> Optional[ModelConfig]:
        """Get model configuration"""
        models = self.get("models", {})
        
        if model_id in models:
            return ModelConfig(**models[model_id])
        
        # Check for default model
        default = models.get("default")
        if default:
            config = ModelConfig(**default)
            config.model_id = model_id
            return config
        
        return None
    
    def get_agent_config(self, agent_id: str) -> Optional[AgentConfig]:
        """Get agent configuration"""
        agents = self.get("agents", {})
        
        if agent_id in agents:
            return AgentConfig(**agents[agent_id])
        
        return None
    
    def get_all_agents(self) -> List[AgentConfig]:
        """Get all agent configurations"""
        agents = self.get("agents", {})
        
        return [
            AgentConfig(**config) 
            for config in agents.values()
            if config.get("enabled", True)
        ]
    
    def get_feature_flag(self, flag_name: str) -> FeatureFlag:
        """Get feature flag configuration"""
        features = self.get("features", {})
        
        if flag_name in features:
            return FeatureFlag(**features[flag_name])
        
        # Default to disabled
        return FeatureFlag(
            name=flag_name,
            enabled=False,
            description="Unknown feature flag"
        )
    
    def is_feature_enabled(
        self,
        flag_name: str,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Check if a feature is enabled"""
        flag = self.get_feature_flag(flag_name)
        
        if not flag.enabled:
            return False
        
        # Check expiration
        if flag.expires_at and datetime.now() > flag.expires_at:
            return False
        
        # Check rollout percentage
        if flag.rollout_percentage < 100:
            # Use consistent hash for user
            if context and "user_id" in context:
                user_hash = int(hashlib.md5(
                    context["user_id"].encode()
                ).hexdigest()[:8], 16)
                
                if (user_hash % 100) >= flag.rollout_percentage:
                    return False
        
        # Check conditions
        if flag.conditions and context:
            for key, expected_value in flag.conditions.items():
                if context.get(key) != expected_value:
                    return False
        
        return True
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """Get API key for a provider"""
        api_keys = self.get("api_keys", {})
        
        # Check direct key
        if provider in api_keys:
            return api_keys[provider]
        
        # Check environment variable
        env_key = f"{provider.upper()}_API_KEY"
        return os.getenv(env_key)
    
    def get_limits(self) -> Dict[str, Any]:
        """Get rate limits and quotas"""
        return self.get("limits", {
            "max_tokens_per_request": 4000,
            "max_requests_per_minute": 60,
            "max_embeddings_per_batch": 100,
            "max_conversation_length": 100,
            "max_agents_per_conversation": 5,
            "cache_ttl_seconds": 3600
        })
    
    def generate_agent_capabilities(self) -> Dict[str, List[str]]:
        """Generate agent capabilities from configuration"""
        capabilities = {}
        
        for agent in self.get_all_agents():
            capabilities[agent.id] = agent.capabilities
        
        return capabilities
    
    def to_dict(self) -> Dict[str, Any]:
        """Export all configuration as dictionary"""
        return self._config_cache.copy()
    
    def save_config(self, key: str, config: Dict[str, Any], format: str = "yaml"):
        """Save configuration to file"""
        
        file_path = self.config_dir / f"{key}.{format}"
        
        try:
            if format == "yaml":
                with open(file_path, 'w') as f:
                    yaml.dump(config, f, default_flow_style=False)
            elif format == "json":
                with open(file_path, 'w') as f:
                    json.dump(config, f, indent=2)
            
            # Update cache
            self._config_cache[key] = config
            
            logger.info(f"✅ Saved config: {key}")
            
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            raise
    
    def cleanup(self):
        """Cleanup resources"""
        for observer in self._observers:
            observer.stop()
            observer.join()


# Singleton instance
_config_service = None


def get_config_service(config_dir: Optional[str] = None) -> ConfigurationService:
    """Get singleton configuration service"""
    global _config_service
    if _config_service is None:
        _config_service = ConfigurationService(config_dir)
    return _config_service


# Convenience functions
def get_config(key: str, default: Any = None) -> Any:
    """Get configuration value"""
    service = get_config_service()
    return service.get(key, default)


def is_feature_enabled(flag_name: str, context: Optional[Dict[str, Any]] = None) -> bool:
    """Check if feature is enabled"""
    service = get_config_service()
    return service.is_feature_enabled(flag_name, context)