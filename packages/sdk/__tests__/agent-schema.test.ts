import { describe, it, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const SCHEMA_DIR = resolve(__dirname, '../src/agent-schema');

describe('agent-schema types', () => {
  it('exports AgentDefinition interface', async () => {
    const mod = await import('../src/agent-schema/index.js');
    expect(mod).toHaveProperty('AgentTier');
    expect(mod).toHaveProperty('AgentCategory');
    expect(mod).toHaveProperty('AgentStatus');
  });
});

describe('agent-schema JSON schema', () => {
  it('schema.json exists and is valid JSON', () => {
    const raw = readFileSync(resolve(SCHEMA_DIR, 'schema.json'), 'utf-8');
    const schema = JSON.parse(raw);
    expect(schema.$schema).toContain('json-schema.org');
    expect(schema.title).toBe('Convergio Agent Definition');
    expect(schema.type).toBe('object');
  });

  it('schema requires mandatory fields', () => {
    const raw = readFileSync(resolve(SCHEMA_DIR, 'schema.json'), 'utf-8');
    const schema = JSON.parse(raw);
    const required = schema.required as string[];
    expect(required).toContain('agent_id');
    expect(required).toContain('name');
    expect(required).toContain('description');
    expect(required).toContain('capabilities');
  });

  it('schema supports multi-provider (C-07)', () => {
    const raw = readFileSync(resolve(SCHEMA_DIR, 'schema.json'), 'utf-8');
    const schema = JSON.parse(raw);
    const provider = schema.properties.provider;
    expect(provider).toBeDefined();
    expect(provider.type).toBe('string');
    const providerEnum = provider.enum as string[];
    expect(providerEnum.length).toBeGreaterThan(1);
    expect(providerEnum).toContain('openai');
    expect(providerEnum).toContain('anthropic');
  });

  it('schema supports model field (not locked to a single model)', () => {
    const raw = readFileSync(resolve(SCHEMA_DIR, 'schema.json'), 'utf-8');
    const schema = JSON.parse(raw);
    expect(schema.properties.model).toBeDefined();
    expect(schema.properties.model.type).toBe('string');
  });

  it('schema supports tools array', () => {
    const raw = readFileSync(resolve(SCHEMA_DIR, 'schema.json'), 'utf-8');
    const schema = JSON.parse(raw);
    expect(schema.properties.tools).toBeDefined();
    expect(schema.properties.tools.type).toBe('array');
  });

  it('schema supports temperature and max_tokens', () => {
    const raw = readFileSync(resolve(SCHEMA_DIR, 'schema.json'), 'utf-8');
    const schema = JSON.parse(raw);
    expect(schema.properties.temperature).toBeDefined();
    expect(schema.properties.temperature.type).toBe('number');
    expect(schema.properties.max_tokens).toBeDefined();
    expect(schema.properties.max_tokens.type).toBe('integer');
  });
});

describe('agent-schema validator', () => {
  it('exports validateAgentDefinition function', async () => {
    const mod = await import('../src/agent-schema/index.js');
    expect(typeof mod.validateAgentDefinition).toBe('function');
  });

  it('validates a correct agent definition', async () => {
    const { validateAgentDefinition } = await import(
      '../src/agent-schema/index.js'
    );
    const valid = {
      agent_id: 'test_agent',
      name: 'Test Agent',
      description: 'A test agent for validation',
      role: 'Test specialist',
      tier: 'specialist',
      category: 'technical',
      capabilities: ['testing', 'validation'],
      system_prompt: 'You are a test agent that validates schema definitions work correctly.',
      tools: ['Read', 'Write'],
      provider: 'anthropic',
      model: 'claude-3-sonnet',
      temperature: 0.7,
      max_tokens: 4096,
    };
    const result = validateAgentDefinition(valid);
    expect(result.valid).toBe(true);
    expect(result.errors).toHaveLength(0);
  });

  it('rejects missing required fields', async () => {
    const { validateAgentDefinition } = await import(
      '../src/agent-schema/index.js'
    );
    const invalid = {
      name: 'Incomplete Agent',
    };
    const result = validateAgentDefinition(invalid);
    expect(result.valid).toBe(false);
    expect(result.errors.length).toBeGreaterThan(0);
  });

  it('rejects invalid agent_id pattern', async () => {
    const { validateAgentDefinition } = await import(
      '../src/agent-schema/index.js'
    );
    const invalid = {
      agent_id: 'INVALID-ID',
      name: 'Bad ID Agent',
      description: 'Agent with bad ID',
      role: 'Test',
      tier: 'specialist',
      category: 'technical',
      capabilities: ['test'],
      system_prompt: 'You are a test agent that validates schema definitions work correctly.',
    };
    const result = validateAgentDefinition(invalid);
    expect(result.valid).toBe(false);
    expect(result.errors.some((e: string) => e.includes('agent_id'))).toBe(
      true
    );
  });

  it('rejects invalid tier value', async () => {
    const { validateAgentDefinition } = await import(
      '../src/agent-schema/index.js'
    );
    const invalid = {
      agent_id: 'test_agent',
      name: 'Bad Tier Agent',
      description: 'Agent with invalid tier',
      role: 'Test',
      tier: 'supreme_overlord',
      category: 'technical',
      capabilities: ['test'],
      system_prompt: 'You are a test agent that validates schema definitions work correctly.',
    };
    const result = validateAgentDefinition(invalid);
    expect(result.valid).toBe(false);
    expect(result.errors.some((e: string) => e.includes('tier'))).toBe(true);
  });

  it('rejects invalid provider value', async () => {
    const { validateAgentDefinition } = await import(
      '../src/agent-schema/index.js'
    );
    const invalid = {
      agent_id: 'test_agent',
      name: 'Bad Provider Agent',
      description: 'Agent with invalid provider',
      role: 'Test',
      tier: 'specialist',
      category: 'technical',
      capabilities: ['test'],
      system_prompt: 'You are a test agent that validates schema definitions work correctly.',
      provider: 'invalid_provider_xyz',
    };
    const result = validateAgentDefinition(invalid);
    expect(result.valid).toBe(false);
    expect(result.errors.some((e: string) => e.includes('provider'))).toBe(
      true
    );
  });

  it('rejects temperature out of range', async () => {
    const { validateAgentDefinition } = await import(
      '../src/agent-schema/index.js'
    );
    const invalid = {
      agent_id: 'test_agent',
      name: 'Bad Temp Agent',
      description: 'Agent with bad temperature',
      role: 'Test',
      tier: 'specialist',
      category: 'technical',
      capabilities: ['test'],
      system_prompt: 'You are a test agent that validates schema definitions work correctly.',
      temperature: 5.0,
    };
    const result = validateAgentDefinition(invalid);
    expect(result.valid).toBe(false);
    expect(
      result.errors.some((e: string) => e.includes('temperature'))
    ).toBe(true);
  });

  it('rejects empty capabilities array', async () => {
    const { validateAgentDefinition } = await import(
      '../src/agent-schema/index.js'
    );
    const invalid = {
      agent_id: 'test_agent',
      name: 'No Caps Agent',
      description: 'Agent with empty capabilities',
      role: 'Test',
      tier: 'specialist',
      category: 'technical',
      capabilities: [],
      system_prompt: 'You are a test agent that validates schema definitions work correctly.',
    };
    const result = validateAgentDefinition(invalid);
    expect(result.valid).toBe(false);
    expect(
      result.errors.some((e: string) => e.includes('capabilities'))
    ).toBe(true);
  });

  it('accepts minimal valid definition (required fields only)', async () => {
    const { validateAgentDefinition } = await import(
      '../src/agent-schema/index.js'
    );
    const minimal = {
      agent_id: 'minimal_agent',
      name: 'Minimal Agent',
      description: 'A minimal valid agent',
      role: 'Minimal test role',
      tier: 'assistant',
      category: 'operations',
      capabilities: ['basic'],
      system_prompt: 'You are a minimal agent created for testing the validation logic.',
    };
    const result = validateAgentDefinition(minimal);
    expect(result.valid).toBe(true);
    expect(result.errors).toHaveLength(0);
  });
});

describe('agent-schema index exports', () => {
  it('exports schema as JSON object', async () => {
    const mod = await import('../src/agent-schema/index.js');
    expect(mod.agentSchema).toBeDefined();
    expect(mod.agentSchema.title).toBe('Convergio Agent Definition');
  });

  it('exports validation result type-guard', async () => {
    const mod = await import('../src/agent-schema/index.js');
    expect(typeof mod.validateAgentDefinition).toBe('function');
  });
});
