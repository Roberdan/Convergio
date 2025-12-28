<script lang="ts">
	import { onMount } from 'svelte';
	import {
		workforceStore,
		filteredResources,
		workforceSummary
	} from '$lib/stores/workforceStore';
	import {
		WorkforceOverview,
		WorkforceFilters,
		WorkforceList,
		SkillMatrix,
		CapacityGauge,
		ResourceDetail
	} from '$lib/components/workforce';
	import type { UnifiedResource } from '$lib/types/resource';

	let loading = true;
	let error: string | null = null;
	let selectedResource: UnifiedResource | null = null;
	let showDetailModal = false;

	onMount(async () => {
		try {
			await workforceStore.loadAll();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load workforce';
		} finally {
			loading = false;
		}
	});

	function handleResourceSelect(event: CustomEvent<UnifiedResource>) {
		selectedResource = event.detail;
		showDetailModal = true;
	}

	function handleCloseDetail() {
		showDetailModal = false;
		selectedResource = null;
	}

	async function handleRefresh() {
		loading = true;
		error = null;
		try {
			await workforceStore.refresh();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to refresh';
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>Workforce - Convergio</title>
</svelte:head>

<div class="workforce-page min-h-screen bg-surface-50">
	<!-- Page Header -->
	<div class="bg-white border-b border-surface-200">
		<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
			<div class="flex items-center justify-between">
				<div>
					<h1 class="text-2xl font-bold text-surface-900">Workforce Management</h1>
					<p class="mt-1 text-sm text-surface-600">
						Manage your unified workforce of talents and AI agents
					</p>
				</div>
				<div class="flex items-center gap-3">
					<button
						on:click={handleRefresh}
						disabled={loading}
						class="inline-flex items-center px-4 py-2 text-sm font-medium text-surface-700 bg-white border border-surface-300 rounded-lg hover:bg-surface-50 disabled:opacity-50 transition-colors"
					>
						<svg class="w-4 h-4 mr-2 {loading ? 'animate-spin' : ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
						</svg>
						Refresh
					</button>
					<a
						href="/talents"
						class="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 transition-colors"
					>
						<svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
						</svg>
						Add Talent
					</a>
				</div>
			</div>
		</div>
	</div>

	<!-- Main Content -->
	<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
		{#if error}
			<div class="mb-6 p-4 bg-error-50 border border-error-200 rounded-lg">
				<div class="flex items-center">
					<svg class="w-5 h-5 text-error-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
					</svg>
					<span class="text-error-700">{error}</span>
				</div>
			</div>
		{/if}

		<!-- Overview Stats -->
		<WorkforceOverview {loading} />

		<!-- Filters -->
		<WorkforceFilters />

		<!-- Main Grid -->
		<div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
			<!-- Resource List (2 columns) -->
			<div class="lg:col-span-2">
				<div class="bg-white rounded-xl shadow-sm border border-surface-200 p-6">
					<div class="flex items-center justify-between mb-4">
						<h2 class="text-lg font-semibold text-surface-900">
							Resources
							<span class="text-sm font-normal text-surface-500 ml-2">
								({$filteredResources.length} of {$workforceSummary.totalResources})
							</span>
						</h2>
						<div class="flex items-center gap-2">
							<button class="p-2 text-surface-500 hover:text-surface-700 hover:bg-surface-100 rounded-lg transition-colors" title="Grid view" aria-label="Switch to grid view">
								<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
								</svg>
							</button>
							<button class="p-2 text-surface-500 hover:text-surface-700 hover:bg-surface-100 rounded-lg transition-colors" title="List view" aria-label="Switch to list view">
								<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h16M4 18h16" />
								</svg>
							</button>
						</div>
					</div>
					<WorkforceList
						resources={$filteredResources}
						{loading}
						{selectedResource}
						on:select={handleResourceSelect}
					/>
				</div>
			</div>

			<!-- Sidebar (1 column) -->
			<div class="space-y-6">
				<!-- Capacity Gauge -->
				<CapacityGauge resources={$filteredResources} />

				<!-- Skill Matrix -->
				<SkillMatrix resources={$filteredResources} />
			</div>
		</div>
	</div>
</div>

<!-- Resource Detail Modal -->
{#if selectedResource}
	<ResourceDetail
		resource={selectedResource}
		open={showDetailModal}
		on:close={handleCloseDetail}
	/>
{/if}
