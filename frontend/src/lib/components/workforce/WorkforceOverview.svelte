<script lang="ts">
	import { workforceSummary } from '$lib/stores/workforceStore';

	// Props
	export let loading = false;
</script>

<div class="workforce-overview grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
	<!-- Total Resources -->
	<div class="stat-card bg-white rounded-xl shadow-sm border border-surface-200 p-4">
		<div class="flex items-center justify-between">
			<div>
				<p class="text-sm text-surface-600">Total Resources</p>
				<p class="text-2xl font-bold text-surface-900">
					{#if loading}
						<span class="animate-pulse">--</span>
					{:else}
						{$workforceSummary.totalResources}
					{/if}
				</p>
			</div>
			<div class="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center">
				<svg class="w-6 h-6 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
				</svg>
			</div>
		</div>
		<div class="mt-2 flex items-center gap-4 text-sm">
			<span class="text-blue-600">{$workforceSummary.totalTalents} Talents</span>
			<span class="text-purple-600">{$workforceSummary.totalAgents} Agents</span>
		</div>
	</div>

	<!-- Active Resources -->
	<div class="stat-card bg-white rounded-xl shadow-sm border border-surface-200 p-4">
		<div class="flex items-center justify-between">
			<div>
				<p class="text-sm text-surface-600">Active Resources</p>
				<p class="text-2xl font-bold text-success-600">
					{#if loading}
						<span class="animate-pulse">--</span>
					{:else}
						{$workforceSummary.activeResources}
					{/if}
				</p>
			</div>
			<div class="w-12 h-12 bg-success-100 rounded-lg flex items-center justify-center">
				<svg class="w-6 h-6 text-success-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
				</svg>
			</div>
		</div>
		<div class="mt-2 text-sm text-surface-500">
			{Math.round(($workforceSummary.activeResources / Math.max($workforceSummary.totalResources, 1)) * 100)}% of workforce
		</div>
	</div>

	<!-- Average Utilization -->
	<div class="stat-card bg-white rounded-xl shadow-sm border border-surface-200 p-4">
		<div class="flex items-center justify-between">
			<div>
				<p class="text-sm text-surface-600">Avg. Utilization</p>
				<p class="text-2xl font-bold {$workforceSummary.averageUtilization > 80 ? 'text-warning-600' : 'text-surface-900'}">
					{#if loading}
						<span class="animate-pulse">--</span>
					{:else}
						{$workforceSummary.averageUtilization}%
					{/if}
				</p>
			</div>
			<div class="w-12 h-12 bg-warning-100 rounded-lg flex items-center justify-center">
				<svg class="w-6 h-6 text-warning-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
				</svg>
			</div>
		</div>
		<div class="mt-2">
			<div class="w-full bg-surface-200 rounded-full h-2">
				<div
					class="h-2 rounded-full transition-all duration-500 {$workforceSummary.averageUtilization > 80 ? 'bg-warning-500' : 'bg-primary-500'}"
					style="width: {$workforceSummary.averageUtilization}%"
				></div>
			</div>
		</div>
	</div>

	<!-- Available Capacity -->
	<div class="stat-card bg-white rounded-xl shadow-sm border border-surface-200 p-4">
		<div class="flex items-center justify-between">
			<div>
				<p class="text-sm text-surface-600">Available Capacity</p>
				<p class="text-2xl font-bold text-info-600">
					{#if loading}
						<span class="animate-pulse">--</span>
					{:else}
						{$workforceSummary.availableCapacity}%
					{/if}
				</p>
			</div>
			<div class="w-12 h-12 bg-info-100 rounded-lg flex items-center justify-center">
				<svg class="w-6 h-6 text-info-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
				</svg>
			</div>
		</div>
		<div class="mt-2 text-sm text-surface-500">
			{$workforceSummary.totalCapacity}% total capacity
		</div>
	</div>
</div>

<style>
	.stat-card {
		transition: transform 0.2s ease, box-shadow 0.2s ease;
	}
	.stat-card:hover {
		transform: translateY(-2px);
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
	}
</style>
