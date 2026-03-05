import type { Session, SessionCheckpoint, ListSessionsOptions } from '../types.js';
import type { PersistenceAdapter } from './types.js';

/** PostgreSQL connection configuration (C-05: env vars only, no secrets in code) */
export interface PostgresConfig {
  connectionString?: string;
  host?: string;
  port?: number;
  database?: string;
  user?: string;
  password?: string;
  ssl?: boolean;
}

/**
 * PostgreSQL adapter for enterprise deployments (C-09).
 * Intentional stub: actual pg connection is deferred until @convergio/postgres
 * package is added in a future wave. All methods throw a clear error.
 */
export class PostgresAdapter implements PersistenceAdapter {
  private readonly config: PostgresConfig;

  constructor(config: PostgresConfig) {
    this.config = config;
  }

  async save(_session: Session): Promise<void> {
    throw new Error(
      'PostgresAdapter: not yet implemented. Install @convergio/postgres for enterprise persistence.',
    );
  }

  async load(_id: string): Promise<Session | null> {
    throw new Error(
      'PostgresAdapter: not yet implemented. Install @convergio/postgres for enterprise persistence.',
    );
  }

  async delete(_id: string): Promise<void> {
    throw new Error(
      'PostgresAdapter: not yet implemented. Install @convergio/postgres for enterprise persistence.',
    );
  }

  async list(_options?: ListSessionsOptions): Promise<Session[]> {
    throw new Error(
      'PostgresAdapter: not yet implemented. Install @convergio/postgres for enterprise persistence.',
    );
  }

  async saveCheckpoint(_checkpoint: SessionCheckpoint): Promise<void> {
    throw new Error(
      'PostgresAdapter: not yet implemented. Install @convergio/postgres for enterprise persistence.',
    );
  }

  async listCheckpoints(_sessionId: string): Promise<SessionCheckpoint[]> {
    throw new Error(
      'PostgresAdapter: not yet implemented. Install @convergio/postgres for enterprise persistence.',
    );
  }

  async close(): Promise<void> {
    // No-op until pg connection is implemented
  }

  /** Get the resolved configuration (for diagnostics) */
  getConfig(): Readonly<PostgresConfig> {
    return { ...this.config };
  }
}
