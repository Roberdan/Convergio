<script lang="ts">
  import { onMount, createEventDispatcher } from 'svelte';

  export let autoRefresh: boolean = true;
  export let refreshInterval: number = 30000;

  const dispatch = createEventDispatcher();

  interface OllamaModel {
    name: string;
    size: number;
    capabilities: string[];
  }

  interface OllamaStatusData {
    available: boolean;
    version: string | null;
    models: OllamaModel[];
    gpu_available: boolean;
    gpu_name: string | null;
    error: string | null;
  }

  let status: OllamaStatusData | null = null;
  let loading = true;
  let error: string | null = null;
  let intervalId: ReturnType<typeof setInterval> | null = null;

  onMount(() => {
    checkStatus();
    if (autoRefresh) {
      intervalId = setInterval(checkStatus, refreshInterval);
    }
    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  });

  async function checkStatus() {
    loading = true;
    error = null;
    try {
      const response = await fetch('http://localhost:9000/api/v1/settings/ai/ollama/status');
      if (response.ok) {
        status = await response.json();
        dispatch('status', status);
      } else {
        const data = await response.json();
        error = data.detail || 'Failed to check Ollama status';
        status = null;
      }
    } catch (e) {
      error = 'Cannot connect to backend. Is the server running?';
      status = null;
    } finally {
      loading = false;
    }
  }

  function formatSize(bytes: number): string {
    const gb = bytes / (1024 * 1024 * 1024);
    return gb >= 1 ? `${gb.toFixed(1)} GB` : `${(bytes / (1024 * 1024)).toFixed(0)} MB`;
  }

  function getCapabilityBadge(cap: string): { color: string; label: string } {
    const badges: Record<string, { color: string; label: string }> = {
      chat: { color: 'bg-blue-100 text-blue-800', label: 'Chat' },
      function_calling: { color: 'bg-purple-100 text-purple-800', label: 'Functions' },
      code: { color: 'bg-green-100 text-green-800', label: 'Code' },
      vision: { color: 'bg-amber-100 text-amber-800', label: 'Vision' },
      embeddings: { color: 'bg-gray-100 text-gray-800', label: 'Embeddings' }
    };
    return badges[cap] || { color: 'bg-gray-100 text-gray-800', label: cap };
  }
</script>

<div class="border rounded-lg overflow-hidden">
  <div class="px-4 py-3 bg-surface-50 border-b border-surface-200 flex items-center justify-between">
    <div class="flex items-center space-x-2">
      <span class="text-lg">🦙</span>
      <h4 class="text-sm font-medium text-surface-900">Ollama Status</h4>
    </div>
    <button
      on:click={checkStatus}
      disabled={loading}
      class="p-1.5 text-surface-500 hover:text-surface-700 hover:bg-surface-100 rounded transition-colors disabled:opacity-50"
      aria-label="Refresh Ollama status"
    >
      <svg class="h-4 w-4 {loading ? 'animate-spin' : ''}" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
      </svg>
    </button>
  </div>

  <div class="p-4">
    {#if loading && !status}
      <div class="flex items-center justify-center py-6">
        <svg class="h-6 w-6 text-surface-400 animate-spin" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <span class="ml-2 text-sm text-surface-500">Checking Ollama...</span>
      </div>
    {:else if error}
      <div class="p-3 bg-red-50 border border-red-200 rounded">
        <div class="flex items-start space-x-2">
          <svg class="h-5 w-5 text-red-500 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
          </svg>
          <div>
            <p class="text-sm font-medium text-red-800">Ollama Not Available</p>
            <p class="text-xs text-red-700 mt-1">{error}</p>
            <a
              href="https://ollama.ai"
              target="_blank"
              rel="noopener noreferrer"
              class="inline-flex items-center text-xs text-red-600 hover:text-red-800 mt-2"
            >
              Install Ollama →
            </a>
          </div>
        </div>
      </div>
    {:else if status}
      <div class="space-y-4">
        <!-- Connection Status -->
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-2">
            <div class="h-2.5 w-2.5 rounded-full {status.available ? 'bg-green-500' : 'bg-red-500'}"></div>
            <span class="text-sm font-medium {status.available ? 'text-green-700' : 'text-red-700'}">
              {status.available ? 'Connected' : 'Disconnected'}
            </span>
          </div>
          {#if status.version}
            <span class="text-xs text-surface-500">v{status.version}</span>
          {/if}
        </div>

        <!-- GPU Status -->
        {#if status.available}
          <div class="flex items-center space-x-2 text-sm">
            {#if status.gpu_available}
              <svg class="h-4 w-4 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
              </svg>
              <span class="text-green-700">GPU: {status.gpu_name || 'Available'}</span>
            {:else}
              <svg class="h-4 w-4 text-amber-500" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
              </svg>
              <span class="text-amber-700">CPU Mode (slower)</span>
            {/if}
          </div>
        {/if}

        <!-- Models -->
        {#if status.available && status.models.length > 0}
          <div>
            <h5 class="text-xs font-medium text-surface-700 mb-2">Available Models ({status.models.length})</h5>
            <div class="space-y-2 max-h-48 overflow-y-auto">
              {#each status.models as model}
                <div class="p-2 bg-surface-50 rounded border border-surface-200">
                  <div class="flex items-center justify-between">
                    <span class="text-sm font-medium text-surface-900">{model.name}</span>
                    <span class="text-xs text-surface-500">{formatSize(model.size)}</span>
                  </div>
                  {#if model.capabilities.length > 0}
                    <div class="flex flex-wrap gap-1 mt-1">
                      {#each model.capabilities as cap}
                        {@const badge = getCapabilityBadge(cap)}
                        <span class="px-1.5 py-0.5 text-xs rounded {badge.color}">{badge.label}</span>
                      {/each}
                    </div>
                  {/if}
                </div>
              {/each}
            </div>
          </div>
        {:else if status.available}
          <div class="p-3 bg-amber-50 border border-amber-200 rounded">
            <p class="text-sm text-amber-800">No models installed. Pull a model to get started:</p>
            <code class="block mt-2 text-xs bg-amber-100 p-2 rounded">ollama pull llama3.2:latest</code>
          </div>
        {/if}
      </div>
    {/if}
  </div>
</div>
