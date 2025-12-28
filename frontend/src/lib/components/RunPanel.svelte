<!--
RunPanel Component - Visualizza metriche in tempo reale per le conversazioni
Include budget, tokens, errori, partecipanti e altre metriche operative
-->

<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { fade, scale } from 'svelte/transition';
  import { elasticOut } from 'svelte/easing';
  
  // Props
  export let conversationId: string;
  export let autoRefresh: boolean = true;
  export let showAdvanced: boolean = false;
  
  // State
  let metrics: any = {};
  let loading = false;
  let error: string | null = null;
  let refreshInterval: number | null = null;
  let lastUpdate: Date | null = null;
  
  // Types
  interface RunMetrics {
    budget: {
      current: number;
      limit: number;
      remaining: number;
      percentage: number;
    };
    tokens: {
      used: number;
      remaining: number;
      rate: number;
    };
    performance: {
      avg_turn_time: number;
      total_turns: number;
      active_agents: number;
    };
    errors: {
      count: number;
      last_error: string | null;
      error_rate: number;
    };
    agents: {
      total: number;
      active: number;
      names: string[];
    };
  }
  
  // Methods
  async function loadMetrics() {
    if (!conversationId) return;
    
    loading = true;
    error = null;
    
    try {
      const response = await fetch(`/api/v1/telemetry/conversation/${conversationId}/timeline`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const result = await response.json();
      if (result.success) {
        metrics = processMetrics(result.data);
        lastUpdate = new Date();
      } else {
        throw new Error(result.error || 'Failed to load metrics');
      }
    } catch (err) {
      // Silent failure
      error = err instanceof Error ? err.message : 'Unknown error occurred';
    } finally {
      loading = false;
    }
  }
  
  function processMetrics(data: any): RunMetrics {
    const timeline = data.timeline || [];

    // Calcola metriche aggregate
    let totalCost = 0;
    let totalTokens = 0;
    let totalErrors = 0;
    let lastError = null;
    let turnTimes: number[] = [];
    let allAgents = new Set<string>();
    
    for (const turn of timeline) {
      totalCost += turn.total_cost || 0;
      totalTokens += turn.total_tokens || 0;
      (turn.agents_involved || []).forEach((agent: string) => allAgents.add(agent));
      
      // Conta errori e tempi di esecuzione
      for (const event of turn.events || []) {
        if (event.event_type === 'error.occurred') {
          totalErrors++;
          lastError = event.data?.message || 'Unknown error';
        }
        
        if (event.event_type === 'tool_invoked' && event.data?.execution_time) {
          turnTimes.push(event.data.execution_time);
        }
      }
    }
    
    const avgTurnTime = turnTimes.length > 0 ? 
      turnTimes.reduce((a, b) => a + b, 0) / turnTimes.length : 0;
    
    const budgetLimit = 10.0; // Default budget limit
    const remainingBudget = Math.max(0, budgetLimit - totalCost);
    const budgetPercentage = (remainingBudget / budgetLimit) * 100;
    
    return {
      budget: {
        current: totalCost,
        limit: budgetLimit,
        remaining: remainingBudget,
        percentage: budgetPercentage
      },
      tokens: {
        used: totalTokens,
        remaining: 10000 - totalTokens, // Default token limit
        rate: totalTokens / Math.max(1, timeline.length)
      },
      performance: {
        avg_turn_time: avgTurnTime,
        total_turns: timeline.length,
        active_agents: allAgents.size
      },
      errors: {
        count: totalErrors,
        last_error: lastError,
        error_rate: (totalErrors / Math.max(1, timeline.length)) * 100
      },
      agents: {
        total: allAgents.size,
        active: allAgents.size,
        names: Array.from(allAgents)
      }
    };
  }
  
  function formatCost(cost: number): string {
    return `$${cost.toFixed(4)}`;
  }
  
  function formatTokens(tokens: number): string {
    return tokens.toLocaleString();
  }
  
  function formatTime(seconds: number): string {
    if (seconds < 1) {
      return `${(seconds * 1000).toFixed(0)}ms`;
    }
    return `${seconds.toFixed(2)}s`;
  }
  
  function getBudgetColor(percentage: number): string {
    if (percentage > 70) return 'text-green-600';
    if (percentage > 30) return 'text-yellow-600';
    return 'text-red-600';
  }
  
  function getBudgetBgColor(percentage: number): string {
    if (percentage > 70) return 'bg-green-100';
    if (percentage > 30) return 'bg-yellow-100';
    return 'bg-red-100';
  }
  
  function getErrorColor(errorRate: number): string {
    if (errorRate === 0) return 'text-green-600';
    if (errorRate < 5) return 'text-yellow-600';
    return 'text-red-600';
  }
  
  // Lifecycle
  onMount(() => {
    loadMetrics();
    
    if (autoRefresh) {
      refreshInterval = window.setInterval(loadMetrics, 3000); // Refresh every 3 seconds
    }
  });
  
  onDestroy(() => {
    if (refreshInterval) {
      clearInterval(refreshInterval);
    }
  });
  
  // Reactive statements
  $: if (conversationId) {
    loadMetrics();
  }
</script>

<div class="run-panel-container">
  <!-- Header -->
  <div class="panel-header">
    <h3 class="text-lg font-semibold text-surface-900">
      Run Panel
      {#if conversationId}
        <span class="text-sm font-normal text-surface-500">#{conversationId}</span>
      {/if}
    </h3>
    
    <div class="panel-controls">
      <button 
        on:click={loadMetrics}
        disabled={loading}
        class="btn-refresh"
        aria-label="Refresh metrics"
      >
        {#if loading}
          <span class="animate-spin">🔄</span>
        {:else}
          🔄
        {/if}
      </button>
      
      {#if lastUpdate}
        <span class="last-update" title="Last updated">
          📅 {lastUpdate.toLocaleTimeString()}
        </span>
      {/if}
    </div>
  </div>
  
  <!-- Loading State -->
  {#if loading && Object.keys(metrics).length === 0}
    <div class="loading-state" transition:fade>
      <div class="loading-spinner"></div>
      <p class="text-surface-500">Loading metrics...</p>
    </div>
  {/if}
  
  <!-- Error State -->
  {#if error}
    <div class="error-state" transition:fade>
      <div class="error-icon">⚠️</div>
      <p class="error-message">{error}</p>
      <button on:click={loadMetrics} class="btn-retry">
        Try Again
      </button>
    </div>
  {/if}
  
  <!-- Metrics Content -->
  {#if Object.keys(metrics).length > 0}
    <div class="metrics-grid">
      <!-- Budget Section -->
      <div class="metric-card budget-card" transition:scale={{ duration: 300, easing: elasticOut }}>
        <div class="card-header">
          <h4 class="card-title">💰 Budget Status</h4>
          <span class="card-icon">💳</span>
        </div>
        
        <div class="budget-progress">
          <div class="progress-bar">
            <div 
              class="progress-fill {getBudgetBgColor(metrics.budget.percentage)}"
              style="width: {Math.min(100, metrics.budget.percentage)}%"
            ></div>
          </div>
          <div class="progress-labels">
            <span class="current-cost">{formatCost(metrics.budget.current)}</span>
            <span class="budget-limit">{formatCost(metrics.budget.limit)}</span>
          </div>
        </div>
        
        <div class="budget-details">
          <div class="detail-item">
            <span class="label">Remaining:</span>
            <span class="value {getBudgetColor(metrics.budget.percentage)}">
              {formatCost(metrics.budget.remaining)}
            </span>
          </div>
          <div class="detail-item">
            <span class="label">Percentage:</span>
            <span class="value {getBudgetColor(metrics.budget.percentage)}">
              {metrics.budget.percentage.toFixed(1)}%
            </span>
          </div>
        </div>
      </div>
      
      <!-- Tokens Section -->
      <div class="metric-card tokens-card" transition:scale={{ duration: 300, delay: 100, easing: elasticOut }}>
        <div class="card-header">
          <h4 class="card-title">📊 Token Usage</h4>
          <span class="card-icon">🔤</span>
        </div>
        
        <div class="tokens-stats">
          <div class="stat-row">
            <span class="stat-label">Used:</span>
            <span class="stat-value">{formatTokens(metrics.tokens.used)}</span>
          </div>
          <div class="stat-row">
            <span class="stat-label">Remaining:</span>
            <span class="stat-value">{formatTokens(metrics.tokens.remaining)}</span>
          </div>
          <div class="stat-row">
            <span class="stat-label">Rate/Turn:</span>
            <span class="stat-value">{formatTokens(metrics.tokens.rate)}</span>
          </div>
        </div>
      </div>
      
      <!-- Performance Section -->
      <div class="metric-card performance-card" transition:scale={{ duration: 300, delay: 200, easing: elasticOut }}>
        <div class="card-header">
          <h4 class="card-title">⚡ Performance</h4>
          <span class="card-icon">🚀</span>
        </div>
        
        <div class="performance-stats">
          <div class="stat-row">
            <span class="stat-label">Avg Turn Time:</span>
            <span class="stat-value">{formatTime(metrics.performance.avg_turn_time)}</span>
          </div>
          <div class="stat-row">
            <span class="stat-label">Total Turns:</span>
            <span class="stat-value">{metrics.performance.total_turns}</span>
          </div>
          <div class="stat-row">
            <span class="stat-label">Active Agents:</span>
            <span class="stat-value">{metrics.performance.active_agents}</span>
          </div>
        </div>
      </div>
      
      <!-- Errors Section -->
      <div class="metric-card errors-card" transition:scale={{ duration: 300, delay: 300, easing: elasticOut }}>
        <div class="card-header">
          <h4 class="card-title">❌ Error Tracking</h4>
          <span class="card-icon">🚨</span>
        </div>
        
        <div class="errors-stats">
          <div class="stat-row">
            <span class="stat-label">Total Errors:</span>
            <span class="stat-value {getErrorColor(metrics.errors.error_rate)}">
              {metrics.errors.count}
            </span>
          </div>
          <div class="stat-row">
            <span class="stat-label">Error Rate:</span>
            <span class="stat-value {getErrorColor(metrics.errors.error_rate)}">
              {metrics.errors.error_rate.toFixed(1)}%
            </span>
          </div>
          {#if metrics.errors.last_error}
            <div class="error-detail">
              <span class="label">Last Error:</span>
              <span class="error-message">{metrics.errors.last_error}</span>
            </div>
          {/if}
        </div>
      </div>
      
      <!-- Agents Section -->
      <div class="metric-card agents-card" transition:scale={{ duration: 300, delay: 400, easing: elasticOut }}>
        <div class="card-header">
          <h4 class="card-title">🤖 Active Agents</h4>
          <span class="card-icon">👥</span>
        </div>
        
        <div class="agents-stats">
          <div class="stat-row">
            <span class="stat-label">Total:</span>
            <span class="stat-value">{metrics.agents.total}</span>
          </div>
          <div class="stat-row">
            <span class="stat-label">Active:</span>
            <span class="stat-value">{metrics.agents.active}</span>
          </div>
          
          {#if metrics.agents.names.length > 0}
            <div class="agents-list">
              <span class="label">Participants:</span>
              <div class="agent-tags">
                {#each metrics.agents.names as agentName}
                  <span class="agent-tag">{agentName}</span>
                {/each}
              </div>
            </div>
          {/if}
        </div>
      </div>
      
      <!-- Advanced Metrics (if enabled) -->
      {#if showAdvanced}
        <div class="metric-card advanced-card" transition:scale={{ duration: 300, delay: 500, easing: elasticOut }}>
          <div class="card-header">
            <h4 class="card-title">🔬 Advanced Metrics</h4>
            <span class="card-icon">📈</span>
          </div>
          
          <div class="advanced-stats">
            <div class="stat-row">
              <span class="stat-label">Memory Usage:</span>
              <span class="stat-value">Calculating...</span>
            </div>
            <div class="stat-row">
              <span class="stat-label">Cache Hit Rate:</span>
              <span class="stat-value">Calculating...</span>
            </div>
            <div class="stat-row">
              <span class="stat-label">Network Latency:</span>
              <span class="stat-value">Calculating...</span>
            </div>
          </div>
        </div>
      {/if}
    </div>
  {:else if !loading && !error}
    <div class="empty-state" transition:fade>
      <div class="empty-icon">📊</div>
      <p class="empty-message">No metrics available</p>
      <p class="empty-hint">Start a conversation to see real-time metrics</p>
    </div>
  {/if}
</div>

<style>
  .run-panel-container {
    @apply w-full max-w-7xl mx-auto p-4;
  }
  
  .panel-header {
    @apply flex justify-between items-center mb-6 p-4 bg-white rounded-lg shadow-sm border border-surface-200;
  }
  
  .panel-controls {
    @apply flex items-center gap-3;
  }
  
  .btn-refresh {
    @apply p-2 rounded-lg bg-blue-50 text-blue-600 hover:bg-blue-100 transition-colors disabled:opacity-50;
  }
  
  .last-update {
    @apply text-sm text-surface-500 flex items-center gap-1;
  }
  
  .loading-state, .error-state, .empty-state {
    @apply flex flex-col items-center justify-center py-12 text-center;
  }
  
  .loading-spinner {
    @apply w-8 h-8 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mb-4;
  }
  
  .error-icon {
    @apply text-4xl mb-4;
  }
  
  .error-message {
    @apply text-red-600 mb-4;
  }
  
  .btn-retry {
    @apply px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors;
  }
  
  .empty-icon {
    @apply text-4xl mb-4 text-gray-400;
  }
  
  .empty-message {
    @apply text-lg font-medium text-surface-600 mb-2;
  }
  
  .empty-hint {
    @apply text-sm text-surface-500;
  }
  
  .metrics-grid {
    @apply grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6;
  }
  
  .metric-card {
    @apply bg-white rounded-lg shadow-sm border border-surface-200 p-6 hover:shadow-md transition-shadow;
  }
  
  .card-header {
    @apply flex justify-between items-center mb-4;
  }
  
  .card-title {
    @apply text-lg font-semibold text-surface-900;
  }
  
  .card-icon {
    @apply text-2xl;
  }
  
  /* Budget Card */
  .budget-progress {
    @apply mb-4;
  }
  
  .progress-bar {
    @apply w-full h-3 bg-surface-200 rounded-full overflow-hidden mb-2;
  }
  
  .progress-fill {
    @apply h-full transition-all duration-500 ease-out;
  }
  
  .progress-labels {
    @apply flex justify-between text-sm text-surface-600;
  }
  
  .budget-details {
    @apply space-y-2;
  }
  
  .detail-item {
    @apply flex justify-between items-center;
  }
  
  .label {
    @apply text-surface-600;
  }
  
  .value {
    @apply font-medium;
  }
  
  /* Stats Rows */
  .stat-row {
    @apply flex justify-between items-center py-2 border-b border-gray-100 last:border-b-0;
  }
  
  .stat-label {
    @apply text-surface-600;
  }
  
  .stat-value {
    @apply font-medium text-surface-900;
  }
  
  /* Error Details */
  .error-detail {
    @apply mt-3 pt-3 border-t border-gray-100;
  }
  
  .error-message {
    @apply text-sm text-red-600 break-words;
  }
  
  /* Agents List */
  .agents-list {
    @apply mt-3 pt-3 border-t border-gray-100;
  }
  
  .agent-tags {
    @apply flex flex-wrap gap-2 mt-2;
  }
  
  .agent-tag {
    @apply px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full;
  }
  
  /* Responsive Design */
  @media (max-width: 768px) {
    .panel-header {
      @apply flex-col gap-4 items-start;
    }
    
    .panel-controls {
      @apply w-full justify-between;
    }
    
    .metrics-grid {
      @apply grid-cols-1 gap-4;
    }
    
    .metric-card {
      @apply p-4;
    }
  }
  
  /* Accessibility */
  .run-panel-container:focus-within {
    @apply outline-none;
  }
  
  .metric-card:focus-within {
    @apply ring-2 ring-blue-500 ring-offset-2;
  }
  
  /* Dark mode support */
  @media (prefers-color-scheme: dark) {
    .run-panel-container {
      @apply bg-gray-900 text-white;
    }
    
    .panel-header, .metric-card {
      @apply bg-gray-800 border-gray-700;
    }
    
    .card-title {
      @apply text-white;
    }
    
    .stat-value {
      @apply text-white;
    }
    
    .progress-bar {
      @apply bg-gray-600;
    }
  }
</style>
