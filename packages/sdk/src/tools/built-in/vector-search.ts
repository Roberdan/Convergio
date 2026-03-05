import type { ToolDefinition } from '../types.js';

export const vectorSearchTool: ToolDefinition = {
  name: 'vector-search',
  description: 'Perform semantic similarity search over a vector store using an embedding query.',
  parameters: {
    type: 'object',
    properties: {
      query: {
        type: 'string',
        description: 'Natural language query to embed and search',
      },
      collection: {
        type: 'string',
        description: 'Vector store collection or namespace name',
      },
      topK: {
        type: 'string',
        description: 'Number of top results to return (default: 5)',
        default: '5',
      },
      threshold: {
        type: 'string',
        description: 'Minimum similarity score threshold (0-1)',
        default: '0.7',
      },
    },
    required: ['query'],
  },
  execute: async (_params) => {
    throw new Error('NotImplementedError: vector-search requires a vector store adapter');
  },
};
