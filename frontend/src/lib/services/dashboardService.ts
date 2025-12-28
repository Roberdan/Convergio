export interface DashboardMetrics {
  overview?: {
    total_users?: number;
    active_users?: number;
    growth_rate?: number;
    system_health?: string;
    uptime_percentage?: number;
    total_revenue?: number;
  };
  performance_metrics?: {
    agent_interactions?: number;
    avg_response_time?: number;
    success_rate?: number;
    peak_concurrent_users?: number;
  };
  recent_activities?: Array<{
    id: string;
    type: string;
    description: string;
    timestamp: string;
    user_id?: string;
  }>;
  cost_summary?: {
    total_cost_usd?: number;
    cost_per_interaction?: number;
    budget_utilization?: number;
    top_models?: Array<any>;
  };
  user_engagement?: {
    daily_active_users?: number;
    session_duration_avg?: number;
    feature_usage?: Array<{
      feature: string;
      usage_count: number;
      user_count: number;
    }>;
  };
  recent_projects?: Project[];
}

export interface Project {
  id: number;
  name: string;
  progress: number;
  status: "planning" | "in-progress" | "review" | "completed";
  dueDate: string;
  type: string;
  description: string;
  assigned_agents: string[];
  priority: "low" | "medium" | "high" | "critical";
  budget: number;
  revenue_target: number;
  // Backend compatibility fields
  project_name?: string;
  project_type?: string;
  timeline?: string;
  expected_deliverables?: string[];
  agents_assigned?: string[];
}

class DashboardService {
  private baseUrl = `${import.meta.env.VITE_API_URL || "http://localhost:9000"}/api/v1`;

  async getDashboardMetrics(
    timeRange: string = "7d",
  ): Promise<DashboardMetrics> {
    try {
      const response = await fetch(
        `${this.baseUrl}/analytics/dashboard?time_range=${timeRange}`,
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data as DashboardMetrics;
    } catch (error) {
      // Silent failure
      throw error;
    }
  }

  async getProjects(): Promise<Project[]> {
    try {
      const response = await fetch(`${this.baseUrl}/agents/projects`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      if (!data?.projects) {
        throw new Error("Projects payload missing");
      }
      return data.projects as Project[];
    } catch (error) {
      // Silent failure
      throw error;
    }
  }

  async getRevenueTrend(
    timeRange: string = "7d",
  ): Promise<{ labels: string[]; data: number[] }> {
    try {
      const response = await fetch(
        `${this.baseUrl}/analytics/revenue?time_range=${timeRange}`,
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return {
        labels: data.labels,
        data: data.data,
      };
    } catch (error) {
      // Silent failure
      throw error;
    }
  }
}

export const dashboardService = new DashboardService();
