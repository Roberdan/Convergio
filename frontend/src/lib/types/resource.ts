/**
 * WS3: Unified Resource Interface
 * Provides a common interface for both Talents and Agents
 */

import type { Talent, SkillItem } from "$lib/services/talentsService";
import type { Agent } from "$lib/services/agentsService";

export type ResourceType = "talent" | "agent";

export interface UnifiedResource {
  id: string;
  type: ResourceType;
  name: string;
  role: string;
  description?: string;
  status: "active" | "inactive" | "busy" | "error";
  skills: SkillEntry[];
  tier?: "junior" | "mid" | "senior" | "lead" | "principal" | "specialist";
  availability: number; // 0-100
  hourlyRate?: number;
  dailyRate?: number;
  utilization: number; // 0-100
  performance: PerformanceMetrics;
  costData?: CostData;
  metadata: ResourceMetadata;
}

export interface SkillEntry {
  name: string;
  level: "beginner" | "intermediate" | "advanced" | "expert";
  years?: number;
}

export interface PerformanceMetrics {
  tasksCompleted: number;
  averageRating: number;
  efficiency: number; // 0-100
  successRate?: number; // 0-100
  avgResponseTime?: number; // ms
}

export interface CostData {
  totalCost: number;
  costPerInteraction?: number;
  estimatedMonthlyCost?: number;
}

export interface ResourceMetadata {
  createdAt?: string;
  updatedAt?: string;
  email?: string;
  phone?: string;
  location?: string;
  timezone?: string;
  experienceYears?: number;
  bio?: string;
  agentKey?: string;
  toolsCount?: number;
  expertiseCount?: number;
}

/**
 * Convert a Talent to UnifiedResource
 */
export function talentToResource(talent: Talent): UnifiedResource {
  const skills: SkillEntry[] = (talent.skills || []).map((s) => ({
    name: s.name,
    level: s.level,
    years: s.years,
  }));

  return {
    id: `talent-${talent.id}`,
    type: "talent",
    name:
      talent.full_name ||
      `${talent.first_name || ""} ${talent.last_name || ""}`.trim() ||
      talent.email,
    role: talent.role || "Team Member",
    description: talent.bio,
    status: talent.is_active ? "active" : "inactive",
    skills,
    tier: talent.tier,
    availability: talent.availability ?? 100,
    hourlyRate: talent.hourly_rate,
    dailyRate: talent.daily_rate,
    utilization: 100 - (talent.availability ?? 100), // inverse of availability
    performance: {
      tasksCompleted: talent.experience_years ? talent.experience_years * 12 : 0, // Estimate based on experience
      averageRating: talent.rating ?? 0,
      efficiency: talent.rating ? Math.round((talent.rating / 5) * 100) : 75, // Derive from rating or use baseline
    },
    costData: talent.hourly_rate
      ? {
          totalCost: 0,
          estimatedMonthlyCost: talent.hourly_rate * 160, // 160 hours/month
        }
      : undefined,
    metadata: {
      createdAt: talent.created_at,
      updatedAt: talent.updated_at,
      email: talent.email,
      phone: talent.phone,
      location: talent.location,
      timezone: talent.timezone,
      experienceYears: talent.experience_years,
      bio: talent.bio,
    },
  };
}

/**
 * Convert an Agent to UnifiedResource
 */
export function agentToResource(agent: Agent): UnifiedResource {
  const skills: SkillEntry[] = (agent.capabilities || []).map((cap) => ({
    name: cap,
    level: "expert" as const,
  }));

  return {
    id: `agent-${agent.agent_key}`,
    type: "agent",
    name: agent.name,
    role: agent.role || "AI Agent",
    description: agent.description,
    status: agent.status,
    skills,
    tier: agent.tier === "specialist" ? "principal" : agent.tier,
    availability: agent.status === "active" ? 100 : 0,
    hourlyRate: agent.cost_data?.cost_per_interaction
      ? agent.cost_data.cost_per_interaction * 10
      : 0,
    utilization:
      agent.status === "busy" ? 100 : agent.status === "active" ? 50 : 0,
    performance: {
      tasksCompleted: agent.performance_metrics?.total_tasks || 0,
      averageRating: (agent.performance_metrics?.success_rate || 0) / 20, // scale 0-100 to 0-5
      efficiency: agent.performance_metrics?.success_rate || 95,
      successRate: agent.performance_metrics?.success_rate,
      avgResponseTime: agent.performance_metrics?.avg_response_time,
    },
    costData: agent.cost_data
      ? {
          totalCost: agent.cost_data.total_cost,
          costPerInteraction: agent.cost_data.cost_per_interaction,
        }
      : {
          totalCost: 0,
          costPerInteraction: 0, // Ollama = $0
        },
    metadata: {
      agentKey: agent.agent_key,
      toolsCount: agent.tools_count,
      expertiseCount: agent.expertise_count,
    },
  };
}

/**
 * Extract numeric ID from unified resource ID
 */
export function getResourceId(resource: UnifiedResource): number | string {
  const parts = resource.id.split("-");
  if (parts[0] === "talent") {
    return parseInt(parts[1], 10);
  }
  return parts.slice(1).join("-"); // agent keys may contain hyphens
}

/**
 * Get resource type from ID string
 */
export function getResourceTypeFromId(id: string): ResourceType {
  return id.startsWith("talent-") ? "talent" : "agent";
}
