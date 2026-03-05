import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import type { ChatRequest } from '../types.js';

// Mock fetch globally
const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);

describe('OpenAI adapter', () => {
  beforeEach(() => {
    vi.stubEnv('OPENAI_API_KEY', 'sk-test-key');
    mockFetch.mockReset();
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it('exports createOpenAIProvider function', async () => {
    const { createOpenAIProvider } = await import('../openai.js');
    expect(typeof createOpenAIProvider).toBe('function');
  });

  it('creates provider with name "openai"', async () => {
    const { createOpenAIProvider } = await import('../openai.js');
    const provider = createOpenAIProvider({ apiKey: 'sk-test' });
    expect(provider.name).toBe('openai');
  });

  it('reads API key from env if not provided in config', async () => {
    const { createOpenAIProvider } = await import('../openai.js');
    const provider = createOpenAIProvider();

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        choices: [{ message: { content: 'hi' } }],
        model: 'gpt-4',
        usage: { prompt_tokens: 5, completion_tokens: 3, total_tokens: 8 },
      }),
    });

    const req: ChatRequest = {
      model: 'gpt-4',
      messages: [{ role: 'user', content: 'hello' }],
    };
    await provider.chat(req);

    const [, options] = mockFetch.mock.calls[0];
    const headers = options.headers as Record<string, string>;
    expect(headers['Authorization']).toBe('Bearer sk-test-key');
  });

  it('chat() sends correct request to OpenAI API', async () => {
    const { createOpenAIProvider } = await import('../openai.js');
    const provider = createOpenAIProvider({ apiKey: 'sk-test' });

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        choices: [{ message: { content: 'response text' } }],
        model: 'gpt-4',
        usage: { prompt_tokens: 10, completion_tokens: 5, total_tokens: 15 },
      }),
    });

    const req: ChatRequest = {
      model: 'gpt-4',
      messages: [{ role: 'user', content: 'hello' }],
      temperature: 0.5,
      maxTokens: 100,
    };
    const res = await provider.chat(req);

    expect(mockFetch).toHaveBeenCalledOnce();
    const [url, options] = mockFetch.mock.calls[0];
    expect(url).toBe('https://api.openai.com/v1/chat/completions');
    expect(options.method).toBe('POST');

    const body = JSON.parse(options.body);
    expect(body.model).toBe('gpt-4');
    expect(body.messages).toEqual([{ role: 'user', content: 'hello' }]);
    expect(body.temperature).toBe(0.5);
    expect(body.max_tokens).toBe(100);
    expect(body.stream).toBeUndefined();

    expect(res.content).toBe('response text');
    expect(res.model).toBe('gpt-4');
    expect(res.usage).toEqual({
      promptTokens: 10,
      completionTokens: 5,
      totalTokens: 15,
    });
  });

  it('chat() throws on API error response', async () => {
    const { createOpenAIProvider } = await import('../openai.js');
    const provider = createOpenAIProvider({ apiKey: 'sk-test' });

    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
      statusText: 'Unauthorized',
      text: async () => 'Invalid API key',
    });

    const req: ChatRequest = {
      model: 'gpt-4',
      messages: [{ role: 'user', content: 'hello' }],
    };

    await expect(provider.chat(req)).rejects.toThrow(/OpenAI API error/);
  });

  it('chat() uses custom baseUrl if provided', async () => {
    const { createOpenAIProvider } = await import('../openai.js');
    const provider = createOpenAIProvider({
      apiKey: 'sk-test',
      baseUrl: 'https://custom.api.com/v1',
    });

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        choices: [{ message: { content: 'hi' } }],
        model: 'gpt-4',
        usage: { prompt_tokens: 5, completion_tokens: 3, total_tokens: 8 },
      }),
    });

    await provider.chat({
      model: 'gpt-4',
      messages: [{ role: 'user', content: 'hi' }],
    });

    const [url] = mockFetch.mock.calls[0];
    expect(url).toBe('https://custom.api.com/v1/chat/completions');
  });

  it('stream() yields delta chunks and done', async () => {
    const { createOpenAIProvider } = await import('../openai.js');
    const provider = createOpenAIProvider({ apiKey: 'sk-test' });

    const lines = [
      'data: {"choices":[{"delta":{"content":"Hello"}}]}',
      'data: {"choices":[{"delta":{"content":" world"}}]}',
      'data: [DONE]',
    ].join('\n');

    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(encoder.encode(lines));
        controller.close();
      },
    });

    mockFetch.mockResolvedValueOnce({
      ok: true,
      body: stream,
    });

    const chunks = [];
    for await (const chunk of provider.stream({
      model: 'gpt-4',
      messages: [{ role: 'user', content: 'hi' }],
    })) {
      chunks.push(chunk);
    }

    expect(chunks).toEqual([
      { type: 'delta', content: 'Hello' },
      { type: 'delta', content: ' world' },
      { type: 'done' },
    ]);
  });
});
