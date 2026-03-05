import { describe, it, expect, beforeEach } from 'vitest';
import { MemoryAdapter } from '../persistence/memory.js';
import type { Session } from '../types.js';
import type { PersistenceAdapter } from '../persistence/types.js';

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
