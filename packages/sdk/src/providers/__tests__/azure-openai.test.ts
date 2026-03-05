import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import type { ChatRequest } from '../types.js';

const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);

describe('Azure OpenAI adapter', () => {
  beforeEach(() => {
    vi.stubEnv('AZURE_OPENAI_API_KEY', 'az-test-key');
    vi.stubEnv('AZURE_OPENAI_ENDPOINT', 'https://myresource.openai.azure.com');
    mockFetch.mockReset();
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it('exports createAzureOpenAIProvider function', async () => {
    const { createAzureOpenAIProvider } = await import('../azure-openai.js');
    expect(typeof createAzureOpenAIProvider).toBe('function');
  });

  it('creates provider with name "azure-openai"', async () => {
    const { createAzureOpenAIProvider } = await import('../azure-openai.js');
    const provider = createAzureOpenAIProvider({
      apiKey: 'az-test',
      endpoint: 'https://myresource.openai.azure.com',
    });
    expect(provider.name).toBe('azure-openai');
  });

  it('chat() sends request with correct Azure URL format', async () => {
    const { createAzureOpenAIProvider } = await import('../azure-openai.js');
    const provider = createAzureOpenAIProvider({
      apiKey: 'az-test',
      endpoint: 'https://myresource.openai.azure.com',
      apiVersion: '2024-02-01',
    });

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        choices: [{ message: { content: 'azure response' } }],
        model: 'gpt-4',
        usage: { prompt_tokens: 10, completion_tokens: 5, total_tokens: 15 },
      }),
    });

    const req: ChatRequest = {
      model: 'gpt-4',
      messages: [{ role: 'user', content: 'hello' }],
    };
    const res = await provider.chat(req);

    const [url, options] = mockFetch.mock.calls[0];
    expect(url).toContain('myresource.openai.azure.com');
    expect(url).toContain('/openai/deployments/gpt-4/chat/completions');
    expect(url).toContain('api-version=2024-02-01');

    const headers = options.headers as Record<string, string>;
    expect(headers['api-key']).toBe('az-test');

    expect(res.content).toBe('azure response');
  });

  it('chat() reads env vars if config not provided', async () => {
    const { createAzureOpenAIProvider } = await import('../azure-openai.js');
    const provider = createAzureOpenAIProvider();

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        choices: [{ message: { content: 'ok' } }],
        model: 'gpt-4',
        usage: { prompt_tokens: 5, completion_tokens: 2, total_tokens: 7 },
      }),
    });

    await provider.chat({
      model: 'gpt-4',
      messages: [{ role: 'user', content: 'hi' }],
    });

    const [url, options] = mockFetch.mock.calls[0];
    expect(url).toContain('myresource.openai.azure.com');
    expect(options.headers['api-key']).toBe('az-test-key');
  });

  it('chat() throws on API error', async () => {
    const { createAzureOpenAIProvider } = await import('../azure-openai.js');
    const provider = createAzureOpenAIProvider({
      apiKey: 'bad',
      endpoint: 'https://myresource.openai.azure.com',
    });

    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 403,
      statusText: 'Forbidden',
      text: async () => 'Access denied',
    });

    await expect(
      provider.chat({
        model: 'gpt-4',
        messages: [{ role: 'user', content: 'hi' }],
      }),
    ).rejects.toThrow(/Azure OpenAI API error/);
  });

  it('stream() yields delta chunks', async () => {
    const { createAzureOpenAIProvider } = await import('../azure-openai.js');
    const provider = createAzureOpenAIProvider({
      apiKey: 'az-test',
      endpoint: 'https://myresource.openai.azure.com',
    });

    const lines = [
      'data: {"choices":[{"delta":{"content":"Hello"}}]}',
      'data: {"choices":[{"delta":{"content":" Azure"}}]}',
      'data: [DONE]',
    ].join('\n');

    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(encoder.encode(lines));
        controller.close();
      },
    });

    mockFetch.mockResolvedValueOnce({ ok: true, body: stream });

    const chunks = [];
    for await (const chunk of provider.stream({
      model: 'gpt-4',
      messages: [{ role: 'user', content: 'hi' }],
    })) {
      chunks.push(chunk);
    }

    expect(chunks).toEqual([
      { type: 'delta', content: 'Hello' },
      { type: 'delta', content: ' Azure' },
      { type: 'done' },
    ]);
  });
});
