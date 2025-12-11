<script lang="ts">
	import { createEventDispatcher } from 'svelte';

	interface BreadcrumbItem {
		label: string;
		href?: string;
		icon?: string;
		active?: boolean;
		disabled?: boolean;
	}

	interface $$Props {
		items: BreadcrumbItem[];
		separator?: 'slash' | 'chevron' | 'arrow' | 'dot';
		showHome?: boolean;
		homeHref?: string;
		maxItems?: number;
		size?: 'sm' | 'md' | 'lg';
	}

	export let items: $$Props['items'];
	export let separator: NonNullable<$$Props['separator']> = 'chevron';
	export let showHome: $$Props['showHome'] = true;
	export let homeHref: $$Props['homeHref'] = '/';
	export let maxItems: $$Props['maxItems'] = undefined;
	export let size: NonNullable<$$Props['size']> = 'md';

	const dispatch = createEventDispatcher<{
		click: { item: BreadcrumbItem; index: number };
		homeClick: void;
	}>();

	// Compute visible items with ellipsis if needed
	$: visibleItems = maxItems && items.length > maxItems 
		? [
			...items.slice(0, 1), 
			{ label: '...', disabled: true } as BreadcrumbItem,
			...items.slice(-(maxItems - 2))
		]
		: items;

	// Size classes
	$: sizeClasses = {
		sm: 'text-xs',
		md: 'text-sm', 
		lg: 'text-base'
	}[size];

	// Separator icons
	$: separatorIcon = {
		slash: '/',
		chevron: 'chevron-right',
		arrow: 'arrow-right',
		dot: 'dot'
	}[separator];

	function handleItemClick(item: BreadcrumbItem, index: number) {
		if (item.disabled || item.active) return;
		dispatch('click', { item, index });
	}

	function handleHomeClick() {
		dispatch('homeClick');
	}
</script>

<nav class="breadcrumbs {sizeClasses}" aria-label="Breadcrumb">
	<ol class="breadcrumb-list" role="list">
		<!-- Home link -->
		{#if showHome}
			<li class="breadcrumb-item" role="listitem">
				<a
					href={homeHref}
					class="breadcrumb-link home-link"
					on:click={handleHomeClick}
					aria-label="Home"
				>
					<span class="icon-home" aria-hidden="true"></span>
				</a>
				{#if items.length > 0}
					<span class="breadcrumb-separator" aria-hidden="true">
						{#if separator === 'slash'}
							/
						{:else if separator === 'dot'}
							<span class="separator-dot"></span>
						{:else}
							<span class="icon-{separatorIcon}"></span>
						{/if}
					</span>
				{/if}
			</li>
		{/if}

		<!-- Breadcrumb items -->
		{#each visibleItems as item, index (item.label + index)}
			<li class="breadcrumb-item" role="listitem">
				{#if item.label === '...'}
					<span class="breadcrumb-ellipsis" aria-hidden="true">...</span>
				{:else if item.active || !item.href}
					<span 
						class="breadcrumb-current" 
						aria-current={item.active ? 'page' : undefined}
					>
						{#if item.icon}
							<span class="icon-{item.icon}" aria-hidden="true"></span>
						{/if}
						{item.label}
					</span>
				{:else}
					<a
						href={item.href}
						class="breadcrumb-link"
						class:disabled={item.disabled}
						on:click={() => handleItemClick(item, index)}
						aria-disabled={item.disabled}
					>
						{#if item.icon}
							<span class="icon-{item.icon}" aria-hidden="true"></span>
						{/if}
						{item.label}
					</a>
				{/if}

				<!-- Separator -->
				{#if index < visibleItems.length - 1 && item.label !== '...'}
					<span class="breadcrumb-separator" aria-hidden="true">
						{#if separator === 'slash'}
							/
						{:else if separator === 'dot'}
							<span class="separator-dot"></span>
						{:else}
							<span class="icon-{separatorIcon}"></span>
						{/if}
					</span>
				{/if}
			</li>
		{/each}
	</ol>
</nav>

<style>
	.breadcrumbs {
		@apply w-full;
		font-family: var(--font-primary);
	}

	.breadcrumb-list {
		@apply flex items-center flex-wrap gap-1;
	}

	.breadcrumb-item {
		@apply flex items-center gap-1;
	}

	.breadcrumb-link {
		@apply text-gray-500 hover:text-gray-700 transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 rounded px-1 py-0.5 flex items-center gap-1.5;
		text-decoration: none;
	}

	.dark .breadcrumb-link:focus {
		@apply ring-offset-gray-900;
	}

	.breadcrumb-link.disabled {
		@apply opacity-50 cursor-not-allowed pointer-events-none;
	}

	.home-link {
		@apply p-1 rounded-md;
	}

	.breadcrumb-current {
		@apply text-gray-900 font-medium flex items-center gap-1.5 px-1 py-0.5;
	}

	.breadcrumb-ellipsis {
		@apply text-gray-400 px-1 py-0.5;
	}

	.breadcrumb-separator {
		@apply text-gray-400 mx-1 flex items-center;
	}

	.separator-dot {
		@apply w-1 h-1 bg-current rounded-full;
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

	.breadcrumb-separator [class^="icon-"] {
		@apply w-3 h-3;
	}

	/* Size variants */
	.text-xs [class^="icon-"] {
		@apply w-3 h-3;
	}

	.text-xs .breadcrumb-separator [class^="icon-"] {
		@apply w-2.5 h-2.5;
	}

	.text-lg [class^="icon-"] {
		@apply w-5 h-5;
	}

	.text-lg .breadcrumb-separator [class^="icon-"] {
		@apply w-4 h-4;
	}

	.icon-home {
		mask-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='1.5' stroke='currentColor'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='m2.25 12 8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25' /%3e%3c/svg%3e");
	}

	.icon-chevron-right {
		mask-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='1.5' stroke='currentColor'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='m8.25 4.5 7.5 7.5-7.5 7.5' /%3e%3c/svg%3e");
	}

	.icon-arrow-right {
		mask-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='1.5' stroke='currentColor'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3' /%3e%3c/svg%3e");
	}

	/* Responsive adjustments */
	@media (max-width: 640px) {
		.breadcrumb-list {
			@apply gap-0.5;
		}

		.breadcrumb-separator {
			@apply mx-0.5;
		}

		/* Hide intermediate items on very small screens */
		.breadcrumb-item:not(:first-child):not(:last-child):not(:nth-last-child(2)) {
			@apply hidden;
		}
	}
</style>