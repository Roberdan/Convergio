export interface ChatMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export interface ChatRequest {
  model: string;
  messages: ChatMessage[];
  temperature?: number;
  maxTokens?: number;
  stop?: string[];
}

export interface TokenUsage {
  promptTokens: number;
  completionTokens: number;
  totalTokens: number;
}

export interface ChatResponse {
  content: string;
  model: string;
  usage: TokenUsage;
}

export type StreamChunk =
  | { type: 'delta'; content: string }
  | { type: 'done'; content?: undefined; error?: undefined }
  | { type: 'error'; error: string; content?: undefined };

export interface LLMProvider {
  name: string;
  chat(req: ChatRequest): Promise<ChatResponse>;
  stream(req: ChatRequest): AsyncIterable<StreamChunk>;
}

export interface ProviderConfig {
  name: string;
  apiKey?: string;
  baseUrl?: string;
  defaultModel?: string;
}

export interface AzureOpenAIConfig extends ProviderConfig {
  endpoint?: string;
  apiVersion?: string;
}

export interface BedrockConfig extends ProviderConfig {
  accessKeyId?: string;
  secretAccessKey?: string;
  region?: string;
}
