<script lang="ts">
	import {
		// Core UI Components
		Button,
		Input,
		Card,
		StructuredCard,
		Badge,
		Avatar,
		Switch,
		Checkbox,
		// Dashboard Layout
		DashboardLayout,
		Header,
		Sidebar,
		PageHeader,
		GridContainer,
		// Chart and Stats
		StatsCard,
		ChartCard,
		// Navigation
		Breadcrumbs,
		QuickActions,
		NotificationDropdown,
		// Utilities
		Modal,
		Tooltip,
		LoadingSpinner
	} from '$lib/components/ui';

	// Test data and state
	let darkMode = false;
	let sidebarCollapsed = false;
	let showModal = false;
	let inputValue = '';
	let switchValue = false;
	let checkboxValue = false;
	let notifications = [
		{
			id: '1',
			title: 'New message',
			message: 'You have received a new message from John',
			type: 'info' as const,
			timestamp: new Date(),
			read: false
		},
		{
			id: '2',
			title: 'System update',
			message: 'System maintenance completed successfully',
			type: 'success' as const,
			timestamp: new Date(Date.now() - 1000 * 60 * 30),
			read: true
		}
	];

	let quickActions = [
		{
			id: 'new-chat',
			label: 'New Chat',
			icon: 'chat',
			variant: 'primary' as const
		},
		{
			id: 'add-user',
			label: 'Add User',
			icon: 'user-plus',
			variant: 'secondary' as const
		},
		{
			id: 'create-doc',
			label: 'Create Document',
			icon: 'document-plus',
			variant: 'success' as const
		}
	];

	let breadcrumbs = [
		{ label: 'Dashboard', href: '/' },
		{ label: 'Design System', href: '/design-system' },
		{ label: 'Components', active: true }
	];

	let menuItems = [
		{
			id: 'dashboard',
			label: 'Dashboard',
			icon: 'dashboard',
			active: true
		},
		{
			id: 'components',
			label: 'Components',
			icon: 'users',
			badge: { text: '23', variant: 'primary' as const }
		},
		{
			id: 'analytics',
			label: 'Analytics',
			icon: 'chart',
			children: [
				{ id: 'overview', label: 'Overview', icon: 'overview' },
				{ id: 'reports', label: 'Reports', icon: 'reports' }
			]
		}
	];

	// Toggle dark mode
	function toggleDarkMode() {
		darkMode = !darkMode;
		if (darkMode) {
			document.documentElement.classList.add('dark');
		} else {
			document.documentElement.classList.remove('dark');
		}
	}

	// Event handlers
	function handleSidebarToggle() {
		sidebarCollapsed = !sidebarCollapsed;
	}

	function handleModalOpen() {
		showModal = true;
	}

	function handleModalClose() {
		showModal = false;
	}
</script>

<svelte:head>
	<title>Design System Test - Convergio</title>
</svelte:head>

<DashboardLayout bind:sidebarCollapsed>
	<!-- Sidebar -->
	<svelte:fragment slot="sidebar">
		<Sidebar
			{menuItems}
			collapsed={sidebarCollapsed}
			userInfo={{
				name: 'John Doe',
				email: 'john@convergio.com',
				role: 'Admin'
			}}
		/>
	</svelte:fragment>

	<!-- Header -->
	<svelte:fragment slot="header">
		<Header
			title="Design System Test"
			showSearch={true}
			showNotifications={true}
			notificationCount={1}
			userName="John Doe"
			userAvatar=""
			on:toggle-sidebar={handleSidebarToggle}
		/>
	</svelte:fragment>

	<!-- Main Content -->
	<div class="space-y-8">
		<!-- Page Header -->
		<PageHeader
			title="Design System Test"
			subtitle="Testing all UI components and their integration"
			{breadcrumbs}
		>
			<svelte:fragment slot="actions">
				<Button variant="outline" on:click={toggleDarkMode}>
					{darkMode ? 'Light' : 'Dark'} Mode
				</Button>
				<Button variant="primary" on:click={handleModalOpen}>
					Open Modal
				</Button>
			</svelte:fragment>
		</PageHeader>

		<!-- Stats Cards -->
		<div class="mb-8">
			<h2 class="text-lg font-semibold mb-4">Stats Cards</h2>
			<GridContainer cols="auto-fit" gap="md" minItemWidth="280px">
				<StatsCard
					title="Total Users"
					value={1234}
					icon="users"
					iconColor="primary"
					trend={{ value: 1234, percentage: 12.5, direction: 'up', period: 'last month' }}
				/>
				<StatsCard
					title="Active Sessions"
					value={567}
					icon="chart"
					iconColor="success"
					trend={{ value: 567, percentage: 5.2, direction: 'up', period: 'today' }}
				/>
				<StatsCard
					title="Error Rate"
					value="0.02%"
					icon="warning"
					iconColor="warning"
					trend={{ value: 0.02, percentage: 15.3, direction: 'down', period: 'this week' }}
				/>
				<StatsCard
					title="Revenue"
					value="$45.2K"
					icon="currency"
					iconColor="success"
					trend={{ value: 45200, percentage: 8.1, direction: 'up', period: 'this month' }}
				/>
			</GridContainer>
		</div>

		<!-- Core Components -->
		<div class="mb-8">
			<h2 class="text-lg font-semibold mb-4">Core Components</h2>
			<GridContainer cols={2} gap="lg">
				<!-- Buttons -->
				<Card>
					<h3 class="text-md font-medium mb-4">Buttons</h3>
					<div class="space-y-3">
						<div class="flex flex-wrap gap-2">
							<Button variant="primary">Primary</Button>
							<Button variant="secondary">Secondary</Button>
							<Button variant="outline">Outline</Button>
							<Button variant="ghost">Ghost</Button>
						</div>
						<div class="flex flex-wrap gap-2">
							<Button variant="primary" size="sm">Small</Button>
							<Button variant="primary" size="md">Medium</Button>
							<Button variant="primary" size="lg">Large</Button>
						</div>
						<div class="flex flex-wrap gap-2">
							<Button variant="primary" loading>Loading</Button>
							<Button variant="primary" disabled>Disabled</Button>
						</div>
					</div>
				</Card>

				<!-- Form Controls -->
				<Card>
					<h3 class="text-md font-medium mb-4">Form Controls</h3>
					<div class="space-y-4">
						<Input
							label="Email"
							placeholder="Enter your email"
							leadingIcon="email"
							bind:value={inputValue}
						/>
						<Input
							label="Password"
							type="password"
							placeholder="Enter password"
							leadingIcon="lock"
							variant="default"
						/>
						<div class="flex items-center gap-4">
							<Switch bind:checked={switchValue} label="Enable notifications" />
							<Checkbox bind:checked={checkboxValue} label="Remember me" />
						</div>
					</div>
				</Card>
			</GridContainer>
		</div>

		<!-- Badges and Avatars -->
		<div class="mb-8">
			<h2 class="text-lg font-semibold mb-4">Badges and Avatars</h2>
			<Card>
				<div class="space-y-4">
					<div>
						<h3 class="text-sm font-medium mb-2">Badges</h3>
						<div class="flex flex-wrap gap-2">
							<Badge variant="primary">Primary</Badge>
							<Badge variant="success">Success</Badge>
							<Badge variant="warning">Warning</Badge>
							<Badge variant="error">Error</Badge>
							<Badge variant="info">Info</Badge>
							<Badge variant="gray">Gray</Badge>
						</div>
					</div>
					<div>
						<h3 class="text-sm font-medium mb-2">Avatars</h3>
						<div class="flex items-center gap-3">
							<Avatar size="xs" fallback="XS" />
							<Avatar size="sm" fallback="SM" />
							<Avatar size="md" fallback="MD" />
							<Avatar size="lg" fallback="LG" />
							<Avatar size="xl" fallback="XL" />
							<Avatar size="md" fallback="ON" status="online" />
							<Avatar size="md" fallback="OF" status="offline" />
						</div>
					</div>
				</div>
			</Card>
		</div>

		<!-- Chart Card -->
		<div class="mb-8">
			<h2 class="text-lg font-semibold mb-4">Chart Components</h2>
			<ChartCard
				title="User Growth"
				subtitle="Monthly active users over time"
				showControls={true}
				refreshable={true}
				exportable={true}
			>
				<div class="flex items-center justify-center h-64 bg-gray-50 rounded-lg">
					<p class="text-gray-500">Chart visualization would go here</p>
				</div>
				<svelte:fragment slot="legend">
					<div class="flex items-center gap-4">
						<div class="flex items-center gap-2">
							<div class="w-3 h-3 bg-primary-500 rounded-full"></div>
							<span class="text-sm">Active Users</span>
						</div>
						<div class="flex items-center gap-2">
							<div class="w-3 h-3 bg-success-500 rounded-full"></div>
							<span class="text-sm">New Users</span>
						</div>
					</div>
				</svelte:fragment>
			</ChartCard>
		</div>

		<!-- Navigation Components -->
		<div class="mb-8">
			<h2 class="text-lg font-semibold mb-4">Navigation Components</h2>
			<GridContainer cols={2} gap="lg">
				<Card>
					<h3 class="text-md font-medium mb-4">Breadcrumbs</h3>
					<Breadcrumbs items={breadcrumbs} />
				</Card>

				<Card>
					<h3 class="text-md font-medium mb-4">Notifications</h3>
					<div class="flex items-center gap-4">
						<NotificationDropdown {notifications} />
						<span class="text-sm text-gray-600">Click the bell icon</span>
					</div>
				</Card>
			</GridContainer>
		</div>

		<!-- Utility Components -->
		<div class="mb-8">
			<h2 class="text-lg font-semibold mb-4">Utility Components</h2>
			<GridContainer cols={2} gap="lg">
				<Card>
					<h3 class="text-md font-medium mb-4">Loading Spinners</h3>
					<div class="space-y-4">
						<div class="flex items-center gap-4">
							<LoadingSpinner size="sm" />
							<LoadingSpinner size="md" />
							<LoadingSpinner size="lg" variant="primary" />
						</div>
						<div class="flex items-center gap-4">
							<LoadingSpinner variant="dots" />
							<LoadingSpinner variant="pulse" />
							<LoadingSpinner variant="bars" />
						</div>
					</div>
				</Card>

				<Card>
					<h3 class="text-md font-medium mb-4">Tooltips</h3>
					<div class="space-y-4">
						<div class="flex items-center gap-4">
							<Tooltip content="This is a tooltip">
								<Button variant="outline">Hover me</Button>
							</Tooltip>
							<Tooltip content="Click tooltip" trigger="click">
								<Button variant="outline">Click me</Button>
							</Tooltip>
						</div>
						<div class="flex items-center gap-4">
							<Tooltip content="Error tooltip" variant="error">
								<Badge variant="error">Error</Badge>
							</Tooltip>
							<Tooltip content="Success tooltip" variant="success">
								<Badge variant="success">Success</Badge>
							</Tooltip>
						</div>
					</div>
				</Card>
			</GridContainer>
		</div>

		<!-- Structured Card Example -->
		<div class="mb-8">
			<h2 class="text-lg font-semibold mb-4">Structured Cards</h2>
			<StructuredCard>
				<svelte:fragment slot="header">
					<div class="flex items-center justify-between">
						<h3 class="text-lg font-medium">User Profile</h3>
						<Badge variant="success">Active</Badge>
					</div>
				</svelte:fragment>

				<svelte:fragment slot="content">
					<div class="flex items-start gap-4">
						<Avatar size="lg" fallback="JD" status="online" />
						<div class="space-y-2">
							<h4 class="font-medium">John Doe</h4>
							<p class="text-sm text-gray-600">john@convergio.com</p>
							<p class="text-sm text-gray-500">Administrator</p>
						</div>
					</div>
				</svelte:fragment>

				<svelte:fragment slot="footer">
					<div class="flex items-center justify-between">
						<span class="text-sm text-gray-500">Last seen: 2 minutes ago</span>
						<div class="flex gap-2">
							<Button size="sm" variant="outline">Message</Button>
							<Button size="sm" variant="primary">Edit</Button>
						</div>
					</div>
				</svelte:fragment>
			</StructuredCard>
		</div>
	</div>

	<!-- Quick Actions -->
	<QuickActions
		actions={quickActions}
		position="bottom-right"
		trigger="hover"
	/>

	<!-- Modal -->
	<Modal
		bind:open={showModal}
		title="Test Modal"
		description="This is a test modal to verify modal functionality"
		showFooter={true}
		on:close={handleModalClose}
		on:cancel={handleModalClose}
		on:confirm={handleModalClose}
	>
		<div class="space-y-4">
			<p>This modal demonstrates the modal component integration with the design system.</p>
			<Input
				label="Test Input"
				placeholder="Type something..."
			/>
			<div class="flex items-center gap-4">
				<Switch label="Enable feature" />
				<Checkbox label="I agree to terms" />
			</div>
		</div>
	</Modal>
</DashboardLayout>

<style>
	:global(html) {
		font-family: var(--font-primary);
	}
</style>