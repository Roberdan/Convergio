/** Valid organizational tiers for agents */
export const AgentTier = [
  'executive',
  'director',
  'manager',
  'specialist',
  'assistant',
] as const;
export type AgentTier = (typeof AgentTier)[number];

/** Valid expertise categories */
export const AgentCategory = [
  'strategic',
  'financial',
  'technical',
  'marketing',
  'operations',
  'creative',
  'security',
  'hr',
  'legal',
  'analytics',
] as const;
export type AgentCategory = (typeof AgentCategory)[number];

/** Agent lifecycle status */
export const AgentStatus = [
  'active',
  'beta',
  'deprecated',
  'disabled',
] as const;
export type AgentStatus = (typeof AgentStatus)[number];

/** Multi-provider support (C-07: NEVER lock to single vendor) */
export const AgentProvider = [
  'openai',
  'anthropic',
  'google',
  'mistral',
  'ollama',
  'azure',
  'custom',
] as const;
export type AgentProvider = (typeof AgentProvider)[number];

/** Tool reference within an agent definition */
export interface AgentToolRef {
  name: string;
  description?: string;
  required?: boolean;
}

/** Few-shot prompt example */
export interface AgentPromptExample {
  user: string;
  assistant: string;
}

/** Success metrics for agent performance */
export interface AgentSuccessMetrics {
  accuracy?: number;
  response_time_ms?: number;
  user_satisfaction?: number;
}

/**
 * Unified Agent Definition (C-08: single source of truth).
 * Generates CLI config, .claude/agents/*.md, and API schema.
 */
export interface AgentDefinition {
  agent_id: string;
  name: string;
  description: string;
  role: string;
  tier: AgentTier;
  category: AgentCategory;
  capabilities: string[];
  system_prompt: string;

  // Optional fields
  tools?: string[] | AgentToolRef[];
  dependencies?: string[];
  tags?: string[];
  provider?: AgentProvider;
  model?: string;
  temperature?: number;
  max_tokens?: number;
  max_context_tokens?: number;
  cost_per_interaction?: number;
  prompt_examples?: AgentPromptExample[];
  constraints?: string[];
  success_metrics?: AgentSuccessMetrics;
  version?: string;
  status?: AgentStatus;
  color?: string;
  author?: string;
  created_at?: string;
  updated_at?: string;
  instructions?: string;
}

/** Result of validating an agent definition */
export interface ValidationResult {
  valid: boolean;
  errors: string[];
}
