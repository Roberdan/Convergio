<script lang="ts">
	import { Badge } from './index';

	interface TrendData {
		value: number;
		percentage: number;
		direction: 'up' | 'down' | 'neutral';
		period?: string;
	}

	interface $$Props {
		title: string;
		value: string | number;
		subtitle?: string;
		icon?: string;
		iconColor?: 'primary' | 'success' | 'warning' | 'error' | 'info' | 'gray';
		trend?: TrendData;
		loading?: boolean;
		variant?: 'default' | 'compact' | 'detailed';
		href?: string;
		clickable?: boolean;
	}

	export let title: $$Props['title'];
	export let value: $$Props['value'];
	export let subtitle: $$Props['subtitle'] = '';
	export let icon: $$Props['icon'] = '';
	export let iconColor: NonNullable<$$Props['iconColor']> = 'primary';
	export let trend: $$Props['trend'] = undefined;
	export let loading: $$Props['loading'] = false;
	export let variant: NonNullable<$$Props['variant']> = 'default';
	export let href: $$Props['href'] = '';
	export let clickable: $$Props['clickable'] = false;

	import { createEventDispatcher } from 'svelte';

	const dispatch = createEventDispatcher<{
		click: MouseEvent;
	}>();

	// Compute icon color classes
	$: iconColorClasses = {
		primary: 'text-primary-600 bg-primary-100',
		success: 'text-success-600 bg-success-100',
		warning: 'text-warning-600 bg-warning-100',
		error: 'text-error-600 bg-error-100',
		info: 'text-info-600 bg-info-100',
		gray: 'text-gray-600 bg-gray-100'
	};

	// Compute trend color classes
	$: trendColorClasses = trend ? {
		up: 'text-success-600',
		down: 'text-error-600',
		neutral: 'text-gray-500'
	}[trend.direction] : '';

	// Compute card classes
	$: cardClasses = [
		'stats-card',
		variant === 'compact' ? 'stats-card-compact' : '',
		variant === 'detailed' ? 'stats-card-detailed' : '',
		clickable || href ? 'cursor-pointer hover:shadow-lg hover:-translate-y-1' : '',
		'transition-all duration-200'
	].filter(Boolean).join(' ');

	function handleClick(event: MouseEvent | KeyboardEvent) {
		if (href) {
			window.location.href = href;
		}
		dispatch('click', event as MouseEvent);
	}

	function formatValue(val: string | number): string {
		if (typeof val === 'number') {
			// Format large numbers with K, M, B suffixes
			if (val >= 1000000000) {
				return (val / 1000000000).toFixed(1) + 'B';
			} else if (val >= 1000000) {
				return (val / 1000000).toFixed(1) + 'M';
			} else if (val >= 1000) {
				return (val / 1000).toFixed(1) + 'K';
			}
			return val.toLocaleString();
		}
		return String(val);
	}
</script>

<div
	class={cardClasses}
	on:click={handleClick}
	on:keydown={(e) => (e.key === 'Enter' || e.key === ' ') && handleClick(e)}
	{...(clickable || href ? { role: 'button', tabindex: 0 } : {})}
>
	{#if loading}
		<!-- Loading State -->
		<div class="stats-loading">
			<div class="flex items-center gap-4">
				<div class="skeleton-avatar w-12 h-12 rounded-xl"></div>
				<div class="flex-1 space-y-2">
					<div class="skeleton-text h-4 w-20"></div>
					<div class="skeleton-title h-8 w-24"></div>
					{#if variant === 'detailed'}
						<div class="skeleton-text h-3 w-16"></div>
					{/if}
				</div>
			</div>
		</div>
	{:else}
		<!-- Header with Icon and Title -->
		<div class="stats-header">
			{#if icon}
				<div class="stats-icon {iconColorClasses[iconColor]}">
					<span class="icon-{icon}" aria-hidden="true"></span>
				</div>
			{/if}
			
			<div class="stats-meta">
				<h3 class="stats-title">{title}</h3>
				{#if subtitle && variant !== 'compact'}
					<p class="stats-subtitle">{subtitle}</p>
				{/if}
			</div>

			{#if $$slots.actions}
				<div class="stats-actions">
					<slot name="actions" />
				</div>
			{/if}
		</div>

		<!-- Main Value -->
		<div class="stats-content">
			<div class="stats-value">{formatValue(value)}</div>
			
			{#if trend}
				<div class="stats-trend {trendColorClasses}">
					<span class="trend-icon icon-{trend.direction === 'up' ? 'arrow-up' : trend.direction === 'down' ? 'arrow-down' : 'minus'}" aria-hidden="true"></span>
					<span class="trend-percentage">{Math.abs(trend.percentage)}%</span>
					{#if trend.period}
						<span class="trend-period">vs {trend.period}</span>
					{/if}
				</div>
			{/if}
		</div>

		<!-- Footer (detailed variant only) -->
		{#if variant === 'detailed' && ($$slots.footer || subtitle)}
			<div class="stats-footer">
				{#if $$slots.footer}
					<slot name="footer" />
				{:else if subtitle}
					<p class="footer-subtitle">{subtitle}</p>
				{/if}
			</div>
		{/if}
	{/if}
</div>

<style>
	.stats-card {
		@apply bg-white border border-gray-200 rounded-xl p-6;
		box-shadow: var(--shadow-sm);
	}

	:global(.dark) .stats-card {
		@apply bg-gray-800 border-gray-700;
	}

	.stats-card:hover {
		box-shadow: var(--shadow-md);
	}

	.stats-card-compact {
		@apply p-4;
	}

	.stats-card-detailed {
		@apply p-8;
	}

	.stats-loading {
		@apply animate-pulse;
	}

	.stats-header {
		@apply flex items-start gap-4 mb-4;
	}

	.stats-card-compact .stats-header {
		@apply mb-3;
	}

	.stats-icon {
		@apply w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0;
	}

	.stats-card-compact .stats-icon {
		@apply w-10 h-10;
	}

	.stats-meta {
		@apply flex-1 min-w-0;
	}

	.stats-title {
		@apply text-sm font-medium text-gray-600 uppercase tracking-wide;
		font-family: var(--font-primary);
	}

	:global(.dark) .stats-title {
		@apply text-gray-400;
	}

	.stats-subtitle {
		@apply mt-1 text-xs text-gray-500;
		font-family: var(--font-primary);
	}

	.stats-actions {
		@apply flex-shrink-0;
	}

	.stats-content {
		@apply space-y-2;
	}

	.stats-value {
		@apply text-3xl font-bold text-gray-900 leading-none;
		font-family: var(--font-primary);
	}

	:global(.dark) .stats-value {
		@apply text-gray-100;
	}

	.stats-card-compact .stats-value {
		@apply text-2xl;
	}

	.stats-card-detailed .stats-value {
		@apply text-4xl;
	}

	.stats-trend {
		@apply flex items-center gap-1.5 text-sm font-medium;
		font-family: var(--font-primary);
	}

	.trend-icon {
		@apply w-4 h-4;
	}

	.trend-period {
		@apply text-gray-500 font-normal;
	}

	.stats-footer {
		@apply mt-6 pt-4 border-t border-gray-200;
	}

	:global(.dark) .stats-footer {
		@apply border-gray-700;
	}

	.footer-subtitle {
		@apply text-sm text-gray-600;
		font-family: var(--font-primary);
	}

	:global(.dark) .footer-subtitle {
		@apply text-gray-400;
	}

	/* Icon styles */
	[class^="icon-"] {
		display: inline-block;
		width: 1.5rem;
		height: 1.5rem;
		background-color: currentColor;
		mask-size: contain;
		mask-repeat: no-repeat;
		mask-position: center;
	}

	.stats-card-compact [class^="icon-"] {
		@apply w-5 h-5;
	}

	.trend-icon {
		@apply w-4 h-4;
	}

	/* Common icons */
	.icon-users {
		mask-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='1.5' stroke='currentColor'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='M15 19.128a9.38 9.38 0 0 0 2.625.372 9.337 9.337 0 0 0 4.121-.952 4.125 4.125 0 0 0-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 0 1 8.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0 1 11.964-3.07M12 6.375a3.375 3.375 0 1 1-6.75 0 3.375 3.375 0 0 1 6.75 0Zm8.25 2.25a2.625 2.625 0 1 1-5.25 0 2.625 2.625 0 0 1 5.25 0Z' /%3e%3c/svg%3e");
	}

	.icon-chart {
		mask-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='1.5' stroke='currentColor'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z' /%3e%3c/svg%3e");
	}

	.icon-currency {
		mask-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='1.5' stroke='currentColor'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='M12 6v12m-3-2.818.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.333-.78-1.333-1.778 0-.1.083-.176.176-.176.892 0 1.815.446 2.4 1.185M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z' /%3e%3c/svg%3e");
	}

	.icon-clock {
		mask-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='1.5' stroke='currentColor'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z' /%3e%3c/svg%3e");
	}

	.icon-arrow-up {
		mask-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='1.5' stroke='currentColor'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='M4.5 10.5 12 3m0 0 7.5 7.5M12 3v18' /%3e%3c/svg%3e");
	}

	.icon-arrow-down {
		mask-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='1.5' stroke='currentColor'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='M19.5 13.5 12 21m0 0-7.5-7.5M12 21V3' /%3e%3c/svg%3e");
	}

	.icon-minus {
		mask-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='1.5' stroke='currentColor'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='M5 12h14' /%3e%3c/svg%3e");
	}
</style>