<script lang="ts">
  import { createEventDispatcher } from 'svelte';

  export let config = {
    endpoint: '',
    api_key: '',
    deployment_name: '',
    api_version: '2024-02-15-preview'
  };
  export let disabled: boolean = false;

  const dispatch = createEventDispatcher();

  let testing = false;
  let testResult: { success: boolean; message: string } | null = null;
  let showApiKey = false;

  function updateConfig(field: keyof typeof config, value: string) {
    if (disabled) return;
    config = { ...config, [field]: value };
    dispatch('change', { config });
  }

  async function testConnection() {
    testing = true;
    testResult = null;

    try {
      const response = await fetch('http://localhost:9000/api/v1/settings/ai/azure/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });

      const data = await response.json();
      testResult = {
        success: response.ok,
        message: response.ok ? 'Connection successful!' : (data.detail || 'Connection failed')
      };
    } catch (e) {
      testResult = {
        success: false,
        message: 'Failed to connect to backend'
      };
    } finally {
      testing = false;
    }
  }

  $: isConfigured = config.endpoint && config.api_key && config.deployment_name;
</script>

<div class="border rounded-lg overflow-hidden">
  <div class="px-4 py-3 bg-blue-50 border-b border-blue-200">
    <div class="flex items-center space-x-2">
      <svg class="h-5 w-5 text-blue-600" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/>
      </svg>
      <h4 class="text-sm font-medium text-blue-900">Azure OpenAI Configuration</h4>
    </div>
    <p class="text-xs text-blue-700 mt-1">Enterprise-grade AI with Azure compliance and SLAs</p>
  </div>

  <div class="p-4 space-y-4">
    <!-- Endpoint -->
    <div class="space-y-1">
      <label for="azure-endpoint" class="block text-xs font-medium text-surface-700">
        Azure Endpoint <span class="text-red-500">*</span>
      </label>
      <input
        id="azure-endpoint"
        type="url"
        value={config.endpoint}
        on:input={(e) => updateConfig('endpoint', e.currentTarget.value)}
        placeholder="https://your-resource.openai.azure.com"
        disabled={disabled}
        class="w-full px-3 py-2 text-sm border border-surface-300 rounded focus:ring-1 focus:ring-gray-900 focus:border-gray-900 disabled:opacity-50 disabled:bg-surface-100"
      />
      <p class="text-xs text-surface-500">Your Azure OpenAI resource endpoint URL</p>
    </div>

    <!-- API Key -->
    <div class="space-y-1">
      <label for="azure-key" class="block text-xs font-medium text-surface-700">
        API Key <span class="text-red-500">*</span>
      </label>
      <div class="relative">
        <input
          id="azure-key"
          type={showApiKey ? 'text' : 'password'}
          value={config.api_key}
          on:input={(e) => updateConfig('api_key', e.currentTarget.value)}
          placeholder="Enter your Azure OpenAI API key"
          disabled={disabled}
          class="w-full px-3 py-2 pr-10 text-sm border border-surface-300 rounded focus:ring-1 focus:ring-gray-900 focus:border-gray-900 disabled:opacity-50 disabled:bg-surface-100"
        />
        <button
          type="button"
          on:click={() => showApiKey = !showApiKey}
          class="absolute right-2 top-1/2 -translate-y-1/2 text-surface-400 hover:text-surface-600"
          aria-label={showApiKey ? 'Hide API key' : 'Show API key'}
        >
          {#if showApiKey}
            <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"/>
            </svg>
          {:else}
            <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
            </svg>
          {/if}
        </button>
      </div>
    </div>

    <!-- Deployment Name -->
    <div class="space-y-1">
      <label for="azure-deployment" class="block text-xs font-medium text-surface-700">
        Deployment Name <span class="text-red-500">*</span>
      </label>
      <input
        id="azure-deployment"
        type="text"
        value={config.deployment_name}
        on:input={(e) => updateConfig('deployment_name', e.currentTarget.value)}
        placeholder="gpt-4o-deployment"
        disabled={disabled}
        class="w-full px-3 py-2 text-sm border border-surface-300 rounded focus:ring-1 focus:ring-gray-900 focus:border-gray-900 disabled:opacity-50 disabled:bg-surface-100"
      />
      <p class="text-xs text-surface-500">The name of your model deployment in Azure</p>
    </div>

    <!-- API Version -->
    <div class="space-y-1">
      <label for="azure-version" class="block text-xs font-medium text-surface-700">
        API Version
      </label>
      <select
        id="azure-version"
        value={config.api_version}
        on:change={(e) => updateConfig('api_version', e.currentTarget.value)}
        disabled={disabled}
        class="w-full px-3 py-2 text-sm border border-surface-300 rounded focus:ring-1 focus:ring-gray-900 focus:border-gray-900 disabled:opacity-50 disabled:bg-surface-100"
      >
        <option value="2024-02-15-preview">2024-02-15-preview (Latest)</option>
        <option value="2024-02-01">2024-02-01</option>
        <option value="2023-12-01-preview">2023-12-01-preview</option>
        <option value="2023-05-15">2023-05-15 (Stable)</option>
      </select>
    </div>

    <!-- Test Connection -->
    <div class="pt-3 border-t border-surface-200">
      <button
        on:click={testConnection}
        disabled={disabled || testing || !isConfigured}
        class="w-full px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:bg-surface-300 rounded transition-colors disabled:cursor-not-allowed"
      >
        {#if testing}
          Testing Connection...
        {:else}
          Test Connection
        {/if}
      </button>

      {#if testResult}
        <div class="mt-3 p-3 rounded {testResult.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}">
          <div class="flex items-center space-x-2">
            {#if testResult.success}
              <svg class="h-4 w-4 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
              </svg>
            {:else}
              <svg class="h-4 w-4 text-red-600" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
              </svg>
            {/if}
            <span class="text-sm {testResult.success ? 'text-green-800' : 'text-red-800'}">
              {testResult.message}
            </span>
          </div>
        </div>
      {/if}
    </div>
  </div>

  <!-- Help Section -->
  <div class="px-4 py-3 bg-surface-50 border-t border-surface-200">
    <details class="text-xs">
      <summary class="cursor-pointer text-surface-600 hover:text-surface-900">Setup instructions</summary>
      <ol class="mt-2 ml-4 list-decimal space-y-1 text-surface-600">
        <li>Go to <a href="https://portal.azure.com" target="_blank" rel="noopener" class="text-blue-600 hover:underline">Azure Portal</a></li>
        <li>Create or select an Azure OpenAI resource</li>
        <li>Deploy a model (e.g., gpt-4o) in Model deployments</li>
        <li>Copy the endpoint URL and API key from Keys and Endpoint</li>
        <li>Enter the deployment name you chose</li>
      </ol>
    </details>
  </div>
</div>
