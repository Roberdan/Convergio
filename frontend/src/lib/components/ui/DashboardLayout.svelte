<script lang="ts">
	import { onMount } from 'svelte';
	import { writable } from 'svelte/store';

	interface $$Props {
		sidebarCollapsed?: boolean;
		showMobileOverlay?: boolean;
		fixedHeader?: boolean;
		maxWidth?: 'full' | 'wide' | 'narrow';
	}

	export let sidebarCollapsed: $$Props['sidebarCollapsed'] = false;
	export let showMobileOverlay: $$Props['showMobileOverlay'] = false; 
	export let fixedHeader: $$Props['fixedHeader'] = true;
	export let maxWidth: NonNullable<$$Props['maxWidth']> = 'full';

	// Create stores for responsive behavior
	const isMobile = writable(false);
	const isTablet = writable(false);

	// Handle responsive behavior
	onMount(() => {
		const checkScreenSize = () => {
			isMobile.set(window.innerWidth < 768);
			isTablet.set(window.innerWidth >= 768 && window.innerWidth < 1024);
		};

		checkScreenSize();
		window.addEventListener('resize', checkScreenSize);

		return () => {
			window.removeEventListener('resize', checkScreenSize);
		};
	});

	// Close mobile sidebar when clicking overlay
	function closeMobileSidebar() {
		showMobileOverlay = false;
	}

	// Compute container classes
	$: containerClasses = {
		full: 'container-wide',
		wide: 'container-wide', 
		narrow: 'container-narrow'
	};

	$: mainClasses = [
		'dashboard-main',
		sidebarCollapsed ? 'sidebar-collapsed' : 'sidebar-expanded',
		fixedHeader ? 'fixed-header' : ''
	].filter(Boolean).join(' ');
</script>

<div class="dashboard-layout">
	<!-- Sidebar -->
	<aside class="dashboard-sidebar" class:collapsed={sidebarCollapsed} class:mobile-open={showMobileOverlay}>
		<slot name="sidebar" />
	</aside>

	<!-- Mobile overlay -->
	{#if showMobileOverlay}
		<div 
			class="mobile-overlay" 
			on:click={closeMobileSidebar}
			on:keydown={(e) => e.key === 'Escape' && closeMobileSidebar()}
			role="button"
			tabindex="0"
			aria-label="Close sidebar"
		></div>
	{/if}

	<!-- Main content area -->
	<div class={mainClasses}>
		<!-- Header -->
		{#if $$slots.header}
			<header class="dashboard-header" class:fixed={fixedHeader}>
				<slot name="header" />
			</header>
		{/if}

		<!-- Page content -->
		<main class="dashboard-content {containerClasses[maxWidth]}">
			<slot />
		</main>

		<!-- Footer -->
		{#if $$slots.footer}
			<footer class="dashboard-footer">
				<slot name="footer" />
			</footer>
		{/if}
	</div>
</div>

<style>
	.dashboard-layout {
		@apply min-h-screen bg-gray-50 flex;
	}

	/* Sidebar */
	.dashboard-sidebar {
		@apply fixed inset-y-0 left-0 z-50 w-64 bg-white border-r border-gray-200 transform transition-transform duration-300 ease-in-out;
		box-shadow: var(--shadow-lg);
	}

	.dashboard-sidebar.collapsed {
		@apply -translate-x-full lg:translate-x-0 lg:w-20;
	}

	.dashboard-sidebar.mobile-open {
		@apply translate-x-0;
	}

	/* Mobile overlay */
	.mobile-overlay {
		@apply fixed inset-0 z-40 bg-black bg-opacity-50 lg:hidden;
	}

	/* Main content */
	.dashboard-main {
		@apply flex-1 flex flex-col min-h-screen transition-all duration-300 ease-in-out;
		margin-left: 0;
	}

	.dashboard-main.sidebar-expanded {
		@apply lg:ml-64;
	}

	.dashboard-main.sidebar-collapsed {
		@apply lg:ml-20;
	}

	/* Header */
	.dashboard-header {
		@apply bg-white border-b border-gray-200 px-6 py-4 z-30;
		box-shadow: var(--shadow-sm);
	}

	.dashboard-header.fixed {
		@apply sticky top-0;
	}

	/* Content */
	.dashboard-content {
		@apply flex-1 px-6 py-8 overflow-auto;
	}

	/* Footer */
	.dashboard-footer {
		@apply bg-white border-t border-gray-200 px-6 py-4 mt-auto;
	}

	/* Responsive adjustments */
	@media (max-width: 1023px) {
		.dashboard-sidebar {
			@apply -translate-x-full;
		}

		.dashboard-main {
			@apply ml-0;
		}

		.dashboard-main.sidebar-expanded,
		.dashboard-main.sidebar-collapsed {
			@apply ml-0;
		}
	}

	/* Animation for smooth transitions */
	@media (prefers-reduced-motion: no-preference) {
		.dashboard-layout * {
			transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
		}
	}

	/* Glass effect for modern look */
	.dashboard-header {
		backdrop-filter: blur(8px) saturate(180%);
		background-color: rgba(255, 255, 255, 0.8);
	}

	.dark .dashboard-header {
		background-color: rgba(31, 41, 55, 0.8);
	}
</style>