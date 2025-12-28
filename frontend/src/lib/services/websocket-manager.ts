import { writable, get } from "svelte/store";
import { notify } from "$lib/stores/notifications";

export interface WebSocketConfig {
  url: string;
  protocols?: string | string[];
  reconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  heartbeatInterval?: number;
  messageQueueSize?: number;
  debug?: boolean;
}

export interface WebSocketMessage {
  id: string;
  type: string;
  data: any;
  timestamp: Date;
}

export interface ConnectionState {
  status: "connecting" | "connected" | "disconnected" | "error";
  reconnectAttempts: number;
  lastError?: string;
  lastConnected?: Date;
  lastDisconnected?: Date;
}

class WebSocketManager {
  private ws: WebSocket | null = null;
  private config: Required<WebSocketConfig>;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null;
  private messageQueue: WebSocketMessage[] = [];
  private pendingMessages: Map<
    string,
    {
      resolve: (value: any) => void;
      reject: (reason?: any) => void;
      timeout: ReturnType<typeof setTimeout>;
    }
  > = new Map();

  public state = writable<ConnectionState>({
    status: "disconnected",
    reconnectAttempts: 0,
  });

  public messages = writable<WebSocketMessage[]>([]);
  public connected = writable<boolean>(false);

  private listeners: Map<string, Set<(data: any) => void>> = new Map();

  constructor(config: WebSocketConfig) {
    this.config = {
      url: config.url,
      protocols: config.protocols || [],
      reconnect: config.reconnect ?? true,
      reconnectInterval: config.reconnectInterval ?? 5000,
      maxReconnectAttempts: config.maxReconnectAttempts ?? 10,
      heartbeatInterval: config.heartbeatInterval ?? 30000,
      messageQueueSize: config.messageQueueSize ?? 100,
      debug: config.debug ?? false,
    };
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        resolve();
        return;
      }

      this.updateState({ status: "connecting" });

      try {
        this.ws = new WebSocket(this.config.url, this.config.protocols);

        this.ws.onopen = () => {
          this.handleOpen();
          resolve();
        };

        this.ws.onmessage = (event) => {
          this.handleMessage(event);
        };

        this.ws.onerror = (error) => {
          this.handleError(error);
          reject(error);
        };

        this.ws.onclose = (event) => {
          this.handleClose(event);
        };
      } catch (error) {
        this.handleError(error as Event);
        reject(error);
      }
    });
  }

  disconnect() {
    this.config.reconnect = false;

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }

    if (this.ws) {
      this.ws.close(1000, "User requested disconnect");
      this.ws = null;
    }

    this.updateState({
      status: "disconnected",
      lastDisconnected: new Date(),
    });

    this.connected.set(false);
  }

  private handleOpen() {
    this.updateState({
      status: "connected",
      reconnectAttempts: 0,
      lastConnected: new Date(),
    });

    this.connected.set(true);

    notify.success("Connected", "WebSocket connection established");

    // Start heartbeat
    this.startHeartbeat();

    // Flush message queue
    this.flushMessageQueue();
  }

  private handleMessage(event: MessageEvent) {
    try {
      const message = JSON.parse(event.data);

      const wsMessage: WebSocketMessage = {
        id: message.id || crypto.randomUUID(),
        type: message.type || "message",
        data: message.data || message,
        timestamp: new Date(),
      };

      // Add to messages store
      this.messages.update((msgs) => {
        const updated = [...msgs, wsMessage];
        // Keep only last messageQueueSize messages
        if (updated.length > this.config.messageQueueSize) {
          updated.shift();
        }
        return updated;
      });

      // Handle response for pending messages
      if (message.id && this.pendingMessages.has(message.id)) {
        const pending = this.pendingMessages.get(message.id);
        if (pending) {
          clearTimeout(pending.timeout);
          pending.resolve(message);
          this.pendingMessages.delete(message.id);
        }
      }

      // Emit to type listeners
      if (message.type && this.listeners.has(message.type)) {
        const listeners = this.listeners.get(message.type);
        listeners?.forEach((listener) => listener(message.data || message));
      }

      // Emit to wildcard listeners
      if (this.listeners.has("*")) {
        const listeners = this.listeners.get("*");
        listeners?.forEach((listener) => listener(wsMessage));
      }
    } catch (error) {
      // Silent failure
    }
  }

  private handleError(_error: Event) {
    const errorMessage = "WebSocket error occurred";

    this.updateState({
      status: "error",
      lastError: errorMessage,
    });

    notify.error("Connection Error", errorMessage);
  }

  private handleClose(_event: CloseEvent) {
    this.updateState({
      status: "disconnected",
      lastDisconnected: new Date(),
    });

    this.connected.set(false);

    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }

    const state = get(this.state);

    // Handle reconnection
    if (
      this.config.reconnect &&
      state.reconnectAttempts < this.config.maxReconnectAttempts
    ) {
      const delay = this.getReconnectDelay(state.reconnectAttempts);

      notify.warning("Disconnected", `Reconnecting in ${delay / 1000}s...`);

      this.reconnectTimer = setTimeout(() => {
        this.updateState({
          reconnectAttempts: state.reconnectAttempts + 1,
        });

        this.connect().catch(() => {
          // Reconnection failed, will retry
        });
      }, delay);
    } else if (state.reconnectAttempts >= this.config.maxReconnectAttempts) {
      notify.error(
        "Connection Failed",
        "Maximum reconnection attempts reached",
      );
    }
  }

  private getReconnectDelay(attempt: number): number {
    // Exponential backoff with jitter
    const baseDelay = this.config.reconnectInterval;
    const maxDelay = baseDelay * Math.pow(2, Math.min(attempt, 5));
    const jitter = Math.random() * 1000;
    return Math.min(maxDelay + jitter, 30000); // Cap at 30 seconds
  }

  private startHeartbeat() {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
    }

    this.heartbeatTimer = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.send({ type: "ping" });
      }
    }, this.config.heartbeatInterval);
  }

  private flushMessageQueue() {
    while (
      this.messageQueue.length > 0 &&
      this.ws &&
      this.ws.readyState === WebSocket.OPEN
    ) {
      const message = this.messageQueue.shift();
      if (message) {
        this.ws.send(JSON.stringify(message));
      }
    }
  }

  private updateState(updates: Partial<ConnectionState>) {
    this.state.update((s) => ({ ...s, ...updates }));
  }

  send(data: any): Promise<any> {
    return new Promise((resolve, reject) => {
      const message: WebSocketMessage = {
        id: crypto.randomUUID(),
        type: data.type || "message",
        data: data.data || data,
        timestamp: new Date(),
      };

      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        try {
          this.ws.send(JSON.stringify(message));

          // Set up response handler with timeout
          const timeout = setTimeout(() => {
            this.pendingMessages.delete(message.id);
            reject(new Error("Message timeout"));
          }, 30000); // 30 second timeout

          this.pendingMessages.set(message.id, { resolve, reject, timeout });
        } catch (error) {
          reject(error);
        }
      } else {
        // Queue message if not connected
        this.messageQueue.push(message);

        if (this.messageQueue.length > this.config.messageQueueSize) {
          this.messageQueue.shift(); // Remove oldest message
        }

        // Try to reconnect if disconnected
        if (!this.ws || this.ws.readyState === WebSocket.CLOSED) {
          this.connect()
            .then(() => {
              this.flushMessageQueue();
              resolve(message);
            })
            .catch(reject);
        } else {
          reject(new Error("WebSocket not connected"));
        }
      }
    });
  }

  on(type: string, callback: (data: any) => void) {
    if (!this.listeners.has(type)) {
      this.listeners.set(type, new Set());
    }
    this.listeners.get(type)?.add(callback);

    // Return unsubscribe function
    return () => {
      this.listeners.get(type)?.delete(callback);
    };
  }

  off(type: string, callback?: (data: any) => void) {
    if (callback) {
      this.listeners.get(type)?.delete(callback);
    } else {
      this.listeners.delete(type);
    }
  }

  getState(): ConnectionState {
    return get(this.state);
  }

  getMessages(): WebSocketMessage[] {
    return get(this.messages);
  }

  clearMessages() {
    this.messages.set([]);
  }

  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }

  getReadyState(): number {
    return this.ws?.readyState ?? WebSocket.CLOSED;
  }
}

// Factory function to create WebSocket connections
export function createWebSocketConnection(
  config: WebSocketConfig,
): WebSocketManager {
  return new WebSocketManager(config);
}

// Global connection pool
const connections = new Map<string, WebSocketManager>();

export function getConnection(name: string): WebSocketManager | undefined {
  return connections.get(name);
}

export function createConnection(
  name: string,
  config: WebSocketConfig,
): WebSocketManager {
  if (connections.has(name)) {
    connections.get(name)?.disconnect();
  }

  const manager = new WebSocketManager(config);
  connections.set(name, manager);
  return manager;
}

export function removeConnection(name: string) {
  const manager = connections.get(name);
  if (manager) {
    manager.disconnect();
    connections.delete(name);
  }
}

export function disconnectAll() {
  connections.forEach((manager) => manager.disconnect());
  connections.clear();
}

// Default connection
let defaultConnection: WebSocketManager | null = null;

export function setDefaultConnection(
  config: WebSocketConfig,
): WebSocketManager {
  if (defaultConnection) {
    defaultConnection.disconnect();
  }
  defaultConnection = new WebSocketManager(config);
  return defaultConnection;
}

export function getDefaultConnection(): WebSocketManager | null {
  return defaultConnection;
}

export default WebSocketManager;
