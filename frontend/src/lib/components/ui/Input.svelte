<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import type { HTMLInputAttributes } from 'svelte/elements';

	

	interface Props {
		variant?: 'default' | 'error' | 'success';
		size?: 'sm' | 'md' | 'lg';
		label?: string;
		helperText?: string;
		errorMessage?: string;
		leadingIcon?: string;
		trailingIcon?: string;
		clearable?: boolean;
		required?: boolean;
		disabled?: HTMLInputAttributes['disabled'];
		value?: HTMLInputAttributes['value'];
		placeholder?: HTMLInputAttributes['placeholder'];
		type?: HTMLInputAttributes['type'];
		id?: HTMLInputAttributes['id'];
		[key: string]: any
	}

	let {
		variant = 'default',
		size = 'md',
		label = '',
		helperText = '',
		errorMessage = '',
		leadingIcon = '',
		trailingIcon = '',
		clearable = false,
		required = false,
		disabled = false,
		value = $bindable(''),
		placeholder = '',
		type = 'text',
		id = '',
		...rest
	}: Props = $props();

	const dispatch = createEventDispatcher<{
		input: Event;
		change: Event;
		focus: FocusEvent;
		blur: FocusEvent;
		clear: void;
	}>();

	// Generate unique ID if not provided
	const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`;

	// Compute CSS classes
	let variantClasses = $derived({
		default: 'input',
		error: 'input input-error',
		success: 'input input-success'
	});

	let sizeClasses = $derived({
		sm: 'input-sm',
		md: '',
		lg: 'input-lg'
	});

	let inputClasses = $derived([
		variantClasses[variant],
		sizeClasses[size],
		leadingIcon ? 'pl-10' : '',
		trailingIcon || clearable ? 'pr-10' : ''
	].filter(Boolean).join(' '));

	let showError = $derived(variant === 'error' && errorMessage);
	let showHelper = $derived(!showError && helperText);

	function handleInput(event: Event) {
		dispatch('input', event);
	}

	function handleChange(event: Event) {
		dispatch('change', event);
	}

	function handleFocus(event: FocusEvent) {
		dispatch('focus', event);
	}

	function handleBlur(event: FocusEvent) {
		dispatch('blur', event);
	}

	function handleClear() {
		value = '';
		dispatch('clear');
	}
</script>

<div class="input-wrapper">
	{#if label}
		<label for={inputId} class="input-label">
			{label}
			{#if required}
				<span class="text-error-500 ml-1">*</span>
			{/if}
		</label>
	{/if}

	<div class="input-container">
		{#if leadingIcon}
			<div class="input-icon input-icon-leading">
				<span class="icon-{leadingIcon}" aria-hidden="true"></span>
			</div>
		{/if}

		<input
			{...rest}
			{id}
			{type}
			{placeholder}
			{disabled}
			{required}
			bind:value
			class={inputClasses}
			oninput={handleInput}
			onchange={handleChange}
			onfocus={handleFocus}
			onblur={handleBlur}
		/>

		{#if clearable && value}
			<button
				type="button"
				class="input-icon input-icon-trailing input-clear-btn"
				onclick={handleClear}
				aria-label="Clear input"
			>
				<span class="icon-x" aria-hidden="true"></span>
			</button>
		{:else if trailingIcon}
			<div class="input-icon input-icon-trailing">
				<span class="icon-{trailingIcon}" aria-hidden="true"></span>
			</div>
		{/if}
	</div>

	{#if showError}
		<p class="input-feedback input-error-text" role="alert">
			{errorMessage}
		</p>
	{:else if showHelper}
		<p class="input-feedback input-helper-text">
			{helperText}
		</p>
	{/if}
</div>

<style>
	.input-wrapper {
		@apply w-full;
	}

	.input-label {
		@apply block text-sm font-medium text-gray-700 mb-2;
		font-family: var(--font-primary);
	}

	.input-container {
		@apply relative;
	}

	.input-icon {
		@apply absolute inset-y-0 flex items-center pointer-events-none;
		width: 1rem;
		height: 1rem;
	}

	.input-icon-leading {
		@apply left-3;
	}

	.input-icon-trailing {
		@apply right-3;
	}

	.input-clear-btn {
		@apply absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-auto cursor-pointer text-gray-400 hover:text-gray-600 transition-colors duration-200;
	}

	.input-feedback {
		@apply mt-2 text-xs;
		font-family: var(--font-primary);
	}

	.input-error-text {
		@apply text-error-600;
	}

	.input-helper-text {
		@apply text-gray-500;
	}

	/* Icon styles - replace with your icon system */
	[class^="icon-"] {
		display: inline-block;
		width: 1rem;
		height: 1rem;
		background-color: currentColor;
		mask-size: contain;
		mask-repeat: no-repeat;
		mask-position: center;
	}

	.icon-search {
		mask-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='1.5' stroke='currentColor'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z' /%3e%3c/svg%3e");
	}

	.icon-x {
		mask-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='1.5' stroke='currentColor'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='M6 18 18 6M6 6l12 12' /%3e%3c/svg%3e");
	}

	.icon-email {
		mask-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='1.5' stroke='currentColor'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='M21.75 6.75v10.5a2.25 2.25 0 0 1-2.25 2.25h-15a2.25 2.25 0 0 1-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0 0 19.5 4.5h-15a2.25 2.25 0 0 0-2.25 2.25m19.5 0v.243a2.25 2.25 0 0 1-1.07 1.916l-7.5 4.615a2.25 2.25 0 0 1-2.36 0L3.32 8.91a2.25 2.25 0 0 1-1.07-1.916V6.75' /%3e%3c/svg%3e");
	}

	.icon-lock {
		mask-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='1.5' stroke='currentColor'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='M16.5 10.5V6.75a4.5 4.5 0 1 0-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 0 0 2.25-2.25v-6.75a2.25 2.25 0 0 0-2.25-2.25H6.75a2.25 2.25 0 0 0-2.25 2.25v6.75a2.25 2.25 0 0 0 2.25 2.25Z' /%3e%3c/svg%3e");
	}

	.icon-user {
		mask-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='1.5' stroke='currentColor'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.501 20.118a7.5 7.5 0 0 1 14.998 0A17.933 17.933 0 0 1 12 21.75c-2.676 0-5.216-.584-7.499-1.632Z' /%3e%3c/svg%3e");
	}
</style>
