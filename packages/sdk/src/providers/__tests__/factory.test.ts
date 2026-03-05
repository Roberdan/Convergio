import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);

const ENV_KEYS = [
  'OPENAI_API_KEY',
  'ANTHROPIC_API_KEY',
  'AZURE_OPENAI_API_KEY',
  'AZURE_OPENAI_ENDPOINT',
  'AWS_ACCESS_KEY_ID',
  'AWS_SECRET_ACCESS_KEY',
  'AWS_REGION',
  'OLLAMA_BASE_URL',
];

function clearProviderEnvs(): void {
  for (const key of ENV_KEYS) {
    vi.stubEnv(key, '');
    delete process.env[key];
  }
}

describe('createProvider factory', () => {
  beforeEach(() => {
    clearProviderEnvs();
    mockFetch.mockReset();
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it('exports createProvider function', async () => {
    const { createProvider } = await import('../index.js');
    expect(typeof createProvider).toBe('function');
  });

  it('creates OpenAI provider by name', async () => {
    const { createProvider } = await import('../index.js');
    const provider = createProvider('openai', { apiKey: 'sk-test' });
    expect(provider.name).toBe('openai');
  });

  it('creates Anthropic provider by name', async () => {
    const { createProvider } = await import('../index.js');
    const provider = createProvider('anthropic', { apiKey: 'sk-ant' });
    expect(provider.name).toBe('anthropic');
  });

  it('creates Azure OpenAI provider by name', async () => {
    const { createProvider } = await import('../index.js');
    const provider = createProvider('azure-openai', {
      apiKey: 'az-key',
      endpoint: 'https://test.openai.azure.com',
    });
    expect(provider.name).toBe('azure-openai');
  });

  it('creates Ollama provider by name', async () => {
    const { createProvider } = await import('../index.js');
    const provider = createProvider('ollama');
    expect(provider.name).toBe('ollama');
  });

  it('creates Bedrock provider by name', async () => {
    const { createProvider } = await import('../index.js');
    const provider = createProvider('bedrock', {
      accessKeyId: 'AKIA',
      secretAccessKey: 'secret',
      region: 'us-east-1',
    });
    expect(provider.name).toBe('bedrock');
  });

  it('throws on unknown provider name', async () => {
    const { createProvider } = await import('../index.js');
    expect(() => createProvider('unknown' as never)).toThrow(
      /Unknown provider/,
    );
  });

  it('auto-detects OpenAI from OPENAI_API_KEY env', async () => {
    vi.stubEnv('OPENAI_API_KEY', 'sk-auto');
    const { createProvider } = await import('../index.js');
    const provider = createProvider();
    expect(provider.name).toBe('openai');
  });

  it('auto-detects Anthropic from ANTHROPIC_API_KEY env', async () => {
    vi.stubEnv('ANTHROPIC_API_KEY', 'sk-ant-auto');
    const { createProvider } = await import('../index.js');
    const provider = createProvider();
    expect(provider.name).toBe('anthropic');
  });

  it('auto-detects Azure from AZURE_OPENAI_API_KEY env', async () => {
    vi.stubEnv('AZURE_OPENAI_API_KEY', 'az-auto');
    vi.stubEnv('AZURE_OPENAI_ENDPOINT', 'https://test.openai.azure.com');
    const { createProvider } = await import('../index.js');
    const provider = createProvider();
    expect(provider.name).toBe('azure-openai');
  });

  it('auto-detects Bedrock from AWS_ACCESS_KEY_ID env', async () => {
    vi.stubEnv('AWS_ACCESS_KEY_ID', 'AKIA');
    vi.stubEnv('AWS_SECRET_ACCESS_KEY', 'secret');
    const { createProvider } = await import('../index.js');
    const provider = createProvider();
    expect(provider.name).toBe('bedrock');
  });

  it('throws when no provider can be auto-detected', async () => {
    const { createProvider } = await import('../index.js');
    expect(() => createProvider()).toThrow(/No LLM provider/);
  });

  it('re-exports all adapter creators', async () => {
    const mod = await import('../index.js');
    expect(typeof mod.createOpenAIProvider).toBe('function');
    expect(typeof mod.createAnthropicProvider).toBe('function');
    expect(typeof mod.createAzureOpenAIProvider).toBe('function');
    expect(typeof mod.createOllamaProvider).toBe('function');
    expect(typeof mod.createBedrockProvider).toBe('function');
  });

  it('re-exports all types', async () => {
    const mod = await import('../index.js');
    expect(mod).toBeDefined();
  });
});
