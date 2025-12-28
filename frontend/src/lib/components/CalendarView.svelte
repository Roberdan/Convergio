<script lang="ts">
	import { onMount } from 'svelte';
	
	export let projectId: string;
	
	interface Task {
		id: string;
		title: string;
		description?: string;
		start_date?: string;
		due_date?: string;
		status: string;
		priority: string;
		assignee?: string;
		assignedAgent?: string;
		is_milestone: boolean;
	}
	
	interface CalendarDay {
		date: Date;
		day: number;
		isCurrentMonth: boolean;
		isToday: boolean;
		tasks: Task[];
		milestones: Task[];
	}
	
	let currentDate = new Date();
	let currentMonth = currentDate.getMonth();
	let currentYear = currentDate.getFullYear();
	let calendarDays: CalendarDay[] = [];
	let tasks: Task[] = [];
	let selectedDay: CalendarDay | null = null;
	let showTaskDialog = false;
	let viewMode: 'month' | 'week' | 'day' = 'month';
	
	const monthNames = [
		'January', 'February', 'March', 'April', 'May', 'June',
		'July', 'August', 'September', 'October', 'November', 'December'
	];
	
	const weekDays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
	
	onMount(async () => {
		await loadTasks();
		generateCalendar();
	});
	
	async function loadTasks() {
		try {
			const response = await fetch(`/api/v1/pm/tasks?project_id=${projectId}`);
			if (response.ok) {
				tasks = await response.json();
			}
		} catch {
			// Silent failure
		}
	}
	
	function generateCalendar() {
		calendarDays = [];
		const firstDay = new Date(currentYear, currentMonth, 1);
		const lastDay = new Date(currentYear, currentMonth + 1, 0);
		const prevLastDay = new Date(currentYear, currentMonth, 0);
		
		const firstDayOfWeek = firstDay.getDay();
		const daysInMonth = lastDay.getDate();
		const daysInPrevMonth = prevLastDay.getDate();
		
		// Previous month days
		for (let i = firstDayOfWeek - 1; i >= 0; i--) {
			const date = new Date(currentYear, currentMonth - 1, daysInPrevMonth - i);
			calendarDays.push(createCalendarDay(date, false));
		}
		
		// Current month days
		for (let day = 1; day <= daysInMonth; day++) {
			const date = new Date(currentYear, currentMonth, day);
			calendarDays.push(createCalendarDay(date, true));
		}
		
		// Next month days (fill to 42 days for 6 weeks)
		const remainingDays = 42 - calendarDays.length;
		for (let day = 1; day <= remainingDays; day++) {
			const date = new Date(currentYear, currentMonth + 1, day);
			calendarDays.push(createCalendarDay(date, false));
		}
	}
	
	function createCalendarDay(date: Date, isCurrentMonth: boolean): CalendarDay {
		const today = new Date();
		const isToday = 
			date.getDate() === today.getDate() &&
			date.getMonth() === today.getMonth() &&
			date.getFullYear() === today.getFullYear();
		
		// Filter tasks for this day
		const dayTasks = tasks.filter(task => {
			if (task.is_milestone && task.due_date) {
				const dueDate = new Date(task.due_date);
				return isSameDay(dueDate, date);
			}
			
			if (task.start_date && task.due_date) {
				const startDate = new Date(task.start_date);
				const dueDate = new Date(task.due_date);
				return date >= startDate && date <= dueDate;
			}
			
			if (task.due_date) {
				const dueDate = new Date(task.due_date);
				return isSameDay(dueDate, date);
			}
			
			return false;
		});
		
		const milestones = dayTasks.filter(t => t.is_milestone);
		const regularTasks = dayTasks.filter(t => !t.is_milestone);
		
		return {
			date,
			day: date.getDate(),
			isCurrentMonth,
			isToday,
			tasks: regularTasks,
			milestones
		};
	}
	
	function isSameDay(date1: Date, date2: Date): boolean {
		return date1.getDate() === date2.getDate() &&
			   date1.getMonth() === date2.getMonth() &&
			   date1.getFullYear() === date2.getFullYear();
	}
	
	function previousMonth() {
		if (currentMonth === 0) {
			currentMonth = 11;
			currentYear--;
		} else {
			currentMonth--;
		}
		generateCalendar();
	}
	
	function nextMonth() {
		if (currentMonth === 11) {
			currentMonth = 0;
			currentYear++;
		} else {
			currentMonth++;
		}
		generateCalendar();
	}
	
	function goToToday() {
		const today = new Date();
		currentMonth = today.getMonth();
		currentYear = today.getFullYear();
		generateCalendar();
	}
	
	function selectDay(day: CalendarDay) {
		selectedDay = day;
		if (day.tasks.length > 0 || day.milestones.length > 0) {
			showTaskDialog = true;
		}
	}
	
	function getTaskColor(task: Task): string {
		if (task.status === 'completed') return 'bg-green-100 text-green-800';
		if (task.status === 'in_progress') return 'bg-blue-100 text-blue-800';
		if (task.status === 'blocked') return 'bg-red-100 text-red-800';
		if (task.priority === 'critical') return 'bg-red-200 text-red-900';
		if (task.priority === 'high') return 'bg-orange-100 text-orange-800';
		return 'bg-surface-100 text-surface-800';
	}
	
	function getPriorityIcon(priority: string): string {
		switch (priority) {
			case 'critical': return '🔴';
			case 'high': return '🟠';
			case 'medium': return '🟡';
			case 'low': return '🟢';
			default: return '⚪';
		}
	}
	
	async function createTask(date: Date) {
		// Navigate to task creation with pre-filled date
		window.location.href = `/pm/tasks/new?project_id=${projectId}&due_date=${date.toISOString()}`;
	}
</script>

<div class="calendar-container">
	<div class="calendar-header">
		<div class="header-left">
			<h2 class="text-xl font-semibold">
				{monthNames[currentMonth]} {currentYear}
			</h2>
		</div>
		
		<div class="header-controls">
			<button on:click={previousMonth} class="nav-btn" aria-label="Previous month">
				<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
				</svg>
			</button>
			
			<button on:click={goToToday} class="today-btn" aria-label="Go to today">
				Today
			</button>
			
			<button on:click={nextMonth} class="nav-btn" aria-label="Next month">
				<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
				</svg>
			</button>
			
			<div class="view-selector ml-4">
				<button
					class:active={viewMode === 'month'}
					on:click={() => viewMode = 'month'}
					class="px-3 py-1 rounded-l border"
				>
					Month
				</button>
				<button
					class:active={viewMode === 'week'}
					on:click={() => viewMode = 'week'}
					class="px-3 py-1 border-t border-b"
				>
					Week
				</button>
				<button
					class:active={viewMode === 'day'}
					on:click={() => viewMode = 'day'}
					class="px-3 py-1 rounded-r border"
				>
					Day
				</button>
			</div>
		</div>
	</div>
	
	{#if viewMode === 'month'}
		<div class="calendar-grid">
			<!-- Week day headers -->
			{#each weekDays as day}
				<div class="weekday-header">
					{day}
				</div>
			{/each}
			
			<!-- Calendar days -->
			{#each calendarDays as day}
				<div
					class="calendar-day"
					class:current-month={day.isCurrentMonth}
					class:today={day.isToday}
					class:has-tasks={day.tasks.length > 0}
					on:click={() => selectDay(day)}
					on:keydown={(e) => (e.key === 'Enter' || e.key === ' ') && selectDay(day)}
					role="button"
					tabindex="0"
					aria-label={`Select day ${day.date.toDateString()}`}
				>
					<div class="day-header">
						<span class="day-number">{day.day}</span>
						{#if day.milestones.length > 0}
							<span class="milestone-indicator" title="{day.milestones.length} milestone(s)">
								💎
							</span>
						{/if}
					</div>
					
					<div class="day-content">
						{#if day.tasks.length > 0}
							<div class="task-count">
								{day.tasks.length} task{day.tasks.length > 1 ? 's' : ''}
							</div>
						{/if}
						
						{#each day.tasks.slice(0, 3) as task}
							<div class="task-item {getTaskColor(task)}">
								<span class="task-icon">
									{task.assignedAgent ? '🤖' : ''}
									{getPriorityIcon(task.priority)}
								</span>
								<span class="task-title">{task.title}</span>
							</div>
						{/each}
						
						{#if day.tasks.length > 3}
							<div class="more-tasks">
								+{day.tasks.length - 3} more
							</div>
						{/if}
					</div>
					
					{#if day.isCurrentMonth}
						<button
							on:click|stopPropagation={() => createTask(day.date)}
							class="add-task-btn"
							title="Add task"
							aria-label="Add task"
						>
							+
						</button>
					{/if}
				</div>
			{/each}
		</div>
	{:else if viewMode === 'week'}
		<div class="week-view">
			<!-- Week view implementation -->
			<p class="text-center py-8 text-surface-500">Week view coming soon...</p>
		</div>
	{:else if viewMode === 'day'}
		<div class="day-view">
			<!-- Day view implementation -->
			<p class="text-center py-8 text-surface-500">Day view coming soon...</p>
		</div>
	{/if}
	
	<!-- Task details dialog -->
	{#if showTaskDialog && selectedDay}
			<div 
				class="task-dialog-overlay" 
				on:click={() => showTaskDialog = false}
				role="button"
				tabindex="0"
				aria-label="Close tasks dialog"
				on:keydown={(e) => (e.key === 'Enter' || e.key === ' ') && (showTaskDialog = false)}
			>
						<div 
							class="task-dialog" 
							on:click|stopPropagation 
							role="dialog" 
							aria-modal="true"
							tabindex="-1"
							aria-label="Tasks for selected day"
							on:keydown={(e) => (e.key === 'Escape') && (showTaskDialog = false)}
						>
				<div class="dialog-header">
					<h3 class="text-lg font-semibold">
						Tasks for {selectedDay.date.toLocaleDateString()}
					</h3>
					<button on:click={() => showTaskDialog = false} class="close-btn">
						×
					</button>
				</div>
				
				<div class="dialog-content">
					{#if selectedDay.milestones.length > 0}
						<div class="milestone-section">
							<h4 class="section-title">💎 Milestones</h4>
							{#each selectedDay.milestones as milestone}
								<div class="task-detail-item milestone">
									<strong>{milestone.title}</strong>
									{#if milestone.description}
										<p class="text-sm text-surface-600">{milestone.description}</p>
									{/if}
								</div>
							{/each}
						</div>
					{/if}
					
					{#if selectedDay.tasks.length > 0}
						<div class="tasks-section">
							<h4 class="section-title">📋 Tasks</h4>
							{#each selectedDay.tasks as task}
								<div class="task-detail-item {getTaskColor(task)}">
									<div class="task-header-detail">
										<strong>{task.title}</strong>
										<span class="status-badge">{task.status}</span>
									</div>
									{#if task.description}
										<p class="text-sm mt-1">{task.description}</p>
									{/if}
									<div class="task-meta">
										{#if task.assignedAgent}
											<span class="meta-item">🤖 {task.assignedAgent}</span>
										{/if}
										{#if task.assignee}
											<span class="meta-item">👤 {task.assignee}</span>
										{/if}
										<span class="meta-item">{getPriorityIcon(task.priority)} {task.priority}</span>
									</div>
								</div>
							{/each}
						</div>
					{/if}
				</div>
				
				<div class="dialog-footer">
					<button
						on:click={() => selectedDay && createTask(selectedDay.date)}
						class="btn-primary"
					>
						Add New Task
					</button>
				</div>
			</div>
		</div>
	{/if}
</div>

<style>
	.calendar-container {
		background: white;
		border-radius: 8px;
		padding: 1.5rem;
		height: 100%;
		display: flex;
		flex-direction: column;
	}
	
	.calendar-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1.5rem;
	}
	
	.header-controls {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	
	.nav-btn, .today-btn {
		padding: 0.5rem 1rem;
		border: 1px solid #e5e7eb;
		background: white;
		border-radius: 6px;
		cursor: pointer;
		transition: all 0.2s;
	}
	
	.nav-btn:hover, .today-btn:hover {
		background: #f3f4f6;
	}
	
	.view-selector {
		display: flex;
	}
	
	.view-selector button {
		background: white;
		color: #6b7280;
		transition: all 0.2s;
	}
	
	.view-selector button.active {
		background: #3b82f6;
		color: white;
	}
	
	.calendar-grid {
		display: grid;
		grid-template-columns: repeat(7, 1fr);
		gap: 1px;
		background: #e5e7eb;
		border: 1px solid #e5e7eb;
		border-radius: 8px;
		overflow: hidden;
		flex: 1;
	}
	
	.weekday-header {
		background: #f9fafb;
		padding: 0.75rem;
		text-align: center;
		font-weight: 600;
		color: #374151;
		font-size: 0.875rem;
	}
	
	.calendar-day {
		background: white;
		min-height: 100px;
		padding: 0.5rem;
		position: relative;
		cursor: pointer;
		transition: all 0.2s;
	}
	
	.calendar-day:hover {
		background: #f9fafb;
	}
	
	.calendar-day.current-month {
		background: white;
	}
	
	.calendar-day:not(.current-month) {
		background: #fafafa;
		color: #9ca3af;
	}
	
	.calendar-day.today {
		background: #eff6ff;
	}
	
	.calendar-day.today .day-number {
		background: #3b82f6;
		color: white;
		width: 28px;
		height: 28px;
		border-radius: 50%;
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
	
	.day-header {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		margin-bottom: 0.25rem;
	}
	
	.day-number {
		font-weight: 500;
		font-size: 0.875rem;
	}
	
	.milestone-indicator {
		font-size: 0.75rem;
	}
	
	.day-content {
		font-size: 0.75rem;
	}
	
	.task-count {
		color: #6b7280;
		margin-bottom: 0.25rem;
	}
	
	.task-item {
		padding: 0.125rem 0.25rem;
		border-radius: 3px;
		margin-bottom: 0.125rem;
		display: flex;
		align-items: center;
		gap: 0.25rem;
		overflow: hidden;
		white-space: nowrap;
		text-overflow: ellipsis;
	}
	
	.task-icon {
		font-size: 0.625rem;
	}
	
	.task-title {
		overflow: hidden;
		text-overflow: ellipsis;
		flex: 1;
	}
	
	.more-tasks {
		color: #6b7280;
		font-size: 0.625rem;
		margin-top: 0.25rem;
	}
	
	.add-task-btn {
		position: absolute;
		top: 0.25rem;
		right: 0.25rem;
		width: 20px;
		height: 20px;
		border-radius: 50%;
		border: 1px solid #d1d5db;
		background: white;
		color: #6b7280;
		font-size: 14px;
		line-height: 1;
		cursor: pointer;
		opacity: 0;
		transition: all 0.2s;
	}
	
	.calendar-day:hover .add-task-btn {
		opacity: 1;
	}
	
	.add-task-btn:hover {
		background: #3b82f6;
		color: white;
		border-color: #3b82f6;
	}
	
	.task-dialog-overlay {
		position: fixed;
		inset: 0;
		background: rgba(0, 0, 0, 0.5);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1000;
	}
	
	.task-dialog {
		background: white;
		border-radius: 12px;
		width: 90%;
		max-width: 600px;
		max-height: 80vh;
		display: flex;
		flex-direction: column;
	}
	
	.dialog-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1.5rem;
		border-bottom: 1px solid #e5e7eb;
	}
	
	.close-btn {
		background: none;
		border: none;
		font-size: 24px;
		cursor: pointer;
		color: #6b7280;
	}
	
	.dialog-content {
		padding: 1.5rem;
		overflow-y: auto;
		flex: 1;
	}
	
	.section-title {
		font-weight: 600;
		margin-bottom: 0.75rem;
		color: #374151;
	}
	
	.milestone-section, .tasks-section {
		margin-bottom: 1.5rem;
	}
	
	.task-detail-item {
		padding: 0.75rem;
		border-radius: 6px;
		margin-bottom: 0.5rem;
	}
	
	.task-detail-item.milestone {
		background: #fef3c7;
		border: 1px solid #fcd34d;
	}
	
	.task-header-detail {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}
	
	.status-badge {
		font-size: 0.75rem;
		padding: 0.125rem 0.5rem;
		border-radius: 12px;
		background: #e5e7eb;
	}
	
	.task-meta {
		display: flex;
		gap: 1rem;
		margin-top: 0.5rem;
		font-size: 0.75rem;
		color: #6b7280;
	}
	
	.dialog-footer {
		padding: 1.5rem;
		border-top: 1px solid #e5e7eb;
	}
	
	.btn-primary {
		background: #3b82f6;
		color: white;
		padding: 0.5rem 1rem;
		border-radius: 6px;
		border: none;
		cursor: pointer;
		font-weight: 500;
		transition: background 0.2s;
	}
	
	.btn-primary:hover {
		background: #2563eb;
	}
</style>