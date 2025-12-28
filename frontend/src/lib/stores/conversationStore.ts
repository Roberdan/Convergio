/**
 * 💬 Conversation Store - Multi-Agent Conversation Management
 * Manages persistent conversations for each agent with AutoGen Memory integration
 */

import { writable, derived, get } from "svelte/store";
import type { Writable, Readable } from "svelte/store";
import { authStore } from "$lib/auth/auth.store";

export interface ConversationMessage {
  id: string;
  agentId: string;
  agentName: string;
  content: string;
  timestamp: Date;
  type: "user" | "agent";
  status: "sending" | "sent" | "error";
}

export interface AgentConversation {
  agentId: string;
  agentName: string;
  messages: ConversationMessage[];
  lastActivity: Date;
  status: "active" | "waiting" | "idle" | "error";
  conversationId: string;
  summary?: string;
}

export interface AgentStatus {
  id: string;
  name: string;
  status: "active" | "waiting" | "idle" | "error";
  lastActivity: Date;
  conversationCount: number;
}

// Main conversation store
const conversationsStore: Writable<Map<string, AgentConversation>> = writable(
  new Map(),
);
export const conversations = conversationsStore;

// Current active agent
export const currentAgentId: Writable<string | null> = writable(null);

// Agent status tracking
const agentStatusStore: Writable<Map<string, AgentStatus>> = writable(
  new Map(),
);
export const agentStatuses = agentStatusStore;

// Derived store for current conversation
export const currentConversation: Readable<AgentConversation | null> = derived(
  [conversations, currentAgentId],
  ([$conversations, $currentAgentId]) => {
    if (!$currentAgentId) return null;
    return $conversations.get($currentAgentId) || null;
  },
);

// Conversation management functions
export const conversationManager = {
  // Initialize conversation for an agent
  initializeConversation(agentId: string, agentName: string): void {
    conversationsStore.update((conversations) => {
      if (!conversations.has(agentId)) {
        const newConversation: AgentConversation = {
          agentId,
          agentName,
          messages: [],
          lastActivity: new Date(),
          status: "idle",
          conversationId: `conv_${agentId}_${Date.now()}`,
        };
        conversations.set(agentId, newConversation);

        // Initialize agent status
        agentStatusStore.update((statuses) => {
          statuses.set(agentId, {
            id: agentId,
            name: agentName,
            status: "idle",
            lastActivity: new Date(),
            conversationCount: 0,
          });
          return statuses;
        });
      }
      return conversations;
    });
  },

  // Switch to an agent's conversation
  switchToAgent(agentId: string): void {
    currentAgentId.set(agentId);
  },

  // Add message to conversation
  addMessage(agentId: string, message: Omit<ConversationMessage, "id">): void {
    const messageId = `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    conversationsStore.update((conversations) => {
      const conversation = conversations.get(agentId);
      if (conversation) {
        const newMessage: ConversationMessage = {
          ...message,
          id: messageId,
        };

        conversation.messages.push(newMessage);
        conversation.lastActivity = new Date();
        conversation.status = message.type === "user" ? "waiting" : "active";

        conversations.set(agentId, conversation);
      }
      return conversations;
    });

    // Update agent status
    agentStatusStore.update((statuses) => {
      const status = statuses.get(agentId);
      if (status) {
        status.lastActivity = new Date();
        status.status = message.type === "user" ? "waiting" : "active";
        status.conversationCount = status.conversationCount + 1;
        statuses.set(agentId, status);
      }
      return statuses;
    });
  },

  // Update message status
  updateMessageStatus(
    agentId: string,
    messageId: string,
    status: "sending" | "sent" | "error",
  ): void {
    conversationsStore.update((conversations) => {
      const conversation = conversations.get(agentId);
      if (conversation) {
        const message = conversation.messages.find((m) => m.id === messageId);
        if (message) {
          message.status = status;
        }
        conversations.set(agentId, conversation);
      }
      return conversations;
    });
  },

  // Update agent status
  updateAgentStatus(
    agentId: string,
    status: "active" | "waiting" | "idle" | "error",
  ): void {
    agentStatusStore.update((statuses) => {
      const agentStatus = statuses.get(agentId);
      if (agentStatus) {
        agentStatus.status = status;
        agentStatus.lastActivity = new Date();
        statuses.set(agentId, agentStatus);
      }
      return statuses;
    });

    // Also update conversation status
    conversationsStore.update((conversations) => {
      const conversation = conversations.get(agentId);
      if (conversation) {
        conversation.status = status;
        conversations.set(agentId, conversation);
      }
      return conversations;
    });
  },

  // Reset conversation (start new)
  resetConversation(agentId: string): void {
    conversationsStore.update((conversations) => {
      const conversation = conversations.get(agentId);
      if (conversation) {
        conversation.messages = [];
        conversation.conversationId = `conv_${agentId}_${Date.now()}`;
        conversation.lastActivity = new Date();
        conversation.status = "idle";
        conversation.summary = undefined;
        conversations.set(agentId, conversation);
      }
      return conversations;
    });

    // Reset agent status
    this.updateAgentStatus(agentId, "idle");
  },

  // Delete conversation
  deleteConversation(agentId: string): void {
    conversationsStore.update((conversations) => {
      conversations.delete(agentId);
      return conversations;
    });

    agentStatusStore.update((statuses) => {
      statuses.delete(agentId);
      return statuses;
    });

    // If this was the current agent, clear selection
    currentAgentId.update((current) => (current === agentId ? null : current));
  },

  // Get conversation history
  getConversationHistory(agentId: string): ConversationMessage[] {
    let conversation: AgentConversation | undefined;

    conversations.subscribe((convs) => {
      conversation = convs.get(agentId);
    })();

    return conversation ? conversation.messages : [];
  },

  // Get full conversation object (helper for UI components)
  getConversation(agentId: string): AgentConversation | null {
    let conversation: AgentConversation | null = null;
    conversations.subscribe((convs) => {
      conversation = convs.get(agentId) || null;
    })();
    return conversation;
  },

  // Save conversation to backend (AutoGen Memory integration)
  async saveConversationToMemory(agentId: string): Promise<void> {
    let conversation: AgentConversation | undefined;

    conversations.subscribe((convs) => {
      conversation = convs.get(agentId);
    })();

    if (
      !conversation ||
      !conversation.messages ||
      conversation.messages.length === 0
    )
      return;

    try {
      // Get current user from auth store
      const auth = get(authStore);
      const userId = auth.user?.id ?? "anonymous";

      // Save to AutoGen Memory system
      const response = await fetch(
        "http://localhost:9000/api/v1/agents/conversation/save",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            conversation_id: conversation.conversationId,
            agent_id: agentId,
            messages: conversation.messages,
            user_id: userId,
            summary: conversation.summary,
          }),
        },
      );

      if (!response.ok) {
        // Silent failure - conversation will be saved on next attempt
      }
    } catch {
      // Silent failure - network issues are handled by retry
    }
  },

  // Load conversation from backend (AutoGen Memory)
  async loadConversationFromMemory(
    agentId: string,
    conversationId?: string,
  ): Promise<void> {
    try {
      const url = conversationId
        ? `http://localhost:9000/api/v1/agents/conversation/load/${conversationId}`
        : `http://localhost:9000/api/v1/agents/conversation/load/latest/${agentId}`;

      const response = await fetch(url);

      if (response.ok) {
        const data = await response.json();

        // Restore conversation from memory
        conversationsStore.update((conversations) => {
          const restoredConversation: AgentConversation = {
            agentId,
            agentName: data.agent_name,
            messages: data.messages.map((msg: any) => ({
              ...msg,
              timestamp: new Date(msg.timestamp),
            })),
            lastActivity: new Date(data.last_activity),
            status: "idle",
            conversationId: data.conversation_id,
            summary: data.summary,
          };

          conversations.set(agentId, restoredConversation);
          return conversations;
        });
      }
    } catch {
      // Silent failure - will use empty conversation
    }
  },
};

// Initialize on page load
if (typeof window !== "undefined") {
  // Auto-save conversations periodically
  setInterval(() => {
    conversations.subscribe((convs) => {
      convs.forEach((conv, agentId) => {
        if (conv.messages.length > 0) {
          conversationManager.saveConversationToMemory(agentId);
        }
      });
    })();
  }, 30000); // Save every 30 seconds
}
