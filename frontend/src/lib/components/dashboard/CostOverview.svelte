<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { writable } from 'svelte/store';

  // Cost data store with provider breakdown
  const costData = writable({
    total_cost_usd: 0.0,
    today_cost_usd: 0.0,
    total_interactions: 0,
    total_tokens: 0,
    active_sessions: 0,
    budget_utilization: 0.0,
    status: 'loading',
    provider_breakdown: {},
    model_breakdown: {},
    hourly_breakdown: {},
    last_updated: ''
  });

  let updateInterval: ReturnType<typeof setInterval> | null = null;

  async function fetchCostData() {
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:9000';
      const response = await fetch(`${apiUrl}/api/v1/cost-management/realtime/current`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (response.ok) {
        const data = await response.json();
        costData.set(data);
      } else {
        console.warn('Cost API unavailable, using fallback');
        costData.set({
          total_cost_usd: 0.0,
          today_cost_usd: 0.0,
          total_interactions: 0,
          total_tokens: 0,
          active_sessions: 0,
          budget_utilization: 0.0,
          status: 'unavailable',
          provider_breakdown: {},
          model_breakdown: {},
          hourly_breakdown: {},
          last_updated: new Date().toISOString()
        });
      }
    } catch (error) {
      console.warn('Cost tracking unavailable:', error);
      costData.set({
        total_cost_usd: 0.0,
        today_cost_usd: 0.0,
        total_interactions: 0,
        total_tokens: 0,
        active_sessions: 0,
        budget_utilization: 0.0,
        status: 'error',
        provider_breakdown: {},
        model_breakdown: {},
        hourly_breakdown: {},
        last_updated: new Date().toISOString()
      });
    }
  }

  onMount(() => {
    // Initial fetch
    fetchCostData();
    
    // Update every 30 seconds
    updateInterval = setInterval(fetchCostData, 30000);
  });

  onDestroy(() => {
    if (updateInterval) {
      clearInterval(updateInterval);
    }
  });

  function formatCost(amount: number): string {
    if (amount === 0) return '$0.00';
    if (amount < 0.01) return '<$0.01';
    return `$${amount.toFixed(2)}`;
  }

  function getStatusIcon(status: string): string {
    switch (status) {
      case 'healthy': return '💚';
      case 'moderate': return '💛';
      case 'warning': return '🟠';
      case 'exceeded': return '🔴';
      case 'error': case 'unavailable': return '⚪';
      default: return '🔵';
    }
  }
</script>

<!-- Cost Dashboard Component -->
<div class="bg-white border border-surface-200 rounded-lg shadow-sm">
  <!-- Header -->
  <div class="bg-gradient-to-r from-blue-600 to-blue-700 text-white px-6 py-4 rounded-t-lg">
    <div class="flex items-center justify-between">
      <div class="flex items-center space-x-2">
        <span class="text-xl">{getStatusIcon($costData.status)}</span>
        <h3 class="text-lg font-bold">💰 Cost Overview</h3>
      </div>
      <div class="flex items-center space-x-2">
        <span class="text-sm px-3 py-1 rounded-full bg-white/20 font-bold">
          {$costData.status}
        </span>
        <button 
          on:click={fetchCostData}
          class="px-3 py-1 bg-white/20 hover:bg-white/30 text-white font-bold rounded transition-colors"
        >
          Refresh
        </button>
      </div>
    </div>
  </div>

  <div class="p-6 space-y-6">
    <!-- Cost Metrics -->
    <div class="grid grid-cols-2 gap-4">
      <div class="bg-gradient-to-r from-gray-50 to-gray-100 p-4 rounded-lg border">
        <div class="text-sm font-bold text-surface-600 mb-1">Total Cost</div>
        <div class="text-2xl font-bold text-surface-900">
          {formatCost($costData.total_cost_usd)}
        </div>
      </div>
      
      <div class="bg-gradient-to-r from-blue-50 to-blue-100 p-4 rounded-lg border">
        <div class="text-sm font-bold text-blue-700 mb-1">Today</div>
        <div class="text-2xl font-bold text-blue-900">
          {formatCost($costData.today_cost_usd)}
        </div>
      </div>
    </div>

    <!-- Budget Utilization -->
    {#if $costData.budget_utilization > 0}
      <div class="space-y-3 p-4 bg-gradient-to-r from-gray-50 to-gray-100 rounded-lg border">
        <div class="flex justify-between items-center">
          <h4 class="text-sm font-bold text-surface-800">Budget Utilization</h4>
          <span class="text-lg font-bold text-surface-900">{$costData.budget_utilization.toFixed(1)}%</span>
        </div>
        <div class="w-full bg-surface-200 rounded-full h-4">
          <div class="h-4 rounded-full transition-all duration-300 {$costData.budget_utilization > 80 ? 'bg-gradient-to-r from-red-500 to-red-600' : $costData.budget_utilization > 50 ? 'bg-gradient-to-r from-yellow-500 to-yellow-600' : 'bg-gradient-to-r from-green-500 to-green-600'}" 
               style="width: {Math.min($costData.budget_utilization, 100)}%"></div>
        </div>
      </div>
    {/if}

    <!-- Service Breakdown (DETAILED) -->
    {#if $costData.service_details && Object.keys($costData.service_details).length > 0}
      <div class="space-y-3">
        <h4 class="text-lg font-bold text-surface-900 flex items-center space-x-2">
          <span>🔥</span>
          <span>Service Details (Today)</span>
        </h4>
        {#each Object.entries($costData.service_details) as [provider, details]}
          <div class="bg-gradient-to-r from-gray-50 to-gray-100 rounded-lg p-5 border space-y-3">
            <div class="flex justify-between items-center">
              <div class="flex items-center space-x-3">
                <div class="w-5 h-5 rounded-full {provider === 'openai' ? 'bg-gradient-to-r from-green-500 to-green-600' : provider === 'anthropic' ? 'bg-gradient-to-r from-purple-500 to-purple-600' : provider === 'perplexity' ? 'bg-gradient-to-r from-blue-500 to-blue-600' : 'bg-gradient-to-r from-gray-500 to-gray-600'}"></div>
                <span class="text-lg font-bold text-surface-900 capitalize">{provider}</span>
              </div>
              <span class="text-xl font-mono font-bold text-surface-900">{formatCost(details.cost_usd)}</span>
            </div>
            
            <!-- Service Detail Stats -->
            <div class="grid grid-cols-3 gap-4 text-sm">
              <div class="bg-white p-3 rounded-lg border text-center">
                <div class="text-surface-600 font-bold mb-1">Calls</div>
                <div class="text-lg font-bold text-surface-900">{details.calls}</div>
              </div>
              <div class="bg-white p-3 rounded-lg border text-center">
                <div class="text-surface-600 font-bold mb-1">Tokens</div>
                <div class="text-lg font-bold text-surface-900">{details.tokens.toLocaleString()}</div>
              </div>
              <div class="bg-white p-3 rounded-lg border text-center">
                <div class="text-surface-600 font-bold mb-1">Avg/Call</div>
                <div class="text-lg font-bold text-surface-900">{formatCost(details.avg_cost_per_call)}</div>
              </div>
            </div>
          </div>
        {/each}
      </div>
    {/if}

    <!-- Top Models -->
    {#if Object.keys($costData.model_breakdown).length > 0}
      <div class="space-y-3">
        <h4 class="text-lg font-bold text-surface-900">📊 Top Models (Today)</h4>
        <div class="space-y-2">
          {#each Object.entries($costData.model_breakdown).slice(0, 5) as [model, cost]}
            <div class="flex justify-between items-center py-3 px-4 bg-gradient-to-r from-gray-50 to-gray-100 rounded-lg border">
              <span class="text-sm font-bold text-surface-800 truncate">{model}</span>
              <span class="text-lg font-mono font-bold text-surface-900">{formatCost(cost)}</span>
            </div>
          {/each}
        </div>
      </div>
    {/if}

    <!-- Current Session Info -->
    {#if $costData.session_summary && $costData.session_summary.total_calls > 0}
      <div class="space-y-4 p-5 bg-gradient-to-r from-blue-50 to-blue-100 rounded-lg border">
        <h4 class="text-lg font-bold text-blue-900 flex items-center space-x-2">
          <span>🚀</span>
          <span>Current Session</span>
        </h4>
        <div class="grid grid-cols-3 gap-4 text-sm">
          <div class="bg-white p-3 rounded-lg border text-center">
            <div class="text-blue-700 font-bold mb-1">Cost</div>
            <div class="text-lg font-bold text-blue-900">{formatCost($costData.session_summary.total_cost_usd)}</div>
          </div>
          <div class="bg-white p-3 rounded-lg border text-center">
            <div class="text-blue-700 font-bold mb-1">Calls</div>
            <div class="text-lg font-bold text-blue-900">{$costData.session_summary.total_calls}</div>
          </div>
          <div class="bg-white p-3 rounded-lg border text-center">
            <div class="text-blue-700 font-bold mb-1">Tokens</div>
            <div class="text-lg font-bold text-blue-900">{$costData.session_summary.total_tokens.toLocaleString()}</div>
          </div>
        </div>
        
        <!-- Session Provider Breakdown -->
        {#if $costData.session_summary.by_provider && Object.keys($costData.session_summary.by_provider).length > 0}
          <div class="space-y-2">
            <div class="text-sm font-bold text-blue-800">Session Providers:</div>
            {#each Object.entries($costData.session_summary.by_provider) as [provider, stats]}
              <div class="flex justify-between text-sm bg-white p-3 rounded-lg border">
                <span class="capitalize font-bold text-surface-600">{provider}</span>
                <span class="font-mono font-bold text-surface-900">{formatCost(stats.cost)} ({stats.calls} calls)</span>
              </div>
            {/each}
          </div>
        {/if}
      </div>
    {/if}

    <!-- Usage Metrics -->
    {#if $costData.total_interactions > 0}
      <div class="pt-4 border-t border-surface-200 space-y-4">
        <h4 class="text-lg font-bold text-surface-900 flex items-center space-x-2">
          <span>📈</span>
          <span>Overall Statistics</span>
        </h4>
        <div class="grid grid-cols-2 gap-4 text-sm">
          <div class="bg-gradient-to-r from-gray-50 to-gray-100 p-4 rounded-lg border">
            <div class="text-surface-600 font-bold mb-1">Total Interactions</div>
            <div class="text-xl font-bold text-surface-900">{$costData.total_interactions.toLocaleString()}</div>
          </div>
          
          <div class="bg-gradient-to-r from-gray-50 to-gray-100 p-4 rounded-lg border">
            <div class="text-surface-600 font-bold mb-1">Total Tokens</div>
            <div class="text-xl font-bold text-surface-900">{$costData.total_tokens.toLocaleString()}</div>
          </div>

          {#if $costData.today_interactions}
            <div class="bg-gradient-to-r from-green-50 to-green-100 p-4 rounded-lg border">
              <div class="text-green-700 font-bold mb-1">Today Interactions</div>
              <div class="text-xl font-bold text-green-900">{$costData.today_interactions.toLocaleString()}</div>
            </div>
          {/if}
          
          {#if $costData.today_tokens}
            <div class="bg-gradient-to-r from-green-50 to-green-100 p-4 rounded-lg border">
              <div class="text-green-700 font-bold mb-1">Today Tokens</div>
              <div class="text-xl font-bold text-green-900">{$costData.today_tokens.toLocaleString()}</div>
            </div>
          {/if}
        </div>
      </div>
    {/if}
  </div>

  <!-- Footer -->
  <div class="bg-gradient-to-r from-gray-100 to-gray-200 px-6 py-4 rounded-b-lg flex justify-between items-center text-sm border-t">
    <span class="text-surface-600 font-medium">
      Updated: {$costData.last_updated ? new Date($costData.last_updated + (($costData.last_updated.includes('Z') || $costData.last_updated.includes('+')) ? '' : 'Z')).toLocaleTimeString() : 'N/A'}
    </span>
  </div>

  <!-- Status Message -->
  {#if $costData.status === 'error' || $costData.status === 'unavailable'}
    <div class="mx-6 mb-6 p-4 bg-yellow-100 border border-yellow-300 rounded-lg">
      <div class="text-sm text-yellow-800 font-medium text-center">
        Cost tracking temporarily unavailable
      </div>
    </div>
  {/if}
</div>