<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import type { HTMLInputAttributes } from 'svelte/elements';

	interface $$Props extends Omit<HTMLInputAttributes, 'type' | 'size'> {
		checked?: boolean;
		indeterminate?: boolean;
		size?: 'sm' | 'md' | 'lg';
		label?: string;
		description?: string;
		error?: string;
		disabled?: boolean;
	}

	export let checked: $$Props['checked'] = false;
	export let indeterminate: $$Props['indeterminate'] = false;
	export let size: NonNullable<$$Props['size']> = 'md';
	export let label: $$Props['label'] = '';
	export let description: $$Props['description'] = '';
	export let error: $$Props['error'] = '';
	export let disabled: $$Props['disabled'] = false;
	export let id: $$Props['id'] = '';

	const dispatch = createEventDispatcher<{
		change: { checked: boolean; indeterminate: boolean };
	}>();

	// Generate unique ID if not provided
	const checkboxId = id || `checkbox-${Math.random().toString(36).substr(2, 9)}`;

	// Compute CSS classes
	$: sizeClasses = {
		sm: 'checkbox-sm',
		md: 'checkbox-md',
		lg: 'checkbox-lg'
	};

	$: checkboxClasses = [
		'checkbox',
		sizeClasses[size],
		checked ? 'checkbox-checked' : '',
		indeterminate ? 'checkbox-indeterminate' : '',
		error ? 'checkbox-error' : '',
		disabled ? 'checkbox-disabled' : ''
	].filter(Boolean).join(' ');

	function handleChange(event: Event) {
		const target = event.target as HTMLInputElement;
		checked = target.checked;
		indeterminate = target.indeterminate;
		dispatch('change', { checked, indeterminate });
	}

	// Handle indeterminate state
	let checkboxElement: HTMLInputElement;
	$: if (checkboxElement && indeterminate !== undefined) {
		checkboxElement.indeterminate = indeterminate;
	}
</script>

<div class="checkbox-wrapper">
	<div class="checkbox-container">
		<div class="checkbox-input-wrapper">
			<input
				{...$$restProps}
				bind:this={checkboxElement}
				id={checkboxId}
				type="checkbox"
				bind:checked
				{disabled}
				class={checkboxClasses}
				on:change={handleChange}
			/>
			
			<!-- Custom checkbox visual -->
			<div class="checkbox-visual" aria-hidden="true">
				{#if checked && !indeterminate}
					<span class="checkbox-icon icon-check"></span>
				{:else if indeterminate}
					<span class="checkbox-icon icon-minus"></span>
				{/if}
			</div>
		</div>

		{#if label || description}
			<div class="checkbox-content">
				{#if label}
					<label for={checkboxId} class="checkbox-label">
						{label}
					</label>
				{/if}
				{#if description}
					<p class="checkbox-description">
						{description}
					</p>
				{/if}
			</div>
		{/if}
	</div>

	{#if error}
		<p class="checkbox-error-text" role="alert">
			{error}
		</p>
	{/if}
</div>

<style>
	.checkbox-wrapper {
		@apply w-full;
	}

	.checkbox-container {
		@apply flex items-start gap-3;
	}

	.checkbox-input-wrapper {
		@apply relative;
	}

	.checkbox {
		@apply sr-only;
	}

	.checkbox-visual {
		@apply flex items-center justify-center border-2 border-gray-300 rounded transition-all duration-200 bg-white cursor-pointer;
	}

	:global(.dark) .checkbox-visual {
		@apply border-gray-600 bg-gray-800;
	}

	.checkbox:focus + .checkbox-visual {
		@apply ring-2 ring-primary-500 ring-offset-2;
	}

	:global(.dark) .checkbox:focus + .checkbox-visual {
		@apply ring-offset-gray-800;
	}

	.checkbox-checked + .checkbox-visual,
	.checkbox-indeterminate + .checkbox-visual {
		@apply bg-primary-600 border-primary-600;
	}

	.checkbox-error + .checkbox-visual {
		@apply border-error-500;
	}

	.checkbox-error.checkbox-checked + .checkbox-visual {
		@apply bg-error-500 border-error-500;
	}

	.checkbox-disabled + .checkbox-visual {
		@apply opacity-50 cursor-not-allowed bg-gray-100 border-gray-200;
	}

	:global(.dark) .checkbox-disabled + .checkbox-visual {
		@apply bg-gray-900 border-gray-700;
	}

	.checkbox-visual:hover {
		@apply border-gray-400;
	}

	:global(.dark) .checkbox-visual:hover {
		@apply border-gray-500;
	}

	.checkbox-checked + .checkbox-visual:hover,
	.checkbox-indeterminate + .checkbox-visual:hover {
		@apply bg-primary-700 border-primary-700;
	}

	.checkbox-disabled + .checkbox-visual:hover {
		@apply border-gray-200;
	}

	:global(.dark) .checkbox-disabled + .checkbox-visual:hover {
		@apply border-gray-700;
	}

	/* Size variants */
	.checkbox-sm + .checkbox-visual {
		@apply w-4 h-4;
	}

	.checkbox-md + .checkbox-visual {
		@apply w-5 h-5;
	}

	.checkbox-lg + .checkbox-visual {
		@apply w-6 h-6;
	}

	.checkbox-icon {
		@apply text-white;
		display: inline-block;
		background-color: currentColor;
		mask-size: contain;
		mask-repeat: no-repeat;
		mask-position: center;
	}

	.checkbox-sm + .checkbox-visual .checkbox-icon {
		@apply w-2.5 h-2.5;
	}

	.checkbox-md + .checkbox-visual .checkbox-icon {
		@apply w-3 h-3;
	}

	.checkbox-lg + .checkbox-visual .checkbox-icon {
		@apply w-4 h-4;
	}

	.icon-check {
		mask-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='1.5' stroke='currentColor'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='m4.5 12.75 6 6 9-13.5' /%3e%3c/svg%3e");
	}

	.icon-minus {
		mask-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='1.5' stroke='currentColor'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='M5 12h14' /%3e%3c/svg%3e");
	}

	.checkbox-content {
		@apply flex-1;
	}

	.checkbox-label {
		@apply block text-sm font-medium text-gray-700 cursor-pointer;
		font-family: var(--font-primary);
	}

	:global(.dark) .checkbox-label {
		@apply text-gray-300;
	}

	.checkbox-description {
		@apply mt-1 text-xs text-gray-500;
		font-family: var(--font-primary);
	}

	:global(.dark) .checkbox-description {
		@apply text-gray-400;
	}

	.checkbox-error-text {
		@apply mt-2 text-xs text-error-600;
		font-family: var(--font-primary);
	}

	:global(.dark) .checkbox-error-text {
		@apply text-error-400;
	}
</style>