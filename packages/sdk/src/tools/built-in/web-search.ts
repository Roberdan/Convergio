import type { ToolDefinition } from '../types.js';

export const webSearchTool: ToolDefinition = {
  name: 'web-search',
  description: 'Search the web for information using a query string and return ranked results.',
  parameters: {
    type: 'object',
    properties: {
      query: {
        type: 'string',
        description: 'Search query string',
      },
      maxResults: {
        type: 'string',
        description: 'Maximum number of results to return (default: 10)',
        default: '10',
      },
      language: {
        type: 'string',
        description: 'Language code for results (e.g. en, it)',
        default: 'en',
      },
    },
    required: ['query'],
  },
  execute: async (_params) => {
    throw new Error('NotImplementedError: web-search requires a search provider API key');
  },
};
