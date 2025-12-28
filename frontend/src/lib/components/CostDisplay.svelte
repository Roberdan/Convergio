<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { writable } from 'svelte/store';

  interface ServiceDetails {
    cost_usd: number;
    calls: number;
    tokens: number;
    avg_cost_per_call: number;
  }

  interface SessionProviderStats {
    cost: number;
    calls: number;
  }

  interface SessionSummary {
    total_cost_usd: number;
    total_calls: number;
    total_tokens: number;
    by_provider?: Record<string, SessionProviderStats>;
  }

  interface CostData {
    total_cost_usd: number;
    today_cost_usd: number;
    total_interactions: number;
    total_tokens: number;
    active_sessions: number;
    budget_utilization: number;
    status: string;
    provider_breakdown: Record<string, unknown>;
    model_breakdown: Record<string, number>;
    hourly_breakdown: Record<string, unknown>;
    last_updated: string;
    service_details?: Record<string, ServiceDetails>;
    session_summary?: SessionSummary;
    today_interactions?: number;
    today_tokens?: number;
  }

  // Cost data store with provider breakdown
  const costData = writable<CostData>({
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

  let showDetails = false;
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
    } catch {
      // Silent failure
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

<!-- Cost Display Component -->
<div class="relative">
  <!-- Main Cost Display Button -->
  <button
    on:click={() => showDetails = !showDetails}
    class="flex items-start space-x-2 px-4 py-2 bg-surface-50 rounded-lg hover:bg-blue-50 transition-all duration-200 shadow-sm"
    title="Click to toggle detailed cost breakdown"
  >
    <span class="text-lg">{getStatusIcon($costData.status)}</span>
    <div class="flex flex-col items-start">
      <span class="text-sm font-bold text-surface-900 ">
        {formatCost($costData.total_cost_usd)}
      </span>
      {#if $costData.today_cost_usd > 0 && $costData.today_cost_usd !== $costData.total_cost_usd}
        <span class="text-xs text-surface-700  font-medium">
          {formatCost($costData.today_cost_usd)} today
        </span>
      {/if}
    </div>
    <svg class="h-4 w-4 text-surface-600 transform transition-transform {showDetails ? 'rotate-180' : ''}" fill="currentColor" viewBox="0 0 20 20">
      <path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd" />
    </svg>
  </button>

  <!-- Dropdown Panel -->
  {#if showDetails}
    <div class="absolute right-0 top-full mt-2 w-96 bg-surface-50 border-2 border-surface-400  rounded-xl shadow-2xl z-[10000] overflow-hidden">
      <!-- Header -->
      <div class="bg-blue-600 text-white px-6 py-4">
        <div class="flex items-center justify-between">
          <h3 class="text-lg font-bold">💰 Cost Overview</h3>
          <div class="flex items-center space-x-2">
            <span class="text-sm px-3 py-1 rounded-full bg-white/20 font-bold">
              {$costData.status}
            </span>
          </div>
        </div>
      </div>

      <div class="p-6 space-y-6">
        <!-- Cost Metrics -->
        <div class="grid grid-cols-2 gap-4">
          <div class="bg-surface-200  p-4 rounded-lg">
            <div class="text-sm font-bold text-surface-700  mb-1">Total Cost</div>
            <div class="text-xl font-bold text-surface-900 ">
              {formatCost($costData.total_cost_usd)}
            </div>
          </div>
          
          <div class="bg-blue-100 p-4 rounded-lg">
            <div class="text-sm font-bold text-blue-700 mb-1">Today</div>
            <div class="text-xl font-bold text-blue-900">
              {formatCost($costData.today_cost_usd)}
            </div>
          </div>
        </div>

        <!-- Budget Utilization -->
        {#if $costData.budget_utilization > 0}
          <div class="space-y-2">
            <div class="flex justify-between text-sm">
              <span class="font-bold text-surface-800 ">Budget Used:</span>
              <span class="font-bold text-surface-900 ">{$costData.budget_utilization.toFixed(1)}%</span>
            </div>
            <div class="w-full bg-surface-300  rounded-full h-3">
              <div class="h-3 rounded-full {$costData.budget_utilization > 80 ? 'bg-red-500' : $costData.budget_utilization > 50 ? 'bg-yellow-500' : 'bg-green-500'}" 
                   style="width: {Math.min($costData.budget_utilization, 100)}%"></div>
            </div>
          </div>
        {/if}

        <!-- Service Breakdown (DETAILED) -->
        {#if $costData.service_details && Object.keys($costData.service_details).length > 0}
          <div class="space-y-3">
            <div class="text-sm font-bold text-surface-900 ">🔥 Service Details (Today)</div>
            {#each Object.entries($costData.service_details) as [provider, details]}
              <div class="bg-surface-100  rounded-lg p-4 space-y-2">
                <div class="flex justify-between items-center">
                  <div class="flex items-center space-x-3">
                    <div class="w-4 h-4 rounded-full {provider === 'openai' ? 'bg-green-500' : provider === 'anthropic' ? 'bg-purple-500' : provider === 'perplexity' ? 'bg-blue-500' : 'bg-surface-500'}"></div>
                    <span class="capitalize font-bold text-surface-900 ">{provider}</span>
                  </div>
                  <span class="font-mono font-bold text-surface-900 ">{formatCost(details.cost_usd)}</span>
                </div>
                
                <!-- Service Detail Stats -->
                <div class="grid grid-cols-3 gap-3 text-xs">
                  <div class="bg-surface-50 p-2 rounded">
                    <div class="text-surface-600  font-bold">Calls</div>
                    <div class="font-bold text-surface-900 ">{details.calls}</div>
                  </div>
                  <div class="bg-surface-50 p-2 rounded">
                    <div class="text-surface-600  font-bold">Tokens</div>
                    <div class="font-bold text-surface-900 ">{details.tokens.toLocaleString()}</div>
                  </div>
                  <div class="bg-surface-50 p-2 rounded">
                    <div class="text-surface-600  font-bold">Avg/Call</div>
                    <div class="font-bold text-surface-900 ">{formatCost(details.avg_cost_per_call)}</div>
                  </div>
                </div>
              </div>
            {/each}
          </div>
        {/if}

        <!-- Top Models -->
        {#if Object.keys($costData.model_breakdown).length > 0}
          <div class="space-y-3">
            <div class="text-sm font-bold text-surface-900">Top Models (Today)</div>
            {#each Object.entries($costData.model_breakdown).slice(0, 3) as [model, cost]}
              <div class="flex justify-between items-center py-2 px-3 bg-surface-50 rounded">
                <span class="text-sm font-bold text-surface-800 truncate">{model}</span>
                <span class="font-mono text-sm font-bold text-surface-900">{formatCost(cost)}</span>
              </div>
            {/each}
          </div>
        {/if}

        <!-- Current Session Info -->
        {#if $costData.session_summary && $costData.session_summary.total_calls > 0}
          <div class="space-y-3">
            <div class="text-sm font-bold text-surface-900">🚀 Current Session</div>
            <div class="bg-blue-50 rounded-lg p-4 space-y-3">
              <div class="grid grid-cols-3 gap-3 text-sm">
                <div class="bg-white p-2 rounded">
                  <div class="text-blue-700 font-bold">Cost</div>
                  <div class="font-bold text-blue-900">{formatCost($costData.session_summary.total_cost_usd)}</div>
                </div>
                <div class="bg-white p-2 rounded">
                  <div class="text-blue-700 font-bold">Calls</div>
                  <div class="font-bold text-blue-900">{$costData.session_summary.total_calls}</div>
                </div>
                <div class="bg-white p-2 rounded">
                  <div class="text-blue-700 font-bold">Tokens</div>
                  <div class="font-bold text-blue-900">{$costData.session_summary.total_tokens.toLocaleString()}</div>
                </div>
              </div>
              
              <!-- Session Provider Breakdown -->
              {#if $costData.session_summary.by_provider && Object.keys($costData.session_summary.by_provider).length > 0}
                <div class="space-y-2">
                  <div class="text-xs font-bold text-blue-800">Session Providers:</div>
                  {#each Object.entries($costData.session_summary.by_provider) as [provider, stats]}
                    <div class="flex justify-between text-xs bg-white p-2 rounded">
                      <span class="capitalize font-bold text-surface-600">{provider}</span>
                      <span class="font-mono font-bold text-surface-900">{formatCost(stats.cost)} ({stats.calls} calls)</span>
                    </div>
                  {/each}
                </div>
              {/if}
            </div>
          </div>
        {/if}

        <!-- Usage Metrics -->
        {#if $costData.total_interactions > 0}
          <div class="pt-4 border-t border-surface-200 space-y-3">
            <div class="text-sm font-bold text-surface-900">📊 Overall Stats</div>
            <div class="grid grid-cols-2 gap-4 text-sm">
              <div class="bg-surface-50 p-3 rounded">
                <div class="text-surface-600 font-bold">Total Interactions</div>
                <div class="font-bold text-surface-900">{$costData.total_interactions.toLocaleString()}</div>
              </div>
              
              <div class="bg-surface-50 p-3 rounded">
                <div class="text-surface-600 font-bold">Total Tokens</div>
                <div class="font-bold text-surface-900">{$costData.total_tokens.toLocaleString()}</div>
              </div>

              {#if $costData.today_interactions}
                <div class="bg-green-50 p-3 rounded">
                  <div class="text-green-700 font-bold">Today Interactions</div>
                  <div class="font-bold text-green-900">{$costData.today_interactions.toLocaleString()}</div>
                </div>
              {/if}
              
              {#if $costData.today_tokens}
                <div class="bg-green-50 p-3 rounded">
                  <div class="text-green-700 font-bold">Today Tokens</div>
                  <div class="font-bold text-green-900">{$costData.today_tokens.toLocaleString()}</div>
                </div>
              {/if}
            </div>
          </div>
        {/if}
      </div>

      <!-- Footer -->
      <div class="bg-surface-200  px-6 py-4 flex justify-between items-center text-sm">
        <span class="text-surface-700  font-medium">
          Updated: {$costData.last_updated ? new Date($costData.last_updated + (($costData.last_updated.includes('Z') || $costData.last_updated.includes('+')) ? '' : 'Z')).toLocaleTimeString() : 'N/A'}
        </span>
        <button 
          on:click={fetchCostData}
          class="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded transition-colors"
        >
          Refresh
        </button>
      </div>

      <!-- Status Message -->
      {#if $costData.status === 'error' || $costData.status === 'unavailable'}
        <div class="mx-6 mb-6 p-3 bg-yellow-100 border border-yellow-300 rounded-lg">
          <div class="text-sm text-yellow-800 font-medium">
            Cost tracking temporarily unavailable
          </div>
        </div>
      {/if}
    </div>
  {/if}
</div>

<!-- Click outside to close -->
{#if showDetails}
  <div 
    class="fixed inset-0 z-[9999]" 
    role="button"
    tabindex="-1"
    aria-label="Close cost details"
    on:click={() => showDetails = false}
    on:keydown={(e) => e.key === 'Escape' && (showDetails = false)}
  ></div>
{/if}