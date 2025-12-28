<script lang="ts">
	import { workforceStore, allSkills } from '$lib/stores/workforceStore';
	import type { ResourceType } from '$lib/types/resource';

	// Local state
	let searchQuery = '';
	let selectedType: ResourceType | 'all' = 'all';
	let selectedStatus: 'active' | 'inactive' | 'busy' | 'all' = 'all';
	let selectedTier: string = '';
	let minAvailability: number = 0;

	const tiers = ['junior', 'mid', 'senior', 'lead', 'principal'];

	function applyFilters() {
		workforceStore.setFilter({
			type: selectedType,
			status: selectedStatus,
			tier: selectedTier || undefined,
			minAvailability: minAvailability > 0 ? minAvailability : undefined,
			search: searchQuery || undefined
		});
	}

	function clearFilters() {
		searchQuery = '';
		selectedType = 'all';
		selectedStatus = 'all';
		selectedTier = '';
		minAvailability = 0;
		workforceStore.clearFilters();
	}

	// Auto-apply filters on change
	$: {
		searchQuery;
		selectedType;
		selectedStatus;
		selectedTier;
		minAvailability;
		applyFilters();
	}
</script>

<div class="workforce-filters bg-white rounded-xl shadow-sm border border-surface-200 p-4 mb-6">
	<div class="flex flex-wrap items-center gap-4">
		<!-- Search -->
		<div class="flex-1 min-w-[200px]">
			<label for="workforce-search" class="sr-only">Search by name, role, or skill</label>
			<div class="relative">
				<svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-surface-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
				</svg>
				<input
					id="workforce-search"
					type="text"
					bind:value={searchQuery}
					placeholder="Search by name, role, or skill..."
					class="w-full pl-10 pr-4 py-2 border border-surface-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
				/>
			</div>
		</div>

		<!-- Type Filter -->
		<div>
			<label for="workforce-type" class="sr-only">Filter by resource type</label>
			<select
				id="workforce-type"
				bind:value={selectedType}
				class="px-3 py-2 border border-surface-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
			>
				<option value="all">All Types</option>
				<option value="talent">Talents</option>
				<option value="agent">AI Agents</option>
			</select>
		</div>

		<!-- Status Filter -->
		<div>
			<label for="workforce-status" class="sr-only">Filter by status</label>
			<select
				id="workforce-status"
				bind:value={selectedStatus}
				class="px-3 py-2 border border-surface-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
			>
				<option value="all">All Status</option>
				<option value="active">Active</option>
				<option value="inactive">Inactive</option>
				<option value="busy">Busy</option>
			</select>
		</div>

		<!-- Tier Filter -->
		<div>
			<label for="workforce-tier" class="sr-only">Filter by tier</label>
			<select
				id="workforce-tier"
				bind:value={selectedTier}
				class="px-3 py-2 border border-surface-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
			>
				<option value="">All Tiers</option>
				{#each tiers as tier}
					<option value={tier}>{tier.charAt(0).toUpperCase() + tier.slice(1)}</option>
				{/each}
			</select>
		</div>

		<!-- Availability Slider -->
		<div class="flex items-center gap-2">
			<label for="min-availability" class="text-sm text-surface-600 whitespace-nowrap">Min Availability:</label>
			<input
				id="min-availability"
				type="range"
				bind:value={minAvailability}
				min="0"
				max="100"
				step="10"
				class="w-24"
				aria-valuemin="0"
				aria-valuemax="100"
				aria-valuenow={minAvailability}
			/>
			<span class="text-sm font-medium text-surface-900 w-10">{minAvailability}%</span>
		</div>

		<!-- Clear Filters -->
		<button
			on:click={clearFilters}
			class="px-4 py-2 text-sm text-surface-600 hover:text-surface-900 hover:bg-surface-100 rounded-lg transition-colors"
		>
			Clear Filters
		</button>
	</div>

	<!-- Active Skills -->
	{#if $allSkills.length > 0}
		<div class="mt-4 pt-4 border-t border-surface-200">
			<p class="text-sm text-surface-600 mb-2">Popular Skills:</p>
			<div class="flex flex-wrap gap-2">
				{#each $allSkills.slice(0, 10) as skill}
					<button
						on:click={() => { searchQuery = skill; applyFilters(); }}
						class="px-3 py-1 text-sm bg-surface-100 text-surface-700 rounded-full hover:bg-primary-100 hover:text-primary-700 transition-colors"
					>
						{skill}
					</button>
				{/each}
			</div>
		</div>
	{/if}
</div>
