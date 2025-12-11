<script lang="ts">
	import { onMount } from 'svelte';
	import { projectsService } from '$lib/services/projectsService';

	// Props
	export let projectId: string;

	// Interfaces
	interface Resource {
		id: string;
		name: string;
		role: string;
		type: 'human' | 'ai_agent' | 'system' | 'external';
		availability: number; // percentage
		costPerHour: number;
		skills: string[];
		currentTasks: Task[];
		utilization: number;
		performance: {
			tasksCompleted: number;
			averageRating: number;
			efficiency: number;
		};
	}

	interface Task {
		id: string;
		title: string;
		priority: 'low' | 'medium' | 'high' | 'critical';
		dueDate: string;
		estimatedHours: number;
	}

	interface TeamAllocation {
		resourceId: string;
		hours: number;
		role: string;
	}

	// State
	let resources: Resource[] = [];
	let loading = false;
	let selectedResource: Resource | null = null;
	let showAddResourceModal = false;
	let filterType = 'all';
	let sortBy = 'utilization';

	// Mock data for demo - TODO: Replace with real API calls
	const mockResources: Resource[] = [
		{
			id: '1',
			name: 'Alice Chen',
			role: 'Project Manager',
			type: 'human',
			availability: 90,
			costPerHour: 85,
			skills: ['Project Management', 'Agile', 'Risk Management', 'Team Leadership'],
			currentTasks: [
				{ id: '1', title: 'Sprint Planning', priority: 'high', dueDate: '2024-02-20', estimatedHours: 8 },
				{ id: '2', title: 'Stakeholder Review', priority: 'medium', dueDate: '2024-02-25', estimatedHours: 4 }
			],
			utilization: 85,
			performance: {
				tasksCompleted: 47,
				averageRating: 4.8,
				efficiency: 92
			}
		},
		{
			id: '2',
			name: 'Bob Wilson',
			role: 'Tech Lead',
			type: 'human',
			availability: 100,
			costPerHour: 95,
			skills: ['JavaScript', 'Node.js', 'System Architecture', 'Code Review'],
			currentTasks: [
				{ id: '3', title: 'API Development', priority: 'critical', dueDate: '2024-02-18', estimatedHours: 32 },
				{ id: '4', title: 'Code Review', priority: 'medium', dueDate: '2024-02-22', estimatedHours: 6 }
			],
			utilization: 95,
			performance: {
				tasksCompleted: 38,
				averageRating: 4.9,
				efficiency: 89
			}
		},
		{
			id: '3',
			name: 'Ali AI Agent',
			role: 'AI Chief of Staff',
			type: 'ai_agent',
			availability: 100,
			costPerHour: 12,
			skills: ['Strategic Planning', 'Data Analysis', 'Process Optimization', 'Decision Support'],
			currentTasks: [
				{ id: '5', title: 'Project Analysis', priority: 'high', dueDate: '2024-02-19', estimatedHours: 2 },
				{ id: '6', title: 'Risk Assessment', priority: 'medium', dueDate: '2024-02-21', estimatedHours: 1 }
			],
			utilization: 65,
			performance: {
				tasksCompleted: 156,
				averageRating: 4.7,
				efficiency: 98
			}
		},
		{
			id: '4',
			name: 'Carol Davis',
			role: 'UX Designer',
			type: 'human',
			availability: 80,
			costPerHour: 75,
			skills: ['UI/UX Design', 'Figma', 'User Research', 'Prototyping'],
			currentTasks: [
				{ id: '7', title: 'Design System', priority: 'high', dueDate: '2024-02-23', estimatedHours: 24 },
				{ id: '8', title: 'User Testing', priority: 'medium', dueDate: '2024-02-28', estimatedHours: 8 }
			],
			utilization: 78,
			performance: {
				tasksCompleted: 29,
				averageRating: 4.6,
				efficiency: 87
			}
		}
	];

	onMount(async () => {
		await loadResources();
	});

	async function loadResources() {
		loading = true;
		try {
			// TODO: Load real resource data from backend
			await new Promise(resolve => setTimeout(resolve, 500));
			resources = mockResources;
		} catch (error) {
			console.error('Error loading resources:', error);
		} finally {
			loading = false;
		}
	}

	function getTypeColor(type: string) {
		switch (type) {
			case 'human': return 'bg-blue-100 text-blue-700 border-blue-200';
			case 'ai_agent': return 'bg-purple-100 text-purple-700 border-purple-200';
			case 'system': return 'bg-gray-100 text-gray-700 border-gray-200';
			case 'external': return 'bg-orange-100 text-orange-700 border-orange-200';
			default: return 'bg-gray-100 text-gray-700 border-gray-200';
		}
	}

	function getUtilizationColor(utilization: number) {
		if (utilization >= 90) return 'text-error-600';
		if (utilization >= 70) return 'text-warning-600';
		return 'text-success-600';
	}

	function getPriorityColor(priority: string) {
		switch (priority) {
			case 'critical': return 'bg-error-500';
			case 'high': return 'bg-warning-500';
			case 'medium': return 'bg-info-500';
			case 'low': return 'bg-surface-400';
			default: return 'bg-surface-400';
		}
	}

	// Filtered and sorted resources
	$: filteredResources = resources
		.filter(resource => {
			if (filterType === 'all') return true;
			return resource.type === filterType;
		})
		.sort((a, b) => {
			switch (sortBy) {
				case 'name': return a.name.localeCompare(b.name);
				case 'utilization': return b.utilization - a.utilization;
				case 'efficiency': return b.performance.efficiency - a.performance.efficiency;
				case 'cost': return b.costPerHour - a.costPerHour;
				default: return 0;
			}
		});
</script>

<div class="resource-management bg-white rounded-xl shadow-sm border border-surface-200  overflow-hidden">
	<!-- Header -->
	<div class="p-6 border-b border-surface-200  bg-surface-50 ">
		<div class="flex items-center justify-between">
			<div>
				<h3 class="text-lg font-semibold text-surface-900 ">Resource Management</h3>
				<p class="text-sm text-surface-600 ">Team allocation, utilization, and performance tracking</p>
			</div>
			<div class="flex items-center space-x-3">
				<!-- Filter by Type -->
				<select bind:value={filterType} class="input input-sm">
					<option value="all">All Types</option>
					<option value="human">Human</option>
					<option value="ai_agent">AI Agent</option>
					<option value="system">System</option>
					<option value="external">External</option>
				</select>
				
				<!-- Sort By -->
				<select bind:value={sortBy} class="input input-sm">
					<option value="utilization">Utilization</option>
					<option value="name">Name</option>
					<option value="efficiency">Efficiency</option>
					<option value="cost">Cost</option>
				</select>
				
				<button class="btn-primary btn-sm" on:click={() => showAddResourceModal = true}>
					<svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
					</svg>
					Add Resource
				</button>
			</div>
		</div>
	</div>

	{#if loading}
		<div class="flex items-center justify-center py-12">
			<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
		</div>
	{:else}
		<!-- Resource Overview Cards -->
		<div class="p-6">
			<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 mb-6">
				{#each filteredResources as resource}
					<div class="resource-card border border-surface-200  rounded-lg p-4 hover:shadow-md transition-shadow duration-200 cursor-pointer" on:click={() => selectedResource = resource}>
						<div class="flex items-start justify-between mb-3">
							<div class="flex items-center space-x-3">
								<div class="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-600 rounded-full flex items-center justify-center">
									<span class="text-white font-semibold text-sm">
										{resource.type === 'ai_agent' ? '🤖' : resource.name.charAt(0)}
									</span>
								</div>
								<div>
									<h4 class="font-medium text-surface-900 ">{resource.name}</h4>
									<p class="text-sm text-surface-600 ">{resource.role}</p>
								</div>
							</div>
							<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border {getTypeColor(resource.type)}">
								{resource.type.replace('_', ' ')}
							</span>
						</div>

						<!-- Utilization -->
						<div class="mb-3">
							<div class="flex items-center justify-between mb-1">
								<span class="text-sm text-surface-600 ">Utilization</span>
								<span class="text-sm font-medium {getUtilizationColor(resource.utilization)}">{resource.utilization}%</span>
							</div>
							<div class="w-full bg-surface-200  rounded-full h-2">
								<div class="bg-primary-500 h-2 rounded-full transition-all duration-500" style="width: {resource.utilization}%"></div>
							</div>
						</div>

						<!-- Performance Metrics -->
						<div class="grid grid-cols-3 gap-2 text-center">
							<div>
								<div class="text-xs text-surface-500">Tasks</div>
								<div class="font-medium text-surface-900 ">{resource.performance.tasksCompleted}</div>
							</div>
							<div>
								<div class="text-xs text-surface-500">Rating</div>
								<div class="font-medium text-surface-900 ">{resource.performance.averageRating.toFixed(1)}</div>
							</div>
							<div>
								<div class="text-xs text-surface-500">Efficiency</div>
								<div class="font-medium text-surface-900 ">{resource.performance.efficiency}%</div>
							</div>
						</div>

						<!-- Current Tasks -->
						<div class="mt-3 pt-3 border-t border-surface-100">
							<div class="text-xs text-surface-500 mb-2">Current Tasks ({resource.currentTasks.length})</div>
							<div class="space-y-1">
								{#each resource.currentTasks.slice(0, 2) as task}
									<div class="flex items-center space-x-2">
										<div class="w-2 h-2 rounded-full {getPriorityColor(task.priority)}"></div>
										<span class="text-xs text-surface-600  truncate">{task.title}</span>
									</div>
								{/each}
								{#if resource.currentTasks.length > 2}
									<div class="text-xs text-surface-500">+{resource.currentTasks.length - 2} more...</div>
								{/if}
							</div>
						</div>
					</div>
				{/each}
			</div>
		</div>
	{/if}
</div>

<!-- Resource Detail Modal -->
{#if selectedResource}
	<div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" on:click={() => selectedResource = null}>
		<div class="bg-white rounded-xl shadow-xl max-w-2xl w-full mx-4 p-6 max-h-[90vh] overflow-y-auto" on:click|stopPropagation>
			<div class="flex items-center justify-between mb-6">
				<div class="flex items-center space-x-4">
					<div class="w-12 h-12 bg-gradient-to-br from-primary-500 to-primary-600 rounded-full flex items-center justify-center">
						<span class="text-white font-semibold text-lg">
							{selectedResource.type === 'ai_agent' ? '🤖' : selectedResource.name.charAt(0)}
						</span>
					</div>
					<div>
						<h4 class="text-xl font-semibold text-surface-900 ">{selectedResource.name}</h4>
						<p class="text-surface-600 ">{selectedResource.role}</p>
					</div>
				</div>
				<button on:click={() => selectedResource = null} class="text-surface-500 hover:text-surface-700">
					<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
					</svg>
				</button>
			</div>
			
			<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
				<!-- Resource Info -->
				<div class="space-y-4">
					<div>
						<h5 class="font-medium text-surface-900  mb-2">Resource Details</h5>
						<div class="space-y-2">
							<div class="flex justify-between">
								<span class="text-sm text-surface-600 ">Type</span>
								<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border {getTypeColor(selectedResource.type)}">
									{selectedResource.type.replace('_', ' ')}
								</span>
							</div>
							<div class="flex justify-between">
								<span class="text-sm text-surface-600 ">Availability</span>
								<span class="text-sm font-medium text-surface-900 ">{selectedResource.availability}%</span>
							</div>
							<div class="flex justify-between">
								<span class="text-sm text-surface-600 ">Cost per Hour</span>
								<span class="text-sm font-medium text-surface-900 ">${selectedResource.costPerHour}</span>
							</div>
						</div>
					</div>

					<div>
						<h5 class="font-medium text-surface-900  mb-2">Skills</h5>
						<div class="flex flex-wrap gap-2">
							{#each selectedResource.skills as skill}
								<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-primary-100 text-primary-700 border border-primary-200">
									{skill}
								</span>
							{/each}
						</div>
					</div>
				</div>

				<!-- Performance & Tasks -->
				<div class="space-y-4">
					<div>
						<h5 class="font-medium text-surface-900  mb-2">Performance Metrics</h5>
						<div class="space-y-3">
							<div>
								<div class="flex items-center justify-between mb-1">
									<span class="text-sm text-surface-600 ">Utilization</span>
									<span class="text-sm font-medium {getUtilizationColor(selectedResource.utilization)}">{selectedResource.utilization}%</span>
								</div>
								<div class="w-full bg-surface-200  rounded-full h-2">
									<div class="bg-primary-500 h-2 rounded-full transition-all duration-500" style="width: {selectedResource.utilization}%"></div>
								</div>
							</div>
							<div class="grid grid-cols-3 gap-4 text-center">
								<div>
									<div class="text-xs text-surface-500 mb-1">Tasks Completed</div>
									<div class="text-lg font-semibold text-surface-900 ">{selectedResource.performance.tasksCompleted}</div>
								</div>
								<div>
									<div class="text-xs text-surface-500 mb-1">Average Rating</div>
									<div class="text-lg font-semibold text-surface-900 ">{selectedResource.performance.averageRating.toFixed(1)}</div>
								</div>
								<div>
									<div class="text-xs text-surface-500 mb-1">Efficiency</div>
									<div class="text-lg font-semibold text-surface-900 ">{selectedResource.performance.efficiency}%</div>
								</div>
							</div>
						</div>
					</div>

					<div>
						<h5 class="font-medium text-surface-900  mb-2">Current Tasks</h5>
						<div class="space-y-2 max-h-40 overflow-y-auto">
							{#each selectedResource.currentTasks as task}
								<div class="flex items-center justify-between p-2 bg-surface-50  rounded">
									<div class="flex items-center space-x-2">
										<div class="w-3 h-3 rounded-full {getPriorityColor(task.priority)}"></div>
										<span class="text-sm font-medium text-surface-900 ">{task.title}</span>
									</div>
									<div class="text-xs text-surface-500">
										{task.estimatedHours}h
									</div>
								</div>
							{/each}
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>
{/if}

<style>
	.resource-card {
		background: linear-gradient(135deg, rgb(248 250 252) 0%, rgb(241 245 249) 100%);
	}
	
	:global(.dark) .resource-card {
		background: linear-gradient(135deg, rgb(15 23 42) 0%, rgb(30 41 59) 100%);
	}
</style>