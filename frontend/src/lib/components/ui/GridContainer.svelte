<script lang="ts">
	

	interface Props {
		cols?: 1 | 2 | 3 | 4 | 5 | 6 | 12 | 'auto-fit' | 'auto-fill';
		gap?: 'none' | 'sm' | 'md' | 'lg' | 'xl';
		responsive?: {
			sm?: 1 | 2 | 3 | 4 | 5 | 6 | 12 | 'auto-fit' | 'auto-fill';
			md?: 1 | 2 | 3 | 4 | 5 | 6 | 12 | 'auto-fit' | 'auto-fill';
			lg?: 1 | 2 | 3 | 4 | 5 | 6 | 12 | 'auto-fit' | 'auto-fill';
			xl?: 1 | 2 | 3 | 4 | 5 | 6 | 12 | 'auto-fit' | 'auto-fill';
		};
		minItemWidth?: string;
		maxItemWidth?: string;
		alignItems?: 'start' | 'center' | 'end' | 'stretch';
		justifyItems?: 'start' | 'center' | 'end' | 'stretch';
		children?: import('svelte').Snippet;
		[key: string]: any
	}

	let {
		cols = 12,
		gap = 'md',
		responsive = {},
		minItemWidth = '300px',
		maxItemWidth = '1fr',
		alignItems = 'stretch',
		justifyItems = 'stretch',
		children,
		...rest
	}: Props = $props();

	// Compute CSS classes
	let gapClasses = $derived({
		none: 'gap-0',
		sm: 'gap-4',
		md: 'gap-6',
		lg: 'gap-8',
		xl: 'gap-12'
	});

	let colsClasses = $derived({
		1: 'grid-cols-1',
		2: 'grid-cols-2',
		3: 'grid-cols-3',
		4: 'grid-cols-4',
		5: 'grid-cols-5',
		6: 'grid-cols-6',
		12: 'grid-cols-12',
		'auto-fit': 'grid-cols-auto-fit',
		'auto-fill': 'grid-cols-auto-fill'
	});

	let responsiveClasses = $derived([
		responsive?.sm ? `sm:${colsClasses[responsive.sm]}` : '',
		responsive?.md ? `md:${colsClasses[responsive.md]}` : '',
		responsive?.lg ? `lg:${colsClasses[responsive.lg]}` : '',
		responsive?.xl ? `xl:${colsClasses[responsive.xl]}` : ''
	].filter(Boolean));

	let alignItemsClasses = $derived({
		start: 'items-start',
		center: 'items-center',
		end: 'items-end',
		stretch: 'items-stretch'
	});

	let justifyItemsClasses = $derived({
		start: 'justify-items-start',
		center: 'justify-items-center',
		end: 'justify-items-end',
		stretch: 'justify-items-stretch'
	});

	let classes = $derived([
		'grid',
		colsClasses[cols ?? 12],
		gapClasses[gap],
		alignItems ? alignItemsClasses[alignItems] : '',
		justifyItems ? justifyItemsClasses[justifyItems] : '',
		...responsiveClasses
	].filter(Boolean).join(' '));

	// Dynamic styles for auto-fit/auto-fill
	let gridStyle = $derived((cols === 'auto-fit' || cols === 'auto-fill') 
		? `grid-template-columns: repeat(${cols}, minmax(${minItemWidth}, ${maxItemWidth}));`
		: '');
</script>

<div class={classes} style={gridStyle} {...rest}>
	{@render children?.()}
</div>

<style>
	/* Custom grid utilities for auto-fit and auto-fill */
	:global(.grid-cols-auto-fit) {
		grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
	}

	:global(.grid-cols-auto-fill) {
		grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
	}

	/* Responsive auto-fit variants */
	@media (min-width: 640px) {
		:global(.sm\\:grid-cols-auto-fit) {
			grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
		}

		:global(.sm\\:grid-cols-auto-fill) {
			grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
		}
	}

	@media (min-width: 768px) {
		:global(.md\\:grid-cols-auto-fit) {
			grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
		}

		:global(.md\\:grid-cols-auto-fill) {
			grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
		}
	}

	@media (min-width: 1024px) {
		:global(.lg\\:grid-cols-auto-fit) {
			grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
		}

		:global(.lg\\:grid-cols-auto-fill) {
			grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
		}
	}

	@media (min-width: 1280px) {
		:global(.xl\\:grid-cols-auto-fit) {
			grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
		}

		:global(.xl\\:grid-cols-auto-fill) {
			grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
		}
	}
</style>