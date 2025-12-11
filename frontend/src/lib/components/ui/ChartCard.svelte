<script lang="ts">
	import { onMount } from 'svelte';
	import { Button, Badge } from './index';

	interface $$Props {
		title: string;
		subtitle?: string;
		loading?: boolean;
		error?: string;
		showLegend?: boolean;
		showControls?: boolean;
		fullscreen?: boolean;
		exportable?: boolean;
		refreshable?: boolean;
		lastUpdated?: Date;
		variant?: 'default' | 'compact' | 'full';
	}

	export let title: $$Props['title'];
	export let subtitle: $$Props['subtitle'] = '';
	export let loading: $$Props['loading'] = false;
	export let error: $$Props['error'] = '';
	export let showLegend: $$Props['showLegend'] = true;
	export let showControls: $$Props['showControls'] = true;
	export let fullscreen: $$Props['fullscreen'] = false;
	export let exportable: $$Props['exportable'] = false;
	export let refreshable: $$Props['refreshable'] = false;
	export let lastUpdated: $$Props['lastUpdated'] = undefined;
	export let variant: NonNullable<$$Props['variant']> = 'default';

	import { createEventDispatcher } from 'svelte';

	const dispatch = createEventDispatcher<{
		refresh: void;
		export: { format: 'png' | 'svg' | 'pdf' };
		fullscreen: { enabled: boolean };
		filter: { filters: Record<string, any> };
	}>();

	let chartContainer: HTMLElement;
	let isRefreshing = false;

	// Chart height based on variant
	$: chartHeight = {
		compact: '200px',
		default: '300px',
		full: '500px'
	}[variant];

	// Format last updated time
	$: lastUpdatedText = lastUpdated 
		? `Updated ${formatRelativeTime(lastUpdated)}`
		: '';

	function handleRefresh() {
		if (isRefreshing) return;
		isRefreshing = true;
		dispatch('refresh');
		
		// Reset refreshing state after a delay
		setTimeout(() => {
			isRefreshing = false;
		}, 2000);
	}

	function handleExport(format: 'png' | 'svg' | 'pdf') {
		dispatch('export', { format });
	}

	function toggleFullscreen() {
		fullscreen = !fullscreen;
		dispatch('fullscreen', { enabled: fullscreen });
	}

	function formatRelativeTime(date: Date): string {
		const now = new Date();
		const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);
		
		if (diffInSeconds < 60) return 'just now';
		if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
		if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
		return `${Math.floor(diffInSeconds / 86400)}d ago`;
	}

	onMount(() => {
		// Chart initialization would happen here
		// This is where you'd integrate with Chart.js or D3.js
	});
</script>

<div class="chart-card" class:fullscreen>
	<!-- Header -->
	<div class="chart-header">
		<div class="header-content">
			<div class="header-main">
				<h3 class="chart-title">{title}</h3>
				{#if subtitle}
					<p class="chart-subtitle">{subtitle}</p>
				{/if}
				{#if lastUpdatedText}
					<p class="last-updated">{lastUpdatedText}</p>
				{/if}
			</div>

			{#if $$slots.badge}
				<div class="header-badge">
					<slot name="badge" />
				</div>
			{/if}
		</div>

		{#if showControls}
			<div class="chart-controls">
				<!-- Filters slot -->
				{#if $$slots.filters}
					<div class="chart-filters">
						<slot name="filters" />
					</div>
				{/if}

				<!-- Action buttons -->
				<div class="action-buttons">
					{#if refreshable}
						<Button
							variant="ghost"
							size="sm"
							loading={isRefreshing}
							on:click={handleRefresh}
							aria-label="Refresh chart"
						>
							<span class="icon-refresh" aria-hidden="true"></span>
						</Button>
					{/if}

					{#if exportable}
						<div class="export-dropdown">
							<Button
								variant="ghost"
								size="sm"
								aria-label="Export chart"
							>
								<span class="icon-download" aria-hidden="true"></span>
							</Button>
							<!-- Export menu would be implemented here -->
						</div>
					{/if}

					<Button
						variant="ghost"
						size="sm"
						on:click={toggleFullscreen}
						aria-label={fullscreen ? 'Exit fullscreen' : 'Enter fullscreen'}
					>
						<span class="icon-{fullscreen ? 'minimize' : 'expand'}" aria-hidden="true"></span>
					</Button>
				</div>
			</div>
		{/if}
	</div>

	<!-- Chart Content -->
	<div class="chart-content" style="height: {chartHeight}">
		{#if loading}
			<!-- Loading State -->
			<div class="chart-loading">
				<div class="loading-spinner"></div>
				<p class="loading-text">Loading chart data...</p>
			</div>
		{:else if error}
			<!-- Error State -->
			<div class="chart-error">
				<span class="icon-error error-icon" aria-hidden="true"></span>
				<h4 class="error-title">Unable to load chart</h4>
				<p class="error-message">{error}</p>
				{#if refreshable}
					<Button variant="outline" size="sm" on:click={handleRefresh}>
						Try again
					</Button>
				{/if}
			</div>
		{:else}
			<!-- Chart Container -->
			<div bind:this={chartContainer} class="chart-container">
				<slot />
			</div>
		{/if}
	</div>

	<!-- Legend -->
	{#if showLegend && $$slots.legend && !loading && !error}
		<div class="chart-legend">
			<slot name="legend" />
		</div>
	{/if}

	<!-- Footer -->
	{#if $$slots.footer}
		<div class="chart-footer">
			<slot name="footer" />
		</div>
	{/if}
</div>

<!-- Fullscreen backdrop -->
{#if fullscreen}
	<div class="fullscreen-backdrop" on:click={toggleFullscreen}></div>
{/if}

<style>
	.chart-card {
		@apply bg-white border border-gray-200 rounded-xl overflow-hidden;
		box-shadow: var(--shadow-sm);
		transition: all 0.3s ease;
	}

	.chart-card:hover {
		box-shadow: var(--shadow-md);
	}

	.chart-card.fullscreen {
		@apply fixed inset-4 z-50 max-w-none max-h-none;
		box-shadow: var(--shadow-xl);
	}

	.chart-header {
		padding: 1rem 1.5rem;
		border-bottom: 1px solid var(--color-border-light);
		background-color: var(--color-surface-50);
	}

	.header-content {
		@apply flex items-start justify-between gap-4 mb-4;
	}

	.header-main {
		@apply flex-1 min-w-0;
	}

	.chart-title {
		@apply text-lg font-semibold text-gray-900;
		font-family: var(--font-primary);
	}

	.chart-subtitle {
		@apply mt-1 text-sm text-gray-600;
		font-family: var(--font-primary);
	}

	.last-updated {
		@apply mt-2 text-xs text-gray-500;
		font-family: var(--font-primary);
	}

	.header-badge {
		@apply flex-shrink-0;
	}

	.chart-controls {
		@apply flex items-center justify-between gap-4;
	}

	.chart-filters {
		@apply flex items-center gap-2;
	}

	.action-buttons {
		@apply flex items-center gap-1;
	}

	.export-dropdown {
		@apply relative;
	}

	.chart-content {
		@apply relative overflow-hidden;
	}

	.chart-loading {
		@apply h-full flex flex-col items-center justify-center gap-4 text-gray-500;
	}

	.loading-text {
		@apply text-sm;
		font-family: var(--font-primary);
	}

	.chart-error {
		@apply h-full flex flex-col items-center justify-center gap-4 p-8 text-center;
	}

	.error-icon {
		@apply w-12 h-12 text-error-500;
	}

	.error-title {
		@apply text-lg font-medium text-gray-900;
		font-family: var(--font-primary);
	}

	.error-message {
		@apply text-sm text-gray-600 max-w-sm;
		font-family: var(--font-primary);
	}

	.chart-container {
		@apply w-full h-full p-4;
	}

	.chart-legend {
		padding: 1rem 1.5rem;
		border-top: 1px solid var(--color-border-light);
		background-color: var(--color-surface-50);
	}

	.chart-footer {
		padding: 1rem 1.5rem;
		border-top: 1px solid var(--color-border-light);
		background-color: var(--color-surface-50);
	}

	.fullscreen-backdrop {
		@apply fixed inset-0 bg-black bg-opacity-50 z-40;
	}

	/* Icon styles */
	[class^="icon-"] {
		display: inline-block;
		width: 1rem;
		height: 1rem;
		background-color: currentColor;
		mask-size: contain;
		mask-repeat: no-repeat;
		mask-position: center;
	}

	.error-icon {
		@apply w-12 h-12;
	}

	.icon-refresh {
		mask-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='1.5' stroke='currentColor'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99' /%3e%3c/svg%3e");
	}

	.icon-download {
		mask-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='1.5' stroke='currentColor'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M16.5 12 12 16.5m0 0L7.5 12m4.5 4.5V3' /%3e%3c/svg%3e");
	}

	.icon-expand {
		mask-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='1.5' stroke='currentColor'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='M3.75 3.75v4.5m0-4.5h4.5m-4.5 0L9 9M3.75 20.25v-4.5m0 4.5h4.5m-4.5 0L9 15M20.25 3.75h-4.5m4.5 0v4.5m0-4.5L15 9m5.25 11.25h-4.5m4.5 0v-4.5m0 4.5L15 15' /%3e%3c/svg%3e");
	}

	.icon-minimize {
		mask-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='1.5' stroke='currentColor'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='M9 9V4.5M9 9H4.5M9 9 3.75 3.75M9 15v4.5M9 15H4.5M9 15l-5.25 5.25M15 9h4.5M15 9V4.5M15 9l5.25-5.25M15 15h4.5M15 15v4.5m0-4.5 5.25 5.25' /%3e%3c/svg%3e");
	}

	.icon-error {
		mask-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='1.5' stroke='currentColor'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z' /%3e%3c/svg%3e");
	}

	/* Responsive adjustments */
	@media (max-width: 640px) {
		.chart-controls {
			@apply flex-col items-stretch gap-3;
		}

		.chart-filters {
			@apply justify-center;
		}

		.action-buttons {
			@apply justify-center;
		}

		.chart-card.fullscreen {
			@apply inset-2;
		}
	}
</style>