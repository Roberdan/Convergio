import type { ToolDefinition } from '../types.js';

export const httpRequestTool: ToolDefinition = {
  name: 'http-request',
  description: 'Make an HTTP request to an external URL and return the response body and status.',
  parameters: {
    type: 'object',
    properties: {
      url: {
        type: 'string',
        description: 'Target URL for the HTTP request',
      },
      method: {
        type: 'string',
        description: 'HTTP method: GET, POST, PUT, PATCH, DELETE',
        enum: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'],
        default: 'GET',
      },
      headers: {
        type: 'object',
        description: 'HTTP headers as key-value pairs',
        properties: {},
        additionalProperties: true,
      },
      body: {
        type: 'string',
        description: 'Request body (for POST/PUT/PATCH)',
      },
      timeoutMs: {
        type: 'string',
        description: 'Request timeout in milliseconds (default: 10000)',
        default: '10000',
      },
    },
    required: ['url'],
  },
  execute: async (_params) => {
    throw new Error('NotImplementedError: http-request requires network access configuration');
  },
};
