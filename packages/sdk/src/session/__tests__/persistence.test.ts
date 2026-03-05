import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { fileURLToPath } from 'node:url';
import { join, dirname } from 'node:path';
import { mkdirSync, existsSync, rmSync } from 'node:fs';
import { MemoryAdapter } from '../persistence/memory.js';
import { FileAdapter } from '../persistence/sqlite.js';
import type { Session, SessionCheckpoint } from '../types.js';
import type { PersistenceAdapter } from '../persistence/types.js';

const __dir = dirname(fileURLToPath(import.meta.url));
const TMP_FILE = join(__dir, '__fixtures__', 'test-sessions.json');

function makeSession(overrides: Partial<Session> = {}): Session {
  return {
    id: overrides.id ?? `ses-${Date.now()}`,
    agentName: overrides.agentName ?? 'test-agent',
    messages: overrides.messages ?? [],
    metadata: overrides.metadata ?? {},
    state: overrides.state ?? 'active',
    createdAt: overrides.createdAt ?? new Date(),
    updatedAt: overrides.updatedAt ?? new Date(),
  };
}

describe('MemoryAdapter', () => {
  let adapter: PersistenceAdapter;

  beforeEach(() => {
    adapter = new MemoryAdapter();
  });

  it('saves and loads a session', async () => {
    const session = makeSession({ id: 'ses-1' });
    await adapter.save(session);

    const loaded = await adapter.load('ses-1');
    expect(loaded).toBeDefined();
    expect(loaded!.id).toBe('ses-1');
    expect(loaded!.agentName).toBe('test-agent');
  });

  it('returns null for non-existent session', async () => {
    const loaded = await adapter.load('non-existent');
    expect(loaded).toBeNull();
  });

  it('overwrites existing session on save', async () => {
    const session = makeSession({ id: 'ses-1' });
    await adapter.save(session);

    const updated = { ...session, agentName: 'updated-agent' };
    await adapter.save(updated);

    const loaded = await adapter.load('ses-1');
    expect(loaded!.agentName).toBe('updated-agent');
  });

  it('deletes a session', async () => {
    const session = makeSession({ id: 'ses-1' });
    await adapter.save(session);
    await adapter.delete('ses-1');

    const loaded = await adapter.load('ses-1');
    expect(loaded).toBeNull();
  });

  it('lists all sessions', async () => {
    await adapter.save(makeSession({ id: 'ses-1', agentName: 'agent-a' }));
    await adapter.save(makeSession({ id: 'ses-2', agentName: 'agent-b' }));

    const sessions = await adapter.list();
    expect(sessions).toHaveLength(2);
  });

  it('lists sessions filtered by agentName', async () => {
    await adapter.save(makeSession({ id: 'ses-1', agentName: 'agent-a' }));
    await adapter.save(makeSession({ id: 'ses-2', agentName: 'agent-b' }));
    await adapter.save(makeSession({ id: 'ses-3', agentName: 'agent-a' }));

    const sessions = await adapter.list({ agentName: 'agent-a' });
    expect(sessions).toHaveLength(2);
  });

  it('saves and loads a checkpoint', async () => {
    const checkpoint = {
      sessionId: 'ses-1',
      messages: [{ role: 'user' as const, content: 'Hello', timestamp: new Date() }],
      metadata: {},
      state: 'active' as const,
      createdAt: new Date(),
    };

    await adapter.saveCheckpoint(checkpoint);
    const checkpoints = await adapter.listCheckpoints('ses-1');

    expect(checkpoints).toHaveLength(1);
    expect(checkpoints[0].sessionId).toBe('ses-1');
  });

  it('lists multiple checkpoints for a session', async () => {
    const base = {
      sessionId: 'ses-1',
      messages: [],
      metadata: {},
      state: 'active' as const,
      createdAt: new Date(),
    };

    await adapter.saveCheckpoint({ ...base, createdAt: new Date('2026-01-01') });
    await adapter.saveCheckpoint({ ...base, createdAt: new Date('2026-01-02') });

    const checkpoints = await adapter.listCheckpoints('ses-1');
    expect(checkpoints).toHaveLength(2);
  });
});

describe('FileAdapter — restart-survival', () => {
  function makeSession(id: string): Session {
    return {
      id,
      agentName: 'persist-agent',
      messages: [],
      metadata: { key: 'value' },
      state: 'active',
      createdAt: new Date('2026-01-01T10:00:00Z'),
      updatedAt: new Date('2026-01-01T10:00:00Z'),
    };
  }

  beforeEach(() => {
    mkdirSync(join(__dir, '__fixtures__'), { recursive: true });
    if (existsSync(TMP_FILE)) rmSync(TMP_FILE);
  });

  afterEach(() => {
    if (existsSync(TMP_FILE)) rmSync(TMP_FILE);
  });

  it('saves session and loads it from a new adapter instance (simulates restart)', async () => {
    // Write with first adapter instance
    const adapter1 = new FileAdapter(TMP_FILE);
    await adapter1.save(makeSession('ses-restart-1'));
    await adapter1.close();

    // Read with second adapter instance (simulates process restart)
    const adapter2 = new FileAdapter(TMP_FILE);
    const loaded = await adapter2.load('ses-restart-1');
    expect(loaded).not.toBeNull();
    expect(loaded!.id).toBe('ses-restart-1');
    expect(loaded!.agentName).toBe('persist-agent');
    expect(loaded!.metadata).toEqual({ key: 'value' });
  });

  it('saves checkpoint and retrieves it after simulated restart', async () => {
    const checkpoint: SessionCheckpoint = {
      sessionId: 'ses-ckpt-1',
      messages: [{ role: 'user', content: 'Hello', timestamp: new Date('2026-01-01T10:00:00Z') }],
      metadata: { step: 1 },
      state: 'active',
      createdAt: new Date('2026-01-01T10:00:00Z'),
    };

    const adapter1 = new FileAdapter(TMP_FILE);
    await adapter1.saveCheckpoint(checkpoint);
    await adapter1.close();

    const adapter2 = new FileAdapter(TMP_FILE);
    const checkpoints = await adapter2.listCheckpoints('ses-ckpt-1');
    expect(checkpoints).toHaveLength(1);
    expect(checkpoints[0].sessionId).toBe('ses-ckpt-1');
    expect(checkpoints[0].messages).toHaveLength(1);
  });

  it('lists multiple sessions after restart', async () => {
    const adapter1 = new FileAdapter(TMP_FILE);
    await adapter1.save(makeSession('ses-a'));
    await adapter1.save(makeSession('ses-b'));
    await adapter1.close();

    const adapter2 = new FileAdapter(TMP_FILE);
    const sessions = await adapter2.list();
    expect(sessions).toHaveLength(2);
    const ids = sessions.map((s) => s.id).sort();
    expect(ids).toEqual(['ses-a', 'ses-b']);
  });
});
