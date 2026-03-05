import type { Session, SessionCheckpoint, ListSessionsOptions } from '../types.js';
import type { PersistenceAdapter } from './types.js';

/** In-memory adapter for testing and short-lived sessions */
export class MemoryAdapter implements PersistenceAdapter {
  private sessions = new Map<string, Session>();
  private checkpoints = new Map<string, SessionCheckpoint[]>();

  async save(session: Session): Promise<void> {
    this.sessions.set(session.id, structuredClone(session));
  }

  async load(id: string): Promise<Session | null> {
    const session = this.sessions.get(id);
    return session ? structuredClone(session) : null;
  }

  async delete(id: string): Promise<void> {
    this.sessions.delete(id);
    this.checkpoints.delete(id);
  }

  async list(options?: ListSessionsOptions): Promise<Session[]> {
    let results = Array.from(this.sessions.values());
    if (options?.agentName) {
      results = results.filter((s) => s.agentName === options.agentName);
    }
    return results.map((s) => structuredClone(s));
  }

  async saveCheckpoint(checkpoint: SessionCheckpoint): Promise<void> {
    const existing = this.checkpoints.get(checkpoint.sessionId) ?? [];
    existing.push(structuredClone(checkpoint));
    this.checkpoints.set(checkpoint.sessionId, existing);
  }

  async listCheckpoints(sessionId: string): Promise<SessionCheckpoint[]> {
    const checkpoints = this.checkpoints.get(sessionId) ?? [];
    return checkpoints.map((c) => structuredClone(c));
  }

  async close(): Promise<void> {
    this.sessions.clear();
    this.checkpoints.clear();
  }
}
