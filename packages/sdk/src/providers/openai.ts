import type {
  LLMProvider,
  ChatRequest,
  ChatResponse,
  StreamChunk,
  ProviderConfig,
} from './types.js';
import { readLines } from './stream-utils.js';

const DEFAULT_BASE_URL = 'https://api.openai.com/v1';

export function createOpenAIProvider(
  config?: Partial<ProviderConfig>,
): LLMProvider {
  const apiKey = config?.apiKey ?? process.env['OPENAI_API_KEY'] ?? '';
  const baseUrl = config?.baseUrl ?? DEFAULT_BASE_URL;

  function buildHeaders(): Record<string, string> {
    return {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${apiKey}`,
    };
  }

  async function chat(req: ChatRequest): Promise<ChatResponse> {
    const body = {
      model: req.model,
      messages: req.messages,
      ...(req.temperature !== undefined && { temperature: req.temperature }),
      ...(req.maxTokens !== undefined && { max_tokens: req.maxTokens }),
      ...(req.stop && { stop: req.stop }),
    };

    const res = await fetch(`${baseUrl}/chat/completions`, {
      method: 'POST',
      headers: buildHeaders(),
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(
        `OpenAI API error ${res.status} ${res.statusText}: ${text}`,
      );
    }

    const data = (await res.json()) as {
      choices: Array<{ message: { content: string } }>;
      model: string;
      usage: { prompt_tokens: number; completion_tokens: number; total_tokens: number };
    };
    return {
      content: data.choices[0].message.content,
      model: data.model,
      usage: {
        promptTokens: data.usage.prompt_tokens,
        completionTokens: data.usage.completion_tokens,
        totalTokens: data.usage.total_tokens,
      },
    };
  }

  async function* stream(req: ChatRequest): AsyncIterable<StreamChunk> {
    const body = {
      model: req.model,
      messages: req.messages,
      stream: true,
      ...(req.temperature !== undefined && { temperature: req.temperature }),
      ...(req.maxTokens !== undefined && { max_tokens: req.maxTokens }),
      ...(req.stop && { stop: req.stop }),
    };

    const res = await fetch(`${baseUrl}/chat/completions`, {
      method: 'POST',
      headers: buildHeaders(),
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(
        `OpenAI API error ${res.status} ${res.statusText}: ${text}`,
      );
    }

    for await (const line of readLines(res.body!)) {
      if (line.startsWith('data: [DONE]')) {
        yield { type: 'done' };
        return;
      }
      if (line.startsWith('data: ')) {
        const json = JSON.parse(line.slice(6));
        const content = json.choices?.[0]?.delta?.content;
        if (content) {
          yield { type: 'delta', content };
        }
      }
    }
  }

  return { name: 'openai', chat, stream };
}
