<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import type { UnifiedResource } from '$lib/types/resource';

	export let resources: UnifiedResource[] = [];
	export let selected: UnifiedResource[] = [];

	let searchQuery = '';
	let filterType: 'all' | 'talent' | 'agent' = 'all';

	const dispatch = createEventDispatcher<{ add: UnifiedResource }>();

	$: filteredResources = resources.filter(resource => {
		// Exclude already selected
		if (selected.find(r => r.id === resource.id)) return false;

		// Type filter
		if (filterType !== 'all' && resource.type !== filterType) return false;

		// Search filter
		if (searchQuery) {
			const query = searchQuery.toLowerCase();
			const matchesName = resource.name.toLowerCase().includes(query);
			const matchesRole = resource.role.toLowerCase().includes(query);
			const matchesSkill = resource.skills.some(s => s.name.toLowerCase().includes(query));
			if (!matchesName && !matchesRole && !matchesSkill) return false;
		}

		// Only show available resources
		if (resource.availability < 10 || resource.status !== 'active') return false;

		return true;
	});

	function handleAdd(resource: UnifiedResource) {
		dispatch('add', resource);
	}
</script>

<div class="resource-selector">
	<h3 class="text-sm font-semibold text-surface-700 uppercase tracking-wider mb-3">Available Resources</h3>

	<!-- Search & Filter -->
	<div class="space-y-2 mb-4">
		<div class="relative">
			<svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-surface-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
			</svg>
			<input
				type="text"
				bind:value={searchQuery}
				placeholder="Search resources..."
				class="w-full pl-10 pr-4 py-2 text-sm border border-surface-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
			/>
		</div>
		<div class="flex gap-2">
			<button
				on:click={() => filterType = 'all'}
				class="px-3 py-1 text-xs rounded-full transition-colors {filterType === 'all' ? 'bg-primary-100 text-primary-700' : 'bg-surface-100 text-surface-600 hover:bg-surface-200'}"
			>
				All
			</button>
			<button
				on:click={() => filterType = 'talent'}
				class="px-3 py-1 text-xs rounded-full transition-colors {filterType === 'talent' ? 'bg-blue-100 text-blue-700' : 'bg-surface-100 text-surface-600 hover:bg-surface-200'}"
			>
				Talents
			</button>
			<button
				on:click={() => filterType = 'agent'}
				class="px-3 py-1 text-xs rounded-full transition-colors {filterType === 'agent' ? 'bg-purple-100 text-purple-700' : 'bg-surface-100 text-surface-600 hover:bg-surface-200'}"
			>
				Agents
			</button>
		</div>
	</div>

	<!-- Resource List -->
	<div class="space-y-2 max-h-[400px] overflow-y-auto">
		{#if filteredResources.length === 0}
			<div class="text-center py-6 text-surface-500 text-sm">
				No available resources found
			</div>
		{:else}
			{#each filteredResources as resource (resource.id)}
				<button
					on:click={() => handleAdd(resource)}
					class="w-full text-left p-3 bg-white border border-surface-200 rounded-lg hover:border-primary-300 hover:bg-primary-50 transition-colors group"
				>
					<div class="flex items-center gap-3">
						<div class="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 {resource.type === 'agent' ? 'bg-purple-100' : 'bg-primary-100'}">
							{#if resource.type === 'agent'}
								<span class="text-sm">🤖</span>
							{:else}
								<span class="text-sm font-medium text-primary-700">{resource.name.charAt(0)}</span>
							{/if}
						</div>
						<div class="flex-1 min-w-0">
							<div class="font-medium text-surface-900 text-sm truncate">{resource.name}</div>
							<div class="text-xs text-surface-500 truncate">{resource.role}</div>
						</div>
						<div class="flex flex-col items-end">
							<span class="text-xs font-medium text-success-600">{resource.availability}%</span>
							<span class="text-xs text-surface-400">available</span>
						</div>
						<svg class="w-4 h-4 text-surface-300 group-hover:text-primary-500 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
						</svg>
					</div>
					{#if resource.skills.length > 0}
						<div class="mt-2 flex flex-wrap gap-1">
							{#each resource.skills.slice(0, 3) as skill}
								<span class="px-1.5 py-0.5 text-xs bg-surface-100 text-surface-600 rounded">
									{skill.name}
								</span>
							{/each}
							{#if resource.skills.length > 3}
								<span class="px-1.5 py-0.5 text-xs bg-surface-100 text-surface-400 rounded">
									+{resource.skills.length - 3}
								</span>
							{/if}
						</div>
					{/if}
				</button>
			{/each}
		{/if}
	</div>
</div>
