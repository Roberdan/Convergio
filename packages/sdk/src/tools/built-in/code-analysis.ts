import type { ToolDefinition } from '../types.js';

export const codeAnalysisTool: ToolDefinition = {
  name: 'code-analysis',
  description: 'Analyze code for complexity, issues, dependencies, and structure.',
  parameters: {
    type: 'object',
    properties: {
      code: {
        type: 'string',
        description: 'Source code string to analyze',
      },
      language: {
        type: 'string',
        description: 'Programming language (e.g. typescript, python, rust)',
      },
      checks: {
        type: 'array',
        description: 'Analysis checks to run: complexity, deps, security, style',
        items: { type: 'string' },
      },
    },
    required: ['code'],
  },
  execute: async (_params) => {
    throw new Error('NotImplementedError: code-analysis requires a language analysis backend');
  },
};
