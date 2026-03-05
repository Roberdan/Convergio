import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import type { ChatRequest } from '../types.js';

const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);

describe('Ollama adapter', () => {
  beforeEach(() => {
    mockFetch.mockReset();
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it('exports createOllamaProvider function', async () => {
    const { createOllamaProvider } = await import('../ollama.js');
    expect(typeof createOllamaProvider).toBe('function');
  });

  it('creates provider with name "ollama"', async () => {
    const { createOllamaProvider } = await import('../ollama.js');
    const provider = createOllamaProvider();
    expect(provider.name).toBe('ollama');
  });

  it('defaults baseUrl to http://localhost:11434', async () => {
    const { createOllamaProvider } = await import('../ollama.js');
    const provider = createOllamaProvider();

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        message: { content: 'local response' },
        model: 'llama3',
      }),
    });

    await provider.chat({
      model: 'llama3',
      messages: [{ role: 'user', content: 'hi' }],
    });

    const [url] = mockFetch.mock.calls[0];
    expect(url).toBe('http://localhost:11434/api/chat');
  });

  it('uses OLLAMA_BASE_URL env var if set', async () => {
    vi.stubEnv('OLLAMA_BASE_URL', 'http://gpu-server:11434');
    const { createOllamaProvider } = await import('../ollama.js');
    const provider = createOllamaProvider();

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        message: { content: 'ok' },
        model: 'llama3',
      }),
    });

    await provider.chat({
      model: 'llama3',
      messages: [{ role: 'user', content: 'hi' }],
    });

    const [url] = mockFetch.mock.calls[0];
    expect(url).toBe('http://gpu-server:11434/api/chat');
  });

  it('chat() sends correct Ollama API request', async () => {
    const { createOllamaProvider } = await import('../ollama.js');
    const provider = createOllamaProvider({ baseUrl: 'http://local:11434' });

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        message: { content: 'ollama response' },
        model: 'llama3',
        prompt_eval_count: 10,
        eval_count: 5,
      }),
    });

    const req: ChatRequest = {
      model: 'llama3',
      messages: [{ role: 'user', content: 'hello' }],
      temperature: 0.8,
    };
    const res = await provider.chat(req);

    const [url, options] = mockFetch.mock.calls[0];
    expect(url).toBe('http://local:11434/api/chat');

    const body = JSON.parse(options.body);
    expect(body.model).toBe('llama3');
    expect(body.messages).toEqual([{ role: 'user', content: 'hello' }]);
    expect(body.stream).toBe(false);
    expect(body.options.temperature).toBe(0.8);

    expect(res.content).toBe('ollama response');
    expect(res.model).toBe('llama3');
  });

  it('chat() throws on API error', async () => {
    const { createOllamaProvider } = await import('../ollama.js');
    const provider = createOllamaProvider();

    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
      text: async () => 'model not found',
    });

    await expect(
      provider.chat({
        model: 'nonexistent',
        messages: [{ role: 'user', content: 'hi' }],
      }),
    ).rejects.toThrow(/Ollama API error/);
  });

  it('stream() yields NDJSON chunks from Ollama', async () => {
    const { createOllamaProvider } = await import('../ollama.js');
    const provider = createOllamaProvider();

    const lines = [
      JSON.stringify({ message: { content: 'Hello' }, done: false }),
      JSON.stringify({ message: { content: ' local' }, done: false }),
      JSON.stringify({ message: { content: '' }, done: true }),
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
      model: 'llama3',
      messages: [{ role: 'user', content: 'hi' }],
    })) {
      chunks.push(chunk);
    }

    expect(chunks).toEqual([
      { type: 'delta', content: 'Hello' },
      { type: 'delta', content: ' local' },
      { type: 'done' },
    ]);
  });
});
