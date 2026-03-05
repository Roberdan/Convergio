import type { Session, SessionCheckpoint, ListSessionsOptions } from '../types.js';

/** Persistence adapter interface for session storage (C-09: SQLite local, Postgres enterprise) */
export interface PersistenceAdapter {
  /** Save or update a session */
  save(session: Session): Promise<void>;

  /** Load a session by ID, null if not found */
  load(id: string): Promise<Session | null>;

  /** Delete a session by ID */
  delete(id: string): Promise<void>;

  /** List all sessions, optionally filtered */
  list(options?: ListSessionsOptions): Promise<Session[]>;

  /** Save a checkpoint snapshot */
  saveCheckpoint(checkpoint: SessionCheckpoint): Promise<void>;

  /** List all checkpoints for a session */
  listCheckpoints(sessionId: string): Promise<SessionCheckpoint[]>;

  /** Close adapter and release resources */
  close(): Promise<void>;
}
