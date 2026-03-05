import type { ToolDefinition } from '../types.js';

export const jsonTransformTool: ToolDefinition = {
  name: 'json-transform',
  description: 'Transform, filter, or reshape JSON data using a jq-style expression or JSONPath.',
  parameters: {
    type: 'object',
    properties: {
      data: {
        type: 'string',
        description: 'JSON string to transform',
      },
      expression: {
        type: 'string',
        description: 'Transformation expression (jq syntax or JSONPath)',
      },
      outputFormat: {
        type: 'string',
        description: 'Output format: json or text (default: json)',
        enum: ['json', 'text'],
        default: 'json',
      },
    },
    required: ['data', 'expression'],
  },
  execute: async (_params) => {
    throw new Error('NotImplementedError: json-transform requires a jq or JSONPath interpreter');
  },
};
