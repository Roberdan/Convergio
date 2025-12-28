<script lang="ts">
	import { Button, Badge } from './index';

	interface BreadcrumbItem {
		label: string;
		href?: string;
		active?: boolean;
	}

	interface $$Props {
		title: string;
		subtitle?: string;
		breadcrumbs?: BreadcrumbItem[];
		showBackButton?: boolean;
		backHref?: string;
		badge?: {
			text: string;
			variant?: 'primary' | 'success' | 'warning' | 'error' | 'info' | 'gray';
		};
	}

	export let title: $$Props['title'];
	export let subtitle: $$Props['subtitle'] = '';
	export let breadcrumbs: BreadcrumbItem[] = [];
	export let showBackButton: $$Props['showBackButton'] = false;
	export let backHref: $$Props['backHref'] = '';
	export let badge: $$Props['badge'] = undefined;

	import { createEventDispatcher } from 'svelte';

	const dispatch = createEventDispatcher<{
		'back-click': void;
		'breadcrumb-click': { item: BreadcrumbItem };
	}>();

	function handleBackClick() {
		dispatch('back-click');
	}

	function handleBreadcrumbClick(item: BreadcrumbItem) {
		if (!item.active) {
			dispatch('breadcrumb-click', { item });
		}
	}
</script>

<div class="page-header">
	<!-- Breadcrumbs -->
	{#if breadcrumbs.length > 0}
		<nav class="breadcrumbs" aria-label="Breadcrumb">
			<ol class="breadcrumb-list" role="list">
				{#each breadcrumbs as item, index (item.label)}
					<li class="breadcrumb-item" role="listitem">
						{#if item.active || !item.href}
							<span class="breadcrumb-current" aria-current="page">
								{item.label}
							</span>
						{:else}
							<a
								href={item.href}
								class="breadcrumb-link"
								on:click={() => handleBreadcrumbClick(item)}
							>
								{item.label}
							</a>
						{/if}
						
						{#if index < breadcrumbs.length - 1}
							<span class="breadcrumb-separator" aria-hidden="true">
								<span class="icon-chevron-right"></span>
							</span>
						{/if}
					</li>
				{/each}
			</ol>
		</nav>
	{/if}

	<!-- Header Content -->
	<div class="header-content">
		<div class="header-main">
			<!-- Back Button -->
			{#if showBackButton}
				{#if backHref}
					<a href={backHref} class="back-button" on:click={handleBackClick}>
						<span class="icon-arrow-left" aria-hidden="true"></span>
						<span class="sr-only">Go back</span>
					</a>
				{:else}
					<button type="button" class="back-button" on:click={handleBackClick}>
						<span class="icon-arrow-left" aria-hidden="true"></span>
						<span class="sr-only">Go back</span>
					</button>
				{/if}
			{/if}

			<!-- Title and Badge -->
			<div class="title-section">
				<div class="title-row">
					<h1 class="page-title">{title}</h1>
					{#if badge}
						<Badge variant={badge.variant} size="sm" class="title-badge">
							{badge.text}
						</Badge>
					{/if}
				</div>
				
				{#if subtitle}
					<p class="page-subtitle">{subtitle}</p>
				{/if}
			</div>
		</div>

		<!-- Actions -->
		{#if $$slots.actions}
			<div class="header-actions">
				<slot name="actions" />
			</div>
		{/if}
	</div>

	<!-- Additional content (tabs, filters, etc.) -->
	{#if $$slots.additional}
		<div class="header-additional">
			<slot name="additional" />
		</div>
	{/if}
</div>

<style>
	.page-header {
		@apply pb-6 border-b border-gray-200;
	}

	:global(.dark) .page-header {
		@apply border-gray-700;
	}

	.breadcrumbs {
		@apply mb-4;
	}

	.breadcrumb-list {
		@apply flex items-center flex-wrap gap-1;
	}

	.breadcrumb-item {
		@apply flex items-center;
	}

	.breadcrumb-link {
		@apply text-sm text-gray-500 hover:text-gray-700 transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 rounded;
		font-family: var(--font-primary);
	}

	:global(.dark) .breadcrumb-link {
		@apply text-gray-400 hover:text-gray-300;
	}

	:global(.dark) .breadcrumb-link:focus {
		@apply ring-offset-gray-900;
	}

	:global(.dark) .breadcrumb-separator {
		@apply text-gray-600;
	}

	.breadcrumb-current {
		@apply text-sm font-medium text-gray-900;
		font-family: var(--font-primary);
	}

	:global(.dark) .breadcrumb-current {
		@apply text-gray-100;
	}

	.breadcrumb-separator {
		@apply mx-2 text-gray-400;
	}

	.header-content {
		@apply flex items-start justify-between gap-4;
	}

	.header-main {
		@apply flex items-start gap-4 flex-1 min-w-0;
	}

	.back-button {
		@apply flex items-center justify-center w-10 h-10 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 mt-1;
	}

	:global(.dark) .back-button {
		@apply text-gray-400 hover:text-gray-300 hover:bg-gray-800;
	}

	:global(.dark) .back-button:focus {
		@apply ring-offset-gray-900;
	}

	.title-section {
		@apply flex-1 min-w-0;
	}

	.title-row {
		@apply flex items-center gap-3 flex-wrap;
	}

	.page-title {
		@apply text-2xl font-bold text-gray-900 truncate;
		font-family: var(--font-primary);
	}

	:global(.dark) .page-title {
		@apply text-gray-100;
	}

	:global(.title-badge) {
		@apply flex-shrink-0;
	}

	.page-subtitle {
		@apply mt-2 text-base text-gray-600;
		font-family: var(--font-primary);
	}

	:global(.dark) .page-subtitle {
		@apply text-gray-400;
	}

	.header-actions {
		@apply flex items-center gap-3 flex-shrink-0;
	}

	.header-additional {
		@apply mt-6 pt-6 border-t border-gray-200;
	}

	:global(.dark) .header-additional {
		@apply border-gray-700;
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

	.icon-chevron-right {
		@apply w-3 h-3;
		mask-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='1.5' stroke='currentColor'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='m8.25 4.5 7.5 7.5-7.5 7.5' /%3e%3c/svg%3e");
	}

	.icon-arrow-left {
		mask-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='1.5' stroke='currentColor'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='M10.5 19.5 3 12m0 0 7.5-7.5M3 12h18' /%3e%3c/svg%3e");
	}

	/* Responsive adjustments */
	@media (max-width: 640px) {
		.header-content {
			@apply flex-col items-stretch gap-4;
		}

		.header-main {
			@apply flex-col gap-3;
		}

		.title-row {
			@apply items-start;
		}

		.page-title {
			@apply text-xl;
		}

		.header-actions {
			@apply justify-end;
		}
	}
</style>