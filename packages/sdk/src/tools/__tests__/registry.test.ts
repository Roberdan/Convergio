import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ToolRegistry } from '../registry.js';
import { createBuiltInTools } from '../built-in/index.js';
import type { ToolDefinition, ToolResult, ToolContext } from '../types.js';

describe('ToolRegistry', () => {
  let registry: ToolRegistry;

  beforeEach(() => {
    registry = new ToolRegistry();
  });

  describe('register / get / unregister', () => {
    it('registers a tool and retrieves it by name', () => {
      const tool: ToolDefinition = {
        name: 'test-tool',
        description: 'A test tool',
        parameters: { type: 'object', properties: {}, required: [] },
        execute: async () => ({ success: true, data: 'ok' }),
      };
      registry.register(tool);
      expect(registry.get('test-tool')).toBe(tool);
    });

    it('returns undefined for unknown tool', () => {
      expect(registry.get('nonexistent')).toBeUndefined();
    });

    it('unregisters a tool', () => {
      const tool: ToolDefinition = {
        name: 'removable',
        description: 'Removable tool',
        parameters: { type: 'object', properties: {} },
        execute: async () => ({ success: true, data: null }),
      };
      registry.register(tool);
      registry.unregister('removable');
      expect(registry.get('removable')).toBeUndefined();
    });

    it('throws when registering a duplicate tool name', () => {
      const tool: ToolDefinition = {
        name: 'dup',
        description: 'Duplicate',
        parameters: { type: 'object', properties: {} },
        execute: async () => ({ success: true, data: null }),
      };
      registry.register(tool);
      expect(() => registry.register(tool)).toThrow(/already registered/i);
    });

    it('unregistering non-existent tool is a no-op', () => {
      expect(() => registry.unregister('ghost')).not.toThrow();
    });
  });

  describe('list()', () => {
    it('returns built-in tools by default', () => {
      expect(registry.list().length).toBeGreaterThanOrEqual(10);
    });

    it('returns empty list when skipBuiltIns is true', () => {
      const empty = new ToolRegistry({ skipBuiltIns: true });
      expect(empty.list()).toHaveLength(0);
    });

    it('returns all registered tools', () => {
      const t1: ToolDefinition = {
        name: 'a',
        description: 'A',
        parameters: { type: 'object', properties: {} },
        execute: async () => ({ success: true, data: null }),
      };
      const t2: ToolDefinition = {
        name: 'b',
        description: 'B',
        parameters: { type: 'object', properties: {} },
        execute: async () => ({ success: true, data: null }),
      };
      registry.register(t1);
      registry.register(t2);
      const names = registry.list().map((t) => t.name);
      expect(names).toContain('a');
      expect(names).toContain('b');
    });
  });

  describe('built-in tools', () => {
    let registryWithBuiltins: ToolRegistry;

    beforeEach(() => {
      registryWithBuiltins = ToolRegistry.withBuiltIns();
    });

    it('has at least 10 built-in tools', () => {
      expect(registryWithBuiltins.list().length).toBeGreaterThanOrEqual(10);
    });

    it('includes database-query tool', () => {
      expect(registryWithBuiltins.get('database-query')).toBeDefined();
    });

    it('includes web-search tool', () => {
      expect(registryWithBuiltins.get('web-search')).toBeDefined();
    });

    it('includes vector-search tool', () => {
      expect(registryWithBuiltins.get('vector-search')).toBeDefined();
    });

    it('includes file-read tool', () => {
      expect(registryWithBuiltins.get('file-read')).toBeDefined();
    });

    it('includes file-write tool', () => {
      expect(registryWithBuiltins.get('file-write')).toBeDefined();
    });

    it('includes code-analysis tool', () => {
      expect(registryWithBuiltins.get('code-analysis')).toBeDefined();
    });

    it('includes http-request tool', () => {
      expect(registryWithBuiltins.get('http-request')).toBeDefined();
    });

    it('includes json-transform tool', () => {
      expect(registryWithBuiltins.get('json-transform')).toBeDefined();
    });

    it('includes text-extract tool', () => {
      expect(registryWithBuiltins.get('text-extract')).toBeDefined();
    });

    it('includes calculator tool', () => {
      expect(registryWithBuiltins.get('calculator')).toBeDefined();
    });

    it('each built-in tool has a description', () => {
      for (const tool of registryWithBuiltins.list()) {
        expect(tool.description.length).toBeGreaterThan(0);
      }
    });

    it('each built-in tool has a parameters schema', () => {
      for (const tool of registryWithBuiltins.list()) {
        expect(tool.parameters).toBeDefined();
        expect(tool.parameters.type).toBe('object');
      }
    });
  });

  describe('execute()', () => {
    it('returns ToolResult from a successful tool', async () => {
      const tool: ToolDefinition = {
        name: 'echo',
        description: 'Echo tool',
        parameters: { type: 'object', properties: {} },
        execute: async (params) => ({ success: true, data: params }),
      };
      registry.register(tool);
      const result = await registry.execute('echo', { msg: 'hello' });
      expect(result.success).toBe(true);
      expect(result.data).toEqual({ msg: 'hello' });
    });

    it('returns error result when tool throws', async () => {
      const tool: ToolDefinition = {
        name: 'failing',
        description: 'Failing tool',
        parameters: { type: 'object', properties: {} },
        execute: async () => { throw new Error('boom'); },
      };
      registry.register(tool);
      const result = await registry.execute('failing', {});
      expect(result.success).toBe(false);
      expect(result.error).toContain('boom');
    });

    it('returns error result for unknown tool', async () => {
      const result = await registry.execute('unknown-tool', {});
      expect(result.success).toBe(false);
      expect(result.error).toMatch(/not found/i);
    });

    it('times out after configured ms', async () => {
      const tool: ToolDefinition = {
        name: 'slow',
        description: 'Slow tool',
        parameters: { type: 'object', properties: {} },
        execute: async () => {
          await new Promise((resolve) => setTimeout(resolve, 5000));
          return { success: true, data: 'done' };
        },
      };
      registry.register(tool);
      const result = await registry.execute('slow', {}, { timeoutMs: 50 });
      expect(result.success).toBe(false);
      expect(result.error).toMatch(/timeout/i);
    }, 2000);

    it('retries on transient error up to maxRetries', async () => {
      let calls = 0;
      const tool: ToolDefinition = {
        name: 'flaky',
        description: 'Flaky tool',
        parameters: { type: 'object', properties: {} },
        execute: async () => {
          calls++;
          if (calls < 3) throw new Error('transient');
          return { success: true, data: 'recovered' };
        },
      };
      registry.register(tool);
      const result = await registry.execute('flaky', {}, { maxRetries: 2 });
      expect(result.success).toBe(true);
      expect(calls).toBe(3);
    });

    it('fails after exhausting retries', async () => {
      let calls = 0;
      const tool: ToolDefinition = {
        name: 'always-fails',
        description: 'Always failing',
        parameters: { type: 'object', properties: {} },
        execute: async () => {
          calls++;
          throw new Error('persistent error');
        },
      };
      registry.register(tool);
      const result = await registry.execute('always-fails', {}, { maxRetries: 2 });
      expect(result.success).toBe(false);
      expect(calls).toBe(3); // 1 initial + 2 retries
    });
  });

  describe('formatResult()', () => {
    it('formats a successful result as JSON string', () => {
      const result: ToolResult = { success: true, data: { value: 42 } };
      const formatted = ToolRegistry.formatResult(result);
      expect(formatted).toContain('"success": true');
      expect(formatted).toContain('"value": 42');
    });

    it('formats a failure result with error', () => {
      const result: ToolResult = { success: false, data: null, error: 'Something broke' };
      const formatted = ToolRegistry.formatResult(result);
      expect(formatted).toContain('"success": false');
      expect(formatted).toContain('Something broke');
    });
  });
});

describe('createBuiltInTools', () => {
  it('returns an array of tool definitions', () => {
    const tools = createBuiltInTools();
    expect(Array.isArray(tools)).toBe(true);
    expect(tools.length).toBeGreaterThanOrEqual(10);
  });

  it('each tool has name, description, parameters, execute', () => {
    for (const tool of createBuiltInTools()) {
      expect(typeof tool.name).toBe('string');
      expect(typeof tool.description).toBe('string');
      expect(typeof tool.parameters).toBe('object');
      expect(typeof tool.execute).toBe('function');
    }
  });
});

describe('ToolResult type shape', () => {
  it('success result has success:true and data', () => {
    const r: ToolResult = { success: true, data: 'test' };
    expect(r.success).toBe(true);
    expect(r.data).toBe('test');
    expect(r.error).toBeUndefined();
  });

  it('failure result has success:false and error', () => {
    const r: ToolResult = { success: false, data: null, error: 'fail' };
    expect(r.success).toBe(false);
    expect(r.error).toBe('fail');
  });
});
