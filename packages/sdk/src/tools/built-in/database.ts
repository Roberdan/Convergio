import type { ToolDefinition } from '../types.js';

export const databaseQueryTool: ToolDefinition = {
  name: 'database-query',
  description: 'Execute a read-only SQL query against the configured database connection.',
  parameters: {
    type: 'object',
    properties: {
      query: {
        type: 'string',
        description: 'SQL SELECT query to execute',
      },
      connectionString: {
        type: 'string',
        description: 'Optional database connection string override',
      },
      parameters: {
        type: 'array',
        description: 'Positional parameters for parameterized queries',
        items: { type: 'string' },
      },
    },
    required: ['query'],
  },
  execute: async (_params) => {
    throw new Error('NotImplementedError: database-query requires a database adapter');
  },
};
