import type { ToolDefinition, ToolResult, ExecuteOptions } from './types.js';
import { createBuiltInTools } from './built-in/index.js';

const DEFAULT_TIMEOUT_MS = 30_000;
const DEFAULT_MAX_RETRIES = 2;

export class ToolRegistry {
  private readonly tools = new Map<string, ToolDefinition>();

  constructor(options: { skipBuiltIns?: boolean } = {}) {
    if (!options.skipBuiltIns) {
      for (const tool of createBuiltInTools()) {
        this.tools.set(tool.name, tool);
      }
    }
  }

  static withBuiltIns(): ToolRegistry {
    return new ToolRegistry();
  }

  register(tool: ToolDefinition): void {
    if (this.tools.has(tool.name)) {
      throw new Error(`Tool '${tool.name}' already registered`);
    }
    this.tools.set(tool.name, tool);
  }

  unregister(name: string): void {
    this.tools.delete(name);
  }

  get(name: string): ToolDefinition | undefined {
    return this.tools.get(name);
  }

  list(): ToolDefinition[] {
    return Array.from(this.tools.values());
  }

  async execute(
    name: string,
    params: Record<string, unknown>,
    options: ExecuteOptions = {},
  ): Promise<ToolResult> {
    const tool = this.tools.get(name);
    if (!tool) {
      return { success: false, data: null, error: `Tool '${name}' not found` };
    }

    const timeoutMs = options.timeoutMs ?? DEFAULT_TIMEOUT_MS;
    const maxRetries = options.maxRetries ?? DEFAULT_MAX_RETRIES;
    const context = options.context;

    let lastError: Error | undefined;

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        const result = await Promise.race([
          tool.execute(params, context),
          new Promise<never>((_, reject) =>
            setTimeout(() => reject(new Error(`Tool execution timeout after ${timeoutMs}ms`)), timeoutMs),
          ),
        ]);
        return result;
      } catch (err) {
        lastError = err instanceof Error ? err : new Error(String(err));
        if (lastError.message.toLowerCase().includes('timeout')) {
          return { success: false, data: null, error: lastError.message };
        }
        if (attempt < maxRetries) {
          continue;
        }
      }
    }

    return {
      success: false,
      data: null,
      error: lastError?.message ?? 'Unknown error',
    };
  }

  static formatResult(result: ToolResult): string {
    return JSON.stringify(result, null, 2);
  }
}
