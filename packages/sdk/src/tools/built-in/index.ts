import type { ToolDefinition } from '../types.js';
import { databaseQueryTool } from './database.js';
import { webSearchTool } from './web-search.js';
import { vectorSearchTool } from './vector-search.js';
import { fileReadTool, fileWriteTool } from './file-ops.js';
import { codeAnalysisTool } from './code-analysis.js';
import { httpRequestTool } from './http-request.js';
import { jsonTransformTool } from './json-transform.js';
import { textExtractTool } from './text-extract.js';
import { calculatorTool } from './calculator.js';

export {
  databaseQueryTool,
  webSearchTool,
  vectorSearchTool,
  fileReadTool,
  fileWriteTool,
  codeAnalysisTool,
  httpRequestTool,
  jsonTransformTool,
  textExtractTool,
  calculatorTool,
};

export function createBuiltInTools(): ToolDefinition[] {
  return [
    databaseQueryTool,
    webSearchTool,
    vectorSearchTool,
    fileReadTool,
    fileWriteTool,
    codeAnalysisTool,
    httpRequestTool,
    jsonTransformTool,
    textExtractTool,
    calculatorTool,
  ];
}
