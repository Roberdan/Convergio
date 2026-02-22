<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import type { HTMLButtonAttributes } from 'svelte/elements';

	

	interface Props {
		variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
		size?: 'sm' | 'md' | 'lg' | 'icon';
		loading?: boolean;
		loadingText?: string;
		icon?: string;
		iconPosition?: 'left' | 'right';
		fullWidth?: boolean;
		disabled?: HTMLButtonAttributes['disabled'];
		type?: HTMLButtonAttributes['type'];
		children?: import('svelte').Snippet;
		[key: string]: any
	}

	let {
		variant = 'primary',
		size = 'md',
		loading = false,
		loadingText = 'Loading...',
		icon = '',
		iconPosition = 'left',
		fullWidth = false,
		disabled = false,
		type = 'button',
		children,
		...rest
	}: Props = $props();

	const dispatch = createEventDispatcher<{
		click: MouseEvent;
	}>();

	// Compute CSS classes based on props
	let variantClasses = $derived({
		primary: 'btn-primary',
		secondary: 'btn-secondary', 
		outline: 'btn-outline',
		ghost: 'btn-ghost'
	});

	let sizeClasses = $derived({
		sm: 'btn-sm',
		md: '',
		lg: 'btn-lg',
		icon: 'btn-icon'
	});

	let classes = $derived([
		'btn',
		variantClasses[variant],
		sizeClasses[size],
		fullWidth ? 'w-full' : '',
		loading ? 'btn-loading' : '',
		disabled ? 'opacity-50 cursor-not-allowed' : ''
	].filter(Boolean).join(' '));

	function handleClick(event: MouseEvent) {
		if (disabled || loading) {
			event.preventDefault();
			return;
		}
		dispatch('click', event);
	}
</script>

<button 
	{type}
	class={classes}
	{disabled}
	onclick={handleClick}
	{...rest}
>
	{#if loading}
		<div class="loading-spinner" aria-hidden="true"></div>
		{#if loadingText && size !== 'icon'}
			<span class="sr-only">{loadingText}</span>
		{/if}
	{:else}
		{#if icon && iconPosition === 'left' && size !== 'icon'}
			<span class="icon-{icon}" aria-hidden="true"></span>
		{/if}
		
		{#if size === 'icon'}
			{#if icon}
				<span class="icon-{icon}" aria-hidden="true"></span>
			{:else}
				{@render children?.()}
			{/if}
		{:else}
			{@render children?.()}
		{/if}
		
		{#if icon && iconPosition === 'right' && size !== 'icon'}
			<span class="icon-{icon}" aria-hidden="true"></span>
		{/if}
	{/if}
</button>

<style>
	.btn {
		font-family: var(--font-primary);
	}
	
	/* Icon placeholder styles - replace with your icon system */
	[class^="icon-"] {
		display: inline-block;
		width: 1rem;
		height: 1rem;
		background-color: currentColor;
		mask-size: contain;
		mask-repeat: no-repeat;
		mask-position: center;
	}
	
	.icon-plus {
		mask-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='1.5' stroke='currentColor'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='M12 4.5v15m7.5-7.5h-15' /%3e%3c/svg%3e");
	}
	
	.icon-edit {
		mask-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='1.5' stroke='currentColor'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L10.582 16.07a4.5 4.5 0 0 1-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 0 1 1.13-1.897l8.932-8.931Zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0 1 15.75 21H5.25A2.25 2.25 0 0 1 3 18.75V8.25A2.25 2.25 0 0 1 5.25 6H10' /%3e%3c/svg%3e");
	}
	
	.icon-save {
		mask-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='1.5' stroke='currentColor'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='M17.593 3.322c1.1.128 1.907 1.077 1.907 2.185V21L12 17.25 4.5 21V5.507c0-1.108.806-2.057 1.907-2.185a48.507 48.507 0 0 1 11.186 0Z' /%3e%3c/svg%3e");
	}
	
	.icon-delete {
		mask-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='1.5' stroke='currentColor'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0' /%3e%3c/svg%3e");
	}
</style>
