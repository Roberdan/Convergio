"""
Framework Feature Flag (I3)
Controls which agent framework to use with rollback support.
"""

import os
from typing import Optional, Dict, Any
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

import structlog

from .framework_adapter import (
    FrameworkAdapter,
    FrameworkType,
    MockFrameworkAdapter,
    create_adapter,
)

logger = structlog.get_logger()


class FrameworkSelection(Enum):
    """Framework selection strategy."""
    AGENT_FRAMEWORK = "agent_framework"  # Use AF only
    AUTOGEN = "autogen"  # Use AutoGen only
    AGENT_FRAMEWORK_WITH_FALLBACK = "agent_framework_with_fallback"  # AF with AutoGen fallback
    AUTOGEN_WITH_MIGRATION = "autogen_with_migration"  # AutoGen migrating to AF
    MOCK = "mock"  # Testing mode


@dataclass
class FrameworkConfig:
    """Configuration for framework selection."""
    selection: FrameworkSelection = FrameworkSelection.AGENT_FRAMEWORK_WITH_FALLBACK
    agent_framework_percentage: int = 100  # % of traffic to send to AF
    enable_fallback: bool = True
    fallback_on_error: bool = True
    log_framework_usage: bool = True
    force_framework: Optional[str] = None  # Override for testing


@dataclass
class FrameworkUsageStats:
    """Track framework usage for monitoring."""
    agent_framework_calls: int = 0
    autogen_calls: int = 0
    mock_calls: int = 0
    fallback_triggered: int = 0
    errors: int = 0
    last_updated: datetime = None

    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_framework_calls": self.agent_framework_calls,
            "autogen_calls": self.autogen_calls,
            "mock_calls": self.mock_calls,
            "fallback_triggered": self.fallback_triggered,
            "errors": self.errors,
            "total_calls": self.agent_framework_calls + self.autogen_calls + self.mock_calls,
            "last_updated": self.last_updated.isoformat()
        }


class FrameworkFeatureFlag:
    """Feature flag controller for framework selection.

    Controls which framework to use based on configuration,
    traffic percentage, and fallback settings.
    """

    def __init__(self, config: Optional[FrameworkConfig] = None):
        """Initialize feature flag.

        Args:
            config: Framework configuration
        """
        self.config = config or self._load_config_from_env()
        self.stats = FrameworkUsageStats()
        self._primary_adapter: Optional[FrameworkAdapter] = None
        self._fallback_adapter: Optional[FrameworkAdapter] = None
        self._call_count = 0

        logger.info(
            "FrameworkFeatureFlag initialized",
            selection=self.config.selection.value,
            percentage=self.config.agent_framework_percentage,
            fallback_enabled=self.config.enable_fallback
        )

    def _load_config_from_env(self) -> FrameworkConfig:
        """Load configuration from environment variables."""
        selection_str = os.environ.get(
            "AGENT_FRAMEWORK_SELECTION",
            "agent_framework_with_fallback"
        )

        try:
            selection = FrameworkSelection(selection_str)
        except ValueError:
            selection = FrameworkSelection.AGENT_FRAMEWORK_WITH_FALLBACK

        return FrameworkConfig(
            selection=selection,
            agent_framework_percentage=int(
                os.environ.get("AGENT_FRAMEWORK_PERCENTAGE", "100")
            ),
            enable_fallback=os.environ.get("AGENT_FRAMEWORK_FALLBACK", "true").lower() == "true",
            fallback_on_error=os.environ.get("AGENT_FRAMEWORK_FALLBACK_ON_ERROR", "true").lower() == "true",
            log_framework_usage=os.environ.get("AGENT_FRAMEWORK_LOG_USAGE", "true").lower() == "true",
            force_framework=os.environ.get("FORCE_FRAMEWORK", None)
        )

    def get_framework_type(self) -> FrameworkType:
        """Determine which framework to use for current request.

        Uses configuration, percentage rollout, and availability
        to select the appropriate framework.

        Returns:
            FrameworkType to use
        """
        # Check for forced override
        if self.config.force_framework:
            forced = self.config.force_framework.lower()
            if forced == "mock":
                return FrameworkType.MOCK
            elif forced == "autogen":
                return FrameworkType.AUTOGEN
            elif forced == "agent_framework":
                return FrameworkType.AGENT_FRAMEWORK

        # Based on selection strategy
        if self.config.selection == FrameworkSelection.MOCK:
            return FrameworkType.MOCK

        if self.config.selection == FrameworkSelection.AUTOGEN:
            return FrameworkType.AUTOGEN

        if self.config.selection == FrameworkSelection.AGENT_FRAMEWORK:
            return FrameworkType.AGENT_FRAMEWORK

        # Percentage-based rollout
        if self.config.selection in (
            FrameworkSelection.AGENT_FRAMEWORK_WITH_FALLBACK,
            FrameworkSelection.AUTOGEN_WITH_MIGRATION
        ):
            self._call_count += 1
            use_af = (self._call_count % 100) < self.config.agent_framework_percentage

            if self.config.selection == FrameworkSelection.AGENT_FRAMEWORK_WITH_FALLBACK:
                return FrameworkType.AGENT_FRAMEWORK if use_af else FrameworkType.AUTOGEN
            else:
                return FrameworkType.AUTOGEN if not use_af else FrameworkType.AGENT_FRAMEWORK

        return FrameworkType.MOCK

    def get_adapter(self, name: str = "default") -> FrameworkAdapter:
        """Get adapter based on current feature flag state.

        Args:
            name: Adapter name

        Returns:
            FrameworkAdapter instance
        """
        framework = self.get_framework_type()
        return create_adapter(framework, name)

    async def get_adapter_with_fallback(
        self,
        agents_dir: str,
        model_client: Optional[Any] = None,
        **kwargs
    ) -> FrameworkAdapter:
        """Get adapter with fallback support.

        Tries primary framework first, falls back if initialization fails.

        Args:
            agents_dir: Agent definitions directory
            model_client: Model client
            **kwargs: Additional configuration

        Returns:
            Initialized FrameworkAdapter
        """
        primary_type = self.get_framework_type()

        # Create and initialize primary adapter
        self._primary_adapter = create_adapter(primary_type, "primary")

        try:
            success = await self._primary_adapter.initialize(
                agents_dir, model_client, **kwargs
            )

            if success:
                self._record_usage(primary_type)
                return self._primary_adapter

        except Exception as e:
            logger.warning(f"Primary adapter initialization failed: {e}")

        # Try fallback if enabled
        if self.config.enable_fallback:
            self.stats.fallback_triggered += 1
            logger.info("Falling back to alternate framework")

            # Determine fallback type
            if primary_type == FrameworkType.AGENT_FRAMEWORK:
                fallback_type = FrameworkType.AUTOGEN
            elif primary_type == FrameworkType.AUTOGEN:
                fallback_type = FrameworkType.MOCK
            else:
                fallback_type = FrameworkType.MOCK

            self._fallback_adapter = create_adapter(fallback_type, "fallback")

            try:
                success = await self._fallback_adapter.initialize(
                    agents_dir, model_client, **kwargs
                )

                if success:
                    self._record_usage(fallback_type)
                    return self._fallback_adapter

            except Exception as e:
                logger.error(f"Fallback adapter initialization failed: {e}")

        # Last resort: mock adapter
        logger.warning("All adapters failed, using mock")
        mock = MockFrameworkAdapter("emergency_mock")
        await mock.initialize(agents_dir)
        self._record_usage(FrameworkType.MOCK)
        return mock

    def _record_usage(self, framework: FrameworkType) -> None:
        """Record framework usage for monitoring."""
        self.stats.last_updated = datetime.now()

        if framework == FrameworkType.AGENT_FRAMEWORK:
            self.stats.agent_framework_calls += 1
        elif framework == FrameworkType.AUTOGEN:
            self.stats.autogen_calls += 1
        else:
            self.stats.mock_calls += 1

        if self.config.log_framework_usage:
            logger.debug("Framework used", framework=framework.value)

    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        return {
            "config": {
                "selection": self.config.selection.value,
                "agent_framework_percentage": self.config.agent_framework_percentage,
                "fallback_enabled": self.config.enable_fallback,
                "force_framework": self.config.force_framework
            },
            "stats": self.stats.to_dict()
        }

    def update_percentage(self, percentage: int) -> None:
        """Update AF traffic percentage for gradual rollout.

        Args:
            percentage: New percentage (0-100)
        """
        self.config.agent_framework_percentage = max(0, min(100, percentage))
        logger.info(
            "Framework percentage updated",
            new_percentage=self.config.agent_framework_percentage
        )

    def set_selection(self, selection: FrameworkSelection) -> None:
        """Update framework selection strategy.

        Args:
            selection: New selection strategy
        """
        self.config.selection = selection
        logger.info("Framework selection updated", selection=selection.value)

    def force_framework(self, framework: Optional[str]) -> None:
        """Force specific framework (for testing).

        Args:
            framework: Framework to force, or None to clear
        """
        self.config.force_framework = framework
        logger.info("Framework forced", framework=framework)


# Global feature flag instance
_feature_flag: Optional[FrameworkFeatureFlag] = None


def get_feature_flag() -> FrameworkFeatureFlag:
    """Get global feature flag instance."""
    global _feature_flag
    if _feature_flag is None:
        _feature_flag = FrameworkFeatureFlag()
    return _feature_flag


def reset_feature_flag() -> None:
    """Reset global feature flag (for testing)."""
    global _feature_flag
    _feature_flag = None


# Convenience function
def use_agent_framework() -> bool:
    """Check if Agent Framework should be used.

    Returns:
        True if AF should be used for current request
    """
    return get_feature_flag().get_framework_type() == FrameworkType.AGENT_FRAMEWORK


__all__ = [
    "FrameworkFeatureFlag",
    "FrameworkConfig",
    "FrameworkSelection",
    "FrameworkUsageStats",
    "get_feature_flag",
    "reset_feature_flag",
    "use_agent_framework",
]
