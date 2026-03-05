/** Valid session states */
export const SessionState = ['active', 'paused', 'completed', 'error'] as const;
export type SessionState = (typeof SessionState)[number];

/** Valid message roles */
export const MessageRole = ['user', 'assistant', 'system', 'tool'] as const;
export type MessageRole = (typeof MessageRole)[number];

/** A message within a session */
export interface SessionMessage {
  role: MessageRole;
  content: string;
  timestamp?: Date;
  metadata?: Record<string, unknown>;
}

/** Core session entity. Survives process restart via persistence adapters. */
export interface Session {
  id: string;
  agentName: string;
  messages: SessionMessage[];
  metadata: Record<string, unknown>;
  state: SessionState;
  createdAt: Date;
  updatedAt: Date;
}

/** Snapshot of session state for checkpoint/resume */
export interface SessionCheckpoint {
  sessionId: string;
  messages: SessionMessage[];
  metadata: Record<string, unknown>;
  state: SessionState;
  createdAt: Date;
}

/** Options for creating a new session */
export interface CreateSessionOptions {
  agentName: string;
  metadata?: Record<string, unknown>;
}

/** Options for listing sessions */
export interface ListSessionsOptions {
  agentName?: string;
}

/** Valid state transitions: from -> allowed destinations */
export const VALID_TRANSITIONS: Record<SessionState, SessionState[]> = {
  active: ['paused', 'completed', 'error'],
  paused: ['active', 'completed', 'error'],
  completed: [],
  error: ['active'],
};
