<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import type { UnifiedResource } from '$lib/types/resource';

	export let resources: UnifiedResource[] = [];
	export let loading = false;
	export let selectedResource: UnifiedResource | null = null;

	const dispatch = createEventDispatcher<{ select: UnifiedResource }>();

	function getTypeColor(type: string) {
		return type === 'talent'
			? 'bg-blue-100 text-blue-700 border-blue-200'
			: 'bg-purple-100 text-purple-700 border-purple-200';
	}

	function getStatusColor(status: string) {
		switch (status) {
			case 'active': return 'bg-success-100 text-success-700';
			case 'inactive': return 'bg-surface-100 text-surface-600';
			case 'busy': return 'bg-warning-100 text-warning-700';
			case 'error': return 'bg-error-100 text-error-700';
			default: return 'bg-surface-100 text-surface-600';
		}
	}

	function getUtilizationColor(utilization: number) {
		if (utilization >= 90) return 'text-error-600';
		if (utilization >= 70) return 'text-warning-600';
		return 'text-success-600';
	}

	function getTierBadge(tier: string | undefined) {
		if (!tier) return null;
		const colors: Record<string, string> = {
			junior: 'bg-green-100 text-green-700',
			mid: 'bg-blue-100 text-blue-700',
			senior: 'bg-purple-100 text-purple-700',
			lead: 'bg-orange-100 text-orange-700',
			principal: 'bg-red-100 text-red-700',
			specialist: 'bg-indigo-100 text-indigo-700'
		};
		return colors[tier] || 'bg-surface-100 text-surface-700';
	}

	function handleSelect(resource: UnifiedResource) {
		dispatch('select', resource);
	}
</script>

<div class="workforce-list">
	{#if loading}
		<div class="flex items-center justify-center py-12">
			<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
		</div>
	{:else if resources.length === 0}
		<div class="text-center py-12 bg-white rounded-xl border border-surface-200">
			<svg class="w-12 h-12 text-surface-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
			</svg>
			<p class="text-surface-600">No resources found matching your criteria</p>
		</div>
	{:else}
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
			{#each resources as resource (resource.id)}
				<div
					class="resource-card bg-white rounded-xl shadow-sm border border-surface-200 p-4 cursor-pointer transition-all duration-200 hover:shadow-md hover:border-primary-300 {selectedResource?.id === resource.id ? 'ring-2 ring-primary-500' : ''}"
					on:click={() => handleSelect(resource)}
					on:keypress={(e) => e.key === 'Enter' && handleSelect(resource)}
					role="button"
					tabindex="0"
				>
					<!-- Header -->
					<div class="flex items-start justify-between mb-3">
						<div class="flex items-center gap-3">
							<div class="w-10 h-10 rounded-full flex items-center justify-center {resource.type === 'agent' ? 'bg-purple-100' : 'bg-primary-100'}">
								{#if resource.type === 'agent'}
									<span class="text-lg">🤖</span>
								{:else}
									<span class="font-semibold text-primary-700">{resource.name.charAt(0)}</span>
								{/if}
							</div>
							<div>
								<h4 class="font-medium text-surface-900 line-clamp-1">{resource.name}</h4>
								<p class="text-sm text-surface-600 line-clamp-1">{resource.role}</p>
							</div>
						</div>
					</div>

					<!-- Badges Row -->
					<div class="flex flex-wrap gap-2 mb-3">
						<span class="px-2 py-0.5 text-xs font-medium rounded-full border {getTypeColor(resource.type)}">
							{resource.type}
						</span>
						<span class="px-2 py-0.5 text-xs font-medium rounded-full {getStatusColor(resource.status)}">
							{resource.status}
						</span>
						{#if resource.tier}
							<span class="px-2 py-0.5 text-xs font-medium rounded-full {getTierBadge(resource.tier)}">
								{resource.tier}
							</span>
						{/if}
					</div>

					<!-- Availability/Utilization Bar -->
					<div class="mb-3">
						<div class="flex items-center justify-between mb-1">
							<span class="text-xs text-surface-600">Availability</span>
							<span class="text-xs font-medium {getUtilizationColor(resource.utilization)}">{resource.availability}%</span>
						</div>
						<div class="w-full bg-surface-200 rounded-full h-1.5">
							<div
								class="bg-primary-500 h-1.5 rounded-full transition-all duration-500"
								style="width: {resource.availability}%"
							></div>
						</div>
					</div>

					<!-- Skills -->
					{#if resource.skills.length > 0}
						<div class="mb-3">
							<div class="flex flex-wrap gap-1">
								{#each resource.skills.slice(0, 3) as skill}
									<span class="px-2 py-0.5 text-xs bg-surface-100 text-surface-600 rounded">
										{skill.name}
									</span>
								{/each}
								{#if resource.skills.length > 3}
									<span class="px-2 py-0.5 text-xs bg-surface-100 text-surface-500 rounded">
										+{resource.skills.length - 3}
									</span>
								{/if}
							</div>
						</div>
					{/if}

					<!-- Stats -->
					<div class="grid grid-cols-3 gap-2 text-center pt-3 border-t border-surface-100">
						<div>
							<div class="text-xs text-surface-500">Tasks</div>
							<div class="font-medium text-surface-900">{resource.performance.tasksCompleted}</div>
						</div>
						<div>
							<div class="text-xs text-surface-500">Rating</div>
							<div class="font-medium text-surface-900">{resource.performance.averageRating.toFixed(1)}</div>
						</div>
						<div>
							<div class="text-xs text-surface-500">Efficiency</div>
							<div class="font-medium text-surface-900">{resource.performance.efficiency}%</div>
						</div>
					</div>

					<!-- Cost (if available) -->
					{#if resource.hourlyRate}
						<div class="mt-3 pt-3 border-t border-surface-100 text-center">
							<span class="text-sm text-surface-600">
								${resource.hourlyRate}/hr
							</span>
						</div>
					{/if}
				</div>
			{/each}
		</div>
	{/if}
</div>

<style>
	.resource-card {
		background: linear-gradient(135deg, rgb(255 255 255) 0%, rgb(248 250 252) 100%);
	}
</style>
