/**
 * Telemetry Store - Gestisce lo stato globale della telemetria
 * Fornisce metodi per recuperare e gestire eventi, timeline e metriche
 */

import { writable, derived } from "svelte/store";

// Types
export interface TelemetryEvent {
  id: string;
  timestamp: string;
  event_type: string;
  conversation_id: string;
  user_id: string;
  agent_name?: string;
  turn_number?: number;
  data: any;
  metadata?: any;
}

export interface TimelineTurn {
  turn_number: number;
  timestamp: string;
  events: TelemetryEvent[];
  agents_involved: string[];
  total_cost: number;
  total_tokens: number;
}

export interface ConversationTimeline {
  conversation_id: string;
  timeline: TimelineTurn[];
  summary: {
    total_turns: number;
    total_cost: number;
    total_tokens: number;
    agents_involved: string[];
    start_time?: string;
    end_time?: string;
  };
}

export interface TelemetryStats {
  period: {
    start: string;
    end: string;
    days: number;
  };
  total_events: number;
  event_types: Record<string, number>;
  conversations: Record<string, number>;
  agents: Record<string, number>;
  costs: {
    total: number;
    average_per_conversation: number;
    by_agent: Record<string, number>;
  };
  performance: {
    average_turn_time: number;
    total_tokens: number;
    rag_hit_rate: number;
  };
}

export interface TelemetryState {
  events: TelemetryEvent[];
  conversations: Record<string, ConversationTimeline>;
  stats: TelemetryStats | null;
  loading: boolean;
  error: string | null;
  lastUpdate: Date | null;
}

// Initial state
const initialState: TelemetryState = {
  events: [],
  conversations: {},
  stats: null,
  loading: false,
  error: null,
  lastUpdate: null,
};

// Create store
const telemetryStore = writable<TelemetryState>(initialState);

// API base URL
const API_BASE = "/api/v1/telemetry";

// Helper functions
async function handleApiResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`HTTP ${response.status}: ${errorText}`);
  }

  const result = await response.json();
  if (!result.success) {
    throw new Error(result.error || "API request failed");
  }

  return result.data;
}

// Store actions
export const telemetryActions = {
  /**
   * Recupera eventi di telemetria con filtri opzionali
   */
  async fetchEvents(
    filters: {
      conversation_id?: string;
      user_id?: string;
      event_type?: string;
      start_time?: string;
      end_time?: string;
      limit?: number;
    } = {},
  ) {
    telemetryStore.update((state) => ({
      ...state,
      loading: true,
      error: null,
    }));

    try {
      const params = new URLSearchParams();
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined) {
          params.append(key, value.toString());
        }
      });

      const response = await fetch(`${API_BASE}/events?${params}`);
      const data = await handleApiResponse<{
        events: TelemetryEvent[];
        stats: any;
        filters_applied: any;
        total_returned: number;
      }>(response);

      telemetryStore.update((state) => ({
        ...state,
        events: data.events,
        loading: false,
        lastUpdate: new Date(),
      }));

      return data.events;
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Unknown error";
      telemetryStore.update((state) => ({
        ...state,
        error: errorMessage,
        loading: false,
      }));
      throw error;
    }
  },

  /**
   * Recupera timeline completa per una conversazione
   */
  async fetchConversationTimeline(
    conversationId: string,
  ): Promise<ConversationTimeline> {
    if (!conversationId) {
      throw new Error("Conversation ID is required");
    }

    telemetryStore.update((state) => ({
      ...state,
      loading: true,
      error: null,
    }));

    try {
      const response = await fetch(
        `${API_BASE}/conversation/${conversationId}/timeline`,
      );
      const data = await handleApiResponse<ConversationTimeline>(response);

      telemetryStore.update((state) => ({
        ...state,
        conversations: {
          ...state.conversations,
          [conversationId]: data,
        },
        loading: false,
        lastUpdate: new Date(),
      }));

      return data;
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Unknown error";
      telemetryStore.update((state) => ({
        ...state,
        error: errorMessage,
        loading: false,
      }));
      throw error;
    }
  },

  /**
   * Recupera statistiche riassuntive
   */
  async fetchStats(days: number = 7): Promise<TelemetryStats> {
    telemetryStore.update((state) => ({
      ...state,
      loading: true,
      error: null,
    }));

    try {
      const response = await fetch(`${API_BASE}/stats/summary?days=${days}`);
      const data = await handleApiResponse<TelemetryStats>(response);

      telemetryStore.update((state) => ({
        ...state,
        stats: data,
        loading: false,
        lastUpdate: new Date(),
      }));

      return data;
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Unknown error";
      telemetryStore.update((state) => ({
        ...state,
        error: errorMessage,
        loading: false,
      }));
      throw error;
    }
  },

  /**
   * Verifica lo stato del servizio di telemetria
   */
  async checkHealth(): Promise<boolean> {
    try {
      const response = await fetch(`${API_BASE}/health`);
      const data = await response.json();
      return data.success && data.status === "healthy";
    } catch {
      return false;
    }
  },

  /**
   * Pulisce gli errori
   */
  clearError() {
    telemetryStore.update((state) => ({ ...state, error: null }));
  },

  /**
   * Resetta lo store
   */
  reset() {
    telemetryStore.set(initialState);
  },

  /**
   * Aggiorna manualmente un evento
   */
  updateEvent(eventId: string, updates: Partial<TelemetryEvent>) {
    telemetryStore.update((state) => ({
      ...state,
      events: state.events.map((event) =>
        event.id === eventId ? { ...event, ...updates } : event,
      ),
    }));
  },

  /**
   * Aggiunge un nuovo evento
   */
  addEvent(event: TelemetryEvent) {
    telemetryStore.update((state) => ({
      ...state,
      events: [event, ...state.events],
    }));
  },

  /**
   * Rimuove un evento
   */
  removeEvent(eventId: string) {
    telemetryStore.update((state) => ({
      ...state,
      events: state.events.filter((event) => event.id !== eventId),
    }));
  },
};

// Derived stores
export const telemetryEvents = derived(
  telemetryStore,
  ($store) => $store.events,
);
export const telemetryConversations = derived(
  telemetryStore,
  ($store) => $store.conversations,
);
export const telemetryStats = derived(telemetryStore, ($store) => $store.stats);
export const telemetryLoading = derived(
  telemetryStore,
  ($store) => $store.loading,
);
export const telemetryError = derived(telemetryStore, ($store) => $store.error);
export const telemetryLastUpdate = derived(
  telemetryStore,
  ($store) => $store.lastUpdate,
);

// Computed values
export const telemetrySummary = derived(telemetryStore, ($store) => {
  const events = $store.events;
  const conversations = $store.conversations;

  return {
    totalEvents: events.length,
    totalConversations: Object.keys(conversations).length,
    eventTypes: events.reduce(
      (acc, event) => {
        acc[event.event_type] = (acc[event.event_type] || 0) + 1;
        return acc;
      },
      {} as Record<string, number>,
    ),
    agents: events.reduce(
      (acc, event) => {
        if (event.agent_name) {
          acc[event.agent_name] = (acc[event.agent_name] || 0) + 1;
        }
        return acc;
      },
      {} as Record<string, number>,
    ),
  };
});

export const telemetryHealth = derived(telemetryStore, ($store) => {
  const now = new Date();
  const lastUpdate = $store.lastUpdate;

  if (!lastUpdate) return "unknown";

  const timeDiff = now.getTime() - lastUpdate.getTime();
  const minutesDiff = timeDiff / (1000 * 60);

  if (minutesDiff < 1) return "excellent";
  if (minutesDiff < 5) return "good";
  if (minutesDiff < 15) return "fair";
  return "poor";
});

// Export the main store
export default telemetryStore;
