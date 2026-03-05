import { describe, it, expect, beforeAll } from 'vitest';
import { fileURLToPath } from 'node:url';
import { join, dirname } from 'node:path';
import { mkdirSync, writeFileSync } from 'node:fs';
import { AgentManager } from '../manager.js';
import type { AgentConfig } from '../types.js';

const __dir = dirname(fileURLToPath(import.meta.url));
const fixtureDir = join(__dir, '__fixtures__');

const makeAgent = (id: string, overrides: Partial<AgentConfig> = {}): AgentConfig => ({
  id,
  name: id,
  description: `Agent ${id}`,
  tools: ['Task'],
  metadata: {},
  ...overrides,
});

beforeAll(() => {
  mkdirSync(fixtureDir, { recursive: true });
  writeFileSync(
    join(fixtureDir, 'mgr-agent.md'),
    `---\nname: mgr-agent\ndescription: Manager test agent\ntools: ["Bash"]\n---\nSystem prompt.`,
  );
});

describe('AgentManager', () => {
  describe('register / get / list', () => {
    it('registers and retrieves an agent by id', () => {
      const mgr = new AgentManager();
      const agent = makeAgent('alpha');
      mgr.register(agent);
      expect(mgr.get('alpha')).toBe(agent);
    });

    it('returns undefined for unknown id', () => {
      const mgr = new AgentManager();
      expect(mgr.get('ghost')).toBeUndefined();
    });

    it('list() returns all registered agents', () => {
      const mgr = new AgentManager();
      mgr.register(makeAgent('a'));
      mgr.register(makeAgent('b'));
      expect(mgr.list()).toHaveLength(2);
    });

    it('overwrites existing agent on re-register', () => {
      const mgr = new AgentManager();
      mgr.register(makeAgent('dup', { description: 'first' }));
      mgr.register(makeAgent('dup', { description: 'second' }));
      expect(mgr.get('dup')!.description).toBe('second');
    });
  });

  describe('getByCapability()', () => {
    it('filters agents by capability', () => {
      const mgr = new AgentManager();
      mgr.register(makeAgent('analyst', { capabilities: ['search', 'analyze'] }));
      mgr.register(makeAgent('writer', { capabilities: ['write'] }));
      const result = mgr.getByCapability('search');
      expect(result).toHaveLength(1);
      expect(result[0].id).toBe('analyst');
    });

    it('returns empty when no agents have capability', () => {
      const mgr = new AgentManager();
      mgr.register(makeAgent('basic'));
      expect(mgr.getByCapability('rare-skill')).toHaveLength(0);
    });
  });

  describe('getByTool()', () => {
    it('filters agents by tool name', () => {
      const mgr = new AgentManager();
      mgr.register(makeAgent('tool-user', { tools: ['Bash', 'Read'] }));
      mgr.register(makeAgent('no-bash', { tools: ['Read'] }));
      const result = mgr.getByTool('Bash');
      expect(result).toHaveLength(1);
      expect(result[0].id).toBe('tool-user');
    });
  });

  describe('loadFromDirectory()', () => {
    it('loads agents from fixture directory', () => {
      const mgr = new AgentManager();
      const { loaded, errors } = mgr.loadFromDirectory(fixtureDir);
      expect(loaded).toBeGreaterThanOrEqual(1);
      expect(errors).toBe(0);
    });

    it('populates manager after loadFromDirectory', () => {
      const mgr = new AgentManager({ definitionsDir: fixtureDir });
      expect(mgr.list().length).toBeGreaterThanOrEqual(1);
    });
  });

  describe('close()', () => {
    it('close() does not throw', () => {
      const mgr = new AgentManager();
      expect(() => mgr.close()).not.toThrow();
    });
  });
});
