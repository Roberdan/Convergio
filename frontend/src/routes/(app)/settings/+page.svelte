<script lang="ts">
  import { onMount } from 'svelte';

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

  let saving = false;
  let testing = false;
  let showSuccess = false;

  onMount(async () => {
    await loadKeyStatus();
  });

  async function loadKeyStatus() {
    try {
      const response = await fetch('http://localhost:9000/api/v1/user-keys/status');
      if (response.ok) {
        keyStatus = await response.json();
      }
    } catch (error) {
      console.error('Failed to load API key status:', error);
    }
  }

  async function saveApiKeys() {
    // Allow saving model preference even if key is empty
    saving = true;
    try {
      const response = await fetch('http://localhost:9000/api/v1/user-keys', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(apiKeys)
      });

      if (response.ok) {
        showSuccess = true;
        setTimeout(() => showSuccess = false, 3000);
        await loadKeyStatus();
        
        // Clear only key fields
        apiKeys.openai_api_key = '';
        apiKeys.anthropic_api_key = '';
        apiKeys.perplexity_api_key = '';
      } else {
        alert('Failed to save API keys');
      }
    } catch (error) {
      console.error('Failed to save API keys:', error);
      alert('Failed to save API keys');
    } finally {
      saving = false;
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
    } catch (error) {
      console.error(`Failed to test ${service} API key:`, error);
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
    } catch (error) {
      console.error('Failed to clear API keys:', error);
      alert('Failed to clear API keys');
    }
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

<!-- Settings Page -->
<div class="space-y-6">
  <!-- Header -->
  <header>
    <h1 class="text-lg font-medium text-surface-900">Settings</h1>
    <p class="mt-1 text-xs text-surface-500">Configure your API keys and platform preferences</p>
  </header>

  <!-- Success Message -->
  {#if showSuccess}
    <div class="bg-green-50 border border-green-200 rounded p-3" role="alert" aria-live="polite">
      <div class="flex items-center">
        <img src="/convergio_icons/success.svg" alt="Success" class="h-4 w-4 text-green-600 mr-2" />
        <p class="text-sm text-green-800 font-medium">API keys saved successfully!</p>
      </div>
    </div>
  {/if}

  <!-- API Keys Configuration -->
  <section class="bg-white border border-surface-200 rounded" aria-labelledby="api-keys-heading">
    <div class="px-4 py-3 border-b border-surface-200">
      <h3 id="api-keys-heading" class="text-sm font-medium text-surface-900">API Keys Configuration</h3>
      <p class="text-xs text-surface-500 mt-1">
        Your API keys are encrypted and stored securely. Required for AI agent functionality.
      </p>
    </div>

    <div class="p-4 space-y-4">
      <!-- OpenAI API Key -->
      <div class="space-y-2">
        <label for="openai-key" class="block text-xs font-medium text-surface-700">
          OpenAI API Key <span class="text-red-500" aria-label="required">*</span>
          <span class="font-normal text-surface-500">(Required - Primary AI service)</span>
        </label>
        <div class="flex space-x-2">
          <input
            id="openai-key"
            type="password"
            bind:value={apiKeys.openai_api_key}
            placeholder="sk-..."
            class="flex-1 px-3 py-2 border border-surface-300 rounded text-sm focus:ring-1 focus:ring-gray-900 focus:border-gray-900"
            aria-describedby="openai-help"
            aria-required="false"
          />
          <div class="flex items-center space-x-2">
            {#if keyStatus.openai.is_configured}
              <span class="flex items-center text-xs text-green-600" role="status" aria-label="OpenAI API key configured">
                <div class="h-2 w-2 bg-green-500 rounded-full mr-1" aria-hidden="true"></div>
                Configured
              </span>
            {:else}
              <span class="flex items-center text-xs text-gray-400" role="status" aria-label="OpenAI API key not set">
                <div class="h-2 w-2 bg-surface-300 rounded-full mr-1" aria-hidden="true"></div>
                Not set
              </span>
            {/if}
            {#if keyStatus.openai.is_configured}
              <button
                on:click={() => testApiKey('openai')}
                disabled={testing}
                class="px-2 py-1 text-xs bg-surface-100 hover:bg-surface-200 text-surface-700 rounded transition-colors disabled:opacity-50"
                aria-label="Test OpenAI API key"
              >
                {testing ? 'Testing...' : 'Test'}
              </button>
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
          <span class="font-normal text-surface-500">(Optional - Alternative AI service)</span>
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
              <span class="flex items-center text-xs text-green-600" role="status" aria-label="Anthropic API key configured">
                <div class="h-2 w-2 bg-green-500 rounded-full mr-1" aria-hidden="true"></div>
                Configured
              </span>
            {:else}
              <span class="flex items-center text-xs text-gray-400" role="status" aria-label="Anthropic API key optional">
                <div class="h-2 w-2 bg-surface-300 rounded-full mr-1" aria-hidden="true"></div>
                Optional
              </span>
            {/if}
            {#if keyStatus.anthropic.is_configured}
              <button
                on:click={() => testApiKey('anthropic')}
                disabled={testing}
                class="px-2 py-1 text-xs bg-surface-100 hover:bg-surface-200 text-surface-700 rounded transition-colors disabled:opacity-50"
                aria-label="Test Anthropic API key"
              >
                {testing ? 'Testing...' : 'Test'}
              </button>
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
          <span class="font-normal text-surface-500">(Required for real-time web search)</span>
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
              <span class="flex items-center text-xs text-green-600" role="status" aria-label="Perplexity API key configured">
                <div class="h-2 w-2 bg-green-500 rounded-full mr-1" aria-hidden="true"></div>
                Configured
              </span>
            {:else}
              <span class="flex items-center text-xs text-yellow-600" role="status" aria-label="Perplexity API key recommended">
                <div class="h-2 w-2 bg-yellow-500 rounded-full mr-1" aria-hidden="true"></div>
                Recommended
              </span>
            {/if}
            {#if keyStatus.perplexity?.is_configured}
              <button
                on:click={() => testApiKey('perplexity')}
                disabled={testing}
                class="px-2 py-1 text-xs bg-surface-100 hover:bg-surface-200 text-surface-700 rounded transition-colors disabled:opacity-50"
                aria-label="Test Perplexity API key"
              >
                {testing ? 'Testing...' : 'Test'}
              </button>
            {/if}
          </div>
        </div>
        <p id="perplexity-help" class="text-xs text-surface-500">
          Get your API key from <a href="https://www.perplexity.ai/settings/api" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:text-blue-800">Perplexity Settings</a>. Enables real-time data access for financial queries.
        </p>
      </div>

      <!-- Action Buttons -->
      <div class="flex justify-between pt-4 border-t border-surface-200">
        <div class="flex space-x-2">
          <button
            on:click={saveApiKeys}
            disabled={saving}
            class="px-3 py-2 bg-gray-900 hover:bg-gray-800 disabled:bg-surface-300 text-white text-xs font-medium rounded transition-colors disabled:cursor-not-allowed"
            aria-describedby="save-help"
          >
            {#if saving}
              <span aria-live="polite">Saving...</span>
            {:else}
              Save API Keys
            {/if}
          </button>
          <div id="save-help" class="sr-only">You can save keys and/or default model</div>
        </div>
        
        {#if keyStatus.openai.is_configured || keyStatus.anthropic.is_configured || keyStatus.perplexity?.is_configured}
          <button
            on:click={clearApiKeys}
            class="px-3 py-2 text-xs text-red-600 hover:text-red-800 transition-colors"
            aria-label="Clear all stored API keys"
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
          <li>No API keys are transmitted to external servers except directly to OpenAI/Anthropic</li>
          <li>Clear your keys before closing the browser for maximum security</li>
        </ul>
      </div>
    </div>
  </section>

  <!-- Cost Information -->
  <section class="bg-yellow-50 border border-yellow-200 rounded p-4" aria-labelledby="cost-heading">
    <div class="flex items-start space-x-3">
      <img src="/convergio_icons/info.svg" alt="Information" class="h-4 w-4 text-yellow-600 mt-0.5" />
      <div>
        <h4 id="cost-heading" class="text-xs font-medium text-yellow-900">API Usage & Costs</h4>
        <ul class="text-xs text-yellow-800 mt-1 space-y-1 list-disc ml-4">
          <li><strong>OpenAI GPT-4:</strong> ~$0.03-0.06 per conversation (varies by length)</li>
          <li><strong>Anthropic Claude:</strong> ~$0.015-0.075 per conversation</li>
          <li><strong>Perplexity Sonar:</strong> ~$0.005 per search query (real-time web data)</li>
          <li>You maintain full control over your API usage and billing</li>
        </ul>
      </div>
    </div>
  </section>
</div>
