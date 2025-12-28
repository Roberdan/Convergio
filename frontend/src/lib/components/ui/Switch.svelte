<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import type { HTMLInputAttributes } from 'svelte/elements';

	interface $$Props extends Omit<HTMLInputAttributes, 'type' | 'size'> {
		checked?: boolean;
		size?: 'sm' | 'md' | 'lg';
		label?: string;
		description?: string;
		disabled?: boolean;
	}

	export let checked: $$Props['checked'] = false;
	export let size: NonNullable<$$Props['size']> = 'md';
	export let label: $$Props['label'] = '';
	export let description: $$Props['description'] = '';
	export let disabled: $$Props['disabled'] = false;
	export let id: $$Props['id'] = '';

	const dispatch = createEventDispatcher<{
		change: { checked: boolean };
	}>();

	// Generate unique ID if not provided
	const switchId = id || `switch-${Math.random().toString(36).substr(2, 9)}`;

	// Compute CSS classes
	$: sizeClasses = {
		sm: 'switch-sm',
		md: 'switch-md',
		lg: 'switch-lg'
	};

	$: switchClasses = [
		'switch',
		sizeClasses[size],
		checked ? 'switch-checked' : '',
		disabled ? 'switch-disabled' : ''
	].filter(Boolean).join(' ');

	function handleChange(event: Event) {
		const target = event.target as HTMLInputElement;
		checked = target.checked;
		dispatch('change', { checked });
	}
</script>

<div class="switch-wrapper">
	<div class="switch-container">
		<button
			type="button"
			role="switch"
			aria-checked={checked}
			aria-labelledby={label ? `${switchId}-label` : undefined}
			aria-describedby={description ? `${switchId}-description` : undefined}
			class={switchClasses}
			{disabled}
			on:click={() => !disabled && (checked = !checked)}
			on:click={handleChange}
		>
			<span class="switch-track" aria-hidden="true">
				<span class="switch-thumb"></span>
			</span>
		</button>

		<!-- Hidden input for form submission -->
		<input
			{...$$restProps}
			id={switchId}
			type="checkbox"
			bind:checked
			{disabled}
			class="sr-only"
			on:change={handleChange}
		/>

		{#if label || description}
			<div class="switch-content">
				{#if label}
					<label for={switchId} id="{switchId}-label" class="switch-label">
						{label}
					</label>
				{/if}
				{#if description}
					<p id="{switchId}-description" class="switch-description">
						{description}
					</p>
				{/if}
			</div>
		{/if}
	</div>
</div>

<style>
	.switch-wrapper {
		@apply w-full;
	}

	.switch-container {
		@apply flex items-start gap-3;
	}

	.switch {
		@apply relative inline-flex items-center cursor-pointer transition-all duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 rounded-full;
	}

	.switch:focus {
		@apply ring-2 ring-primary-500 ring-offset-2;
	}

	:global(.dark) .switch:focus {
		@apply ring-offset-gray-800;
	}

	.switch-disabled {
		@apply opacity-50 cursor-not-allowed;
	}

	.switch-track {
		@apply relative inline-block bg-gray-200 border-2 border-transparent rounded-full transition-colors duration-200 ease-in-out;
	}

	:global(.dark) .switch-track {
		@apply bg-gray-700;
	}

	.switch-checked .switch-track {
		@apply bg-primary-600;
	}

	.switch-thumb {
		@apply pointer-events-none inline-block bg-white rounded-full shadow transform ring-0 transition-transform duration-200 ease-in-out;
	}

	.switch-checked .switch-thumb {
		@apply translate-x-full;
	}

	/* Size variants */
	.switch-sm .switch-track {
		@apply w-8 h-5;
	}

	.switch-sm .switch-thumb {
		@apply w-3 h-3 translate-x-0.5 translate-y-0.5;
	}

	.switch-sm.switch-checked .switch-thumb {
		@apply translate-x-3.5 translate-y-0.5;
	}

	.switch-md .switch-track {
		@apply w-11 h-6;
	}

	.switch-md .switch-thumb {
		@apply w-4 h-4 translate-x-0.5 translate-y-0.5;
	}

	.switch-md.switch-checked .switch-thumb {
		@apply translate-x-5 translate-y-0.5;
	}

	.switch-lg .switch-track {
		@apply w-14 h-8;
	}

	.switch-lg .switch-thumb {
		@apply w-6 h-6 translate-x-0.5 translate-y-0.5;
	}

	.switch-lg.switch-checked .switch-thumb {
		@apply translate-x-6 translate-y-0.5;
	}

	.switch-content {
		@apply flex-1;
	}

	.switch-label {
		@apply block text-sm font-medium text-gray-700 cursor-pointer;
		font-family: var(--font-primary);
	}

	:global(.dark) .switch-label {
		@apply text-gray-300;
	}

	.switch-description {
		@apply mt-1 text-xs text-gray-500;
		font-family: var(--font-primary);
	}

	:global(.dark) .switch-description {
		@apply text-gray-400;
	}
</style>