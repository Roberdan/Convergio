<script lang="ts">
  import { onMount, onDestroy } from 'svelte';

  // Get app version from environment or fallback
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const APP_VERSION: string = ((globalThis as any).__APP_VERSION__ || (globalThis as any).__VERSION__ || 'V1.0.129') as string;
  
  interface ApiStatus {
    openai: { connected: boolean; model?: string; error?: string };
    anthropic: { connected: boolean; model?: string; error?: string };
    perplexity: { connected: boolean; model?: string; error?: string };
    backend: { connected: boolean; version?: string };
  }
  
  let isOpen = false;
  let apiStatus: ApiStatus = {
    openai: { connected: false },
    anthropic: { connected: false },
    perplexity: { connected: false },
    backend: { connected: false }
  };
  
  let overallStatus: 'online' | 'partial' | 'offline' = 'offline';
  let intervalId: NodeJS.Timeout;
  
  onMount(() => {
    checkApiStatus();
    // Check status every 30 seconds
    intervalId = setInterval(checkApiStatus, 30000);
  });
  
  onDestroy(() => {
    if (intervalId) {
      clearInterval(intervalId);
    }
  });
  
  async function checkApiStatus() {
    try {
      // Check system API status (from .env configuration)
      const systemResponse = await fetch('http://localhost:9000/api/v1/system/api-status', {
        signal: AbortSignal.timeout(3000)
      });
      
      if (systemResponse.ok) {
        const systemStatus = await systemResponse.json();
        
        // Update backend status
        apiStatus.backend = { 
          connected: systemStatus.backend?.connected || false, 
          version: systemStatus.backend?.version || 'Unknown'
        };
        
        // Update OpenAI status from system config
        apiStatus.openai = {
          connected: systemStatus.openai?.connected || false,
          model: systemStatus.openai?.model || undefined,
          error: systemStatus.openai?.connected ? undefined : 'Not configured in .env'
        };
        
        // Update Anthropic status from system config
        apiStatus.anthropic = {
          connected: systemStatus.anthropic?.connected || false,
          model: systemStatus.anthropic?.model || undefined,
          error: systemStatus.anthropic?.connected ? undefined : 'Not configured in .env'
        };
        
        // Update Perplexity status from system config
        apiStatus.perplexity = {
          connected: systemStatus.perplexity?.connected || false,
          model: systemStatus.perplexity?.model || undefined,
          error: systemStatus.perplexity?.connected ? undefined : 'Not configured in .env'
        };
      } else {
        apiStatus.backend = { connected: false };
      }
      
      // Also check user-provided keys (optional override)
      try {
        const keysResponse = await fetch('http://localhost:9000/api/v1/user-keys/status', {
          signal: AbortSignal.timeout(3000)
        });
        
        if (keysResponse.ok) {
          const keysStatus = await keysResponse.json();
          
          // Override with user keys if provided
          if (keysStatus.openai?.is_configured) {
            apiStatus.openai.connected = true;
            apiStatus.openai.model = 'GPT-4 (User)';
            apiStatus.openai.error = keysStatus.openai?.is_valid === false ? 'Invalid user API key' : undefined;
          }
          
          if (keysStatus.anthropic?.is_configured) {
            apiStatus.anthropic.connected = true;
            apiStatus.anthropic.model = 'Claude 3 (User)';
            apiStatus.anthropic.error = keysStatus.anthropic?.is_valid === false ? 'Invalid user API key' : undefined;
          }
          
          if (keysStatus.perplexity?.is_configured) {
            apiStatus.perplexity.connected = true;
            apiStatus.perplexity.model = 'Sonar (User)';
            apiStatus.perplexity.error = keysStatus.perplexity?.is_valid === false ? 'Invalid user API key' : undefined;
          }
        }
      } catch (userKeysError) {
        // User keys are optional, don't fail if not available
      }

    } catch {
      // Silent failure
      apiStatus.backend = { connected: false };
    }
    
    // Calculate overall status
    updateOverallStatus();
  }
  
  function updateOverallStatus() {
    const connectedCount = [
      apiStatus.backend.connected,
      apiStatus.openai.connected,
      apiStatus.anthropic.connected,
      apiStatus.perplexity.connected
    ].filter(Boolean).length;
    
    if (!apiStatus.backend.connected) {
      overallStatus = 'offline';
    } else if (connectedCount === 4) {
      overallStatus = 'online';
    } else if (connectedCount > 1) {
      overallStatus = 'partial';
    } else {
      overallStatus = 'offline';
    }
  }
  
  function getStatusColor(status: 'online' | 'partial' | 'offline') {
    switch (status) {
      case 'online': return 'text-green-700';
      case 'partial': return 'text-yellow-700';
      case 'offline': return 'text-red-700';
    }
  }
  
  function getStatusBgColor(status: 'online' | 'partial' | 'offline') {
    switch (status) {
      case 'online': return 'bg-green-500';
      case 'partial': return 'bg-yellow-500';
      case 'offline': return 'bg-red-500';
    }
  }
  
  function getServiceIcon(service: string) {
    switch (service) {
      case 'openai': return '🤖';
      case 'anthropic': return '🧠';
      case 'perplexity': return '🔍';
      case 'backend': return '⚙️';
      default: return '📡';
    }
  }
</script>

<div class="relative">
  <!-- Status Button -->
  <button
    on:click={() => isOpen = !isOpen}
    class="flex items-start space-x-2 px-4 py-2 bg-white rounded-lg hover:bg-blue-50 transition-all duration-200 shadow-sm {getStatusColor(overallStatus)}"
    aria-label="API connection status"
    aria-expanded={isOpen}
  >
    <div class="h-2 w-2 {getStatusBgColor(overallStatus)} rounded-full animate-pulse"></div>
    <span class="hidden sm:inline capitalize font-bold text-sm">{overallStatus}</span>
    <svg
      class="w-4 h-4 text-surface-600 transform transition-transform {isOpen ? 'rotate-180' : ''}"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
    >
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
    </svg>
  </button>
  
  <!-- Dropdown Panel -->
  {#if isOpen}
    <div class="absolute right-0 top-full mt-2 w-80 bg-white border-2 border-surface-300 rounded-xl shadow-2xl z-[10000] overflow-hidden">
      <!-- Header -->
      <div class="bg-blue-600 text-white px-6 py-4">
        <div class="flex items-center justify-between">
          <div>
            <h3 class="text-lg font-bold">API Connection Status</h3>
            <p class="text-sm text-blue-100 mt-1">Real-time service availability</p>
          </div>
        </div>
      </div>
      
      <!-- Version Info -->
      <div class="bg-surface-50 border-b border-surface-200 px-6 py-3">
        <div class="flex items-center justify-between">
          <span class="text-sm text-surface-600">Platform Version</span>
          <span class="text-sm font-bold text-surface-900">{APP_VERSION}</span>
        </div>
      </div>
      
      <div class="p-6 space-y-4">
        <!-- Backend Status -->
        <div class="flex items-center justify-between p-4 bg-surface-100 rounded-lg">
          <div class="flex items-center space-x-3">
            <span class="text-xl">{getServiceIcon('backend')}</span>
            <div>
              <p class="font-bold text-surface-900">Backend Server</p>
              <p class="text-sm text-surface-600">
                {#if apiStatus.backend.connected}
                  v{apiStatus.backend.version || 'Unknown'}
                {:else}
                  Not connected
                {/if}
              </p>
            </div>
          </div>
          <div class="flex items-center space-x-2">
            <div class="h-3 w-3 rounded-full {apiStatus.backend.connected ? 'bg-green-500' : 'bg-red-500'}"></div>
            <span class="text-sm font-bold {apiStatus.backend.connected ? 'text-green-700' : 'text-red-700'}">
              {apiStatus.backend.connected ? 'Online' : 'Offline'}
            </span>
          </div>
        </div>
        
        <!-- OpenAI Status -->
        <div class="flex items-center justify-between p-4 bg-surface-100 rounded-lg">
          <div class="flex items-center space-x-3">
            <span class="text-xl">{getServiceIcon('openai')}</span>
            <div>
              <p class="font-bold text-surface-900">OpenAI</p>
              <p class="text-sm text-surface-600">
                {#if apiStatus.openai.connected}
                  {apiStatus.openai.model || 'Connected'}
                {:else if apiStatus.openai.error}
                  {apiStatus.openai.error}
                {:else}
                  Check .env configuration
                {/if}
              </p>
            </div>
          </div>
          <div class="flex items-center space-x-2">
            <div class="h-3 w-3 rounded-full {apiStatus.openai.connected ? 'bg-green-500' : 'bg-surface-500'}"></div>
            <span class="text-sm font-bold {apiStatus.openai.connected ? 'text-green-700' : 'text-surface-600'}">
              {apiStatus.openai.connected ? 'Active' : 'Inactive'}
            </span>
          </div>
        </div>
        
        <!-- Anthropic Status -->
        <div class="flex items-center justify-between p-4 bg-surface-100 rounded-lg">
          <div class="flex items-center space-x-3">
            <span class="text-xl">{getServiceIcon('anthropic')}</span>
            <div>
              <p class="font-bold text-surface-900">Anthropic</p>
              <p class="text-sm text-surface-600">
                {#if apiStatus.anthropic.connected}
                  {apiStatus.anthropic.model || 'Connected'}
                {:else if apiStatus.anthropic.error}
                  {apiStatus.anthropic.error}
                {:else}
                  Check .env configuration
                {/if}
              </p>
            </div>
          </div>
          <div class="flex items-center space-x-2">
            <div class="h-3 w-3 rounded-full {apiStatus.anthropic.connected ? 'bg-green-500' : 'bg-surface-500'}"></div>
            <span class="text-sm font-bold {apiStatus.anthropic.connected ? 'text-green-700' : 'text-surface-600'}">
              {apiStatus.anthropic.connected ? 'Active' : 'Inactive'}
            </span>
          </div>
        </div>
        
        <!-- Perplexity Status -->
        <div class="flex items-center justify-between p-4 bg-surface-100 rounded-lg">
          <div class="flex items-center space-x-3">
            <span class="text-xl">{getServiceIcon('perplexity')}</span>
            <div>
              <p class="font-bold text-surface-900">Perplexity</p>
              <p class="text-sm text-surface-600">
                {#if apiStatus.perplexity.connected}
                  {apiStatus.perplexity.model || 'Web Search Ready'}
                {:else if apiStatus.perplexity.error}
                  {apiStatus.perplexity.error}
                {:else}
                  Check .env configuration
                {/if}
              </p>
            </div>
          </div>
          <div class="flex items-center space-x-2">
            <div class="h-3 w-3 rounded-full {apiStatus.perplexity.connected ? 'bg-green-500' : 'bg-yellow-500'}"></div>
            <span class="text-sm font-bold {apiStatus.perplexity.connected ? 'text-green-700' : 'text-yellow-700'}">
              {apiStatus.perplexity.connected ? 'Active' : 'Optional'}
            </span>
          </div>
        </div>
      </div>
      
      <!-- Footer -->
      <div class="bg-surface-100 px-6 py-4 flex items-center justify-between text-sm">
        <p class="text-surface-600 font-medium">
          Last checked: {new Date().toLocaleTimeString()}
        </p>
        <button
          on:click={checkApiStatus}
          class="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded transition-colors"
        >
          Refresh
        </button>
      </div>
    </div>
  {/if}
</div>

<!-- Click outside to close -->
{#if isOpen}
  <div 
    class="fixed inset-0 z-[9999]" 
    role="button"
    tabindex="-1"
    aria-label="Close API status"
    on:click={() => isOpen = false}
    on:keydown={(e) => e.key === 'Escape' && (isOpen = false)}
  ></div>
{/if}

<style>
  @keyframes pulse {
    0%, 100% {
      opacity: 1;
    }
    50% {
      opacity: 0.5;
    }
  }
  
  .animate-pulse {
    animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
  }
</style>