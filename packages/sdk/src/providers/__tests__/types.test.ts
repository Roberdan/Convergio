import { describe, it, expect } from 'vitest';
import type {
  LLMProvider,
  ProviderConfig,
  ChatMessage,
  ChatRequest,
  ChatResponse,
  StreamChunk,
} from '../types.js';

describe('Provider types', () => {
  it('ChatMessage has role and content fields', () => {
    const msg: ChatMessage = { role: 'user', content: 'hello' };
    expect(msg.role).toBe('user');
    expect(msg.content).toBe('hello');
  });

  it('ChatMessage supports system, user, assistant roles', () => {
    const roles: ChatMessage['role'][] = ['system', 'user', 'assistant'];
    roles.forEach((role) => {
      const msg: ChatMessage = { role, content: 'test' };
      expect(msg.role).toBe(role);
    });
  });

  it('ChatRequest has model, messages, and optional params', () => {
    const req: ChatRequest = {
      model: 'gpt-4',
      messages: [{ role: 'user', content: 'hi' }],
    };
    expect(req.model).toBe('gpt-4');
    expect(req.messages).toHaveLength(1);
  });

  it('ChatRequest supports temperature, maxTokens, stop', () => {
    const req: ChatRequest = {
      model: 'gpt-4',
      messages: [{ role: 'user', content: 'hi' }],
      temperature: 0.7,
      maxTokens: 1000,
      stop: ['\n'],
    };
    expect(req.temperature).toBe(0.7);
    expect(req.maxTokens).toBe(1000);
    expect(req.stop).toEqual(['\n']);
  });

  it('ChatResponse has content, model, usage fields', () => {
    const res: ChatResponse = {
      content: 'hello back',
      model: 'gpt-4',
      usage: { promptTokens: 10, completionTokens: 5, totalTokens: 15 },
    };
    expect(res.content).toBe('hello back');
    expect(res.usage.totalTokens).toBe(15);
  });

  it('StreamChunk has type and content', () => {
    const chunk: StreamChunk = { type: 'delta', content: 'hi' };
    expect(chunk.type).toBe('delta');
    expect(chunk.content).toBe('hi');
  });

  it('StreamChunk done type has no content', () => {
    const chunk: StreamChunk = { type: 'done' };
    expect(chunk.type).toBe('done');
    expect(chunk.content).toBeUndefined();
  });

  it('StreamChunk error type has error field', () => {
    const chunk: StreamChunk = { type: 'error', error: 'timeout' };
    expect(chunk.type).toBe('error');
    expect(chunk.error).toBe('timeout');
  });

  it('ProviderConfig has name and optional fields', () => {
    const config: ProviderConfig = { name: 'openai' };
    expect(config.name).toBe('openai');
  });

  it('ProviderConfig supports apiKey, baseUrl, model', () => {
    const config: ProviderConfig = {
      name: 'openai',
      apiKey: 'sk-test',
      baseUrl: 'https://api.openai.com',
      defaultModel: 'gpt-4',
    };
    expect(config.apiKey).toBe('sk-test');
    expect(config.baseUrl).toBe('https://api.openai.com');
    expect(config.defaultModel).toBe('gpt-4');
  });

  it('LLMProvider interface has chat and stream methods', () => {
    const provider: LLMProvider = {
      name: 'test',
      chat: async () => ({
        content: '',
        model: 'test',
        usage: { promptTokens: 0, completionTokens: 0, totalTokens: 0 },
      }),
      stream: async function* () {
        yield { type: 'done' as const };
      },
    };
    expect(provider.name).toBe('test');
    expect(typeof provider.chat).toBe('function');
    expect(typeof provider.stream).toBe('function');
  });
});
