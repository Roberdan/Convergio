export type {
  AgentDefinition,
  AgentToolRef,
  AgentPromptExample,
  AgentSuccessMetrics,
  ValidationResult,
} from './types.js';

export {
  AgentTier,
  AgentCategory,
  AgentStatus,
  AgentProvider,
} from './types.js';

export { validateAgentDefinition } from './validator.js';

// Re-export schema as a parsed JSON object
import schemaJson from './schema.json' with { type: 'json' };
export const agentSchema = schemaJson;
