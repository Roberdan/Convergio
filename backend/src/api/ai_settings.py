"""
AI Settings API - Provider Configuration and Management

This module provides:
- GET/PUT AI provider configuration
- Ollama status and model management
- Provider capability matrix
- Usage statistics and cost tracking

Copyright (c) 2025 Convergio.io
"""

import os
from datetime import datetime
from typing import Dict, Any, Optional, List

import structlog
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from ..core.ai_providers import (
    AIConfig,
    AIProvider,
    ProviderMode,
    FeatureCapability,
    CAPABILITY_MATRIX,
    PROVIDER_INFO,
    get_ai_config_from_env,
)
from ..core.ollama_service import (
    OllamaService,
    OllamaStatus,
    OllamaModel,
    get_ollama_service,
)
from ..core.provider_router import get_provider_router

logger = structlog.get_logger()
router = APIRouter(tags=["AI Settings"])


# ============================================================================
# Request/Response Models
# ============================================================================

class AIConfigUpdate(BaseModel):
    """Request model for updating AI configuration."""
    mode: Optional[ProviderMode] = Field(
        None, description="Provider mode (ollama_only, azure_only, hybrid, cloud_first)"
    )
    strict_mode: Optional[bool] = Field(
        None, description="If true, never fallback to cloud providers"
    )
    default_model: Optional[str] = Field(
        None, description="Default model name"
    )
    ollama_host: Optional[str] = Field(
        None, description="Ollama server URL"
    )


class FeatureOverride(BaseModel):
    """Configure provider override for a specific feature."""
    feature: FeatureCapability
    provider: AIProvider
    model: str


class AgentOverride(BaseModel):
    """Configure provider override for a specific agent."""
    agent_id: str
    provider: AIProvider
    model: str


class ProviderInfo(BaseModel):
    """Information about an AI provider."""
    name: str
    display_name: str
    is_local: bool
    is_free: bool
    requires_api_key: bool
    configured: bool
    capabilities: List[str]
    context_window: int


class OllamaPullRequest(BaseModel):
    """Request to pull (download) an Ollama model."""
    model_name: str = Field(..., description="Model name to pull (e.g., llama3.2:latest)")


# ============================================================================
# AI Configuration Endpoints
# ============================================================================

@router.get("/config")
async def get_ai_config() -> Dict[str, Any]:
    """
    Get current AI provider configuration.

    Returns the active configuration including:
    - Provider mode (ollama_only, azure_only, hybrid, cloud_first)
    - Strict mode setting
    - Default provider and model
    - Feature and agent overrides
    """
    config = get_ai_config_from_env()

    return {
        "mode": config.mode.value,
        "strict_mode": config.strict_mode,
        "default_provider": config.default_provider.value,
        "default_model": config.default_model,
        "ollama_host": config.ollama_host,
        "azure_endpoint": config.azure_endpoint,
        "azure_deployment": config.azure_deployment,
        "feature_overrides": {
            k.value: {"provider": v.provider.value, "model": v.model}
            for k, v in config.features.items()
        },
        "agent_overrides": {
            k: {"provider": v.provider.value, "model": v.model}
            for k, v in config.agents.items()
        },
    }


@router.put("/config")
async def update_ai_config(update: AIConfigUpdate) -> Dict[str, Any]:
    """
    Update AI provider configuration.

    Note: This endpoint updates environment variables that will take effect
    on the next application restart. For immediate changes, use the provider
    override endpoints.
    """
    changes = {}

    if update.mode is not None:
        os.environ["AI_PROVIDER_MODE"] = update.mode.value
        changes["mode"] = update.mode.value

    if update.strict_mode is not None:
        os.environ["AI_STRICT_MODE"] = str(update.strict_mode).lower()
        changes["strict_mode"] = update.strict_mode

    if update.default_model is not None:
        os.environ["OLLAMA_DEFAULT_MODEL"] = update.default_model
        changes["default_model"] = update.default_model

    if update.ollama_host is not None:
        os.environ["OLLAMA_HOST"] = update.ollama_host
        changes["ollama_host"] = update.ollama_host

    logger.info("AI config updated", changes=changes)

    # Reset the provider router to pick up changes
    from ..core.provider_router import reset_provider_router
    reset_provider_router()

    return {
        "status": "updated",
        "changes": changes,
        "note": "Some changes may require application restart to take full effect",
    }


@router.post("/config/feature-override")
async def set_feature_override(override: FeatureOverride) -> Dict[str, Any]:
    """
    Set provider override for a specific feature.

    This allows configuring different providers for different capabilities:
    - Use Ollama for simple chat
    - Use Azure for complex reasoning
    - Use Perplexity for web search
    """
    # Validate provider can handle the feature
    if override.feature not in CAPABILITY_MATRIX.get(override.provider, []):
        raise HTTPException(
            status_code=400,
            detail=f"Provider {override.provider.value} does not support {override.feature.value}"
        )

    # Store in environment (could use Redis for persistence)
    env_key = f"AI_FEATURE_{override.feature.value.upper()}_PROVIDER"
    os.environ[env_key] = override.provider.value
    os.environ[f"{env_key}_MODEL"] = override.model

    logger.info(
        "Feature override set",
        feature=override.feature.value,
        provider=override.provider.value,
        model=override.model,
    )

    return {
        "status": "override_set",
        "feature": override.feature.value,
        "provider": override.provider.value,
        "model": override.model,
    }


@router.post("/config/agent-override")
async def set_agent_override(override: AgentOverride) -> Dict[str, Any]:
    """
    Set provider override for a specific agent.

    This allows configuring different providers for different agents:
    - Use Ollama for cost-sensitive agents
    - Use GPT-4 for complex reasoning agents
    - Use Claude for creative agents
    """
    # Store in environment (could use Redis for persistence)
    env_key = f"AI_AGENT_{override.agent_id.upper()}_PROVIDER"
    os.environ[env_key] = override.provider.value
    os.environ[f"{env_key}_MODEL"] = override.model

    logger.info(
        "Agent override set",
        agent_id=override.agent_id,
        provider=override.provider.value,
        model=override.model,
    )

    return {
        "status": "override_set",
        "agent_id": override.agent_id,
        "provider": override.provider.value,
        "model": override.model,
    }


@router.delete("/config/feature-override/{feature}")
async def remove_feature_override(feature: FeatureCapability) -> Dict[str, Any]:
    """Remove provider override for a feature."""
    env_key = f"AI_FEATURE_{feature.value.upper()}_PROVIDER"

    if env_key in os.environ:
        del os.environ[env_key]
    if f"{env_key}_MODEL" in os.environ:
        del os.environ[f"{env_key}_MODEL"]

    return {"status": "override_removed", "feature": feature.value}


@router.delete("/config/agent-override/{agent_id}")
async def remove_agent_override(agent_id: str) -> Dict[str, Any]:
    """Remove provider override for an agent."""
    env_key = f"AI_AGENT_{agent_id.upper()}_PROVIDER"

    if env_key in os.environ:
        del os.environ[env_key]
    if f"{env_key}_MODEL" in os.environ:
        del os.environ[f"{env_key}_MODEL"]

    return {"status": "override_removed", "agent_id": agent_id}


# ============================================================================
# Provider Information Endpoints
# ============================================================================

@router.get("/providers")
async def list_providers() -> Dict[str, Any]:
    """
    List all available AI providers with their configuration status.

    Shows which providers are:
    - Configured (API key available)
    - Local vs Cloud
    - Free vs Paid
    """
    providers = []

    for provider, info in PROVIDER_INFO.items():
        # Check if provider is configured
        configured = False
        if provider == AIProvider.OLLAMA:
            ollama = get_ollama_service()
            try:
                status = await ollama.health_check()
                configured = status.available
            except Exception:
                configured = False
        elif provider == AIProvider.OPENAI:
            configured = bool(os.getenv("OPENAI_API_KEY"))
        elif provider == AIProvider.ANTHROPIC:
            configured = bool(os.getenv("ANTHROPIC_API_KEY"))
        elif provider == AIProvider.AZURE_OPENAI:
            configured = bool(os.getenv("AZURE_OPENAI_API_KEY")) and bool(os.getenv("AZURE_OPENAI_ENDPOINT"))
        elif provider == AIProvider.PERPLEXITY:
            configured = bool(os.getenv("PERPLEXITY_API_KEY"))
        elif provider == AIProvider.LOCAL_EMBEDDINGS:
            configured = True  # Always available

        providers.append({
            "name": provider.value,
            "display_name": provider.value.replace("_", " ").title(),
            "is_local": info.is_local,
            "is_free": info.is_free,
            "requires_api_key": info.requires_api_key,
            "configured": configured,
            "capabilities": [c.value for c in info.capabilities],
            "context_window": info.context_window,
            "supports_streaming": info.supports_streaming,
        })

    return {
        "providers": providers,
        "total": len(providers),
        "configured_count": sum(1 for p in providers if p["configured"]),
    }


@router.get("/capabilities")
async def get_capability_matrix() -> Dict[str, Any]:
    """
    Get the capability matrix showing which providers support which features.

    Useful for understanding what each provider can do.
    """
    matrix = {}

    for capability in FeatureCapability:
        matrix[capability.value] = {
            "name": capability.value.replace("_", " ").title(),
            "providers": [
                p.value
                for p, caps in CAPABILITY_MATRIX.items()
                if capability in caps
            ],
        }

    return {
        "capabilities": matrix,
        "providers": [p.value for p in AIProvider],
    }


# ============================================================================
# Ollama Endpoints
# ============================================================================

@router.get("/ollama/status")
async def get_ollama_status() -> Dict[str, Any]:
    """
    Get Ollama server status.

    Returns:
    - Availability status
    - Version
    - Available models
    - GPU availability
    """
    ollama = get_ollama_service()
    status = await ollama.health_check()

    return {
        "available": status.available,
        "version": status.version,
        "gpu_available": status.gpu_available,
        "gpu_name": status.gpu_name,
        "error": status.error,
        "models": [
            {
                "name": m.name,
                "size_bytes": m.size,
                "size_human": f"{m.size / 1024 / 1024 / 1024:.1f} GB",
                "capabilities": [c.value for c in m.capabilities],
                "modified_at": m.modified_at,
            }
            for m in status.models
        ],
        "model_count": len(status.models),
    }


@router.post("/ollama/pull")
async def pull_ollama_model(request: OllamaPullRequest) -> Dict[str, Any]:
    """
    Pull (download) an Ollama model.

    This starts the download process. For large models, this can take
    several minutes to complete.
    """
    ollama = get_ollama_service()

    # Check Ollama is available
    status = await ollama.health_check()
    if not status.available:
        raise HTTPException(
            status_code=503,
            detail=f"Ollama is not available: {status.error}"
        )

    # Start pull
    success = await ollama.pull_model(request.model_name)

    if success:
        return {
            "status": "pulling",
            "model_name": request.model_name,
            "message": "Model download started. This may take several minutes for large models.",
        }
    else:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start model pull for {request.model_name}"
        )


@router.get("/ollama/recommended")
async def get_recommended_models() -> Dict[str, Any]:
    """
    Get recommended Ollama models for different use cases.
    """
    return {
        "general": {
            "name": "llama3.2:latest",
            "description": "Best balance of quality and speed",
            "size": "~4GB",
        },
        "fast": {
            "name": "llama3.2:3b",
            "description": "Faster responses, smaller model",
            "size": "~2GB",
        },
        "coding": {
            "name": "qwen2.5-coder:7b",
            "description": "Optimized for code generation",
            "size": "~4GB",
        },
        "embeddings": {
            "name": "nomic-embed-text",
            "description": "High quality text embeddings",
            "size": "~500MB",
        },
        "vision": {
            "name": "llava:7b",
            "description": "Image understanding",
            "size": "~4GB",
        },
    }


# ============================================================================
# Statistics Endpoints
# ============================================================================

@router.get("/stats")
async def get_provider_stats() -> Dict[str, Any]:
    """
    Get AI provider usage statistics.

    Returns:
    - Call counts per provider
    - Costs per provider
    - Savings from using local providers
    """
    router_instance = get_provider_router()
    stats = router_instance.get_stats()

    return {
        "mode": stats["mode"],
        "strict_mode": stats["strict_mode"],
        "default_provider": stats["default_provider"],
        "call_counts": stats["call_counts"],
        "costs_usd": stats["costs_usd"],
        "total_cost_usd": stats["total_cost_usd"],
        "savings_vs_cloud_usd": stats["savings_vs_cloud"],
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/costs")
async def get_provider_costs() -> Dict[str, Any]:
    """
    Get detailed cost breakdown by provider.

    Useful for monitoring cloud API usage and calculating ROI
    of using local models.
    """
    router_instance = get_provider_router()
    costs = router_instance.get_costs()
    stats = router_instance.get_stats()

    return {
        "costs_by_provider": costs,
        "total_cost_usd": stats["total_cost_usd"],
        "savings_vs_cloud_usd": stats["savings_vs_cloud"],
        "recommendations": {
            "use_ollama_for": [
                "Simple chat completions",
                "Code generation",
                "Embedding generation",
            ],
            "use_cloud_for": [
                "Complex multi-step reasoning",
                "Long context processing",
                "Real-time web search",
            ],
        },
    }


# ============================================================================
# Validation Endpoint
# ============================================================================

@router.post("/validate")
async def validate_config() -> Dict[str, Any]:
    """
    Validate current AI configuration.

    Checks:
    - Provider availability
    - API key validity
    - Model availability
    """
    config = get_ai_config_from_env()
    issues = []
    warnings = []

    # Check Ollama if configured
    if config.mode in [ProviderMode.OLLAMA_ONLY, ProviderMode.HYBRID]:
        ollama = get_ollama_service()
        status = await ollama.health_check()
        if not status.available:
            if config.mode == ProviderMode.OLLAMA_ONLY and config.strict_mode:
                issues.append(f"Ollama is not available: {status.error}")
            else:
                warnings.append(f"Ollama is not available: {status.error}")
        elif config.default_model and not any(
            m.name == config.default_model or m.name.startswith(config.default_model.split(":")[0])
            for m in status.models
        ):
            warnings.append(f"Default model '{config.default_model}' not found in Ollama")

    # Check Azure if configured
    if config.mode == ProviderMode.AZURE_ONLY:
        if not os.getenv("AZURE_OPENAI_API_KEY"):
            issues.append("Azure OpenAI API key not configured")
        if not os.getenv("AZURE_OPENAI_ENDPOINT"):
            issues.append("Azure OpenAI endpoint not configured")
        if not os.getenv("AZURE_OPENAI_DEPLOYMENT"):
            warnings.append("Azure OpenAI deployment not configured (will use default)")

    # Check cloud providers for hybrid/cloud_first
    if config.mode in [ProviderMode.CLOUD_FIRST, ProviderMode.HYBRID]:
        if not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
            if config.mode == ProviderMode.CLOUD_FIRST:
                issues.append("No cloud provider API key configured")
            else:
                warnings.append("No cloud provider API key configured (Ollama will be used)")

    valid = len(issues) == 0

    return {
        "valid": valid,
        "issues": issues,
        "warnings": warnings,
        "config": {
            "mode": config.mode.value,
            "strict_mode": config.strict_mode,
            "default_provider": config.default_provider.value,
        },
    }


# ============================================================================
# Azure OpenAI Endpoints
# ============================================================================

class AzureConfigUpdate(BaseModel):
    """Request model for updating Azure OpenAI configuration."""
    endpoint: Optional[str] = Field(None, description="Azure OpenAI endpoint URL")
    api_key: Optional[str] = Field(None, description="Azure OpenAI API key")
    deployment: Optional[str] = Field(None, description="Default deployment name")
    api_version: Optional[str] = Field(None, description="API version")
    realtime_endpoint: Optional[str] = Field(None, description="Realtime API endpoint")
    realtime_deployment: Optional[str] = Field(None, description="Realtime deployment name")


@router.get("/azure/status")
async def get_azure_status() -> Dict[str, Any]:
    """
    Get Azure OpenAI configuration status.

    Returns:
    - Configuration status
    - Available deployments (if connected)
    - Realtime capability
    """
    import httpx

    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")

    # Check basic configuration
    configured = bool(endpoint and api_key)

    result = {
        "configured": configured,
        "endpoint": endpoint[:50] + "..." if endpoint and len(endpoint) > 50 else endpoint,
        "deployment": deployment,
        "api_version": api_version,
        "connection_status": "unknown",
        "deployments": [],
        "realtime": {
            "configured": bool(os.getenv("AZURE_OPENAI_REALTIME_ENDPOINT")),
            "endpoint": os.getenv("AZURE_OPENAI_REALTIME_ENDPOINT"),
            "deployment": os.getenv("AZURE_OPENAI_REALTIME_DEPLOYMENT"),
        },
    }

    if not configured:
        result["connection_status"] = "not_configured"
        return result

    # Test connection and discover deployments
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Try to list deployments
            url = f"{endpoint.rstrip('/')}/openai/deployments?api-version={api_version}"
            response = await client.get(
                url,
                headers={"api-key": api_key},
            )

            if response.status_code == 200:
                data = response.json()
                deployments = data.get("data", [])
                result["connection_status"] = "connected"
                result["deployments"] = [
                    {
                        "id": d.get("id"),
                        "model": d.get("model"),
                        "status": d.get("status"),
                        "capabilities": d.get("capabilities", {}),
                    }
                    for d in deployments
                ]
            elif response.status_code == 401:
                result["connection_status"] = "unauthorized"
                result["error"] = "Invalid API key"
            elif response.status_code == 404:
                # Deployment list might not be available, try a simple test
                result["connection_status"] = "connected"
                result["note"] = "Deployment discovery not available, but endpoint is reachable"
            else:
                result["connection_status"] = "error"
                result["error"] = f"HTTP {response.status_code}"

    except httpx.ConnectError:
        result["connection_status"] = "unreachable"
        result["error"] = "Cannot connect to Azure OpenAI endpoint"
    except httpx.TimeoutException:
        result["connection_status"] = "timeout"
        result["error"] = "Connection timed out"
    except Exception as e:
        result["connection_status"] = "error"
        result["error"] = str(e)

    return result


@router.put("/azure/config")
async def update_azure_config(update: AzureConfigUpdate) -> Dict[str, Any]:
    """
    Update Azure OpenAI configuration.

    Note: For security, API keys are stored in environment variables.
    Changes take effect immediately for new requests.
    """
    changes = {}

    if update.endpoint is not None:
        os.environ["AZURE_OPENAI_ENDPOINT"] = update.endpoint
        changes["endpoint"] = update.endpoint

    if update.api_key is not None:
        os.environ["AZURE_OPENAI_API_KEY"] = update.api_key
        changes["api_key"] = "***" + update.api_key[-4:] if len(update.api_key) > 4 else "****"

    if update.deployment is not None:
        os.environ["AZURE_OPENAI_DEPLOYMENT"] = update.deployment
        changes["deployment"] = update.deployment

    if update.api_version is not None:
        os.environ["AZURE_OPENAI_API_VERSION"] = update.api_version
        changes["api_version"] = update.api_version

    if update.realtime_endpoint is not None:
        os.environ["AZURE_OPENAI_REALTIME_ENDPOINT"] = update.realtime_endpoint
        changes["realtime_endpoint"] = update.realtime_endpoint

    if update.realtime_deployment is not None:
        os.environ["AZURE_OPENAI_REALTIME_DEPLOYMENT"] = update.realtime_deployment
        changes["realtime_deployment"] = update.realtime_deployment

    # Reset provider router to pick up changes
    from ..core.provider_router import reset_provider_router
    reset_provider_router()

    logger.info("Azure OpenAI config updated", changes=list(changes.keys()))

    return {
        "status": "updated",
        "changes": changes,
    }


@router.post("/azure/test")
async def test_azure_connection() -> Dict[str, Any]:
    """
    Test Azure OpenAI connection with a simple completion.

    Sends a minimal request to verify the configuration is working.
    """
    import httpx

    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")

    if not all([endpoint, api_key, deployment]):
        return {
            "success": False,
            "error": "Azure OpenAI not fully configured",
            "missing": [
                k for k, v in {
                    "endpoint": endpoint,
                    "api_key": api_key,
                    "deployment": deployment,
                }.items() if not v
            ],
        }

    try:
        url = f"{endpoint.rstrip('/')}/openai/deployments/{deployment}/chat/completions?api-version={api_version}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                headers={"api-key": api_key},
                json={
                    "messages": [{"role": "user", "content": "Say 'OK' if you can read this."}],
                    "max_tokens": 10,
                },
            )

            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                return {
                    "success": True,
                    "response": content,
                    "model": data.get("model"),
                    "usage": data.get("usage", {}),
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "detail": response.text[:200],
                }

    except httpx.ConnectError:
        return {
            "success": False,
            "error": "Cannot connect to Azure OpenAI endpoint",
        }
    except httpx.TimeoutException:
        return {
            "success": False,
            "error": "Request timed out",
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


@router.get("/azure/realtime/status")
async def get_azure_realtime_status() -> Dict[str, Any]:
    """
    Get Azure OpenAI Realtime API status.

    The Realtime API enables voice interactions with low latency.
    Requires a separate deployment with gpt-4o-realtime model.
    """
    endpoint = os.getenv("AZURE_OPENAI_REALTIME_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_REALTIME_API_KEY") or os.getenv("AZURE_OPENAI_API_KEY")
    deployment = os.getenv("AZURE_OPENAI_REALTIME_DEPLOYMENT")

    configured = bool(endpoint and api_key and deployment)

    return {
        "configured": configured,
        "endpoint": endpoint,
        "deployment": deployment,
        "capabilities": {
            "voice_input": configured,
            "voice_output": configured,
            "low_latency": configured,
        },
        "requirements": {
            "model": "gpt-4o-realtime-preview",
            "api_version": "2024-10-01-preview",
            "websocket": True,
        },
        "setup_guide": "https://learn.microsoft.com/azure/ai-services/openai/realtime-audio-quickstart" if not configured else None,
    }


# ============================================================================
# Cost Alerts Endpoint
# ============================================================================

class CostAlertConfig(BaseModel):
    """Configuration for cost alerts."""
    enabled: bool = Field(True, description="Enable cost alerts")
    daily_limit_usd: float = Field(10.0, description="Daily spending limit in USD")
    monthly_limit_usd: float = Field(100.0, description="Monthly spending limit in USD")
    alert_threshold_percent: float = Field(80.0, description="Alert at this percentage of limit")


@router.get("/costs/alerts")
async def get_cost_alerts() -> Dict[str, Any]:
    """
    Get current cost alert configuration and status.
    """
    router_instance = get_provider_router()
    stats = router_instance.get_stats()
    total_cost = stats["total_cost_usd"]

    # Get alert config from env (default values if not set)
    daily_limit = float(os.getenv("AI_COST_DAILY_LIMIT_USD", "10.0"))
    monthly_limit = float(os.getenv("AI_COST_MONTHLY_LIMIT_USD", "100.0"))
    alert_threshold = float(os.getenv("AI_COST_ALERT_THRESHOLD_PERCENT", "80.0"))

    daily_usage_percent = (total_cost / daily_limit * 100) if daily_limit > 0 else 0

    alerts = []
    if daily_usage_percent >= 100:
        alerts.append({
            "level": "critical",
            "message": f"Daily spending limit exceeded: ${total_cost:.2f} / ${daily_limit:.2f}",
        })
    elif daily_usage_percent >= alert_threshold:
        alerts.append({
            "level": "warning",
            "message": f"Approaching daily limit: ${total_cost:.2f} / ${daily_limit:.2f} ({daily_usage_percent:.0f}%)",
        })

    return {
        "config": {
            "enabled": os.getenv("AI_COST_ALERTS_ENABLED", "true").lower() == "true",
            "daily_limit_usd": daily_limit,
            "monthly_limit_usd": monthly_limit,
            "alert_threshold_percent": alert_threshold,
        },
        "current": {
            "total_cost_usd": total_cost,
            "daily_usage_percent": daily_usage_percent,
            "savings_usd": stats["savings_vs_cloud"],
        },
        "alerts": alerts,
        "recommendations": [
            "Use Ollama for routine tasks to reduce cloud costs",
            "Configure per-agent provider overrides for cost control",
        ] if total_cost > 0 else [],
    }


@router.put("/costs/alerts")
async def update_cost_alerts(config: CostAlertConfig) -> Dict[str, Any]:
    """
    Update cost alert configuration.
    """
    os.environ["AI_COST_ALERTS_ENABLED"] = str(config.enabled).lower()
    os.environ["AI_COST_DAILY_LIMIT_USD"] = str(config.daily_limit_usd)
    os.environ["AI_COST_MONTHLY_LIMIT_USD"] = str(config.monthly_limit_usd)
    os.environ["AI_COST_ALERT_THRESHOLD_PERCENT"] = str(config.alert_threshold_percent)

    logger.info("Cost alert config updated", config=config.model_dump())

    return {
        "status": "updated",
        "config": config.model_dump(),
    }
