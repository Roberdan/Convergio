<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import type { UnifiedResource } from '$lib/types/resource';

	export let resource: UnifiedResource;
	export let open = false;

	const dispatch = createEventDispatcher<{ close: void }>();

	function close() {
		dispatch('close');
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

	function getLevelColor(level: string) {
		switch (level) {
			case 'expert': return 'bg-purple-100 text-purple-700';
			case 'advanced': return 'bg-blue-100 text-blue-700';
			case 'intermediate': return 'bg-green-100 text-green-700';
			case 'beginner': return 'bg-yellow-100 text-yellow-700';
			default: return 'bg-surface-100 text-surface-700';
		}
	}
</script>

{#if open}
	<div
		class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
		on:click={close}
		on:keypress={(e) => e.key === 'Escape' && close()}
		role="dialog"
		aria-modal="true"
	>
		<div
			class="bg-white rounded-2xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto"
			on:click|stopPropagation
		>
			<!-- Header -->
			<div class="p-6 border-b border-surface-200">
				<div class="flex items-center justify-between">
					<div class="flex items-center gap-4">
						<div class="w-16 h-16 rounded-full flex items-center justify-center {resource.type === 'agent' ? 'bg-purple-100' : 'bg-primary-100'}">
							{#if resource.type === 'agent'}
								<span class="text-3xl">🤖</span>
							{:else}
								<span class="text-2xl font-bold text-primary-700">{resource.name.charAt(0)}</span>
							{/if}
						</div>
						<div>
							<h2 class="text-xl font-bold text-surface-900">{resource.name}</h2>
							<p class="text-surface-600">{resource.role}</p>
							<div class="flex items-center gap-2 mt-1">
								<span class="px-2 py-0.5 text-xs font-medium rounded-full {resource.type === 'talent' ? 'bg-blue-100 text-blue-700' : 'bg-purple-100 text-purple-700'}">
									{resource.type}
								</span>
								<span class="px-2 py-0.5 text-xs font-medium rounded-full {getStatusColor(resource.status)}">
									{resource.status}
								</span>
								{#if resource.tier}
									<span class="px-2 py-0.5 text-xs font-medium rounded-full bg-surface-100 text-surface-700">
										{resource.tier}
									</span>
								{/if}
							</div>
						</div>
					</div>
					<button
						on:click={close}
						class="p-2 text-surface-400 hover:text-surface-600 hover:bg-surface-100 rounded-lg transition-colors"
					>
						<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
						</svg>
					</button>
				</div>
			</div>

			<!-- Content -->
			<div class="p-6 space-y-6">
				<!-- Description -->
				{#if resource.description}
					<div>
						<h3 class="text-sm font-medium text-surface-500 uppercase tracking-wider mb-2">About</h3>
						<p class="text-surface-700">{resource.description}</p>
					</div>
				{/if}

				<!-- Metrics Grid -->
				<div class="grid grid-cols-2 md:grid-cols-4 gap-4">
					<div class="bg-surface-50 rounded-lg p-4 text-center">
						<div class="text-2xl font-bold text-primary-600">{resource.availability}%</div>
						<div class="text-sm text-surface-600">Availability</div>
					</div>
					<div class="bg-surface-50 rounded-lg p-4 text-center">
						<div class="text-2xl font-bold text-surface-900">{resource.performance.tasksCompleted}</div>
						<div class="text-sm text-surface-600">Tasks Done</div>
					</div>
					<div class="bg-surface-50 rounded-lg p-4 text-center">
						<div class="text-2xl font-bold text-warning-600">{resource.performance.averageRating.toFixed(1)}</div>
						<div class="text-sm text-surface-600">Avg. Rating</div>
					</div>
					<div class="bg-surface-50 rounded-lg p-4 text-center">
						<div class="text-2xl font-bold text-success-600">{resource.performance.efficiency}%</div>
						<div class="text-sm text-surface-600">Efficiency</div>
					</div>
				</div>

				<!-- Skills -->
				{#if resource.skills.length > 0}
					<div>
						<h3 class="text-sm font-medium text-surface-500 uppercase tracking-wider mb-3">Skills & Capabilities</h3>
						<div class="flex flex-wrap gap-2">
							{#each resource.skills as skill}
								<span class="inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium {getLevelColor(skill.level)}">
									{skill.name}
									{#if skill.years}
										<span class="text-xs opacity-75">({skill.years}y)</span>
									{/if}
								</span>
							{/each}
						</div>
					</div>
				{/if}

				<!-- Cost Information -->
				{#if resource.hourlyRate || resource.dailyRate}
					<div>
						<h3 class="text-sm font-medium text-surface-500 uppercase tracking-wider mb-3">Cost Information</h3>
						<div class="grid grid-cols-2 md:grid-cols-3 gap-4">
							{#if resource.hourlyRate}
								<div class="bg-surface-50 rounded-lg p-3">
									<div class="text-sm text-surface-600">Hourly Rate</div>
									<div class="text-lg font-semibold text-surface-900">${resource.hourlyRate}</div>
								</div>
							{/if}
							{#if resource.dailyRate}
								<div class="bg-surface-50 rounded-lg p-3">
									<div class="text-sm text-surface-600">Daily Rate</div>
									<div class="text-lg font-semibold text-surface-900">${resource.dailyRate}</div>
								</div>
							{/if}
							{#if resource.costData?.estimatedMonthlyCost}
								<div class="bg-surface-50 rounded-lg p-3">
									<div class="text-sm text-surface-600">Est. Monthly</div>
									<div class="text-lg font-semibold text-surface-900">${resource.costData.estimatedMonthlyCost.toLocaleString()}</div>
								</div>
							{/if}
						</div>
					</div>
				{/if}

				<!-- Contact Information (for talents) -->
				{#if resource.type === 'talent' && (resource.metadata.email || resource.metadata.phone || resource.metadata.location)}
					<div>
						<h3 class="text-sm font-medium text-surface-500 uppercase tracking-wider mb-3">Contact</h3>
						<div class="space-y-2">
							{#if resource.metadata.email}
								<div class="flex items-center gap-2 text-surface-700">
									<svg class="w-4 h-4 text-surface-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
									</svg>
									{resource.metadata.email}
								</div>
							{/if}
							{#if resource.metadata.phone}
								<div class="flex items-center gap-2 text-surface-700">
									<svg class="w-4 h-4 text-surface-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
									</svg>
									{resource.metadata.phone}
								</div>
							{/if}
							{#if resource.metadata.location}
								<div class="flex items-center gap-2 text-surface-700">
									<svg class="w-4 h-4 text-surface-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
									</svg>
									{resource.metadata.location}
								</div>
							{/if}
							{#if resource.metadata.timezone}
								<div class="flex items-center gap-2 text-surface-700">
									<svg class="w-4 h-4 text-surface-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
									</svg>
									{resource.metadata.timezone}
								</div>
							{/if}
						</div>
					</div>
				{/if}

				<!-- Agent Metadata -->
				{#if resource.type === 'agent' && (resource.metadata.toolsCount || resource.metadata.expertiseCount)}
					<div>
						<h3 class="text-sm font-medium text-surface-500 uppercase tracking-wider mb-3">Agent Details</h3>
						<div class="grid grid-cols-2 gap-4">
							{#if resource.metadata.toolsCount}
								<div class="bg-surface-50 rounded-lg p-3">
									<div class="text-sm text-surface-600">Tools Available</div>
									<div class="text-lg font-semibold text-surface-900">{resource.metadata.toolsCount}</div>
								</div>
							{/if}
							{#if resource.metadata.expertiseCount}
								<div class="bg-surface-50 rounded-lg p-3">
									<div class="text-sm text-surface-600">Expertise Areas</div>
									<div class="text-lg font-semibold text-surface-900">{resource.metadata.expertiseCount}</div>
								</div>
							{/if}
						</div>
					</div>
				{/if}
			</div>

			<!-- Footer -->
			<div class="p-6 border-t border-surface-200 bg-surface-50">
				<div class="flex items-center justify-between">
					<div class="text-sm text-surface-500">
						{#if resource.metadata.createdAt}
							Added: {new Date(resource.metadata.createdAt).toLocaleDateString()}
						{/if}
					</div>
					<div class="flex gap-2">
						<button on:click={close} class="px-4 py-2 text-surface-700 bg-white border border-surface-300 rounded-lg hover:bg-surface-50 transition-colors">
							Close
						</button>
						<button class="px-4 py-2 text-white bg-primary-600 rounded-lg hover:bg-primary-700 transition-colors">
							Assign to Project
						</button>
					</div>
				</div>
			</div>
		</div>
	</div>
{/if}
