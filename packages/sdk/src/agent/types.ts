/** AgentConfig: parsed from .md frontmatter or YAML definition files */
export interface AgentConfig {
  /** Unique identifier (derived from filename if not in frontmatter) */
  id: string;
  name: string;
  description: string;
  /** Tool names the agent can use */
  tools: string[];
  /** Optional system prompt / instructions body */
  systemPrompt?: string;
  /** Optional capabilities tags */
  capabilities?: string[];
  /** Optional model override */
  model?: string;
  /** Optional color for UI */
  color?: string;
  /** Raw metadata from frontmatter */
  metadata: Record<string, unknown>;
}

export interface AgentLoadResult {
  agents: AgentConfig[];
  errors: Array<{ file: string; error: string }>;
}

export interface AgentManagerOptions {
  /** Directory to load agents from on init */
  definitionsDir?: string;
  /** Enable hot-reload via fs.watch */
  watch?: boolean;
}
