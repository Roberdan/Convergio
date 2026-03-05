import type { ToolDefinition, ToolResult } from '../types.js';

function safeEval(expression: string): number {
  const sanitized = expression.replace(/[^0-9+\-*/.() ]/g, '');
  if (sanitized !== expression.replace(/\s+/g, ' ').trim()) {
    throw new Error('Expression contains invalid characters');
  }
  // eslint-disable-next-line no-new-func
  const result = Function(`"use strict"; return (${sanitized})`)() as unknown;
  if (typeof result !== 'number' || !Number.isFinite(result)) {
    throw new Error('Expression did not produce a finite number');
  }
  return result;
}

export const calculatorTool: ToolDefinition = {
  name: 'calculator',
  description: 'Evaluate a mathematical expression and return the numeric result.',
  parameters: {
    type: 'object',
    properties: {
      expression: {
        type: 'string',
        description: 'Mathematical expression to evaluate (e.g. "2 + 3 * 4")',
      },
    },
    required: ['expression'],
  },
  execute: async (params): Promise<ToolResult> => {
    const expression = params['expression'];
    if (typeof expression !== 'string' || expression.trim().length === 0) {
      return { success: false, data: null, error: 'expression must be a non-empty string' };
    }
    try {
      const result = safeEval(expression);
      return { success: true, data: { result, expression } };
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      return { success: false, data: null, error: `Calculation failed: ${msg}` };
    }
  },
};
