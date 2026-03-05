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

// Re-export schema as a parsed JSON object (fs.readFileSync for Node 20 compatibility)
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { resolve, dirname } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
export const agentSchema = JSON.parse(
  readFileSync(resolve(__dirname, 'schema.json'), 'utf-8'),
) as Record<string, unknown>;
