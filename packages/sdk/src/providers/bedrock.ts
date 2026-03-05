import type {
  LLMProvider,
  ChatRequest,
  ChatResponse,
  StreamChunk,
  BedrockConfig,
} from './types.js';
import { readLines } from './stream-utils.js';
import { createHmac, createHash } from 'node:crypto';

const SERVICE = 'bedrock';
const DEFAULT_REGION = 'us-east-1';

function sha256(data: string): string {
  return createHash('sha256').update(data).digest('hex');
}

function hmacSha256(key: Buffer | string, data: string): Buffer {
  return createHmac('sha256', key).update(data).digest();
}

function getSignatureKey(
  secret: string,
  date: string,
  region: string,
  service: string,
): Buffer {
  const kDate = hmacSha256(`AWS4${secret}`, date);
  const kRegion = hmacSha256(kDate, region);
  const kService = hmacSha256(kRegion, service);
  return hmacSha256(kService, 'aws4_request');
}

function signRequest(
  method: string,
  url: string,
  headers: Record<string, string>,
  body: string,
  accessKeyId: string,
  secretAccessKey: string,
  region: string,
): Record<string, string> {
  const parsed = new URL(url);
  const now = new Date();
  const dateStamp = now.toISOString().replace(/[:-]|\.\d{3}/g, '').slice(0, 8);
  const amzDate = now.toISOString().replace(/[:-]|\.\d{3}/g, '').slice(0, 15) + 'Z';

  headers['x-amz-date'] = amzDate;
  headers['host'] = parsed.host;

  const signedHeaderKeys = Object.keys(headers)
    .map((k) => k.toLowerCase())
    .sort();
  const signedHeaders = signedHeaderKeys.join(';');
  const canonicalHeaders = signedHeaderKeys
    .map((k) => `${k}:${headers[k] ?? (headers as Record<string, string>)[Object.keys(headers).find((h) => h.toLowerCase() === k)!]}`)
    .join('\n') + '\n';

  const canonicalRequest = [
    method,
    parsed.pathname,
    parsed.searchParams.toString(),
    canonicalHeaders,
    signedHeaders,
    sha256(body),
  ].join('\n');

  const credentialScope = `${dateStamp}/${region}/${SERVICE}/aws4_request`;
  const stringToSign = [
    'AWS4-HMAC-SHA256',
    amzDate,
    credentialScope,
    sha256(canonicalRequest),
  ].join('\n');

  const signingKey = getSignatureKey(
    secretAccessKey,
    dateStamp,
    region,
    SERVICE,
  );
  const signature = createHmac('sha256', signingKey)
    .update(stringToSign)
    .digest('hex');

  headers['Authorization'] =
    `AWS4-HMAC-SHA256 Credential=${accessKeyId}/${credentialScope}, ` +
    `SignedHeaders=${signedHeaders}, Signature=${signature}`;

  return headers;
}

export function createBedrockProvider(
  config?: Partial<BedrockConfig>,
): LLMProvider {
  const accessKeyId =
    config?.accessKeyId ?? process.env['AWS_ACCESS_KEY_ID'] ?? '';
  const secretAccessKey =
    config?.secretAccessKey ?? process.env['AWS_SECRET_ACCESS_KEY'] ?? '';
  const region =
    config?.region ?? process.env['AWS_REGION'] ?? DEFAULT_REGION;

  function buildUrl(model: string, stream = false): string {
    const action = stream ? 'converse-stream' : 'converse';
    return `https://bedrock-runtime.${region}.amazonaws.com/model/${encodeURIComponent(model)}/${action}`;
  }

  function formatMessages(
    messages: ChatRequest['messages'],
  ): { system?: Array<{ text: string }>; messages: Array<Record<string, unknown>> } {
    const systemMsg = messages.find((m) => m.role === 'system');
    const nonSystem = messages.filter((m) => m.role !== 'system');

    return {
      ...(systemMsg && { system: [{ text: systemMsg.content }] }),
      messages: nonSystem.map((m) => ({
        role: m.role,
        content: [{ text: m.content }],
      })),
    };
  }

  async function chat(req: ChatRequest): Promise<ChatResponse> {
    const { system, messages } = formatMessages(req.messages);
    const bodyObj = {
      messages,
      ...(system && { system }),
      ...(req.maxTokens && {
        inferenceConfig: { maxTokens: req.maxTokens },
      }),
      ...(req.temperature !== undefined && {
        inferenceConfig: {
          ...(req.maxTokens && { maxTokens: req.maxTokens }),
          temperature: req.temperature,
        },
      }),
    };

    const bodyStr = JSON.stringify(bodyObj);
    const url = buildUrl(req.model);
    let headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    headers = signRequest(
      'POST',
      url,
      headers,
      bodyStr,
      accessKeyId,
      secretAccessKey,
      region,
    );

    const res = await fetch(url, {
      method: 'POST',
      headers,
      body: bodyStr,
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(
        `Bedrock API error ${res.status} ${res.statusText}: ${text}`,
      );
    }

    const data = await res.json() as {
      output: { message: { content: Array<{ text: string }> } };
      usage?: { inputTokens?: number; outputTokens?: number; totalTokens?: number };
    };
    const content = data.output.message.content
      .map((b: { text: string }) => b.text)
      .join('');

    return {
      content,
      model: req.model,
      usage: {
        promptTokens: data.usage?.inputTokens ?? 0,
        completionTokens: data.usage?.outputTokens ?? 0,
        totalTokens: data.usage?.totalTokens ?? 0,
      },
    };
  }

  async function* stream(req: ChatRequest): AsyncIterable<StreamChunk> {
    const { system, messages } = formatMessages(req.messages);
    const bodyObj = {
      messages,
      ...(system && { system }),
      ...(req.maxTokens && {
        inferenceConfig: { maxTokens: req.maxTokens },
      }),
    };

    const bodyStr = JSON.stringify(bodyObj);
    const url = buildUrl(req.model, true);
    let headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    headers = signRequest(
      'POST',
      url,
      headers,
      bodyStr,
      accessKeyId,
      secretAccessKey,
      region,
    );

    const res = await fetch(url, {
      method: 'POST',
      headers,
      body: bodyStr,
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(
        `Bedrock API error ${res.status} ${res.statusText}: ${text}`,
      );
    }

    for await (const line of readLines(res.body!)) {
      const json = JSON.parse(line);
      if (json.contentBlockDelta?.delta?.text) {
        yield { type: 'delta', content: json.contentBlockDelta.delta.text };
      } else if (json.messageStop !== undefined) {
        yield { type: 'done' };
        return;
      }
    }
  }

  return { name: 'bedrock', chat, stream };
}
