<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { pmRealtimeService, type PMRealtimeEvent } from '$lib/services/pmRealtimeService';

	// Props
	export let projectId: string;
	export let compact: boolean = false;

	// State
	let activityFeed: PMRealtimeEvent[] = [];
	let connectionStatus: string = 'disconnected';
	let showAll = false;
	let unsubscribes: (() => void)[] = [];

	onMount(async () => {
		// Subscribe to real-time updates
		const unsubscribeActivity = pmRealtimeService.activityFeed.subscribe(feed => {
			activityFeed = feed;
		});

		const unsubscribeStatus = pmRealtimeService.connectionStatus.subscribe(status => {
			connectionStatus = status;
		});

		unsubscribes = [unsubscribeActivity, unsubscribeStatus];

		// Connect and subscribe to project
		try {
			await pmRealtimeService.connect();
			if (projectId) {
				await pmRealtimeService.subscribeToProject(projectId);
			}
		} catch (error) {
			console.error('Failed to connect to real-time service:', error);
		}
	});

	onDestroy(async () => {
		// Clean up subscriptions
		unsubscribes.forEach(unsubscribe => unsubscribe());
		
		// Unsubscribe from project
		try {
			await pmRealtimeService.unsubscribeFromProject();
		} catch (error) {
			console.error('Failed to unsubscribe from project:', error);
		}
	});

	function getEventIcon(event: PMRealtimeEvent): string {
		switch (event.type) {
			case 'project_created': return '🎯';
			case 'project_updated': return '📝';
			case 'project_deleted': return '🗑️';
			case 'task_created': return '➕';
			case 'task_updated': return '✏️';
			case 'task_deleted': return '❌';
			case 'task_moved': return '🔄';
			case 'resource_allocated': return '👤';
			case 'resource_freed': return '🆓';
			case 'utilization_changed': return '📊';
			case 'ali_insight': return '🤖';
			case 'ali_recommendation': return '💡';
			case 'ali_alert': return '⚠️';
			default: return '📋';
		}
	}

	function getEventColor(event: PMRealtimeEvent): string {
		switch (event.type) {
			case 'project_created':
			case 'task_created':
				return 'text-success-600 bg-success-50 border-success-200';
			case 'project_updated':
			case 'task_updated':
			case 'task_moved':
				return 'text-info-600 bg-info-50 border-info-200';
			case 'project_deleted':
			case 'task_deleted':
				return 'text-error-600 bg-error-50 border-error-200';
			case 'resource_allocated':
			case 'resource_freed':
			case 'utilization_changed':
				return 'text-purple-600 bg-purple-50 border-purple-200';
			case 'ali_insight':
			case 'ali_recommendation':
				return 'text-primary-600 bg-primary-50 border-primary-200';
			case 'ali_alert':
				return 'text-warning-600 bg-warning-50 border-warning-200';
			default:
				return 'text-surface-600 bg-surface-50 border-surface-200';
		}
	}

	function formatEventMessage(event: PMRealtimeEvent): string {
		switch (event.type) {
			case 'project_created':
				return `New project created: ${event.data?.name || 'Unnamed Project'}`;
			case 'project_updated':
				return `Project updated: ${event.data?.name || 'Project'}`;
			case 'project_deleted':
				return `Project deleted: ${event.data?.name || 'Project'}`;
			case 'task_created':
				return `New task created: ${event.data?.title || 'Unnamed Task'}`;
			case 'task_updated':
				return `Task updated: ${event.data?.title || 'Task'}`;
			case 'task_deleted':
				return `Task deleted: ${event.data?.title || 'Task'}`;
			case 'task_moved':
				return `Task moved: ${event.data?.title || 'Task'} → ${event.data?.newStatus || 'New Status'}`;
			case 'resource_allocated':
				return `Resource allocated: ${event.data?.resourceName || 'Resource'} to ${event.data?.taskName || 'Task'}`;
			case 'resource_freed':
				return `Resource freed: ${event.data?.resourceName || 'Resource'}`;
			case 'utilization_changed':
				return `Resource utilization changed: ${event.data?.resourceName || 'Resource'} (${event.data?.utilization || 0}%)`;
			case 'ali_insight':
				return `Ali insight: ${event.message || 'New insight available'}`;
			case 'ali_recommendation':
				return `Ali recommends: ${event.message || 'New recommendation available'}`;
			case 'ali_alert':
				return `Ali alert: ${event.message || 'Alert from Ali'}`;
			default:
				return 'Project activity update';
		}
	}

	function getTimeAgo(timestamp: string): string {
		const now = new Date();
		const time = new Date(timestamp);
		const diffInSeconds = Math.floor((now.getTime() - time.getTime()) / 1000);

		if (diffInSeconds < 60) {
			return 'just now';
		} else if (diffInSeconds < 3600) {
			const minutes = Math.floor(diffInSeconds / 60);
			return `${minutes}m ago`;
		} else if (diffInSeconds < 86400) {
			const hours = Math.floor(diffInSeconds / 3600);
			return `${hours}h ago`;
		} else {
			const days = Math.floor(diffInSeconds / 86400);
			return `${days}d ago`;
		}
	}

	$: displayedEvents = compact ? activityFeed.slice(0, 5) : showAll ? activityFeed : activityFeed.slice(0, 10);
</script>

<div class="activity-feed bg-white rounded-xl shadow-sm border border-surface-200  overflow-hidden">
	<!-- Header -->
	<div class="p-4 border-b border-surface-200  bg-surface-50 ">
		<div class="flex items-center justify-between">
			<div class="flex items-center space-x-3">
				<h3 class="font-semibold text-surface-900 ">
					{compact ? 'Recent Activity' : 'Real-time Activity Feed'}
				</h3>
				<!-- Connection Status -->
				<div class="flex items-center space-x-2">
					<div class="w-2 h-2 {connectionStatus === 'connected' ? 'bg-success-500' : connectionStatus === 'connecting' ? 'bg-warning-500' : 'bg-error-500'} rounded-full {connectionStatus === 'connecting' ? 'animate-pulse' : ''}"></div>
					<span class="text-xs text-surface-500 ">
						{connectionStatus === 'connected' ? 'Live' : 
						 connectionStatus === 'connecting' ? 'Connecting...' : 
						 connectionStatus === 'error' ? 'Error' : 'Offline'}
					</span>
				</div>
			</div>
			{#if !compact}
				<div class="flex items-center space-x-2">
					<button 
						on:click={() => pmRealtimeService.clearHistory()}
						class="btn-secondary btn-sm"
					>
						Clear
					</button>
					{#if activityFeed.length > 10}
						<button 
							on:click={() => showAll = !showAll}
							class="btn-secondary btn-sm"
						>
							{showAll ? 'Show Less' : `Show All (${activityFeed.length})`}
						</button>
					{/if}
				</div>
			{/if}
		</div>
	</div>

	<!-- Activity List -->
	<div class="max-h-{compact ? '64' : '96'} overflow-y-auto">
		{#if displayedEvents.length === 0}
			<div class="p-8 text-center">
				<div class="text-4xl mb-2">📡</div>
				<div class="text-surface-500 ">
					{connectionStatus === 'connected' ? 'No activity yet' : 'Connecting to real-time updates...'}
				</div>
			</div>
		{:else}
			<div class="divide-y divide-surface-100">
				{#each displayedEvents as event}
					<div class="p-4 hover:bg-surface-50 transition-colors duration-200">
						<div class="flex items-start space-x-3">
							<!-- Event Icon -->
							<div class="flex-shrink-0 w-8 h-8 rounded-full border {getEventColor(event)} flex items-center justify-center">
								<span class="text-sm">{getEventIcon(event)}</span>
							</div>
							
							<!-- Event Content -->
							<div class="flex-1 min-w-0">
								<div class="text-sm font-medium text-surface-900 ">
									{formatEventMessage(event)}
								</div>
								{#if event.data?.description}
									<div class="text-xs text-surface-600  mt-1 truncate">
										{event.data.description}
									</div>
								{/if}
								<div class="flex items-center space-x-2 mt-2">
									<span class="text-xs text-surface-500 ">
										{getTimeAgo(event.timestamp)}
									</span>
									{#if 'userId' in event && event.userId}
										<span class="text-xs text-surface-500 ">•</span>
										<span class="text-xs text-surface-500 ">
											by {event.userId}
										</span>
									{/if}
									{#if 'priority' in event && event.priority}
										<span class="text-xs text-surface-500 ">•</span>
										<span class="text-xs {event.priority === 'critical' ? 'text-error-600' : event.priority === 'high' ? 'text-warning-600' : 'text-surface-500'}">
											{event.priority}
										</span>
									{/if}
								</div>
							</div>
						</div>
					</div>
				{/each}
			</div>
		{/if}
	</div>

	{#if compact && activityFeed.length > 5}
		<div class="p-3 border-t border-surface-100 bg-surface-50 ">
			<button class="text-sm text-primary-600 hover:text-primary-700">
				View all activity ({activityFeed.length})
			</button>
		</div>
	{/if}
</div>

<style>
	.activity-feed {
		transition: all 0.2s ease;
	}
	
	@keyframes slideIn {
		from {
			opacity: 0;
			transform: translateY(-10px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}
	
	.divide-y > div {
		animation: slideIn 0.3s ease;
	}
</style>