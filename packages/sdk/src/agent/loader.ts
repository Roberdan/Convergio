import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join, basename, extname } from 'node:path';
import { load as yamlLoad } from 'js-yaml';
import type { AgentConfig, AgentLoadResult } from './types.js';

/** Extract YAML frontmatter from a markdown file */
function parseFrontmatter(content: string): { frontmatter: Record<string, unknown>; body: string } {
  const match = content.match(/^---\n([\s\S]*?)\n---\n?([\s\S]*)$/);
  if (!match) {
    return { frontmatter: {}, body: content };
  }
  const raw = yamlLoad(match[1]);
  const frontmatter = (raw && typeof raw === 'object' && !Array.isArray(raw))
    ? raw as Record<string, unknown>
    : {};
  return { frontmatter, body: match[2].trim() };
}

/** Parse tools field — can be JSON array string or real array */
function parseTools(raw: unknown): string[] {
  if (Array.isArray(raw)) {
    return raw.map(String);
  }
  if (typeof raw === 'string') {
    try {
      const parsed = JSON.parse(raw);
      return Array.isArray(parsed) ? parsed.map(String) : [];
    } catch {
      return raw.split(',').map((s) => s.trim()).filter(Boolean);
    }
  }
  return [];
}

/** Convert frontmatter + body to AgentConfig */
function toAgentConfig(filename: string, frontmatter: Record<string, unknown>, body: string): AgentConfig {
  const id = (frontmatter['agent_id'] as string | undefined)
    ?? (frontmatter['name'] as string | undefined)
    ?? basename(filename, extname(filename));

  return {
    id,
    name: (frontmatter['name'] as string | undefined) ?? id,
    description: (frontmatter['description'] as string | undefined) ?? '',
    tools: parseTools(frontmatter['tools']),
    systemPrompt: body || undefined,
    capabilities: Array.isArray(frontmatter['capabilities'])
      ? (frontmatter['capabilities'] as unknown[]).map(String)
      : undefined,
    model: frontmatter['model'] as string | undefined,
    color: frontmatter['color'] as string | undefined,
    metadata: frontmatter,
  };
}

export class AgentLoader {
  /** Load all agent definition files from a directory (.md and .yaml/.yml) */
  loadFromDirectory(dir: string): AgentLoadResult {
    const agents: AgentConfig[] = [];
    const errors: Array<{ file: string; error: string }> = [];

    let entries: string[];
    try {
      entries = readdirSync(dir);
    } catch (err) {
      return { agents, errors: [{ file: dir, error: String(err) }] };
    }

    for (const entry of entries) {
      const ext = extname(entry).toLowerCase();
      if (!['.md', '.yaml', '.yml'].includes(ext)) continue;

      const fullPath = join(dir, entry);
      try {
        if (statSync(fullPath).isDirectory()) continue;
        const agent = this.loadFromFile(fullPath);
        if (agent) agents.push(agent);
      } catch (err) {
        errors.push({ file: entry, error: String(err) });
      }
    }

    return { agents, errors };
  }

  /** Load a single agent definition file */
  loadFromFile(filePath: string): AgentConfig | null {
    const ext = extname(filePath).toLowerCase();
    const content = readFileSync(filePath, 'utf-8');

    if (ext === '.md') {
      const { frontmatter, body } = parseFrontmatter(content);
      if (!frontmatter['name'] && !frontmatter['agent_id']) return null;
      return toAgentConfig(filePath, frontmatter, body);
    }

    if (ext === '.yaml' || ext === '.yml') {
      const raw = yamlLoad(content);
      if (!raw || typeof raw !== 'object' || Array.isArray(raw)) return null;
      const data = raw as Record<string, unknown>;
      return toAgentConfig(filePath, data, (data['system_prompt'] as string | undefined) ?? '');
    }

    return null;
  }
}
