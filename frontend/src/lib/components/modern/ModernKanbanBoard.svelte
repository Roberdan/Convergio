<script lang="ts">
  import { onMount, createEventDispatcher } from 'svelte';
  import { dndzone } from 'svelte-dnd-action';
  
  export let projectId: string;
  
  const dispatch = createEventDispatcher();
  
  let loading = true;
  let error = '';
  let columns: any[] = [];
  let tasks: any[] = [];
  let availableAgents: any[] = [];
  let showNewTaskForm = false;
  let newTaskData = {
    title: '',
    description: '',
    priority: 'medium',
    assignedAgent: '',
    dueDate: '',
    tags: []
  };
  
  // Available tags for task creation
  const availableTags = [
    'research', 'strategy', 'design', 'frontend', 'backend', 'architecture',
    'security', 'performance', 'optimization', 'testing', 'documentation',
    'planning', 'development', 'review', 'deployment', 'maintenance'
  ];
  
  onMount(async () => {
    await Promise.all([
      loadProjectData(),
      loadAvailableAgents()
    ]);
  });
  
  async function loadProjectData() {
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:9000';
      // Prefer focused endpoint to ensure activities even when details is sparse
      const response = await fetch(`${apiUrl}/api/v1/projects/activities?engagement_id=${projectId}`);
      
      if (response.ok) {
        const data = await response.json();
        tasks = Array.isArray(data.activities) ? data.activities : [];
        
        // Create columns based on available task statuses
        const statuses = [...new Set(tasks.map(task => task.status))];
        columns = statuses.map(status => ({
          id: status,
          title: status.replace('_', ' ').toUpperCase(),
          tasks: tasks.filter(task => task.status === status)
        }));
        
        // Add empty columns for missing statuses
        const defaultStatuses = ['backlog', 'planning', 'in_progress', 'review', 'done'];
        defaultStatuses.forEach(status => {
          if (!columns.find(col => col.id === status)) {
            columns.push({
              id: status,
              title: status.replace('_', ' ').toUpperCase(),
              tasks: []
            });
          }
        });
        
        // Sort columns by default order
        const statusOrder: Record<string, number> = { 
          backlog: 0, 
          planning: 1, 
          in_progress: 2, 
          review: 3, 
          done: 4 
        };
        columns.sort((a, b) => (statusOrder[a.id] || 999) - (statusOrder[b.id] || 999));
        
      } else {
        error = 'Failed to load project data';
        columns = [];
        tasks = [];
      }
    } catch (err) {
      console.error('Error loading project data:', err);
      error = 'Failed to load project data';
      columns = [];
      tasks = [];
    } finally {
      loading = false;
    }
  }
  
  async function loadAvailableAgents() {
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:9000';
      const response = await fetch(`${apiUrl}/api/v1/agents`);
      
      if (response.ok) {
        const data = await response.json();
        availableAgents = data.agents || data || [];
      } else {
        console.error('Failed to load agents');
        availableAgents = [];
      }
    } catch (err) {
      console.error('Error loading agents:', err);
      availableAgents = [];
    }
  }
  
  async function getAIRecommendedAgent(taskTitle: string, taskDescription: string, taskTags: string[]) {
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:9000';
      const response = await fetch(`${apiUrl}/api/v1/agents/recommend`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          task_title: taskTitle,
          task_description: taskDescription,
          task_tags: taskTags,
          project_id: projectId
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        return data.recommended_agent || data.agent_id;
      }
    } catch (err) {
      console.error('Error getting AI recommendation:', err);
    }
    return null;
  }
  
  async function createNewTask() {
    if (!newTaskData.title.trim()) return;
    
    try {
      // Get AI recommendation for agent assignment
      const recommendedAgentId = await getAIRecommendedAgent(
        newTaskData.title, 
        newTaskData.description, 
        newTaskData.tags
      );
      
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:9000';
      const response = await fetch(`${apiUrl}/api/v1/projects/engagements/${projectId}/activities`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: newTaskData.title,
          description: newTaskData.description,
          priority: newTaskData.priority,
          assigned_agent: recommendedAgentId || newTaskData.assignedAgent,
          due_date: newTaskData.dueDate,
          tags: newTaskData.tags,
          status: 'backlog',
          progress: 0
        })
      });
      
      if (response.ok) {
        // Reload project data to show new task
        await loadProjectData();
        
        // Reset form
        newTaskData = {
          title: '',
          description: '',
          priority: 'medium',
          assignedAgent: '',
          dueDate: '',
          tags: []
        };
        
        showNewTaskForm = false;
        
        // Trigger change event
        dispatch('tasksUpdated', { columns, tasks });
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create task');
      }
    } catch (err) {
      console.error('Error creating task:', err);
      alert(`Failed to create task: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  }
  
  function toggleTag(tag: string) {
    if (newTaskData.tags.includes(tag)) {
      newTaskData.tags = newTaskData.tags.filter(t => t !== tag);
    } else {
      newTaskData.tags = [...newTaskData.tags, tag];
    }
  }
  
  function handleDndConsider(e: CustomEvent) {
    columns = e.detail.columns;
  }
  
  async function handleDndFinalize(e: CustomEvent) {
    columns = e.detail.columns;
    
    // Update task statuses based on new column positions
    const updatedTasks: any[] = [];
    columns.forEach(column => {
      column.tasks.forEach((task: any) => {
        if (task.status !== column.id) {
          task.status = column.id;
        }
        updatedTasks.push(task);
      });
    });
    
    tasks = updatedTasks;
    
    // Save changes to backend
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:9000';
      await fetch(`${apiUrl}/api/v1/projects/engagements/${projectId}/activities/batch-update`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ activities: updatedTasks })
      });
    } catch (err) {
      console.error('Failed to save task updates:', err);
      // Reload data to revert changes
      await loadProjectData();
    }
    
    dispatch('tasksUpdated', { columns, tasks });
  }
  
  function selectTask(task: any) {
    dispatch('taskSelected', { task });
  }
</script>

<!-- Modern Kanban Board -->
<div class="bg-white rounded-2xl shadow-lg border border-surface-200 overflow-hidden">
  <!-- Loading State -->
  {#if loading}
    <div class="flex items-center justify-center p-8">
      <div class="text-surface-500">Loading project data...</div>
    </div>
  {:else if error}
    <div class="bg-red-50 border border-red-200 rounded-xl p-4">
      <div class="text-red-800">{error}</div>
    </div>
  {:else}
    <!-- Kanban Board -->
    <div class="space-y-6">
      <!-- Board Header -->
      <div class="flex items-center justify-between">
        <h3 class="text-lg font-semibold text-surface-900">Project Tasks</h3>
        <div class="flex items-center space-x-4">
          <div class="text-sm text-surface-500">
            {tasks.length} total tasks
          </div>
          <button
            on:click={() => showNewTaskForm = true}
            class="inline-flex items-center px-3 py-2 text-sm font-medium text-green-700 bg-green-100 border border-green-200 rounded-lg hover:bg-green-200 transition-colors"
          >
            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
            </svg>
            New Task
          </button>
        </div>
      </div>
      
      <!-- Columns Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        {#each columns as column}
          <div class="bg-surface-50 rounded-xl p-4">
            <div class="flex items-center justify-between mb-4">
              <h4 class="font-medium text-surface-900">{column.title}</h4>
              <span class="text-sm text-surface-500 bg-white px-2 py-1 rounded-full">
                {column.tasks.length}
              </span>
            </div>
            
            <!-- Tasks in Column -->
            <div 
              use:dndzone={{ items: column.tasks }}
              on:consider={handleDndConsider}
              on:finalize={handleDndFinalize}
              class="space-y-3 min-h-[200px]"
            >
              {#each column.tasks as task (task.id)}
                <button 
                  type="button"
                  class="w-full text-left bg-white p-3 rounded-lg border border-surface-200 shadow-sm cursor-pointer hover:shadow-md transition-shadow"
                  on:click={() => selectTask(task)}
                >
                  <div class="font-medium text-surface-900 text-sm mb-1">{task.title || 'Untitled Task'}</div>
                  {#if task.description}
                    <div class="text-surface-600 text-xs mb-2 line-clamp-2">{task.description}</div>
                  {/if}
                  
                  <!-- Task Metadata -->
                  <div class="flex items-center justify-between text-xs text-surface-500">
                    {#if task.assigned_agent}
                      <span>👤 {task.assigned_agent}</span>
                    {/if}
                    {#if task.due_date}
                      <span>📅 {new Date(task.due_date).toLocaleDateString()}</span>
                    {/if}
                  </div>
                </button>
              {/each}
            </div>
          </div>
        {/each}
      </div>
    </div>
  {/if}
</div>

<!-- New Task Form Modal -->
{#if showNewTaskForm}
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded-2xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
      <div class="px-6 py-5 border-b border-surface-200">
        <div class="flex items-center justify-between">
          <h3 class="text-lg font-semibold text-surface-900">Create New Task</h3>
          <button
            on:click={() => showNewTaskForm = false}
            class="text-gray-400 hover:text-surface-600 transition-colors"
            aria-label="Close new task form"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
      
      <div class="px-6 py-4 space-y-4">
        <div>
          <label class="block text-sm font-medium text-surface-600 mb-2" for="mkb-title">Task Title *</label>
          <input
            id="mkb-title"
            type="text"
            bind:value={newTaskData.title}
            class="w-full px-3 py-2 border border-surface-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Enter task title"
          />
        </div>
        
        <div>
          <label class="block text-sm font-medium text-surface-600 mb-2" for="mkb-desc">Description</label>
          <textarea
            id="mkb-desc"
            bind:value={newTaskData.description}
            rows="3"
            class="w-full px-3 py-2 border border-surface-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Enter task description"
          ></textarea>
        </div>
        
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-surface-600 mb-2" for="mkb-priority">Priority</label>
            <select
              id="mkb-priority"
              bind:value={newTaskData.priority}
              class="w-full px-3 py-2 border border-surface-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-surface-600 mb-2" for="mkb-due">Due Date</label>
            <input
              id="mkb-due"
              type="date"
              bind:value={newTaskData.dueDate}
              class="w-full px-3 py-2 border border-surface-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>
        
        <fieldset>
          <legend class="block text-sm font-medium text-surface-600 mb-2">Tags</legend>
          <div class="flex flex-wrap gap-2" role="group" aria-label="Task tags">
            {#each availableTags as tag}
              <button
                type="button"
                on:click={() => toggleTag(tag)}
                class="px-3 py-1 rounded-full text-sm font-medium border transition-colors {newTaskData.tags.includes(tag) 
                  ? 'bg-blue-100 text-blue-800 border-blue-200' 
                  : 'bg-surface-100 text-surface-600 border-surface-200 hover:bg-surface-200'}"
              >
                {tag}
              </button>
            {/each}
          </div>
        </fieldset>
        
        {#if availableAgents.length > 0}
          <div>
            <label class="block text-sm font-medium text-surface-600 mb-2" for="mkb-agent-select">Manual Agent Assignment (Optional)</label>
            <select
              id="mkb-agent-select"
              bind:value={newTaskData.assignedAgent}
              class="w-full px-3 py-2 border border-surface-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">AI will recommend best agent</option>
              {#each availableAgents as agent}
                <option value={agent.id}>{agent.name || agent.title} - {agent.tier || agent.specialty}</option>
              {/each}
            </select>
            <p class="text-xs text-surface-500 mt-1">Leave empty for AI-powered agent recommendation based on task requirements</p>
          </div>
        {/if}
      </div>
      
      <div class="px-6 py-4 border-t border-surface-200 flex justify-end space-x-3">
        <button
          on:click={() => showNewTaskForm = false}
          class="px-4 py-2 text-surface-600 bg-surface-100 rounded-lg hover:bg-surface-200 transition-colors"
        >
          Cancel
        </button>
        <button
          on:click={createNewTask}
          disabled={!newTaskData.title.trim()}
          class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Create Task
        </button>
      </div>
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
  
  /* Custom scrollbar */
  ::-webkit-scrollbar {
    width: 6px;
    height: 6px;
  }
  
  ::-webkit-scrollbar-track {
    background: transparent;
  }
  
  ::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 3px;
  }
  
  ::-webkit-scrollbar-thumb:hover {
    background: #94a3b8;
  }
</style>