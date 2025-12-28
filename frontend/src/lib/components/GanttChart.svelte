<script lang="ts">
	import { onMount } from 'svelte';
	import { scaleTime, scaleBand } from 'd3-scale';
	import { timeMonth, timeWeek, timeDay } from 'd3-time';
	import { timeFormat } from 'd3-time-format';
	
	export let projectId: string;
	
	interface Task {
		id: string;
		title: string;
		start_date: Date;
		end_date: Date;
		progress: number;
		dependencies: string[];
		assignee?: string;
		assignedAgent?: string;
		priority: string;
		status: string;
		is_milestone?: boolean;
	}
	
	interface Milestone {
		id: string;
		title: string;
		date: Date;
	}
	
	let tasks: Task[] = [];
	let milestones: Milestone[] = [];
	let svgWidth = 0;
	let svgHeight = 0;
	let chartContainer: HTMLDivElement;
	
	// View settings
	let viewMode: 'day' | 'week' | 'month' = 'week';
	let showDependencies = true;
	let showProgress = true;
	let selectedTask: Task | null = null;
	
	// Chart dimensions
	const margin = { top: 60, right: 40, bottom: 40, left: 200 };
	const rowHeight = 40;
	const barHeight = 25;
	
	onMount(() => {
		loadProjectData();
		updateDimensions();
		window.addEventListener('resize', updateDimensions);
		return () => window.removeEventListener('resize', updateDimensions);
	});
	
	async function loadProjectData() {
		try {
			const response = await fetch(`/api/v1/pm/tasks?project_id=${projectId}`);
			if (response.ok) {
				const data = await response.json();
				tasks = data.map((t: any) => ({
					...t,
					start_date: new Date(t.start_date || Date.now()),
					end_date: new Date(t.due_date || Date.now() + 86400000 * 7)
				}));
				
				// Extract milestones
				milestones = tasks
					.filter(t => t.is_milestone)
					.map(t => ({
						id: t.id,
						title: t.title,
						date: t.end_date
					}));
			}
		} catch {
			// Silent failure
		}
	}
	
	function updateDimensions() {
		if (chartContainer) {
			svgWidth = chartContainer.clientWidth;
			svgHeight = Math.max(400, tasks.length * rowHeight + margin.top + margin.bottom);
		}
	}
	
	$: chartWidth = svgWidth - margin.left - margin.right;
	$: chartHeight = svgHeight - margin.top - margin.bottom;
	
	$: timeScale = (() => {
		if (tasks.length === 0) return null;
		const startDate = new Date(Math.min(...tasks.map(t => t.start_date.getTime())));
		const endDate = new Date(Math.max(...tasks.map(t => t.end_date.getTime())));
		return scaleTime()
			.domain([startDate, endDate])
			.range([0, chartWidth]);
	})();
	
	$: yScale = scaleBand()
		.domain(tasks.map(t => t.id))
		.range([0, chartHeight])
		.padding(0.2);
	
	function getTimeIntervals() {
		if (!timeScale) return [];
		const [start, end] = timeScale.domain();
		
		switch (viewMode) {
			case 'day':
				return timeDay.range(start, end);
			case 'week':
				return timeWeek.range(start, end);
			case 'month':
				return timeMonth.range(start, end);
		}
	}
	
	function formatDate(date: Date): string {
		switch (viewMode) {
			case 'day':
				return timeFormat('%b %d')(date);
			case 'week':
				return timeFormat('W%U')(date);
			case 'month':
				return timeFormat('%b %Y')(date);
		}
	}
	
	function getTaskColor(task: Task): string {
		if (task.status === 'completed') return '#10b981';
		if (task.status === 'in_progress') return '#3b82f6';
		if (task.status === 'blocked') return '#ef4444';
		if (task.priority === 'critical') return '#dc2626';
		if (task.priority === 'high') return '#f59e0b';
		return '#6b7280';
	}
	
	function handleTaskClick(task: Task) {
		selectedTask = task;
	}
	
	function getDepPath(fromTask: Task, toTask: Task): string {
		if (!timeScale || !yScale) return '';
		
		const fromX = timeScale(fromTask.end_date);
		const fromY = (yScale(fromTask.id) || 0) + barHeight / 2;
		const toX = timeScale(toTask.start_date);
		const toY = (yScale(toTask.id) || 0) + barHeight / 2;
		
		const midX = (fromX + toX) / 2;
		
		return `M ${fromX} ${fromY} 
				C ${midX} ${fromY}, ${midX} ${toY}, ${toX} ${toY}`;
	}
	
	function changeViewMode(mode: 'day' | 'week' | 'month') {
		viewMode = mode;
	}
</script>

<div class="gantt-chart-container">
	<div class="gantt-header">
		<h2 class="text-xl font-semibold">Project Timeline</h2>
		
		<div class="gantt-controls">
			<div class="view-mode-selector">
				<button
					class:active={viewMode === 'day'}
					on:click={() => changeViewMode('day')}
					class="px-3 py-1 rounded-l border"
				>
					Day
				</button>
				<button
					class:active={viewMode === 'week'}
					on:click={() => changeViewMode('week')}
					class="px-3 py-1 border-t border-b"
				>
					Week
				</button>
				<button
					class:active={viewMode === 'month'}
					on:click={() => changeViewMode('month')}
					class="px-3 py-1 rounded-r border"
				>
					Month
				</button>
			</div>
			
			<label for="show-dependencies" class="flex items-center gap-2">
				<input
					id="show-dependencies"
					type="checkbox"
					bind:checked={showDependencies}
				/>
				Dependencies
			</label>
			
			<label for="show-progress" class="flex items-center gap-2">
				<input
					id="show-progress"
					type="checkbox"
					bind:checked={showProgress}
				/>
				Progress
			</label>
		</div>
	</div>
	
	<div class="gantt-chart" bind:this={chartContainer}>
		{#if timeScale && yScale}
			<svg width={svgWidth} height={svgHeight}>
				<!-- Background grid -->
				<g class="grid" transform="translate({margin.left}, {margin.top})">
					{#each getTimeIntervals() as date}
						<line
							x1={timeScale(date)}
							y1={0}
							x2={timeScale(date)}
							y2={chartHeight}
							stroke="#e5e7eb"
							stroke-dasharray="2,2"
						/>
					{/each}
				</g>
				
				<!-- Time axis -->
				<g class="time-axis" transform="translate({margin.left}, {margin.top - 10})">
					{#each getTimeIntervals() as date}
						<text
							x={timeScale(date)}
							y={0}
							text-anchor="middle"
							font-size="12"
							fill="#6b7280"
						>
							{formatDate(date)}
						</text>
					{/each}
				</g>
				
				<!-- Task labels -->
				<g class="task-labels" transform="translate(10, {margin.top})">
					{#each tasks as task}
						<text
							x={0}
							y={(yScale(task.id) || 0) + barHeight / 2 + 5}
							font-size="14"
							fill="#374151"
						>
							{task.title}
						</text>
					{/each}
				</g>
				
				<!-- Dependencies -->
				{#if showDependencies}
					<g class="dependencies" transform="translate({margin.left}, {margin.top})">
						{#each tasks as task}
							{#each task.dependencies as depId}
								{@const depTask = tasks.find(t => t.id === depId)}
								{#if depTask}
									<path
										d={getDepPath(depTask, task)}
										stroke="#9ca3af"
										stroke-width="2"
										fill="none"
										marker-end="url(#arrowhead)"
									/>
								{/if}
							{/each}
						{/each}
						
						<defs>
							<marker
								id="arrowhead"
								markerWidth="10"
								markerHeight="10"
								refX="9"
								refY="3"
								orient="auto"
							>
								<polygon
									points="0 0, 10 3, 0 6"
									fill="#9ca3af"
								/>
							</marker>
						</defs>
					</g>
				{/if}
				
				<!-- Task bars -->
				<g class="task-bars" transform="translate({margin.left}, {margin.top})">
					{#each tasks as task}
						{@const taskWidth = timeScale(task.end_date) - timeScale(task.start_date)}
						{@const taskY = yScale(task.id) || 0}
						
						<g
							class="task-group"
							on:click={() => handleTaskClick(task)}
							on:keydown={(e) => e.key === 'Enter' && handleTaskClick(task)}
							role="button"
							tabindex="0"
						>
							<!-- Task bar -->
							<rect
								x={timeScale(task.start_date)}
								y={taskY}
								width={taskWidth}
								height={barHeight}
								fill={getTaskColor(task)}
								rx="3"
								opacity="0.8"
								class="cursor-pointer hover:opacity-100"
							/>
							
							<!-- Progress bar -->
							{#if showProgress && task.progress > 0}
								<rect
									x={timeScale(task.start_date)}
									y={taskY + barHeight - 5}
									width={taskWidth * (task.progress / 100)}
									height="5"
									fill="#10b981"
									rx="2"
								/>
							{/if}
							
							<!-- Agent/Assignee indicator -->
							{#if task.assignedAgent || task.assignee}
								<text
									x={timeScale(task.start_date) + 5}
									y={taskY + barHeight / 2 + 5}
									font-size="10"
									fill="white"
									font-weight="bold"
								>
									{task.assignedAgent ? '🤖' : '👤'}
								</text>
							{/if}
						</g>
					{/each}
				</g>
				
				<!-- Milestones -->
				<g class="milestones" transform="translate({margin.left}, {margin.top})">
					{#each milestones as milestone}
						<g>
							<polygon
								points="{timeScale(milestone.date) - 7},0 {timeScale(milestone.date)},7 {timeScale(milestone.date) + 7},0 {timeScale(milestone.date)},−7"
								fill="#dc2626"
							/>
							<text
								x={timeScale(milestone.date)}
								y={-15}
								text-anchor="middle"
								font-size="12"
								fill="#dc2626"
								font-weight="bold"
							>
								{milestone.title}
							</text>
						</g>
					{/each}
				</g>
				
				<!-- Today line -->
				{#if timeScale}
					{@const today = new Date()}
					{@const todayX = timeScale(today)}
					{#if todayX >= 0 && todayX <= chartWidth}
						<line
							x1={margin.left + todayX}
							y1={margin.top}
							x2={margin.left + todayX}
							y2={margin.top + chartHeight}
							stroke="#ef4444"
							stroke-width="2"
							stroke-dasharray="5,5"
						/>
						<text
							x={margin.left + todayX}
							y={margin.top - 20}
							text-anchor="middle"
							fill="#ef4444"
							font-size="12"
							font-weight="bold"
						>
							Today
						</text>
					{/if}
				{/if}
			</svg>
		{/if}
	</div>
	
	<!-- Task details panel -->
	{#if selectedTask}
		<div class="task-details-panel">
			<div class="panel-header">
				<h3 class="font-semibold">{selectedTask.title}</h3>
				<button on:click={() => selectedTask = null} class="close-btn" aria-label="Close task details">×</button>
			</div>
			<div class="panel-content">
				<p><strong>Status:</strong> {selectedTask.status}</p>
				<p><strong>Priority:</strong> {selectedTask.priority}</p>
				<p><strong>Progress:</strong> {selectedTask.progress}%</p>
				<p><strong>Start:</strong> {selectedTask.start_date.toLocaleDateString()}</p>
				<p><strong>End:</strong> {selectedTask.end_date.toLocaleDateString()}</p>
				{#if selectedTask.assignedAgent}
					<p><strong>AI Agent:</strong> {selectedTask.assignedAgent}</p>
				{/if}
				{#if selectedTask.assignee}
					<p><strong>Assignee:</strong> {selectedTask.assignee}</p>
				{/if}
			</div>
		</div>
	{/if}
</div>

<style>
	.gantt-chart-container {
		display: flex;
		flex-direction: column;
		height: 100%;
		@apply bg-white border border-surface-200;
		border-radius: 8px;
		padding: 1rem;
		transition: background-color 0.3s, border-color 0.3s;
	}
	
	.gantt-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
		padding-bottom: 1rem;
		@apply border-b border-surface-200;
	}
	
	.gantt-controls {
		display: flex;
		gap: 1rem;
		align-items: center;
	}
	
	.view-mode-selector {
		display: flex;
	}
	
	.view-mode-selector button {
		@apply bg-surface-50 text-surface-500;
		transition: all 0.2s;
	}
	
	.view-mode-selector button.active {
		@apply bg-primary-600 text-white;
	}
	
	.gantt-chart {
		flex: 1;
		overflow: auto;
		min-height: 400px;
	}
	
	.task-details-panel {
		position: fixed;
		right: 20px;
		top: 50%;
		transform: translateY(-50%);
		@apply bg-white border border-surface-200;
		border-radius: 8px;
		padding: 1rem;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
		min-width: 250px;
		z-index: 100;
	}
	
	.panel-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
		padding-bottom: 0.5rem;
		@apply border-b border-surface-200;
	}
	
	.close-btn {
		background: none;
		border: none;
		font-size: 24px;
		cursor: pointer;
		@apply text-surface-500 hover:text-surface-800;
		transition: color 0.2s;
	}
	
	.panel-content p {
		margin: 0.5rem 0;
		font-size: 14px;
		@apply text-surface-600;
	}
	
	label {
		cursor: pointer;
		user-select: none;
		@apply text-surface-600;
	}
	
	/* SVG elements dynamic colors */
	:global(.gantt-chart svg text) {
		@apply fill-surface-300;
	}
	
	:global(.gantt-chart svg line) {
		@apply stroke-surface-600;
	}
</style>