<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { Button, Input, Avatar, Badge } from './index';

	interface $$Props {
		title?: string;
		showSearch?: boolean;
		showNotifications?: boolean;
		notificationCount?: number;
		userAvatar?: string;
		userName?: string;
		showMobileMenuButton?: boolean;
		sidebarCollapsed?: boolean;
	}

	export let title: $$Props['title'] = '';
	export let showSearch: $$Props['showSearch'] = true;
	export let showNotifications: $$Props['showNotifications'] = true;
	export let notificationCount: $$Props['notificationCount'] = 0;
	export let userAvatar: $$Props['userAvatar'] = '';
	export let userName: $$Props['userName'] = 'User';
	export let showMobileMenuButton: $$Props['showMobileMenuButton'] = true;
	export let sidebarCollapsed: $$Props['sidebarCollapsed'] = false;

	const dispatch = createEventDispatcher<{
		'toggle-sidebar': void;
		'search': { query: string };
		'notifications-click': void;
		'user-menu-click': void;
	}>();

	let searchQuery = '';
	let showUserMenu = false;

	function handleSearch() {
		dispatch('search', { query: searchQuery });
	}

	function handleNotifications() {
		dispatch('notifications-click');
	}

	function toggleUserMenu() {
		showUserMenu = !showUserMenu;
	}

	function handleUserMenuClick() {
		dispatch('user-menu-click');
	}

	function toggleSidebar() {
		dispatch('toggle-sidebar');
	}
</script>

<div class="header-container">
	<div class="header-left">
		<!-- Mobile menu button -->
		{#if showMobileMenuButton}
			<Button
				variant="ghost"
				size="icon"
				class="lg:hidden"
				on:click={toggleSidebar}
				aria-label="Toggle sidebar"
			>
				<span class="icon-menu" aria-hidden="true"></span>
			</Button>
		{/if}

		<!-- Desktop sidebar toggle -->
		<Button
			variant="ghost"
			size="icon"
			class="hidden lg:flex"
			on:click={toggleSidebar}
			aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
		>
			<span class="icon-{sidebarCollapsed ? 'expand' : 'collapse'}" aria-hidden="true"></span>
		</Button>

		<!-- Title -->
		{#if title}
			<h1 class="header-title">
				{title}
			</h1>
		{/if}
	</div>

	<div class="header-center">
		<!-- Search -->
		{#if showSearch}
			<div class="search-container">
				<Input
					type="search"
					placeholder="Search..."
					leadingIcon="search"
					clearable
					bind:value={searchQuery}
					on:input={handleSearch}
					on:clear={() => searchQuery = ''}
					class="header-search"
				/>
			</div>
		{/if}
	</div>

	<div class="header-right">
		<!-- Notifications -->
		{#if showNotifications}
			<div class="relative">
				<Button
					variant="ghost"
					size="icon"
					on:click={handleNotifications}
					aria-label="Notifications"
				>
					<span class="icon-bell" aria-hidden="true"></span>
					{#if (notificationCount ?? 0) > 0}
						<Badge
							variant="error"
							size="sm"
							class="notification-badge"
						>
							{(notificationCount ?? 0) > 99 ? '99+' : (notificationCount ?? 0)}
						</Badge>
					{/if}
				</Button>
			</div>
		{/if}

		<!-- User menu -->
		<div class="relative user-menu-container">
			<button
				type="button"
				class="user-menu-trigger"
				on:click={toggleUserMenu}
				aria-expanded={showUserMenu}
				aria-haspopup="true"
				aria-label="User menu"
			>
				<Avatar
					src={userAvatar}
					fallback={userName}
					size="sm"
					class="cursor-pointer hover:ring-2 hover:ring-primary-500 transition-all duration-200"
				/>
				<span class="icon-chevron-down user-menu-arrow" aria-hidden="true"></span>
			</button>

			<!-- User dropdown menu -->
			{#if showUserMenu}
				<div class="user-menu-dropdown" role="menu">
					<div class="user-info" role="none">
						<Avatar src={userAvatar} fallback={userName} size="md" />
						<div class="user-details">
							<span class="user-name">{userName}</span>
							<span class="user-email">user@example.com</span>
						</div>
					</div>

					<div class="menu-divider" role="none"></div>

					<button type="button" class="menu-item" role="menuitem" on:click={handleUserMenuClick}>
						<span class="icon-user" aria-hidden="true"></span>
						Profile
					</button>

					<button type="button" class="menu-item" role="menuitem">
						<span class="icon-settings" aria-hidden="true"></span>
						Settings
					</button>

					<button type="button" class="menu-item" role="menuitem">
						<span class="icon-help" aria-hidden="true"></span>
						Help & Support
					</button>

					<div class="menu-divider" role="none"></div>

					<button type="button" class="menu-item text-error-600" role="menuitem">
						<span class="icon-logout" aria-hidden="true"></span>
						Sign Out
					</button>
				</div>
			{/if}
		</div>
	</div>
</div>

<!-- Click outside to close user menu -->
{#if showUserMenu}
	<div
		class="fixed inset-0 z-10"
		on:click={() => showUserMenu = false}
		on:keydown={(e) => e.key === 'Escape' && (showUserMenu = false)}
		role="button"
		tabindex="-1"
		aria-label="Close menu"
	></div>
{/if}

<style>
	.header-container {
		@apply flex items-center justify-between w-full gap-4;
	}

	.header-left {
		@apply flex items-center gap-3;
	}

	.header-center {
		@apply flex-1 max-w-2xl mx-8;
	}

	.header-right {
		@apply flex items-center gap-3;
	}

	.header-title {
		@apply text-xl font-semibold text-gray-900 truncate;
		font-family: var(--font-primary);
	}

	:global(.dark) .header-title {
		@apply text-gray-100;
	}

	.search-container {
		@apply w-full;
	}

	:global(.header-search) {
		@apply w-full;
	}

	:global(.notification-badge) {
		@apply absolute -top-1 -right-1 min-w-[1.25rem] h-5 flex items-center justify-center;
	}

	.user-menu-container {
		@apply relative;
	}

	.user-menu-trigger {
		@apply flex items-center gap-2 p-1 rounded-lg hover:bg-gray-100 transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2;
	}

	:global(.dark) .user-menu-trigger {
		@apply hover:bg-gray-800;
	}

	:global(.dark) .user-menu-trigger:focus {
		@apply ring-offset-gray-800;
	}

	.user-menu-arrow {
		@apply w-4 h-4 text-gray-500 transition-transform duration-200;
	}

	.user-menu-trigger[aria-expanded="true"] .user-menu-arrow {
		@apply rotate-180;
	}

	.user-menu-dropdown {
		@apply absolute right-0 top-full mt-2 w-64 bg-white border border-gray-200 rounded-xl shadow-lg z-50 py-2;
		box-shadow: var(--shadow-xl);
		animation: fadeInDown 0.2s ease-out;
	}

	:global(.dark) .user-menu-dropdown {
		@apply bg-gray-800 border-gray-700;
	}

	.user-info {
		@apply flex items-center gap-3 px-4 py-3;
	}

	.user-details {
		@apply flex flex-col;
	}

	.user-name {
		@apply text-sm font-medium text-gray-900;
		font-family: var(--font-primary);
	}

	:global(.dark) .user-name {
		@apply text-gray-100;
	}

	.user-email {
		@apply text-xs text-gray-500;
		font-family: var(--font-primary);
	}

	:global(.dark) .user-email {
		@apply text-gray-400;
	}

	.menu-divider {
		@apply border-t border-gray-200 my-1;
	}

	.menu-item {
		@apply w-full flex items-center gap-3 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition-colors duration-200 focus:outline-none focus:bg-gray-100;
		font-family: var(--font-primary);
	}

	:global(.dark) .menu-item {
		@apply text-gray-300 hover:bg-gray-700 focus:bg-gray-700;
	}

	:global(.dark) .menu-divider {
		@apply border-gray-700;
	}

	/* Icon styles */
	[class^="icon-"] {
		display: inline-block;
		width: 1rem;
		height: 1rem;
		background-color: currentColor;
		mask-size: contain;
		mask-repeat: no-repeat;
		mask-position: center;
	}

	.icon-menu {
		mask-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='1.5' stroke='currentColor'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5' /%3e%3c/svg%3e");
	}

	.icon-expand {
		mask-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='1.5' stroke='currentColor'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='M3.75 6A2.25 2.25 0 0 1 6 3.75h2.25A2.25 2.25 0 0 1 10.5 6v2.25a2.25 2.25 0 0 1-2.25 2.25H6a2.25 2.25 0 0 1-2.25-2.25V6ZM13.5 6a2.25 2.25 0 0 1 2.25-2.25H18A2.25 2.25 0 0 1 20.25 6v2.25A2.25 2.25 0 0 1 18 10.5h-2.25a2.25 2.25 0 0 1-2.25-2.25V6ZM3.75 15.75A2.25 2.25 0 0 1 6 13.5h2.25a2.25 2.25 0 0 1 2.25 2.25V18a2.25 2.25 0 0 1-2.25 2.25H6A2.25 2.25 0 0 1 3.75 18v-2.25ZM13.5 15.75a2.25 2.25 0 0 1 2.25-2.25H18a2.25 2.25 0 0 1 2.25 2.25V18A2.25 2.25 0 0 1 18 20.25h-2.25A2.25 2.25 0 0 1 13.5 18v-2.25Z' /%3e%3c/svg%3e");
	}

	.icon-collapse {
		mask-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='1.5' stroke='currentColor'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='M3.75 6A2.25 2.25 0 0 1 6 3.75h2.25A2.25 2.25 0 0 1 10.5 6v2.25a2.25 2.25 0 0 1-2.25 2.25H6a2.25 2.25 0 0 1-2.25-2.25V6ZM13.5 6a2.25 2.25 0 0 1 2.25-2.25H18A2.25 2.25 0 0 1 20.25 6v2.25A2.25 2.25 0 0 1 18 10.5h-2.25a2.25 2.25 0 0 1-2.25-2.25V6ZM3.75 15.75A2.25 2.25 0 0 1 6 13.5h2.25a2.25 2.25 0 0 1 2.25 2.25V18a2.25 2.25 0 0 1-2.25 2.25H6A2.25 2.25 0 0 1 3.75 18v-2.25ZM13.5 15.75a2.25 2.25 0 0 1 2.25-2.25H18a2.25 2.25 0 0 1 2.25 2.25V18A2.25 2.25 0 0 1 18 20.25h-2.25A2.25 2.25 0 0 1 13.5 18v-2.25Z' /%3e%3c/svg%3e");
	}

	.icon-bell {
		mask-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='1.5' stroke='currentColor'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='M14.857 17.082a23.848 23.848 0 0 0 5.454-1.31A8.967 8.967 0 0 1 18 9.75V9A6 6 0 0 0 6 9v.75a8.967 8.967 0 0 1-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 0 1-5.714 0m5.714 0a3 3 0 1 1-5.714 0' /%3e%3c/svg%3e");
	}

	.icon-chevron-down {
		mask-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='1.5' stroke='currentColor'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='m19.5 8.25-7.5 7.5-7.5-7.5' /%3e%3c/svg%3e");
	}

	.icon-user {
		mask-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='1.5' stroke='currentColor'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.501 20.118a7.5 7.5 0 0 1 14.998 0A17.933 17.933 0 0 1 12 21.75c-2.676 0-5.216-.584-7.499-1.632Z' /%3e%3c/svg%3e");
	}

	.icon-settings {
		mask-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='1.5' stroke='currentColor'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.325.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 0 1 1.37.49l1.296 2.247a1.125 1.125 0 0 1-.26 1.431l-1.003.827c-.293.241-.438.613-.43.992a6.759 6.759 0 0 1 0 .255c-.008.378.137.75.43.991l1.004.827c.424.35.534.955.26 1.43l-1.298 2.247a1.125 1.125 0 0 1-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.57 6.57 0 0 1-.22.128c-.331.183-.581.495-.644.869l-.213 1.281c-.09.543-.56.94-1.11.94h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 0 1-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 0 1-1.369-.49l-1.297-2.247a1.125 1.125 0 0 1 .26-1.431l1.004-.827c.292-.24.437-.613.43-.991a6.932 6.932 0 0 1 0-.255c.007-.38-.138-.751-.43-.992l-1.004-.827a1.125 1.125 0 0 1-.26-1.43l1.297-2.247a1.125 1.125 0 0 1 1.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.086.22-.128.332-.183.582-.495.644-.869l.214-1.28Z' /%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z' /%3e%3c/svg%3e");
	}

	.icon-help {
		mask-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='1.5' stroke='currentColor'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='M9.879 7.519c.89-1.789 3.252-1.789 4.142 0c.645 1.295.383 2.878-.766 3.818-.5.409-.5 1.17 0 1.579c1.149.94 1.411 2.523.766 3.818-.89 1.789-3.252 1.789-4.142 0' /%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='M12 17.25h.007v.008H12v-.008Z' /%3e%3c/svg%3e");
	}

	.icon-logout {
		mask-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='1.5' stroke='currentColor'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='M15.75 9V5.25A2.25 2.25 0 0 0 13.5 3h-6a2.25 2.25 0 0 0-2.25 2.25v13.5A2.25 2.25 0 0 0 7.5 21h6a2.25 2.25 0 0 0 2.25-2.25V15M12 9l-3 3m0 0 3 3m-3-3h12.75' /%3e%3c/svg%3e");
	}

	@keyframes fadeInDown {
		from {
			opacity: 0;
			transform: translateY(-10px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}
</style>