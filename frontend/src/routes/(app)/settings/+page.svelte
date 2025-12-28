<script lang="ts">
  import { onMount } from 'svelte';
  import {
    ProviderModeSelector,
    StrictModeToggle,
    OllamaStatus,
    FeatureProviderMatrix,
    AgentProviderOverride,
    AzureSetup
  } from '$lib/components/settings';
  import { AccessibilitySettings } from '$lib/components/accessibility';

  // API Keys state
  let apiKeys = {
    openai_api_key: '',
    anthropic_api_key: '',
    perplexity_api_key: ''
  };

  let keyStatus = {
    openai: { is_configured: false, is_valid: null },
    anthropic: { is_configured: false, is_valid: null },
    perplexity: { is_configured: false, is_valid: null }
  };

  // AI Provider Settings
  let aiSettings = {
    mode: 'ollama_only',
    strict_mode: false,
    default_model: 'llama3.2:latest',
    feature_overrides: {} as Record<string, { provider: string; model: string }>,
    agent_overrides: {} as Record<string, { provider: string; model: string }>,
    azure_config: {
      endpoint: '',
      api_key: '',
      deployment_name: '',
      api_version: '2024-02-15-preview'
    }
  };

  let saving = false;
  let testing = false;
  let showSuccess = false;
  let savingAiSettings = false;
  let aiSettingsSuccess = false;
  let activeTab: 'api-keys' | 'ai-provider' | 'accessibility' = 'ai-provider';

  onMount(async () => {
    await Promise.all([loadKeyStatus(), loadAiSettings()]);
  });

  async function loadKeyStatus() {
    try {
      const response = await fetch('http://localhost:9000/api/v1/user-keys/status');
      if (response.ok) {
        keyStatus = await response.json();
      }
    } catch {
      // Silent failure
    }
  }

  async function loadAiSettings() {
    try {
      const response = await fetch('http://localhost:9000/api/v1/settings/ai/config');
      if (response.ok) {
        const data = await response.json();
        aiSettings = { ...aiSettings, ...data };
      }
    } catch {
      // Silent failure
    }
  }

  async function saveApiKeys() {
    saving = true;
    try {
      const response = await fetch('http://localhost:9000/api/v1/user-keys', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(apiKeys)
      });

      if (response.ok) {
        showSuccess = true;
        setTimeout(() => showSuccess = false, 3000);
        await loadKeyStatus();
        apiKeys.openai_api_key = '';
        apiKeys.anthropic_api_key = '';
        apiKeys.perplexity_api_key = '';
      } else {
        alert('Failed to save API keys');
      }
    } catch {
      // Silent failure
      alert('Failed to save API keys');
    } finally {
      saving = false;
    }
  }

  async function saveAiSettings() {
    savingAiSettings = true;
    try {
      const response = await fetch('http://localhost:9000/api/v1/settings/ai/config', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(aiSettings)
      });

      if (response.ok) {
        aiSettingsSuccess = true;
        setTimeout(() => aiSettingsSuccess = false, 3000);
      } else {
        alert('Failed to save AI settings');
      }
    } catch {
      // Silent failure
      alert('Failed to save AI settings');
    } finally {
      savingAiSettings = false;
    }
  }

  async function testApiKey(service: string) {
    testing = true;
    try {
      const response = await fetch(`http://localhost:9000/api/v1/user-keys/test/${service}`, {
        method: 'POST'
      });

      const result = await response.json();

      if (response.ok) {
        alert(`${service.toUpperCase()} API Key: ${result.message}`);
      } else {
        alert(`${service.toUpperCase()} API Key test failed: ${result.detail}`);
      }

      await loadKeyStatus();
    } catch {
      // Silent failure
      alert(`Failed to test ${service} API key`);
    } finally {
      testing = false;
    }
  }

  async function clearApiKeys() {
    if (!confirm('Are you sure you want to clear all stored API keys?')) {
      return;
    }

    try {
      const response = await fetch('http://localhost:9000/api/v1/user-keys', {
        method: 'DELETE'
      });

      if (response.ok) {
        await loadKeyStatus();
        alert('API keys cleared successfully');
      } else {
        alert('Failed to clear API keys');
      }
    } catch {
      // Silent failure
      alert('Failed to clear API keys');
    }
  }

  function handleModeChange(event: CustomEvent<{ mode: string }>) {
    aiSettings.mode = event.detail.mode;
  }

  function handleStrictModeChange(event: CustomEvent<{ enabled: boolean }>) {
    aiSettings.strict_mode = event.detail.enabled;
  }

  function handleFeatureOverrideChange(event: CustomEvent<{ overrides: Record<string, { provider: string; model: string }> }>) {
    aiSettings.feature_overrides = event.detail.overrides;
  }

  function handleAgentOverrideChange(event: CustomEvent<{ overrides: Record<string, { provider: string; model: string }> }>) {
    aiSettings.agent_overrides = event.detail.overrides;
  }

  function handleAzureConfigChange(event: CustomEvent<{ config: typeof aiSettings.azure_config }>) {
    aiSettings.azure_config = event.detail.config;
  }
</script>

<style>
  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
  }
</style>

<svelte:head>
  <title>Settings - platform.Convergio.io</title>
</svelte:head>

<div class="space-y-6">
  <!-- Header -->
  <header>
    <h1 class="text-lg font-medium text-surface-900">Settings</h1>
    <p class="mt-1 text-xs text-surface-500">Configure AI providers, API keys, and platform preferences</p>
  </header>

  <!-- Tab Navigation -->
  <div class="border-b border-surface-200">
    <nav class="flex space-x-4" aria-label="Settings tabs">
      <button
        on:click={() => activeTab = 'ai-provider'}
        class="px-3 py-2 text-sm font-medium border-b-2 transition-colors {activeTab === 'ai-provider'
          ? 'border-gray-900 text-gray-900'
          : 'border-transparent text-surface-500 hover:text-surface-700 hover:border-surface-300'}"
        aria-current={activeTab === 'ai-provider' ? 'page' : undefined}
      >
        AI Providers
      </button>
      <button
        on:click={() => activeTab = 'api-keys'}
        class="px-3 py-2 text-sm font-medium border-b-2 transition-colors {activeTab === 'api-keys'
          ? 'border-gray-900 text-gray-900'
          : 'border-transparent text-surface-500 hover:text-surface-700 hover:border-surface-300'}"
        aria-current={activeTab === 'api-keys' ? 'page' : undefined}
      >
        API Keys
      </button>
      <button
        on:click={() => activeTab = 'accessibility'}
        class="px-3 py-2 text-sm font-medium border-b-2 transition-colors {activeTab === 'accessibility'
          ? 'border-gray-900 text-gray-900'
          : 'border-transparent text-surface-500 hover:text-surface-700 hover:border-surface-300'}"
        aria-current={activeTab === 'accessibility' ? 'page' : undefined}
      >
        Accessibility
      </button>
    </nav>
  </div>

  <!-- Success Messages -->
  {#if showSuccess}
    <div class="bg-green-50 border border-green-200 rounded p-3" role="alert" aria-live="polite">
      <div class="flex items-center">
        <img src="/convergio_icons/success.svg" alt="Success" class="h-4 w-4 text-green-600 mr-2" />
        <p class="text-sm text-green-800 font-medium">API keys saved successfully!</p>
      </div>
    </div>
  {/if}

  {#if aiSettingsSuccess}
    <div class="bg-green-50 border border-green-200 rounded p-3" role="alert" aria-live="polite">
      <div class="flex items-center">
        <img src="/convergio_icons/success.svg" alt="Success" class="h-4 w-4 text-green-600 mr-2" />
        <p class="text-sm text-green-800 font-medium">AI settings saved successfully!</p>
      </div>
    </div>
  {/if}

  <!-- AI Provider Tab -->
  {#if activeTab === 'ai-provider'}
    <div class="space-y-6">
      <!-- Provider Mode Selection -->
      <section class="bg-white border border-surface-200 rounded" aria-labelledby="provider-mode-heading">
        <div class="px-4 py-3 border-b border-surface-200">
          <h3 id="provider-mode-heading" class="text-sm font-medium text-surface-900">AI Provider Mode</h3>
          <p class="text-xs text-surface-500 mt-1">Choose how AI requests are routed</p>
        </div>
        <div class="p-4">
          <ProviderModeSelector
            currentMode={aiSettings.mode}
            on:change={handleModeChange}
          />
        </div>
      </section>

      <!-- Strict Mode -->
      <section aria-labelledby="strict-mode-heading">
        <h3 id="strict-mode-heading" class="sr-only">Strict Mode Settings</h3>
        <StrictModeToggle
          enabled={aiSettings.strict_mode}
          currentMode={aiSettings.mode}
          on:change={handleStrictModeChange}
        />
      </section>

      <!-- Ollama Status -->
      {#if aiSettings.mode === 'ollama_only' || aiSettings.mode === 'hybrid'}
        <section aria-labelledby="ollama-status-heading">
          <h3 id="ollama-status-heading" class="sr-only">Ollama Status</h3>
          <OllamaStatus />
        </section>
      {/if}

      <!-- Azure Setup -->
      {#if aiSettings.mode === 'azure_only' || aiSettings.mode === 'hybrid'}
        <section aria-labelledby="azure-setup-heading">
          <h3 id="azure-setup-heading" class="sr-only">Azure OpenAI Setup</h3>
          <AzureSetup
            config={aiSettings.azure_config}
            on:change={handleAzureConfigChange}
          />
        </section>
      {/if}

      <!-- Feature Provider Matrix -->
      {#if aiSettings.mode === 'hybrid'}
        <section aria-labelledby="feature-matrix-heading">
          <h3 id="feature-matrix-heading" class="sr-only">Feature Provider Matrix</h3>
          <FeatureProviderMatrix
            overrides={aiSettings.feature_overrides}
            currentMode={aiSettings.mode}
            on:change={handleFeatureOverrideChange}
          />
        </section>
      {/if}

      <!-- Agent Provider Overrides -->
      {#if aiSettings.mode === 'hybrid'}
        <section aria-labelledby="agent-override-heading">
          <h3 id="agent-override-heading" class="sr-only">Agent Provider Overrides</h3>
          <AgentProviderOverride
            overrides={aiSettings.agent_overrides}
            currentMode={aiSettings.mode}
            on:change={handleAgentOverrideChange}
          />
        </section>
      {/if}

      <!-- Save Button -->
      <div class="flex justify-end pt-4 border-t border-surface-200">
        <button
          on:click={saveAiSettings}
          disabled={savingAiSettings}
          class="px-4 py-2 bg-gray-900 hover:bg-gray-800 disabled:bg-surface-300 text-white text-sm font-medium rounded transition-colors disabled:cursor-not-allowed"
        >
          {#if savingAiSettings}
            Saving...
          {:else}
            Save AI Settings
          {/if}
        </button>
      </div>

      <!-- Cost Information for Ollama -->
      {#if aiSettings.mode === 'ollama_only'}
        <section class="bg-green-50 border border-green-200 rounded p-4" aria-labelledby="ollama-cost-heading">
          <div class="flex items-start space-x-3">
            <span class="text-xl">💰</span>
            <div>
              <h4 id="ollama-cost-heading" class="text-xs font-medium text-green-900">$0 AI Costs</h4>
              <p class="text-xs text-green-800 mt-1">
                Running in Ollama-only mode. All AI operations are processed locally with zero API costs.
                Your data never leaves your machine.
              </p>
            </div>
          </div>
        </section>
      {/if}
    </div>
  {/if}

  <!-- API Keys Tab -->
  {#if activeTab === 'api-keys'}
    <section class="bg-white border border-surface-200 rounded" aria-labelledby="api-keys-heading">
      <div class="px-4 py-3 border-b border-surface-200">
        <h3 id="api-keys-heading" class="text-sm font-medium text-surface-900">API Keys Configuration</h3>
        <p class="text-xs text-surface-500 mt-1">
          Your API keys are encrypted and stored securely. Required for cloud AI functionality.
        </p>
      </div>

      <div class="p-4 space-y-4">
        <!-- OpenAI API Key -->
        <div class="space-y-2">
          <label for="openai-key" class="block text-xs font-medium text-surface-700">
            OpenAI API Key
            <span class="font-normal text-surface-500">(For cloud_first mode)</span>
          </label>
          <div class="flex space-x-2">
            <input
              id="openai-key"
              type="password"
              bind:value={apiKeys.openai_api_key}
              placeholder="sk-..."
              class="flex-1 px-3 py-2 border border-surface-300 rounded text-sm focus:ring-1 focus:ring-gray-900 focus:border-gray-900"
              aria-describedby="openai-help"
            />
            <div class="flex items-center space-x-2">
              {#if keyStatus.openai.is_configured}
                <span class="flex items-center text-xs text-green-600" role="status">
                  <div class="h-2 w-2 bg-green-500 rounded-full mr-1"></div>
                  Configured
                </span>
                <button
                  on:click={() => testApiKey('openai')}
                  disabled={testing}
                  class="px-2 py-1 text-xs bg-surface-100 hover:bg-surface-200 text-surface-700 rounded transition-colors disabled:opacity-50"
                >
                  {testing ? 'Testing...' : 'Test'}
                </button>
              {:else}
                <span class="flex items-center text-xs text-gray-400" role="status">
                  <div class="h-2 w-2 bg-surface-300 rounded-full mr-1"></div>
                  Not set
                </span>
              {/if}
            </div>
          </div>
          <p id="openai-help" class="text-xs text-surface-500">
            Get your API key from <a href="https://platform.openai.com/api-keys" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:text-blue-800">OpenAI Platform</a>
          </p>
        </div>

        <!-- Anthropic API Key -->
        <div class="space-y-2">
          <label for="anthropic-key" class="block text-xs font-medium text-surface-700">
            Anthropic Claude API Key
            <span class="font-normal text-surface-500">(Optional)</span>
          </label>
          <div class="flex space-x-2">
            <input
              id="anthropic-key"
              type="password"
              bind:value={apiKeys.anthropic_api_key}
              placeholder="sk-ant-..."
              class="flex-1 px-3 py-2 border border-surface-300 rounded text-sm focus:ring-1 focus:ring-gray-900 focus:border-gray-900"
              aria-describedby="anthropic-help"
            />
            <div class="flex items-center space-x-2">
              {#if keyStatus.anthropic.is_configured}
                <span class="flex items-center text-xs text-green-600" role="status">
                  <div class="h-2 w-2 bg-green-500 rounded-full mr-1"></div>
                  Configured
                </span>
                <button
                  on:click={() => testApiKey('anthropic')}
                  disabled={testing}
                  class="px-2 py-1 text-xs bg-surface-100 hover:bg-surface-200 text-surface-700 rounded transition-colors disabled:opacity-50"
                >
                  {testing ? 'Testing...' : 'Test'}
                </button>
              {:else}
                <span class="flex items-center text-xs text-gray-400" role="status">
                  <div class="h-2 w-2 bg-surface-300 rounded-full mr-1"></div>
                  Optional
                </span>
              {/if}
            </div>
          </div>
          <p id="anthropic-help" class="text-xs text-surface-500">
            Get your API key from <a href="https://console.anthropic.com/" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:text-blue-800">Anthropic Console</a>
          </p>
        </div>

        <!-- Perplexity API Key -->
        <div class="space-y-2">
          <label for="perplexity-key" class="block text-xs font-medium text-surface-700">
            Perplexity API Key
            <span class="font-normal text-surface-500">(For real-time web search)</span>
          </label>
          <div class="flex space-x-2">
            <input
              id="perplexity-key"
              type="password"
              bind:value={apiKeys.perplexity_api_key}
              placeholder="pplx-..."
              class="flex-1 px-3 py-2 border border-surface-300 rounded text-sm focus:ring-1 focus:ring-gray-900 focus:border-gray-900"
              aria-describedby="perplexity-help"
            />
            <div class="flex items-center space-x-2">
              {#if keyStatus.perplexity?.is_configured}
                <span class="flex items-center text-xs text-green-600" role="status">
                  <div class="h-2 w-2 bg-green-500 rounded-full mr-1"></div>
                  Configured
                </span>
                <button
                  on:click={() => testApiKey('perplexity')}
                  disabled={testing}
                  class="px-2 py-1 text-xs bg-surface-100 hover:bg-surface-200 text-surface-700 rounded transition-colors disabled:opacity-50"
                >
                  {testing ? 'Testing...' : 'Test'}
                </button>
              {:else}
                <span class="flex items-center text-xs text-yellow-600" role="status">
                  <div class="h-2 w-2 bg-yellow-500 rounded-full mr-1"></div>
                  Recommended
                </span>
              {/if}
            </div>
          </div>
          <p id="perplexity-help" class="text-xs text-surface-500">
            Get your API key from <a href="https://www.perplexity.ai/settings/api" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:text-blue-800">Perplexity Settings</a>
          </p>
        </div>

        <!-- Action Buttons -->
        <div class="flex justify-between pt-4 border-t border-surface-200">
          <div class="flex space-x-2">
            <button
              on:click={saveApiKeys}
              disabled={saving}
              class="px-3 py-2 bg-gray-900 hover:bg-gray-800 disabled:bg-surface-300 text-white text-xs font-medium rounded transition-colors disabled:cursor-not-allowed"
            >
              {#if saving}
                Saving...
              {:else}
                Save API Keys
              {/if}
            </button>
          </div>

          {#if keyStatus.openai.is_configured || keyStatus.anthropic.is_configured || keyStatus.perplexity?.is_configured}
            <button
              on:click={clearApiKeys}
              class="px-3 py-2 text-xs text-red-600 hover:text-red-800 transition-colors"
            >
              Clear All Keys
            </button>
          {/if}
        </div>
      </div>
    </section>

    <!-- Security Notice -->
    <section class="bg-blue-50 border border-blue-200 rounded p-4" aria-labelledby="security-heading">
      <div class="flex items-start space-x-3">
        <img src="/convergio_icons/security_shield.svg" alt="Security shield" class="h-4 w-4 text-blue-600 mt-0.5" />
        <div>
          <h4 id="security-heading" class="text-xs font-medium text-blue-900">Security & Privacy</h4>
          <ul class="text-xs text-blue-800 mt-1 space-y-1 list-disc ml-4">
            <li>API keys are encrypted using industry-standard encryption</li>
            <li>Keys are stored temporarily per session (not permanently saved)</li>
            <li>No API keys are transmitted to external servers except directly to providers</li>
            <li>Use Ollama-only mode for complete data privacy</li>
          </ul>
        </div>
      </div>
    </section>
  {/if}

  <!-- Accessibility Tab -->
  {#if activeTab === 'accessibility'}
    <AccessibilitySettings />
  {/if}
</div>
