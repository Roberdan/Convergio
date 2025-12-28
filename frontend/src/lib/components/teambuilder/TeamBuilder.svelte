<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { workforceService } from '$lib/services/workforceService';
	import type { UnifiedResource } from '$lib/types/resource';
	import ResourceSelector from './ResourceSelector.svelte';
	import AllocationSlider from './AllocationSlider.svelte';
	import TeamCostEstimate from './TeamCostEstimate.svelte';
	import SkillCoverage from './SkillCoverage.svelte';

	// Props
	export let requiredSkills: string[] = [];
	export let availableResources: UnifiedResource[] = [];

	// State
	let selectedResources: UnifiedResource[] = [];
	let allocations: Record<string, number> = {};
	let loading = false;

	const dispatch = createEventDispatcher<{
		save: { resources: UnifiedResource[]; allocations: Record<string, number> };
		cancel: void;
	}>();

	// Cost calculation
	$: costEstimate = workforceService.calculateTeamCost(selectedResources, allocations);

	// Skill coverage
	$: skillCoverage = workforceService.analyzeSkillCoverage(selectedResources, requiredSkills);

	function handleResourceAdd(resource: UnifiedResource) {
		if (!selectedResources.find(r => r.id === resource.id)) {
			selectedResources = [...selectedResources, resource];
			allocations = { ...allocations, [resource.id]: 100 };
		}
	}

	function handleResourceRemove(resourceId: string) {
		selectedResources = selectedResources.filter(r => r.id !== resourceId);
		const newAllocations = { ...allocations };
		delete newAllocations[resourceId];
		allocations = newAllocations;
	}

	function handleAllocationChange(resourceId: string, value: number) {
		allocations = { ...allocations, [resourceId]: value };
	}

	async function handleSave() {
		loading = true;
		try {
			dispatch('save', { resources: selectedResources, allocations });
		} finally {
			loading = false;
		}
	}

	function handleCancel() {
		dispatch('cancel');
	}
</script>

<div class="team-builder bg-white rounded-xl shadow-lg border border-surface-200 overflow-hidden">
	<!-- Header -->
	<div class="p-6 border-b border-surface-200 bg-gradient-to-r from-primary-50 to-blue-50">
		<h2 class="text-xl font-bold text-surface-900">Build Project Team</h2>
		<p class="text-sm text-surface-600 mt-1">
			Select resources and configure allocations for the project
		</p>
	</div>

	<div class="grid grid-cols-1 lg:grid-cols-3 gap-6 p-6">
		<!-- Resource Selector (Left) -->
		<div class="lg:col-span-1">
			<ResourceSelector
				resources={availableResources}
				selected={selectedResources}
				on:add={(e) => handleResourceAdd(e.detail)}
			/>
		</div>

		<!-- Team Configuration (Middle) -->
		<div class="lg:col-span-1 space-y-4">
			<h3 class="text-sm font-semibold text-surface-700 uppercase tracking-wider">Team Members</h3>

			{#if selectedResources.length === 0}
				<div class="text-center py-8 text-surface-500 bg-surface-50 rounded-lg">
					<svg class="w-12 h-12 mx-auto mb-2 text-surface-300" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
					</svg>
					<p>Select resources from the left to add to the team</p>
				</div>
			{:else}
				<div class="space-y-3 max-h-[400px] overflow-y-auto">
					{#each selectedResources as resource (resource.id)}
						<div class="bg-surface-50 rounded-lg p-4">
							<div class="flex items-center justify-between mb-3">
								<div class="flex items-center gap-3">
									<div class="w-8 h-8 rounded-full flex items-center justify-center {resource.type === 'agent' ? 'bg-purple-100' : 'bg-primary-100'}">
										{#if resource.type === 'agent'}
											<span>🤖</span>
										{:else}
											<span class="text-sm font-medium text-primary-700">{resource.name.charAt(0)}</span>
										{/if}
									</div>
									<div>
										<div class="font-medium text-surface-900">{resource.name}</div>
										<div class="text-xs text-surface-500">{resource.role}</div>
									</div>
								</div>
								<button
									on:click={() => handleResourceRemove(resource.id)}
									class="p-1 text-surface-400 hover:text-error-500 rounded transition-colors"
									aria-label="Remove {resource.name} from team"
								>
									<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
									</svg>
								</button>
							</div>
							<AllocationSlider
								value={allocations[resource.id] || 100}
								maxAvailable={resource.availability}
								on:change={(e) => handleAllocationChange(resource.id, e.detail)}
							/>
						</div>
					{/each}
				</div>
			{/if}
		</div>

		<!-- Cost & Coverage (Right) -->
		<div class="lg:col-span-1 space-y-6">
			<TeamCostEstimate {costEstimate} memberCount={selectedResources.length} />

			{#if requiredSkills.length > 0}
				<SkillCoverage {skillCoverage} />
			{/if}
		</div>
	</div>

	<!-- Footer -->
	<div class="p-6 border-t border-surface-200 bg-surface-50">
		<div class="flex items-center justify-between">
			<div class="text-sm text-surface-600">
				{selectedResources.length} member{selectedResources.length !== 1 ? 's' : ''} selected
			</div>
			<div class="flex gap-3">
				<button
					on:click={handleCancel}
					class="px-4 py-2 text-surface-700 bg-white border border-surface-300 rounded-lg hover:bg-surface-50 transition-colors"
				>
					Cancel
				</button>
				<button
					on:click={handleSave}
					disabled={selectedResources.length === 0 || loading}
					class="px-4 py-2 text-white bg-primary-600 rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
				>
					{#if loading}
						<svg class="w-4 h-4 animate-spin mr-2 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
						</svg>
					{/if}
					Save Team
				</button>
			</div>
		</div>
	</div>
</div>
