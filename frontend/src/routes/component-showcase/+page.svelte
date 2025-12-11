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

	// Component showcase data
	let showModal = false;
	let inputValue = '';
	let switchValue = false;
	let checkboxValue = false;

	let breadcrumbs = [
		{ label: 'Documentation', href: '/docs' },
		{ label: 'Components', href: '/docs/components' },
		{ label: 'Showcase', active: true }
	];

	let notifications = [
		{
			id: '1',
			title: 'Welcome to Convergio',
			message: 'Your account has been successfully created',
			type: 'success' as const,
			timestamp: new Date(),
			read: false
		},
		{
			id: '2',
			title: 'System Maintenance',
			message: 'Scheduled maintenance will begin at 2:00 AM UTC',
			type: 'info' as const,
			timestamp: new Date(Date.now() - 1000 * 60 * 30),
			read: true
		}
	];

	let quickActions = [
		{
			id: 'new-project',
			label: 'New Project',
			icon: 'plus',
			variant: 'primary' as const
		},
		{
			id: 'new-user',
			label: 'Add User',
			icon: 'user-plus',
			variant: 'secondary' as const
		}
	];
</script>

<svelte:head>
	<title>Component Showcase - Convergio Design System</title>
</svelte:head>

<div class="component-showcase">
	<!-- Page Header -->
	<PageHeader
		title="Component Showcase"
		subtitle="Interactive examples of all design system components"
		{breadcrumbs}
	>
		<svelte:fragment slot="actions">
			<Button variant="outline" on:click={() => window.location.href = '/design-system-test'}>
				View Test Page
			</Button>
			<Button variant="primary">
				Get Started
			</Button>
		</svelte:fragment>
	</PageHeader>

	<!-- Component Sections -->
	<div class="showcase-content space-y-12">
		
		<!-- Core UI Components -->
		<section class="component-section">
			<h2 class="section-title">Core UI Components</h2>
			
			<!-- Buttons -->
			<div class="component-demo">
				<h3 class="demo-title">Buttons</h3>
				<div class="demo-content">
					<div class="component-grid">
						<div class="demo-group">
							<h4 class="demo-subtitle">Variants</h4>
							<div class="flex flex-wrap gap-3">
								<Button variant="primary">Primary</Button>
								<Button variant="secondary">Secondary</Button>
								<Button variant="outline">Outline</Button>
								<Button variant="ghost">Ghost</Button>
							</div>
						</div>
						
						<div class="demo-group">
							<h4 class="demo-subtitle">Sizes</h4>
							<div class="flex flex-wrap items-center gap-3">
								<Button size="sm">Small</Button>
								<Button size="md">Medium</Button>
								<Button size="lg">Large</Button>
								<Button size="icon" variant="outline">
									<span class="icon-heart" aria-hidden="true"></span>
								</Button>
							</div>
						</div>
						
						<div class="demo-group">
							<h4 class="demo-subtitle">States</h4>
							<div class="flex flex-wrap gap-3">
								<Button disabled>Disabled</Button>
								<Button loading>Loading</Button>
								<Button variant="primary" loading>Saving</Button>
							</div>
						</div>
					</div>
				</div>
			</div>

			<!-- Inputs -->
			<div class="component-demo">
				<h3 class="demo-title">Inputs</h3>
				<div class="demo-content">
					<div class="component-grid">
						<div class="demo-group">
							<h4 class="demo-subtitle">Basic Inputs</h4>
							<div class="space-y-4 max-w-md">
								<Input placeholder="Basic input" bind:value={inputValue} />
								<Input leadingIcon="search" placeholder="With leading icon" />
								<Input trailingIcon="eye" placeholder="With trailing icon" />
								<Input leadingIcon="mail" clearable placeholder="Clearable input" />
							</div>
						</div>
						
						<div class="demo-group">
							<h4 class="demo-subtitle">States</h4>
							<div class="space-y-4 max-w-md">
								<Input placeholder="Default state" />
								<Input variant="error" placeholder="Error state" helperText="This field is required" />
								<Input variant="success" placeholder="Success state" helperText="Looks good!" />
								<Input disabled placeholder="Disabled state" />
							</div>
						</div>
						
						<div class="demo-group">
							<h4 class="demo-subtitle">Sizes</h4>
							<div class="space-y-4 max-w-md">
								<Input size="sm" placeholder="Small input" />
								<Input size="md" placeholder="Medium input" />
								<Input size="lg" placeholder="Large input" />
							</div>
						</div>
					</div>
				</div>
			</div>

			<!-- Cards -->
			<div class="component-demo">
				<h3 class="demo-title">Cards</h3>
				<div class="demo-content">
					<div class="grid grid-cols-1 md:grid-cols-3 gap-6">
						<Card variant="default">
							<h4 class="font-semibold mb-2">Default Card</h4>
							<p class="text-sm text-gray-600">
								This is a default card with basic styling and subtle shadow.
							</p>
						</Card>
						
						<Card variant="elevated">
							<h4 class="font-semibold mb-2">Elevated Card</h4>
							<p class="text-sm text-gray-600">
								This card has enhanced shadow for more prominence.
							</p>
						</Card>
						
						<StructuredCard>
							<svelte:fragment slot="header">
								<h4 class="font-semibold">Structured Card</h4>
							</svelte:fragment>
							<p class="text-sm text-gray-600">
								Cards can have structured headers and footers.
							</p>
							<svelte:fragment slot="footer">
								<Button size="sm" variant="outline">Action</Button>
							</svelte:fragment>
						</StructuredCard>
					</div>
				</div>
			</div>

			<!-- Badges and Avatars -->
			<div class="component-demo">
				<h3 class="demo-title">Badges & Avatars</h3>
				<div class="demo-content">
					<div class="component-grid">
						<div class="demo-group">
							<h4 class="demo-subtitle">Badges</h4>
							<div class="flex flex-wrap gap-3">
								<Badge variant="primary">Primary</Badge>
								<Badge variant="gray">Default</Badge>
								<Badge variant="success">Success</Badge>
								<Badge variant="warning">Warning</Badge>
								<Badge variant="error">Error</Badge>
								<Badge variant="info">Info</Badge>
							</div>
						</div>
						
						<div class="demo-group">
							<h4 class="demo-subtitle">Avatars</h4>
							<div class="flex flex-wrap items-center gap-4">
								<Avatar fallback="JD" size="xs" />
								<Avatar fallback="AB" size="sm" />
								<Avatar fallback="CD" size="md" />
								<Avatar fallback="EF" size="lg" />
								<Avatar fallback="GH" size="xl" />
							</div>
						</div>
					</div>
				</div>
			</div>

			<!-- Form Controls -->
			<div class="component-demo">
				<h3 class="demo-title">Form Controls</h3>
				<div class="demo-content">
					<div class="component-grid">
						<div class="demo-group">
							<h4 class="demo-subtitle">Switch</h4>
							<Switch bind:checked={switchValue} label="Enable notifications" />
						</div>
						
						<div class="demo-group">
							<h4 class="demo-subtitle">Checkbox</h4>
							<Checkbox 
								bind:checked={checkboxValue} 
								label="I agree to the terms" 
								description="Please read our terms and conditions"
							/>
						</div>
					</div>
				</div>
			</div>
		</section>

		<!-- Chart and Stats Components -->
		<section class="component-section">
			<h2 class="section-title">Chart & Stats Components</h2>
			
			<div class="component-demo">
				<h3 class="demo-title">Stats Cards</h3>
				<div class="demo-content">
					<GridContainer cols="auto-fit" gap="md" minItemWidth="280px">
						<StatsCard
							title="Total Users"
							value={15420}
							icon="users"
							iconColor="primary"
							trend={{ value: 15420, percentage: 12.5, direction: 'up', period: 'last month' }}
						/>
						<StatsCard
							title="Revenue"
							value="$45.2K"
							icon="currency"
							iconColor="success"
							trend={{ value: 45200, percentage: 8.1, direction: 'up', period: 'this quarter' }}
							variant="compact"
						/>
						<StatsCard
							title="Conversion Rate"
							value="3.2%"
							icon="chart"
							iconColor="warning"
							trend={{ value: 3.2, percentage: 2.4, direction: 'down', period: 'last week' }}
						/>
					</GridContainer>
				</div>
			</div>

			<div class="component-demo">
				<h3 class="demo-title">Chart Card</h3>
				<div class="demo-content">
					<ChartCard
						title="Revenue Overview"
						subtitle="Monthly revenue trends for the past 6 months"
					>
						<svelte:fragment slot="default">
							<div class="h-64 bg-gray-100 rounded-lg flex items-center justify-center">
								<p class="text-gray-500">Chart component placeholder</p>
							</div>
						</svelte:fragment>
						<svelte:fragment slot="legend">
							<div class="flex items-center gap-4">
								<div class="flex items-center gap-2">
									<div class="w-3 h-3 bg-primary-500 rounded"></div>
									<span class="text-sm">Current Period</span>
								</div>
								<div class="flex items-center gap-2">
									<div class="w-3 h-3 bg-gray-400 rounded"></div>
									<span class="text-sm">Previous Period</span>
								</div>
							</div>
						</svelte:fragment>
					</ChartCard>
				</div>
			</div>
		</section>

		<!-- Navigation Components -->
		<section class="component-section">
			<h2 class="section-title">Navigation Components</h2>
			
			<div class="component-demo">
				<h3 class="demo-title">Breadcrumbs</h3>
				<div class="demo-content">
					<Breadcrumbs items={breadcrumbs} />
				</div>
			</div>

			<div class="component-demo">
				<h3 class="demo-title">Notification Dropdown</h3>
				<div class="demo-content">
					<div class="flex justify-center">
						<NotificationDropdown {notifications} />
					</div>
				</div>
			</div>
		</section>

		<!-- Utility Components -->
		<section class="component-section">
			<h2 class="section-title">Utility Components</h2>
			
			<div class="component-demo">
				<h3 class="demo-title">Loading Spinners</h3>
				<div class="demo-content">
					<div class="component-grid">
						<div class="demo-group">
							<h4 class="demo-subtitle">Variants</h4>
							<div class="flex flex-wrap items-center gap-6">
								<LoadingSpinner variant="default" size="md" />
								<LoadingSpinner variant="dots" size="md" />
								<LoadingSpinner variant="pulse" size="md" />
								<LoadingSpinner variant="bars" size="md" />
							</div>
						</div>
						
						<div class="demo-group">
							<h4 class="demo-subtitle">With Text</h4>
							<LoadingSpinner variant="default" size="lg" text="Loading content..." />
						</div>
					</div>
				</div>
			</div>

			<div class="component-demo">
				<h3 class="demo-title">Tooltips</h3>
				<div class="demo-content">
					<div class="flex justify-center gap-8">
						<Tooltip content="This is a helpful tooltip" placement="top">
							<Button variant="outline">Hover me (Top)</Button>
						</Tooltip>
						<Tooltip content="Bottom tooltip" placement="bottom">
							<Button variant="outline">Hover me (Bottom)</Button>
						</Tooltip>
						<Tooltip content="Left tooltip" placement="left">
							<Button variant="outline">Hover me (Left)</Button>
						</Tooltip>
						<Tooltip content="Right tooltip" placement="right">
							<Button variant="outline">Hover me (Right)</Button>
						</Tooltip>
					</div>
				</div>
			</div>

			<div class="component-demo">
				<h3 class="demo-title">Modal</h3>
				<div class="demo-content">
					<div class="flex justify-center">
						<Button variant="primary" on:click={() => showModal = true}>
							Open Modal
						</Button>
					</div>
				</div>
			</div>
		</section>
	</div>

	<!-- Quick Actions (positioned fixed) -->
	<QuickActions actions={quickActions} position="bottom-right" size="md" />

	<!-- Modal Example -->
	<Modal
		bind:open={showModal}
		title="Example Modal"
		size="md"
	>
		<p class="mb-4">
			This is an example modal showcasing the modal component with proper focus management,
			backdrop click handling, and keyboard navigation.
		</p>
		<p class="text-sm text-gray-600">
			You can press Escape to close this modal or click the backdrop.
		</p>
		
		<svelte:fragment slot="footer">
			<Button variant="outline" on:click={() => showModal = false}>
				Cancel
			</Button>
			<Button variant="primary" on:click={() => showModal = false}>
				Confirm
			</Button>
		</svelte:fragment>
	</Modal>
</div>

<style>
	.component-showcase {
		@apply max-w-7xl mx-auto px-6 py-8;
	}

	.showcase-content {
		@apply mt-8;
	}

	.component-section {
		@apply space-y-8;
	}

	.section-title {
		@apply text-2xl font-bold text-gray-900 mb-6;
		font-family: var(--font-primary);
	}

	.component-demo {
		@apply bg-white border border-gray-200 rounded-xl p-6;
	}

	.demo-title {
		@apply text-lg font-semibold text-gray-900 mb-4;
		font-family: var(--font-primary);
	}

	.demo-subtitle {
		@apply text-sm font-medium text-gray-700 mb-3;
		font-family: var(--font-primary);
	}

	.demo-content {
		@apply space-y-6;
	}

	.component-grid {
		@apply grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6;
	}

	.demo-group {
		@apply space-y-3;
	}

	/* Icon placeholder styles */
	.icon-heart {
		display: inline-block;
		width: 1rem;
		height: 1rem;
		background-color: currentColor;
		mask-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='1.5' stroke='currentColor'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12Z' /%3e%3c/svg%3e");
		mask-size: contain;
		mask-repeat: no-repeat;
		mask-position: center;
	}
</style>