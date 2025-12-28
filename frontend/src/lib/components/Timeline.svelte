<!--
Timeline Component - Visualizza timeline per-turn delle conversazioni
Include speaker, tools, fonti, costi, razionali per ogni turn
-->

<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { fade, fly } from 'svelte/transition';
  import { quintOut } from 'svelte/easing';
  
  // Props
  export let conversationId: string;
  export let autoRefresh: boolean = true;
  export let showDetails: boolean = true;
  
  // State
  let timeline: any[] = [];
  let loading = false;
  let error: string | null = null;
  let refreshInterval: number | null = null;
  
  // Types
  interface TimelineEvent {
    event_type: string;
    agent_name?: string;
    data: any;
    timestamp: string;
  }
  
  interface TimelineTurn {
    turn_number: number;
    timestamp: string;
    events: TimelineEvent[];
    agents_involved: string[];
    total_cost: number;
    total_tokens: number;
  }
  
  // Methods
  async function loadTimeline() {
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
        timeline = result.data.timeline || [];
      } else {
        throw new Error(result.error || 'Failed to load timeline');
      }
    } catch (err) {
      // Silent failure
      error = err instanceof Error ? err.message : 'Unknown error occurred';
    } finally {
      loading = false;
    }
  }
  
  function formatTimestamp(timestamp: string): string {
    try {
      const date = new Date(timestamp);
      return date.toLocaleTimeString();
    } catch {
      return timestamp;
    }
  }
  
  function formatCost(cost: number): string {
    return `$${cost.toFixed(4)}`;
  }
  
  function formatTokens(tokens: number): string {
    return tokens.toLocaleString();
  }
  
  function getEventIcon(eventType: string): string {
    const icons: Record<string, string> = {
      'conversation.start': '🚀',
      'conversation.end': '🏁',
      'decision_made': '🎯',
      'tool_invoked': '🔧',
      'budget_event': '💰',
      'rag_injected': '🧠',
      'conflict_detected': '⚠️',
      'conflict_resolved': '✅',
      'agent.invocation': '🤖',
      'agent.response': '💬',
      'error.occurred': '❌'
    };
    return icons[eventType] || '📝';
  }
  
  function getEventColor(eventType: string): string {
    const colors: Record<string, string> = {
      'conversation.start': 'bg-blue-100 border-blue-300',
      'conversation.end': 'bg-green-100 border-green-300',
      'decision_made': 'bg-purple-100 border-purple-300',
      'tool_invoked': 'bg-orange-100 border-orange-300',
      'budget_event': 'bg-yellow-100 border-yellow-300',
      'rag_injected': 'bg-indigo-100 border-indigo-300',
      'conflict_detected': 'bg-red-100 border-red-300',
      'conflict_resolved': 'bg-emerald-100 border-emerald-300',
      'error.occurred': 'bg-red-100 border-red-300'
    };
    return colors[eventType] || 'bg-surface-100 border-surface-300';
  }
  
  function getEventTitle(eventType: string): string {
    const titles: Record<string, string> = {
      'conversation.start': 'Conversation Started',
      'conversation.end': 'Conversation Ended',
      'decision_made': 'Decision Made',
      'tool_invoked': 'Tool Invoked',
      'budget_event': 'Budget Update',
      'rag_injected': 'RAG Context Injected',
      'conflict_detected': 'Conflict Detected',
      'conflict_resolved': 'Conflict Resolved',
      'agent.invocation': 'Agent Invoked',
      'agent.response': 'Agent Response',
      'error.occurred': 'Error Occurred'
    };
    return titles[eventType] || eventType.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  }
  
  // Lifecycle
  onMount(() => {
    loadTimeline();
    
    if (autoRefresh) {
      refreshInterval = window.setInterval(loadTimeline, 5000); // Refresh every 5 seconds
    }
  });
  
  onDestroy(() => {
    if (refreshInterval) {
      clearInterval(refreshInterval);
    }
  });
  
  // Reactive statements
  $: if (conversationId) {
    loadTimeline();
  }
</script>

<div class="timeline-container">
  <!-- Header -->
  <div class="timeline-header">
    <h3 class="text-lg font-semibold text-surface-900">
      Conversation Timeline
      {#if conversationId}
        <span class="text-sm font-normal text-surface-500">#{conversationId}</span>
      {/if}
    </h3>
    
    <div class="timeline-controls">
      <button 
        on:click={loadTimeline}
        disabled={loading}
        class="btn-refresh"
        aria-label="Refresh timeline"
      >
        {#if loading}
          <span class="animate-spin">🔄</span>
        {:else}
          🔄
        {/if}
      </button>
    </div>
  </div>
  
  <!-- Loading State -->
  {#if loading && timeline.length === 0}
    <div class="loading-state" transition:fade>
      <div class="loading-spinner"></div>
      <p class="text-surface-500">Loading timeline...</p>
    </div>
  {/if}
  
  <!-- Error State -->
  {#if error}
    <div class="error-state" transition:fade>
      <div class="error-icon">⚠️</div>
      <p class="error-message">{error}</p>
      <button on:click={loadTimeline} class="btn-retry">
        Try Again
      </button>
    </div>
  {/if}
  
  <!-- Timeline Content -->
  {#if timeline.length > 0}
    <div class="timeline-content">
      {#each timeline as turn, index (turn.turn_number)}
        <div class="timeline-turn" transition:fly={{ y: 20, duration: 300, delay: index * 100, easing: quintOut }}>
          <!-- Turn Header -->
          <div class="turn-header">
            <div class="turn-number">
              <span class="turn-badge">Turn {turn.turn_number}</span>
              <span class="turn-time">{formatTimestamp(turn.timestamp)}</span>
            </div>
            
            <div class="turn-stats">
              <span class="stat-item" title="Total cost for this turn">
                💰 {formatCost(turn.total_cost)}
              </span>
              <span class="stat-item" title="Total tokens used">
                📊 {formatTokens(turn.total_tokens)}
              </span>
              <span class="stat-item" title="Agents involved">
                🤖 {turn.agents_involved.length}
              </span>
            </div>
          </div>
          
          <!-- Turn Events -->
          <div class="turn-events">
            {#each turn.events as event, eventIndex (event.timestamp + eventIndex)}
              <div class="timeline-event {getEventColor(event.event_type)}" transition:fade>
                <div class="event-header">
                  <span class="event-icon">{getEventIcon(event.event_type)}</span>
                  <span class="event-title">{getEventTitle(event.event_type)}</span>
                  {#if event.agent_name}
                    <span class="event-agent">by {event.agent_name}</span>
                  {/if}
                  <span class="event-time">{formatTimestamp(event.timestamp)}</span>
                </div>
                
                {#if showDetails && event.data}
                  <div class="event-details">
                    {#if event.event_type === 'decision_made'}
                      <div class="decision-details">
                        <p><strong>Rationale:</strong> {event.data.rationale || 'N/A'}</p>
                        <p><strong>Confidence:</strong> {(event.data.confidence * 100).toFixed(1)}%</p>
                        {#if event.data.sources && event.data.sources.length > 0}
                          <p><strong>Sources:</strong> {event.data.sources.join(', ')}</p>
                        {/if}
                        {#if event.data.tools && event.data.tools.length > 0}
                          <p><strong>Tools:</strong> {event.data.tools.join(', ')}</p>
                        {/if}
                      </div>
                    {:else if event.event_type === 'tool_invoked'}
                      <div class="tool-details">
                        <p><strong>Tool:</strong> {event.data.tool_name || 'N/A'}</p>
                        {#if event.data.execution_time}
                          <p><strong>Execution Time:</strong> {event.data.execution_time.toFixed(2)}s</p>
                        {/if}
                        {#if event.data.input}
                          <p><strong>Input:</strong> <code class="text-xs">{JSON.stringify(event.data.input)}</code></p>
                        {/if}
                      </div>
                    {:else if event.event_type === 'budget_event'}
                      <div class="budget-details">
                        <p><strong>Current Cost:</strong> {formatCost(event.data.current_cost || 0)}</p>
                        <p><strong>Remaining Budget:</strong> {formatCost(event.data.remaining_budget || 0)}</p>
                        <p><strong>Tokens Used:</strong> {formatTokens(event.data.tokens_used || 0)}</p>
                      </div>
                    {:else if event.event_type === 'rag_injected'}
                      <div class="rag-details">
                        <p><strong>Context Items:</strong> {event.data.context_items || 0}</p>
                        <p><strong>Hit Rate:</strong> {(event.data.hit_rate * 100).toFixed(1)}%</p>
                        <p><strong>Latency:</strong> {(event.data.latency * 1000).toFixed(1)}ms</p>
                      </div>
                    {:else if event.event_type.startsWith('conflict_')}
                      <div class="conflict-details">
                        <p><strong>Type:</strong> {event.event_type}</p>
                        {#if event.data.description}
                          <p><strong>Description:</strong> {event.data.description}</p>
                        {/if}
                        {#if event.data.involved_agents && event.data.involved_agents.length > 0}
                          <p><strong>Involved Agents:</strong> {event.data.involved_agents.join(', ')}</p>
                        {/if}
                      </div>
                    {:else}
                      <div class="generic-details">
                        <pre class="text-xs overflow-auto">{JSON.stringify(event.data, null, 2)}</pre>
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
  {:else if !loading && !error}
    <div class="empty-state" transition:fade>
      <div class="empty-icon">📝</div>
      <p class="empty-message">No timeline data available</p>
      <p class="empty-hint">Start a conversation to see the timeline</p>
    </div>
  {/if}
</div>

<style>
  .timeline-container {
    @apply w-full max-w-6xl mx-auto p-4;
  }
  
  .timeline-header {
    @apply flex justify-between items-center mb-6 p-4 bg-white rounded-lg shadow-sm border border-surface-200;
  }
  
  .timeline-controls {
    @apply flex gap-2;
  }
  
  .btn-refresh {
    @apply p-2 rounded-lg bg-blue-50 text-blue-600 hover:bg-blue-100 transition-colors disabled:opacity-50;
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
  
  .timeline-content {
    @apply space-y-6;
  }
  
  .timeline-turn {
    @apply bg-white rounded-lg shadow-sm border border-surface-200 overflow-hidden;
  }
  
  .turn-header {
    @apply flex justify-between items-center p-4 bg-surface-50 border-b border-surface-200;
  }
  
  .turn-number {
    @apply flex items-center gap-3;
  }
  
  .turn-badge {
    @apply px-3 py-1 bg-blue-600 text-white text-sm font-medium rounded-full;
  }
  
  .turn-time {
    @apply text-sm text-surface-600;
  }
  
  .turn-stats {
    @apply flex gap-4;
  }
  
  .stat-item {
    @apply text-sm text-surface-600 flex items-center gap-1;
  }
  
  .turn-events {
    @apply p-4 space-y-3;
  }
  
  .timeline-event {
    @apply p-4 rounded-lg border transition-all duration-200 hover:shadow-md;
  }
  
  .event-header {
    @apply flex items-center gap-3 mb-3 flex-wrap;
  }
  
  .event-icon {
    @apply text-lg;
  }
  
  .event-title {
    @apply font-medium text-surface-900;
  }
  
  .event-agent {
    @apply text-sm text-surface-600 bg-surface-100 px-2 py-1 rounded;
  }
  
  .event-time {
    @apply text-sm text-surface-500 ml-auto;
  }
  
  .event-details {
    @apply mt-3 pt-3 border-t border-surface-200;
  }
  
  .decision-details, .tool-details, .budget-details, .rag-details, .conflict-details {
    @apply space-y-2 text-sm;
  }
  
  .generic-details {
    @apply mt-2;
  }
  
  .generic-details pre {
    @apply bg-surface-100 p-2 rounded text-surface-600;
  }
  
  /* Responsive Design */
  @media (max-width: 768px) {
    .timeline-header {
      @apply flex-col gap-4 items-start;
    }
    
    .turn-header {
      @apply flex-col gap-3 items-start;
    }
    
    .turn-stats {
      @apply flex-wrap gap-2;
    }
    
    .event-header {
      @apply flex-col items-start gap-2;
    }
    
    .event-time {
      @apply ml-0;
    }
  }
  
  /* Accessibility */
  .timeline-container:focus-within {
    @apply outline-none;
  }
  
  .timeline-event:focus-within {
    @apply ring-2 ring-blue-500 ring-offset-2;
  }
  
  /* Dark mode support */
  @media (prefers-color-scheme: dark) {
    .timeline-container {
      @apply bg-gray-900 text-white;
    }
    
    .timeline-header, .timeline-turn {
      @apply bg-gray-800 border-gray-700;
    }
    
    .turn-header {
      @apply bg-gray-700 border-gray-600;
    }
    
    .event-title {
      @apply text-white;
    }
    
    .timeline-event {
      @apply border-gray-600;
    }
  }
</style>
