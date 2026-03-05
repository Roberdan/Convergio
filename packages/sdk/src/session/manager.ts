import { randomUUID } from 'node:crypto';
import type {
  Session,
  SessionMessage,
  SessionCheckpoint,
  SessionState,
  CreateSessionOptions,
  ListSessionsOptions,
} from './types.js';
import { VALID_TRANSITIONS } from './types.js';
import type { PersistenceAdapter } from './persistence/types.js';

/** Configuration for SessionManager */
export interface SessionManagerConfig {
  adapter: PersistenceAdapter;
}

/**
 * Manages agent sessions with dual persistence support.
 * Session state survives process restart via configurable adapters.
 * Supports checkpoint/resume for long-running conversations.
 */
export class SessionManager {
  private readonly adapter: PersistenceAdapter;

  constructor(config: SessionManagerConfig) {
    this.adapter = config.adapter;
  }

  /** Create a new session for an agent */
  async create(options: CreateSessionOptions): Promise<Session> {
    const now = new Date();
    const session: Session = {
      id: randomUUID(),
      agentName: options.agentName,
      messages: [],
      metadata: options.metadata ?? {},
      state: 'active',
      createdAt: now,
      updatedAt: now,
    };
    await this.adapter.save(session);
    return session;
  }

  /** Get a session by ID, null if not found */
  async get(id: string): Promise<Session | null> {
    return this.adapter.load(id);
  }

  /** Add a message to a session and persist */
  async addMessage(sessionId: string, msg: SessionMessage): Promise<Session> {
    const session = await this.adapter.load(sessionId);
    if (!session) {
      throw new Error(`Session not found: ${sessionId}`);
    }
    const message: SessionMessage = {
      ...msg,
      timestamp: msg.timestamp ?? new Date(),
    };
    session.messages.push(message);
    session.updatedAt = new Date();
    await this.adapter.save(session);
    return session;
  }

  /** Save an externally modified session */
  async save(session: Session): Promise<void> {
    session.updatedAt = new Date();
    await this.adapter.save(session);
  }

  /** Delete a session by ID */
  async delete(id: string): Promise<void> {
    await this.adapter.delete(id);
  }

  /** List sessions, optionally filtered */
  async list(options?: ListSessionsOptions): Promise<Session[]> {
    return this.adapter.list(options);
  }

  /** Create a checkpoint of current session state */
  async checkpoint(sessionId: string): Promise<SessionCheckpoint> {
    const session = await this.adapter.load(sessionId);
    if (!session) {
      throw new Error(`Session not found: ${sessionId}`);
    }
    const cp: SessionCheckpoint = {
      sessionId: session.id,
      messages: [...session.messages],
      metadata: { ...session.metadata },
      state: session.state,
      createdAt: new Date(),
    };
    await this.adapter.saveCheckpoint(cp);
    return cp;
  }

  /** Resume a session from a checkpoint (restores messages/metadata/state) */
  async resume(sessionId: string, checkpoint: SessionCheckpoint): Promise<Session> {
    const session = await this.adapter.load(sessionId);
    if (!session) {
      throw new Error(`Session not found: ${sessionId}`);
    }
    session.messages = [...checkpoint.messages];
    session.metadata = { ...checkpoint.metadata };
    session.state = checkpoint.state;
    session.updatedAt = new Date();
    await this.adapter.save(session);
    return session;
  }

  /** Transition session state with validation */
  async setState(sessionId: string, newState: SessionState): Promise<Session> {
    const session = await this.adapter.load(sessionId);
    if (!session) {
      throw new Error(`Session not found: ${sessionId}`);
    }
    const allowed = VALID_TRANSITIONS[session.state];
    if (!allowed.includes(newState)) {
      throw new Error(
        `Invalid state transition: ${session.state} -> ${newState}`,
      );
    }
    session.state = newState;
    session.updatedAt = new Date();
    await this.adapter.save(session);
    return session;
  }

  /** Close the underlying adapter */
  async close(): Promise<void> {
    await this.adapter.close();
  }
}
