<script lang="ts">
	import { onMount } from 'svelte';
	import { workforceStore, filteredResources } from '$lib/stores/workforceStore';
	import { workforceService } from '$lib/services/workforceService';
	import type { UnifiedResource } from '$lib/types/resource';
	import { ResourceDetail } from '$lib/components/workforce';

	// Props
	export let projectId: string;

	// State
	let loading = true;
	let error: string | null = null;
	let selectedResource: UnifiedResource | null = null;
	let showDetailModal = false;
	let showAddResourceModal = false;
	let filterType: 'all' | 'talent' | 'agent' = 'all';
	let sortBy: 'utilization' | 'name' | 'efficiency' | 'availability' = 'utilization';

	onMount(async () => {
		await loadResources();
	});

	async function loadResources() {
		loading = true;
		error = null;
		try {
			await workforceStore.loadAll();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load resources';
			console.error('Error loading resources:', e);
		} finally {
			loading = false;
		}
	}

	function getTypeColor(type: string) {
		return type === 'talent'
			? 'bg-blue-100 text-blue-700 border-blue-200'
			: 'bg-purple-100 text-purple-700 border-purple-200';
	}

	function getUtilizationColor(utilization: number) {
		if (utilization >= 90) return 'text-error-600';
		if (utilization >= 70) return 'text-warning-600';
		return 'text-success-600';
	}

	function handleResourceClick(resource: UnifiedResource) {
		selectedResource = resource;
		showDetailModal = true;
	}

	function handleCloseDetail() {
		showDetailModal = false;
		selectedResource = null;
	}

	// Apply local filter and sort
	$: displayResources = $filteredResources
		.filter(resource => {
			if (filterType === 'all') return true;
			return resource.type === filterType;
		})
		.sort((a, b) => {
			switch (sortBy) {
				case 'name': return a.name.localeCompare(b.name);
				case 'utilization': return b.utilization - a.utilization;
				case 'efficiency': return b.performance.efficiency - a.performance.efficiency;
				case 'availability': return b.availability - a.availability;
				default: return 0;
			}
		});
</script>

<div class="resource-management bg-white rounded-xl shadow-sm border border-surface-200 overflow-hidden">
	<!-- Header -->
	<div class="p-6 border-b border-surface-200 bg-surface-50">
		<div class="flex items-center justify-between">
			<div>
				<h3 class="text-lg font-semibold text-surface-900">Resource Management</h3>
				<p class="text-sm text-surface-600">Team allocation, utilization, and performance tracking</p>
			</div>
			<div class="flex items-center space-x-3">
				<!-- Filter by Type -->
				<select bind:value={filterType} class="px-3 py-2 text-sm border border-surface-300 rounded-lg focus:ring-2 focus:ring-primary-500">
					<option value="all">All Types</option>
					<option value="talent">Talents</option>
					<option value="agent">AI Agents</option>
				</select>

				<!-- Sort By -->
				<select bind:value={sortBy} class="px-3 py-2 text-sm border border-surface-300 rounded-lg focus:ring-2 focus:ring-primary-500">
					<option value="utilization">Utilization</option>
					<option value="name">Name</option>
					<option value="efficiency">Efficiency</option>
					<option value="availability">Availability</option>
				</select>

				<a
					href="/workforce"
					class="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 transition-colors"
				>
					<svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
					</svg>
					Manage Team
				</a>
			</div>
		</div>
	</div>

	{#if loading}
		<div class="flex items-center justify-center py-12">
			<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
		</div>
	{:else if error}
		<div class="p-6">
			<div class="p-4 bg-error-50 border border-error-200 rounded-lg">
				<div class="flex items-center">
					<svg class="w-5 h-5 text-error-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
					</svg>
					<span class="text-error-700">{error}</span>
				</div>
				<button
					on:click={loadResources}
					class="mt-2 text-sm text-error-600 hover:text-error-700 underline"
				>
					Try again
				</button>
			</div>
		</div>
	{:else if displayResources.length === 0}
		<div class="p-12 text-center">
			<svg class="w-12 h-12 text-surface-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
			</svg>
			<p class="text-surface-600 mb-4">No resources found</p>
			<a
				href="/workforce"
				class="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 transition-colors"
			>
				View Workforce
			</a>
		</div>
	{:else}
		<!-- Resource Overview Cards -->
		<div class="p-6">
			<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 mb-6">
				{#each displayResources as resource (resource.id)}
					<div
						class="resource-card border border-surface-200 rounded-lg p-4 hover:shadow-md transition-shadow duration-200 cursor-pointer"
						on:click={() => handleResourceClick(resource)}
						on:keypress={(e) => e.key === 'Enter' && handleResourceClick(resource)}
						role="button"
						tabindex="0"
					>
						<div class="flex items-start justify-between mb-3">
							<div class="flex items-center space-x-3">
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
							<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border {getTypeColor(resource.type)}">
								{resource.type}
							</span>
						</div>

						<!-- Availability -->
						<div class="mb-3">
							<div class="flex items-center justify-between mb-1">
								<span class="text-sm text-surface-600">Availability</span>
								<span class="text-sm font-medium {getUtilizationColor(resource.utilization)}">{resource.availability}%</span>
							</div>
							<div class="w-full bg-surface-200 rounded-full h-2">
								<div class="bg-primary-500 h-2 rounded-full transition-all duration-500" style="width: {resource.availability}%"></div>
							</div>
						</div>

						<!-- Performance Metrics -->
						<div class="grid grid-cols-3 gap-2 text-center">
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

						<!-- Skills -->
						{#if resource.skills.length > 0}
							<div class="mt-3 pt-3 border-t border-surface-100">
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

						<!-- Cost -->
						{#if resource.hourlyRate}
							<div class="mt-2 text-center">
								<span class="text-xs text-surface-500">${resource.hourlyRate}/hr</span>
							</div>
						{/if}
					</div>
				{/each}
			</div>

			<!-- Summary -->
			<div class="flex items-center justify-between p-4 bg-surface-50 rounded-lg">
				<div class="flex items-center gap-6">
					<div class="text-sm">
						<span class="text-surface-600">Total:</span>
						<span class="font-medium text-surface-900 ml-1">{displayResources.length} resources</span>
					</div>
					<div class="text-sm">
						<span class="text-surface-600">Talents:</span>
						<span class="font-medium text-blue-600 ml-1">{displayResources.filter(r => r.type === 'talent').length}</span>
					</div>
					<div class="text-sm">
						<span class="text-surface-600">Agents:</span>
						<span class="font-medium text-purple-600 ml-1">{displayResources.filter(r => r.type === 'agent').length}</span>
					</div>
				</div>
				<a href="/workforce" class="text-sm text-primary-600 hover:text-primary-700 font-medium">
					View All Workforce →
				</a>
			</div>
		</div>
	{/if}
</div>

<!-- Resource Detail Modal -->
{#if selectedResource}
	<ResourceDetail
		resource={selectedResource}
		open={showDetailModal}
		on:close={handleCloseDetail}
	/>
{/if}

<style>
	.resource-card {
		background: linear-gradient(135deg, rgb(248 250 252) 0%, rgb(241 245 249) 100%);
	}

	:global(.dark) .resource-card {
		background: linear-gradient(135deg, rgb(15 23 42) 0%, rgb(30 41 59) 100%);
	}
</style>
