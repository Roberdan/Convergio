<script lang="ts">
  import { onMount } from 'svelte';

  // API Keys state
  let apiKeys = {
    openai_api_key: '',
    anthropic_api_key: ''
  };

  let keyStatus = {
    openai: { is_configured: false, is_valid: null },
    anthropic: { is_configured: false, is_valid: null }
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
    if (!apiKeys.openai_api_key.trim()) {
      alert('OpenAI API Key is required for the platform to function');
      return;
    }

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
        
        // Clear the form
        apiKeys = {
          openai_api_key: '',
          anthropic_api_key: ''
        };
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

<svelte:head>
  <title>Settings - platform.Convergio.io</title>
</svelte:head>

<!-- Settings Page -->
<div class="space-y-6">
  <!-- Header -->
  <div>
    <h1 class="text-lg font-medium text-gray-900">Settings</h1>
    <p class="mt-1 text-xs text-gray-500">Configure your API keys and platform preferences</p>
  </div>

  <!-- Success Message -->
  {#if showSuccess}
    <div class="bg-green-50 border border-green-200 rounded p-3">
      <div class="flex items-center">
        <img src="/convergio_icons/success.svg" alt="" class="h-4 w-4 text-green-600 mr-2" />
        <p class="text-sm text-green-800 font-medium">API keys saved successfully!</p>
      </div>
    </div>
  {/if}

  <!-- API Keys Configuration -->
  <div class="bg-white border border-gray-200 rounded">
    <div class="px-4 py-3 border-b border-gray-200">
      <h3 class="text-sm font-medium text-gray-900">API Keys Configuration</h3>
      <p class="text-xs text-gray-500 mt-1">
        Your API keys are encrypted and stored securely. Required for AI agent functionality.
      </p>
    </div>

    <div class="p-4 space-y-4">
      <!-- OpenAI API Key -->
      <div class="space-y-2">
        <label class="block text-xs font-medium text-gray-700">
          OpenAI API Key <span class="text-red-500">*</span>
          <span class="font-normal text-gray-500">(Required - Primary AI service)</span>
        </label>
        <div class="flex space-x-2">
          <input
            type="password"
            bind:value={apiKeys.openai_api_key}
            placeholder="sk-..."
            class="flex-1 px-3 py-2 border border-gray-300 rounded text-sm focus:ring-1 focus:ring-gray-900 focus:border-gray-900"
          />
          <div class="flex items-center space-x-2">
            {#if keyStatus.openai.is_configured}
              <span class="flex items-center text-xs text-green-600">
                <div class="h-2 w-2 bg-green-500 rounded-full mr-1"></div>
                Configured
              </span>
            {:else}
              <span class="flex items-center text-xs text-gray-400">
                <div class="h-2 w-2 bg-gray-300 rounded-full mr-1"></div>
                Not set
              </span>
            {/if}
            {#if keyStatus.openai.is_configured}
              <button
                on:click={() => testApiKey('openai')}
                disabled={testing}
                class="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 rounded transition-colors disabled:opacity-50"
              >
                Test
              </button>
            {/if}
          </div>
        </div>
        <p class="text-xs text-gray-500">
          Get your API key from <a href="https://platform.openai.com/api-keys" target="_blank" class="text-blue-600 hover:text-blue-800">OpenAI Platform</a>
        </p>
      </div>

      <!-- Anthropic API Key -->
      <div class="space-y-2">
        <label class="block text-xs font-medium text-gray-700">
          Anthropic Claude API Key
          <span class="font-normal text-gray-500">(Optional - Alternative AI service)</span>
        </label>
        <div class="flex space-x-2">
          <input
            type="password"
            bind:value={apiKeys.anthropic_api_key}
            placeholder="sk-ant-..."
            class="flex-1 px-3 py-2 border border-gray-300 rounded text-sm focus:ring-1 focus:ring-gray-900 focus:border-gray-900"
          />
          <div class="flex items-center space-x-2">
            {#if keyStatus.anthropic.is_configured}
              <span class="flex items-center text-xs text-green-600">
                <div class="h-2 w-2 bg-green-500 rounded-full mr-1"></div>
                Configured
              </span>
            {:else}
              <span class="flex items-center text-xs text-gray-400">
                <div class="h-2 w-2 bg-gray-300 rounded-full mr-1"></div>
                Optional
              </span>
            {/if}
            {#if keyStatus.anthropic.is_configured}
              <button
                on:click={() => testApiKey('anthropic')}
                disabled={testing}
                class="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 rounded transition-colors disabled:opacity-50"
              >
                Test
              </button>
            {/if}
          </div>
        </div>
        <p class="text-xs text-gray-500">
          Get your API key from <a href="https://console.anthropic.com/" target="_blank" class="text-blue-600 hover:text-blue-800">Anthropic Console</a>
        </p>
      </div>

      <!-- Action Buttons -->
      <div class="flex justify-between pt-4 border-t border-gray-200">
        <div class="flex space-x-2">
          <button
            on:click={saveApiKeys}
            disabled={saving || !apiKeys.openai_api_key.trim()}
            class="px-3 py-2 bg-gray-900 hover:bg-gray-800 disabled:bg-gray-300 text-white text-xs font-medium rounded transition-colors disabled:cursor-not-allowed"
          >
            {#if saving}
              Saving...
            {:else}
              Save API Keys
            {/if}
          </button>
        </div>
        
        {#if keyStatus.openai.is_configured || keyStatus.anthropic.is_configured}
          <button
            on:click={clearApiKeys}
            class="px-3 py-2 text-xs text-red-600 hover:text-red-800 transition-colors"
          >
            Clear All Keys
          </button>
        {/if}
      </div>
    </div>
  </div>

  <!-- Security Notice -->
  <div class="bg-blue-50 border border-blue-200 rounded p-4">
    <div class="flex items-start space-x-3">
      <img src="/convergio_icons/security_shield.svg" alt="" class="h-4 w-4 text-blue-600 mt-0.5" />
      <div>
        <h4 class="text-xs font-medium text-blue-900">Security & Privacy</h4>
        <div class="text-xs text-blue-800 mt-1 space-y-1">
          <p>• API keys are encrypted using industry-standard encryption</p>
          <p>• Keys are stored temporarily per session (not permanently saved)</p>
          <p>• No API keys are transmitted to external servers except directly to OpenAI/Anthropic</p>
          <p>• Clear your keys before closing the browser for maximum security</p>
        </div>
      </div>
    </div>
  </div>

  <!-- Cost Information -->
  <div class="bg-yellow-50 border border-yellow-200 rounded p-4">
    <div class="flex items-start space-x-3">
      <img src="/convergio_icons/info.svg" alt="" class="h-4 w-4 text-yellow-600 mt-0.5" />
      <div>
        <h4 class="text-xs font-medium text-yellow-900">API Usage & Costs</h4>
        <div class="text-xs text-yellow-800 mt-1 space-y-1">
          <p>• <strong>OpenAI GPT-4:</strong> ~$0.03-0.06 per conversation (varies by length)</p>
          <p>• <strong>Anthropic Claude:</strong> ~$0.015-0.075 per conversation</p>
          <p>• You maintain full control over your API usage and billing</p>
        </div>
      </div>
    </div>
  </div>
</div>