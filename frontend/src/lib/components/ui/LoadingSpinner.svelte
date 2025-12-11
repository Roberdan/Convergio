<script lang="ts">
	interface $$Props {
		size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
		variant?: 'default' | 'primary' | 'white' | 'dots' | 'pulse' | 'bars';
		text?: string;
		center?: boolean;
		overlay?: boolean;
		fullscreen?: boolean;
	}

	export let size: NonNullable<$$Props['size']> = 'md';
	export let variant: NonNullable<$$Props['variant']> = 'default';
	export let text: $$Props['text'] = '';
	export let center: $$Props['center'] = false;
	export let overlay: $$Props['overlay'] = false;
	export let fullscreen: $$Props['fullscreen'] = false;

	// Size classes
	$: sizeClasses = {
		xs: 'w-3 h-3',
		sm: 'w-4 h-4',
		md: 'w-6 h-6',
		lg: 'w-8 h-8',
		xl: 'w-12 h-12'
	}[size];

	// Variant classes
	$: variantClasses = {
		default: 'text-gray-500',
		primary: 'text-primary-600',
		white: 'text-white'
	}[variant === 'dots' || variant === 'pulse' || variant === 'bars' ? 'default' : variant];

	// Container classes
	$: containerClasses = [
		center ? 'flex items-center justify-center' : '',
		fullscreen ? 'fixed inset-0 z-50' : '',
		overlay ? 'absolute inset-0 bg-white bg-opacity-75' : '',
		text ? 'flex flex-col items-center gap-3' : ''
	].filter(Boolean).join(' ');
</script>

<div class="loading-container {containerClasses}">
	{#if variant === 'default' || variant === 'primary' || variant === 'white'}
		<!-- Spinning Circle -->
		<div class="spinner-circle {sizeClasses} {variantClasses}">
			<svg class="animate-spin" fill="none" viewBox="0 0 24 24">
				<circle
					class="opacity-25"
					cx="12"
					cy="12"
					r="10"
					stroke="currentColor"
					stroke-width="4"
				></circle>
				<path
					class="opacity-75"
					fill="currentColor"
					d="m4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
				></path>
			</svg>
		</div>
	{:else if variant === 'dots'}
		<!-- Bouncing Dots -->
		<div class="spinner-dots {variantClasses}">
			<div class="dot dot-1 {sizeClasses}"></div>
			<div class="dot dot-2 {sizeClasses}"></div>
			<div class="dot dot-3 {sizeClasses}"></div>
		</div>
	{:else if variant === 'pulse'}
		<!-- Pulsing Circle -->
		<div class="spinner-pulse {sizeClasses} {variantClasses}">
			<div class="pulse-ring pulse-ring-1"></div>
			<div class="pulse-ring pulse-ring-2"></div>
			<div class="pulse-center"></div>
		</div>
	{:else if variant === 'bars'}
		<!-- Loading Bars -->
		<div class="spinner-bars {variantClasses}">
			<div class="bar bar-1"></div>
			<div class="bar bar-2"></div>
			<div class="bar bar-3"></div>
			<div class="bar bar-4"></div>
		</div>
	{/if}

	{#if text}
		<p class="loading-text text-sm {variantClasses}">
			{text}
		</p>
	{/if}
</div>

<style>
	.loading-container {
		font-family: var(--font-primary);
	}

	/* Spinner Circle */
	.spinner-circle {
		display: inline-block;
	}

	/* Bouncing Dots */
	.spinner-dots {
		@apply flex items-center gap-1;
	}

	.dot {
		@apply bg-current rounded-full;
		animation: dotBounce 1.4s ease-in-out infinite both;
	}

	.dot-1 {
		animation-delay: -0.32s;
	}

	.dot-2 {
		animation-delay: -0.16s;
	}

	.dot-3 {
		animation-delay: 0s;
	}

	/* Pulsing Circle */
	.spinner-pulse {
		@apply relative;
	}

	.pulse-ring {
		@apply absolute inset-0 border-2 border-current rounded-full opacity-75;
		animation: pulseScale 2s cubic-bezier(0.455, 0.03, 0.515, 0.955) infinite;
	}

	.pulse-ring-1 {
		animation-delay: 0s;
	}

	.pulse-ring-2 {
		animation-delay: 1s;
	}

	.pulse-center {
		@apply absolute inset-2 bg-current rounded-full opacity-50;
	}

	/* Loading Bars */
	.spinner-bars {
		@apply flex items-end gap-1;
		height: 1.5rem;
	}

	.bar {
		@apply bg-current w-1;
		animation: barStretch 1.2s ease-in-out infinite;
	}

	.bar-1 {
		animation-delay: -1.1s;
	}

	.bar-2 {
		animation-delay: -1.0s;
	}

	.bar-3 {
		animation-delay: -0.9s;
	}

	.bar-4 {
		animation-delay: -0.8s;
	}

	.loading-text {
		@apply text-center;
	}

	/* Animations */
	@keyframes dotBounce {
		0%, 80%, 100% {
			transform: scale(0.8);
			opacity: 0.5;
		}
		40% {
			transform: scale(1);
			opacity: 1;
		}
	}

	@keyframes pulseScale {
		0% {
			transform: scale(0);
			opacity: 1;
		}
		100% {
			transform: scale(1);
			opacity: 0;
		}
	}

	@keyframes barStretch {
		0%, 40%, 100% {
			height: 0.25rem;
		}
		20% {
			height: 1.5rem;
		}
	}

	/* Size-specific adjustments */
	.w-3.h-3 + .loading-text {
		font-size: 0.75rem;
	}

	.w-12.h-12 + .loading-text {
		font-size: 1rem;
	}

	/* Dots size adjustments */
	.spinner-dots .w-3.h-3 {
		width: 0.25rem;
		height: 0.25rem;
	}

	.spinner-dots .w-4.h-4 {
		width: 0.375rem;
		height: 0.375rem;
	}

	.spinner-dots .w-6.h-6 {
		width: 0.5rem;
		height: 0.5rem;
	}

	.spinner-dots .w-8.h-8 {
		width: 0.625rem;
		height: 0.625rem;
	}

	.spinner-dots .w-12.h-12 {
		width: 0.75rem;
		height: 0.75rem;
	}

	/* Overlay styles */
	.loading-container.absolute.inset-0 {
		backdrop-filter: blur(2px);
	}

	.loading-container.fixed.inset-0 {
		backdrop-filter: blur(4px);
		background-color: rgba(255, 255, 255, 0.9);
	}

	.dark .loading-container.fixed.inset-0 {
		background-color: rgba(15, 23, 42, 0.9);
	}

	/* Reduce motion for accessibility */
	@media (prefers-reduced-motion: reduce) {
		.spinner-circle svg,
		.dot,
		.pulse-ring,
		.bar {
			animation: none;
		}

		.spinner-circle {
			opacity: 0.75;
		}
	}
</style>