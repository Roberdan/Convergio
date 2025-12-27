# API Response Format Baseline

**Document Version:** 1.0
**Date:** 2025-12-27
**Purpose:** Document current API response formats to ensure parity during Microsoft Agent Framework migration

---

## Overview

This document captures the exact API request/response formats for all agent-related endpoints in the current AutoGen-based implementation. These formats MUST be preserved during the migration to Microsoft Agent Framework to maintain frontend compatibility.

## Core Endpoints

### 1. POST /api/v1/agents/conversation

**Primary conversation endpoint used by frontend chat interface.**

#### Request Schema

```typescript
interface ConversationRequest {
  message: string;                    // User message
  conversation_id?: string;           // Optional conversation ID for continuity
  user_id?: string;                   // Optional user ID (defaults to "anonymous")
  mode?: string;                      // "autogen" | "graphflow" | "swarm" (default: "autogen")
  context?: {                         // Optional context
    test_mode?: boolean;
    track_cost?: boolean;
    user_api_key?: string;
    target_agent?: string;            // Force specific agent
    agent_name?: string;              // Alias for target_agent
    agent_id?: string;                // Alias for target_agent
    multi_agent_preferred?: boolean;
    rag_limit?: number;
    rag_threshold?: number;
    include_history?: boolean;
    include_knowledge?: boolean;
    [key: string]: any;
  };
}
```

#### Response Schema

```typescript
interface ConversationResponse {
  conversation_id: string;            // Unique conversation identifier
  response: string;                   // Main agent response text
  agents_used: string[];              // List of agent IDs that participated
  turn_count: number;                 // Number of conversation turns
  duration_seconds: number;           // Total execution time in seconds
  cost_breakdown: {                   // Cost details by provider
    [provider: string]: {
      cost: number;                   // Cost in USD
      tokens: number;                 // Total tokens used
    };
  };
  cost: number;                       // Total cost in USD
  timestamp: string;                  // ISO 8601 timestamp
  routing?: string;                   // "single_agent" | "multi_agent" (optional)
  error?: string;                     // Error message if failed (optional)
  blocked?: boolean;                  // True if safety guardian blocked (optional)
}
```

#### Example Response

```json
{
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "response": "I can help you with that. Based on the analysis...",
  "agents_used": ["ali", "data-analyst"],
  "turn_count": 3,
  "duration_seconds": 2.45,
  "cost_breakdown": {
    "openai": {
      "cost": 0.0234,
      "tokens": 1500
    }
  },
  "cost": 0.0234,
  "timestamp": "2025-12-27T10:30:45.123Z",
  "routing": "multi_agent"
}
```

#### Critical Fields to Preserve

- ✅ **response** - Main text response (MANDATORY)
- ✅ **agents_used** - Array of agent names (MANDATORY, can be empty array)
- ✅ **turn_count** - Integer turn count (MANDATORY, minimum 0)
- ✅ **cost** - Total cost as float (MANDATORY for cost tracking tests)
- ✅ **conversation_id** - String ID (MANDATORY)
- ✅ **timestamp** - ISO 8601 string (MANDATORY)

---

### 2. POST /api/v1/agents/group-chat

**Group chat endpoint used by E2E tests for multi-agent scenarios.**

#### Request Schema

```typescript
interface GroupChatRequest {
  message: string;                    // User message
  participants: string[];             // List of agent IDs to participate
  session_id?: string;                // Optional session ID
  max_turns?: number;                 // Maximum conversation turns (default: 10)
  context?: {
    autogen_test?: boolean;           // Enable test mode with deterministic responses
    enable_memory?: boolean;
    enable_tools?: boolean;
    [key: string]: any;
  };
}
```

#### Response Schema

```typescript
interface GroupChatResponse {
  conversation: {
    session_id: string;               // Session identifier
    messages: Array<{                 // Array of conversation messages
      agent: string;                  // Agent name/ID
      content: string;                // Message content
      turn: number;                   // Turn number (1-indexed)
      timestamp: string;              // ISO 8601 timestamp
    }>;
  };
  metrics?: {                         // Optional metrics
    turns: number;                    // Total turns
    participants: string[];           // Unique participants
  };
}
```

#### Example Response

```json
{
  "conversation": {
    "session_id": "550e8400-e29b-41d4-a716-446655440001",
    "messages": [
      {
        "agent": "ali",
        "content": "Turn 1 response from ali. This references prior memory and may use a tool if needed.",
        "turn": 1,
        "timestamp": "2025-12-27T10:30:45.123Z"
      },
      {
        "agent": "data-analyst",
        "content": "Turn 2 response from data-analyst. Memory: recalled key facts.",
        "turn": 2,
        "timestamp": "2025-12-27T10:30:46.456Z"
      }
    ]
  },
  "metrics": {
    "turns": 2,
    "participants": ["ali", "data-analyst"]
  }
}
```

---

### 3. POST /api/v1/agents/conversation/stream

**Streaming conversation initialization endpoint.**

#### Request Schema

```typescript
interface StreamingConversationRequest {
  message: string;                    // User message
  conversation_id?: string;           // Optional conversation ID
  user_id?: string;                   // Optional user ID
  context?: Record<string, any>;      // Optional context
  stream?: boolean;                   // Enable streaming (default: true)
}
```

#### Response Schema

```typescript
interface StreamingConversationResponse {
  stream_id: string;                  // Unique stream identifier
  conversation_id: string;            // Conversation ID
  websocket_url: string;              // WebSocket URL to connect to
  message: string;                    // Instructions for client
}
```

#### Example Response

```json
{
  "stream_id": "stream_550e8400-e29b-41d4-a716-446655440002",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440002",
  "websocket_url": "/api/v1/agents/ws/streaming/stream_550e8400-e29b-41d4-a716-446655440002",
  "message": "Connect to WebSocket URL to receive streaming responses"
}
```

---

### 4. POST /api/v1/agents/orchestrate

**Multi-agent orchestration endpoint with advanced routing.**

#### Request Schema

```typescript
interface OrchestrationRequest {
  message: string;                    // User message
  context?: Record<string, any>;      // Optional context (user_api_key added automatically)
  mode?: string;                      // "adaptive" | "sequential" | "parallel" (default: "adaptive")
  max_agents?: number;                // Maximum agents to use (default: 3)
  require_consensus?: boolean;        // Require agent consensus (default: false)
  conversation_id?: string;           // Optional conversation ID
  user_id?: string;                   // Optional user ID
}
```

#### Response Schema

```typescript
interface AgentExecutionResponse {
  execution_id: string;               // Unique execution identifier
  agent_id: string;                   // Agent ID (or "orchestrator")
  status: string;                     // "completed" | "failed" | "pending"
  result?: any;                       // Orchestration result (varies by mode)
  error?: string;                     // Error message if failed
  duration_ms?: number;               // Execution duration in milliseconds
}
```

#### Example Response

```json
{
  "execution_id": "exec_550e8400-e29b-41d4-a716-446655440003",
  "agent_id": "orchestrator",
  "status": "completed",
  "result": {
    "response": "Analysis complete...",
    "agents_used": ["ali", "data-analyst"],
    "duration_seconds": 2.1
  },
  "duration_ms": 2100
}
```

---

### 5. POST /api/v1/agents/execute

**Direct agent execution endpoint.**

#### Request Schema

```typescript
interface AgentExecutionRequest {
  agent_id: string;                   // Agent identifier (MANDATORY)
  task: string;                       // Task description (MANDATORY)
  parameters?: Record<string, any>;   // Optional parameters (default: {})
  context?: Record<string, any>;      // Optional context (default: {})
  timeout?: number;                   // Timeout in seconds (default: 60)
}
```

#### Response Schema

```typescript
interface AgentExecutionResponse {
  execution_id: string;               // Unique execution identifier
  agent_id: string;                   // Agent ID
  status: string;                     // "completed" | "failed"
  result?: any;                       // Agent execution result
  error?: string;                     // Error message if failed
  duration_ms?: number;               // Execution duration in milliseconds
}
```

#### Example Response

```json
{
  "execution_id": "exec_550e8400-e29b-41d4-a716-446655440004",
  "agent_id": "data-analyst",
  "status": "completed",
  "result": {
    "analysis": "Data shows...",
    "metrics": {}
  },
  "duration_ms": 1850
}
```

---

### 6. POST /api/v1/agents/conversation/save

**Conversation persistence endpoint (used by frontend AutoSave).**

#### Request Schema

```typescript
interface ConversationSaveRequest {
  conversation_id: string;            // Conversation ID (MANDATORY)
  agent_id: string;                   // Agent ID (MANDATORY)
  agent_name?: string;                // Agent display name
  messages: Array<Record<string, any>>; // Conversation messages (MANDATORY)
  user_id?: string;                   // User ID (defaults to "anonymous")
  summary?: string;                   // Conversation summary
}
```

#### Response Schema

```typescript
interface ConversationSaveResponse {
  status: string;                     // "ok" | "error"
  conversation_id: string;            // Conversation ID
}
```

---

### 7. GET /api/v1/agents/conversation/load/{conversation_id}

**Load saved conversation by ID.**

#### Response Schema

```typescript
interface LoadedConversation {
  conversation_id: string;            // Conversation ID
  agent_id: string;                   // Agent ID
  agent_name: string;                 // Agent display name
  messages: Array<Record<string, any>>; // Conversation messages
  user_id: string;                    // User ID
  summary?: string;                   // Conversation summary
  last_activity: string;              // ISO 8601 timestamp
  saved_at: string;                   // ISO 8601 timestamp
}
```

---

### 8. GET /api/v1/agents/conversation/load/latest/{agent_id}

**Load latest conversation for specific agent.**

#### Response Schema

Same as conversation load endpoint above.

---

## WebSocket Endpoints

### 1. WebSocket /api/v1/agents/ws/conversation/{conversation_id}

**Real-time conversation WebSocket.**

#### Connection Parameters

- `conversation_id` (path): Conversation identifier
- `user_id` (query, optional): User identifier

#### Message Types

**Client → Server:**

```typescript
interface WSClientMessage {
  type?: "ping";                      // Ping message
  message?: string;                   // User message
  context?: Record<string, any>;      // Optional context
}
```

**Server → Client:**

```typescript
// System message
interface WSSystemMessage {
  type: "system";
  message: string;                    // System message text
  conversation_id: string;            // Conversation ID
  timestamp: string;                  // ISO 8601 timestamp
}

// Typing indicator
interface WSTypingMessage {
  type: "typing";
  agent: string;                      // Agent name
}

// Response message
interface WSResponseMessage {
  type: "response";
  message: string;                    // Agent response
  agents_used: string[];              // Participating agents
  turn_count: number;                 // Turn count
  timestamp: string;                  // ISO 8601 timestamp
}

// Error message
interface WSErrorMessage {
  type: "error";
  message: string;                    // Error description
}

// Pong message
interface WSPongMessage {
  type: "pong";
}
```

---

### 2. WebSocket /api/v1/agents/ws/streaming/{stream_id}

**Streaming response WebSocket.**

#### Stream Chunks

Server sends text chunks as the agent generates responses. Exact format depends on streaming manager implementation.

---

## Agent Management Endpoints

### GET /api/v1/agents/list

**List all available agents.**

#### Response Schema

```typescript
interface AgentInfo {
  id: string;                         // Agent ID
  name: string;                       // Agent display name
  description: string;                // Agent description
  capabilities: string[];             // Agent capabilities
  status: string;                     // "available" | "busy"
  model?: string;                     // AI model used (optional)
  tools: string[];                    // Available tools
}

type AgentListResponse = AgentInfo[];
```

#### Example Response

```json
[
  {
    "id": "ali",
    "name": "Ali - Chief of Staff",
    "description": "Strategic advisor and project manager",
    "capabilities": ["strategy", "planning", "coordination"],
    "status": "available",
    "model": "gpt-4",
    "tools": ["web_search", "database_query"]
  }
]
```

---

### GET /api/v1/agents/ecosystem

**Get ecosystem status.**

#### Response Schema

```typescript
interface EcosystemStatus {
  total_agents: number;               // Total agents in system
  available_agents: number;           // Available agents
  busy_agents: number;                // Busy agents
  agents: AgentInfo[];                // Detailed agent info
  orchestrator_status: string;        // "healthy" | "unhealthy"
  memory_system_status: string;       // "healthy" | "unhealthy"
  vector_db_status: string;           // "healthy" | "unhealthy"
  redis_status: string;               // "healthy" | "unhealthy"
}
```

---

## Orchestrator Internal Response Format

**These are the internal response formats from the UnifiedOrchestrator that feed into the API responses.**

### Single Agent Execution

```typescript
interface OrchestratorSingleAgentResponse {
  response: string;                   // Agent response text
  agents_used: string[];              // [agent_name] - single element array
  turn_count: number;                 // Always 1 for single agent
  duration_seconds: number;           // 0 (set by caller)
  routing: "single_agent";            // Routing strategy used
  cost_breakdown: {                   // Estimated costs
    total_cost_usd?: number;
    [provider: string]: {
      cost: number;
      tokens: number;
    } | number;
  };
}
```

### Multi-Agent Execution

```typescript
interface OrchestratorMultiAgentResponse {
  response: string;                   // Final consolidated response
  agents_used: string[];              // All participating agent names
  turn_count: number;                 // Number of conversation turns
  duration_seconds: number;           // 0 (set by caller)
  routing: "multi_agent";             // Routing strategy used
  cost_breakdown: {                   // Estimated costs
    total_cost_usd?: number;
    [provider: string]: {
      cost: number;
      tokens: number;
    } | number;
  };
}
```

### Error Response

```typescript
interface OrchestratorErrorResponse {
  response: string;                   // Error description
  agents_used: string[];              // Empty array or ["safety_guardian"]
  turn_count: number;                 // 0
  duration_seconds: number;           // Actual duration
  error: string;                      // Error message
  blocked?: boolean;                  // True if safety blocked
}
```

### Circuit Breaker Response

```typescript
interface CircuitBreakerResponse {
  response: "The system is temporarily unavailable. Please try again in a moment.";
  agents_used: [];                    // Empty array
  turn_count: 0;
  duration_seconds: 0;
  circuit_breaker: "open";
  circuit_status: {
    name: string;
    state: "open" | "closed" | "half_open";
    stats: {
      total_calls: number;
      failed_calls: number;
      successful_calls: number;
      consecutive_failures: number;
      consecutive_successes: number;
      last_failure_time: string | null;
      last_success_time: string | null;
    };
    state_changed_at: string;         // ISO 8601 timestamp
  };
}
```

---

## Critical Compatibility Notes

### 1. Response Field Requirements

**MANDATORY fields that MUST be present in all conversation responses:**

- `response` (string) - Never null, minimum empty string
- `agents_used` (array) - Never null, minimum empty array `[]`
- `turn_count` (number) - Never null, minimum 0
- `conversation_id` (string) - Always present
- `timestamp` (string) - ISO 8601 format

### 2. Cost Tracking

**The cost_breakdown field has a specific structure that tests depend on:**

```typescript
{
  "cost_breakdown": {
    "[provider_name]": {
      "cost": number,    // USD
      "tokens": number   // Total tokens
    }
  }
}
```

**Additionally, a top-level `cost` field is calculated:**
```typescript
{
  "cost": number  // Sum of all provider costs
}
```

### 3. Context Handling

**Special context fields that affect behavior:**

- `test_mode` (boolean) - Enables test-specific behavior
- `track_cost` (boolean) - Enable/disable cost tracking (default: true)
- `target_agent` (string) - Force routing to specific agent
- `multi_agent_preferred` (boolean) - Prefer multi-agent routing
- `autogen_test` (boolean) - Enable deterministic test responses

### 4. Agent Name Format

**Agent IDs use hyphenated format:**
- ✅ `ali-chief-of-staff`
- ✅ `data-analyst`
- ❌ `ali_chief_of_staff` (underscore version handled as fallback)

### 5. Timestamp Format

**All timestamps MUST be ISO 8601 format:**
```
2025-12-27T10:30:45.123Z
```

Generated via: `datetime.now().isoformat()`

### 6. Error Handling

**Errors should return 500 status with structured response:**

```json
{
  "detail": "Conversation failed: [error message]"
}
```

**Orchestrator errors return valid response structure with error field:**

```json
{
  "conversation_id": "...",
  "response": "I encountered an issue processing your request: [error]",
  "agents_used": [],
  "turn_count": 0,
  "duration_seconds": 1.23,
  "error": "[error message]",
  "timestamp": "2025-12-27T10:30:45.123Z"
}
```

---

## Testing Implications

### Test Files That Depend on These Formats

1. **backend/tests/e2e/test_autogen_integration.py**
   - Tests conversation endpoint response structure
   - Validates agents_used array
   - Checks turn_count accuracy
   - Verifies cost tracking

2. **backend/tests/e2e/test_database_cost_tracking.py**
   - Depends on cost_breakdown structure
   - Requires cost field in response
   - Validates cost persistence

3. **backend/tests/e2e/test_agent_proactive_intelligence.py**
   - Validates response content structure
   - Checks for specific response patterns

### Migration Validation Checklist

Before marking migration complete, verify:

- [ ] All response fields match baseline schemas
- [ ] agents_used is always an array (never null)
- [ ] turn_count is always a number (never null)
- [ ] cost_breakdown structure matches exactly
- [ ] Timestamps are ISO 8601 format
- [ ] Error responses maintain structure
- [ ] WebSocket message types preserved
- [ ] Context fields work as expected
- [ ] Agent name format compatibility
- [ ] All E2E tests pass without modification

---

## Appendix: Field Type Reference

| Field | Type | Nullable | Default | Notes |
|-------|------|----------|---------|-------|
| response | string | No | "" | Main response text |
| agents_used | array[string] | No | [] | Agent IDs |
| turn_count | number | No | 0 | Integer >= 0 |
| duration_seconds | number | No | 0 | Float >= 0 |
| cost_breakdown | object | No | {} | Provider costs |
| cost | number | No | 0 | Total USD |
| conversation_id | string | No | - | UUID format |
| timestamp | string | No | - | ISO 8601 |
| error | string | Yes | undefined | Error message |
| routing | string | Yes | undefined | Strategy used |
| blocked | boolean | Yes | undefined | Safety block |

---

**End of Document**

*This baseline must be validated against all migrated endpoints before considering the migration complete.*
