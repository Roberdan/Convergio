"""
Feature Flags System - Complete implementation for staged rollout
Provides granular control over feature activation with user/group targeting.
"""

import json
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass, field
from enum import Enum
import random

import structlog

logger = structlog.get_logger()


class RolloutStrategy(Enum):
    """Feature rollout strategies"""
    OFF = "off"
    ON = "on"
    PERCENTAGE = "percentage"
    USER_WHITELIST = "user_whitelist"
    GROUP_BASED = "group_based"
    GRADUAL = "gradual"
    CANARY = "canary"
    A_B_TEST = "ab_test"


class FeatureFlagName(Enum):
    """All feature flags in the system"""
    # Core features
    RAG_IN_LOOP = "rag_in_loop"
    TRUE_STREAMING = "true_streaming"
    SPEAKER_POLICY = "speaker_policy"
    GRAPHFLOW = "graphflow"
    HITL = "hitl"
    COST_SAFETY = "cost_safety"
    
    # Advanced features
    OBSERVABILITY = "observability"
    MEMORY_PERSISTENCE = "memory_persistence"
    ADVANCED_ROUTING = "advanced_routing"
    WORKFLOW_TEMPLATES = "workflow_templates"
    
    # Experimental features
    MULTI_MODAL = "multi_modal"
    VOICE_INTERFACE = "voice_interface"
    AUTO_SCALING = "auto_scaling"
    PREDICTIVE_CACHING = "predictive_caching"


@dataclass
class FeatureFlagConfig:
    """Configuration for a feature flag"""
    name: FeatureFlagName
    enabled: bool
    strategy: RolloutStrategy
    description: str
    
    # Rollout configuration
    percentage: float = 0.0  # For percentage rollout
    whitelist_users: Set[str] = field(default_factory=set)
    whitelist_groups: Set[str] = field(default_factory=set)
    
    # Gradual rollout
    rollout_start: Optional[datetime] = None
    rollout_end: Optional[datetime] = None
    target_percentage: float = 100.0
    
    # A/B testing
    variant_weights: Dict[str, float] = field(default_factory=dict)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    updated_by: str = "system"
    
    # Dependencies
    depends_on: List[FeatureFlagName] = field(default_factory=list)
    conflicts_with: List[FeatureFlagName] = field(default_factory=list)
    
    # Monitoring
    track_usage: bool = True
    alert_on_error: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name.value,
            "enabled": self.enabled,
            "strategy": self.strategy.value,
            "description": self.description,
            "percentage": self.percentage,
            "whitelist_users": list(self.whitelist_users),
            "whitelist_groups": list(self.whitelist_groups),
            "rollout_start": self.rollout_start.isoformat() if self.rollout_start else None,
            "rollout_end": self.rollout_end.isoformat() if self.rollout_end else None,
            "target_percentage": self.target_percentage,
            "variant_weights": self.variant_weights,
            "depends_on": [d.value for d in self.depends_on],
            "conflicts_with": [c.value for c in self.conflicts_with],
            "track_usage": self.track_usage,
            "alert_on_error": self.alert_on_error,
            "updated_at": self.updated_at.isoformat(),
            "updated_by": self.updated_by
        }


class FeatureFlagManager:
    """Centralized feature flag management"""
    
    def __init__(self):
        self.flags: Dict[FeatureFlagName, FeatureFlagConfig] = {}
        self.usage_stats: Dict[str, Dict[str, int]] = {}
        self._initialize_default_flags()
        
    def _initialize_default_flags(self):
        """Initialize default feature flags"""
        
        # RAG Feature
        self.flags[FeatureFlagName.RAG_IN_LOOP] = FeatureFlagConfig(
            name=FeatureFlagName.RAG_IN_LOOP,
            enabled=True,
            strategy=RolloutStrategy.ON,
            description="Enable RAG with memory integration for context-aware responses"
        )
        
        # Streaming Feature
        self.flags[FeatureFlagName.TRUE_STREAMING] = FeatureFlagConfig(
            name=FeatureFlagName.TRUE_STREAMING,
            enabled=True,
            strategy=RolloutStrategy.PERCENTAGE,
            description="Enable native AutoGen streaming",
            percentage=100.0
        )
        
        # Speaker Policy
        self.flags[FeatureFlagName.SPEAKER_POLICY] = FeatureFlagConfig(
            name=FeatureFlagName.SPEAKER_POLICY,
            enabled=True,
            strategy=RolloutStrategy.ON,
            description="Enable intelligent speaker selection policy"
        )
        
        # GraphFlow Workflows
        self.flags[FeatureFlagName.GRAPHFLOW] = FeatureFlagConfig(
            name=FeatureFlagName.GRAPHFLOW,
            enabled=True,
            strategy=RolloutStrategy.GROUP_BASED,
            description="Enable GraphFlow workflow execution",
            whitelist_groups={"enterprise", "premium"}
        )
        
        # HITL Approvals
        self.flags[FeatureFlagName.HITL] = FeatureFlagConfig(
            name=FeatureFlagName.HITL,
            enabled=False,
            strategy=RolloutStrategy.USER_WHITELIST,
            description="Enable human-in-the-loop approvals",
            whitelist_users={"admin", "supervisor"},
            depends_on=[FeatureFlagName.COST_SAFETY]
        )
        
        # Cost Safety
        self.flags[FeatureFlagName.COST_SAFETY] = FeatureFlagConfig(
            name=FeatureFlagName.COST_SAFETY,
            enabled=True,
            strategy=RolloutStrategy.ON,
            description="Enable cost tracking and budget enforcement"
        )
        
        # Observability
        self.flags[FeatureFlagName.OBSERVABILITY] = FeatureFlagConfig(
            name=FeatureFlagName.OBSERVABILITY,
            enabled=True,
            strategy=RolloutStrategy.GRADUAL,
            description="Enable comprehensive observability",
            rollout_start=datetime.utcnow(),
            rollout_end=datetime.utcnow().replace(hour=23, minute=59),
            target_percentage=100.0
        )
        
        # Experimental Features
        self.flags[FeatureFlagName.MULTI_MODAL] = FeatureFlagConfig(
            name=FeatureFlagName.MULTI_MODAL,
            enabled=False,
            strategy=RolloutStrategy.CANARY,
            description="Enable multi-modal input/output (images, audio)",
            percentage=5.0,
            whitelist_groups={"beta_testers"}
        )
        
        logger.info(f"Initialized {len(self.flags)} feature flags")
    
    def is_enabled(
        self,
        flag_name: FeatureFlagName,
        user_id: Optional[str] = None,
        group_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Check if a feature flag is enabled for a user/group"""
        
        if flag_name not in self.flags:
            logger.warning(f"Unknown feature flag: {flag_name}")
            return False
        
        flag = self.flags[flag_name]
        
        # Track usage
        self._track_usage(flag_name, user_id, "check")
        
        # Check basic enabled state
        if not flag.enabled:
            return False
        
        # Check dependencies
        if not self._check_dependencies(flag):
            return False
        
        # Check conflicts
        if self._has_conflicts(flag):
            return False
        
        # Apply rollout strategy
        result = self._apply_strategy(flag, user_id, group_id, context)
        
        # Track result
        self._track_usage(flag_name, user_id, "enabled" if result else "disabled")
        
        return result
    
    def _apply_strategy(
        self,
        flag: FeatureFlagConfig,
        user_id: Optional[str],
        group_id: Optional[str],
        context: Optional[Dict[str, Any]]
    ) -> bool:
        """Apply rollout strategy to determine if feature is enabled"""
        
        strategy = flag.strategy
        
        if strategy == RolloutStrategy.OFF:
            return False
        
        if strategy == RolloutStrategy.ON:
            return True
        
        if strategy == RolloutStrategy.PERCENTAGE:
            return self._check_percentage(flag.percentage, user_id)
        
        if strategy == RolloutStrategy.USER_WHITELIST:
            return user_id in flag.whitelist_users if user_id else False
        
        if strategy == RolloutStrategy.GROUP_BASED:
            return group_id in flag.whitelist_groups if group_id else False
        
        if strategy == RolloutStrategy.GRADUAL:
            return self._check_gradual_rollout(flag, user_id)
        
        if strategy == RolloutStrategy.CANARY:
            return self._check_canary(flag, user_id, group_id)
        
        if strategy == RolloutStrategy.A_B_TEST:
            return self._check_ab_test(flag, user_id, context)
        
        return False
    
    def _check_percentage(self, percentage: float, user_id: Optional[str]) -> bool:
        """Check if user falls within percentage rollout"""
        if not user_id:
            return random.random() * 100 < percentage
        
        # Consistent hashing for deterministic results
        hash_value = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
        return (hash_value % 100) < percentage
    
    def _check_gradual_rollout(self, flag: FeatureFlagConfig, user_id: Optional[str]) -> bool:
        """Check gradual rollout based on time"""
        if not flag.rollout_start or not flag.rollout_end:
            return True
        
        now = datetime.utcnow()
        
        if now < flag.rollout_start:
            return False
        
        if now > flag.rollout_end:
            return self._check_percentage(flag.target_percentage, user_id)
        
        # Calculate current percentage based on time
        total_duration = (flag.rollout_end - flag.rollout_start).total_seconds()
        elapsed = (now - flag.rollout_start).total_seconds()
        current_percentage = (elapsed / total_duration) * flag.target_percentage
        
        return self._check_percentage(current_percentage, user_id)
    
    def _check_canary(
        self,
        flag: FeatureFlagConfig,
        user_id: Optional[str],
        group_id: Optional[str]
    ) -> bool:
        """Check canary deployment"""
        # First check if user/group is in whitelist
        if user_id and user_id in flag.whitelist_users:
            return True
        if group_id and group_id in flag.whitelist_groups:
            return True
        
        # Then apply percentage for canary
        return self._check_percentage(flag.percentage, user_id)
    
    def _check_ab_test(
        self,
        flag: FeatureFlagConfig,
        user_id: Optional[str],
        context: Optional[Dict[str, Any]]
    ) -> bool:
        """Check A/B test variant assignment"""
        if not flag.variant_weights:
            return False
        
        if not user_id:
            return False
        
        # Get user's variant
        variant = self.get_variant(flag.name, user_id)
        
        # Check if variant is enabled
        return variant != "control"
    
    def get_variant(self, flag_name: FeatureFlagName, user_id: str) -> str:
        """Get A/B test variant for user"""
        flag = self.flags.get(flag_name)
        if not flag or not flag.variant_weights:
            return "control"
        
        # Consistent hashing for variant assignment
        hash_value = int(hashlib.md5(f"{flag_name.value}:{user_id}".encode()).hexdigest(), 16)
        percentage = hash_value % 100
        
        cumulative = 0
        for variant, weight in flag.variant_weights.items():
            cumulative += weight
            if percentage < cumulative:
                return variant
        
        return "control"
    
    def _check_dependencies(self, flag: FeatureFlagConfig) -> bool:
        """Check if all dependencies are enabled"""
        for dep in flag.depends_on:
            if dep not in self.flags or not self.flags[dep].enabled:
                logger.debug(f"Dependency {dep.value} not enabled for {flag.name.value}")
                return False
        return True
    
    def _has_conflicts(self, flag: FeatureFlagConfig) -> bool:
        """Check if any conflicting flags are enabled"""
        for conflict in flag.conflicts_with:
            if conflict in self.flags and self.flags[conflict].enabled:
                logger.debug(f"Conflict with {conflict.value} for {flag.name.value}")
                return True
        return False
    
    def _track_usage(self, flag_name: FeatureFlagName, user_id: Optional[str], action: str):
        """Track feature flag usage"""
        flag_key = flag_name.value
        if flag_key not in self.usage_stats:
            self.usage_stats[flag_key] = {}
        
        stat_key = f"{action}:{user_id or 'anonymous'}"
        self.usage_stats[flag_key][stat_key] = self.usage_stats[flag_key].get(stat_key, 0) + 1
    
    def update_flag(
        self,
        flag_name: FeatureFlagName,
        enabled: Optional[bool] = None,
        strategy: Optional[RolloutStrategy] = None,
        percentage: Optional[float] = None,
        whitelist_users: Optional[Set[str]] = None,
        whitelist_groups: Optional[Set[str]] = None,
        updated_by: str = "system"
    ):
        """Update feature flag configuration"""
        if flag_name not in self.flags:
            raise ValueError(f"Unknown feature flag: {flag_name}")
        
        flag = self.flags[flag_name]
        
        if enabled is not None:
            flag.enabled = enabled
        if strategy is not None:
            flag.strategy = strategy
        if percentage is not None:
            flag.percentage = percentage
        if whitelist_users is not None:
            flag.whitelist_users = whitelist_users
        if whitelist_groups is not None:
            flag.whitelist_groups = whitelist_groups
        
        flag.updated_at = datetime.utcnow()
        flag.updated_by = updated_by
        
        logger.info(
            f"Updated feature flag {flag_name.value}",
            enabled=flag.enabled,
            strategy=flag.strategy.value,
            updated_by=updated_by
        )
    
    def get_all_flags(self) -> Dict[str, Dict[str, Any]]:
        """Get all feature flags and their configurations"""
        return {
            flag_name.value: flag.to_dict()
            for flag_name, flag in self.flags.items()
        }
    
    def get_enabled_features(
        self,
        user_id: Optional[str] = None,
        group_id: Optional[str] = None
    ) -> List[str]:
        """Get list of enabled features for a user/group"""
        enabled = []
        for flag_name in FeatureFlagName:
            if self.is_enabled(flag_name, user_id, group_id):
                enabled.append(flag_name.value)
        return enabled
    
    def get_usage_stats(self) -> Dict[str, Dict[str, int]]:
        """Get usage statistics for all flags"""
        return self.usage_stats
    
    def reset_usage_stats(self):
        """Reset usage statistics"""
        self.usage_stats = {}
        logger.info("Reset feature flag usage statistics")
    
    def export_config(self) -> str:
        """Export feature flag configuration as JSON"""
        config = {
            "flags": self.get_all_flags(),
            "exported_at": datetime.utcnow().isoformat(),
            "version": "1.0.0"
        }
        return json.dumps(config, indent=2)
    
    def import_config(self, config_json: str):
        """Import feature flag configuration from JSON"""
        config = json.loads(config_json)
        
        for flag_name_str, flag_data in config.get("flags", {}).items():
            try:
                flag_name = FeatureFlagName(flag_name_str)
                if flag_name in self.flags:
                    self.update_flag(
                        flag_name,
                        enabled=flag_data.get("enabled"),
                        strategy=RolloutStrategy(flag_data.get("strategy")),
                        percentage=flag_data.get("percentage"),
                        whitelist_users=set(flag_data.get("whitelist_users", [])),
                        whitelist_groups=set(flag_data.get("whitelist_groups", [])),
                        updated_by="import"
                    )
            except Exception as e:
                logger.error(f"Failed to import flag {flag_name_str}: {e}")
        
        logger.info("Imported feature flag configuration")


# Global feature flag manager
_feature_flags: Optional[FeatureFlagManager] = None


def initialize_feature_flags() -> FeatureFlagManager:
    """Initialize global feature flag manager"""
    global _feature_flags
    _feature_flags = FeatureFlagManager()
    return _feature_flags


def get_feature_flags() -> FeatureFlagManager:
    """Get global feature flag manager"""
    if _feature_flags is None:
        return initialize_feature_flags()
    return _feature_flags


def is_feature_enabled(
    flag_name: FeatureFlagName,
    user_id: Optional[str] = None,
    group_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> bool:
    """Check if a feature is enabled"""
    manager = get_feature_flags()
    return manager.is_enabled(flag_name, user_id, group_id, context)


def get_variant(flag_name: FeatureFlagName, user_id: str) -> str:
    """Get A/B test variant for user"""
    manager = get_feature_flags()
    return manager.get_variant(flag_name, user_id)


# Decorators for feature flag gating
def feature_flag(flag_name: FeatureFlagName, fallback=None):
    """Decorator to gate functions with feature flags"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Extract user_id from kwargs or context
            user_id = kwargs.get("user_id")
            group_id = kwargs.get("group_id")
            
            if is_feature_enabled(flag_name, user_id, group_id):
                return func(*args, **kwargs)
            else:
                logger.debug(f"Feature {flag_name.value} disabled, using fallback")
                if fallback is not None:
                    return fallback(*args, **kwargs)
                else:
                    raise RuntimeError(f"Feature {flag_name.value} is not enabled")
        
        return wrapper
    return decorator


__all__ = [
    "FeatureFlagName",
    "FeatureFlagConfig",
    "FeatureFlagManager",
    "RolloutStrategy",
    "initialize_feature_flags",
    "get_feature_flags",
    "is_feature_enabled",
    "get_variant",
    "feature_flag"
]