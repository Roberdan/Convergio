export interface JSONSchema {
  type: string;
  properties?: Record<string, JSONSchemaProperty>;
  required?: string[];
  additionalProperties?: boolean;
  description?: string;
}

export interface JSONSchemaProperty {
  type: string;
  description?: string;
  enum?: unknown[];
  items?: JSONSchemaProperty;
  default?: unknown;
  properties?: Record<string, JSONSchemaProperty>;
  additionalProperties?: boolean | JSONSchemaProperty;
}

export interface ToolContext {
  agentId?: string;
  sessionId?: string;
  metadata?: Record<string, unknown>;
}

export interface ToolResult {
  success: boolean;
  data: unknown;
  error?: string;
}

export interface ToolDefinition {
  name: string;
  description: string;
  parameters: JSONSchema;
  execute: (params: Record<string, unknown>, context?: ToolContext) => Promise<ToolResult>;
}

export interface ExecuteOptions {
  timeoutMs?: number;
  maxRetries?: number;
  context?: ToolContext;
}
