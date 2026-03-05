export { SessionManager } from './manager.js';
export type { SessionManagerConfig } from './manager.js';

export type {
  Session,
  SessionMessage,
  SessionCheckpoint,
  CreateSessionOptions,
  ListSessionsOptions,
} from './types.js';

export { SessionState, MessageRole, VALID_TRANSITIONS } from './types.js';

export type { PersistenceAdapter } from './persistence/types.js';
export { MemoryAdapter } from './persistence/memory.js';
export { SqliteAdapter } from './persistence/sqlite.js';
export { PostgresAdapter } from './persistence/postgres.js';
export type { PostgresConfig } from './persistence/postgres.js';
