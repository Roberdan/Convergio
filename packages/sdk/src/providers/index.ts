export type {
  LLMProvider,
  ProviderConfig,
  AzureOpenAIConfig,
  BedrockConfig,
  ChatMessage,
  ChatRequest,
  ChatResponse,
  StreamChunk,
  TokenUsage,
} from './types.js';

export { createOpenAIProvider } from './openai.js';
export { createAnthropicProvider } from './anthropic.js';
export { createAzureOpenAIProvider } from './azure-openai.js';
export { createOllamaProvider } from './ollama.js';
export { createBedrockProvider } from './bedrock.js';

import type { LLMProvider } from './types.js';
import { createOpenAIProvider } from './openai.js';
import { createAnthropicProvider } from './anthropic.js';
import { createAzureOpenAIProvider } from './azure-openai.js';
import { createOllamaProvider } from './ollama.js';
import { createBedrockProvider } from './bedrock.js';

type ProviderName =
  | 'openai'
  | 'anthropic'
  | 'azure-openai'
  | 'ollama'
  | 'bedrock';

/**
 * Create an LLM provider by name, or auto-detect from env vars.
 * Detection order: OPENAI_API_KEY, ANTHROPIC_API_KEY,
 * AZURE_OPENAI_API_KEY, AWS_ACCESS_KEY_ID, fallback Ollama (no key).
 */
export function createProvider(
  name?: ProviderName,
  config?: Record<string, unknown>,
): LLMProvider {
  const resolved = name ?? detectProvider();

  switch (resolved) {
    case 'openai':
      return createOpenAIProvider(config);
    case 'anthropic':
      return createAnthropicProvider(config);
    case 'azure-openai':
      return createAzureOpenAIProvider(config);
    case 'ollama':
      return createOllamaProvider(config);
    case 'bedrock':
      return createBedrockProvider(config);
    default:
      throw new Error(`Unknown provider: ${resolved as string}`);
  }
}

function detectProvider(): ProviderName {
  if (process.env['OPENAI_API_KEY']) return 'openai';
  if (process.env['ANTHROPIC_API_KEY']) return 'anthropic';
  if (process.env['AZURE_OPENAI_API_KEY']) return 'azure-openai';
  if (process.env['AWS_ACCESS_KEY_ID']) return 'bedrock';
  throw new Error(
    'No LLM provider detected. Set one of: OPENAI_API_KEY, ANTHROPIC_API_KEY, AZURE_OPENAI_API_KEY, AWS_ACCESS_KEY_ID, or specify provider name explicitly.',
  );
}
