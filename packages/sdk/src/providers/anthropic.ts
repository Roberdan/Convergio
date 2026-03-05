import type {
  LLMProvider,
  ChatRequest,
  ChatResponse,
  StreamChunk,
  ProviderConfig,
} from './types.js';
import { readLines } from './stream-utils.js';

const DEFAULT_BASE_URL = 'https://api.anthropic.com/v1';
const DEFAULT_MAX_TOKENS = 4096;
const API_VERSION = '2023-06-01';

export function createAnthropicProvider(
  config?: Partial<ProviderConfig>,
): LLMProvider {
  const apiKey = config?.apiKey ?? process.env['ANTHROPIC_API_KEY'] ?? '';
  const baseUrl = config?.baseUrl ?? DEFAULT_BASE_URL;

  function buildHeaders(): Record<string, string> {
    return {
      'Content-Type': 'application/json',
      'x-api-key': apiKey,
      'anthropic-version': API_VERSION,
    };
  }

  function extractSystemMessage(
    messages: ChatRequest['messages'],
  ): { system?: string; messages: ChatRequest['messages'] } {
    const systemMsg = messages.find((m) => m.role === 'system');
    const nonSystemMsgs = messages.filter((m) => m.role !== 'system');
    return {
      system: systemMsg?.content,
      messages: nonSystemMsgs,
    };
  }

  async function chat(req: ChatRequest): Promise<ChatResponse> {
    const { system, messages } = extractSystemMessage(req.messages);
    const body = {
      model: req.model,
      messages,
      max_tokens: req.maxTokens ?? DEFAULT_MAX_TOKENS,
      ...(system && { system }),
      ...(req.temperature !== undefined && { temperature: req.temperature }),
      ...(req.stop && { stop_sequences: req.stop }),
    };

    const res = await fetch(`${baseUrl}/messages`, {
      method: 'POST',
      headers: buildHeaders(),
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(
        `Anthropic API error ${res.status} ${res.statusText}: ${text}`,
      );
    }

    const data = (await res.json()) as {
      content: Array<{ type: string; text: string }>;
      model: string;
      usage: { input_tokens: number; output_tokens: number };
    };
    const content = data.content
      .filter((b) => b.type === 'text')
      .map((b) => b.text)
      .join('');

    return {
      content,
      model: data.model,
      usage: {
        promptTokens: data.usage.input_tokens,
        completionTokens: data.usage.output_tokens,
        totalTokens: data.usage.input_tokens + data.usage.output_tokens,
      },
    };
  }

  async function* stream(req: ChatRequest): AsyncIterable<StreamChunk> {
    const { system, messages } = extractSystemMessage(req.messages);
    const body = {
      model: req.model,
      messages,
      max_tokens: req.maxTokens ?? DEFAULT_MAX_TOKENS,
      stream: true,
      ...(system && { system }),
      ...(req.temperature !== undefined && { temperature: req.temperature }),
      ...(req.stop && { stop_sequences: req.stop }),
    };

    const res = await fetch(`${baseUrl}/messages`, {
      method: 'POST',
      headers: buildHeaders(),
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(
        `Anthropic API error ${res.status} ${res.statusText}: ${text}`,
      );
    }

    for await (const line of readLines(res.body!)) {
      if (line.startsWith('data: ')) {
        const json = JSON.parse(line.slice(6));
        if (json.type === 'content_block_delta') {
          yield { type: 'delta', content: json.delta.text };
        } else if (json.type === 'message_stop') {
          yield { type: 'done' };
          return;
        }
      }
    }
  }

  return { name: 'anthropic', chat, stream };
}
