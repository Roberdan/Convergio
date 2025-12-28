export interface Agent {
  agent_key: string;
  name: string;
  role?: string;
  description?: string;
  status: "active" | "inactive" | "busy" | "error";
  capabilities: string[];
  tier?: "junior" | "mid" | "senior" | "lead" | "specialist";
  tools_count?: number;
  expertise_count?: number;
  performance_metrics?: {
    total_tasks: number;
    success_rate: number;
    avg_response_time: number;
  };
  cost_data?: {
    total_cost: number;
    cost_per_interaction: number;
  };
}

export interface SwarmStatus {
  active_agents: number;
  total_tasks: number;
  coordination_patterns: string[];
  performance_overview: {
    efficiency_score: number;
    collaboration_score: number;
    task_completion_rate: number;
  };
}

export interface AgentTask {
  task_id: string;
  title: string;
  description: string;
  status: "pending" | "in-progress" | "completed" | "failed";
  assigned_to: string[];
  priority: "low" | "medium" | "high" | "critical";
  created_at: string;
  updated_at: string;
  estimated_completion?: string;
}

class AgentsService {
  private baseUrl = `${import.meta.env.VITE_API_URL || "http://localhost:9000"}/api/v1`;

  async getAgents(): Promise<Agent[]> {
    const response = await fetch(`${this.baseUrl}/agents/list`);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data.agents || [];
  }

  async getSwarmStatus(): Promise<SwarmStatus> {
    const response = await fetch(`${this.baseUrl}/swarm/status`);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  }

  async getAgentTasks(): Promise<AgentTask[]> {
    const response = await fetch(`${this.baseUrl}/swarm/tasks`);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data.tasks || [];
  }

  async getAgentProjects(): Promise<any[]> {
    const response = await fetch(`${this.baseUrl}/agents/projects`);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data.projects || [];
  }
}

export const agentsService = new AgentsService();
