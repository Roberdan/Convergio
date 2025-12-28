<script lang="ts">
  import { onMount } from 'svelte';
  import { workflowsService, type Workflow, type RecentExecution } from '$lib/services/workflowsService';
  import WorkflowEditor from './WorkflowEditor.svelte';

  let workflows: Workflow[] = [];
  let recentExecutions: RecentExecution[] = [];
  let loading = true;
  let error: string | null = null;
  let selectedWorkflow: any = null;
  let showDetails = false;
  let executingWorkflow = false;
  let showEditor = false;
  let editingWorkflowId: string | null = null;

  function getStatusColor(status: string): string {
    switch (status) {
      case 'completed': return 'text-green-600 bg-green-50';
      case 'running': return 'text-blue-600 bg-blue-50';
      case 'failed': return 'text-red-600 bg-red-50';
      case 'cancelled': return 'text-surface-600 bg-surface-50';
      case 'pending': return 'text-yellow-600 bg-yellow-50';
      case 'active': return 'text-green-600 bg-green-50';
      case 'inactive': return 'text-surface-600 bg-surface-50';
      case 'draft': return 'text-yellow-600 bg-yellow-50';
      default: return 'text-surface-600 bg-surface-50';
    }
  }

  function formatDuration(seconds: number): string {
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
    return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
  }

  function formatDate(dateString: string): string {
    return new Date(dateString).toLocaleDateString() + ' ' + new Date(dateString).toLocaleTimeString();
  }

  async function loadWorkflowsData() {
    try {
      loading = true;
      error = null;
      
      const [workflowsData, executionsData] = await Promise.all([
        workflowsService.getWorkflows(),
        workflowsService.getRecentExecutions()
      ]);
      
      workflows = workflowsData || [];
      recentExecutions = executionsData || [];
    } catch {
      // Silent failure
      error = 'Failed to load workflows data';
    } finally {
      loading = false;
    }
  }

  onMount(loadWorkflowsData);

  async function viewWorkflowDetails(workflowId: string) {
    try {
      const details = await workflowsService.getWorkflowDetails(workflowId);
      selectedWorkflow = details;
      showDetails = true;
    } catch {
      // Silent failure
      error = 'Failed to load workflow details';
    }
  }

  async function executeWorkflow(workflowId: string) {
    const userRequest = prompt('Describe what you want to analyze:');
    if (!userRequest) return;
    
    try {
      executingWorkflow = true;
      const result = await fetch('http://localhost:9000/api/v1/workflows/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          workflow_id: workflowId,
          user_request: userRequest,
          user_id: 'dashboard-user'
        })
      });
      
      if (result.ok) {
        const data = await result.json();
        alert(`✅ Workflow started! Execution ID: ${data.execution_id}`);
        loadWorkflowsData();
      }
    } catch {
      // Silent failure
      alert('Failed to start workflow');
    } finally {
      executingWorkflow = false;
    }
  }
  
  function openEditor(workflowId: string | null = null) {
    editingWorkflowId = workflowId;
    showEditor = true;
  }
  
  async function handleSaveWorkflow(workflow: any) {
    try {
      // Save workflow via API
      const response = await fetch('http://localhost:9000/api/v1/workflows/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(workflow)
      });
      
      if (response.ok) {
        alert('✅ Workflow saved successfully!');
        showEditor = false;
        loadWorkflowsData();
      } else {
        alert('Failed to save workflow');
      }
    } catch {
      // Silent failure
      alert('Failed to save workflow');
    }
  }

  $: activeWorkflows = workflows; // All workflows are considered active
  $: totalExecutions = 0; // No execution count in current API
  $: avgSuccessRate = 0; // No success rate in current API
</script>

<div class="bg-white border border-surface-200 rounded">
  <div class="px-4 py-3 border-b border-surface-200">
    <div class="flex items-center justify-between">
      <h3 class="text-sm font-medium text-surface-900">Workflows & Automation</h3>
      <div class="flex items-center space-x-2">
        <button 
          on:click={() => { showEditor = true; editingWorkflowId = null; }}
          class="text-xs px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          + Create Workflow
        </button>
        <button 
          on:click={loadWorkflowsData}
          class="text-xs text-surface-500 hover:text-surface-600 flex items-center space-x-1"
        >
          <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          <span>Refresh</span>
        </button>
      </div>
    </div>
  </div>

  <div class="p-4">
    {#if loading}
      <div class="animate-pulse space-y-4">
        <div class="grid grid-cols-3 gap-4 mb-6">
          {#each Array(3) as _}
            <div class="bg-surface-100 p-4 rounded">
              <div class="w-16 h-6 bg-surface-200 rounded mb-1"></div>
              <div class="w-12 h-4 bg-surface-200 rounded"></div>
            </div>
          {/each}
        </div>
        {#each Array(5) as _}
          <div class="flex items-center space-x-3 p-3 border border-surface-200 rounded">
            <div class="w-8 h-8 bg-surface-200 rounded"></div>
            <div class="flex-1">
              <div class="w-32 h-4 bg-surface-200 rounded mb-1"></div>
              <div class="w-48 h-3 bg-surface-200 rounded"></div>
            </div>
            <div class="w-16 h-4 bg-surface-200 rounded"></div>
          </div>
        {/each}
      </div>
    {:else if error}
      <div class="text-center text-red-600">
        <p>{error}</p>
        <button 
          on:click={loadWorkflowsData}
          class="mt-2 text-sm text-blue-600 hover:text-blue-800"
        >
          Try again
        </button>
      </div>
    {:else}
      <!-- Workflow Stats -->
      <div class="grid grid-cols-3 gap-4 mb-6">
        <div class="bg-blue-50 p-4 rounded">
          <p class="text-2xl font-bold text-blue-600">{workflows.length}</p>
          <p class="text-sm text-blue-600">Total Workflows</p>
        </div>
        <div class="bg-green-50 p-4 rounded">
          <p class="text-2xl font-bold text-green-600">{activeWorkflows.length}</p>
          <p class="text-sm text-green-600">Active</p>
        </div>
        <div class="bg-purple-50 p-4 rounded">
          <p class="text-2xl font-bold text-purple-600">{avgSuccessRate.toFixed(1)}%</p>
          <p class="text-sm text-purple-600">Avg Success Rate</p>
        </div>
      </div>

      <!-- Workflows List -->
      {#if workflows.length > 0}
        <div class="mb-6">
          <h4 class="text-xs font-medium text-surface-600 mb-3">Active Workflows</h4>
          <div class="space-y-3">
            {#each workflows.slice(0, 5) as workflow}
              <div class="flex items-center justify-between p-3 border border-surface-200 rounded hover:bg-surface-50">
                <div class="flex items-center space-x-3">
                  <div class="w-8 h-8 bg-gradient-to-br from-indigo-400 to-purple-500 rounded flex items-center justify-center">
                    <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                  </div>
                  <div>
                    <p class="text-sm font-medium text-surface-900">{workflow.name}</p>
                    <p class="text-xs text-surface-500">
                      {workflow.steps_count} agent steps • {formatDuration(workflow.estimated_duration)}
                    </p>
                    {#if workflow.agents_involved && workflow.agents_involved.length > 0}
                      <p class="text-xs text-surface-600 mt-1">
                        Agents: {workflow.agents_involved.join(', ')}
                      </p>
                    {/if}
                  </div>
                </div>
                <div class="flex items-center space-x-3">
                  <div class="text-right">
                    <p class="text-xs text-surface-500">
                      {workflow.complexity}
                    </p>
                    <p class="text-xs text-surface-500">
                      {formatDuration(workflow.estimated_duration)}
                    </p>
                  </div>
                  <button 
                    on:click={() => viewWorkflowDetails(workflow.workflow_id)}
                    class="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
                  >
                    Details
                  </button>
                  <button 
                    on:click={() => openEditor(workflow.workflow_id)}
                    class="text-xs px-2 py-1 bg-yellow-100 text-yellow-700 rounded hover:bg-yellow-200 mx-1"
                  >
                    Edit
                  </button>
                  <button 
                    on:click={() => executeWorkflow(workflow.workflow_id)}
                    class="text-xs px-2 py-1 bg-green-100 text-green-700 rounded hover:bg-green-200"
                    disabled={executingWorkflow}
                  >
                    Execute
                  </button>
                </div>
              </div>
            {/each}
          </div>
        </div>
      {/if}

      <!-- Recent Executions -->
      {#if recentExecutions.length > 0}
        <div>
          <h4 class="text-xs font-medium text-surface-600 mb-3">Recent Executions</h4>
          <div class="space-y-2">
            {#each recentExecutions.slice(0, 6) as execution}
              <div class="flex items-center justify-between p-2 hover:bg-surface-50 rounded">
                <div>
                  <p class="text-sm font-medium text-surface-900">{execution.workflow_name}</p>
                  <p class="text-xs text-surface-500">
                    {formatDate(execution.started_at)} • {formatDuration(execution.duration)}
                  </p>
                </div>
                <div class="flex items-center space-x-2">
                  <span class="text-xs text-surface-500">
                    {execution.success_rate.toFixed(1)}%
                  </span>
                  <span class="text-xs px-2 py-1 rounded-full {getStatusColor(execution.status)}">
                    {execution.status}
                  </span>
                </div>
              </div>
            {/each}
          </div>
        </div>
      {:else if workflows.length === 0}
        <div class="text-center text-surface-500">
          <p class="text-xs">No workflows or executions available</p>
        </div>
      {/if}
    {/if}
  </div>
</div>

<!-- Workflow Details Modal -->
{#if showDetails && selectedWorkflow}
  <div class="fixed inset-0 bg-surface-600 bg-opacity-50 z-50 flex items-center justify-center p-4">
    <div class="bg-white rounded max-w-4xl max-h-[90vh] overflow-y-auto p-6 w-full">
      <div class="flex justify-between items-start mb-4">
        <div>
          <h2 class="text-lg font-medium text-surface-900">{selectedWorkflow.name}</h2>
          <p class="text-sm text-surface-500 mt-1">{selectedWorkflow.description}</p>
        </div>
        <button
          on:click={() => { showDetails = false; selectedWorkflow = null; }}
          class="text-surface-600 hover:text-surface-300"
          aria-label="Close workflow details"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- Workflow Metadata -->
      <div class="grid grid-cols-3 gap-4 mb-6 bg-surface-50 p-4 rounded">
        <div>
          <p class="text-xs text-surface-500">Business Domain</p>
          <p class="text-sm font-medium">{selectedWorkflow.business_domain || 'Strategy'}</p>
        </div>
        <div>
          <p class="text-xs text-surface-500">Priority</p>
          <p class="text-sm font-medium">{selectedWorkflow.priority || 'High'}</p>
        </div>
        <div>
          <p class="text-xs text-surface-500">SLA</p>
          <p class="text-sm font-medium">{selectedWorkflow.sla_minutes || 180} minutes</p>
        </div>
      </div>

      <!-- Workflow Steps -->
      <h3 class="text-sm font-medium text-surface-900 mb-3">AutoGen Agent Orchestration Steps</h3>
      <div class="space-y-4">
        {#if selectedWorkflow.steps}
          {#each selectedWorkflow.steps as step, i}
            <div class="border border-surface-200 rounded p-4 hover:bg-surface-50">
              <div class="flex items-start justify-between">
                <div class="flex-1">
                  <div class="flex items-center space-x-2 mb-2">
                    <span class="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded">
                      Step {i + 1}
                    </span>
                    <span class="text-xs px-2 py-1 bg-purple-100 text-purple-700 rounded">
                      {step.step_type}
                    </span>
                    <span class="text-xs text-surface-500">
                      ~{step.estimated_duration_minutes} min
                    </span>
                  </div>
                  <h4 class="text-sm font-medium text-surface-900">{step.description}</h4>
                  <p class="text-xs text-surface-600 mt-1">
                    <strong>Agent:</strong> {step.agent_name.replace(/_/g, ' ')}
                  </p>
                  {#if step.detailed_instructions}
                    <details class="mt-2">
                      <summary class="text-xs text-surface-500 cursor-pointer hover:text-surface-600">
                        View instructions
                      </summary>
                      <pre class="text-xs text-surface-600 mt-2 whitespace-pre-wrap bg-surface-50 p-2 rounded">
{step.detailed_instructions.trim()}
                      </pre>
                    </details>
                  {/if}
                  {#if step.tools_required && step.tools_required.length > 0}
                    <p class="text-xs text-surface-500 mt-2">
                      <strong>Tools:</strong> {step.tools_required.join(', ')}
                    </p>
                  {/if}
                  {#if step.dependencies && step.dependencies.length > 0}
                    <p class="text-xs text-surface-500 mt-1">
                      <strong>Dependencies:</strong> {step.dependencies.join(', ')}
                    </p>
                  {/if}
                </div>
              </div>
            </div>
          {/each}
        {:else}
          <p class="text-sm text-surface-500">No step details available</p>
        {/if}
      </div>

      <!-- Success Metrics -->
      {#if selectedWorkflow.success_metrics}
        <div class="mt-6 bg-green-50 p-4 rounded">
          <h3 class="text-sm font-medium text-green-900 mb-2">Success Metrics</h3>
          <div class="space-y-1">
            {#each Object.entries(selectedWorkflow.success_metrics) as [key, value]}
              <p class="text-xs text-green-700">
                <strong>{key.replace(/_/g, ' ')}:</strong> {value}
              </p>
            {/each}
          </div>
        </div>
      {/if}

      <!-- Action Buttons -->
      <div class="mt-6 flex justify-end space-x-3">
        <button 
          on:click={() => { showDetails = false; selectedWorkflow = null; }}
          class="px-4 py-2 text-sm text-surface-600 bg-surface-100 hover:bg-surface-200 rounded"
        >
          Close
        </button>
        <button 
          on:click={() => { executeWorkflow(selectedWorkflow.workflow_id); showDetails = false; }}
          class="px-4 py-2 text-sm text-white bg-blue-600 hover:bg-blue-700 rounded"
        >
          Execute This Workflow
        </button>
      </div>
    </div>
  </div>
{/if}

<!-- Workflow Editor -->
{#if showEditor}
  <WorkflowEditor 
    workflowId={editingWorkflowId}
    onSave={handleSaveWorkflow}
    onClose={() => { showEditor = false; editingWorkflowId = null; }}
  />
{/if}