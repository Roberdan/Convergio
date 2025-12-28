/**
 * WS3: Workforce Store
 * Svelte store for unified workforce management
 */

import { writable, derived, get } from "svelte/store";
import {
  workforceService,
  type WorkforceFilter,
  type WorkforceSummary,
} from "$lib/services/workforceService";
import type { UnifiedResource } from "$lib/types/resource";

// State types
interface WorkforceState {
  resources: UnifiedResource[];
  loading: boolean;
  error: string | null;
  lastUpdated: Date | null;
  filter: WorkforceFilter;
  selectedResource: UnifiedResource | null;
}

// Initial state
const initialState: WorkforceState = {
  resources: [],
  loading: false,
  error: null,
  lastUpdated: null,
  filter: { type: "all", status: "all" },
  selectedResource: null,
};

// Create the store
function createWorkforceStore() {
  const { subscribe, set, update } = writable<WorkforceState>(initialState);

  return {
    subscribe,

    /**
     * Load all workforce resources
     */
    async loadAll(): Promise<void> {
      update((state) => ({ ...state, loading: true, error: null }));

      try {
        const resources = await workforceService.getAll();
        update((state) => ({
          ...state,
          resources,
          loading: false,
          lastUpdated: new Date(),
        }));
      } catch (error) {
        update((state) => ({
          ...state,
          loading: false,
          error:
            error instanceof Error ? error.message : "Failed to load workforce",
        }));
      }
    },

    /**
     * Set filter and optionally reload
     */
    setFilter(filter: Partial<WorkforceFilter>, reload: boolean = false): void {
      update((state) => ({
        ...state,
        filter: { ...state.filter, ...filter },
      }));

      if (reload) {
        this.loadAll();
      }
    },

    /**
     * Clear all filters
     */
    clearFilters(): void {
      update((state) => ({
        ...state,
        filter: { type: "all", status: "all" },
      }));
    },

    /**
     * Select a resource for detail view
     */
    selectResource(resource: UnifiedResource | null): void {
      update((state) => ({ ...state, selectedResource: resource }));
    },

    /**
     * Get resources by skill
     */
    async getBySkill(skillName: string): Promise<UnifiedResource[]> {
      const state = get({ subscribe });
      return workforceService.applyFilter(state.resources, {
        skill: skillName,
      });
    },

    /**
     * Get available resources
     */
    async getAvailable(
      minAvailability: number = 50,
    ): Promise<UnifiedResource[]> {
      const state = get({ subscribe });
      return workforceService.applyFilter(state.resources, {
        minAvailability,
        status: "active",
      });
    },

    /**
     * Search resources
     */
    search(query: string): void {
      update((state) => ({
        ...state,
        filter: { ...state.filter, search: query },
      }));
    },

    /**
     * Refresh data from server
     */
    async refresh(): Promise<void> {
      return this.loadAll();
    },

    /**
     * Reset store to initial state
     */
    reset(): void {
      set(initialState);
    },
  };
}

// Export the store instance
export const workforceStore = createWorkforceStore();

// Derived stores for filtered views
export const filteredResources = derived(workforceStore, ($state) =>
  workforceService.applyFilter($state.resources, $state.filter),
);

export const talentResources = derived(workforceStore, ($state) =>
  $state.resources.filter((r) => r.type === "talent"),
);

export const agentResources = derived(workforceStore, ($state) =>
  $state.resources.filter((r) => r.type === "agent"),
);

export const activeResources = derived(workforceStore, ($state) =>
  $state.resources.filter((r) => r.status === "active"),
);

export const availableResources = derived(workforceStore, ($state) =>
  $state.resources.filter((r) => r.availability >= 50 && r.status === "active"),
);

// Derived store for summary statistics
export const workforceSummary = derived(workforceStore, ($state) => {
  const all = $state.resources;
  const talents = all.filter((r) => r.type === "talent");
  const agents = all.filter((r) => r.type === "agent");
  const active = all.filter((r) => r.status === "active");

  const avgUtilization =
    all.length > 0
      ? all.reduce((sum, r) => sum + r.utilization, 0) / all.length
      : 0;

  const totalCapacity = all.reduce((sum, _r) => sum + 100, 0);
  const availableCapacity = all.reduce((sum, r) => sum + r.availability, 0);

  // Calculate skill distribution
  const skillDistribution: Record<string, number> = {};
  all.forEach((r) => {
    r.skills.forEach((s) => {
      skillDistribution[s.name] = (skillDistribution[s.name] || 0) + 1;
    });
  });

  // Calculate tier distribution
  const tierDistribution: Record<string, number> = {};
  all.forEach((r) => {
    const tier = r.tier || "unspecified";
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
    tierDistribution,
  } as WorkforceSummary;
});

// Skill list derived from all resources
export const allSkills = derived(workforceStore, ($state) => {
  const skillSet = new Set<string>();
  $state.resources.forEach((r) => {
    r.skills.forEach((s) => skillSet.add(s.name));
  });
  return Array.from(skillSet).sort();
});
