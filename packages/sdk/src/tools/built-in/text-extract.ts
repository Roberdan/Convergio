import type { ToolDefinition } from '../types.js';

export const textExtractTool: ToolDefinition = {
  name: 'text-extract',
  description: 'Extract structured text content from HTML, PDF, or plain text documents.',
  parameters: {
    type: 'object',
    properties: {
      content: {
        type: 'string',
        description: 'Raw content string (HTML, PDF base64, or plain text)',
      },
      format: {
        type: 'string',
        description: 'Input format: html, pdf, text',
        enum: ['html', 'pdf', 'text'],
        default: 'text',
      },
      selector: {
        type: 'string',
        description: 'CSS selector to extract specific element (for HTML format)',
      },
      stripTags: {
        type: 'string',
        description: 'Whether to strip HTML tags from output (default: true)',
        default: 'true',
      },
    },
    required: ['content'],
  },
  execute: async (_params) => {
    throw new Error('NotImplementedError: text-extract requires a document parsing backend');
  },
};
