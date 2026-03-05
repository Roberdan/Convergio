import { watch } from 'node:fs';
import type { AgentConfig, AgentManagerOptions } from './types.js';
import { AgentLoader } from './loader.js';

export class AgentManager {
  private readonly agents = new Map<string, AgentConfig>();
  private watcher: ReturnType<typeof watch> | null = null;
  private readonly loader = new AgentLoader();

  constructor(options: AgentManagerOptions = {}) {
    if (options.definitionsDir) {
      this.loadFromDirectory(options.definitionsDir);
      if (options.watch) {
        this.startWatch(options.definitionsDir);
      }
    }
  }

  /** Register a single agent (throws if duplicate name) */
  register(agent: AgentConfig): void {
    this.agents.set(agent.id, agent);
  }

  /** Get an agent by id */
  get(id: string): AgentConfig | undefined {
    return this.agents.get(id);
  }

  /** List all registered agents */
  list(): AgentConfig[] {
    return Array.from(this.agents.values());
  }

  /** Find agents that have a specific capability */
  getByCapability(capability: string): AgentConfig[] {
    return this.list().filter((a) => a.capabilities?.includes(capability));
  }

  /** Find agents that have a specific tool */
  getByTool(toolName: string): AgentConfig[] {
    return this.list().filter((a) => a.tools.includes(toolName));
  }

  /** Load all agents from a directory, replacing current registry */
  loadFromDirectory(dir: string): { loaded: number; errors: number } {
    const result = this.loader.loadFromDirectory(dir);
    for (const agent of result.agents) {
      this.agents.set(agent.id, agent);
    }
    return { loaded: result.agents.length, errors: result.errors.length };
  }

  /** Stop file watcher if running */
  close(): void {
    this.watcher?.close();
    this.watcher = null;
  }

  private startWatch(dir: string): void {
    this.watcher = watch(dir, { recursive: false }, () => {
      this.agents.clear();
      this.loader.loadFromDirectory(dir).agents.forEach((a) => this.agents.set(a.id, a));
    });
  }
}
