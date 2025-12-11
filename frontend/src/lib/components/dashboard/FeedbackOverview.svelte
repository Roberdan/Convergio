<script lang="ts">
  import { onMount } from 'svelte';
  import { feedbackService, type Feedback, type FeedbackStats } from '$lib/services/feedbackService';

  let feedback: Feedback[] = [];
  let stats: FeedbackStats | null = null;
  let loading = true;
  let error: string | null = null;

  function getTypeColor(type: string): string {
    switch (type) {
      case 'bug': return 'text-red-600 bg-red-50';
      case 'feature': return 'text-green-600 bg-green-50';
      case 'improvement': return 'text-blue-600 bg-blue-50';
      case 'general': return 'text-surface-600 bg-surface-50';
      default: return 'text-surface-600 bg-surface-50';
    }
  }

  function getStatusColor(status: string): string {
    switch (status) {
      case 'resolved': return 'text-green-600 bg-green-50';
      case 'in-progress': return 'text-blue-600 bg-blue-50';
      case 'new': return 'text-yellow-600 bg-yellow-50';
      case 'closed': return 'text-surface-600 bg-surface-50';
      default: return 'text-surface-600 bg-surface-50';
    }
  }

  function getPriorityColor(priority: string): string {
    switch (priority) {
      case 'critical': return 'text-red-600 bg-red-50';
      case 'high': return 'text-orange-600 bg-orange-50';
      case 'medium': return 'text-yellow-600 bg-yellow-50';
      case 'low': return 'text-surface-600 bg-surface-50';
      default: return 'text-surface-600 bg-surface-50';
    }
  }

  function formatDate(dateString: string): string {
    return new Date(dateString).toLocaleDateString();
  }

  async function loadFeedbackData() {
    try {
      loading = true;
      error = null;
      
      const [feedbackData, statsData] = await Promise.all([
        feedbackService.getFeedback(20),
        feedbackService.getFeedbackStats()
      ]);
      
      feedback = feedbackData || [];
      stats = statsData;
    } catch (err) {
      console.error('Failed to load feedback data:', err);
      error = 'Failed to load feedback data';
    } finally {
      loading = false;
    }
  }

  onMount(loadFeedbackData);
</script>

<div class="bg-white border border-surface-200 rounded">
  <div class="px-4 py-3 border-b border-surface-200">
    <div class="flex items-center justify-between">
      <h3 class="text-sm font-medium text-surface-900">Feedback & Support</h3>
      <button 
        on:click={loadFeedbackData}
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
          on:click={loadFeedbackData}
          class="mt-2 text-sm text-blue-600 hover:text-blue-800"
        >
          Try again
        </button>
      </div>
    {:else}
      <!-- Feedback Stats -->
      {#if stats}
        <div class="grid grid-cols-4 gap-4 mb-6">
          <div class="bg-blue-50 p-4 rounded">
            <p class="text-2xl font-bold text-blue-600">{stats.total_feedback}</p>
            <p class="text-sm text-blue-600">Total Feedback</p>
          </div>
          <div class="bg-green-50 p-4 rounded">
            <p class="text-2xl font-bold text-green-600">{stats.by_status?.resolved || 0}</p>
            <p class="text-sm text-green-600">Resolved</p>
          </div>
          <div class="bg-yellow-50 p-4 rounded">
            <p class="text-2xl font-bold text-yellow-600">{stats.by_status?.new || 0}</p>
            <p class="text-sm text-yellow-600">New</p>
          </div>
          <div class="bg-purple-50 p-4 rounded">
            <p class="text-2xl font-bold text-purple-600">{stats.satisfaction_score?.toFixed(1) || 'N/A'}%</p>
            <p class="text-sm text-purple-600">Satisfaction</p>
          </div>
        </div>

        <!-- Feedback by Type -->
        <div class="grid grid-cols-2 gap-6 mb-6">
          <div>
            <h4 class="text-xs font-medium text-surface-600 mb-3">By Type</h4>
            <div class="space-y-2">
              {#each Object.entries(stats.by_type || {}) as [type, count]}
                <div class="flex justify-between items-center">
                  <span class="text-xs px-2 py-1 rounded-full {getTypeColor(type)}">{type}</span>
                  <span class="text-sm font-medium">{count}</span>
                </div>
              {/each}
            </div>
          </div>
          
          <div>
            <h4 class="text-xs font-medium text-surface-600 mb-3">By Priority</h4>
            <div class="space-y-2">
              {#each Object.entries(stats.by_priority || {}) as [priority, count]}
                <div class="flex justify-between items-center">
                  <span class="text-xs px-2 py-1 rounded-full {getPriorityColor(priority)}">{priority}</span>
                  <span class="text-sm font-medium">{count}</span>
                </div>
              {/each}
            </div>
          </div>
        </div>
      {/if}

      <!-- Recent Feedback -->
      {#if feedback.length > 0}
        <div>
          <h4 class="text-xs font-medium text-surface-600 mb-3">Recent Feedback</h4>
          <div class="space-y-3">
            {#each feedback.slice(0, 8) as item}
              <div class="flex items-center justify-between p-3 border border-surface-200 rounded hover:bg-surface-50">
                <div class="flex items-center space-x-3">
                  <div class="w-8 h-8 bg-gradient-to-br from-indigo-400 to-purple-500 rounded flex items-center justify-center">
                    <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                    </svg>
                  </div>
                  <div>
                    <p class="text-sm font-medium text-surface-900">{item.title}</p>
                    <p class="text-xs text-surface-500 truncate max-w-sm">{item.description}</p>
                    <p class="text-xs text-surface-600">{formatDate(item.created_at)}</p>
                  </div>
                </div>
                <div class="flex items-center space-x-2">
                  <span class="text-xs px-2 py-1 rounded-full {getTypeColor(item.type)}">
                    {item.type}
                  </span>
                  <span class="text-xs px-2 py-1 rounded-full {getPriorityColor(item.priority)}">
                    {item.priority}
                  </span>
                  <span class="text-xs px-2 py-1 rounded-full {getStatusColor(item.status)}">
                    {item.status}
                  </span>
                </div>
              </div>
            {/each}
          </div>
        </div>
      {:else}
        <div class="text-center text-surface-500">
          <p class="text-xs">No feedback available</p>
        </div>
      {/if}
    {/if}
  </div>
</div>