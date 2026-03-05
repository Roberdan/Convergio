import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import type { ChatRequest } from '../types.js';

const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);

describe('Bedrock adapter', () => {
  beforeEach(() => {
    vi.stubEnv('AWS_ACCESS_KEY_ID', 'AKIATEST');
    vi.stubEnv('AWS_SECRET_ACCESS_KEY', 'secret-test');
    vi.stubEnv('AWS_REGION', 'us-east-1');
    mockFetch.mockReset();
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it('exports createBedrockProvider function', async () => {
    const { createBedrockProvider } = await import('../bedrock.js');
    expect(typeof createBedrockProvider).toBe('function');
  });

  it('creates provider with name "bedrock"', async () => {
    const { createBedrockProvider } = await import('../bedrock.js');
    const provider = createBedrockProvider({
      accessKeyId: 'AKIA',
      secretAccessKey: 'secret',
      region: 'us-east-1',
    });
    expect(provider.name).toBe('bedrock');
  });

  it('chat() sends request to Bedrock converse endpoint', async () => {
    const { createBedrockProvider } = await import('../bedrock.js');
    const provider = createBedrockProvider({
      accessKeyId: 'AKIA',
      secretAccessKey: 'secret',
      region: 'us-east-1',
    });

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        output: { message: { content: [{ text: 'bedrock response' }] } },
        usage: { inputTokens: 10, outputTokens: 5, totalTokens: 15 },
      }),
    });

    const req: ChatRequest = {
      model: 'anthropic.claude-3-sonnet-20240229-v1:0',
      messages: [{ role: 'user', content: 'hello' }],
      maxTokens: 512,
    };
    const res = await provider.chat(req);

    const [url, options] = mockFetch.mock.calls[0];
    expect(url).toContain('bedrock-runtime.us-east-1.amazonaws.com');
    expect(url).toContain('/model/');
    expect(url).toContain('/converse');
    expect(options.method).toBe('POST');

    expect(res.content).toBe('bedrock response');
    expect(res.usage.promptTokens).toBe(10);
    expect(res.usage.completionTokens).toBe(5);
  });

  it('chat() reads env vars if config not provided', async () => {
    const { createBedrockProvider } = await import('../bedrock.js');
    const provider = createBedrockProvider();

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        output: { message: { content: [{ text: 'ok' }] } },
        usage: { inputTokens: 5, outputTokens: 2, totalTokens: 7 },
      }),
    });

    await provider.chat({
      model: 'anthropic.claude-3-sonnet-20240229-v1:0',
      messages: [{ role: 'user', content: 'hi' }],
    });

    expect(mockFetch).toHaveBeenCalledOnce();
    const [url] = mockFetch.mock.calls[0];
    expect(url).toContain('us-east-1');
  });

  it('chat() throws on API error', async () => {
    const { createBedrockProvider } = await import('../bedrock.js');
    const provider = createBedrockProvider({
      accessKeyId: 'AKIA',
      secretAccessKey: 'bad',
      region: 'us-east-1',
    });

    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 403,
      statusText: 'Forbidden',
      text: async () => 'Access denied',
    });

    await expect(
      provider.chat({
        model: 'anthropic.claude-3-sonnet-20240229-v1:0',
        messages: [{ role: 'user', content: 'hi' }],
      }),
    ).rejects.toThrow(/Bedrock API error/);
  });

  it('stream() yields chunks from Bedrock event stream', async () => {
    const { createBedrockProvider } = await import('../bedrock.js');
    const provider = createBedrockProvider({
      accessKeyId: 'AKIA',
      secretAccessKey: 'secret',
      region: 'us-east-1',
    });

    const lines = [
      JSON.stringify({ contentBlockDelta: { delta: { text: 'Hello' } } }),
      JSON.stringify({ contentBlockDelta: { delta: { text: ' AWS' } } }),
      JSON.stringify({ messageStop: {} }),
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
      model: 'anthropic.claude-3-sonnet-20240229-v1:0',
      messages: [{ role: 'user', content: 'hi' }],
    })) {
      chunks.push(chunk);
    }

    expect(chunks).toEqual([
      { type: 'delta', content: 'Hello' },
      { type: 'delta', content: ' AWS' },
      { type: 'done' },
    ]);
  });
});
