/**
 * 🔗 Convergio2030 API Client
 * Unified API client for the new backend architecture
 */

import { get } from "svelte/store";
import { authStore } from "$lib/auth/auth.store";
import type { User, AuthResponse } from "$lib/auth/auth.types";

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:9000";

export class ApiError extends Error {
  constructor(
    public status: number,
    public message: string,
    public details?: any,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  /**
   * Make authenticated API request
   */
  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;

    // Get current auth token
    const auth = get(authStore);

    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(options.headers as Record<string, string>),
    };

    // Add authorization header if token exists
    if (auth.token) {
      headers.Authorization = `Bearer ${auth.token}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
        credentials: "include", // Include cookies for additional security
      });

      // Handle 401 Unauthorized - token expired
      if (response.status === 401) {
        authStore.logout();
        throw new ApiError(401, "Authentication required");
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new ApiError(
          response.status,
          errorData.detail || `HTTP ${response.status}`,
          errorData,
        );
      }

      // Handle empty responses
      const contentType = response.headers.get("content-type");
      if (!contentType || !contentType.includes("application/json")) {
        return null as T;
      }

      return await response.json();
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      throw new ApiError(0, `Network error: ${error}`);
    }
  }

  // ============================================
  // 🔐 AUTHENTICATION ENDPOINTS
  // ============================================

  async login(username: string, password: string): Promise<AuthResponse> {
    return this.request<AuthResponse>("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });
  }

  async getUser(): Promise<User> {
    return this.request<User>("/api/v1/auth/user");
  }

  async refreshToken(): Promise<AuthResponse> {
    return this.request<AuthResponse>("/api/v1/auth/refresh", {
      method: "POST",
    });
  }

  async logout(): Promise<void> {
    await this.request<void>("/api/v1/auth/logout", {
      method: "POST",
    });
  }

  // ============================================
  // 🤖 AI AGENTS ENDPOINTS
  // ============================================

  async getAgents(): Promise<any[]> {
    return this.request<any[]>("/api/v1/agents");
  }

  async executeAgent(
    agentType: string,
    message: string,
    context?: any,
  ): Promise<any> {
    return this.request<any>(`/api/v1/agents/${agentType}/execute`, {
      method: "POST",
      body: JSON.stringify({ message, context }),
    });
  }

  async getAgentExecution(executionId: string): Promise<any> {
    return this.request<any>(`/api/v1/agents/executions/${executionId}`);
  }

  async listAgentExecutions(): Promise<any[]> {
    return this.request<any[]>("/api/v1/agents/executions");
  }

  // ============================================
  // 🔍 VECTOR SEARCH ENDPOINTS
  // ============================================

  async searchDocuments(query: string, filters?: any): Promise<any[]> {
    return this.request<any[]>("/api/v1/vector/search", {
      method: "POST",
      body: JSON.stringify({ query, filters }),
    });
  }

  async indexDocument(content: string, metadata?: any): Promise<any> {
    return this.request<any>("/api/v1/vector/index", {
      method: "POST",
      body: JSON.stringify({ content, metadata }),
    });
  }

  async getDocuments(): Promise<any[]> {
    return this.request<any[]>("/api/v1/vector/documents");
  }

  async deleteDocument(documentId: string): Promise<void> {
    await this.request<void>(`/api/v1/vector/documents/${documentId}`, {
      method: "DELETE",
    });
  }

  // ============================================
  // 📊 ANALYTICS ENDPOINTS
  // ============================================

  async getDashboardAnalytics(timeRange: string = "7d"): Promise<any> {
    return this.request<any>(
      `/api/v1/analytics/dashboard?time_range=${timeRange}`,
    );
  }

  async getPerformanceMetrics(): Promise<any> {
    return this.request<any>("/api/v1/analytics/performance");
  }

  async getRealTimeMetrics(): Promise<any> {
    return this.request<any>("/api/v1/analytics/real-time");
  }

  async exportAnalyticsData(
    format: string = "json",
    timeRange: string = "30d",
  ): Promise<any> {
    return this.request<any>(
      `/api/v1/analytics/export?format=${format}&time_range=${timeRange}`,
      {
        method: "POST",
      },
    );
  }

  // ============================================
  // 💰 COST MANAGEMENT ENDPOINTS
  // ============================================

  async getCostOverview(timeRange: string = "30d"): Promise<any> {
    return this.request<any>(
      `/api/v1/cost-management/overview?time_range=${timeRange}`,
    );
  }

  async getAgentCostSummary(
    agentId: string,
    timeRange: string = "30d",
  ): Promise<any> {
    return this.request<any>(
      `/api/v1/cost-management/agents/${agentId}/summary?time_range=${timeRange}`,
    );
  }

  async getLLMProviders(): Promise<any[]> {
    return this.request<any[]>("/api/v1/cost-management/providers");
  }

  async createAgentBudget(
    agentId: string,
    monthlyBudget: number,
    alertThreshold: number = 80,
  ): Promise<any> {
    return this.request<any>("/api/v1/cost-management/budgets", {
      method: "POST",
      body: JSON.stringify({
        agent_id: agentId,
        monthly_budget_usd: monthlyBudget,
        alert_threshold_percentage: alertThreshold,
      }),
    });
  }

  async getBudgetAlerts(agentId: string): Promise<any[]> {
    return this.request<any[]>(
      `/api/v1/cost-management/agents/${agentId}/alerts`,
    );
  }

  // ============================================
  // 🔍 HEALTH CHECK ENDPOINTS
  // ============================================

  async getHealthStatus(): Promise<any> {
    return this.request<any>("/health/");
  }

  async getDetailedHealth(): Promise<any> {
    return this.request<any>("/health/detailed");
  }

  // ============================================
  // 👥 USER MANAGEMENT ENDPOINTS
  // ============================================

  async getProfile(): Promise<User> {
    return this.request<User>("/api/v1/profile");
  }

  async updateProfile(data: Partial<User>): Promise<User> {
    return this.request<User>("/api/v1/profile", {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async changePassword(
    currentPassword: string,
    newPassword: string,
  ): Promise<void> {
    await this.request<void>("/api/v1/auth/change-password", {
      method: "POST",
      body: JSON.stringify({
        current_password: currentPassword,
        new_password: newPassword,
      }),
    });
  }
}

// Singleton instance
export const apiClient = new ApiClient();

// Helper functions for common operations
export const api = {
  // Authentication
  login: (username: string, password: string) =>
    apiClient.login(username, password),
  logout: () => apiClient.logout(),
  getUser: () => apiClient.getUser(),

  // Agents
  getAgents: () => apiClient.getAgents(),
  executeAgent: (agentType: string, message: string, context?: any) =>
    apiClient.executeAgent(agentType, message, context),
  getAgentExecution: (executionId: string) =>
    apiClient.getAgentExecution(executionId),

  // Vector Search
  searchDocuments: (query: string, filters?: any) =>
    apiClient.searchDocuments(query, filters),
  indexDocument: (content: string, metadata?: any) =>
    apiClient.indexDocument(content, metadata),

  // Analytics
  getDashboard: (timeRange?: string) =>
    apiClient.getDashboardAnalytics(timeRange),
  getMetrics: () => apiClient.getPerformanceMetrics(),
  getRealTime: () => apiClient.getRealTimeMetrics(),

  // Cost Management
  getCosts: (timeRange?: string) => apiClient.getCostOverview(timeRange),
  getAgentCosts: (agentId: string, timeRange?: string) =>
    apiClient.getAgentCostSummary(agentId, timeRange),

  // Health
  getHealth: () => apiClient.getHealthStatus(),

  // Profile
  getProfile: () => apiClient.getProfile(),
  updateProfile: (data: Partial<User>) => apiClient.updateProfile(data),
};

export default apiClient;
