<script lang="ts">
  import { onMount } from 'svelte';
  import { agentsService, type Agent, type SwarmStatus } from '$lib/services/agentsService';

  let agents: Agent[] = [];
  let swarmStatus: SwarmStatus | null = null;
  let loading = true;
  let error: string | null = null;

  function getStatusColor(status: string): string {
    switch (status) {
      case 'active': return 'text-green-600 bg-green-50';
      case 'busy': return 'text-yellow-600 bg-yellow-50';
      case 'inactive': return 'text-surface-600 bg-surface-50';
      case 'error': return 'text-red-600 bg-red-50';
      default: return 'text-surface-600 bg-surface-50';
    }
  }

  function formatNumber(num: number): string {
    return new Intl.NumberFormat('en-US').format(num);
  }

  async function loadAgentsData() {
    try {
      loading = true;
      error = null;
      
      const [agentsData, swarmData] = await Promise.all([
        agentsService.getAgents(),
        agentsService.getSwarmStatus()
      ]);
      
      agents = agentsData || [];
      swarmStatus = swarmData;
    } catch {
      // Silent failure
      error = 'Failed to load agents data';
    } finally {
      loading = false;
    }
  }

  onMount(loadAgentsData);

  $: activeAgents = agents.filter(a => a.status === 'active');
  $: busyAgents = agents.filter(a => a.status === 'busy');
</script>

<div class="bg-white border border-surface-200 rounded">
  <div class="px-4 py-3 border-b border-surface-200">
    <div class="flex items-center justify-between">
      <h3 class="text-sm font-medium text-surface-900">AI Agents Ecosystem</h3>
      <button 
        on:click={loadAgentsData}
        class="text-xs text-surface-500 hover:text-surface-600 flex items-center space-x-1"
      >
        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        <span>Refresh</span>
      </button>
    </div>
  </div>

  <div class="p-4">
    {#if loading}
      <div class="animate-pulse space-y-4">
        <div class="grid grid-cols-4 gap-4 mb-6">
          {#each Array(4) as _}
            <div class="bg-surface-100 p-4 rounded">
              <div class="w-16 h-6 bg-surface-200 rounded mb-1"></div>
              <div class="w-12 h-4 bg-surface-200 rounded"></div>
            </div>
          {/each}
        </div>
        {#each Array(6) as _}
          <div class="flex items-center space-x-3 p-3 border border-surface-200 rounded">
            <div class="w-8 h-8 bg-surface-200 rounded-full"></div>
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
          on:click={loadAgentsData}
          class="mt-2 text-sm text-blue-600 hover:text-blue-800"
        >
          Try again
        </button>
      </div>
    {:else}
      <!-- Swarm Overview -->
      {#if swarmStatus}
        <div class="grid grid-cols-4 gap-4 mb-6">
          <div class="bg-blue-50 p-4 rounded">
            <p class="text-2xl font-bold text-blue-600">{swarmStatus.active_agents}</p>
            <p class="text-sm text-blue-600">Active Agents</p>
          </div>
          <div class="bg-green-50 p-4 rounded">
            <p class="text-2xl font-bold text-green-600">{swarmStatus.total_tasks}</p>
            <p class="text-sm text-green-600">Total Tasks</p>
          </div>
          <div class="bg-purple-50 p-4 rounded">
            <p class="text-2xl font-bold text-purple-600">
              {swarmStatus.performance_overview?.efficiency_score?.toFixed(1) || 'N/A'}%
            </p>
            <p class="text-sm text-purple-600">Efficiency</p>
          </div>
          <div class="bg-orange-50 p-4 rounded">
            <p class="text-2xl font-bold text-orange-600">
              {swarmStatus.performance_overview?.task_completion_rate?.toFixed(1) || 'N/A'}%
            </p>
            <p class="text-sm text-orange-600">Completion Rate</p>
          </div>
        </div>
      {/if}

      <!-- Agent Status Summary -->
      <div class="grid grid-cols-4 gap-4 mb-6">
        <div class="bg-green-50 p-3 rounded">
          <p class="text-xl font-bold text-green-600">{activeAgents.length}</p>
          <p class="text-xs text-green-600">Active</p>
        </div>
        <div class="bg-yellow-50 p-3 rounded">
          <p class="text-xl font-bold text-yellow-600">{busyAgents.length}</p>
          <p class="text-xs text-yellow-600">Busy</p>
        </div>
        <div class="bg-surface-50 p-3 rounded">
          <p class="text-xl font-bold text-surface-600">{agents.filter(a => a.status === 'inactive').length}</p>
          <p class="text-xs text-surface-600">Inactive</p>
        </div>
        <div class="bg-red-50 p-3 rounded">
          <p class="text-xl font-bold text-red-600">{agents.filter(a => a.status === 'error').length}</p>
          <p class="text-xs text-red-600">Error</p>
        </div>
      </div>

      <!-- Agents List -->
      {#if agents.length > 0}
        <div class="space-y-3">
          <h4 class="text-xs font-medium text-surface-600">Active Agents</h4>
          {#each agents.slice(0, 8) as agent}
            <div class="flex items-center justify-between p-3 border border-surface-200 rounded hover:bg-surface-50">
              <div class="flex items-center space-x-3">
                <div class="w-8 h-8 bg-gradient-to-br from-green-400 to-blue-500 rounded-full flex items-center justify-center">
                  <span class="text-white text-sm font-semibold">
                    {agent.name ? agent.name.charAt(0).toUpperCase() : agent.agent_key.charAt(0).toUpperCase()}
                  </span>
                </div>
                <div>
                  <p class="text-sm font-medium text-surface-900">{agent.name || agent.agent_key}</p>
                  <p class="text-xs text-surface-500">
                    {agent.role || 'General Agent'} • 
                    {agent.capabilities?.length || 0} capabilities
                  </p>
                </div>
              </div>
              <div class="flex items-center space-x-3">
                {#if agent.performance_metrics}
                  <div class="text-right">
                    <p class="text-xs text-surface-500">
                      {agent.performance_metrics.success_rate?.toFixed(1) || 'N/A'}% success
                    </p>
                    <p class="text-xs text-surface-500">
                      {agent.performance_metrics.total_tasks || 0} tasks
                    </p>
                  </div>
                {/if}
                <span class="text-xs px-2 py-1 rounded-full {getStatusColor(agent.status)}">
                  {agent.status}
                </span>
              </div>
            </div>
          {/each}
          
          {#if agents.length > 8}
            <div class="text-center">
              <p class="text-xs text-surface-500">... and {agents.length - 8} more</p>
            </div>
          {/if}
        </div>
      {:else}
        <div class="text-center text-surface-500">
          <p class="text-xs">No agents available</p>
        </div>
      {/if}
    {/if}
  </div>
</div>