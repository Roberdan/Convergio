import type {
  LLMProvider,
  ChatRequest,
  ChatResponse,
  StreamChunk,
  AzureOpenAIConfig,
} from './types.js';
import { readLines } from './stream-utils.js';

const DEFAULT_API_VERSION = '2024-02-01';

export function createAzureOpenAIProvider(
  config?: Partial<AzureOpenAIConfig>,
): LLMProvider {
  const apiKey =
    config?.apiKey ?? process.env['AZURE_OPENAI_API_KEY'] ?? '';
  const endpoint =
    config?.endpoint ?? process.env['AZURE_OPENAI_ENDPOINT'] ?? '';
  const apiVersion = config?.apiVersion ?? DEFAULT_API_VERSION;

  function buildUrl(model: string): string {
    const base = endpoint.replace(/\/$/, '');
    return `${base}/openai/deployments/${model}/chat/completions?api-version=${apiVersion}`;
  }

  function buildHeaders(): Record<string, string> {
    return {
      'Content-Type': 'application/json',
      'api-key': apiKey,
    };
  }

  async function chat(req: ChatRequest): Promise<ChatResponse> {
    const body = {
      messages: req.messages,
      ...(req.temperature !== undefined && { temperature: req.temperature }),
      ...(req.maxTokens !== undefined && { max_tokens: req.maxTokens }),
      ...(req.stop && { stop: req.stop }),
    };

    const res = await fetch(buildUrl(req.model), {
      method: 'POST',
      headers: buildHeaders(),
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(
        `Azure OpenAI API error ${res.status} ${res.statusText}: ${text}`,
      );
    }

    const data = await res.json() as {
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
      messages: req.messages,
      stream: true,
      ...(req.temperature !== undefined && { temperature: req.temperature }),
      ...(req.maxTokens !== undefined && { max_tokens: req.maxTokens }),
      ...(req.stop && { stop: req.stop }),
    };

    const res = await fetch(buildUrl(req.model), {
      method: 'POST',
      headers: buildHeaders(),
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(
        `Azure OpenAI API error ${res.status} ${res.statusText}: ${text}`,
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

  return { name: 'azure-openai', chat, stream };
}
