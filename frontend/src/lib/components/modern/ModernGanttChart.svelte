<script lang="ts">
  import { onMount, createEventDispatcher } from 'svelte';
  import { scaleTime, scaleLinear } from 'd3-scale';
  import { extent } from 'd3-array';
  import { timeFormat } from 'd3-time-format';
  
  export let projectId: string;
  export let tasks: any[] = [];
  export let timeRange: 'week' | 'month' | 'quarter' = 'month';
  
  const dispatch = createEventDispatcher();
  
  let svgWidth = 1200;
  let svgHeight = 600;
  let ganttContainer: HTMLDivElement;
  let loading = true;
  let selectedTask: any = null;
  let aiSuggestions: any[] = [];
  
  // Modern Glassmorphism colors
  const colors = {
    primary: '#3b82f6',
    secondary: '#8b5cf6', 
    success: '#10b981',
    warning: '#f59e0b',
    danger: '#ef4444',
    background: '#ffffff',
    glass: '#ffffff',
    text: '#111827',
    textSecondary: '#6b7280'
  };
  
  // Only real tasks from backend
  $: displayTasks = tasks;
  
  // Time scale setup (robust when no tasks are present)
  $: now = new Date();
  $: fallbackExtent = [now, new Date(now.getTime() + 30 * 24 * 60 * 60 * 1000)] as [Date, Date];
  $: datePairs = (displayTasks || []).flatMap((d: any) => [d.start, d.end]).filter(Boolean) as Date[];
  $: timeExtent = (datePairs.length ? extent(datePairs) : fallbackExtent) as [Date, Date];
  $: xScale = scaleTime()
    .domain(timeExtent)
    .range([200, svgWidth - 50]);
  
  $: yScale = scaleLinear()
    .domain([0, (displayTasks || []).length])
    .range([50, svgHeight - 50]);
  
  const formatDate = timeFormat('%b %d');
  const formatDateFull = timeFormat('%Y-%m-%d');
  
  onMount(async () => {
    await loadProjectTasks();
    await getAISuggestions();
    loading = false;
  });
  
  async function loadProjectTasks() {
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:9000';
      // Prefer filtered activities endpoint to avoid empty details
      const response = await fetch(`${apiUrl}/api/v1/projects/activities?engagement_id=${projectId}`);
      if (response.ok) {
        const projectData = await response.json();
        const list = Array.isArray(projectData.activities) ? projectData.activities : [];
        tasks = list.map((activity: any) => {
          const progressValue = typeof activity.progress === 'number' ? (activity.progress > 1 ? activity.progress / 100 : activity.progress) : 0;
          const startDate = activity.start_date || activity.created_at;
          const endDate = activity.end_date || activity.due_date || activity.updated_at;
          return {
            id: activity.id,
            name: activity.title || 'Untitled',
            start: new Date(startDate || Date.now()),
            end: new Date(endDate || Date.now() + 7 * 24 * 60 * 60 * 1000),
            progress: progressValue,
            priority: activity.priority || 'medium',
            assignedAgent: activity.assigned_agent || 'Unassigned',
            dependencies: activity.dependencies || [],
            status: activity.status || 'planning',
            aiInsights: activity.ai_insights || ''
          };
        });
      }
    } catch {
      // Silent failure
    }
  }
  
  async function getAISuggestions() {
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:9000';
      const response = await fetch(`${apiUrl}/api/v1/projects/engagements/${projectId}/ai-suggestions`);
      if (response.ok) {
        const data = await response.json();
        aiSuggestions = Array.isArray(data) ? data : (data.suggestions || []);
      } else {
        aiSuggestions = [];
      }
    } catch {
      // Silent failure
      aiSuggestions = [];
    }
  }
  
  function handleTaskClick(task: any) {
    selectedTask = task;
    dispatch('taskSelected', task);
  }

  function handleTaskDrag(task: any, e?: MouseEvent) {
    // Implement drag functionality for task scheduling
  }
  
  function getPriorityColor(priority: string): string {
    switch (priority) {
      case 'critical': return colors.danger;
      case 'high': return colors.warning;
      case 'medium': return colors.primary;
      case 'low': return colors.success;
      default: return colors.secondary;
    }
  }
  
  function getStatusIcon(status: string): string {
    switch (status) {
      case 'completed': return '✅';
      case 'in_progress': return '🚀';
      case 'planning': return '📋';
      case 'waiting': return '⏳';
      case 'blocked': return '🚫';
      default: return '📝';
    }
  }
  
  async function askAliOptimization() {
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:9000';
      const response = await fetch(`${apiUrl}/api/v1/agents/ali/optimize-project`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_id: projectId,
          current_tasks: displayTasks,
          optimization_type: 'timeline'
        })
      });
      
      if (response.ok) {
        const optimization = await response.json();
        alert(`🤖 Ali's Optimization:\n\n${optimization.recommendation}`);
      }
    } catch {
      // Silent failure
      alert('Optimization service unavailable right now.');
    }
  }
</script>

<div class="modern-gantt-container" bind:this={ganttContainer}>
  <!-- Modern Header with AI Integration -->
  <div class="gantt-header">
    <div class="header-left">
      <h2 class="gantt-title">
        <span class="title-icon">📊</span>
        Project Timeline Intelligence
      </h2>
      <p class="gantt-subtitle">AI-powered Gantt chart with smart optimization</p>
    </div>
    
    <div class="header-actions">
      <button 
        class="ai-button"
        on:click={askAliOptimization}
      >
        <span class="ai-icon">🤖</span>
        Ask Ali to Optimize
      </button>
      
      <div class="view-controls">
        <button 
          class="control-btn"
          class:active={timeRange === 'week'}
          on:click={() => timeRange = 'week'}
        >
          Week
        </button>
        <button 
          class="control-btn"
          class:active={timeRange === 'month'}
          on:click={() => timeRange = 'month'}
        >
          Month
        </button>
        <button 
          class="control-btn"
          class:active={timeRange === 'quarter'}
          on:click={() => timeRange = 'quarter'}
        >
          Quarter
        </button>
      </div>
    </div>
  </div>
  
  <!-- AI Suggestions Panel -->
  {#if aiSuggestions.length > 0}
    <div class="ai-suggestions">
      <h3 class="suggestions-title">
        <span class="ai-icon">🧠</span>
        AI Insights & Recommendations
      </h3>
      <div class="suggestions-grid">
        {#each aiSuggestions as suggestion}
          <div class="suggestion-card" class:high-impact={suggestion.impact === 'high'}>
            <div class="suggestion-type">{suggestion.type.toUpperCase()}</div>
            <p class="suggestion-message">{suggestion.message}</p>
            <div class="suggestion-meta">
              <span class="confidence">Confidence: {Math.round(suggestion.confidence * 100)}%</span>
              <span class="impact impact-{suggestion.impact}">{suggestion.impact.toUpperCase()}</span>
            </div>
          </div>
        {/each}
      </div>
    </div>
  {/if}
  
  <!-- Main Gantt Chart SVG -->
  <div class="gantt-chart-wrapper">
    {#if loading}
      <div class="loading-overlay">
        <div class="loading-spinner"></div>
        <p>Loading project timeline...</p>
      </div>
    {:else}
      <svg width={svgWidth} height={svgHeight} class="gantt-svg">
        <!-- Background Grid -->
        <defs>
          <pattern id="grid" width="50" height="50" patternUnits="userSpaceOnUse">
            <path d="M 50 0 L 0 0 0 50" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="1"/>
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#grid)" />
        
        <!-- Time Axis -->
        <g class="time-axis">
          {#each xScale.ticks(8) as tick}
            <g transform="translate({xScale(tick)}, 0)">
              <line x1="0" y1="30" x2="0" y2={svgHeight - 30} stroke="rgba(255,255,255,0.2)" stroke-width="1"/>
              <text x="0" y="25" text-anchor="middle" fill={colors.textSecondary} font-size="12">
                {formatDate(tick)}
              </text>
            </g>
          {/each}
        </g>
        
        <!-- Task Bars with Glassmorphism Effect -->
        {#each displayTasks as task, i}
          <g 
            class="task-group" 
            transform="translate(0, {yScale(i)})"
            on:click={() => handleTaskClick(task)}
            on:mousedown={(e) => handleTaskDrag(task, e)}
            role="button"
            tabindex="0"
            aria-label={`Select task ${task.name}`}
            on:keydown={(e) => (e.key === 'Enter' || e.key === ' ') && handleTaskClick(task)}
          >
            <!-- Task Background Bar -->
            <rect
              x={xScale(task.start)}
              y="5"
              width={xScale(task.end) - xScale(task.start)}
              height="30"
              fill="rgba(255,255,255,0.05)"
              stroke="rgba(255,255,255,0.2)"
              stroke-width="1"
              rx="8"
              class="task-background"
            />
            
            <!-- Progress Bar -->
            <rect
              x={xScale(task.start)}
              y="5"
              width={(xScale(task.end) - xScale(task.start)) * task.progress}
              height="30"
              fill={getPriorityColor(task.priority)}
              rx="8"
              class="task-progress"
              style="filter: drop-shadow(0 4px 12px rgba({getPriorityColor(task.priority)}, 0.3))"
            />
            
            <!-- Task Label -->
            <text
              x={xScale(task.start) + 10}
              y="25"
              fill={colors.text}
              font-size="11"
              font-weight="500"
              class="task-label"
            >
              {getStatusIcon(task.status)} {task.name}
            </text>
            
            <!-- Progress Percentage -->
            <text
              x={xScale(task.end) - 35}
              y="25"
              fill={colors.text}
              font-size="10"
              text-anchor="middle"
              class="progress-text"
            >
              {Math.round(task.progress * 100)}%
            </text>
          </g>
        {/each}
        
        <!-- Dependencies Lines -->
        {#each displayTasks as task, i}
          {#each task.dependencies as depId}
            {@const depTask = displayTasks.find(t => t.id === depId)}
            {#if depTask}
              {@const depIndex = displayTasks.findIndex(t => t.id === depId)}
              <path
                d="M {xScale(depTask.end)} {yScale(depIndex) + 20} 
                   L {xScale(depTask.end) + 20} {yScale(depIndex) + 20}
                   L {xScale(depTask.end) + 20} {yScale(i) + 20}
                   L {xScale(task.start)} {yScale(i) + 20}"
                stroke={colors.secondary}
                stroke-width="2"
                fill="none"
                marker-end="url(#arrowhead)"
                class="dependency-line"
              />
            {/if}
          {/each}
        {/each}
        
        <!-- Arrow marker definition -->
        <defs>
          <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
            <polygon points="0 0, 10 3.5, 0 7" fill={colors.secondary} />
          </marker>
        </defs>
      </svg>
    {/if}
  </div>
  
  <!-- Task Details Panel -->
  {#if selectedTask}
    <div class="task-details-panel">
      <div class="panel-header">
        <h3>{selectedTask.name}</h3>
        <button class="close-btn" on:click={() => selectedTask = null}>×</button>
      </div>
      
      <div class="panel-content">
        <div class="detail-row">
          <span class="label">Assigned Agent:</span>
          <span class="value agent-badge">{selectedTask.assignedAgent}</span>
        </div>
        
        <div class="detail-row">
          <span class="label">Timeline:</span>
          <span class="value">{formatDateFull(selectedTask.start)} → {formatDateFull(selectedTask.end)}</span>
        </div>
        
        <div class="detail-row">
          <span class="label">Progress:</span>
          <div class="progress-bar-mini">
            <div 
              class="progress-fill-mini" 
              style="width: {selectedTask.progress * 100}%; background: {getPriorityColor(selectedTask.priority)}"
            ></div>
          </div>
          <span class="value">{Math.round(selectedTask.progress * 100)}%</span>
        </div>
        
        <div class="detail-row">
          <span class="label">Priority:</span>
          <span class="value priority-badge" style="background: {getPriorityColor(selectedTask.priority)}">
            {selectedTask.priority.toUpperCase()}
          </span>
        </div>
        
        <div class="detail-row">
          <span class="label">AI Insights:</span>
          <p class="ai-insight">{selectedTask.aiInsights}</p>
        </div>
        
        <div class="panel-actions">
          <button class="action-btn primary">Update Progress</button>
          <button class="action-btn secondary">Ask Agent</button>
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  .modern-gantt-container {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    border-radius: 16px;
    padding: 24px;
    min-height: 600px;
    position: relative;
    overflow: hidden;
  }
  
  .modern-gantt-container::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: 
      radial-gradient(circle at 20% 80%, rgba(99, 102, 241, 0.1) 0%, transparent 50%),
      radial-gradient(circle at 80% 20%, rgba(139, 92, 246, 0.1) 0%, transparent 50%);
    pointer-events: none;
    z-index: 0;
  }
  
  .gantt-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
    position: relative;
    z-index: 1;
  }
  
  .gantt-title {
    font-size: 24px;
    font-weight: 700;
    color: #f8fafc;
    margin: 0;
    display: flex;
    align-items: center;
    gap: 12px;
  }
  
  .title-icon {
    font-size: 28px;
  }
  
  .gantt-subtitle {
    color: #cbd5e1;
    margin: 4px 0 0 40px;
    font-size: 14px;
  }
  
  .header-actions {
    display: flex;
    align-items: center;
    gap: 16px;
  }
  
  .ai-button {
    background: rgba(99, 102, 241, 0.2);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(99, 102, 241, 0.3);
    color: #6366f1;
    padding: 12px 20px;
    border-radius: 12px;
    font-weight: 600;
    transition: all 0.3s ease;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  .ai-button:hover {
    background: rgba(99, 102, 241, 0.3);
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(99, 102, 241, 0.3);
  }
  
  .ai-icon {
    font-size: 18px;
  }
  
  .view-controls {
    display: flex;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 12px;
    padding: 4px;
    backdrop-filter: blur(12px);
  }
  
  .control-btn {
    padding: 8px 16px;
    border: none;
    background: transparent;
    color: #cbd5e1;
    border-radius: 8px;
    transition: all 0.3s ease;
    font-weight: 500;
  }
  
  .control-btn.active {
    background: rgba(99, 102, 241, 0.3);
    color: #6366f1;
  }
  
  .ai-suggestions {
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 24px;
    position: relative;
    z-index: 1;
  }
  
  .suggestions-title {
    color: #f8fafc;
    font-size: 18px;
    font-weight: 600;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 10px;
  }
  
  .suggestions-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 16px;
  }
  
  .suggestion-card {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 16px;
    transition: all 0.3s ease;
  }
  
  .suggestion-card.high-impact {
    border-color: rgba(239, 68, 68, 0.3);
    background: rgba(239, 68, 68, 0.05);
  }
  
  .suggestion-type {
    font-size: 10px;
    font-weight: 700;
    color: #6366f1;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 8px;
  }
  
  .suggestion-message {
    color: #f8fafc;
    font-size: 14px;
    margin-bottom: 12px;
    line-height: 1.5;
  }
  
  .suggestion-meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 12px;
  }
  
  .confidence {
    color: #cbd5e1;
  }
  
  .impact {
    padding: 4px 8px;
    border-radius: 6px;
    font-weight: 600;
  }
  
  .impact-high {
    background: rgba(239, 68, 68, 0.2);
    color: #fca5a5;
  }
  
  .impact-medium {
    background: rgba(245, 158, 11, 0.2);
    color: #fcd34d;
  }
  
  .gantt-chart-wrapper {
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 16px;
    overflow: hidden;
    position: relative;
    z-index: 1;
  }
  
  .gantt-svg {
    width: 100%;
    height: auto;
    background: transparent;
  }
  
  .task-group {
    cursor: pointer;
    transition: all 0.3s ease;
  }
  
  .task-group:hover .task-background {
    fill: rgba(255, 255, 255, 0.1);
  }
  
  .task-background {
    transition: all 0.3s ease;
  }
  
  .task-progress {
    transition: all 0.3s ease;
  }
  
  .task-label {
    pointer-events: none;
  }
  
  .dependency-line {
    opacity: 0.7;
    transition: all 0.3s ease;
  }
  
  .loading-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(15, 23, 42, 0.8);
    backdrop-filter: blur(8px);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    color: #f8fafc;
    z-index: 10;
  }
  
  .loading-spinner {
    width: 40px;
    height: 40px;
    border: 3px solid rgba(99, 102, 241, 0.2);
    border-top: 3px solid #6366f1;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-bottom: 16px;
  }
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
  
  .task-details-panel {
    position: fixed;
    top: 50%;
    right: 24px;
    transform: translateY(-50%);
    width: 320px;
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 16px;
    z-index: 100;
    overflow: hidden;
  }
  
  .panel-header {
    background: rgba(99, 102, 241, 0.2);
    padding: 16px 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .panel-header h3 {
    color: #f8fafc;
    font-size: 16px;
    font-weight: 600;
    margin: 0;
  }
  
  .close-btn {
    background: none;
    border: none;
    color: #f8fafc;
    font-size: 24px;
    cursor: pointer;
    padding: 0;
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .panel-content {
    padding: 20px;
  }
  
  .detail-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
  }
  
  .label {
    color: #cbd5e1;
    font-size: 14px;
    font-weight: 500;
  }
  
  .value {
    color: #f8fafc;
    font-size: 14px;
    text-align: right;
  }
  
  .agent-badge {
    background: rgba(139, 92, 246, 0.2);
    color: #a78bfa;
    padding: 4px 8px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 600;
  }
  
  .priority-badge {
    padding: 4px 8px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 700;
    color: white;
  }
  
  .progress-bar-mini {
    width: 80px;
    height: 8px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 4px;
    overflow: hidden;
  }
  
  .progress-fill-mini {
    height: 100%;
    transition: width 0.3s ease;
  }
  
  .ai-insight {
    color: #a78bfa;
    font-style: italic;
    font-size: 13px;
    margin: 8px 0 0 0;
    line-height: 1.4;
  }
  
  .panel-actions {
    display: flex;
    gap: 12px;
    margin-top: 20px;
  }
  
  .action-btn {
    flex: 1;
    padding: 10px 16px;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
  }
  
  .action-btn.primary {
    background: #6366f1;
    color: white;
  }
  
  .action-btn.secondary {
    background: rgba(255, 255, 255, 0.1);
    color: #f8fafc;
    border: 1px solid rgba(255, 255, 255, 0.2);
  }
  
  .action-btn:hover {
    transform: translateY(-2px);
  }
</style>