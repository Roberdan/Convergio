import { writable, get } from "svelte/store";

export interface QueuedMessage {
  id: string;
  payload: any;
  priority: number;
  timestamp: Date;
  retryCount: number;
  maxRetries: number;
  status: "pending" | "processing" | "completed" | "failed";
  error?: string;
  callback?: (result: any) => void;
  errorCallback?: (error: any) => void;
}

export interface QueueConfig {
  maxSize: number;
  maxRetries: number;
  retryDelay: number;
  processingTimeout: number;
  persistQueue: boolean;
  storageKey: string;
}

export interface QueueStats {
  totalMessages: number;
  pendingMessages: number;
  processingMessages: number;
  completedMessages: number;
  failedMessages: number;
  averageProcessingTime: number;
  successRate: number;
}

export class MessageQueue {
  private queue: QueuedMessage[] = [];
  private processing = new Set<string>();
  private config: QueueConfig;
  private processor: ((message: any) => Promise<any>) | null = null;
  private isProcessing = false;
  private processTimer: NodeJS.Timeout | null = null;
  private stats: QueueStats = {
    totalMessages: 0,
    pendingMessages: 0,
    processingMessages: 0,
    completedMessages: 0,
    failedMessages: 0,
    averageProcessingTime: 0,
    successRate: 0,
  };

  public queueStore = writable<QueuedMessage[]>([]);
  public statsStore = writable<QueueStats>(this.stats);
  public processingStore = writable<boolean>(false);

  constructor(config: Partial<QueueConfig> = {}) {
    this.config = {
      maxSize: config.maxSize || 1000,
      maxRetries: config.maxRetries || 3,
      retryDelay: config.retryDelay || 1000,
      processingTimeout: config.processingTimeout || 30000,
      persistQueue: config.persistQueue || true,
      storageKey: config.storageKey || "message-queue",
    };

    if (this.config.persistQueue) {
      this.loadFromStorage();
    }
  }

  setProcessor(processor: (message: any) => Promise<any>) {
    this.processor = processor;
    this.startProcessing();
  }

  enqueue(
    payload: any,
    options: {
      priority?: number;
      maxRetries?: number;
      callback?: (result: any) => void;
      errorCallback?: (error: any) => void;
    } = {},
  ): string {
    const message: QueuedMessage = {
      id: crypto.randomUUID(),
      payload,
      priority: options.priority || 0,
      timestamp: new Date(),
      retryCount: 0,
      maxRetries: options.maxRetries || this.config.maxRetries,
      status: "pending",
      callback: options.callback,
      errorCallback: options.errorCallback,
    };

    // Check queue size
    if (this.queue.length >= this.config.maxSize) {
      // Remove oldest low-priority message
      const lowestPriorityIndex = this.queue.reduce(
        (minIdx, msg, idx, arr) =>
          msg.priority < arr[minIdx].priority ? idx : minIdx,
        0,
      );

      if (this.queue[lowestPriorityIndex].priority <= message.priority) {
        this.queue.splice(lowestPriorityIndex, 1);
      } else {
        throw new Error("Queue is full and message priority is too low");
      }
    }

    // Insert message based on priority
    const insertIndex = this.queue.findIndex(
      (m) => m.priority < message.priority,
    );
    if (insertIndex === -1) {
      this.queue.push(message);
    } else {
      this.queue.splice(insertIndex, 0, message);
    }

    this.updateStats();
    this.updateStores();
    this.saveToStorage();

    // Start processing if not already running
    if (!this.isProcessing) {
      this.startProcessing();
    }

    return message.id;
  }

  async dequeue(): Promise<QueuedMessage | null> {
    const message = this.queue.find((m) => m.status === "pending");

    if (message) {
      message.status = "processing";
      this.processing.add(message.id);
      this.updateStores();
    }

    return message || null;
  }

  async processNext(): Promise<void> {
    if (!this.processor || this.processing.size >= 5) {
      // Max 5 concurrent processing
      return;
    }

    const message = await this.dequeue();
    if (!message) {
      return;
    }

    const startTime = Date.now();

    try {
      // Set processing timeout
      const timeoutPromise = new Promise((_, reject) => {
        setTimeout(
          () => reject(new Error("Processing timeout")),
          this.config.processingTimeout,
        );
      });

      const result = await Promise.race([
        this.processor(message.payload),
        timeoutPromise,
      ]);

      // Mark as completed
      message.status = "completed";
      this.processing.delete(message.id);
      this.stats.completedMessages++;

      // Update average processing time
      const processingTime = Date.now() - startTime;
      this.stats.averageProcessingTime =
        (this.stats.averageProcessingTime * (this.stats.completedMessages - 1) +
          processingTime) /
        this.stats.completedMessages;

      // Call success callback
      if (message.callback) {
        message.callback(result);
      }

      // Remove from queue
      this.removeMessage(message.id);
    } catch (error) {
      message.retryCount++;
      this.processing.delete(message.id);

      if (message.retryCount < message.maxRetries) {
        // Retry after delay
        message.status = "pending";
        setTimeout(() => {
          this.updateStores();
        }, this.config.retryDelay * message.retryCount);
      } else {
        // Mark as failed
        message.status = "failed";
        message.error = (error as Error).message;
        this.stats.failedMessages++;

        // Call error callback
        if (message.errorCallback) {
          message.errorCallback(error);
        }

        // Remove from queue after a delay
        setTimeout(() => {
          this.removeMessage(message.id);
        }, 5000);
      }
    }

    this.updateStats();
    this.updateStores();
    this.saveToStorage();
  }

  async startProcessing() {
    if (this.isProcessing) {
      return;
    }

    this.isProcessing = true;
    this.processingStore.set(true);

    // Process messages continuously
    this.processTimer = setInterval(async () => {
      if (this.processor && this.queue.some((m) => m.status === "pending")) {
        await this.processNext();
      } else if (this.queue.length === 0) {
        this.stopProcessing();
      }
    }, 100);
  }

  stopProcessing() {
    this.isProcessing = false;
    this.processingStore.set(false);

    if (this.processTimer) {
      clearInterval(this.processTimer);
      this.processTimer = null;
    }
  }

  removeMessage(id: string) {
    const index = this.queue.findIndex((m) => m.id === id);
    if (index !== -1) {
      this.queue.splice(index, 1);
      this.processing.delete(id);
      this.updateStores();
      this.saveToStorage();
    }
  }

  clearQueue() {
    this.queue = [];
    this.processing.clear();
    this.updateStats();
    this.updateStores();
    this.saveToStorage();
  }

  retryMessage(id: string) {
    const message = this.queue.find((m) => m.id === id);
    if (message && message.status === "failed") {
      message.status = "pending";
      message.retryCount = 0;
      message.error = undefined;
      this.updateStores();

      if (!this.isProcessing) {
        this.startProcessing();
      }
    }
  }

  retryAllFailed() {
    this.queue
      .filter((m) => m.status === "failed")
      .forEach((m) => {
        m.status = "pending";
        m.retryCount = 0;
        m.error = undefined;
      });

    this.updateStores();

    if (!this.isProcessing) {
      this.startProcessing();
    }
  }

  getMessage(id: string): QueuedMessage | undefined {
    return this.queue.find((m) => m.id === id);
  }

  getMessages(status?: QueuedMessage["status"]): QueuedMessage[] {
    if (status) {
      return this.queue.filter((m) => m.status === status);
    }
    return [...this.queue];
  }

  private updateStats() {
    this.stats = {
      totalMessages: this.queue.length,
      pendingMessages: this.queue.filter((m) => m.status === "pending").length,
      processingMessages: this.queue.filter((m) => m.status === "processing")
        .length,
      completedMessages: this.stats.completedMessages,
      failedMessages: this.stats.failedMessages,
      averageProcessingTime: this.stats.averageProcessingTime,
      successRate:
        this.stats.completedMessages > 0
          ? (this.stats.completedMessages /
              (this.stats.completedMessages + this.stats.failedMessages)) *
            100
          : 0,
    };

    this.statsStore.set(this.stats);
  }

  private updateStores() {
    this.queueStore.set([...this.queue]);
    this.updateStats();
  }

  private saveToStorage() {
    if (!this.config.persistQueue) {
      return;
    }

    try {
      const data = JSON.stringify({
        queue: this.queue.map((m) => ({
          ...m,
          timestamp: m.timestamp.toISOString(),
          callback: undefined,
          errorCallback: undefined,
        })),
        stats: this.stats,
      });

      localStorage.setItem(this.config.storageKey, data);
    } catch (error) {
      // Silent failure
    }
  }

  private loadFromStorage() {
    if (!this.config.persistQueue) {
      return;
    }

    try {
      const data = localStorage.getItem(this.config.storageKey);
      if (data) {
        const parsed = JSON.parse(data);

        this.queue = parsed.queue.map((m: any) => ({
          ...m,
          timestamp: new Date(m.timestamp),
          status: m.status === "processing" ? "pending" : m.status, // Reset processing to pending
        }));

        this.stats = parsed.stats || this.stats;
        this.updateStores();
      }
    } catch (error) {
      // Silent failure
    }
  }

  getStats(): QueueStats {
    return { ...this.stats };
  }

  getQueueSize(): number {
    return this.queue.length;
  }

  isPaused(): boolean {
    return !this.isProcessing;
  }

  pause() {
    this.stopProcessing();
  }

  resume() {
    if (!this.isProcessing && this.processor) {
      this.startProcessing();
    }
  }
}

// Global message queue instance
let globalQueue: MessageQueue | null = null;

export function getGlobalQueue(): MessageQueue {
  if (!globalQueue) {
    globalQueue = new MessageQueue({
      maxSize: 1000,
      maxRetries: 3,
      retryDelay: 1000,
      processingTimeout: 30000,
      persistQueue: true,
      storageKey: "global-message-queue",
    });
  }
  return globalQueue;
}

// Priority levels
export const Priority = {
  LOW: -1,
  NORMAL: 0,
  HIGH: 1,
  CRITICAL: 2,
} as const;

// Batch processing helper
export class BatchProcessor {
  private queue: MessageQueue;
  private batchSize: number;
  private batchTimeout: number;
  private batch: any[] = [];
  private batchTimer: NodeJS.Timeout | null = null;
  private processor: ((batch: any[]) => Promise<any>) | null = null;

  constructor(
    queue: MessageQueue,
    batchSize: number = 10,
    batchTimeout: number = 1000,
  ) {
    this.queue = queue;
    this.batchSize = batchSize;
    this.batchTimeout = batchTimeout;
  }

  setBatchProcessor(processor: (batch: any[]) => Promise<any>) {
    this.processor = processor;

    // Set up queue processor
    this.queue.setProcessor(async (message) => {
      this.batch.push(message);

      if (this.batch.length >= this.batchSize) {
        await this.processBatch();
      } else if (!this.batchTimer) {
        this.batchTimer = setTimeout(() => {
          this.processBatch();
        }, this.batchTimeout);
      }

      return true;
    });
  }

  private async processBatch() {
    if (this.batchTimer) {
      clearTimeout(this.batchTimer);
      this.batchTimer = null;
    }

    if (this.batch.length === 0 || !this.processor) {
      return;
    }

    const currentBatch = [...this.batch];
    this.batch = [];

    try {
      await this.processor(currentBatch);
    } catch (error) {
      // Silent failure
      throw error;
    }
  }

  async flush() {
    await this.processBatch();
  }
}

export default MessageQueue;
