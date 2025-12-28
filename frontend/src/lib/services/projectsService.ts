export interface Client {
  id: number;
  name: string;
  email: string;
  created_at?: string;
  updated_at?: string;
}

export interface Activity {
  id: number;
  title: string;
  description?: string;
  status: "planning" | "in-progress" | "review" | "completed";
  progress: number;
  created_at?: string;
  updated_at?: string;
}

export interface Engagement {
  id: number;
  title: string;
  description?: string;
  status: "planning" | "in-progress" | "review" | "completed" | "on_hold";
  progress: number;
  created_at?: string;
  updated_at?: string;
}

export interface EngagementDetail {
  id: number;
  title: string;
  description?: string;
  status: "planning" | "in-progress" | "review" | "completed" | "on_hold";
  progress: number;
  created_at?: string;
  updated_at?: string;
  activities: Activity[];
}

export interface ProjectOverview {
  total_engagements: number;
  status_breakdown: Record<string, number>;
  active_engagements: number;
  recent_engagements: Engagement[];
  total_clients: number;
  completed_engagements: number;
  clients: Client[];
}

export interface EngagementCreate {
  title: string;
  description?: string;
  status?: string;
}

export interface TeamMember {
  id: number;
  project_id: number;
  resource_type: "talent" | "agent";
  resource_id: number;
  resource_name: string;
  resource_role?: string;
  allocation_pct: number;
  role_in_project?: string;
}

export interface ProjectTeam {
  project_id: number;
  talents: TeamMember[];
  agents: TeamMember[];
  total_members: number;
  total_allocation: number;
}

export interface ProjectBudget {
  budget: number;
  actual_cost: number;
  ai_cost: number;
  cost_variance: number;
}

export interface ProjectTask {
  id: string;
  title: string;
  status: "pending" | "in_progress" | "in_review" | "blocked" | "completed" | "cancelled";
  priority: "critical" | "high" | "medium" | "low";
  progress_percentage: number;
}

class ProjectsService {
  private baseUrl = `${import.meta.env.VITE_API_URL || "http://localhost:9000"}/api/v1`;

  async getProjectOverview(): Promise<ProjectOverview> {
    try {
      const response = await fetch(`${this.baseUrl}/projects/overview`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      // Silent failure
      throw error;
    }
  }

  async getClients(): Promise<Client[]> {
    try {
      const response = await fetch(`${this.baseUrl}/projects/clients`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data.clients || data; // Handle both formats
    } catch (error) {
      // Silent failure
      throw error;
    }
  }

  async getEngagements(): Promise<Engagement[]> {
    try {
      const response = await fetch(`${this.baseUrl}/projects/engagements`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data.engagements || data; // Handle both formats
    } catch (error) {
      // Silent failure
      throw error;
    }
  }

  async getClient(id: number): Promise<Client> {
    try {
      const response = await fetch(`${this.baseUrl}/projects/clients/${id}`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      // Silent failure
      throw error;
    }
  }

  async getEngagement(id: number): Promise<Engagement> {
    try {
      const response = await fetch(
        `${this.baseUrl}/projects/engagements/${id}`,
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

  async getEngagementDetails(id: number): Promise<EngagementDetail> {
    try {
      const response = await fetch(
        `${this.baseUrl}/projects/engagements/${id}/details`,
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

  async getActivities(): Promise<Activity[]> {
    try {
      const response = await fetch(`${this.baseUrl}/projects/activities`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data.activities || data; // Handle both formats
    } catch (error) {
      // Silent failure
      throw error;
    }
  }

  async createEngagement(engagement: EngagementCreate): Promise<Engagement> {
    try {
      const response = await fetch(`${this.baseUrl}/projects/engagements`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(engagement),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      // Silent failure
      throw error;
    }
  }

  async getProjectTeam(projectId: number): Promise<ProjectTeam> {
    try {
      const response = await fetch(`${this.baseUrl}/projects/${projectId}/team`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      // Return empty team if not found
      return {
        project_id: projectId,
        talents: [],
        agents: [],
        total_members: 0,
        total_allocation: 0,
      };
    }
  }

  async getProjectBudget(projectId: number): Promise<ProjectBudget> {
    try {
      const response = await fetch(`${this.baseUrl}/pm/projects/${projectId}`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const project = await response.json();
      return {
        budget: project.budget || 0,
        actual_cost: project.actual_cost || 0,
        ai_cost: project.ai_cost || 0,
        cost_variance: project.cost_variance || 0,
      };
    } catch (error) {
      // Return zero budget if not found
      return {
        budget: 0,
        actual_cost: 0,
        ai_cost: 0,
        cost_variance: 0,
      };
    }
  }

  async getProjectTasks(projectId: number): Promise<ProjectTask[]> {
    try {
      const response = await fetch(`${this.baseUrl}/pm/projects/${projectId}/tasks`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      // Return empty tasks if not found
      return [];
    }
  }

  getBlockedTasks(tasks: ProjectTask[]): ProjectTask[] {
    return tasks.filter(task => task.status === "blocked");
  }
}

export const projectsService = new ProjectsService();
