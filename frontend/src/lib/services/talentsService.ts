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
    const response = await fetch(`${this.baseUrl}/talents`);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  }

  async getTalent(id: number): Promise<Talent> {
    const response = await fetch(`${this.baseUrl}/talents/${id}`);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  }

  async createTalent(data: TalentCreate): Promise<Talent> {
    const response = await fetch(`${this.baseUrl}/talents`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  }

  async updateTalent(id: number, data: TalentUpdate): Promise<Talent> {
    const response = await fetch(`${this.baseUrl}/talents/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  }

  async deleteTalent(id: number): Promise<void> {
    const response = await fetch(`${this.baseUrl}/talents/${id}`, {
      method: "DELETE",
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
  }

  async getTalentHierarchy(id: number): Promise<TalentHierarchy> {
    const response = await fetch(`${this.baseUrl}/talents/${id}/hierarchy`);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  }

  // ===== Talent Projects =====

  async getTalentProjects(talentId: number): Promise<ResourceProjects> {
    const response = await fetch(
      `${this.baseUrl}/talents/${talentId}/projects`,
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  }

  // ===== Project Team =====

  async getProjectTeam(projectId: number): Promise<ProjectTeam> {
    const response = await fetch(`${this.baseUrl}/projects/${projectId}/team`);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  }

  async addTeamMember(
    projectId: number,
    member: TeamMemberAdd,
  ): Promise<ProjectAssignment> {
    const response = await fetch(`${this.baseUrl}/projects/${projectId}/team`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(member),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  }

  async updateTeamMember(
    projectId: number,
    resourceId: number,
    resourceType: "talent" | "agent",
    update: Partial<ProjectAssignment>,
  ): Promise<ProjectAssignment> {
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
  }

  async removeTeamMember(
    projectId: number,
    resourceId: number,
    resourceType: "talent" | "agent",
  ): Promise<void> {
    const response = await fetch(
      `${this.baseUrl}/projects/${projectId}/team/${resourceId}?resource_type=${resourceType}`,
      {
        method: "DELETE",
      },
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
  }
}

export const talentsService = new TalentsService();
