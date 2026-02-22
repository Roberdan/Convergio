<script lang="ts">
	import { run } from 'svelte/legacy';

	import { createEventDispatcher } from 'svelte';

	

	interface Props {
		content: string;
		placement?: 'top' | 'bottom' | 'left' | 'right' | 'top-start' | 'top-end' | 'bottom-start' | 'bottom-end';
		trigger?: 'hover' | 'click' | 'focus' | 'manual';
		delay?: number;
		hideDelay?: number;
		disabled?: boolean;
		arrow?: boolean;
		maxWidth?: string;
		variant?: 'default' | 'light' | 'error' | 'warning' | 'success';
		children?: import('svelte').Snippet;
	}

	let {
		content,
		placement = 'top',
		trigger = 'hover',
		delay = 100,
		hideDelay = 0,
		disabled = false,
		arrow = true,
		maxWidth = '200px',
		variant = 'light',
		children
	}: Props = $props();

	const dispatch = createEventDispatcher<{
		show: void;
		hide: void;
	}>();

	let isVisible = $state(false);
	let triggerRef: HTMLElement = $state()!;
	let tooltipRef: HTMLElement = $state()!;
	let showTimeout: NodeJS.Timeout;
	let hideTimeout: NodeJS.Timeout;

	// Placement classes
	let placementClasses = $derived({
		top: 'bottom-full left-1/2 transform -translate-x-1/2 mb-2',
		bottom: 'top-full left-1/2 transform -translate-x-1/2 mt-2',
		left: 'right-full top-1/2 transform -translate-y-1/2 mr-2',
		right: 'left-full top-1/2 transform -translate-y-1/2 ml-2',
		'top-start': 'bottom-full left-0 mb-2',
		'top-end': 'bottom-full right-0 mb-2',
		'bottom-start': 'top-full left-0 mt-2',
		'bottom-end': 'top-full right-0 mt-2'
	}[placement]);

	// Arrow classes
	let arrowClasses = $derived({
		top: 'top-full left-1/2 transform -translate-x-1/2 border-l-transparent border-r-transparent border-b-transparent',
		bottom: 'bottom-full left-1/2 transform -translate-x-1/2 border-l-transparent border-r-transparent border-t-transparent',
		left: 'left-full top-1/2 transform -translate-y-1/2 border-t-transparent border-b-transparent border-r-transparent',
		right: 'right-full top-1/2 transform -translate-y-1/2 border-t-transparent border-b-transparent border-l-transparent',
		'top-start': 'top-full left-3 border-l-transparent border-r-transparent border-b-transparent',
		'top-end': 'top-full right-3 border-l-transparent border-r-transparent border-b-transparent',
		'bottom-start': 'bottom-full left-3 border-l-transparent border-r-transparent border-t-transparent',
		'bottom-end': 'bottom-full right-3 border-l-transparent border-r-transparent border-t-transparent'
	}[placement]);

	// Variant classes
	let variantClasses = $derived({
		default: 'bg-white text-gray-900 border border-gray-200',
		light: 'bg-white text-gray-900 border border-gray-200',
		error: 'bg-error-600 text-white',
		warning: 'bg-warning-600 text-white',
		success: 'bg-success-600 text-white'
	}[variant]);

	// Arrow variant classes
	let arrowVariantClasses = $derived({
		default: 'border-white',
		light: 'border-white',
		error: 'border-error-600',
		warning: 'border-warning-600',
		success: 'border-success-600'
	}[variant]);

	function show() {
		if (disabled) return;
		
		clearTimeout(hideTimeout);
		showTimeout = setTimeout(() => {
			isVisible = true;
			dispatch('show');
		}, delay);
	}

	function hide() {
		clearTimeout(showTimeout);
		hideTimeout = setTimeout(() => {
			isVisible = false;
			dispatch('hide');
		}, hideDelay);
	}

	function handleMouseEnter() {
		if (trigger === 'hover') {
			show();
		}
	}

	function handleMouseLeave() {
		if (trigger === 'hover') {
			hide();
		}
	}

	function handleClick() {
		if (trigger === 'click') {
			if (isVisible) {
				hide();
			} else {
				show();
			}
		}
	}

	function handleFocus() {
		if (trigger === 'focus') {
			show();
		}
	}

	function handleBlur() {
		if (trigger === 'focus') {
			hide();
		}
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape' && isVisible) {
			hide();
		}
	}

	// Close tooltip when clicking outside
	function handleClickOutside(event: Event) {
		if (trigger === 'click' && isVisible && triggerRef && tooltipRef) {
			const target = event.target as Node;
			if (!triggerRef.contains(target) && !tooltipRef.contains(target)) {
				hide();
			}
		}
	}

	run(() => {
		if (typeof window !== 'undefined') {
			if (isVisible && trigger === 'click') {
				document.addEventListener('click', handleClickOutside);
			} else {
				document.removeEventListener('click', handleClickOutside);
			}
		}
	});
</script>

<svelte:window onkeydown={handleKeydown} />

<div class="tooltip-container relative inline-block">
	<!-- Trigger Element -->
	<div
		bind:this={triggerRef}
		class="tooltip-trigger"
		onmouseenter={handleMouseEnter}
		onmouseleave={handleMouseLeave}
		onclick={handleClick}
		onfocus={handleFocus}
		onblur={handleBlur}
		onkeydown={(e) => e.key === 'Enter' && handleClick()}
		{...(trigger === 'click' ? { role: 'button', tabindex: 0 } : {})}
	>
		{@render children?.()}
	</div>

	<!-- Tooltip -->
	{#if isVisible && content}
		<div
			bind:this={tooltipRef}
			class="tooltip absolute z-50 {placementClasses} {variantClasses}"
			style="max-width: {maxWidth}"
			role="tooltip"
			aria-hidden={!isVisible}
		>
			<div class="tooltip-content">
				{content}
			</div>

			<!-- Arrow -->
			{#if arrow}
				<div class="tooltip-arrow absolute w-2 h-2 {arrowClasses} {arrowVariantClasses}"></div>
			{/if}
		</div>
	{/if}
</div>

<style>
	.tooltip-container {
		display: inline-block;
	}

	.tooltip-trigger {
		display: inline-block;
	}

	.tooltip {
		@apply px-3 py-2 text-sm rounded-lg shadow-lg;
		font-family: var(--font-primary);
		animation: tooltipFadeIn 0.2s ease-out;
		box-shadow: var(--shadow-lg);
	}

	.tooltip-content {
		@apply break-words;
		line-height: 1.4;
	}

	.tooltip-arrow {
		border-width: 6px;
		border-style: solid;
	}

	/* Animation */
	@keyframes tooltipFadeIn {
		from {
			opacity: 0;
			transform: translateY(-5px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}

	/* Placement-specific arrow adjustments */
	.tooltip-arrow {
		z-index: -1;
	}

	/* Responsive adjustments */
	@media (max-width: 640px) {
		.tooltip {
			@apply max-w-xs text-xs px-2 py-1;
		}
	}

	/* Reduce motion for accessibility */
	@media (prefers-reduced-motion: reduce) {
		.tooltip {
			animation: none;
		}
	}

	/* Focus styles for click trigger */
	.tooltip-trigger[role="button"]:focus {
		@apply outline-none ring-2 ring-primary-500 ring-offset-2 rounded;
	}

</style>