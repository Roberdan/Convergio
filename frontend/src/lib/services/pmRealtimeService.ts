import { writable, derived } from "svelte/store";
import WebSocketManager, { type ConnectionState } from "./websocket-manager";

// Interfaces for real-time PM events
export interface ProjectUpdate {
  type: "project_updated" | "project_created" | "project_deleted";
  projectId: string;
  data: any;
  timestamp: string;
  userId: string;
}

export interface TaskUpdate {
  type: "task_updated" | "task_created" | "task_deleted" | "task_moved";
  taskId: string;
  projectId: string;
  data: any;
  timestamp: string;
  userId: string;
}

export interface ResourceUpdate {
  type: "resource_allocated" | "resource_freed" | "utilization_changed";
  resourceId: string;
  projectId: string;
  data: any;
  timestamp: string;
}

export interface AliUpdate {
  type: "ali_insight" | "ali_recommendation" | "ali_alert";
  projectId: string;
  message: string;
  priority: "low" | "medium" | "high" | "critical";
  data: any;
  timestamp: string;
}

export type PMRealtimeEvent =
  | ProjectUpdate
  | TaskUpdate
  | ResourceUpdate
  | AliUpdate;

class PMRealtimeService {
  private wsManager: WebSocketManager | null = null;
  private connected = false;
  private currentProjectId: string | null = null;

  // Stores for real-time updates
  public projectUpdates = writable<ProjectUpdate[]>([]);
  public taskUpdates = writable<TaskUpdate[]>([]);
  public resourceUpdates = writable<ResourceUpdate[]>([]);
  public aliUpdates = writable<AliUpdate[]>([]);

  // Combined activity feed
  public activityFeed = derived(
    [
      this.projectUpdates,
      this.taskUpdates,
      this.resourceUpdates,
      this.aliUpdates,
    ],
    ([$projects, $tasks, $resources, $ali]) => {
      const allUpdates: PMRealtimeEvent[] = [
        ...$projects,
        ...$tasks,
        ...$resources,
        ...$ali,
      ];

      // Sort by timestamp (newest first)
      return allUpdates
        .sort(
          (a, b) =>
            new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime(),
        )
        .slice(0, 50); // Keep last 50 events
    },
  );

  // Connection status
  public connectionStatus = writable<
    "connected" | "connecting" | "disconnected" | "error"
  >("disconnected");

  constructor() {
    // Initialize WebSocket connection
    this.initializeWebSocket();
  }

  private initializeWebSocket() {
    const wsUrl = `${import.meta.env.VITE_API_URL?.replace("http", "ws") || "ws://localhost:9000"}/api/v1/pm/ws`;

    this.wsManager = new WebSocketManager({
      url: wsUrl,
      reconnect: true,
      reconnectInterval: 5000,
      maxReconnectAttempts: 10,
      heartbeatInterval: 30000,
      debug: true,
    });

    // Subscribe to connection state changes
    this.wsManager.state.subscribe((state: ConnectionState) => {
      this.connectionStatus.set(state.status);
      this.connected = state.status === "connected";
    });

    // Set up message listeners
    this.setupMessageListeners();
  }

  private setupMessageListeners() {
    if (!this.wsManager) return;

    // Listen for project updates
    this.wsManager.on("project_updated", (data: ProjectUpdate) => {
      this.projectUpdates.update((updates) => [data, ...updates].slice(0, 20));
    });

    this.wsManager.on("project_created", (data: ProjectUpdate) => {
      this.projectUpdates.update((updates) => [data, ...updates].slice(0, 20));
    });

    this.wsManager.on("project_deleted", (data: ProjectUpdate) => {
      this.projectUpdates.update((updates) => [data, ...updates].slice(0, 20));
    });

    // Listen for task updates
    this.wsManager.on("task_updated", (data: TaskUpdate) => {
      this.taskUpdates.update((updates) => [data, ...updates].slice(0, 20));
    });

    this.wsManager.on("task_created", (data: TaskUpdate) => {
      this.taskUpdates.update((updates) => [data, ...updates].slice(0, 20));
    });

    this.wsManager.on("task_deleted", (data: TaskUpdate) => {
      this.taskUpdates.update((updates) => [data, ...updates].slice(0, 20));
    });

    this.wsManager.on("task_moved", (data: TaskUpdate) => {
      this.taskUpdates.update((updates) => [data, ...updates].slice(0, 20));
    });

    // Listen for resource updates
    this.wsManager.on("resource_allocated", (data: ResourceUpdate) => {
      this.resourceUpdates.update((updates) => [data, ...updates].slice(0, 20));
    });

    this.wsManager.on("resource_freed", (data: ResourceUpdate) => {
      this.resourceUpdates.update((updates) => [data, ...updates].slice(0, 20));
    });

    this.wsManager.on("utilization_changed", (data: ResourceUpdate) => {
      this.resourceUpdates.update((updates) => [data, ...updates].slice(0, 20));
    });

    // Listen for Ali updates
    this.wsManager.on("ali_insight", (data: AliUpdate) => {
      this.aliUpdates.update((updates) => [data, ...updates].slice(0, 20));
    });

    this.wsManager.on("ali_recommendation", (data: AliUpdate) => {
      this.aliUpdates.update((updates) => [data, ...updates].slice(0, 20));
    });

    this.wsManager.on("ali_alert", (data: AliUpdate) => {
      this.aliUpdates.update((updates) => [data, ...updates].slice(0, 20));
    });
  }

  // Connect to WebSocket
  async connect(): Promise<void> {
    if (!this.wsManager) {
      throw new Error("WebSocket manager not initialized");
    }

    await this.wsManager.connect();
    this.connected = true;
  }

  // Disconnect from WebSocket
  disconnect(): void {
    if (this.wsManager) {
      this.wsManager.disconnect();
      this.connected = false;
    }
  }

  // Subscribe to a specific project
  async subscribeToProject(projectId: string): Promise<void> {
    if (!this.connected || !this.wsManager) {
      await this.connect();
    }

    this.currentProjectId = projectId;

    // Send subscription message
    await this.wsManager?.send({
      type: "subscribe_project",
      projectId,
      timestamp: new Date().toISOString(),
    });
  }

  // Unsubscribe from current project
  async unsubscribeFromProject(): Promise<void> {
    if (!this.connected || !this.wsManager || !this.currentProjectId) {
      return;
    }

    // Send unsubscription message
    await this.wsManager.send({
      type: "unsubscribe_project",
      projectId: this.currentProjectId,
      timestamp: new Date().toISOString(),
    });

    this.currentProjectId = null;
  }

  // Send task status update
  async updateTaskStatus(taskId: string, newStatus: string): Promise<void> {
    if (!this.connected || !this.wsManager) {
      throw new Error("Not connected to WebSocket");
    }

    await this.wsManager.send({
      type: "update_task_status",
      taskId,
      status: newStatus,
      projectId: this.currentProjectId,
      timestamp: new Date().toISOString(),
    });
  }

  // Send resource allocation update
  async updateResourceAllocation(
    resourceId: string,
    allocation: any,
  ): Promise<void> {
    if (!this.connected || !this.wsManager) {
      throw new Error("Not connected to WebSocket");
    }

    await this.wsManager.send({
      type: "update_resource_allocation",
      resourceId,
      allocation,
      projectId: this.currentProjectId,
      timestamp: new Date().toISOString(),
    });
  }

  // Request Ali insight
  async requestAliInsight(query: string): Promise<void> {
    if (!this.connected || !this.wsManager) {
      throw new Error("Not connected to WebSocket");
    }

    await this.wsManager.send({
      type: "request_ali_insight",
      query,
      projectId: this.currentProjectId,
      timestamp: new Date().toISOString(),
    });
  }

  // Get activity summary for a time range
  getActivitySummary(hours: number = 24): PMRealtimeEvent[] {
    const cutoff = new Date(Date.now() - hours * 60 * 60 * 1000);

    // Get current activity feed
    let allUpdates: PMRealtimeEvent[] = [];

    this.activityFeed.subscribe((feed) => {
      allUpdates = feed;
    })();

    return allUpdates.filter((event) => new Date(event.timestamp) > cutoff);
  }

  // Clear all stored updates
  clearHistory(): void {
    this.projectUpdates.set([]);
    this.taskUpdates.set([]);
    this.resourceUpdates.set([]);
    this.aliUpdates.set([]);
  }
}

// Export singleton instance
export const pmRealtimeService = new PMRealtimeService();
