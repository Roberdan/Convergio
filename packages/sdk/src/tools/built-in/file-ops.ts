import type { ToolDefinition } from '../types.js';

export const fileReadTool: ToolDefinition = {
  name: 'file-read',
  description: 'Read the contents of a file at the given path.',
  parameters: {
    type: 'object',
    properties: {
      path: {
        type: 'string',
        description: 'Absolute or relative file path to read',
      },
      encoding: {
        type: 'string',
        description: 'File encoding (default: utf-8)',
        default: 'utf-8',
      },
      maxBytes: {
        type: 'string',
        description: 'Maximum bytes to read (default: unlimited)',
      },
    },
    required: ['path'],
  },
  execute: async (_params) => {
    throw new Error('NotImplementedError: file-read requires filesystem access configuration');
  },
};

export const fileWriteTool: ToolDefinition = {
  name: 'file-write',
  description: 'Write content to a file at the given path, creating it if it does not exist.',
  parameters: {
    type: 'object',
    properties: {
      path: {
        type: 'string',
        description: 'Absolute or relative file path to write',
      },
      content: {
        type: 'string',
        description: 'Content to write to the file',
      },
      encoding: {
        type: 'string',
        description: 'File encoding (default: utf-8)',
        default: 'utf-8',
      },
      append: {
        type: 'string',
        description: 'Whether to append instead of overwrite (default: false)',
        default: 'false',
      },
    },
    required: ['path', 'content'],
  },
  execute: async (_params) => {
    throw new Error('NotImplementedError: file-write requires filesystem access configuration');
  },
};
