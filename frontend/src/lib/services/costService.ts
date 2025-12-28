export interface CostOverview {
  total_cost_usd: number;
  period_cost_usd: number;
  cost_breakdown: {
    input_tokens: number;
    output_tokens: number;
    total_requests: number;
  };
  top_agents: Array<{
    agent_id: string;
    cost_usd: number;
    percentage: number;
  }>;
  top_models: Array<{
    model: string;
    cost_usd: number;
    usage_count: number;
  }>;
}

export interface CostSummary {
  agent_id: string;
  agent_name: string;
  total_cost_usd: number;
  session_count: number;
  avg_cost_per_session: number;
  last_activity: string;
  cost_trend: "increasing" | "decreasing" | "stable";
}

export interface BudgetStatus {
  total_budget_usd: number;
  used_budget_usd: number;
  remaining_budget_usd: number;
  utilization_percentage: number;
  projected_monthly_cost: number;
  budget_health: "healthy" | "warning" | "critical";
  days_remaining: number;
}

export interface LLMProvider {
  provider: string;
  status: "active" | "inactive" | "error";
  models: string[];
  current_cost: number;
  rate_limits: {
    requests_per_minute: number;
    tokens_per_minute: number;
  };
}

class CostService {
  private baseUrl = `${import.meta.env.VITE_API_URL || "http://localhost:9000"}/api/v1`;

  async getCostOverview(): Promise<CostOverview> {
    try {
      const response = await fetch(`${this.baseUrl}/cost-management/overview`);

      if (!response.ok) {
        // NO MOCK DATA - Always show real data or zero
        return {
          total_cost_usd: 0,
          period_cost_usd: 0,
          cost_breakdown: {
            input_tokens: 0,
            output_tokens: 0,
            total_requests: 0,
          },
          top_agents: [],
          top_models: [],
        };
      }

      return await response.json();
    } catch (error) {
      // Silent failure
      throw error;
    }
  }

  async getAgentCostSummary(agentId: string): Promise<CostSummary> {
    try {
      const response = await fetch(
        `${this.baseUrl}/cost-management/agents/${agentId}/summary`,
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      // Silent failure
      throw error;
    }
  }

  async getBudgetStatus(): Promise<BudgetStatus> {
    try {
      const response = await fetch(
        `${this.baseUrl}/cost-management/budget/status`,
      );

      if (!response.ok) {
        // NO MOCK DATA - Always show real budget data or zero
        return {
          total_budget_usd: 0,
          used_budget_usd: 0,
          remaining_budget_usd: 0,
          utilization_percentage: 0,
          projected_monthly_cost: 0,
          budget_health: "healthy",
          days_remaining: 0,
        };
      }

      return await response.json();
    } catch (error) {
      // Silent failure
      throw error;
    }
  }

  async getLLMProviders(): Promise<LLMProvider[]> {
    try {
      const response = await fetch(`${this.baseUrl}/cost-management/providers`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      // Silent failure
      throw error;
    }
  }

  async getRealtimeCost(): Promise<any> {
    try {
      const response = await fetch(
        `${this.baseUrl}/cost-management/realtime/current`,
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      // Silent failure
      throw error;
    }
  }
}

export const costService = new CostService();
