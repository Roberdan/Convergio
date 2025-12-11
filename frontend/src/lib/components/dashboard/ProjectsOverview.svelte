<script lang="ts">
  import { onMount } from 'svelte';
  import { projectsService, type ProjectOverview, type EngagementDetail } from '$lib/services/projectsService';

  let projectOverview: ProjectOverview | null = null;
  let selectedEngagement: EngagementDetail | null = null;
  let loading = true;
  let error: string | null = null;
  let loadingDetails = false;

  function getStatusColor(status: string): string {
    switch (status) {
      case 'completed': return 'text-green-600 bg-green-50';
      case 'in-progress': return 'text-blue-600 bg-blue-50';
      case 'review': return 'text-yellow-600 bg-yellow-50';
      case 'planning': return 'text-surface-600 bg-surface-50';
      default: return 'text-surface-600 bg-surface-50';
    }
  }

  // removed unused getPriorityColor

  async function loadData() {
    try {
      loading = true;
      error = null;
      
      projectOverview = await projectsService.getProjectOverview();
    } catch (err) {
      console.error('Failed to load projects data:', err);
      error = 'Failed to load projects data';
    } finally {
      loading = false;
    }
  }

  async function showEngagementDetails(engagementId: number) {
    try {
      loadingDetails = true;
      selectedEngagement = await projectsService.getEngagementDetails(engagementId);
    } catch (err) {
      console.error('Failed to load engagement details:', err);
      error = 'Failed to load engagement details';
    } finally {
      loadingDetails = false;
    }
  }

  function closeDetails() {
    selectedEngagement = null;
  }

  onMount(loadData);
</script>

<div class="bg-white border border-surface-200 rounded">
  <div class="px-4 py-3 border-b border-surface-200">
    <div class="flex items-center justify-between">
      <h3 class="text-sm font-medium text-surface-900">Projects & Activities</h3>
      <button 
        on:click={loadData}
        class="text-xs text-surface-500 hover:text-surface-600 flex items-center space-x-1"
        aria-label="Refresh projects overview"
      >
        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        <span>Refresh</span>
      </button>
    </div>
  </div>

  <div class="p-0">
    {#if loading}
      <div class="p-4">
        <div class="animate-pulse space-y-4">
          {#each Array.from({ length: 4 }, (_, i) => i) as i (i)}
            <div class="flex items-center justify-between p-4 border border-surface-200 rounded" data-index={i}>
              <div class="flex items-center space-x-3">
                <div class="w-3 h-3 bg-surface-200 rounded-full"></div>
                <div>
                  <div class="w-32 h-4 bg-surface-200 rounded mb-1"></div>
                  <div class="w-48 h-3 bg-surface-200 rounded"></div>
                </div>
              </div>
              <div class="w-16 h-4 bg-surface-200 rounded"></div>
            </div>
          {/each}
        </div>
      </div>
    {:else if error}
      <div class="p-6 text-center text-red-600">
        <p>{error}</p>
        <button 
          on:click={loadData}
          class="mt-2 text-sm text-blue-600 hover:text-blue-800"
        >
          Try again
        </button>
      </div>
    {:else}
      <!-- Summary Stats -->
      {#if projectOverview}
        <div class="p-4 border-b border-surface-200">
          <h4 class="text-xs font-medium text-surface-600 mb-3">Project Summary</h4>
          <div class="grid grid-cols-2 gap-4 mb-4">
            <div class="bg-blue-50 p-3 rounded">
              <p class="text-xl font-bold text-blue-600">{projectOverview.total_clients}</p>
              <p class="text-xs text-blue-600">Clients</p>
            </div>
            <div class="bg-green-50 p-3 rounded">
              <p class="text-xl font-bold text-green-600">{projectOverview.total_engagements}</p>
              <p class="text-xs text-green-600">Projects</p>
            </div>
            <div class="bg-orange-50 p-3 rounded">
              <p class="text-xl font-bold text-orange-600">{projectOverview.active_engagements}</p>
              <p class="text-xs text-orange-600">Active</p>
            </div>
            <div class="bg-purple-50 p-3 rounded">
              <p class="text-xl font-bold text-purple-600">{projectOverview.completed_engagements}</p>
              <p class="text-xs text-purple-600">Completed</p>
            </div>
          </div>
        </div>

        <!-- Recent Projects -->
        {#if projectOverview.recent_engagements.length > 0}
          <div class="p-4 border-b border-surface-200">
            <h4 class="text-xs font-medium text-surface-600 mb-3">Recent Projects</h4>
            <div class="space-y-3">
              {#each projectOverview.recent_engagements.slice(0, 5) as engagement}
                <button 
                  class="w-full flex items-center justify-between p-3 bg-surface-50 rounded hover:bg-surface-100 transition-colors"
                  on:click={() => showEngagementDetails(engagement.id)}
                >
                  <div class="flex items-center space-x-3">
                    <div class="w-2 h-2 rounded-full {getStatusColor(engagement.status).split(' ')[0].replace('text-', 'bg-')}"></div>
                    <div class="text-left">
                      <p class="text-sm font-medium text-surface-900">{engagement.title}</p>
                      <p class="text-xs text-surface-500">{engagement.description || 'No description'}</p>
                    </div>
                  </div>
                  <div class="text-right">
                    <span class="text-xs px-2 py-1 rounded-full {getStatusColor(engagement.status)}">
                      {engagement.status}
                    </span>
                    <p class="text-xs text-surface-500 mt-1">{engagement.progress.toFixed(0)}% complete</p>
                  </div>
                </button>
              {/each}
            </div>
          </div>
        {/if}

        <!-- Clients Section -->
        {#if projectOverview.clients.length > 0}
          <div class="p-4">
            <h4 class="text-xs font-medium text-surface-600 mb-3">Recent Clients</h4>
            <div class="space-y-2">
              {#each projectOverview.clients.slice(0, 8) as client}
                <div class="flex items-center justify-between p-2 hover:bg-surface-50 rounded">
                  <div class="flex items-center space-x-3">
                    <div class="w-6 h-6 bg-gradient-to-br from-blue-400 to-purple-500 rounded-full flex items-center justify-center">
                      <span class="text-white text-xs font-semibold">
                        {client.name.charAt(0).toUpperCase()}
                      </span>
                    </div>
                    <div>
                      <p class="text-xs font-medium text-surface-900">{client.name}</p>
                      <p class="text-xs text-surface-500">{client.email}</p>
                    </div>
                  </div>
                  <div class="text-right">
                    <p class="text-xs text-surface-500">
                      {client.created_at ? new Date(client.created_at).toLocaleDateString() : 'N/A'}
                    </p>
                  </div>
                </div>
              {/each}
            </div>
          </div>
        {/if}
      {:else}
        <div class="p-4 text-center text-surface-500">
          <p class="text-xs">No project data available</p>
        </div>
      {/if}
    {/if}
  </div>
</div>

<!-- Engagement Details Modal -->
{#if selectedEngagement}
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
    <div class="bg-white rounded-lg max-w-2xl w-full max-h-screen overflow-y-auto">
      <div class="p-6">
        <!-- Header -->
        <div class="flex items-center justify-between mb-4">
          <div>
            <h2 class="text-lg font-semibold text-surface-900">{selectedEngagement.title}</h2>
            <span class="text-xs px-2 py-1 rounded-full {getStatusColor(selectedEngagement.status)}">
              {selectedEngagement.status}
            </span>
          </div>
          <button 
            on:click={closeDetails}
            class="text-surface-600 hover:text-surface-300"
            aria-label="Close details"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Description -->
        {#if selectedEngagement.description}
          <div class="mb-6">
            <h3 class="text-sm font-medium text-surface-600 mb-2">Description</h3>
            <p class="text-sm text-surface-600">{selectedEngagement.description}</p>
          </div>
        {/if}

        <!-- Progress -->
        <div class="mb-6">
          <div class="flex items-center justify-between mb-2">
            <h3 class="text-sm font-medium text-surface-600">Progress</h3>
            <span class="text-sm text-surface-600">{selectedEngagement.progress.toFixed(0)}%</span>
          </div>
          <div class="w-full bg-surface-200 rounded-full h-2">
            <div 
              class="bg-blue-600 h-2 rounded-full transition-all duration-300" 
              style="width: {selectedEngagement.progress}%"
            ></div>
          </div>
        </div>

        <!-- Activities -->
        {#if loadingDetails}
          <div class="text-center py-4">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto"></div>
            <p class="text-sm text-surface-500 mt-2">Loading activities...</p>
          </div>
        {:else if selectedEngagement.activities.length > 0}
          <div>
            <h3 class="text-sm font-medium text-surface-600 mb-3">Activities ({selectedEngagement.activities.length})</h3>
            <div class="space-y-3">
              {#each selectedEngagement.activities as activity}
                <div class="border border-surface-200 rounded p-3">
                  <div class="flex items-center justify-between mb-2">
                    <h4 class="text-sm font-medium text-surface-900">{activity.title}</h4>
                    <span class="text-xs px-2 py-1 rounded-full {getStatusColor(activity.status)}">
                      {activity.status}
                    </span>
                  </div>
                  {#if activity.description}
                    <p class="text-xs text-surface-600 mb-2">{activity.description.substring(0, 100)}...</p>
                  {/if}
                  <div class="flex items-center justify-between">
                    <div class="w-full bg-surface-200 rounded-full h-1 mr-2">
                      <div 
                        class="bg-green-600 h-1 rounded-full" 
                        style="width: {activity.progress}%"
                      ></div>
                    </div>
                    <span class="text-xs text-surface-500 whitespace-nowrap">{activity.progress.toFixed(0)}%</span>
                  </div>
                </div>
              {/each}
            </div>
          </div>
        {:else}
          <div class="text-center py-4">
            <p class="text-sm text-surface-500">No activities found for this project</p>
          </div>
        {/if}

        <!-- Footer -->
        <div class="mt-6 pt-4 border-t border-surface-200">
          <div class="flex justify-between text-xs text-surface-500">
            <span>Created: {selectedEngagement.created_at ? new Date(selectedEngagement.created_at).toLocaleDateString() : 'N/A'}</span>
            <span>Updated: {selectedEngagement.updated_at ? new Date(selectedEngagement.updated_at).toLocaleDateString() : 'N/A'}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
{/if}