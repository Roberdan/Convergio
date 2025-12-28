<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  
  let showWarning = false;
  let apiKeyStatus = null;
  
  onMount(async () => {
    await checkApiKeyStatus();
  });
  
  async function checkApiKeyStatus() {
    try {
      const response = await fetch('http://localhost:9000/api/v1/user-keys/status');
      if (response.ok) {
        apiKeyStatus = await response.json();
        showWarning = !apiKeyStatus.openai.is_configured;
      }
    } catch (error) {
      // Could not check API key status
    }
  }
  
  function dismissWarning() {
    showWarning = false;
  }
</script>

{#if showWarning}
  <div class="bg-yellow-50 border border-yellow-200 rounded p-3 mb-4">
    <div class="flex items-start justify-between">
      <div class="flex items-start space-x-3">
        <img src="/convergio_icons/warning.svg" alt="" class="h-4 w-4 text-yellow-600 mt-0.5" />
        <div>
          <h4 class="text-xs font-medium text-yellow-900">API Key Required</h4>
          <p class="text-xs text-yellow-800 mt-1">
            Configure your OpenAI API key to enable AI agent functionality. Your API key is encrypted and stored securely.
          </p>
          <div class="mt-2 flex space-x-2">
            <button
              on:click={() => goto('/settings')}
              class="text-xs font-medium text-yellow-900 hover:text-yellow-800 underline"
            >
              Configure API Key
            </button>
            <span class="text-yellow-500">•</span>
            <button
              on:click={dismissWarning}
              class="text-xs text-yellow-700 hover:text-yellow-600"
            >
              Dismiss
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
{/if}