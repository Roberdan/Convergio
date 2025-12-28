# AI Provider Architecture

*Technical architecture documentation for the Ollama-First AI Provider System (v2.1.0)*

## Overview

The AI Provider System is a flexible routing layer that manages AI requests between local (Ollama) and cloud (Azure OpenAI) providers. It provides intelligent routing, health monitoring, cost tracking, and graceful fallback capabilities.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Application Layer                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │   Agents     │  │   Workflows  │  │   Chat API   │               │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘               │
│         │                 │                  │                       │
│         └────────────────┬┴──────────────────┘                       │
│                          ▼                                           │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                    ProviderRouter                              │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐    │  │
│  │  │  AIConfig   │  │HealthChecker│  │    CostTracker      │    │  │
│  │  │  (modes)    │  │ (liveness)  │  │ (usage metrics)     │    │  │
│  │  └─────────────┘  └─────────────┘  └─────────────────────┘    │  │
│  └───────────────────────────┬───────────────────────────────────┘  │
│                              │                                       │
└──────────────────────────────┼───────────────────────────────────────┘
                               ▼
        ┌──────────────────────┴──────────────────────┐
        │              Provider Selection              │
        │  (based on mode, health, and capabilities)   │
        └──────────────────────┬───────────────────────┘
                               │
           ┌───────────────────┼───────────────────┐
           ▼                   ▼                   ▼
    ┌─────────────┐     ┌─────────────┐    ┌─────────────┐
    │   Ollama    │     │ Azure OpenAI│    │  (Future)   │
    │   Service   │     │   Service   │    │  Providers  │
    └──────┬──────┘     └──────┬──────┘    └─────────────┘
           │                   │
           ▼                   ▼
    ┌─────────────┐     ┌─────────────┐
    │ Local Model │     │ Cloud Model │
    │ (llama3.2)  │     │ (gpt-4o)    │
    └─────────────┘     └─────────────┘
```

## Core Components

### 1. AIConfig

Central configuration class that defines the provider mode and behavior.

**Location**: `backend/src/core/ai_providers.py`

```python
class ProviderMode(str, Enum):
    OLLAMA_ONLY = "ollama_only"      # Local only, $0 cost
    AZURE_ONLY = "azure_only"        # Cloud only
    HYBRID = "hybrid"                 # Local-first, cloud fallback
    CLOUD_FIRST = "cloud_first"      # Cloud-first, local fallback

class AIConfig:
    mode: ProviderMode
    strict_mode: bool  # Block fallback in strict modes
    ollama_host: str
    azure_endpoint: str
    azure_deployment: str
```

### 2. ProviderRouter

Intelligent routing engine that selects the appropriate provider based on mode, health, and capabilities.

**Location**: `backend/src/core/provider_router.py`

**Key Methods**:
- `chat(messages, functions=None)` - Route chat completion requests
- `_get_provider()` - Select provider based on configuration and health
- `_check_capabilities()` - Verify provider supports required features

**Routing Logic**:
```
1. Load AIConfig (mode, strict_mode)
2. If strict_mode AND mode is ollama_only/azure_only:
   → Use specified provider only, fail if unavailable
3. Check primary provider health
   → If healthy: use primary
   → If unhealthy: check fallback availability
4. If fallback available: use fallback
5. If no providers available: raise ProviderError
```

### 3. OllamaService

Native integration with local Ollama instance.

**Location**: `backend/src/core/ollama_service.py`

**Features**:
- Health check with version detection
- Chat completion with function calling
- Streaming support
- Model management

**Key Methods**:
```python
async def health_check() -> OllamaStatus
async def chat(model: str, messages: List[dict], functions: List[dict] = None) -> dict
async def list_models() -> List[str]
```

### 4. AzureOpenAIService

Integration with Azure OpenAI deployments.

**Location**: `backend/src/core/azure_openai_service.py`

**Features**:
- Secure authentication with API keys
- Function calling support
- Vision capabilities (gpt-4o)
- Token usage tracking

## Provider Modes

### OLLAMA_ONLY
- **Use Case**: Development, testing, cost-sensitive operations
- **Cost**: $0
- **Behavior**: All requests go to local Ollama
- **Strict Mode**: Blocks any cloud fallback attempts

### AZURE_ONLY
- **Use Case**: Production environments requiring cloud reliability
- **Cost**: Pay-per-use (Azure pricing)
- **Behavior**: All requests go to Azure OpenAI
- **Strict Mode**: Blocks any local fallback attempts

### HYBRID (Default)
- **Use Case**: Cost optimization with reliability
- **Cost**: Minimal (cloud used only when needed)
- **Behavior**:
  1. Try Ollama first
  2. Fallback to Azure if Ollama unavailable
  3. Track which provider served each request

### CLOUD_FIRST
- **Use Case**: Performance-critical applications
- **Cost**: Standard cloud costs
- **Behavior**:
  1. Try Azure OpenAI first
  2. Fallback to Ollama if Azure unavailable

## Capability Matrix

| Capability | Ollama | Azure OpenAI |
|------------|--------|--------------|
| Chat Completion | Yes | Yes |
| Function Calling | Yes | Yes |
| Streaming | Yes | Yes |
| Embeddings | Yes | Yes |
| Vision | Model-dependent | Yes (gpt-4o) |
| Fine-tuning | No | Yes |
| JSON Mode | Yes | Yes |

## Request Flow

### Chat Completion Request

```sequence
Client -> ProviderRouter: chat(messages, functions)
ProviderRouter -> AIConfig: get_mode()
ProviderRouter -> ProviderRouter: _get_provider()

alt Mode is OLLAMA_ONLY
    ProviderRouter -> OllamaService: health_check()
    OllamaService --> ProviderRouter: OllamaStatus
    alt Healthy
        ProviderRouter -> OllamaService: chat(model, messages, functions)
        OllamaService --> ProviderRouter: response
    else Unhealthy + strict_mode
        ProviderRouter --> Client: ProviderError
    end
else Mode is HYBRID
    ProviderRouter -> OllamaService: health_check()
    alt Ollama Healthy
        ProviderRouter -> OllamaService: chat(...)
    else Ollama Unhealthy
        ProviderRouter -> AzureOpenAIService: chat(...)
    end
end

ProviderRouter -> CostTracker: record(provider, tokens)
ProviderRouter --> Client: ChatResponse
```

## Configuration

### Environment Variables

```bash
# Provider Mode
AI_PROVIDER_MODE=ollama_only|azure_only|hybrid|cloud_first
AI_STRICT_MODE=true|false

# Ollama Configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_DEFAULT_MODEL=llama3.2

# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

### Per-Agent Override

Agents can override the global provider mode:

```python
@agent(
    name="premium_analyst",
    provider_mode=ProviderMode.AZURE_ONLY,  # Always use Azure
    priority="high"
)
async def analyze_data(context: AgentContext):
    ...
```

## Cost Tracking

The system tracks costs in real-time:

```python
class CostTracker:
    def record(self, provider: str, tokens: int, model: str):
        # Ollama: always $0
        # Azure: calculate based on model pricing

    def get_summary(self) -> CostSummary:
        return {
            "ollama": {"requests": N, "cost": 0.00},
            "azure": {"requests": M, "cost": X.XX},
            "savings": estimated_cloud_cost - actual_cost
        }
```

## Error Handling

### ProviderError
Raised when no provider is available:
```python
class ProviderError(Exception):
    """Raised when provider routing fails."""
    provider: str
    reason: str
    fallback_attempted: bool
```

### Retry Logic
- Ollama: Immediate retry with 3 attempts
- Azure: Exponential backoff with 5 attempts
- Cross-provider fallback: Single attempt

## Monitoring

### Health Checks
- Periodic health checks every 30 seconds
- On-demand checks before critical operations
- Health status exposed via `/api/v1/settings/ai/health`

### Metrics
- `ai_provider_requests_total` - Total requests by provider
- `ai_provider_latency_seconds` - Request latency histogram
- `ai_provider_errors_total` - Error count by provider
- `ai_provider_cost_usd` - Accumulated cost

## Security Considerations

1. **API Key Protection**: Azure API keys stored in environment variables
2. **Local-First Default**: Ollama mode prevents accidental cloud exposure
3. **Strict Mode**: Hard enforcement of provider restrictions
4. **Audit Logging**: All provider switches are logged

## Future Extensions

- **OpenAI Direct**: Support for OpenAI API (non-Azure)
- **Anthropic Claude**: Claude API integration
- **Google Gemini**: Gemini API integration
- **Custom Providers**: Plugin architecture for custom LLM providers
- **Load Balancing**: Multiple instances of same provider
- **A/B Testing**: Route percentage of traffic to test providers
