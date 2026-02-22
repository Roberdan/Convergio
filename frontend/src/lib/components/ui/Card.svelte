<script lang="ts">
	import { createBubbler } from 'svelte/legacy';

	const bubble = createBubbler();
	import type { HTMLAttributes } from 'svelte/elements';

	

	interface Props {
		variant?: 'default' | 'elevated' | 'flat' | 'stats';
		padding?: 'none' | 'sm' | 'md' | 'lg';
		hoverable?: boolean;
		clickable?: boolean;
		children?: import('svelte').Snippet;
		header?: import('svelte').Snippet;
		content?: import('svelte').Snippet;
		footer?: import('svelte').Snippet;
		[key: string]: any
	}

	let {
		variant = 'default',
		padding = 'md',
		hoverable = true,
		clickable = false,
		children,
		header,
		content,
		footer,
		...rest
	}: Props = $props();

	// Compute CSS classes
	let variantClasses = $derived({
		default: 'card',
		elevated: 'card-elevated',
		flat: 'card-flat',
		stats: 'card-stats'
	});

	let paddingClasses = $derived({
		none: '',
		sm: 'p-4',
		md: 'p-6',
		lg: 'p-8'
	});

	let classes = $derived([
		variantClasses[variant],
		variant !== 'stats' ? paddingClasses[padding] : '', // stats card has its own padding
		hoverable && !clickable ? 'hover:shadow-md hover:-translate-y-1' : '',
		clickable ? 'cursor-pointer hover:shadow-lg hover:-translate-y-1 active:scale-[0.98]' : '',
		'transition-all duration-200'
	].filter(Boolean).join(' '));
</script>

<div class={classes} {...rest} onclick={bubble('click')}>
	{@render children?.()}
</div>

<!-- Card with separate sections -->
<div class="card-wrapper" style="display: none;">
	<!-- This is a template for structured cards -->
	<div class="card">
		<div class="card-header">
			{@render header?.()}
		</div>
		<div class="card-content">
			{@render content?.()}
		</div>
		<div class="card-footer">
			{@render footer?.()}
		</div>
	</div>
</div>