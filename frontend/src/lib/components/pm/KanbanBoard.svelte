<script lang="ts">
	import { onMount } from 'svelte';
	import { projectsService } from '$lib/services/projectsService';

	// Props
	export let projectId: string;

	// Interfaces
	interface Task {
		id: string;
		title: string;
		description: string;
		assignee: {
			name: string;
			avatar: string;
		};
		priority: 'low' | 'medium' | 'high' | 'critical';
		labels: string[];
		dueDate: string;
		estimatedHours: number;
		actualHours: number;
		subtasks: number;
		completedSubtasks: number;
	}

	interface Column {
		id: string;
		title: string;
		color: string;
		limit?: number;
		tasks: Task[];
	}

	// State
	let columns: Column[] = [];
	let loading = false;
	let draggedTask: Task | null = null;
	let showTaskModal = false;
	let newTask: Partial<Task> = {};

	onMount(async () => {
		await loadKanbanData();
	});

	async function loadKanbanData() {
		loading = true;
		try {
			// Load real activities from backend
			if (projectId) {
				const activities = await projectsService.getActivities();
				
				// Group activities by status into kanban columns
				const tasksByStatus: {
					planning: Task[];
					'in-progress': Task[];
					review: Task[];
					completed: Task[];
					backlog: Task[];
				} = {
					planning: [],
					'in-progress': [],
					review: [],
					completed: [],
					backlog: []
				};

				// Convert activities to tasks and group by status
				const _engagement = await projectsService.getEngagement(parseInt(projectId));

				activities.forEach((activity, _index) => {
					// Calculate realistic due date based on activity creation
					const createdDate = new Date(activity.created_at || new Date());
					const dueDate = new Date(createdDate);
					dueDate.setDate(dueDate.getDate() + 14); // 2 weeks from creation
								
					const task: Task = {
						id: activity.id.toString(),
						title: activity.title,
						description: activity.description || 'No description provided',
						assignee: {
							name: 'Project Team',
							avatar: '/avatars/default.jpg'
						},
						priority: 'medium' as 'medium', // Default priority since activity doesn't have this
						labels: ['Task', activity.status || 'General'],
						dueDate: dueDate.toISOString().split('T')[0],
						estimatedHours: 8, // Default estimate
						actualHours: 0, // Default actual hours
						subtasks: 1, // Default subtask count
						completedSubtasks: activity.status === 'completed' ? 1 : 0
					};

					// Map activity status to kanban columns
					const status = activity.status || 'planning';
					if (status === 'planning') {
						tasksByStatus.backlog.push(task);
					} else if (status === 'in-progress') {
						tasksByStatus['in-progress'].push(task);
					} else if (status === 'review') {
						tasksByStatus.review.push(task);
					} else if (status === 'completed') {
						tasksByStatus.completed.push(task);
					} else {
						tasksByStatus.backlog.push(task);
					}
				});

				// Create columns with real data
				columns = [
					{
						id: 'backlog',
						title: 'Backlog',
						color: 'bg-surface-100 ',
						tasks: tasksByStatus.backlog
					},
					{
						id: 'todo',
						title: 'To Do',
						color: 'bg-info-100',
						limit: 5,
						tasks: tasksByStatus.planning
					},
					{
						id: 'in-progress',
						title: 'In Progress',
						color: 'bg-warning-100',
						limit: 3,
						tasks: tasksByStatus['in-progress']
					},
					{
						id: 'review',
						title: 'Code Review',
						color: 'bg-primary-100',
						limit: 2,
						tasks: tasksByStatus.review
					},
					{
						id: 'done',
						title: 'Done',
						color: 'bg-success-100',
						tasks: tasksByStatus.completed
					}
				];
			} else {
				// If no project ID, show empty state
				columns = [
					{
						id: 'backlog',
						title: 'Backlog',
						color: 'bg-surface-100 ',
						tasks: []
					},
					{
						id: 'todo',
						title: 'To Do',
						color: 'bg-info-100',
						limit: 5,
						tasks: []
					},
					{
						id: 'in-progress',
						title: 'In Progress',
						color: 'bg-warning-100',
						limit: 3,
						tasks: []
					},
					{
						id: 'review',
						title: 'Code Review',
						color: 'bg-primary-100',
						limit: 2,
						tasks: []
					},
					{
						id: 'done',
						title: 'Done',
						color: 'bg-success-100',
						tasks: []
					}
				];
			}
		} catch {
			// Silent failure
			// Set empty state on error instead of mock data
			columns = [
				{
					id: 'backlog',
					title: 'Backlog',
					color: 'bg-surface-100 ',
					tasks: []
				},
				{
					id: 'todo',
					title: 'To Do',
					color: 'bg-info-100',
					limit: 5,
					tasks: []
				},
				{
					id: 'in-progress',
					title: 'In Progress',
					color: 'bg-warning-100',
					limit: 3,
					tasks: []
				},
				{
					id: 'review',
					title: 'Code Review',
					color: 'bg-primary-100',
					limit: 2,
					tasks: []
				},
				{
					id: 'done',
					title: 'Done',
					color: 'bg-success-100',
					tasks: []
				}
			];
		} finally {
			loading = false;
		}
	}

	function getPriorityColor(priority: string) {
		switch (priority) {
			case 'critical': return 'border-l-error-500 bg-error-50';
			case 'high': return 'border-l-warning-500 bg-warning-50';
			case 'medium': return 'border-l-info-500 bg-info-50';
			case 'low': return 'border-l-surface-400 bg-surface-50';
			default: return 'border-l-surface-400 bg-surface-50';
		}
	}

	function getPriorityIcon(priority: string) {
		switch (priority) {
			case 'critical': return '🔴';
			case 'high': return '🟡';
			case 'medium': return '🔵';
			case 'low': return '⚪';
			default: return '⚪';
		}
	}

	function formatDate(dateStr: string) {
		const date = new Date(dateStr);
		const now = new Date();
		const diffTime = date.getTime() - now.getTime();
		const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
		
		if (diffDays < 0) {
			return { text: `${Math.abs(diffDays)} days overdue`, color: 'text-error-600' };
		} else if (diffDays === 0) {
			return { text: 'Due today', color: 'text-warning-600' };
		} else if (diffDays <= 3) {
			return { text: `${diffDays} days left`, color: 'text-warning-600' };
		} else {
			return { text: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }), color: 'text-surface-500' };
		}
	}

	// Drag and Drop handlers
	function handleDragStart(event: DragEvent, task: Task) {
		if (event.dataTransfer) {
			draggedTask = task;
			event.dataTransfer.effectAllowed = 'move';
			event.dataTransfer.setData('text/html', '');
		}
	}

	function handleDragOver(event: DragEvent) {
		event.preventDefault();
		if (event.dataTransfer) {
			event.dataTransfer.dropEffect = 'move';
		}
	}

	function handleDrop(event: DragEvent, targetColumnId: string) {
		event.preventDefault();
		if (!draggedTask) return;

		// Remove task from source column
		columns = columns.map(column => ({
			...column,
			tasks: column.tasks.filter(task => task.id !== draggedTask!.id)
		}));

		// Add task to target column
		columns = columns.map(column => {
			if (column.id === targetColumnId) {
				return {
					...column,
					tasks: [...column.tasks, draggedTask!]
				};
			}
			return column;
		});

		draggedTask = null;
	}

	function getTotalTasks() {
		return columns.reduce((total, column) => total + column.tasks.length, 0);
	}

	function getCompletedTasks() {
		return columns.find(col => col.id === 'done')?.tasks.length || 0;
	}

	function openTaskModal() {
		newTask = {
			title: '',
			description: '',
			priority: 'medium',
			labels: [],
			dueDate: '',
			estimatedHours: 0
		};
		showTaskModal = true;
	}
</script>

<div class="kanban-board bg-white rounded-xl shadow-sm border border-surface-200  overflow-hidden">
	<!-- Header -->
	<div class="p-6 border-b border-surface-200  bg-surface-50 ">
		<div class="flex items-center justify-between">
			<div>
				<h3 class="text-lg font-semibold text-surface-900 ">Kanban Board</h3>
				<p class="text-sm text-surface-600 ">Drag and drop task management</p>
			</div>
			<div class="flex items-center space-x-4">
				<!-- Stats -->
				<div class="flex items-center space-x-4 text-sm">
					<div class="flex items-center space-x-2">
						<div class="w-2 h-2 rounded-full bg-primary-500"></div>
						<span class="text-surface-600 ">{getTotalTasks()} Total</span>
					</div>
					<div class="flex items-center space-x-2">
						<div class="w-2 h-2 rounded-full bg-success-500"></div>
						<span class="text-surface-600 ">{getCompletedTasks()} Done</span>
					</div>
				</div>
				
				<!-- Add Task Button -->
				<button on:click={openTaskModal} class="btn-primary btn-sm">
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
					</svg>
					Add Task
				</button>
			</div>
		</div>
	</div>

	{#if loading}
		<div class="flex items-center justify-center py-12">
			<div class="loading-spinner"></div>
		</div>
	{:else}
		<!-- Kanban Columns -->
		<div class="kanban-columns p-6">
			<div class="flex space-x-6 overflow-x-auto">
				{#each columns as column}
					<div
						class="kanban-column flex-shrink-0 w-80"
						role="region"
						aria-label="Kanban column: {column.title}"
						on:dragover={handleDragOver}
						on:drop={event => handleDrop(event, column.id)}
					>
						<!-- Column Header -->
						<div class="column-header p-4 rounded-t-lg {column.color} border-b border-surface-200 ">
							<div class="flex items-center justify-between">
								<div class="flex items-center space-x-3">
									<h4 class="font-semibold text-surface-900 ">{column.title}</h4>
									<span class="badge badge-sm bg-white  text-surface-700 ">
										{column.tasks.length}
									</span>
								</div>
								{#if column.limit}
									<div class="text-xs text-surface-500 ">
										Limit: {column.limit}
									</div>
								{/if}
							</div>
						</div>

						<!-- Tasks -->
						<div class="tasks-container min-h-[400px] max-h-[600px] overflow-y-auto p-2 space-y-3 bg-surface-50  rounded-b-lg">
							{#each column.tasks as task}
								<div
									class="task-card card p-4 cursor-move border-l-4 {getPriorityColor(task.priority)} hover:shadow-md transition-all duration-200"
									role="button"
									tabindex="0"
									aria-label="Task: {task.title}"
									draggable="true"
									on:dragstart={event => handleDragStart(event, task)}
								>
									<!-- Task Header -->
									<div class="flex items-start justify-between mb-3">
										<div class="flex-1">
											<h5 class="font-medium text-surface-900  mb-1 line-clamp-2">{task.title}</h5>
											<p class="text-sm text-surface-600  line-clamp-2">{task.description}</p>
										</div>
										<div class="ml-2">
											<span class="text-sm">{getPriorityIcon(task.priority)}</span>
										</div>
									</div>

									<!-- Labels -->
									{#if task.labels.length > 0}
										<div class="flex flex-wrap gap-1 mb-3">
											{#each task.labels as label}
												<span class="badge badge-sm badge-primary">{label}</span>
											{/each}
										</div>
									{/if}

									<!-- Progress -->
									{#if task.subtasks > 0}
										<div class="mb-3">
											<div class="flex items-center justify-between text-xs text-surface-600  mb-1">
												<span>Subtasks</span>
												<span>{task.completedSubtasks}/{task.subtasks}</span>
											</div>
											<div class="w-full bg-surface-200  rounded-full h-1.5">
												<div 
													class="bg-primary-500 h-1.5 rounded-full transition-all duration-500" 
													style="width: {(task.completedSubtasks / task.subtasks) * 100}%"
												></div>
											</div>
										</div>
									{/if}

									<!-- Footer -->
									<div class="flex items-center justify-between pt-3 border-t border-surface-200 ">
										<!-- Assignee -->
										<div class="flex items-center space-x-2">
											<div class="avatar avatar-xs">
												<div class="w-full h-full bg-primary-200 rounded-full flex items-center justify-center text-xs font-semibold text-primary-700">
													{task.assignee.name.charAt(0)}
												</div>
											</div>
											<span class="text-xs text-surface-600 ">{task.assignee.name}</span>
										</div>

										<!-- Due Date -->
										<div class="text-xs {formatDate(task.dueDate).color}">
											{formatDate(task.dueDate).text}
										</div>
									</div>

									<!-- Time Tracking -->
									{#if task.actualHours > 0 || task.estimatedHours > 0}
										<div class="flex items-center justify-between text-xs text-surface-500  mt-2">
											<span>⏱️ {task.actualHours}h / {task.estimatedHours}h</span>
											{#if task.estimatedHours > 0}
												<span class="font-medium {task.actualHours > task.estimatedHours ? 'text-error-600' : 'text-success-600'}">
													{Math.round((task.actualHours / task.estimatedHours) * 100)}%
												</span>
											{/if}
										</div>
									{/if}
								</div>
							{/each}

							<!-- Add Task Button for Column -->
							<button 
								on:click={openTaskModal}
								class="w-full p-3 border-2 border-dashed border-surface-300  rounded-lg text-surface-500  hover:border-primary-500 hover:text-primary-600 transition-colors duration-200"
							>
								<svg class="w-5 h-5 mx-auto mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
								</svg>
								Add Task
							</button>
						</div>
					</div>
				{/each}
			</div>
		</div>
	{/if}
</div>

<!-- Task Creation Modal -->
{#if showTaskModal}
	<div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" role="button" tabindex="0" on:click={() => showTaskModal = false} on:keydown={e => e.key === 'Escape' && (showTaskModal = false)}>
		<div class="bg-white rounded-xl shadow-xl max-w-lg w-full mx-4 p-6" role="dialog" aria-modal="true" tabindex="-1" on:click|stopPropagation on:keydown|stopPropagation>
			<div class="flex items-center justify-between mb-6">
				<h4 class="text-lg font-semibold text-surface-900 ">Create New Task</h4>
				<button aria-label="Close modal" on:click={() => showTaskModal = false} class="text-surface-500 hover:text-surface-700">
					<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
					</svg>
				</button>
			</div>
			
			<form class="space-y-4">
				<div>
					<label for="task-title" class="block text-sm font-medium text-surface-700  mb-2">Task Title</label>
					<input id="task-title" type="text" bind:value={newTask.title} class="input" placeholder="Enter task title...">
				</div>

				<div>
					<label for="task-description" class="block text-sm font-medium text-surface-700  mb-2">Description</label>
					<textarea id="task-description" bind:value={newTask.description} class="input" rows="3" placeholder="Describe the task..."></textarea>
				</div>
				
				<div class="grid grid-cols-2 gap-4">
					<div>
						<label for="task-priority" class="block text-sm font-medium text-surface-700  mb-2">Priority</label>
						<select id="task-priority" bind:value={newTask.priority} class="input">
							<option value="low">Low</option>
							<option value="medium">Medium</option>
							<option value="high">High</option>
							<option value="critical">Critical</option>
						</select>
					</div>
					<div>
						<label for="task-due-date" class="block text-sm font-medium text-surface-700  mb-2">Due Date</label>
						<input id="task-due-date" type="date" bind:value={newTask.dueDate} class="input">
					</div>
				</div>

				<div>
					<label for="task-estimated-hours" class="block text-sm font-medium text-surface-700  mb-2">Estimated Hours</label>
					<input id="task-estimated-hours" type="number" bind:value={newTask.estimatedHours} class="input" min="0" placeholder="0">
				</div>
				
				<div class="flex justify-end space-x-3 pt-4">
					<button type="button" on:click={() => showTaskModal = false} class="btn-secondary">
						Cancel
					</button>
					<button type="submit" class="btn-primary">
						Create Task
					</button>
				</div>
			</form>
		</div>
	</div>
{/if}

<style>
	.kanban-columns {
		overflow-x: auto;
		scrollbar-width: thin;
	}
	
	.kanban-column {
		min-width: 320px;
	}
	
	.task-card {
		transition: transform 0.2s ease, box-shadow 0.2s ease;
	}
	
	.task-card:hover {
		transform: translateY(-1px);
	}
	
	.line-clamp-2 {
		display: -webkit-box;
		-webkit-line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}
</style>