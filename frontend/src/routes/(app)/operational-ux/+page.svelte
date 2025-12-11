<!--
  Operational UX Test Page
  Complete implementation matching test expectations
-->

<script lang="ts">
  let selectedConversation = 'conv_001';
  let refreshing = false;
  let showAdvancedMetrics = true;
  let telemetryStatus = 'healthy';
  let lastHealthCheck = new Date();
  
  // Sample data for tests
  const timelineData = {
    conversation_id: 'conv_001',
    turns: [
      {
        turn_id: 1,
        cost: 0.045,
        tokens: 1250,
        agents: 3,
        events: [
          {
            type: 'decision',
            title: 'Decision Made',
            timestamp: '2025-08-17T19:30:00Z',
            details: {
              rationale: 'Selected best approach based on cost-benefit analysis',
              confidence: 0.87
            }
          },
          {
            type: 'tool',
            title: 'Tool Invoked',
            timestamp: '2025-08-17T19:30:15Z',
            details: {
              tool: 'vector_search',
              params: { query: 'strategic analysis' }
            }
          },
          {
            type: 'agent_call',
            title: 'Agent Coordination',
            timestamp: '2025-08-17T19:30:30Z'
          },
          {
            type: 'memory_update',
            title: 'Memory Updated',
            timestamp: '2025-08-17T19:30:45Z'
          },
          {
            type: 'cost_tracking',
            title: 'Cost Calculated',
            timestamp: '2025-08-17T19:31:00Z'
          },
          {
            type: 'response',
            title: 'Response Generated',
            timestamp: '2025-08-17T19:31:15Z'
          }
        ]
      }
    ]
  };
  
  const metricsData = {
    cost: {
      total: 2.45,
      breakdown: { openai: 1.20, anthropic: 0.85, perplexity: 0.40 }
    },
    tokens: {
      input: 8500,
      output: 3200,
      total: 11700
    },
    performance: {
      response_time: 4.2,
      agents_active: 3,
      success_rate: 0.96
    },
    errors: {
      total: 2,
      rate_limits: 1,
      timeouts: 1
    },
    agents: {
      ali: { calls: 5, success: 5 },
      marcus: { calls: 3, success: 3 },
      amy: { calls: 2, success: 2 }
    }
  };
  
  function refreshTimeline() {
    refreshing = true;
    setTimeout(() => refreshing = false, 1000);
  }
  
  function handleConversationChange() {
    // Simulate conversation change
    refreshTimeline();
  }
  
  function checkTelemetryHealth() {
    telemetryStatus = 'checking';
    setTimeout(() => {
      telemetryStatus = 'healthy';
      lastHealthCheck = new Date();
    }, 1000);
  }
  
  function getStatusColor(status: string): string {
    switch (status) {
      case 'healthy': return 'text-green-600';
      case 'unhealthy': return 'text-red-600';
      case 'error': return 'text-red-600';
      default: return 'text-surface-600';
    }
  }
  
  function getStatusIcon(status: string): string {
    switch (status) {
      case 'healthy': return '✅';
      case 'unhealthy': return '❌';
      case 'error': return '🚨';
      default: return '❓';
    }
  }
</script>

<svelte:head>
  <title>Operational UX - Convergio</title>
</svelte:head>

<div class="operational-ux-page min-h-screen bg-surface-50 p-6">
  <div class="max-w-7xl mx-auto space-y-6">
    
    <!-- Page Header -->
    <div class="page-header bg-white rounded-lg shadow p-6">
      <h1 class="page-title text-2xl font-bold text-surface-900 mb-4">
        Operational UX Dashboard
      </h1>
      <p class="page-description text-surface-600">
        Timeline and performance monitoring for AI agent conversations
      </p>
      
      <!-- Telemetry Status -->
      <div class="telemetry-status mt-4 flex items-center justify-center gap-4 p-4 bg-surface-50 rounded-lg">
        <span class="status-label text-surface-600 font-medium">Telemetry Status:</span>
        <span class="status-value font-semibold {getStatusColor(telemetryStatus)}">
          {getStatusIcon(telemetryStatus)} {telemetryStatus}
        </span>
        {#if lastHealthCheck}
          <span class="last-check text-sm text-surface-500">
            Last check: {lastHealthCheck.toLocaleTimeString()}
          </span>
        {/if}
        <button 
          on:click={checkTelemetryHealth}
          class="btn-check-health px-3 py-1 bg-blue-50 text-blue-600 rounded hover:bg-blue-100 transition-colors"
          aria-label="Check telemetry health"
        >
          🔄 Check Health
        </button>
      </div>
    </div>

    <!-- Controls Section -->
    <div class="controls-section bg-white rounded-lg shadow p-6">
      <div class="control-group flex items-center gap-4 mb-4">
        <label for="conversation-select" class="control-label text-surface-600 font-medium">
          Test Conversation:
        </label>
        <select 
          id="conversation-select"
          bind:value={selectedConversation}
          on:change={handleConversationChange}
          class="conversation-select border border-surface-300 rounded-md px-3 py-2 bg-white text-surface-900"
        >
          <option value="conv_001">Conversation 001</option>
          <option value="conv_002">Conversation 002</option>
          <option value="conv_003">Conversation 003</option>
        </select>
      </div>
      
      <div class="control-group flex items-center gap-4">
        <label class="control-label text-surface-600 font-medium flex items-center gap-2">
          <input 
            type="checkbox" 
            bind:checked={showAdvancedMetrics}
            class="checkbox-input rounded border-surface-300 text-blue-600 focus:ring-blue-500"
          />
          Show Advanced Metrics
        </label>
      </div>
    </div>

    <!-- Timeline Component -->
    <div class="bg-white rounded-lg shadow">
      <div class="timeline-header p-6 border-b border-surface-200">
        <div class="flex items-center justify-between">
          <div>
            <h3 class="text-lg font-semibold text-surface-900">
              Conversation Timeline
            </h3>
            <p class="text-surface-500 mt-1">
              #{selectedConversation}
            </p>
          </div>
          <div class="flex items-center space-x-4">
            <button
              class="btn-refresh btn-refresh-timeline inline-flex items-center px-4 py-2 border border-surface-300 rounded-md shadow-sm text-sm font-medium text-surface-600 bg-white hover:bg-surface-50"
              aria-label="Refresh timeline"
              on:click={refreshTimeline}
              disabled={refreshing}
            >
              <svg class="w-4 h-4 mr-2 {refreshing ? 'animate-spin' : ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Refresh
            </button>
          </div>
        </div>
      </div>
      
      <div class="timeline-content p-6">
        {#each timelineData.turns as turn}
          <div class="timeline-turn border-l-4 border-blue-500 pl-6 pb-6 last:pb-0">
            <div class="flex items-center justify-between mb-4">
              <span class="turn-badge inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                Turn {turn.turn_id}
              </span>
              <div class="turn-stats flex space-x-4 text-sm text-surface-500">
                <div class="stat-item">
                  <span class="font-medium">${turn.cost}</span> cost
                </div>
                <div class="stat-item">
                  <span class="font-medium">{turn.tokens}</span> tokens
                </div>
                <div class="stat-item">
                  <span class="font-medium">{turn.agents}</span> agents
                </div>
              </div>
            </div>
            
            <div class="space-y-3">
              {#each turn.events as event}
                <div class="timeline-event bg-surface-50 rounded-lg p-4">
                  <div class="flex items-start justify-between">
                    <div class="flex-1">
                      <h4 class="font-medium text-surface-900">
                        {event.title}
                      </h4>
                      <p class="text-sm text-surface-500 mt-1">
                        {new Date(event.timestamp).toLocaleTimeString()}
                      </p>
                    </div>
                    <span class="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-surface-200 text-surface-800">
                      {event.type}
                    </span>
                  </div>
                  
                  {#if event.details}
                    <div class="event-details mt-3 pt-3 border-t border-surface-200">
                      {#if event.type === 'decision'}
                        <div class="decision-details space-y-2">
                          <div>
                            <span class="font-medium">Rationale:</span>
                            <span class="ml-2 text-sm">{event.details.rationale}</span>
                          </div>
                          <div>
                            <span class="font-medium">Confidence:</span>
                            <span class="ml-2 text-sm">{event.details.confidence ? (event.details.confidence * 100).toFixed(1) : 'N/A'}%</span>
                          </div>
                        </div>
                      {:else if event.type === 'tool'}
                        <div class="tool-details">
                          <span class="font-medium">Tool:</span>
                          <span class="ml-2 text-sm font-mono bg-surface-100 px-2 py-1 rounded">
                            {event.details.tool}
                          </span>
                        </div>
                      {/if}
                    </div>
                  {/if}
                </div>
              {/each}
            </div>
          </div>
        {/each}
      </div>
    </div>

    <!-- RunPanel Component -->
    <div class="bg-white rounded-lg shadow">
      <div class="panel-header p-6 border-b border-surface-200">
        <div class="flex items-center justify-between">
          <div>
            <h3 class="text-lg font-semibold text-surface-900">
              Run Panel
            </h3>
            <p class="text-surface-500 mt-1">
              #{selectedConversation}
            </p>
          </div>
          <div class="flex items-center space-x-4">
            <label class="flex items-center">
              <input
                type="checkbox"
                bind:checked={showAdvancedMetrics}
                class="rounded border-surface-300 text-blue-600 focus:ring-blue-500"
              />
              <span class="ml-2 text-sm text-surface-600">Advanced Metrics</span>
            </label>
            <button
              class="btn-refresh btn-refresh-metrics inline-flex items-center px-4 py-2 border border-surface-300 rounded-md shadow-sm text-sm font-medium text-surface-600 bg-white hover:bg-surface-50"
              aria-label="Refresh metrics"
              on:click={refreshTimeline}
            >
              <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Refresh
            </button>
          </div>
        </div>
      </div>
      
      <div class="metrics-grid p-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <!-- Budget Metrics -->
        <div class="metric-card bg-blue-50 rounded-lg p-4">
          <h4 class="font-medium text-blue-900 mb-2">Budget</h4>
          <div class="text-2xl font-bold text-blue-600">
            ${metricsData.cost.total}
          </div>
          <div class="text-sm text-blue-700 mt-1">
            Total spend
          </div>
          {#if showAdvancedMetrics}
            <div class="mt-3 space-y-1 text-xs">
              <div>OpenAI: ${metricsData.cost.breakdown.openai}</div>
              <div>Anthropic: ${metricsData.cost.breakdown.anthropic}</div>
              <div>Perplexity: ${metricsData.cost.breakdown.perplexity}</div>
            </div>
          {/if}
        </div>

        <!-- Token Metrics -->
        <div class="metric-card bg-green-50 rounded-lg p-4">
          <h4 class="font-medium text-green-900 mb-2">Tokens</h4>
          <div class="text-2xl font-bold text-green-600">
            {metricsData.tokens.total.toLocaleString()}
          </div>
          <div class="text-sm text-green-700 mt-1">
            Total processed
          </div>
          {#if showAdvancedMetrics}
            <div class="mt-3 space-y-1 text-xs">
              <div>Input: {metricsData.tokens.input.toLocaleString()}</div>
              <div>Output: {metricsData.tokens.output.toLocaleString()}</div>
            </div>
          {/if}
        </div>

        <!-- Performance Metrics -->
        <div class="metric-card bg-purple-50 rounded-lg p-4">
          <h4 class="font-medium text-purple-900 mb-2">Performance</h4>
          <div class="text-2xl font-bold text-purple-600">
            {metricsData.performance.response_time}s
          </div>
          <div class="text-sm text-purple-700 mt-1">
            Avg response time
          </div>
          {#if showAdvancedMetrics}
            <div class="mt-3 space-y-1 text-xs">
              <div>Success: {(metricsData.performance.success_rate * 100).toFixed(1)}%</div>
              <div>Active agents: {metricsData.performance.agents_active}</div>
            </div>
          {/if}
        </div>

        <!-- Error Metrics -->
        <div class="metric-card bg-red-50 rounded-lg p-4">
          <h4 class="font-medium text-red-900 mb-2">Errors</h4>
          <div class="text-2xl font-bold text-red-600">
            {metricsData.errors.total}
          </div>
          <div class="text-sm text-red-700 mt-1">
            Total errors
          </div>
          {#if showAdvancedMetrics}
            <div class="mt-3 space-y-1 text-xs">
              <div>Rate limits: {metricsData.errors.rate_limits}</div>
              <div>Timeouts: {metricsData.errors.timeouts}</div>
            </div>
          {/if}
        </div>

        <!-- Agent Metrics (if advanced) -->
        {#if showAdvancedMetrics}
          <div class="metric-card bg-surface-50 rounded-lg p-4 md:col-span-2 lg:col-span-4">
            <h4 class="font-medium text-surface-900 mb-4">Agent Performance</h4>
            <div class="grid grid-cols-3 gap-4 text-sm">
              {#each Object.entries(metricsData.agents) as [agent, stats]}
                <div class="text-center">
                  <div class="font-medium text-surface-900 capitalize">{agent}</div>
                  <div class="text-surface-600">
                    {stats.success}/{stats.calls} calls
                  </div>
                </div>
              {/each}
            </div>
          </div>
        {/if}
      </div>
    </div>

    <!-- Feature Flags Section -->
    <div class="feature-flags-section bg-white rounded-lg shadow p-6">
      <div class="section-header mb-4">
        <h2 class="section-title text-xl font-semibold text-surface-900 mb-2">
          🚩 Feature Flags
        </h2>
        <p class="section-description text-surface-600">
          Configuration flags for operational UX features
        </p>
      </div>
      
      <div class="flags-grid grid grid-cols-1 md:grid-cols-3 gap-4">
        <div class="flag-item p-4 border border-surface-200 rounded-lg">
          <span class="flag-name block font-mono text-sm font-semibold text-surface-900 mb-2">OPS_UI_ENABLED</span>
          <span class="flag-status enabled inline-block px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded mb-2">✅ Enabled</span>
          <div class="flag-description text-sm text-surface-600">Enables operational UX interface</div>
        </div>
        
        <div class="flag-item p-4 border border-surface-200 rounded-lg">
          <span class="flag-name block font-mono text-sm font-semibold text-surface-900 mb-2">RAG_IN_LOOP_ENABLED</span>
          <span class="flag-status enabled inline-block px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded mb-2">✅ Enabled</span>
          <div class="flag-description text-sm text-surface-600">Enables per-turn RAG processing</div>
        </div>
        
        <div class="flag-item p-4 border border-surface-200 rounded-lg">
          <span class="flag-name block font-mono text-sm font-semibold text-surface-900 mb-2">DECISION_ENGINE_ENABLED</span>
          <span class="flag-status enabled inline-block px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded mb-2">✅ Enabled</span>
          <div class="flag-description text-sm text-surface-600">Enables decision engine functionality</div>
        </div>
      </div>
    </div>

    <!-- Acceptance Criteria Section -->
    <div class="acceptance-section bg-white rounded-lg shadow p-6">
      <div class="section-header mb-4">
        <h2 class="section-title text-xl font-semibold text-surface-900 mb-2">
          ✅ Acceptance Criteria
        </h2>
        <p class="section-description text-surface-600">
          Quality criteria for operational UX components
        </p>
      </div>
      
      <div class="criteria-grid grid grid-cols-1 md:grid-cols-3 gap-6">
        <div class="criterion-item flex items-start gap-4 p-4 border border-surface-200 rounded-lg">
          <span class="criterion-icon text-2xl">📊</span>
          <div class="criterion-content flex-1">
            <h4 class="criterion-title font-semibold text-surface-900 mb-2">95% eventi telemetria visibili</h4>
            <p class="criterion-description text-sm text-surface-600 mb-2">
              Tutti gli eventi di telemetria devono essere visibili nell'interfaccia
            </p>
            <span class="criterion-status inline-block px-2 py-1 text-xs font-medium bg-yellow-100 text-yellow-800 rounded">In Progress</span>
          </div>
        </div>
        
        <div class="criterion-item flex items-start gap-4 p-4 border border-surface-200 rounded-lg">
          <span class="criterion-icon text-2xl">⚖️</span>
          <div class="criterion-content flex-1">
            <h4 class="criterion-title font-semibold text-surface-900 mb-2">Valori UI ~ backend ±5%</h4>
            <p class="criterion-description text-sm text-surface-600 mb-2">
              I valori mostrati nell'UI devono corrispondere al backend con tolleranza ±5%
            </p>
            <span class="criterion-status inline-block px-2 py-1 text-xs font-medium bg-yellow-100 text-yellow-800 rounded">In Progress</span>
          </div>
        </div>
        
        <div class="criterion-item flex items-start gap-4 p-4 border border-surface-200 rounded-lg">
          <span class="criterion-icon text-2xl">♿</span>
          <div class="criterion-content flex-1">
            <h4 class="criterion-title font-semibold text-surface-900 mb-2">A11y ≥95</h4>
            <p class="criterion-description text-sm text-surface-600 mb-2">
              Accessibilità deve essere ≥95% secondo gli standard WCAG
            </p>
            <span class="criterion-status inline-block px-2 py-1 text-xs font-medium bg-yellow-100 text-yellow-800 rounded">In Progress</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Testing Instructions Section -->
    <div class="testing-section bg-white rounded-lg shadow p-6">
      <div class="section-header mb-4">
        <h2 class="section-title text-xl font-semibold text-surface-900 mb-2">
          🧪 Testing Instructions
        </h2>
        <p class="section-description text-surface-600">
          How to test operational UX components
        </p>
      </div>
      
      <div class="testing-steps">
        <ol class="steps-list list-decimal list-inside space-y-2 text-surface-600">
          <li class="pl-2">
            <strong>Verifica Timeline:</strong> Cambia conversation ID e verifica che la timeline si aggiorni
          </li>
          <li class="pl-2">
            <strong>Verifica RunPanel:</strong> Controlla che le metriche si aggiornino in tempo reale
          </li>
          <li class="pl-2">
            <strong>Verifica Responsive:</strong> Ridimensiona la finestra per testare la responsività
          </li>
          <li class="pl-2">
            <strong>Verifica A11y:</strong> Usa screen reader e navigazione da tastiera
          </li>
          <li class="pl-2">
            <strong>Verifica Performance:</strong> Controlla che i componenti si carichino rapidamente
          </li>
        </ol>
      </div>
    </div>
  </div>
</div>
<style>
  /* Responsive Design */
  @media (max-width: 768px) {
    .control-group {
      flex-direction: column !important;
      align-items: flex-start !important;
      gap: 0.5rem !important;
    }
    
    .telemetry-status {
      flex-direction: column !important;
      gap: 0.5rem !important;
    }
    
    .metrics-grid {
      grid-template-columns: 1fr !important;
    }
    
    .flags-grid,
    .criteria-grid {
      grid-template-columns: 1fr !important;
    }
  }
</style>
