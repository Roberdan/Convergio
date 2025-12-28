# Ollama Setup Guide

*Complete guide to setting up and using Ollama with Convergio*

## Prerequisites

- macOS, Linux, or Windows (WSL2)
- 8GB+ RAM recommended
- 10GB+ disk space for models

## Installation

### macOS

```bash
# Using Homebrew (recommended)
brew install ollama

# Or download from https://ollama.ai
```

### Linux

```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

### Windows (WSL2)

1. Install WSL2 if not already installed
2. Run the Linux installation command in WSL2

## Quick Start

### 1. Start Ollama Server

```bash
# Start the Ollama server (required)
ollama serve

# The server runs on http://localhost:11434 by default
```

### 2. Pull Required Models

```bash
# Recommended model for general use
ollama pull llama3.2

# For code-related tasks
ollama pull codellama

# For smaller/faster responses
ollama pull mistral
```

### 3. Verify Installation

```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Expected output:
# {"models":[{"name":"llama3.2:latest",...}]}
```

### 4. Configure Convergio

Add to your `.env` file:

```bash
# AI Provider Mode
AI_PROVIDER_MODE=ollama_only
AI_STRICT_MODE=true

# Ollama Configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_DEFAULT_MODEL=llama3.2
```

### 5. Test the Integration

```bash
# Start Convergio backend
cd backend
uvicorn src.main:app --reload

# Test AI endpoint
curl -X POST http://localhost:8000/api/v1/agents/chat \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "ali_chief_of_staff", "message": "Hello"}'
```

## Model Recommendations

| Model | Size | Best For | Pull Command |
|-------|------|----------|--------------|
| llama3.2 | 4GB | General tasks | `ollama pull llama3.2` |
| llama3.2:1b | 1.3GB | Fast responses | `ollama pull llama3.2:1b` |
| codellama | 4GB | Coding tasks | `ollama pull codellama` |
| mistral | 4GB | General + fast | `ollama pull mistral` |
| mixtral | 26GB | Complex reasoning | `ollama pull mixtral` |

## Configuration Options

### Environment Variables

```bash
# Required
OLLAMA_HOST=http://localhost:11434
OLLAMA_DEFAULT_MODEL=llama3.2

# Optional
OLLAMA_TIMEOUT=60              # Request timeout in seconds
OLLAMA_MAX_TOKENS=4096         # Max tokens per response
OLLAMA_TEMPERATURE=0.7         # Response creativity (0.0-1.0)
```

### Running on a Different Port

```bash
# Set custom port
OLLAMA_HOST=0.0.0.0:11435 ollama serve

# Update .env
OLLAMA_HOST=http://localhost:11435
```

### Remote Ollama Server

```bash
# On the remote server
OLLAMA_HOST=0.0.0.0 ollama serve

# In Convergio .env
OLLAMA_HOST=http://remote-server:11434
```

## Function Calling

Ollama supports function calling with compatible models:

```python
# Example function definition
functions = [
    {
        "name": "get_weather",
        "description": "Get current weather for a location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string"}
            },
            "required": ["location"]
        }
    }
]

# The ProviderRouter handles function calling automatically
response = await router.chat(messages, functions=functions)
```

## Performance Tuning

### GPU Acceleration

```bash
# Check GPU availability
ollama run llama3.2 --verbose

# For NVIDIA GPUs, ensure CUDA is installed
nvidia-smi
```

### Memory Optimization

```bash
# Use quantized models for lower memory usage
ollama pull llama3.2:q4_0  # 4-bit quantization
ollama pull llama3.2:q8_0  # 8-bit quantization
```

### Concurrent Requests

```bash
# Set max parallel requests
OLLAMA_NUM_PARALLEL=4 ollama serve
```

## Troubleshooting

### Connection Refused

```bash
# Ensure Ollama is running
pgrep ollama || ollama serve &

# Check the port is listening
lsof -i :11434
```

### Model Not Found

```bash
# List available models
ollama list

# Pull the required model
ollama pull llama3.2
```

### Slow Responses

1. Use a smaller model (`llama3.2:1b`)
2. Enable GPU acceleration
3. Increase `OLLAMA_NUM_PARALLEL`
4. Use quantized models

### Out of Memory

```bash
# Use smaller models
ollama pull llama3.2:1b

# Or increase swap space
sudo swapon --show
```

## Integration Testing

Run the E2E tests to verify your setup:

```bash
cd backend
pytest tests/e2e/test_ollama_e2e.py -v

# Expected: 24 tests passing
```

## Monitoring

### Health Check Endpoint

```bash
curl http://localhost:8000/api/v1/settings/ai/health
```

### Ollama Logs

```bash
# View Ollama server logs
journalctl -u ollama -f  # Linux with systemd
ollama logs              # Direct command
```

## Cost Benefits

| Scenario | Ollama | Cloud Provider |
|----------|--------|----------------|
| 1000 requests/day | $0 | ~$15-30 |
| 10,000 tokens/request | $0 | ~$0.03 |
| Monthly (development) | $0 | ~$50-100 |

Using Ollama for development and testing saves significant costs while maintaining full API compatibility.

## Next Steps

1. [Azure OpenAI Setup Guide](./AZURE_OPENAI_SETUP_GUIDE.md) - For hybrid/cloud configurations
2. [AI Provider Architecture](../AI_PROVIDER_ARCHITECTURE.md) - Technical deep-dive
3. [API Reference](../API_REFERENCE.md) - Full endpoint documentation
