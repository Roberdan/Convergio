import { describe, it, expect, beforeAll } from 'vitest';
import { fileURLToPath } from 'node:url';
import { join, dirname } from 'node:path';
import { mkdirSync, writeFileSync, rmSync } from 'node:fs';
import { AgentLoader } from '../loader.js';

const __dir = dirname(fileURLToPath(import.meta.url));
const fixtureDir = join(__dir, '__fixtures__');

const MD_AGENT = `---
name: test-agent
description: A test agent for unit tests
tools: ["Task", "Read", "Write"]
color: "#FF0000"
---

You are Test Agent. Help users with testing.`;

const MD_AGENT_TOOLS_STRING = `---
name: tools-agent
description: Agent with tools as string
tools: '["Alpha", "Beta"]'
---`;

const YAML_AGENT = `
agent_id: yaml-agent
name: yaml-agent
description: A YAML-defined agent
tools:
  - database-query
  - web-search
system_prompt: You are a YAML agent.
capabilities:
  - search
  - query
`;

const NO_FRONTMATTER = `# Just markdown\n\nNo frontmatter here.`;

beforeAll(() => {
  mkdirSync(fixtureDir, { recursive: true });
  writeFileSync(join(fixtureDir, 'test-agent.md'), MD_AGENT);
  writeFileSync(join(fixtureDir, 'tools-agent.md'), MD_AGENT_TOOLS_STRING);
  writeFileSync(join(fixtureDir, 'yaml-agent.yaml'), YAML_AGENT);
  writeFileSync(join(fixtureDir, 'no-frontmatter.md'), NO_FRONTMATTER);
  writeFileSync(join(fixtureDir, 'ignore.txt'), 'not an agent');
});

describe('AgentLoader', () => {
  const loader = new AgentLoader();

  describe('loadFromFile()', () => {
    it('parses .md file with frontmatter', () => {
      const agent = loader.loadFromFile(join(fixtureDir, 'test-agent.md'));
      expect(agent).not.toBeNull();
      expect(agent!.name).toBe('test-agent');
      expect(agent!.description).toBe('A test agent for unit tests');
      expect(agent!.tools).toEqual(['Task', 'Read', 'Write']);
      expect(agent!.color).toBe('#FF0000');
      expect(agent!.systemPrompt).toContain('You are Test Agent');
    });

    it('parses .md with tools as JSON string', () => {
      const agent = loader.loadFromFile(join(fixtureDir, 'tools-agent.md'));
      expect(agent).not.toBeNull();
      expect(agent!.tools).toEqual(['Alpha', 'Beta']);
    });

    it('parses .yaml file', () => {
      const agent = loader.loadFromFile(join(fixtureDir, 'yaml-agent.yaml'));
      expect(agent).not.toBeNull();
      expect(agent!.id).toBe('yaml-agent');
      expect(agent!.tools).toEqual(['database-query', 'web-search']);
      expect(agent!.capabilities).toEqual(['search', 'query']);
      expect(agent!.systemPrompt).toContain('YAML agent');
    });

    it('returns null for .md without frontmatter name', () => {
      const agent = loader.loadFromFile(join(fixtureDir, 'no-frontmatter.md'));
      expect(agent).toBeNull();
    });
  });

  describe('loadFromDirectory()', () => {
    it('loads all valid agent files from directory', () => {
      const result = loader.loadFromDirectory(fixtureDir);
      expect(result.agents.length).toBeGreaterThanOrEqual(3);
      expect(result.errors).toHaveLength(0);
    });

    it('ignores non-.md/.yaml files', () => {
      const result = loader.loadFromDirectory(fixtureDir);
      const names = result.agents.map((a) => a.name);
      expect(names).not.toContain('ignore');
    });

    it('returns error for non-existent directory', () => {
      const result = loader.loadFromDirectory('/non/existent/path');
      expect(result.agents).toHaveLength(0);
      expect(result.errors.length).toBeGreaterThan(0);
    });
  });
});
