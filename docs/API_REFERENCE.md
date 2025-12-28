# 🚀 Convergio API Reference

*Comprehensive API documentation for the Convergio unified AI platform*

## Overview

Convergio provides a unified REST API built with FastAPI that combines talent management, AI agent orchestration, vector search, and analytics. The API is designed for high performance with AsyncIO, connection pooling, and Redis caching.

**Base URL**: `http://localhost:8000` (development) or your production domain  
**API Version**: v1  
**Documentation**: Available at `/docs` (Swagger UI) and `/redoc` (ReDoc)

## API Architecture

### Core Components
- **FastAPI Framework**: Modern, fast web framework with automatic API documentation
- **AsyncIO**: Asynchronous request handling for high performance
- **Structured Logging**: Comprehensive request/response logging with structlog
- **Rate Limiting**: Protection against abuse with token bucket algorithm
- **CORS Support**: Cross-origin resource sharing for web applications
- **Health Monitoring**: Built-in health checks and metrics

### Security Features
- **Security Headers**: Comprehensive security header middleware
- **Trusted Host Filtering**: Production host validation
- **Request ID Tracking**: Unique request identification for monitoring
- **Exception Handling**: Graceful error handling with structured responses

## Authentication

Currently, most endpoints do not require authentication to support development and integration. Production deployments should implement appropriate authentication middleware.

## API Endpoints

### Health & Monitoring

#### GET /health
**Description**: System health check endpoint  
**Tags**: Health  
**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-08-17T12:00:00Z",
  "version": "1.0.0",
  "database": "connected",
  "redis": "connected"
}
```

#### GET /metrics
**Description**: Prometheus metrics endpoint for monitoring  
**Tags**: Monitoring  
**Response**: Prometheus metrics format

### Talent Management

#### GET /api/v1/talents
**Description**: Retrieve all talents with pagination  
**Tags**: Talents  
**Query Parameters**:
- `skip` (int): Number of records to skip (default: 0)
- `limit` (int): Maximum records to return (default: 100)
- `department` (string): Filter by department
- `skill` (string): Filter by skill

**Response**:
```json
{
  "talents": [
    {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com",
      "department": "Engineering",
      "skills": ["Python", "FastAPI", "PostgreSQL"],
      "status": "active",
      "created_at": "2025-08-17T12:00:00Z"
    }
  ],
  "total": 100,
  "skip": 0,
  "limit": 100
}
```

#### POST /api/v1/talents
**Description**: Create a new talent record  
**Tags**: Talents  
**Request Body**:
```json
{
  "name": "Jane Smith",
  "email": "jane@example.com",
  "department": "Engineering",
  "skills": ["JavaScript", "React", "Node.js"],
  "bio": "Full-stack developer with 5 years experience"
}
```

#### GET /api/v1/talents/{talent_id}
**Description**: Retrieve a specific talent by ID  
**Tags**: Talents  
**Path Parameters**:
- `talent_id` (int): Unique talent identifier

#### PUT /api/v1/talents/{talent_id}
**Description**: Update an existing talent record  
**Tags**: Talents

#### DELETE /api/v1/talents/{talent_id}
**Description**: Delete a talent record  
**Tags**: Talents

### AI Agent Orchestration

#### GET /api/v1/agents
**Description**: List all available AI agents  
**Tags**: AI Agents  
**Response**:
```json
{
  "agents": [
    {
      "id": "ali_chief_of_staff",
      "name": "Ali - Chief of Staff",
      "description": "Master orchestrator and single point of contact",
      "status": "active",
      "capabilities": [
        "Strategic agent selection",
        "Multi-agent coordination",
        "Solution integration"
      ],
      "tools": ["Task", "Read", "Write", "WebSearch"],
      "color": "#4A90E2"
    }
  ],
  "total": 48
}
```

#### POST /api/v1/agents/chat
**Description**: Start a conversation with an AI agent  
**Tags**: AI Agents  
**Request Body**:
```json
{
  "agent_id": "ali_chief_of_staff",
  "message": "Help me analyze our quarterly performance",
  "context": {
    "user_id": "user123",
    "session_id": "session456"
  }
}
```

#### GET /api/v1/agents/signatures
**Description**: Retrieve agent digital signatures for validation  
**Tags**: AI Agents

#### POST /api/v1/agents/validate
**Description**: Validate agent responses and signatures  
**Tags**: AI Agents

### Ali Intelligence System

#### POST /api/v1/agents/ali/query
**Description**: Query Ali's proactive intelligence engine  
**Tags**: Ali Intelligence  
**Request Body**:
```json
{
  "query": "What are the key business risks this quarter?",
  "context": {
    "department": "all",
    "priority": "high"
  }
}
```

#### GET /api/v1/agents/ali/insights
**Description**: Get proactive insights from Ali  
**Tags**: Ali Intelligence

#### POST /api/v1/agents/ali/coordinate
**Description**: Coordinate multi-agent responses through Ali  
**Tags**: Ali Intelligence

### Vector Search & Knowledge

#### POST /api/v1/vector/search
**Description**: Perform semantic search across knowledge base  
**Tags**: Vector Search  
**Request Body**:
```json
{
  "query": "machine learning best practices",
  "filters": {
    "category": "technology",
    "date_range": "2024-2025"
  },
  "limit": 10
}
```

#### POST /api/v1/vector/embed
**Description**: Generate embeddings for text content  
**Tags**: Vector Search  
**Request Body**:
```json
{
  "text": "This is the content to embed",
  "model": "text-embedding-3-small"
}
```

#### POST /api/v1/vector/index
**Description**: Index new content for search  
**Tags**: Vector Search

### AI Provider Settings (v2.1.0)

The AI Provider Settings endpoints allow you to configure how Convergio routes requests between Ollama (local) and Azure OpenAI (cloud) providers.

#### GET /api/v1/settings/ai/mode
**Description**: Get the current AI provider mode configuration
**Tags**: AI Settings
**Response**:
```json
{
  "mode": "ollama_only",
  "strict_mode": true,
  "fallback_enabled": false,
  "primary_provider": "ollama",
  "fallback_provider": null,
  "description": "All AI requests use local Ollama for $0 cost"
}
```

**Provider Modes**:
| Mode | Primary | Fallback | Description |
|------|---------|----------|-------------|
| `ollama_only` | Ollama | None | Local-only, $0 cost |
| `azure_only` | Azure OpenAI | None | Cloud-only, pay-per-use |
| `hybrid` | Ollama | Azure OpenAI | Local-first with cloud fallback |
| `cloud_first` | Azure OpenAI | Ollama | Cloud-first with local fallback |

#### POST /api/v1/settings/ai/mode
**Description**: Update the AI provider mode
**Tags**: AI Settings
**Request Body**:
```json
{
  "mode": "hybrid",
  "strict_mode": false
}
```
**Response**:
```json
{
  "success": true,
  "previous_mode": "ollama_only",
  "new_mode": "hybrid",
  "message": "Provider mode updated successfully"
}
```

#### GET /api/v1/settings/ai/costs
**Description**: Get AI provider cost tracking metrics
**Tags**: AI Settings
**Response**:
```json
{
  "period": "2025-12-28",
  "providers": {
    "ollama": {
      "requests": 1234,
      "tokens": 567890,
      "cost": 0.00,
      "currency": "USD"
    },
    "azure_openai": {
      "requests": 0,
      "tokens": 0,
      "cost": 0.00,
      "currency": "USD"
    }
  },
  "total_cost": 0.00,
  "savings": {
    "estimated_cloud_cost": 45.67,
    "actual_cost": 0.00,
    "saved": 45.67
  }
}
```

#### GET /api/v1/settings/ai/capabilities
**Description**: Get provider capability matrix
**Tags**: AI Settings
**Response**:
```json
{
  "ollama": {
    "available": true,
    "version": "0.4.0",
    "models": ["llama3.2", "codellama", "mistral"],
    "capabilities": {
      "chat": true,
      "function_calling": true,
      "embeddings": true,
      "streaming": true,
      "vision": false
    }
  },
  "azure_openai": {
    "available": true,
    "deployment": "gpt-4o",
    "capabilities": {
      "chat": true,
      "function_calling": true,
      "embeddings": true,
      "streaming": true,
      "vision": true
    }
  }
}
```

#### GET /api/v1/settings/ai/health
**Description**: Check health status of all AI providers
**Tags**: AI Settings
**Response**:
```json
{
  "status": "healthy",
  "providers": {
    "ollama": {
      "status": "healthy",
      "latency_ms": 12,
      "last_check": "2025-12-28T12:00:00Z"
    },
    "azure_openai": {
      "status": "healthy",
      "latency_ms": 145,
      "last_check": "2025-12-28T12:00:00Z"
    }
  },
  "active_provider": "ollama"
}
```

---

### Cost Management & Analytics

#### GET /api/v1/cost-management/usage
**Description**: Get current usage statistics  
**Tags**: Cost Management  
**Response**:
```json
{
  "current_period": {
    "total_cost": 245.67,
    "total_tokens": 1234567,
    "requests": 8901,
    "period_start": "2025-08-01T00:00:00Z",
    "period_end": "2025-08-31T23:59:59Z"
  },
  "by_agent": [
    {
      "agent_id": "ali_chief_of_staff",
      "cost": 45.67,
      "tokens": 234567,
      "requests": 156
    }
  ]
}
```

#### GET /api/v1/cost-management/limits
**Description**: Get current cost limits and thresholds  
**Tags**: Cost Management

#### POST /api/v1/cost-management/alerts
**Description**: Configure cost alerts and notifications  
**Tags**: Cost Management

### Analytics & Insights

#### GET /api/v1/analytics/dashboard
**Description**: Get dashboard metrics and KPIs  
**Tags**: Analytics  
**Response**:
```json
{
  "metrics": {
    "total_conversations": 1234,
    "active_agents": 48,
    "response_time_avg": 2.3,
    "success_rate": 0.987,
    "user_satisfaction": 4.6
  },
  "trends": {
    "daily_usage": [
      {"date": "2025-08-17", "conversations": 67, "cost": 12.34}
    ]
  }
}
```

#### GET /api/v1/analytics/agents
**Description**: Get per-agent analytics and performance metrics  
**Tags**: Analytics

#### GET /api/v1/analytics/usage
**Description**: Get detailed usage analytics  
**Tags**: Analytics

### Workflow Automation (GraphFlow)

#### GET /api/v1/workflows
**Description**: List all available workflows  
**Tags**: Workflows  
**Response**:
```json
{
  "workflows": [
    {
      "id": "workflow_123",
      "name": "Customer Onboarding",
      "description": "Automated customer onboarding process",
      "status": "active",
      "steps": 5,
      "success_rate": 0.95,
      "created_at": "2025-08-17T12:00:00Z"
    }
  ]
}
```

#### POST /api/v1/workflows/generate
**Description**: Generate workflow from natural language description  
**Tags**: Workflows  
**Request Body**:
```json
{
  "description": "Create a workflow for processing customer support tickets",
  "requirements": [
    "Categorize ticket by type",
    "Route to appropriate agent",
    "Track resolution time"
  ]
}
```

#### POST /api/v1/workflows/{workflow_id}/execute
**Description**: Execute a specific workflow  
**Tags**: Workflows

#### GET /api/v1/workflows/{workflow_id}/status
**Description**: Get workflow execution status  
**Tags**: Workflows

### Projects & Client Management

#### GET /api/v1/projects
**Description**: List all projects  
**Tags**: Projects & Clients  
**Query Parameters**:
- `status` (string): Filter by project status
- `client_id` (int): Filter by client
- `skip` (int): Pagination offset
- `limit` (int): Pagination limit

#### POST /api/v1/projects
**Description**: Create a new project  
**Tags**: Projects & Clients

#### GET /api/v1/projects/{project_id}
**Description**: Get project details  
**Tags**: Projects & Clients

#### GET /api/v1/projects/{project_id}/analytics
**Description**: Get project analytics and metrics  
**Tags**: Projects & Clients

### Agent Management

#### POST /api/v1/agent-management/create
**Description**: Create a new AI agent  
**Tags**: Agent Management  
**Request Body**:
```json
{
  "name": "Custom Agent",
  "description": "Specialized agent for custom tasks",
  "capabilities": ["task_automation", "data_analysis"],
  "tools": ["web_search", "database_query"],
  "system_prompt": "You are a specialized agent that..."
}
```

#### PUT /api/v1/agent-management/{agent_id}
**Description**: Update agent configuration  
**Tags**: Agent Management

#### DELETE /api/v1/agent-management/{agent_id}
**Description**: Delete an agent  
**Tags**: Agent Management

#### POST /api/v1/agent-management/{agent_id}/deploy
**Description**: Deploy agent to production  
**Tags**: Agent Management

### Swarm Coordination

#### POST /api/v1/swarm/coordinate
**Description**: Coordinate multiple agents for complex tasks  
**Tags**: Swarm Coordination  
**Request Body**:
```json
{
  "task": "Analyze market trends and create strategic recommendations",
  "agents": ["ali_chief_of_staff", "antonio_strategy_expert", "ava_analytics_virtuoso"],
  "coordination_mode": "collaborative",
  "deadline": "2025-08-20T18:00:00Z"
}
```

#### GET /api/v1/swarm/status/{task_id}
**Description**: Get swarm coordination status  
**Tags**: Swarm Coordination

### Approvals & Human-in-the-Loop

#### GET /api/v1/approvals/pending
**Description**: Get pending approval requests  
**Tags**: Approvals  
**Response**:
```json
{
  "pending_approvals": [
    {
      "id": "approval_123",
      "type": "agent_response",
      "agent_id": "ali_chief_of_staff",
      "content": "Proposed response requiring human review",
      "risk_level": "medium",
      "created_at": "2025-08-17T12:00:00Z"
    }
  ]
}
```

#### POST /api/v1/approvals/{approval_id}/approve
**Description**: Approve a pending request  
**Tags**: Approvals

#### POST /api/v1/approvals/{approval_id}/reject
**Description**: Reject a pending request  
**Tags**: Approvals

### Agent Digital Signatures

#### POST /api/v1/agent-signatures/sign
**Description**: Digitally sign agent responses  
**Tags**: Agent Signatures

#### POST /api/v1/agent-signatures/verify
**Description**: Verify agent signature authenticity  
**Tags**: Agent Signatures

### Component Serialization

#### POST /api/v1/serialization/save
**Description**: Save component state for persistence  
**Tags**: Component Serialization

#### GET /api/v1/serialization/{component_id}
**Description**: Load component state  
**Tags**: Component Serialization

### System Status & Governance

#### GET /api/v1/governance/slo
**Description**: Get Service Level Objective metrics  
**Tags**: Governance  
**Response**:
```json
{
  "slo_metrics": {
    "availability": 99.95,
    "response_time_p95": 1.8,
    "error_rate": 0.02,
    "period": "30d"
  },
  "alerts": [
    {
      "type": "warning",
      "message": "Response time approaching SLO threshold",
      "threshold": 2.0,
      "current": 1.8
    }
  ]
}
```

#### GET /api/v1/governance/rate-limits
**Description**: Get current rate limiting status  
**Tags**: Governance

#### POST /api/v1/governance/runbook/{runbook_id}/execute
**Description**: Execute operational runbook  
**Tags**: Governance

### Telemetry & Monitoring

#### POST /telemetry/events
**Description**: Submit telemetry events  
**Tags**: Telemetry  
**Request Body**:
```json
{
  "event_type": "agent_response",
  "agent_id": "ali_chief_of_staff",
  "duration_ms": 1234,
  "tokens_used": 567,
  "success": true,
  "metadata": {
    "model": "gpt-4",
    "temperature": 0.7
  }
}
```

#### GET /telemetry/metrics
**Description**: Get aggregated telemetry metrics  
**Tags**: Telemetry

### User & API Key Management

#### POST /api/v1/keys
**Description**: Generate new API key  
**Tags**: User Keys

#### GET /api/v1/keys
**Description**: List user's API keys  
**Tags**: User Keys

#### DELETE /api/v1/keys/{key_id}
**Description**: Revoke API key  
**Tags**: User Keys

### Agent Ecosystem Health

#### GET /ecosystem/health
**Description**: Get comprehensive agent ecosystem health  
**Tags**: Agent Ecosystem  
**Response**:
```json
{
  "ecosystem_health": {
    "total_agents": 48,
    "active_agents": 47,
    "healthy_agents": 46,
    "degraded_agents": 1,
    "failed_agents": 0
  },
  "agent_status": [
    {
      "agent_id": "ali_chief_of_staff",
      "status": "healthy",
      "last_response_time": 1.2,
      "success_rate": 0.99
    }
  ]
}
```

#### GET /ecosystem/agents/{agent_id}/health
**Description**: Get specific agent health status  
**Tags**: Agent Ecosystem

### Admin & Maintenance

#### POST /admin/maintenance/vacuum
**Description**: Trigger database vacuum operation  
**Tags**: Admin

#### GET /admin/system/info
**Description**: Get detailed system information  
**Tags**: Admin

#### POST /admin/cache/clear
**Description**: Clear Redis cache  
**Tags**: Admin

## Response Formats

### Standard Success Response
```json
{
  "success": true,
  "data": { /* response data */ },
  "timestamp": "2025-08-17T12:00:00Z",
  "request_id": "req_123456"
}
```

### Standard Error Response
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The provided data is invalid",
    "details": {
      "field": "email",
      "reason": "Invalid email format"
    }
  },
  "timestamp": "2025-08-17T12:00:00Z",
  "request_id": "req_123456"
}
```

### Pagination Response
```json
{
  "data": [ /* array of items */ ],
  "pagination": {
    "total": 1000,
    "skip": 0,
    "limit": 100,
    "has_next": true,
    "has_prev": false
  }
}
```

## HTTP Status Codes

- **200 OK**: Request successful
- **201 Created**: Resource created successfully
- **400 Bad Request**: Invalid request parameters
- **401 Unauthorized**: Authentication required
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **422 Unprocessable Entity**: Validation error
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Server error
- **502 Bad Gateway**: Upstream service error
- **503 Service Unavailable**: Service temporarily unavailable

## Rate Limiting

Rate limiting is implemented using a token bucket algorithm:
- **Default Limit**: 100 requests per 60 seconds per IP
- **Headers**: Response includes rate limit headers
  - `X-RateLimit-Limit`: Request limit per window
  - `X-RateLimit-Remaining`: Remaining requests in window
  - `X-RateLimit-Reset`: Window reset time

## Error Handling

All endpoints implement comprehensive error handling:
- **Validation Errors**: Detailed field-level validation messages
- **Business Logic Errors**: Domain-specific error codes
- **System Errors**: Graceful degradation with error tracking
- **Request Tracing**: Unique request IDs for debugging

## WebSocket Endpoints

### Real-time Agent Communication
**Endpoint**: `ws://localhost:8000/ws/agents/{agent_id}`  
**Description**: Real-time bidirectional communication with AI agents

### Live Metrics Stream
**Endpoint**: `ws://localhost:8000/ws/metrics`  
**Description**: Real-time system metrics and telemetry

### Workflow Status Updates
**Endpoint**: `ws://localhost:8000/ws/workflows/{workflow_id}`  
**Description**: Live workflow execution updates

## SDKs and Client Libraries

### Python SDK
```python
from convergio import ConvergioClient

client = ConvergioClient(base_url="http://localhost:8000")
response = client.agents.chat("ali_chief_of_staff", "Analyze our performance")
```

### JavaScript SDK
```javascript
import { ConvergioClient } from '@convergio/sdk';

const client = new ConvergioClient({ baseUrl: 'http://localhost:8000' });
const response = await client.agents.chat('ali_chief_of_staff', 'Analyze our performance');
```

## Integration Examples

### Agent Conversation Flow
```python
# Start conversation with Ali
response = client.agents.chat(
    agent_id="ali_chief_of_staff",
    message="I need a comprehensive business analysis",
    context={"department": "all", "priority": "high"}
)

# Ali coordinates with specialized agents
coordination_result = client.swarm.coordinate(
    task="comprehensive_business_analysis",
    agents=["antonio_strategy_expert", "ava_analytics_virtuoso", "amy_cfo"],
    coordinator="ali_chief_of_staff"
)

# Monitor progress
status = client.swarm.status(coordination_result.task_id)
```

### Real-time Dashboard Integration
```javascript
// Connect to metrics stream
const ws = new WebSocket('ws://localhost:8000/ws/metrics');

ws.onmessage = (event) => {
  const metrics = JSON.parse(event.data);
  updateDashboard(metrics);
};

// Fetch initial dashboard data
const dashboard = await client.analytics.dashboard();
```

## Performance Considerations

- **Connection Pooling**: Database connections are pooled for optimal performance
- **Async Processing**: All endpoints use AsyncIO for non-blocking operations
- **Caching**: Redis caching for frequently accessed data
- **Pagination**: Large result sets are paginated to prevent memory issues
- **Rate Limiting**: Protects against abuse and ensures fair usage

## Security Best Practices

- **Input Validation**: All inputs are validated against strict schemas
- **SQL Injection Prevention**: Using SQLAlchemy ORM with parameterized queries
- **CORS Configuration**: Properly configured for production environments
- **Security Headers**: Comprehensive security headers applied
- **Error Sanitization**: Internal errors are not exposed in production

## Monitoring and Observability

- **Structured Logging**: All requests/responses logged with context
- **Metrics Collection**: Prometheus metrics for monitoring
- **Distributed Tracing**: Request tracing across services
- **Health Checks**: Comprehensive health monitoring
- **Alerting**: Configurable alerts for critical metrics

---

*Last updated: August 2025 - Convergio FASE 11 Final Documentation*