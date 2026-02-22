<script lang="ts">
	import { createBubbler } from 'svelte/legacy';

	const bubble = createBubbler();
	import type { HTMLAttributes } from 'svelte/elements';

	

	interface Props {
		variant?: 'default' | 'elevated' | 'flat';
		hoverable?: boolean;
		clickable?: boolean;
		header?: import('svelte').Snippet;
		children?: import('svelte').Snippet;
		content?: import('svelte').Snippet;
		footer?: import('svelte').Snippet;
		[key: string]: any
	}

	let {
		variant = 'default',
		hoverable = true,
		clickable = false,
		header,
		children,
		content,
		footer,
		...rest
	}: Props = $props();

	// Compute CSS classes  
	let variantClasses = $derived({
		default: 'card',
		elevated: 'card-elevated', 
		flat: 'card-flat'
	});

	let classes = $derived([
		variantClasses[variant],
		hoverable && !clickable ? 'hover:shadow-md hover:-translate-y-1' : '',
		clickable ? 'cursor-pointer hover:shadow-lg hover:-translate-y-1 active:scale-[0.98]' : '',
		'transition-all duration-200'
	].filter(Boolean).join(' '));
</script>

<div class={classes} {...rest} onclick={bubble('click')}>
	{#if header}
		<div class="card-header">
			{@render header?.()}
		</div>
	{/if}

	{#if children || content}
		<div class="card-content">
			{#if content}{@render content()}{:else}
				{@render children?.()}
			{/if}
		</div>
	{/if}

	{#if footer}
		<div class="card-footer">
			{@render footer?.()}
		</div>
	{/if}
</div>