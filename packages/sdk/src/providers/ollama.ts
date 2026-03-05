import type {
  LLMProvider,
  ChatRequest,
  ChatResponse,
  StreamChunk,
  ProviderConfig,
} from './types.js';
import { readLines } from './stream-utils.js';

const DEFAULT_BASE_URL = 'http://localhost:11434';

export function createOllamaProvider(
  config?: Partial<ProviderConfig>,
): LLMProvider {
  const baseUrl =
    config?.baseUrl ??
    process.env['OLLAMA_BASE_URL'] ??
    DEFAULT_BASE_URL;

  async function chat(req: ChatRequest): Promise<ChatResponse> {
    const body = {
      model: req.model,
      messages: req.messages,
      stream: false,
      options: {
        ...(req.temperature !== undefined && {
          temperature: req.temperature,
        }),
        ...(req.maxTokens !== undefined && { num_predict: req.maxTokens }),
      },
    };

    const res = await fetch(`${baseUrl}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(
        `Ollama API error ${res.status} ${res.statusText}: ${text}`,
      );
    }

    const data = await res.json() as {
      message: { content: string };
      model: string;
      prompt_eval_count?: number;
      eval_count?: number;
    };
    return {
      content: data.message.content,
      model: data.model,
      usage: {
        promptTokens: data.prompt_eval_count ?? 0,
        completionTokens: data.eval_count ?? 0,
        totalTokens: (data.prompt_eval_count ?? 0) + (data.eval_count ?? 0),
      },
    };
  }

  async function* stream(req: ChatRequest): AsyncIterable<StreamChunk> {
    const body = {
      model: req.model,
      messages: req.messages,
      stream: true,
      options: {
        ...(req.temperature !== undefined && {
          temperature: req.temperature,
        }),
        ...(req.maxTokens !== undefined && { num_predict: req.maxTokens }),
      },
    };

    const res = await fetch(`${baseUrl}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(
        `Ollama API error ${res.status} ${res.statusText}: ${text}`,
      );
    }

    for await (const line of readLines(res.body!)) {
      const json = JSON.parse(line);
      if (json.done) {
        yield { type: 'done' };
        return;
      }
      if (json.message?.content) {
        yield { type: 'delta', content: json.message.content };
      }
    }
  }

  return { name: 'ollama', chat, stream };
}
