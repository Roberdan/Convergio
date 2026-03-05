import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import type { ChatRequest } from '../types.js';

const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);

describe('Anthropic adapter', () => {
  beforeEach(() => {
    vi.stubEnv('ANTHROPIC_API_KEY', 'sk-ant-test');
    mockFetch.mockReset();
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it('exports createAnthropicProvider function', async () => {
    const { createAnthropicProvider } = await import('../anthropic.js');
    expect(typeof createAnthropicProvider).toBe('function');
  });

  it('creates provider with name "anthropic"', async () => {
    const { createAnthropicProvider } = await import('../anthropic.js');
    const provider = createAnthropicProvider({ apiKey: 'sk-ant-test' });
    expect(provider.name).toBe('anthropic');
  });

  it('chat() sends correct request to Anthropic Messages API', async () => {
    const { createAnthropicProvider } = await import('../anthropic.js');
    const provider = createAnthropicProvider({ apiKey: 'sk-ant-test' });

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        content: [{ type: 'text', text: 'response' }],
        model: 'claude-sonnet-4-20250514',
        usage: { input_tokens: 10, output_tokens: 5 },
      }),
    });

    const req: ChatRequest = {
      model: 'claude-sonnet-4-20250514',
      messages: [{ role: 'user', content: 'hello' }],
      maxTokens: 1024,
    };
    const res = await provider.chat(req);

    const [url, options] = mockFetch.mock.calls[0];
    expect(url).toBe('https://api.anthropic.com/v1/messages');
    expect(options.method).toBe('POST');

    const headers = options.headers as Record<string, string>;
    expect(headers['x-api-key']).toBe('sk-ant-test');
    expect(headers['anthropic-version']).toBe('2023-06-01');

    const body = JSON.parse(options.body);
    expect(body.model).toBe('claude-sonnet-4-20250514');
    expect(body.messages).toEqual([{ role: 'user', content: 'hello' }]);
    expect(body.max_tokens).toBe(1024);

    expect(res.content).toBe('response');
    expect(res.model).toBe('claude-sonnet-4-20250514');
    expect(res.usage).toEqual({
      promptTokens: 10,
      completionTokens: 5,
      totalTokens: 15,
    });
  });

  it('chat() extracts system message from messages array', async () => {
    const { createAnthropicProvider } = await import('../anthropic.js');
    const provider = createAnthropicProvider({ apiKey: 'sk-ant-test' });

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        content: [{ type: 'text', text: 'ok' }],
        model: 'claude-sonnet-4-20250514',
        usage: { input_tokens: 8, output_tokens: 2 },
      }),
    });

    await provider.chat({
      model: 'claude-sonnet-4-20250514',
      messages: [
        { role: 'system', content: 'You are helpful' },
        { role: 'user', content: 'hi' },
      ],
    });

    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.system).toBe('You are helpful');
    expect(body.messages).toEqual([{ role: 'user', content: 'hi' }]);
  });

  it('chat() defaults maxTokens to 4096 for Anthropic', async () => {
    const { createAnthropicProvider } = await import('../anthropic.js');
    const provider = createAnthropicProvider({ apiKey: 'sk-ant-test' });

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        content: [{ type: 'text', text: 'ok' }],
        model: 'claude-sonnet-4-20250514',
        usage: { input_tokens: 5, output_tokens: 2 },
      }),
    });

    await provider.chat({
      model: 'claude-sonnet-4-20250514',
      messages: [{ role: 'user', content: 'hi' }],
    });

    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.max_tokens).toBe(4096);
  });

  it('chat() throws on API error', async () => {
    const { createAnthropicProvider } = await import('../anthropic.js');
    const provider = createAnthropicProvider({ apiKey: 'bad-key' });

    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
      statusText: 'Unauthorized',
      text: async () => 'Invalid API key',
    });

    await expect(
      provider.chat({
        model: 'claude-sonnet-4-20250514',
        messages: [{ role: 'user', content: 'hi' }],
      }),
    ).rejects.toThrow(/Anthropic API error/);
  });

  it('stream() yields delta chunks from SSE', async () => {
    const { createAnthropicProvider } = await import('../anthropic.js');
    const provider = createAnthropicProvider({ apiKey: 'sk-ant-test' });

    const lines = [
      'event: content_block_delta',
      'data: {"type":"content_block_delta","delta":{"type":"text_delta","text":"Hi"}}',
      '',
      'event: content_block_delta',
      'data: {"type":"content_block_delta","delta":{"type":"text_delta","text":" there"}}',
      '',
      'event: message_stop',
      'data: {"type":"message_stop"}',
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
      model: 'claude-sonnet-4-20250514',
      messages: [{ role: 'user', content: 'hi' }],
    })) {
      chunks.push(chunk);
    }

    expect(chunks).toEqual([
      { type: 'delta', content: 'Hi' },
      { type: 'delta', content: ' there' },
      { type: 'done' },
    ]);
  });
});
