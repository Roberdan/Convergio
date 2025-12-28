/**
 * WS2: Enhanced People Data Model Types
 */

export interface SkillItem {
  name: string;
  level: "beginner" | "intermediate" | "advanced" | "expert";
  years?: number;
}

export interface Talent {
  id: number;
  email: string;
  username: string;
  first_name?: string;
  last_name?: string;
  full_name: string;
  department?: string;
  role?: string;
  tier?: "junior" | "mid" | "senior" | "lead" | "principal";
  skills?: SkillItem[];
  hourly_rate?: number;
  daily_rate?: number;
  availability?: number; // 0-100 percentage
  timezone?: string;
  phone?: string;
  location?: string;
  experience_years?: number;
  bio?: string;
  rating?: number;
  is_admin?: boolean;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface TalentCreate {
  email: string;
  first_name?: string;
  last_name?: string;
  department?: string;
  role?: string;
  tier?: Talent["tier"];
  skills?: SkillItem[];
  hourly_rate?: number;
  daily_rate?: number;
  availability?: number;
  timezone?: string;
  phone?: string;
  location?: string;
  experience_years?: number;
  bio?: string;
  is_admin?: boolean;
}

export interface TalentUpdate extends Partial<TalentCreate> {}

export interface TalentHierarchy {
  talent: Talent;
  subordinates: Talent[];
  hierarchy_level: number;
}

export interface ProjectAssignment {
  id: number;
  project_id: number;
  resource_type: "talent" | "agent";
  resource_id: number;
  allocation_pct: number; // 0-100
  role_in_project?: string;
  start_date?: string;
  end_date?: string;
  status: "active" | "paused" | "completed" | "cancelled";
  billable: boolean;
  hourly_rate_override?: number;
  notes?: string;
  created_at?: string;
  updated_at?: string;
}

export interface ProjectAssignmentWithResource extends ProjectAssignment {
  resource_name?: string;
  resource_email?: string;
  resource_role?: string;
  resource_availability?: number;
}

export interface ProjectTeam {
  project_id: number;
  talents: ProjectAssignmentWithResource[];
  agents: ProjectAssignmentWithResource[];
  total_members: number;
  total_allocation: number;
}

export interface ResourceProjects {
  resource_type: "talent" | "agent";
  resource_id: number;
  assignments: ProjectAssignment[];
  total_allocation: number;
  available_capacity: number;
}

export interface TeamMemberAdd {
  resource_type: "talent" | "agent";
  resource_id: number;
  allocation_pct?: number;
  role_in_project?: string;
  start_date?: string;
  end_date?: string;
  billable?: boolean;
  hourly_rate_override?: number;
}

class TalentsService {
  private baseUrl = `${import.meta.env.VITE_API_URL || "http://localhost:9000"}/api/v1`;

  // ===== Talent CRUD =====

  async getTalents(): Promise<Talent[]> {
    try {
      const response = await fetch(`${this.baseUrl}/talents`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      // Silent failure
      throw error;
    }
  }

  async getTalent(id: number): Promise<Talent> {
    try {
      const response = await fetch(`${this.baseUrl}/talents/${id}`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      // Silent failure
      throw error;
    }
  }

  async createTalent(data: TalentCreate): Promise<Talent> {
    try {
      const response = await fetch(`${this.baseUrl}/talents`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
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

  async updateTalent(id: number, data: TalentUpdate): Promise<Talent> {
    try {
      const response = await fetch(`${this.baseUrl}/talents/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
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

  async deleteTalent(id: number): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/talents/${id}`, {
        method: "DELETE",
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
    } catch (error) {
      // Silent failure
      throw error;
    }
  }

  async getTalentHierarchy(id: number): Promise<TalentHierarchy> {
    try {
      const response = await fetch(`${this.baseUrl}/talents/${id}/hierarchy`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      // Silent failure
      throw error;
    }
  }

  // ===== Talent Projects =====

  async getTalentProjects(talentId: number): Promise<ResourceProjects> {
    try {
      const response = await fetch(
        `${this.baseUrl}/talents/${talentId}/projects`,
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

  // ===== Project Team =====

  async getProjectTeam(projectId: number): Promise<ProjectTeam> {
    try {
      const response = await fetch(
        `${this.baseUrl}/projects/${projectId}/team`,
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

  async addTeamMember(
    projectId: number,
    member: TeamMemberAdd,
  ): Promise<ProjectAssignment> {
    try {
      const response = await fetch(
        `${this.baseUrl}/projects/${projectId}/team`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(member),
        },
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

  async updateTeamMember(
    projectId: number,
    resourceId: number,
    resourceType: "talent" | "agent",
    update: Partial<ProjectAssignment>,
  ): Promise<ProjectAssignment> {
    try {
      const response = await fetch(
        `${this.baseUrl}/projects/${projectId}/team/${resourceId}?resource_type=${resourceType}`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(update),
        },
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

  async removeTeamMember(
    projectId: number,
    resourceId: number,
    resourceType: "talent" | "agent",
  ): Promise<void> {
    try {
      const response = await fetch(
        `${this.baseUrl}/projects/${projectId}/team/${resourceId}?resource_type=${resourceType}`,
        {
          method: "DELETE",
        },
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
    } catch (error) {
      // Silent failure
      throw error;
    }
  }
}

export const talentsService = new TalentsService();
