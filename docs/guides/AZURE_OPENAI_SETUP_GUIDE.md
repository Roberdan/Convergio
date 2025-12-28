# Azure OpenAI Setup Guide

*Complete guide to configuring Azure OpenAI with Convergio*

## Prerequisites

- Azure subscription
- Azure OpenAI Service access (requires application approval)
- Deployed Azure OpenAI model

## Quick Start

### 1. Create Azure OpenAI Resource

1. Go to [Azure Portal](https://portal.azure.com)
2. Search for "Azure OpenAI"
3. Click "Create"
4. Fill in the details:
   - **Subscription**: Your Azure subscription
   - **Resource Group**: Create new or use existing
   - **Region**: Choose a supported region
   - **Name**: Unique resource name (e.g., `convergio-openai`)
   - **Pricing Tier**: Standard S0

### 2. Deploy a Model

1. Go to [Azure OpenAI Studio](https://oai.azure.com)
2. Select your resource
3. Navigate to "Deployments"
4. Click "Create new deployment"
5. Select model and deployment name:
   - **Model**: gpt-4o (recommended) or gpt-4-turbo
   - **Deployment name**: e.g., `gpt-4o-deployment`

### 3. Get Connection Details

From Azure Portal → Your OpenAI Resource:

1. Go to "Keys and Endpoint"
2. Copy:
   - **Endpoint**: `https://your-resource.openai.azure.com/`
   - **Key 1** or **Key 2**: Your API key

### 4. Configure Convergio

Add to your `.env` file:

```bash
# AI Provider Mode
AI_PROVIDER_MODE=hybrid           # or azure_only for cloud-only
AI_STRICT_MODE=false

# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_DEPLOYMENT=gpt-4o-deployment
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

### 5. Test the Integration

```bash
# Start Convergio backend
cd backend
uvicorn src.main:app --reload

# Test with Azure
curl -X POST http://localhost:8000/api/v1/agents/chat \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "ali_chief_of_staff", "message": "Hello"}'
```

## Provider Modes with Azure

| Mode | Behavior | Best For |
|------|----------|----------|
| `azure_only` | Cloud only, no fallback | Production environments |
| `hybrid` | Ollama first, Azure fallback | Cost optimization |
| `cloud_first` | Azure first, Ollama fallback | Performance-critical apps |

## Configuration Options

### Environment Variables

```bash
# Required
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT=gpt-4o-deployment

# Optional
AZURE_OPENAI_API_VERSION=2024-02-15-preview  # API version
AZURE_OPENAI_TIMEOUT=60                       # Request timeout
AZURE_OPENAI_MAX_TOKENS=4096                  # Max response tokens
AZURE_OPENAI_TEMPERATURE=0.7                  # Response creativity
```

### Multiple Deployments

For different use cases, deploy multiple models:

```bash
# Primary deployment (high capability)
AZURE_OPENAI_DEPLOYMENT=gpt-4o-deployment

# Cost-effective deployment for simple tasks
AZURE_OPENAI_DEPLOYMENT_FAST=gpt-35-turbo-deployment

# Embeddings deployment
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
```

## Cost Management

### Pricing Tiers

| Model | Input (per 1K tokens) | Output (per 1K tokens) |
|-------|----------------------|------------------------|
| GPT-4o | $0.005 | $0.015 |
| GPT-4 Turbo | $0.01 | $0.03 |
| GPT-3.5 Turbo | $0.0005 | $0.0015 |

### Cost Tracking

Convergio tracks Azure costs automatically:

```bash
# View cost metrics
curl http://localhost:8000/api/v1/settings/ai/costs
```

### Budget Alerts

Set up Azure budget alerts:

1. Go to Azure Portal → Cost Management
2. Create a budget for your OpenAI resource
3. Set alert thresholds (e.g., 50%, 80%, 100%)

## Security Best Practices

### 1. Use Key Vault

Store API keys in Azure Key Vault:

```bash
# Create Key Vault secret
az keyvault secret set \
  --vault-name your-vault \
  --name azure-openai-key \
  --value "your-api-key"

# Reference in application
AZURE_OPENAI_API_KEY=@Microsoft.KeyVault(SecretUri=...)
```

### 2. Managed Identity

For Azure deployments, use managed identity instead of API keys:

```python
from azure.identity import DefaultAzureCredential

credential = DefaultAzureCredential()
# No API key needed in environment
```

### 3. Network Security

- Enable Private Endpoints for your OpenAI resource
- Configure Virtual Network integration
- Use IP filtering for public access

## Function Calling

Azure OpenAI supports advanced function calling:

```python
functions = [
    {
        "name": "search_database",
        "description": "Search the company database",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "table": {"type": "string", "enum": ["users", "orders", "products"]}
            },
            "required": ["query"]
        }
    }
]

# ProviderRouter handles function calling
response = await router.chat(messages, functions=functions)
```

## Vision Capabilities

GPT-4o supports image analysis:

```python
messages = [
    {
        "role": "user",
        "content": [
            {"type": "text", "text": "What's in this image?"},
            {"type": "image_url", "image_url": {"url": "https://..."}}
        ]
    }
]
```

## Troubleshooting

### Authentication Errors

```bash
# Verify API key
curl https://your-resource.openai.azure.com/openai/deployments?api-version=2024-02-15-preview \
  -H "api-key: your-api-key"

# Check for 401/403 errors
```

### Deployment Not Found

```bash
# List deployments
curl https://your-resource.openai.azure.com/openai/deployments?api-version=2024-02-15-preview \
  -H "api-key: your-api-key"

# Verify deployment name matches .env
```

### Rate Limiting (429)

1. Check your quota in Azure Portal
2. Implement retry with exponential backoff (built into Convergio)
3. Consider upgrading your tier

### Region Availability

Not all models are available in all regions. Check [Azure OpenAI Region Availability](https://learn.microsoft.com/azure/ai-services/openai/concepts/models#model-summary-table-and-region-availability).

## Hybrid Mode Setup

For cost-effective production:

```bash
# Use Ollama primarily, Azure for complex tasks
AI_PROVIDER_MODE=hybrid
AI_STRICT_MODE=false

# Ollama for development/simple tasks
OLLAMA_HOST=http://localhost:11434
OLLAMA_DEFAULT_MODEL=llama3.2

# Azure for production fallback
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT=gpt-4o-deployment
```

Benefits:
- 90%+ cost reduction during development
- Cloud reliability when Ollama unavailable
- Seamless fallback without code changes

## Integration Testing

Run the E2E tests:

```bash
cd backend

# Test Azure-only mode
AI_PROVIDER_MODE=azure_only pytest tests/e2e/test_ollama_e2e.py -v -k azure

# Test hybrid mode
AI_PROVIDER_MODE=hybrid pytest tests/e2e/test_ollama_e2e.py -v
```

## Monitoring

### Health Check

```bash
curl http://localhost:8000/api/v1/settings/ai/health
```

### Azure Monitor

1. Enable diagnostic settings for your OpenAI resource
2. Create dashboards for:
   - Token usage
   - Request latency
   - Error rates
   - Cost accumulation

## Next Steps

1. [Ollama Setup Guide](./OLLAMA_SETUP_GUIDE.md) - For local development
2. [AI Provider Architecture](../AI_PROVIDER_ARCHITECTURE.md) - Technical deep-dive
3. [API Reference](../API_REFERENCE.md) - Full endpoint documentation
