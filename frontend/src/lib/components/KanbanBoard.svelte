<script lang="ts">
	import { onMount } from 'svelte';
	import { flip } from 'svelte/animate';
	import { dndzone } from 'svelte-dnd-action';
	
	export let projectId: string;
	
	interface Task {
		id: string;
		title: string;
		description?: string;
		status: string;
		priority: string;
		assignee?: string;
		assignedAgent?: string;
		dueDate?: string;
		tags: string[];
		progress: number;
	}
	
	interface Column {
		id: string;
		title: string;
		color: string;
		tasks: Task[];
	}
	
	let columns: Column[] = [
		{ id: 'pending', title: 'To Do', color: 'bg-surface-100', tasks: [] },
		{ id: 'in_progress', title: 'In Progress', color: 'bg-blue-500', tasks: [] },
		{ id: 'in_review', title: 'In Review', color: 'bg-yellow-500', tasks: [] },
		{ id: 'completed', title: 'Done', color: 'bg-green-500', tasks: [] }
	];
	
	let selectedTask: Task | null = null;
	let showAgentDialog = false;
	let defaultAgent = 'ali_chief_of_staff'; // 🤖 Ali è l'agente di default
	let availableAgents = [
		'ali_chief_of_staff',
		'davide_project_manager',
		'luke_program_manager',
		'wanda_workflow_orchestrator',
		'baccio_tech_architect',
		'marco_devops_engineer'
	];
	
	onMount(async () => {
		await loadTasks();
	});
	
	async function loadTasks() {
		try {
			const response = await fetch(`/api/v1/pm/tasks?project_id=${projectId}`);
			if (response.ok) {
				const tasks = await response.json();
				
				// Distribute tasks to columns based on status
				columns = columns.map(col => ({
					...col,
					tasks: tasks.filter((t: Task) => t.status === col.id)
				}));
			}
		} catch (error) {
			console.error('Failed to load tasks:', error);
		}
	}
	
	function handleDndConsider(columnId: string) {
		return (e: CustomEvent) => {
			const col = columns.find(c => c.id === columnId);
			if (col) {
				col.tasks = e.detail.items;
				columns = [...columns];
			}
		};
	}
	
	function handleDndFinalize(columnId: string) {
		return async (e: CustomEvent) => {
			const col = columns.find(c => c.id === columnId);
			if (col) {
				col.tasks = e.detail.items;
				columns = [...columns];
				
				// Update task status if moved to different column
				for (const task of col.tasks) {
					if (task.status !== columnId) {
						await updateTaskStatus(task.id, columnId);
						task.status = columnId;
					}
				}
			}
		};
	}
	
	async function updateTaskStatus(taskId: string, status: string) {
		try {
			await fetch(`/api/v1/pm/tasks/${taskId}`, {
				method: 'PUT',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ status })
			});
		} catch (error) {
			console.error('Failed to update task status:', error);
		}
	}
	
	function openAgentDialog(task: Task) {
		selectedTask = task;
		showAgentDialog = true;
	}
	
	async function attachAgent(agentName: string) {
		if (!selectedTask) return;
		
		try {
			const response = await fetch('/api/v1/pm/tasks/attach-agent', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					task_id: selectedTask.id,
					agent_name: agentName,
					configuration: {},
					auto_execute: true
				})
			});
			
			if (response.ok) {
				selectedTask.assignedAgent = agentName;
				columns = [...columns];
				showAgentDialog = false;
			}
		} catch (error) {
			console.error('Failed to attach agent:', error);
		}
	}
	
	function getPriorityColor(priority: string): string {
		switch (priority) {
			case 'critical': return 'bg-red-500';
			case 'high': return 'bg-orange-500';
			case 'medium': return 'bg-yellow-500';
			case 'low': return 'bg-green-500';
			default: return 'bg-surface-500';
		}
	}
	
	function formatDate(dateStr?: string): string {
		if (!dateStr) return '';
		return new Date(dateStr).toLocaleDateString();
	}
</script>

<div class="kanban-board p-6">
	<div class="grid grid-cols-4 gap-4">
		{#each columns as column (column.id)}
			<div class="kanban-column {column.color} rounded-lg p-4">
				<div class="column-header mb-4">
					<h3 class="font-semibold text-lg">{column.title}</h3>
					<span class="text-sm text-surface-600">{column.tasks.length} items</span>
				</div>
				
				<div
					class="tasks-container min-h-[400px]"
					use:dndzone={{
						items: column.tasks,
						flipDurationMs: 300,
						dropTargetStyle: {}
					}}
					on:consider={handleDndConsider(column.id)}
					on:finalize={handleDndFinalize(column.id)}
				>
					{#each column.tasks as task (task.id)}
						<div
							class="task-card bg-white rounded-lg shadow p-4 mb-3 cursor-move hover:shadow-lg transition-shadow"
							animate:flip={{ duration: 300 }}
						>
							<div class="flex items-start justify-between mb-2">
								<h4 class="font-medium text-sm flex-1">{task.title}</h4>
								<span class="priority-badge w-2 h-2 rounded-full {getPriorityColor(task.priority)}"></span>
							</div>
							
							{#if task.description}
								<p class="text-xs text-surface-600 mb-2 line-clamp-2">{task.description}</p>
							{/if}
							
							<div class="task-meta space-y-2">
								{#if task.dueDate}
									<div class="flex items-center text-xs text-surface-500">
										<svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
										</svg>
										{formatDate(task.dueDate)}
									</div>
								{/if}
								
								<div class="flex items-center justify-between">
									{#if task.assignedAgent}
										<span class="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded">
											🤖 {task.assignedAgent === 'ali_chief_of_staff' ? 'Ali (Chief of Staff)' : task.assignedAgent}
										</span>
									{:else if task.assignee}
										<span class="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
											👤 {task.assignee}
										</span>
									{:else}
										<button
											on:click={() => attachAgent(defaultAgent)}
											class="text-xs text-primary-600 hover:text-primary-800 font-medium"
										>
											🤖 Assign to Ali
										</button>
									{/if}
								</div>
								
								{#if task.progress > 0}
									<div class="progress-bar bg-surface-200 rounded-full h-1.5">
										<div
											class="bg-blue-600 h-1.5 rounded-full transition-all"
											style="width: {task.progress}%"
										></div>
									</div>
								{/if}
								
								{#if task.tags.length > 0}
									<div class="flex flex-wrap gap-1">
										{#each task.tags as tag}
											<span class="text-xs bg-surface-100 text-surface-600 px-2 py-0.5 rounded">
												{tag}
											</span>
										{/each}
									</div>
								{/if}
							</div>
						</div>
					{/each}
				</div>
			</div>
		{/each}
	</div>
</div>

<!-- Agent Attachment Dialog -->
{#if showAgentDialog}
	<div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
		<div class="bg-white rounded-lg p-6 max-w-md w-full">
			<h3 class="text-lg font-semibold mb-4">Attach AI Agent to Task</h3>
			
			{#if selectedTask}
				<p class="text-sm text-surface-600 mb-4">
					Task: <strong>{selectedTask.title}</strong>
				</p>
			{/if}
			
			<div class="space-y-2 mb-4">
				{#each availableAgents as agent}
					<button
						on:click={() => attachAgent(agent)}
						class="w-full text-left p-3 border rounded-lg hover:bg-blue-50 hover:border-blue-300 transition-colors"
					>
						<div class="font-medium">{agent}</div>
						<div class="text-xs text-surface-500">
							{#if agent === 'ali_chief_of_staff'}
								Master orchestrator and coordinator
							{:else if agent === 'davide_project_manager'}
								Project execution and delivery
							{:else if agent === 'luke_program_manager'}
								Program coordination and planning
							{:else if agent === 'wanda_workflow_orchestrator'}
								Workflow automation and optimization
							{:else if agent === 'baccio_tech_architect'}
								Technical architecture and design
							{:else if agent === 'marco_devops_engineer'}
								DevOps and infrastructure
							{/if}
						</div>
					</button>
				{/each}
			</div>
			
			<button
				on:click={() => showAgentDialog = false}
				class="w-full px-4 py-2 border border-surface-300 rounded-lg hover:bg-surface-50"
			>
				Cancel
			</button>
		</div>
	</div>
{/if}

<style>
	.line-clamp-2 {
		display: -webkit-box;
		-webkit-line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}
	
	.kanban-column {
		min-height: 500px;
	}
	
	.task-card {
		transition: transform 0.2s;
	}
	
	.task-card:hover {
		transform: translateY(-2px);
	}
</style>