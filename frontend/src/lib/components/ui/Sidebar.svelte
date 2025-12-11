<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { Badge, Avatar } from './index';

	interface MenuItem {
		id: string;
		label: string;
		icon: string;
		href?: string;
		badge?: {
			text: string;
			variant?: 'primary' | 'success' | 'warning' | 'error' | 'info' | 'gray';
		};
		children?: MenuItem[];
		active?: boolean;
		disabled?: boolean;
	}

	interface $$Props {
		collapsed?: boolean;
		menuItems?: MenuItem[];
		userInfo?: {
			name: string;
			email: string;
			avatar?: string;
			role?: string;
		};
		showUserInfo?: boolean;
		showFooter?: boolean;
		brand?: {
			name: string;
			logo?: string;
		};
	}

	export let collapsed: $$Props['collapsed'] = false;
	export let menuItems: $$Props['menuItems'] = [];
	export let userInfo: $$Props['userInfo'] = {
		name: 'User Name',
		email: 'user@example.com'
	};
	export let showUserInfo: $$Props['showUserInfo'] = true;
	export let showFooter: $$Props['showFooter'] = true;
	export let brand: $$Props['brand'] = {
		name: 'Convergio'
	};

	const dispatch = createEventDispatcher<{
		'menu-click': { item: MenuItem };
		'user-click': void;
	}>();

	let expandedGroups = new Set<string>();

	function handleMenuClick(item: MenuItem) {
		if (item.disabled) return;
		
		if (item.children && item.children.length > 0) {
			toggleGroup(item.id);
		} else {
			dispatch('menu-click', { item });
		}
	}

	function toggleGroup(groupId: string) {
		if (expandedGroups.has(groupId)) {
			expandedGroups.delete(groupId);
		} else {
			expandedGroups.add(groupId);
		}
		expandedGroups = new Set(expandedGroups);
	}

	function handleUserClick() {
		dispatch('user-click');
	}

	// Default menu items if none provided
	$: defaultMenuItems = [
		{
			id: 'dashboard',
			label: 'Dashboard',
			icon: 'dashboard',
			href: '/dashboard',
			active: true
		},
		{
			id: 'agents',
			label: 'Agents',
			icon: 'users',
			href: '/agents',
			badge: { text: '12', variant: 'primary' as const }
		},
		{
			id: 'conversations',
			label: 'Conversations',
			icon: 'chat',
			href: '/conversations',
			badge: { text: 'New', variant: 'success' as const }
		},
		{
			id: 'analytics',
			label: 'Analytics',
			icon: 'chart',
			children: [
				{ id: 'overview', label: 'Overview', icon: 'overview', href: '/analytics' },
				{ id: 'reports', label: 'Reports', icon: 'reports', href: '/analytics/reports' },
				{ id: 'metrics', label: 'Metrics', icon: 'metrics', href: '/analytics/metrics' }
			]
		},
		{
			id: 'settings',
			label: 'Settings',
			icon: 'settings',
			href: '/settings'
		}
	];

	$: items = menuItems.length > 0 ? menuItems : defaultMenuItems;
</script>

<div class="sidebar" class:collapsed>
	<!-- Brand/Logo -->
	<div class="sidebar-header">
		{#if brand.logo}
			<img src={brand.logo} alt={brand.name} class="brand-logo" />
		{:else}
			<div class="brand-logo-placeholder">
				<span class="icon-logo" aria-hidden="true"></span>
			</div>
		{/if}
		
		{#if !collapsed}
			<span class="brand-name">{brand.name}</span>
		{/if}
	</div>

	<!-- Navigation Menu -->
	<nav class="sidebar-nav" role="navigation" aria-label="Main navigation">
		<ul class="nav-list" role="list">
			{#each items as item (item.id)}
				<li class="nav-item" role="listitem">
					{#if item.children && item.children.length > 0}
						<!-- Group with children -->
						<button
							type="button"
							class="nav-link nav-group"
							class:active={item.active}
							class:disabled={item.disabled}
							on:click={() => handleMenuClick(item)}
							aria-expanded={expandedGroups.has(item.id)}
							aria-controls="group-{item.id}"
						>
							<span class="nav-icon icon-{item.icon}" aria-hidden="true"></span>
							{#if !collapsed}
								<span class="nav-label">{item.label}</span>
								{#if item.badge}
									<Badge variant={item.badge.variant} size="sm" class="nav-badge">
										{item.badge.text}
									</Badge>
								{/if}
								<span 
									class="nav-chevron icon-chevron-down" 
									class:expanded={expandedGroups.has(item.id)}
									aria-hidden="true"
								></span>
							{/if}
						</button>

						<!-- Children -->
						{#if !collapsed && expandedGroups.has(item.id)}
							<ul class="nav-children" id="group-{item.id}" role="list">
								{#each item.children as child (child.id)}
									<li role="listitem">
										<a
											href={child.href}
											class="nav-link nav-child"
											class:active={child.active}
											class:disabled={child.disabled}
											on:click={() => handleMenuClick(child)}
										>
											<span class="nav-icon icon-{child.icon}" aria-hidden="true"></span>
											<span class="nav-label">{child.label}</span>
											{#if child.badge}
												<Badge variant={child.badge.variant} size="sm" class="nav-badge">
													{child.badge.text}
												</Badge>
											{/if}
										</a>
									</li>
								{/each}
							</ul>
						{/if}
					{:else}
						<!-- Single menu item -->
						<a
							href={item.href}
							class="nav-link"
							class:active={item.active}
							class:disabled={item.disabled}
							on:click={() => handleMenuClick(item)}
						>
							<span class="nav-icon icon-{item.icon}" aria-hidden="true"></span>
							{#if !collapsed}
								<span class="nav-label">{item.label}</span>
								{#if item.badge}
									<Badge variant={item.badge.variant} size="sm" class="nav-badge">
										{item.badge.text}
									</Badge>
								{/if}
							{/if}
						</a>
					{/if}
				</li>
			{/each}
		</ul>
	</nav>

	<!-- User Info -->
	{#if showUserInfo && !collapsed}
		<div class="sidebar-user">
			<button
				type="button"
				class="user-info-button"
				on:click={handleUserClick}
				aria-label="User profile"
			>
				<Avatar
					src={userInfo.avatar}
					fallback={userInfo.name}
					size="sm"
				/>
				<div class="user-details">
					<span class="user-name">{userInfo.name}</span>
					<span class="user-email">{userInfo.email}</span>
					{#if userInfo.role}
						<Badge variant="gray" size="sm" class="user-role">
							{userInfo.role}
						</Badge>
					{/if}
				</div>
			</button>
		</div>
	{/if}

	<!-- Footer -->
	{#if showFooter && !collapsed}
		<div class="sidebar-footer">
			<slot name="footer">
				<p class="footer-text">© 2024 Convergio</p>
			</slot>
		</div>
	{/if}
</div>

<style>
	.sidebar {
		@apply h-full flex flex-col bg-white border-r border-gray-200 transition-all duration-300 ease-in-out overflow-hidden;
		width: 16rem; /* 256px */
	}

	.sidebar.collapsed {
		width: 5rem; /* 80px */
	}

	.sidebar-header {
		@apply flex items-center gap-3 px-6 py-6 border-b border-gray-200;
	}

	.collapsed .sidebar-header {
		@apply px-4 justify-center;
	}

	.brand-logo,
	.brand-logo-placeholder {
		@apply w-8 h-8 rounded-lg bg-primary-600 flex items-center justify-center flex-shrink-0;
	}

	.brand-logo {
		@apply object-cover;
	}

	.brand-name {
		@apply text-lg font-bold text-gray-900 truncate;
		font-family: var(--font-primary);
	}

	.sidebar-nav {
		flex: 1;
		padding: 1.5rem 1rem;
		overflow-y: auto;
	}

	.nav-list {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.nav-item {
		position: relative;
	}

	.nav-link {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 0.5rem 0.75rem;
		font-size: var(--text-sm);
		font-weight: var(--font-medium);
		color: var(--color-text-secondary);
		border-radius: var(--radius-lg);
		transition: all 0.2s ease;
		font-family: var(--font-primary);
		outline: none;
	}
	
	.nav-link:hover {
		background-color: var(--color-surface-100);
	}

	.nav-link:focus {
		box-shadow: 0 0 0 2px var(--color-primary-500);
	}

	.nav-link.active {
		background-color: var(--color-primary-100);
		color: var(--color-primary-700);
	}
	
	.dark .nav-link.active {
		background-color: var(--color-primary-900);
		color: var(--color-primary-300);
	}

	.nav-link.disabled {
		opacity: 0.5;
		cursor: not-allowed;
		pointer-events: none;
	}

	.nav-group {
		border: none;
		background-color: transparent;
		cursor: pointer;
	}

	.nav-child {
		margin-left: 1.5rem;
		font-size: var(--text-xs);
	}

	.collapsed .nav-link {
		justify-content: center;
		padding-left: 0.5rem;
		padding-right: 0.5rem;
	}

	.nav-icon {
		width: 1.25rem;
		height: 1.25rem;
		flex-shrink: 0;
	}

	.nav-label {
		flex: 1;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.nav-badge {
		@apply ml-auto;
	}

	.nav-chevron {
		@apply w-4 h-4 transition-transform duration-200;
	}

	.nav-chevron.expanded {
		@apply rotate-180;
	}

	.nav-children {
		@apply mt-2 space-y-1;
		animation: slideDown 0.2s ease-out;
	}

	.sidebar-user {
		@apply px-4 py-4 border-t border-gray-200;
	}

	.user-info-button {
		@apply w-full flex items-center gap-3 p-3 rounded-lg hover:bg-gray-100 transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-primary-500;
	}

	.user-details {
		@apply flex-1 text-left;
	}

	.user-name {
		@apply block text-sm font-medium text-gray-900 truncate;
		font-family: var(--font-primary);
	}

	.user-email {
		@apply block text-xs text-gray-500 truncate;
		font-family: var(--font-primary);
	}

	.user-role {
		@apply mt-1;
	}

	.sidebar-footer {
		@apply px-6 py-4 border-t border-gray-200;
	}

	.footer-text {
		@apply text-xs text-gray-500 text-center;
		font-family: var(--font-primary);
	}

	/* Icon styles */
	[class^="icon-"] {
		display: inline-block;
		background-color: currentColor;
		mask-size: contain;
		mask-repeat: no-repeat;
		mask-position: center;
	}

	.icon-logo {
		@apply w-6 h-6 text-white;
		mask-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='1.5' stroke='currentColor'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09ZM18.259 8.715 18 9.75l-.259-1.035a3.375 3.375 0 0 0-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 0 0 2.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 0 0 2.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 0 0-2.456 2.456ZM16.894 20.567 16.5 21.75l-.394-1.183a2.25 2.25 0 0 0-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 0 0 1.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 0 0 1.423 1.423l1.183.394-1.183.394a2.25 2.25 0 0 0-1.423 1.423Z' /%3e%3c/svg%3e");
	}

	.icon-dashboard {
		mask-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='1.5' stroke='currentColor'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='M3.75 6A2.25 2.25 0 0 1 6 3.75h2.25A2.25 2.25 0 0 1 10.5 6v2.25a2.25 2.25 0 0 1-2.25 2.25H6a2.25 2.25 0 0 1-2.25-2.25V6ZM13.5 6a2.25 2.25 0 0 1 2.25-2.25H18A2.25 2.25 0 0 1 20.25 6v2.25A2.25 2.25 0 0 1 18 10.5h-2.25a2.25 2.25 0 0 1-2.25-2.25V6ZM3.75 15.75A2.25 2.25 0 0 1 6 13.5h2.25a2.25 2.25 0 0 1 2.25 2.25V18a2.25 2.25 0 0 1-2.25 2.25H6A2.25 2.25 0 0 1 3.75 18v-2.25ZM13.5 15.75a2.25 2.25 0 0 1 2.25-2.25H18a2.25 2.25 0 0 1 2.25 2.25V18A2.25 2.25 0 0 1 18 20.25h-2.25A2.25 2.25 0 0 1 13.5 18v-2.25Z' /%3e%3c/svg%3e");
	}

	.icon-users {
		mask-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='1.5' stroke='currentColor'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='M15 19.128a9.38 9.38 0 0 0 2.625.372 9.337 9.337 0 0 0 4.121-.952 4.125 4.125 0 0 0-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 0 1 8.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0 1 11.964-3.07M12 6.375a3.375 3.375 0 1 1-6.75 0 3.375 3.375 0 0 1 6.75 0Zm8.25 2.25a2.625 2.625 0 1 1-5.25 0 2.625 2.625 0 0 1 5.25 0Z' /%3e%3c/svg%3e");
	}

	.icon-chat {
		mask-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='1.5' stroke='currentColor'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='M8.625 12a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0H8.25m4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0H12m4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 0 1-2.555-.337A5.972 5.972 0 0 1 5.41 20.97a5.969 5.969 0 0 1-.474-.065 4.48 4.48 0 0 0 .978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25Z' /%3e%3c/svg%3e");
	}

	.icon-chart {
		mask-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='1.5' stroke='currentColor'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z' /%3e%3c/svg%3e");
	}

	.icon-settings {
		mask-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='1.5' stroke='currentColor'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.325.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 0 1 1.37.49l1.296 2.247a1.125 1.125 0 0 1-.26 1.431l-1.003.827c-.293.241-.438.613-.43.992a6.759 6.759 0 0 1 0 .255c-.008.378.137.75.43.991l1.004.827c.424.35.534.955.26 1.43l-1.298 2.247a1.125 1.125 0 0 1-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.57 6.57 0 0 1-.22.128c-.331.183-.581.495-.644.869l-.213 1.281c-.09.543-.56.94-1.11.94h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 0 1-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 0 1-1.369-.49l-1.297-2.247a1.125 1.125 0 0 1 .26-1.431l1.004-.827c.292-.24.437-.613.43-.991a6.932 6.932 0 0 1 0-.255c.007-.38-.138-.751-.43-.992l-1.004-.827a1.125 1.125 0 0 1-.26-1.43l1.297-2.247a1.125 1.125 0 0 1 1.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.086.22-.128.332-.183.582-.495.644-.869l.214-1.28Z' /%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z' /%3e%3c/svg%3e");
	}

	.icon-chevron-down {
		mask-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='1.5' stroke='currentColor'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='m19.5 8.25-7.5 7.5-7.5-7.5' /%3e%3c/svg%3e");
	}

	.icon-overview,
	.icon-reports,
	.icon-metrics {
		mask-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='1.5' stroke='currentColor'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='M2.25 18 9 11.25l4.306 4.306a11.95 11.95 0 0 1 5.814-5.518l2.74-1.22m0 0-5.94-2.281m5.94 2.28-2.28 5.941' /%3e%3c/svg%3e");
	}

	@keyframes slideDown {
		from {
			opacity: 0;
			max-height: 0;
		}
		to {
			opacity: 1;
			max-height: 200px;
		}
	}

	/* Scrollbar styling */
	.sidebar-nav::-webkit-scrollbar {
		width: 4px;
	}

	.sidebar-nav::-webkit-scrollbar-track {
		@apply bg-transparent;
	}

	.sidebar-nav::-webkit-scrollbar-thumb {
		@apply bg-gray-300 rounded-full;
	}

	.sidebar-nav::-webkit-scrollbar-thumb:hover {
		@apply bg-gray-400;
	}
</style>