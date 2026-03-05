import type { AgentDefinition, ValidationResult } from './types.js';
import {
  AgentTier,
  AgentCategory,
  AgentStatus,
  AgentProvider,
} from './types.js';

const AGENT_ID_RE = /^[a-z][a-z0-9_-]*$/;
const VERSION_RE = /^\d+\.\d+\.\d+$/;
const COLOR_RE = /^#[0-9A-Fa-f]{6}$/;

function pushIf(errors: string[], cond: boolean, msg: string): void {
  if (cond) errors.push(msg);
}

/**
 * Validates an unknown value against the Convergio Agent Definition schema.
 * Returns { valid, errors } without external dependencies.
 */
export function validateAgentDefinition(
  input: unknown,
): ValidationResult {
  const errors: string[] = [];

  if (typeof input !== 'object' || input === null || Array.isArray(input)) {
    return { valid: false, errors: ['Input must be a non-null object'] };
  }

  const def = input as Record<string, unknown>;

  // Required string fields
  validateRequiredString(def, 'agent_id', errors);
  validateRequiredString(def, 'name', errors);
  validateRequiredString(def, 'description', errors);
  validateRequiredString(def, 'role', errors);
  validateRequiredString(def, 'system_prompt', errors);

  // agent_id pattern
  if (typeof def.agent_id === 'string' && !AGENT_ID_RE.test(def.agent_id)) {
    errors.push('agent_id must match pattern ^[a-z][a-z0-9_-]*$');
  }

  // system_prompt min length
  if (typeof def.system_prompt === 'string' && def.system_prompt.length < 20) {
    errors.push('system_prompt must be at least 20 characters');
  }

  // Enum fields
  validateEnum(def, 'tier', AgentTier as unknown as string[], errors);
  validateEnum(def, 'category', AgentCategory as unknown as string[], errors);
  validateOptionalEnum(def, 'status', AgentStatus as unknown as string[], errors);
  validateOptionalEnum(def, 'provider', AgentProvider as unknown as string[], errors);

  // capabilities: required, non-empty array of strings
  validateCapabilities(def, errors);

  // Optional numeric ranges
  validateOptionalRange(def, 'temperature', 0, 2, errors);
  validateOptionalInteger(def, 'max_tokens', 1, 1_000_000, errors);
  validateOptionalInteger(def, 'max_context_tokens', 1000, 2_000_000, errors);
  validateOptionalRange(def, 'cost_per_interaction', 0, 100, errors);

  // Optional pattern fields
  validateOptionalPattern(def, 'version', VERSION_RE, 'semver (x.y.z)', errors);
  validateOptionalPattern(def, 'color', COLOR_RE, 'hex color (#RRGGBB)', errors);

  // Optional string fields
  validateOptionalString(def, 'model', errors);
  validateOptionalString(def, 'author', errors);
  validateOptionalString(def, 'instructions', errors);

  // Optional string arrays
  validateOptionalStringArray(def, 'tools', errors);
  validateOptionalStringArray(def, 'dependencies', errors);
  validateOptionalStringArray(def, 'tags', errors);
  validateOptionalStringArray(def, 'constraints', errors);

  return { valid: errors.length === 0, errors };
}

function validateRequiredString(
  def: Record<string, unknown>,
  field: string,
  errors: string[],
): void {
  if (def[field] === undefined || def[field] === null) {
    errors.push(`${field} is required`);
  } else if (typeof def[field] !== 'string') {
    errors.push(`${field} must be a string`);
  } else if ((def[field] as string).length === 0) {
    errors.push(`${field} must not be empty`);
  }
}

function validateEnum(
  def: Record<string, unknown>,
  field: string,
  allowed: string[],
  errors: string[],
): void {
  if (def[field] === undefined || def[field] === null) {
    errors.push(`${field} is required`);
  } else if (!allowed.includes(def[field] as string)) {
    errors.push(`${field} must be one of: ${allowed.join(', ')}`);
  }
}

function validateOptionalEnum(
  def: Record<string, unknown>,
  field: string,
  allowed: string[],
  errors: string[],
): void {
  if (def[field] !== undefined && !allowed.includes(def[field] as string)) {
    errors.push(`${field} must be one of: ${allowed.join(', ')}`);
  }
}

function validateCapabilities(
  def: Record<string, unknown>,
  errors: string[],
): void {
  if (!Array.isArray(def.capabilities)) {
    errors.push('capabilities is required and must be an array');
    return;
  }
  if (def.capabilities.length === 0) {
    errors.push('capabilities must have at least 1 item');
    return;
  }
  for (const cap of def.capabilities) {
    pushIf(errors, typeof cap !== 'string', 'Each capability must be a string');
  }
}

function validateOptionalRange(
  def: Record<string, unknown>,
  field: string,
  min: number,
  max: number,
  errors: string[],
): void {
  if (def[field] === undefined) return;
  const val = def[field];
  if (typeof val !== 'number' || val < min || val > max) {
    errors.push(`${field} must be a number between ${min} and ${max}`);
  }
}

function validateOptionalInteger(
  def: Record<string, unknown>,
  field: string,
  min: number,
  max: number,
  errors: string[],
): void {
  if (def[field] === undefined) return;
  const val = def[field];
  if (typeof val !== 'number' || !Number.isInteger(val) || val < min || val > max) {
    errors.push(`${field} must be an integer between ${min} and ${max}`);
  }
}

function validateOptionalPattern(
  def: Record<string, unknown>,
  field: string,
  pattern: RegExp,
  label: string,
  errors: string[],
): void {
  if (def[field] === undefined) return;
  if (typeof def[field] !== 'string' || !pattern.test(def[field] as string)) {
    errors.push(`${field} must match ${label}`);
  }
}

function validateOptionalString(
  def: Record<string, unknown>,
  field: string,
  errors: string[],
): void {
  if (def[field] !== undefined && typeof def[field] !== 'string') {
    errors.push(`${field} must be a string`);
  }
}

function validateOptionalStringArray(
  def: Record<string, unknown>,
  field: string,
  errors: string[],
): void {
  if (def[field] === undefined) return;
  if (!Array.isArray(def[field])) {
    errors.push(`${field} must be an array`);
    return;
  }
  // tools can contain objects or strings, skip strict string check for tools
  if (field === 'tools') return;
  for (const item of def[field] as unknown[]) {
    pushIf(errors, typeof item !== 'string', `Each item in ${field} must be a string`);
  }
}
