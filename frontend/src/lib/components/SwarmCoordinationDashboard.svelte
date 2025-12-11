<script lang="ts">
	import { onMount } from 'svelte';
	import { writable } from 'svelte/store';

	// Stores
	let swarmStatus = writable({});
	let swarmAgents = writable([]);
	let swarmTasks = writable([]);
	let coordinationPatterns = writable({});
	
	// UI State
	let isLoading = true;
	let selectedTab = 'overview';
	let notification = null;
	let showCreateTaskModal = false;
	
	// New task form
	let newTaskForm = {
		description: '',
		priority: 5,
		required_expertise: [],
		estimated_duration: null
	};

	// Reactive computed values
	$: totalAgents = $swarmStatus.total_agents || 0;
	$: activeTasks = $swarmStatus.active_tasks || 0;
	$: completedTasks = $swarmStatus.completed_tasks || 0;
	$: availableAgents = $swarmAgents.filter(agent => agent.is_available).length;

	onMount(async () => {
		await loadSwarmData();
		// Setup periodic refresh
		setInterval(loadSwarmData, 30000); // Refresh every 30 seconds
	});

	async function loadSwarmData() {
		try {
			// Load all swarm data in parallel
			const [statusRes, agentsRes, tasksRes, patternsRes] = await Promise.all([
				fetch('/api/v1/swarm/status'),
				fetch('/api/v1/swarm/agents'),
				fetch('/api/v1/swarm/tasks'),
				fetch('/api/v1/swarm/coordination-patterns')
			]);

			if (statusRes.ok) swarmStatus.set(await statusRes.json());
			if (agentsRes.ok) swarmAgents.set((await agentsRes.json()).agents);
			if (tasksRes.ok) swarmTasks.set((await tasksRes.json()).tasks);
			if (patternsRes.ok) coordinationPatterns.set((await patternsRes.json()).patterns);
			
		} catch (error) {
			console.error('Failed to load swarm data:', error);
			showNotification('Failed to load swarm data', 'error');
		} finally {
			isLoading = false;
		}
	}

	async function initializeSwarm() {
		try {
			const response = await fetch('/api/v1/swarm/initialize', {
				method: 'POST'
			});
			
			if (!response.ok) throw new Error('Failed to initialize swarm');
			
			const result = await response.json();
			showNotification(`Swarm initialized with ${result.agents_registered} agents`, 'success');
			await loadSwarmData();
			
		} catch (error) {
			console.error('Failed to initialize swarm:', error);
			showNotification('Failed to initialize swarm coordination', 'error');
		}
	}

	async function createSwarmTask() {
		try {
			const response = await fetch('/api/v1/swarm/tasks', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(newTaskForm)
			});
			
			if (!response.ok) throw new Error('Failed to create swarm task');
			
			const task = await response.json();
			showNotification(`Swarm task created: ${task.task_id}`, 'success');
			
			// Reset form and close modal
			newTaskForm = {
				description: '',
				priority: 5,
				required_expertise: [],
				estimated_duration: null
			};
			showCreateTaskModal = false;
			
			await loadSwarmData();
			
		} catch (error) {
			console.error('Failed to create swarm task:', error);
			showNotification('Failed to create swarm task', 'error');
		}
	}

	async function executeTask(taskId) {
		try {
			const response = await fetch(`/api/v1/swarm/tasks/${taskId}/execute`, {
				method: 'POST'
			});
			
			if (!response.ok) throw new Error('Failed to execute task');
			
			const result = await response.json();
			showNotification(result.message, 'success');
			await loadSwarmData();
			
		} catch (error) {
			console.error('Failed to execute task:', error);
			showNotification('Failed to execute swarm task', 'error');
		}
	}

	async function cancelTask(taskId) {
		if (!confirm('Are you sure you want to cancel this swarm task?')) return;
		
		try {
			const response = await fetch(`/api/v1/swarm/tasks/${taskId}`, {
				method: 'DELETE'
			});
			
			if (!response.ok) throw new Error('Failed to cancel task');
			
			const result = await response.json();
			showNotification(result.message, 'success');
			await loadSwarmData();
			
		} catch (error) {
			console.error('Failed to cancel task:', error);
			showNotification('Failed to cancel task', 'error');
		}
	}

	function showNotification(message, type = 'info') {
		notification = { message, type };
		setTimeout(() => notification = null, 5000);
	}

	function getStatusColor(status) {
		const colors = {
			pending: 'bg-yellow-100 text-yellow-800',
			assigned: 'bg-blue-100 text-blue-800',
			in_progress: 'bg-purple-100 text-purple-800',
			completed: 'bg-green-100 text-green-800',
			failed: 'bg-red-100 text-red-800'
		};
		return colors[status] || 'bg-surface-100 text-surface-800';
	}

	function getRoleColor(role) {
		const colors = {
			coordinator: 'bg-purple-100 text-purple-800',
			specialist: 'bg-blue-100 text-blue-800',
			executor: 'bg-green-100 text-green-800',
			monitor: 'bg-yellow-100 text-yellow-800',
			communicator: 'bg-pink-100 text-pink-800'
		};
		return colors[role] || 'bg-surface-100 text-surface-800';
	}

	function getLoadBarColor(load) {
		if (load < 0.3) return 'bg-green-500';
		if (load < 0.7) return 'bg-yellow-500';
		return 'bg-red-500';
	}

	// (removed) unused formatDuration
</script>

<svelte:head>
	<title>Swarm Coordination | Convergio</title>
</svelte:head>

<!-- Notification -->
{#if notification}
	<div class="fixed top-4 right-4 z-50 max-w-sm">
		<div class="rounded-lg shadow-lg border p-4"
			 class:bg-green-50={notification.type === 'success'}
			 class:border-green-200={notification.type === 'success'}
			 class:text-green-800={notification.type === 'success'}
			 class:bg-red-50={notification.type === 'error'}
			 class:border-red-200={notification.type === 'error'}
			 class:text-red-800={notification.type === 'error'}
			 class:bg-blue-50={notification.type === 'info'}
			 class:border-blue-200={notification.type === 'info'}
			 class:text-blue-800={notification.type === 'info'}>
			<div class="flex justify-between items-start">
				<p class="text-sm font-medium">{notification.message}</p>
				<button on:click={() => notification = null} class="ml-2 text-surface-600 hover:text-surface-300" aria-label="Dismiss notification">
					<svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
						<path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
					</svg>
				</button>
			</div>
		</div>
	</div>
{/if}

<!-- Create Task Modal -->
{#if showCreateTaskModal}
	<div class="fixed inset-0 bg-black bg-opacity-50 z-40 flex items-center justify-center p-4">
		<div class="bg-white rounded-lg shadow-xl w-full max-w-2xl">
			<div class="px-6 py-4 border-b">
				<div class="flex justify-between items-center">
					<h2 class="text-xl font-semibold">Create Swarm Task</h2>
					<button on:click={() => showCreateTaskModal = false} class="text-surface-600 hover:text-surface-300" aria-label="Close modal">
						<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
						</svg>
					</button>
				</div>
			</div>
			<div class="px-6 py-4 space-y-4">
				<div>
					<label class="block text-sm font-medium text-surface-600 mb-1" for="swarm-task-description">Task Description</label>
					<textarea 
						id="swarm-task-description"
						bind:value={newTaskForm.description}
						rows="4"
						class="w-full px-3 py-2 border border-surface-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
						placeholder="Describe the task for swarm coordination..."
					></textarea>
				</div>
				<div class="grid grid-cols-2 gap-4">
					<div>
						<label class="block text-sm font-medium text-surface-600 mb-1" for="swarm-priority">Priority (1-10)</label>
						<input 
							id="swarm-priority"
							type="number"
							bind:value={newTaskForm.priority}
							min="1"
							max="10"
							class="w-full px-3 py-2 border border-surface-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
						/>
					</div>
					<div>
						<label class="block text-sm font-medium text-surface-600 mb-1" for="swarm-duration">Duration (minutes)</label>
						<input 
							id="swarm-duration"
							type="number"
							bind:value={newTaskForm.estimated_duration}
							min="1"
							class="w-full px-3 py-2 border border-surface-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
							placeholder="Auto-estimated if empty"
						/>
					</div>
				</div>
			</div>
			<div class="px-6 py-4 border-t flex justify-end space-x-3">
				<button 
					on:click={() => showCreateTaskModal = false}
					class="px-4 py-2 border border-surface-300 text-surface-600 rounded-md hover:bg-surface-50"
				>
					Cancel
				</button>
				<button 
					on:click={createSwarmTask}
					disabled={!newTaskForm.description.trim()}
					class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-surface-400 disabled:cursor-not-allowed"
				>
					Create Task
				</button>
			</div>
		</div>
	</div>
{/if}

<div class="min-h-screen bg-surface-50">
	<!-- Header -->
	<div class="bg-white shadow-sm border-b">
		<div class="max-w-7xl mx-auto px-6 py-6">
			<div class="flex justify-between items-start">
				<div>
					<h1 class="text-3xl font-bold text-surface-900 mb-2">🤖 Swarm Coordination</h1>
					<p class="text-surface-600">Advanced agent coordination with swarm intelligence patterns</p>
				</div>
				<div class="flex space-x-3">
					<button
						on:click={initializeSwarm}
						class="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors flex items-center"
					>
						<svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
						</svg>
						Initialize Swarm
					</button>
					<button
						on:click={() => showCreateTaskModal = true}
						class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center"
					>
						<svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/>
						</svg>
						Create Task
					</button>
				</div>
			</div>
		</div>
	</div>

	<!-- Main Content -->
	<div class="max-w-7xl mx-auto px-6 py-6">
		{#if isLoading}
			<div class="flex items-center justify-center py-12">
				<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
				<span class="ml-3 text-surface-600">Loading swarm coordination data...</span>
			</div>
		{:else}
			<!-- Overview Stats -->
			<div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
				<div class="bg-white rounded-lg shadow-sm border p-6">
					<div class="flex items-center">
						<div class="p-3 rounded-full bg-purple-100">
							<svg class="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z"/>
							</svg>
						</div>
						<div class="ml-4">
							<p class="text-sm font-medium text-surface-500">Total Agents</p>
							<p class="text-2xl font-semibold text-surface-900">{totalAgents}</p>
						</div>
					</div>
				</div>

				<div class="bg-white rounded-lg shadow-sm border p-6">
					<div class="flex items-center">
						<div class="p-3 rounded-full bg-blue-100">
							<svg class="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
							</svg>
						</div>
						<div class="ml-4">
							<p class="text-sm font-medium text-surface-500">Available Agents</p>
							<p class="text-2xl font-semibold text-surface-900">{availableAgents}</p>
						</div>
					</div>
				</div>

				<div class="bg-white rounded-lg shadow-sm border p-6">
					<div class="flex items-center">
						<div class="p-3 rounded-full bg-yellow-100">
							<svg class="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
							</svg>
						</div>
						<div class="ml-4">
							<p class="text-sm font-medium text-surface-500">Active Tasks</p>
							<p class="text-2xl font-semibold text-surface-900">{activeTasks}</p>
						</div>
					</div>
				</div>

				<div class="bg-white rounded-lg shadow-sm border p-6">
					<div class="flex items-center">
						<div class="p-3 rounded-full bg-green-100">
							<svg class="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
							</svg>
						</div>
						<div class="ml-4">
							<p class="text-sm font-medium text-surface-500">Completed</p>
							<p class="text-2xl font-semibold text-surface-900">{completedTasks}</p>
						</div>
					</div>
				</div>
			</div>

			<!-- Tabs -->
			<div class="mb-6">
				<nav class="flex space-x-8 border-b border-surface-200">
					{#each ['overview', 'tasks', 'agents', 'patterns'] as tab}
						<button
							on:click={() => selectedTab = tab}
							class="py-2 px-1 border-b-2 font-medium text-sm capitalize transition-colors"
							class:border-purple-500={selectedTab === tab}
							class:text-purple-600={selectedTab === tab}
							class:border-transparent={selectedTab !== tab}
							class:text-surface-500={selectedTab !== tab}
							class:hover:text-surface-600={selectedTab !== tab}
						>
							{tab.replace('_', ' ')}
						</button>
					{/each}
				</nav>
			</div>

			<!-- Tab Content -->
			{#if selectedTab === 'overview'}
				<div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
					<!-- System Status -->
					<div class="bg-white rounded-lg shadow-sm border p-6">
						<h3 class="text-lg font-semibold mb-4">System Status</h3>
						<div class="space-y-3">
							<div class="flex justify-between items-center">
								<span class="text-sm text-surface-600">System Status</span>
								<span class="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs">
									{$swarmStatus.system_status || 'Operational'}
								</span>
							</div>
							<div class="flex justify-between items-center">
								<span class="text-sm text-surface-600">Coordination Ready</span>
								<span class="px-2 py-1 rounded-full text-xs"
									  class:bg-green-100={totalAgents >= 3}
									  class:text-green-800={totalAgents >= 3}
									  class:bg-yellow-100={totalAgents < 3}
									  class:text-yellow-800={totalAgents < 3}>
									{totalAgents >= 3 ? 'Ready' : 'Limited'}
								</span>
							</div>
							<div class="flex justify-between items-center">
								<span class="text-sm text-surface-600">Available Patterns</span>
								<span class="text-sm font-medium">{Object.keys($coordinationPatterns).length}</span>
							</div>
						</div>
					</div>

					<!-- Quick Actions -->
					<div class="bg-white rounded-lg shadow-sm border p-6">
						<h3 class="text-lg font-semibold mb-4">Quick Actions</h3>
						<div class="space-y-3">
							<button
								on:click={loadSwarmData}
								class="w-full px-4 py-2 border border-surface-300 text-surface-600 rounded-md hover:bg-surface-50 transition-colors text-left"
								aria-label="Refresh status"
							>
								🔄 Refresh Status
							</button>
							<button
								on:click={() => showCreateTaskModal = true}
								class="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-left"
								aria-label="Create swarm task"
							>
								➕ Create Swarm Task
							</button>
							<button
								on:click={initializeSwarm}
								class="w-full px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors text-left"
								aria-label="Re-initialize swarm"
							>
								⚡ Re-initialize Swarm
							</button>
						</div>
					</div>
				</div>

			{:else if selectedTab === 'tasks'}
				<!-- Tasks Tab -->
				<div class="bg-white rounded-lg shadow-sm border">
					<div class="px-6 py-4 border-b">
						<h3 class="text-lg font-semibold">Swarm Tasks</h3>
					</div>
					<div class="overflow-x-auto">
						<table class="min-w-full divide-y divide-gray-200">
							<thead class="bg-surface-50">
								<tr>
									<th class="px-6 py-3 text-left text-xs font-medium text-surface-500 uppercase">Task</th>
									<th class="px-6 py-3 text-left text-xs font-medium text-surface-500 uppercase">Status</th>
									<th class="px-6 py-3 text-left text-xs font-medium text-surface-500 uppercase">Complexity</th>
									<th class="px-6 py-3 text-left text-xs font-medium text-surface-500 uppercase">Agents</th>
									<th class="px-6 py-3 text-left text-xs font-medium text-surface-500 uppercase">Pattern</th>
									<th class="px-6 py-3 text-left text-xs font-medium text-surface-500 uppercase">Priority</th>
									<th class="px-6 py-3 text-left text-xs font-medium text-surface-500 uppercase">Actions</th>
								</tr>
							</thead>
							<tbody class="bg-white divide-y divide-gray-200">
								{#each $swarmTasks as task (task.task_id)}
									<tr>
										<td class="px-6 py-4 whitespace-nowrap">
											<div class="text-sm font-medium text-surface-900">{task.task_id}</div>
											<div class="text-sm text-surface-500">{task.description}</div>
										</td>
										<td class="px-6 py-4 whitespace-nowrap">
											<span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full {getStatusColor(task.status)}">
												{task.status}
											</span>
										</td>
										<td class="px-6 py-4 whitespace-nowrap text-sm text-surface-900">
											{task.complexity}
										</td>
										<td class="px-6 py-4 whitespace-nowrap text-sm text-surface-900">
											{task.assigned_agents_count || 0}
										</td>
										<td class="px-6 py-4 whitespace-nowrap text-sm text-surface-500">
											{task.coordination_pattern || 'Not assigned'}
										</td>
										<td class="px-6 py-4 whitespace-nowrap">
											<span class="text-sm font-medium">{task.priority}/10</span>
										</td>
										<td class="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
											{#if task.status === 'pending' || task.status === 'assigned'}
												<button
													on:click={() => executeTask(task.task_id)}
													class="text-green-600 hover:text-green-900"
												>
													Execute
												</button>
											{/if}
											{#if task.status !== 'completed'}
												<button
													on:click={() => cancelTask(task.task_id)}
													class="text-red-600 hover:text-red-900"
												>
													Cancel
												</button>
											{/if}
										</td>
									</tr>
								{/each}
							</tbody>
						</table>
						{#if $swarmTasks.length === 0}
							<div class="text-center py-12">
								<svg class="mx-auto h-12 w-12 text-surface-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
								</svg>
								<h3 class="text-lg font-medium text-surface-900 mb-2">No swarm tasks</h3>
								<p class="text-surface-500">Create your first swarm coordination task to get started.</p>
							</div>
						{/if}
					</div>
				</div>

			{:else if selectedTab === 'agents'}
				<!-- Agents Tab -->
				<div class="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
					{#each $swarmAgents as agent (agent.key)}
						<div class="bg-white rounded-lg shadow-sm border p-6">
							<div class="flex items-center justify-between mb-4">
								<div class="flex items-center space-x-3">
									<div class="w-10 h-10 rounded-full bg-gradient-to-br from-purple-400 to-blue-500 flex items-center justify-center text-white font-bold text-sm">
										{agent.name.slice(0, 2).toUpperCase()}
									</div>
									<div>
										<h3 class="font-medium text-surface-900">{agent.name.replace(/_/g, ' ')}</h3>
										<span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full {getRoleColor(agent.role)}">
											{agent.role}
										</span>
									</div>
								</div>
								<div class="w-2 h-2 rounded-full"
									 class:bg-green-500={agent.is_available}
									 class:bg-red-500={!agent.is_available}
								></div>
							</div>

							<div class="space-y-3">
								<!-- Load Bar -->
								<div>
									<div class="flex justify-between items-center text-xs text-surface-500 mb-1">
										<span>Current Load</span>
										<span>{Math.round(agent.current_load * 100)}%</span>
									</div>
									<div class="w-full bg-surface-200 rounded-full h-2">
										<div 
											class="h-2 rounded-full transition-all duration-300 {getLoadBarColor(agent.current_load)}"
											style="width: {agent.current_load * 100}%"
										></div>
									</div>
								</div>

								<!-- Success Rate -->
								<div class="flex justify-between text-sm">
									<span class="text-surface-500">Success Rate</span>
									<span class="font-medium">{Math.round(agent.success_rate * 100)}%</span>
								</div>

								<!-- Tools Count -->
								<div class="flex justify-between text-sm">
									<span class="text-surface-500">Tools</span>
									<span class="font-medium">{agent.tools_count}</span>
								</div>

								<!-- Coordination Score -->
								<div class="flex justify-between text-sm">
									<span class="text-surface-500">Coordination</span>
									<span class="font-medium">{Math.round(agent.coordination_score * 100)}/100</span>
								</div>

								<!-- Expertise Areas -->
								{#if agent.expertise_areas && agent.expertise_areas.length > 0}
									<div class="pt-2 border-t">
										<p class="text-xs text-surface-500 mb-2">Expertise Areas</p>
										<div class="flex flex-wrap gap-1">
											{#each agent.expertise_areas.slice(0, 3) as area}
												<span class="inline-flex px-2 py-1 bg-surface-100 text-surface-600 text-xs rounded">
													{area}
												</span>
											{/each}
											{#if agent.expertise_areas.length > 3}
												<span class="text-xs text-surface-500">+{agent.expertise_areas.length - 3} more</span>
											{/if}
										</div>
									</div>
								{/if}
							</div>
						</div>
					{/each}
				</div>

			{:else if selectedTab === 'patterns'}
				<!-- Patterns Tab -->
				<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
					{#each Object.entries($coordinationPatterns) as [patternName, pattern] (patternName)}
						<div class="bg-white rounded-lg shadow-sm border p-6">
							<div class="flex items-center justify-between mb-4">
								<h3 class="text-lg font-semibold capitalize">{patternName.replace('_', ' ')}</h3>
								<span class="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
									{Math.round((1 - pattern.coordination_overhead) * 100)}% Efficiency
								</span>
							</div>

							<p class="text-surface-600 mb-4">{pattern.description}</p>

							<div class="space-y-3">
								<div>
									<p class="text-sm font-medium text-surface-600 mb-2">Best For:</p>
									<div class="flex flex-wrap gap-2">
										{#each pattern.best_for as useCase}
											<span class="inline-flex px-2 py-1 bg-green-100 text-green-800 text-xs rounded">
												{useCase.replace('_', ' ')}
											</span>
										{/each}
									</div>
								</div>

								<div class="pt-3 border-t">
									<div class="flex justify-between text-sm">
										<span class="text-surface-500">Coordination Overhead</span>
										<span class="font-medium">{Math.round(pattern.coordination_overhead * 100)}%</span>
									</div>
								</div>
							</div>
						</div>
					{/each}
				</div>
			{/if}
		{/if}
	</div>
</div>

<style>
	.min-h-screen {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		background-attachment: fixed;
	}
	
	.min-h-screen > div {
		background: rgba(255, 255, 255, 0.95);
		backdrop-filter: blur(10px);
	}
</style>