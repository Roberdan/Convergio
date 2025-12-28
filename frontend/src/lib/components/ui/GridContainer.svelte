<script lang="ts">
	interface $$Props {
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
	}

	export let cols: $$Props['cols'] = 12;
	export let gap: NonNullable<$$Props['gap']> = 'md';
	export let responsive: $$Props['responsive'] = {};
	export let minItemWidth: $$Props['minItemWidth'] = '300px';
	export let maxItemWidth: $$Props['maxItemWidth'] = '1fr';
	export let alignItems: $$Props['alignItems'] = 'stretch';
	export let justifyItems: $$Props['justifyItems'] = 'stretch';

	// Compute CSS classes
	$: gapClasses = {
		none: 'gap-0',
		sm: 'gap-4',
		md: 'gap-6',
		lg: 'gap-8',
		xl: 'gap-12'
	};

	$: colsClasses = {
		1: 'grid-cols-1',
		2: 'grid-cols-2',
		3: 'grid-cols-3',
		4: 'grid-cols-4',
		5: 'grid-cols-5',
		6: 'grid-cols-6',
		12: 'grid-cols-12',
		'auto-fit': 'grid-cols-auto-fit',
		'auto-fill': 'grid-cols-auto-fill'
	};

	$: responsiveClasses = [
		responsive?.sm ? `sm:${colsClasses[responsive.sm]}` : '',
		responsive?.md ? `md:${colsClasses[responsive.md]}` : '',
		responsive?.lg ? `lg:${colsClasses[responsive.lg]}` : '',
		responsive?.xl ? `xl:${colsClasses[responsive.xl]}` : ''
	].filter(Boolean);

	$: alignItemsClasses = {
		start: 'items-start',
		center: 'items-center',
		end: 'items-end',
		stretch: 'items-stretch'
	};

	$: justifyItemsClasses = {
		start: 'justify-items-start',
		center: 'justify-items-center',
		end: 'justify-items-end',
		stretch: 'justify-items-stretch'
	};

	$: classes = [
		'grid',
		colsClasses[cols ?? 12],
		gapClasses[gap],
		alignItems ? alignItemsClasses[alignItems] : '',
		justifyItems ? justifyItemsClasses[justifyItems] : '',
		...responsiveClasses
	].filter(Boolean).join(' ');

	// Dynamic styles for auto-fit/auto-fill
	$: gridStyle = (cols === 'auto-fit' || cols === 'auto-fill') 
		? `grid-template-columns: repeat(${cols}, minmax(${minItemWidth}, ${maxItemWidth}));`
		: '';
</script>

<div class={classes} style={gridStyle} {...$$restProps}>
	<slot />
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