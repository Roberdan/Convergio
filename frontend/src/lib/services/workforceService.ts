/**
 * WS3: Unified Workforce Service
 * Combines Talents and Agents into a unified workforce view
 */

import { talentsService, type Talent, type ProjectTeam, type ResourceProjects } from './talentsService';
import { agentsService, type Agent } from './agentsService';
import {
  type UnifiedResource,
  type ResourceType,
  talentToResource,
  agentToResource,
  getResourceId
} from '$lib/types/resource';

export interface WorkforceFilter {
  type?: ResourceType | 'all';
  status?: 'active' | 'inactive' | 'busy' | 'all';
  skill?: string;
  minAvailability?: number;
  tier?: string;
  search?: string;
}

export interface WorkforceSummary {
  totalResources: number;
  totalTalents: number;
  totalAgents: number;
  activeResources: number;
  averageUtilization: number;
  totalCapacity: number;
  availableCapacity: number;
  skillDistribution: Record<string, number>;
  tierDistribution: Record<string, number>;
}

class WorkforceService {
  private baseUrl = `${import.meta.env.VITE_API_URL || 'http://localhost:9000'}/api/v1`;

  /**
   * Get all workforce resources (talents + agents)
   */
  async getAll(): Promise<UnifiedResource[]> {
    const [talents, agents] = await Promise.all([
      talentsService.getTalents(),
      agentsService.getAgents()
    ]);

    const talentResources = talents.map(talentToResource);
    const agentResources = agents.map(agentToResource);

    return [...talentResources, ...agentResources];
  }

  /**
   * Get filtered workforce resources
   */
  async getFiltered(filter: WorkforceFilter): Promise<UnifiedResource[]> {
    const all = await this.getAll();
    return this.applyFilter(all, filter);
  }

  /**
   * Apply filter to resources in-memory
   */
  applyFilter(resources: UnifiedResource[], filter: WorkforceFilter): UnifiedResource[] {
    return resources.filter(resource => {
      // Type filter
      if (filter.type && filter.type !== 'all' && resource.type !== filter.type) {
        return false;
      }

      // Status filter
      if (filter.status && filter.status !== 'all' && resource.status !== filter.status) {
        return false;
      }

      // Skill filter
      if (filter.skill) {
        const hasSkill = resource.skills.some(
          s => s.name.toLowerCase().includes(filter.skill!.toLowerCase())
        );
        if (!hasSkill) return false;
      }

      // Availability filter
      if (filter.minAvailability !== undefined && resource.availability < filter.minAvailability) {
        return false;
      }

      // Tier filter
      if (filter.tier && resource.tier !== filter.tier) {
        return false;
      }

      // Search filter
      if (filter.search) {
        const searchLower = filter.search.toLowerCase();
        const matchesName = resource.name.toLowerCase().includes(searchLower);
        const matchesRole = resource.role.toLowerCase().includes(searchLower);
        const matchesSkill = resource.skills.some(s => s.name.toLowerCase().includes(searchLower));
        if (!matchesName && !matchesRole && !matchesSkill) return false;
      }

      return true;
    });
  }

  /**
   * Get resources with specific skill
   */
  async getBySkill(skillName: string): Promise<UnifiedResource[]> {
    return this.getFiltered({ skill: skillName });
  }

  /**
   * Get available resources (availability >= threshold)
   */
  async getAvailable(minAvailability: number = 50): Promise<UnifiedResource[]> {
    return this.getFiltered({ minAvailability, status: 'active' });
  }

  /**
   * Get workforce summary statistics
   */
  async getSummary(): Promise<WorkforceSummary> {
    const all = await this.getAll();

    const talents = all.filter(r => r.type === 'talent');
    const agents = all.filter(r => r.type === 'agent');
    const active = all.filter(r => r.status === 'active');

    const avgUtilization = all.length > 0
      ? all.reduce((sum, r) => sum + r.utilization, 0) / all.length
      : 0;

    const totalCapacity = all.reduce((sum, r) => sum + 100, 0);
    const availableCapacity = all.reduce((sum, r) => sum + r.availability, 0);

    // Calculate skill distribution
    const skillDistribution: Record<string, number> = {};
    all.forEach(r => {
      r.skills.forEach(s => {
        skillDistribution[s.name] = (skillDistribution[s.name] || 0) + 1;
      });
    });

    // Calculate tier distribution
    const tierDistribution: Record<string, number> = {};
    all.forEach(r => {
      const tier = r.tier || 'unspecified';
      tierDistribution[tier] = (tierDistribution[tier] || 0) + 1;
    });

    return {
      totalResources: all.length,
      totalTalents: talents.length,
      totalAgents: agents.length,
      activeResources: active.length,
      averageUtilization: Math.round(avgUtilization),
      totalCapacity,
      availableCapacity,
      skillDistribution,
      tierDistribution
    };
  }

  /**
   * Get resource by ID
   */
  async getById(id: string): Promise<UnifiedResource | null> {
    const all = await this.getAll();
    return all.find(r => r.id === id) || null;
  }

  /**
   * Get project team with unified resources
   */
  async getProjectTeam(projectId: number): Promise<{
    talents: UnifiedResource[];
    agents: UnifiedResource[];
    totalAllocation: number;
  }> {
    const team = await talentsService.getProjectTeam(projectId);
    const allResources = await this.getAll();

    const talents = team.talents.map(assignment => {
      const resource = allResources.find(r =>
        r.type === 'talent' && getResourceId(r) === assignment.resource_id
      );
      return resource;
    }).filter(Boolean) as UnifiedResource[];

    const agents = team.agents.map(assignment => {
      const resource = allResources.find(r =>
        r.type === 'agent' && getResourceId(r) === assignment.resource_id
      );
      return resource;
    }).filter(Boolean) as UnifiedResource[];

    return {
      talents,
      agents,
      totalAllocation: team.total_allocation
    };
  }

  /**
   * Get resource's project assignments
   */
  async getResourceProjects(resource: UnifiedResource): Promise<ResourceProjects | null> {
    if (resource.type === 'talent') {
      const talentId = getResourceId(resource) as number;
      return talentsService.getTalentProjects(talentId);
    }
    // TODO: Implement agent projects when API is available
    return null;
  }

  /**
   * Calculate team cost estimate
   */
  calculateTeamCost(resources: UnifiedResource[], allocations: Record<string, number>): {
    hourly: number;
    daily: number;
    monthly: number;
  } {
    let hourly = 0;
    let daily = 0;

    resources.forEach(resource => {
      const allocation = (allocations[resource.id] || 100) / 100;
      if (resource.hourlyRate) {
        hourly += resource.hourlyRate * allocation;
      }
      if (resource.dailyRate) {
        daily += resource.dailyRate * allocation;
      } else if (resource.hourlyRate) {
        daily += resource.hourlyRate * 8 * allocation;
      }
    });

    return {
      hourly: Math.round(hourly * 100) / 100,
      daily: Math.round(daily * 100) / 100,
      monthly: Math.round(daily * 20 * 100) / 100 // 20 working days
    };
  }

  /**
   * Get skill coverage analysis
   */
  analyzeSkillCoverage(resources: UnifiedResource[], requiredSkills: string[]): {
    covered: string[];
    missing: string[];
    coverage: number;
    skillDetails: Array<{
      skill: string;
      covered: boolean;
      resources: string[];
      bestLevel: string;
    }>;
  } {
    const skillDetails = requiredSkills.map(skill => {
      const matchingResources = resources.filter(r =>
        r.skills.some(s => s.name.toLowerCase() === skill.toLowerCase())
      );

      const bestLevel = matchingResources.reduce((best, r) => {
        const skillEntry = r.skills.find(s => s.name.toLowerCase() === skill.toLowerCase());
        if (!skillEntry) return best;
        const levels = ['beginner', 'intermediate', 'advanced', 'expert'];
        const currentIndex = levels.indexOf(skillEntry.level);
        const bestIndex = levels.indexOf(best);
        return currentIndex > bestIndex ? skillEntry.level : best;
      }, 'beginner');

      return {
        skill,
        covered: matchingResources.length > 0,
        resources: matchingResources.map(r => r.name),
        bestLevel
      };
    });

    const covered = skillDetails.filter(s => s.covered).map(s => s.skill);
    const missing = skillDetails.filter(s => !s.covered).map(s => s.skill);

    return {
      covered,
      missing,
      coverage: requiredSkills.length > 0
        ? Math.round((covered.length / requiredSkills.length) * 100)
        : 100,
      skillDetails
    };
  }
}

export const workforceService = new WorkforceService();
