<script lang="ts">
  import { createEventDispatcher } from 'svelte';

  export let enabled: boolean = false;
  export let currentMode: string = 'ollama_only';
  export let disabled: boolean = false;

  const dispatch = createEventDispatcher();

  function toggle() {
    if (disabled) return;
    enabled = !enabled;
    dispatch('change', { enabled });
  }

  $: isRelevant = currentMode === 'ollama_only' || currentMode === 'azure_only';
  $: modeLabel = currentMode === 'ollama_only' ? 'Ollama' : currentMode === 'azure_only' ? 'Azure' : 'selected provider';
</script>

<div class="p-4 border rounded-lg {enabled ? 'border-red-200 bg-red-50' : 'border-surface-200 bg-white'}">
  <div class="flex items-center justify-between">
    <div class="flex items-center space-x-3">
      <div class="flex-shrink-0">
        {#if enabled}
          <svg class="h-5 w-5 text-red-600" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clip-rule="evenodd"/>
          </svg>
        {:else}
          <svg class="h-5 w-5 text-surface-400" fill="currentColor" viewBox="0 0 20 20">
            <path d="M10 2a5 5 0 00-5 5v2a2 2 0 00-2 2v5a2 2 0 002 2h10a2 2 0 002-2v-5a2 2 0 00-2-2H7V7a3 3 0 015.905-.75 1 1 0 001.937-.5A5.002 5.002 0 0010 2z"/>
          </svg>
        {/if}
      </div>
      <div>
        <h4 class="text-sm font-medium {enabled ? 'text-red-900' : 'text-surface-900'}">
          Strict Mode
        </h4>
        <p class="text-xs {enabled ? 'text-red-700' : 'text-surface-500'}">
          {#if enabled}
            Cloud API calls are BLOCKED. Only {modeLabel} is allowed.
          {:else}
            Cloud API fallback is permitted when needed.
          {/if}
        </p>
      </div>
    </div>

    <button
      on:click={toggle}
      disabled={disabled}
      class="relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-offset-2 {enabled ? 'bg-red-600 focus:ring-red-500' : 'bg-surface-200 focus:ring-gray-500'} {disabled ? 'opacity-50 cursor-not-allowed' : ''}"
      role="switch"
      aria-checked={enabled}
      aria-label="Toggle strict mode"
    >
      <span
        class="pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out {enabled ? 'translate-x-5' : 'translate-x-0'}"
      ></span>
    </button>
  </div>

  {#if enabled && isRelevant}
    <div class="mt-3 p-2 bg-red-100 rounded text-xs text-red-800">
      <strong>Warning:</strong> Any attempt to use cloud providers will be blocked and logged.
      This ensures complete data privacy but may limit functionality for features requiring cloud capabilities.
    </div>
  {/if}
</div>
