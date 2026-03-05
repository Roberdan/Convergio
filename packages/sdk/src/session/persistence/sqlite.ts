import { readFileSync, writeFileSync, mkdirSync, existsSync, unlinkSync } from 'node:fs';
import { join, dirname } from 'node:path';
import type { Session, SessionCheckpoint, ListSessionsOptions } from '../types.js';
import type { PersistenceAdapter } from './types.js';

interface SqliteStore {
  sessions: Record<string, Session>;
  checkpoints: Record<string, SessionCheckpoint[]>;
}

/** File-based JSON persistence adapter for CLI local mode (C-09: SQLite for CLI) */
export class SqliteAdapter implements PersistenceAdapter {
  private readonly filePath: string;

  constructor(filePath: string) {
    this.filePath = filePath;
    this.ensureDir();
  }

  private ensureDir(): void {
    const dir = dirname(this.filePath);
    if (!existsSync(dir)) {
      mkdirSync(dir, { recursive: true });
    }
  }

  private readStore(): SqliteStore {
    if (!existsSync(this.filePath)) {
      return { sessions: {}, checkpoints: {} };
    }
    const raw = readFileSync(this.filePath, 'utf-8');
    return JSON.parse(raw, this.dateReviver) as SqliteStore;
  }

  private writeStore(store: SqliteStore): void {
    writeFileSync(this.filePath, JSON.stringify(store, null, 2), 'utf-8');
  }

  private dateReviver(_key: string, value: unknown): unknown {
    if (typeof value === 'string' && /^\d{4}-\d{2}-\d{2}T/.test(value)) {
      return new Date(value);
    }
    return value;
  }

  async save(session: Session): Promise<void> {
    const store = this.readStore();
    store.sessions[session.id] = structuredClone(session);
    this.writeStore(store);
  }

  async load(id: string): Promise<Session | null> {
    const store = this.readStore();
    return store.sessions[id] ? structuredClone(store.sessions[id]) : null;
  }

  async delete(id: string): Promise<void> {
    const store = this.readStore();
    delete store.sessions[id];
    delete store.checkpoints[id];
    this.writeStore(store);
  }

  async list(options?: ListSessionsOptions): Promise<Session[]> {
    const store = this.readStore();
    let results = Object.values(store.sessions);
    if (options?.agentName) {
      results = results.filter((s) => s.agentName === options.agentName);
    }
    return results;
  }

  async saveCheckpoint(checkpoint: SessionCheckpoint): Promise<void> {
    const store = this.readStore();
    const existing = store.checkpoints[checkpoint.sessionId] ?? [];
    existing.push(structuredClone(checkpoint));
    store.checkpoints[checkpoint.sessionId] = existing;
    this.writeStore(store);
  }

  async listCheckpoints(sessionId: string): Promise<SessionCheckpoint[]> {
    const store = this.readStore();
    return store.checkpoints[sessionId] ?? [];
  }

  async close(): Promise<void> {
    // No cleanup needed for file-based storage
  }

  /** Remove the backing file (for cleanup/testing) */
  destroy(): void {
    if (existsSync(this.filePath)) {
      unlinkSync(this.filePath);
    }
  }
}
