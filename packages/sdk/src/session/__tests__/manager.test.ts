import { describe, it, expect, beforeEach } from 'vitest';
import { SessionManager } from '../manager.js';
import { MemoryAdapter } from '../persistence/memory.js';
import type { Session, SessionMessage } from '../types.js';

describe('SessionManager', () => {
  let manager: SessionManager;

  beforeEach(() => {
    manager = new SessionManager({ adapter: new MemoryAdapter() });
  });

  describe('create', () => {
    it('creates a session with required fields', async () => {
      const session = await manager.create({ agentName: 'test-agent' });

      expect(session.id).toBeDefined();
      expect(session.agentName).toBe('test-agent');
      expect(session.messages).toEqual([]);
      expect(session.state).toBe('active');
      expect(session.createdAt).toBeInstanceOf(Date);
      expect(session.updatedAt).toBeInstanceOf(Date);
    });

    it('creates a session with optional metadata', async () => {
      const session = await manager.create({
        agentName: 'test-agent',
        metadata: { userId: 'u-123', context: 'onboarding' },
      });

      expect(session.metadata).toEqual({ userId: 'u-123', context: 'onboarding' });
    });

    it('generates unique IDs for each session', async () => {
      const s1 = await manager.create({ agentName: 'agent-a' });
      const s2 = await manager.create({ agentName: 'agent-b' });

      expect(s1.id).not.toBe(s2.id);
    });
  });

  describe('get', () => {
    it('retrieves an existing session by ID', async () => {
      const created = await manager.create({ agentName: 'test-agent' });
      const found = await manager.get(created.id);

      expect(found).toBeDefined();
      expect(found!.id).toBe(created.id);
      expect(found!.agentName).toBe('test-agent');
    });

    it('returns null for non-existent session', async () => {
      const found = await manager.get('non-existent-id');
      expect(found).toBeNull();
    });
  });

  describe('addMessage', () => {
    it('adds a message to the session', async () => {
      const session = await manager.create({ agentName: 'test-agent' });
      const msg: SessionMessage = { role: 'user', content: 'Hello' };

      const updated = await manager.addMessage(session.id, msg);

      expect(updated.messages).toHaveLength(1);
      expect(updated.messages[0].role).toBe('user');
      expect(updated.messages[0].content).toBe('Hello');
      expect(updated.messages[0].timestamp).toBeInstanceOf(Date);
    });

    it('appends multiple messages in order', async () => {
      const session = await manager.create({ agentName: 'test-agent' });

      await manager.addMessage(session.id, { role: 'user', content: 'Hi' });
      const updated = await manager.addMessage(session.id, {
        role: 'assistant',
        content: 'Hello!',
      });

      expect(updated.messages).toHaveLength(2);
      expect(updated.messages[0].content).toBe('Hi');
      expect(updated.messages[1].content).toBe('Hello!');
    });

    it('throws for non-existent session', async () => {
      await expect(
        manager.addMessage('bad-id', { role: 'user', content: 'Hi' }),
      ).rejects.toThrow('Session not found: bad-id');
    });
  });

  describe('save', () => {
    it('persists session changes', async () => {
      const session = await manager.create({ agentName: 'test-agent' });
      session.metadata = { updated: true };

      await manager.save(session);
      const found = await manager.get(session.id);

      expect(found!.metadata).toEqual({ updated: true });
    });

    it('updates the updatedAt timestamp on save', async () => {
      const session = await manager.create({ agentName: 'test-agent' });
      const originalUpdatedAt = session.updatedAt;

      // Small delay to ensure timestamp difference
      await new Promise((r) => setTimeout(r, 5));
      session.metadata = { changed: true };
      await manager.save(session);

      const found = await manager.get(session.id);
      expect(found!.updatedAt.getTime()).toBeGreaterThan(originalUpdatedAt.getTime());
    });
  });

  describe('delete', () => {
    it('removes a session', async () => {
      const session = await manager.create({ agentName: 'test-agent' });
      await manager.delete(session.id);

      const found = await manager.get(session.id);
      expect(found).toBeNull();
    });

    it('is idempotent on non-existent session', async () => {
      await expect(manager.delete('non-existent-id')).resolves.not.toThrow();
    });
  });

  describe('list', () => {
    it('lists all sessions', async () => {
      await manager.create({ agentName: 'agent-a' });
      await manager.create({ agentName: 'agent-b' });

      const sessions = await manager.list();
      expect(sessions).toHaveLength(2);
    });

    it('filters sessions by agentName', async () => {
      await manager.create({ agentName: 'agent-a' });
      await manager.create({ agentName: 'agent-b' });
      await manager.create({ agentName: 'agent-a' });

      const sessions = await manager.list({ agentName: 'agent-a' });
      expect(sessions).toHaveLength(2);
      expect(sessions.every((s) => s.agentName === 'agent-a')).toBe(true);
    });
  });

  describe('checkpoint and resume', () => {
    it('creates a checkpoint of session state', async () => {
      const session = await manager.create({ agentName: 'test-agent' });
      await manager.addMessage(session.id, { role: 'user', content: 'Step 1' });
      await manager.addMessage(session.id, { role: 'assistant', content: 'OK 1' });

      const checkpoint = await manager.checkpoint(session.id);

      expect(checkpoint.sessionId).toBe(session.id);
      expect(checkpoint.messages).toHaveLength(2);
      expect(checkpoint.createdAt).toBeInstanceOf(Date);
    });

    it('resumes from a checkpoint', async () => {
      const session = await manager.create({ agentName: 'test-agent' });
      await manager.addMessage(session.id, { role: 'user', content: 'Step 1' });
      await manager.addMessage(session.id, { role: 'assistant', content: 'OK 1' });

      const checkpoint = await manager.checkpoint(session.id);

      // Add more messages after checkpoint
      await manager.addMessage(session.id, { role: 'user', content: 'Step 2' });

      // Resume from checkpoint (rolls back to checkpoint state)
      const resumed = await manager.resume(session.id, checkpoint);

      expect(resumed.messages).toHaveLength(2);
      expect(resumed.messages[1].content).toBe('OK 1');
    });

    it('throws checkpoint for non-existent session', async () => {
      await expect(manager.checkpoint('bad-id')).rejects.toThrow(
        'Session not found: bad-id',
      );
    });
  });

  describe('session state transitions', () => {
    it('starts with active state', async () => {
      const session = await manager.create({ agentName: 'test-agent' });
      expect(session.state).toBe('active');
    });

    it('transitions to paused', async () => {
      const session = await manager.create({ agentName: 'test-agent' });
      const paused = await manager.setState(session.id, 'paused');
      expect(paused.state).toBe('paused');
    });

    it('transitions to completed', async () => {
      const session = await manager.create({ agentName: 'test-agent' });
      const completed = await manager.setState(session.id, 'completed');
      expect(completed.state).toBe('completed');
    });

    it('rejects invalid state transitions', async () => {
      const session = await manager.create({ agentName: 'test-agent' });
      await manager.setState(session.id, 'completed');

      await expect(manager.setState(session.id, 'active')).rejects.toThrow(
        'Invalid state transition',
      );
    });
  });
});
