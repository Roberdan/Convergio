<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { writable } from 'svelte/store';
  import { slide } from 'svelte/transition';
  
  interface Suggestion {
    id: string;
    type: 'optimization' | 'warning' | 'insight' | 'action';
    priority: 'high' | 'medium' | 'low';
    title: string;
    description: string;
    explanation: string;
    impact: string;
    actions: ActionItem[];
    timestamp: Date;
    dismissed: boolean;
    applied: boolean;
  }
  
  interface ActionItem {
    id: string;
    label: string;
    type: 'primary' | 'secondary' | 'danger';
    handler: () => void;
  }
  
  interface Metric {
    name: string;
    value: number;
    change: number;
    trend: 'up' | 'down' | 'stable';
  }
  
  export const projectId: string = '';
  export const userId: string = '';
  export let position: 'right' | 'left' = 'right';
  export let expanded: boolean = true;
  
  let suggestions = writable<Suggestion[]>([]);
  let metrics = writable<Metric[]>([]);
  let loading = false;
  let filterType = 'all';
  let showDismissed = false;
  let autoRefresh = true;
  let refreshInterval: ReturnType<typeof setInterval> | undefined;
  
  onMount(() => {
    loadSuggestions();
    loadMetrics();
    
    if (autoRefresh) {
      refreshInterval = setInterval(() => {
        loadSuggestions();
        loadMetrics();
      }, 30000); // Refresh every 30 seconds
    }
  });
  
  onDestroy(() => {
    if (refreshInterval) {
      clearInterval(refreshInterval);
    }
  });
  
  async function loadSuggestions() {
    loading = true;
    
    // Mock suggestions from Ali
    const mockSuggestions: Suggestion[] = [
      {
        id: 's1',
        type: 'optimization',
        priority: 'high',
        title: 'Resource Optimization Opportunity',
        description: 'David Kumar is underutilized at 45%. Consider assigning to Mobile App Launch project.',
        explanation: 'Based on skill match analysis, David\'s Kubernetes and Docker expertise would accelerate the Mobile App Launch deployment phase by 2 weeks.',
        impact: 'Save $15,000 in project costs and reduce timeline by 2 weeks',
        actions: [
          {
            id: 'a1',
            label: 'Assign David to Project',
            type: 'primary',
            handler: () => assignResource('David Kumar', 'Mobile App Launch')
          },
          {
            id: 'a2',
            label: 'View Details',
            type: 'secondary',
            handler: () => viewResourceDetails('David Kumar')
          }
        ],
        timestamp: new Date(),
        dismissed: false,
        applied: false
      },
      {
        id: 's2',
        type: 'warning',
        priority: 'high',
        title: 'Budget Risk Detected',
        description: 'AI Platform Development is trending 15% over budget with 6 weeks remaining.',
        explanation: 'Current burn rate suggests project will exceed budget by $45,000. Primary driver is unplanned ML infrastructure costs.',
        impact: 'Potential $45,000 budget overrun',
        actions: [
          {
            id: 'a3',
            label: 'Review Budget',
            type: 'primary',
            handler: () => reviewBudget('AI Platform Development')
          },
          {
            id: 'a4',
            label: 'Optimize Costs',
            type: 'secondary',
            handler: () => optimizeCosts('AI Platform Development')
          }
        ],
        timestamp: new Date(Date.now() - 3600000),
        dismissed: false,
        applied: false
      },
      {
        id: 's3',
        type: 'insight',
        priority: 'medium',
        title: 'Team Velocity Improvement',
        description: 'Engineering team velocity increased 23% after implementing pair programming.',
        explanation: 'Analysis shows code review time decreased by 40% and bug density reduced by 35% since implementing pair programming sessions.',
        impact: 'Delivering features 2.3x faster with higher quality',
        actions: [
          {
            id: 'a5',
            label: 'Expand Practice',
            type: 'primary',
            handler: () => expandPractice('pair programming')
          },
          {
            id: 'a6',
            label: 'Share Report',
            type: 'secondary',
            handler: () => shareReport('velocity improvement')
          }
        ],
        timestamp: new Date(Date.now() - 7200000),
        dismissed: false,
        applied: false
      },
      {
        id: 's4',
        type: 'action',
        priority: 'medium',
        title: 'Dependency Conflict Resolution',
        description: 'Customer Portal Redesign blocked by unassigned UX research task.',
        explanation: 'The project timeline shows a 1-week delay risk. Bob Martinez has availability and the required skills.',
        impact: 'Prevent 1-week delay in project delivery',
        actions: [
          {
            id: 'a7',
            label: 'Resolve Conflict',
            type: 'primary',
            handler: () => resolveConflict('Customer Portal Redesign')
          },
          {
            id: 'a8',
            label: 'Adjust Timeline',
            type: 'secondary',
            handler: () => adjustTimeline('Customer Portal Redesign')
          }
        ],
        timestamp: new Date(Date.now() - 10800000),
        dismissed: false,
        applied: false
      },
      {
        id: 's5',
        type: 'optimization',
        priority: 'low',
        title: 'Meeting Efficiency Suggestion',
        description: 'Reduce weekly sync meetings from 60 to 30 minutes based on participation data.',
        explanation: 'Analysis shows only 35% of meeting time involves active discussion. Async updates could cover status reports.',
        impact: 'Save 10 hours per week across the team',
        actions: [
          {
            id: 'a9',
            label: 'Optimize Meetings',
            type: 'primary',
            handler: () => optimizeMeetings()
          },
          {
            id: 'a10',
            label: 'Dismiss',
            type: 'secondary',
            handler: () => dismissSuggestion('s5')
          }
        ],
        timestamp: new Date(Date.now() - 14400000),
        dismissed: false,
        applied: false
      }
    ];
    
    suggestions.set(mockSuggestions);
    loading = false;
  }
  
  async function loadMetrics() {
    // Mock metrics
    metrics.set([
      { name: 'Suggestions Applied', value: 12, change: 3, trend: 'up' },
      { name: 'Cost Savings', value: 45000, change: 15000, trend: 'up' },
      { name: 'Time Saved (hours)', value: 120, change: 20, trend: 'up' },
      { name: 'Accuracy Rate', value: 94, change: 2, trend: 'up' }
    ]);
  }
  
  function assignResource(_r: string, _p: string) {
    void _r; void _p;
    markSuggestionApplied('s1');
  }

  function viewResourceDetails(_r: string) {
    void _r;
  }

  function reviewBudget(_p: string) {
    void _p;
    // Review budget
  }

  function optimizeCosts(_p: string) {
    void _p;
  }

  function expandPractice(_p: string) {
    void _p;
  }

  function shareReport(_r: string) {
    void _r;
  }

  function resolveConflict(_p: string) {
    void _p;
    // Resolve conflict
  }

  function adjustTimeline(_p: string) {
    void _p;
  }

  function optimizeMeetings() {
    // Optimize meetings
  }
  
  function dismissSuggestion(id: string) {
    suggestions.update(items => 
      items.map(s => s.id === id ? { ...s, dismissed: true } : s)
    );
  }
  
  function markSuggestionApplied(id: string) {
    suggestions.update(items => 
      items.map(s => s.id === id ? { ...s, applied: true } : s)
    );
  }
  
  function getTypeIcon(type: string): string {
    switch (type) {
      case 'optimization': return '⚡';
      case 'warning': return '⚠️';
      case 'insight': return '💡';
      case 'action': return '🎯';
      default: return '📌';
    }
  }
  
  function getTypeColor(type: string): string {
    switch (type) {
      case 'optimization': return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'warning': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'insight': return 'bg-purple-100 text-purple-800 border-purple-200';
      case 'action': return 'bg-green-100 text-green-800 border-green-200';
      default: return 'bg-surface-100 text-surface-800 border-surface-200';
    }
  }
  
  function getPriorityColor(priority: string): string {
    switch (priority) {
      case 'high': return 'bg-red-500';
      case 'medium': return 'bg-yellow-500';
      case 'low': return 'bg-green-500';
      default: return 'bg-surface-500';
    }
  }
  
  function formatTimeAgo(date: Date): string {
    const seconds = Math.floor((new Date().getTime() - date.getTime()) / 1000);
    if (seconds < 60) return 'just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)} min ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)} hours ago`;
    return `${Math.floor(seconds / 86400)} days ago`;
  }
  
  $: filteredSuggestions = $suggestions.filter(s => {
    const matchesType = filterType === 'all' || s.type === filterType;
    const matchesVisibility = showDismissed || !s.dismissed;
    return matchesType && matchesVisibility && !s.applied;
  });
  
  $: activeSuggestions = $suggestions.filter(s => !s.dismissed && !s.applied);
</script>

<div class="ali-coach-panel {position === 'left' ? 'left-0' : 'right-0'} {expanded ? 'expanded' : 'collapsed'}">
  <div class="panel-container">
    <!-- Header -->
    <div class="panel-header">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <span class="text-2xl">🤖</span>
          <div>
            <h3 class="font-semibold text-surface-900">Ali Coach</h3>
            <p class="text-xs text-surface-600">AI-Powered Insights</p>
          </div>
        </div>
        <button
          on:click={() => expanded = !expanded}
          class="p-1 hover:bg-surface-100 rounded"
          aria-label={expanded ? 'Collapse panel' : 'Expand panel'}
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            {#if expanded}
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            {:else}
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
            {/if}
          </svg>
        </button>
      </div>
      
      {#if expanded}
        <!-- Metrics Summary -->
        <div class="grid grid-cols-2 gap-2 mt-3">
          {#each $metrics.slice(0, 2) as metric}
            <div class="bg-surface-50 rounded p-2">
              <div class="text-xs text-surface-600">{metric.name}</div>
              <div class="flex items-center gap-1">
                <span class="font-semibold text-sm">
                  {metric.name.includes('Cost') ? '$' : ''}{metric.value.toLocaleString()}
                </span>
                <span class="text-xs {metric.trend === 'up' ? 'text-green-600' : 'text-red-600'}">
                  {metric.trend === 'up' ? '↑' : '↓'} {Math.abs(metric.change)}
                </span>
              </div>
            </div>
          {/each}
        </div>
      {/if}
    </div>
    
    {#if expanded}
      <!-- Filter Bar -->
      <div class="panel-filters">
        <select
          bind:value={filterType}
          class="text-sm px-2 py-1 border rounded"
        >
          <option value="all">All Types</option>
          <option value="optimization">Optimizations</option>
          <option value="warning">Warnings</option>
          <option value="insight">Insights</option>
          <option value="action">Actions</option>
        </select>
        
        <label class="flex items-center gap-1 text-sm">
          <input type="checkbox" bind:checked={showDismissed} />
          <span>Show dismissed</span>
        </label>
        
        <label class="flex items-center gap-1 text-sm">
          <input type="checkbox" bind:checked={autoRefresh} />
          <span>Auto-refresh</span>
        </label>
      </div>
      
      <!-- Suggestions List -->
      <div class="suggestions-container">
        {#if loading}
          <div class="text-center py-8 text-surface-500">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p class="mt-2 text-sm">Loading insights...</p>
          </div>
        {:else if filteredSuggestions.length === 0}
          <div class="text-center py-8 text-surface-500">
            <p class="text-sm">No suggestions at this time</p>
            <p class="text-xs mt-1">Ali is analyzing your data...</p>
          </div>
        {:else}
          <div class="space-y-3">
            {#each filteredSuggestions as suggestion (suggestion.id)}
              <div
                class="suggestion-card {getTypeColor(suggestion.type)}"
                transition:slide
              >
                <!-- Suggestion Header -->
                <div class="flex items-start gap-2 mb-2">
                  <span class="text-lg">{getTypeIcon(suggestion.type)}</span>
                  <div class="flex-1">
                    <div class="flex items-center gap-2">
                      <h4 class="font-semibold text-sm">{suggestion.title}</h4>
                      <span class="w-2 h-2 rounded-full {getPriorityColor(suggestion.priority)}"></span>
                    </div>
                    <p class="text-xs text-surface-600 mt-1">{suggestion.description}</p>
                  </div>
                </div>
                
                <!-- Explanation (collapsible) -->
                <details class="mb-2">
                  <summary class="cursor-pointer text-xs text-surface-600 hover:text-surface-900">
                    Why this matters →
                  </summary>
                  <div class="mt-2 p-2 bg-white bg-opacity-50 rounded text-xs">
                    <p class="mb-1">{suggestion.explanation}</p>
                    <p class="font-semibold">Impact: {suggestion.impact}</p>
                  </div>
                </details>
                
                <!-- Actions -->
                <div class="flex gap-2 mt-2">
                  {#each suggestion.actions as action}
                    <button
                      on:click={action.handler}
                      class="px-3 py-1 text-xs rounded transition-colors
                             {action.type === 'primary' ? 'bg-blue-600 text-white hover:bg-blue-700' :
                              action.type === 'danger' ? 'bg-red-600 text-white hover:bg-red-700' :
                              'bg-surface-200 text-surface-600 hover:bg-surface-600'}"
                    >
                      {action.label}
                    </button>
                  {/each}
                </div>
                
                <!-- Timestamp -->
                <div class="text-xs text-surface-500 mt-2">
                  {formatTimeAgo(suggestion.timestamp)}
                </div>
              </div>
            {/each}
          </div>
        {/if}
      </div>
      
      <!-- Footer -->
      <div class="panel-footer">
        <div class="flex items-center justify-between text-xs text-surface-600">
          <span>{activeSuggestions.length} active suggestions</span>
          <button
            on:click={loadSuggestions}
            class="text-blue-600 hover:text-blue-800"
          >
            Refresh
          </button>
        </div>
      </div>
    {:else}
      <!-- Collapsed State -->
      <div class="collapsed-content">
        <div class="flex items-center justify-center py-4">
          <div class="text-center">
            <div class="relative">
              <span class="text-2xl">🤖</span>
              {#if activeSuggestions.length > 0}
                <span class="absolute -top-1 -right-1 w-4 h-4 bg-red-500 text-white rounded-full text-xs flex items-center justify-center">
                  {activeSuggestions.length}
                </span>
              {/if}
            </div>
            <p class="text-xs text-surface-600 mt-1">Ali</p>
          </div>
        </div>
      </div>
    {/if}
  </div>
</div>

<style>
  .ali-coach-panel {
    position: fixed;
    top: 80px;
    bottom: 20px;
    width: 380px;
    z-index: 40;
    transition: width 0.3s ease;
  }
  
  .ali-coach-panel.collapsed {
    width: 60px;
  }
  
  .panel-container {
    height: 100%;
    background: white;
    border-radius: 0.5rem;
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }
  
  .panel-header {
    padding: 1rem;
    border-bottom: 1px solid #e5e7eb;
    background: linear-gradient(to right, #f9fafb, #ffffff);
  }
  
  .panel-filters {
    padding: 0.75rem 1rem;
    border-bottom: 1px solid #e5e7eb;
    display: flex;
    gap: 0.5rem;
    align-items: center;
  }
  
  .suggestions-container {
    flex: 1;
    overflow-y: auto;
    padding: 1rem;
  }
  
  .suggestion-card {
    padding: 0.75rem;
    border-radius: 0.5rem;
    border: 1px solid;
    transition: transform 0.2s;
  }
  
  .suggestion-card:hover {
    transform: translateX(-2px);
  }
  
  .panel-footer {
    padding: 0.75rem 1rem;
    border-top: 1px solid #e5e7eb;
    background: #f9fafb;
  }
  
  .collapsed-content {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  /* Custom scrollbar */
  .suggestions-container::-webkit-scrollbar {
    width: 6px;
  }
  
  .suggestions-container::-webkit-scrollbar-track {
    background: #f1f1f1;
  }
  
  .suggestions-container::-webkit-scrollbar-thumb {
    background: #888;
    border-radius: 3px;
  }
  
  .suggestions-container::-webkit-scrollbar-thumb:hover {
    background: #555;
  }
</style>