<script lang="ts">
  import { createEventDispatcher } from 'svelte';

  export let currentMode: string = 'ollama_only';
  export let disabled: boolean = false;

  const dispatch = createEventDispatcher();

  const modes = [
    {
      id: 'ollama_only',
      name: 'Ollama Only',
      description: 'Use local Ollama for all AI operations. $0 cost, full privacy.',
      icon: '🏠',
      pros: ['$0 cost', 'Complete privacy', 'Offline capable', 'No rate limits'],
      cons: ['Requires local GPU', 'Slower than cloud', 'Limited model selection']
    },
    {
      id: 'azure_only',
      name: 'Azure OpenAI Only',
      description: 'Enterprise Azure deployment. Compliance-ready.',
      icon: '☁️',
      pros: ['Enterprise SLA', 'GDPR compliant', 'Private endpoints', 'Scalable'],
      cons: ['Monthly costs', 'Requires Azure subscription', 'Setup complexity']
    },
    {
      id: 'hybrid',
      name: 'Hybrid Mode',
      description: 'Ollama for simple tasks, cloud for complex. Best balance.',
      icon: '⚡',
      pros: ['Cost optimized', 'Best of both', 'Automatic routing', 'Fallback support'],
      cons: ['Configuration needed', 'Some cloud costs']
    },
    {
      id: 'cloud_first',
      name: 'Cloud First',
      description: 'Cloud providers with Ollama fallback. Maximum capability.',
      icon: '🚀',
      pros: ['Latest models', 'Fastest inference', 'All features', 'Ollama backup'],
      cons: ['Higher costs', 'Network dependent', 'Data leaves local']
    }
  ];

  function selectMode(modeId: string) {
    if (disabled) return;
    currentMode = modeId;
    dispatch('change', { mode: modeId });
  }

  $: selectedMode = modes.find(m => m.id === currentMode);
</script>

<div class="space-y-4">
  <div class="grid grid-cols-2 gap-3">
    {#each modes as mode}
      <button
        on:click={() => selectMode(mode.id)}
        disabled={disabled}
        class="relative p-4 text-left border rounded-lg transition-all {currentMode === mode.id
          ? 'border-gray-900 bg-gray-50 ring-1 ring-gray-900'
          : 'border-surface-200 hover:border-surface-400'} {disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}"
        aria-pressed={currentMode === mode.id}
      >
        <div class="flex items-start space-x-3">
          <span class="text-2xl" aria-hidden="true">{mode.icon}</span>
          <div class="flex-1 min-w-0">
            <h4 class="text-sm font-medium text-surface-900">{mode.name}</h4>
            <p class="text-xs text-surface-500 mt-1">{mode.description}</p>
          </div>
        </div>
        {#if currentMode === mode.id}
          <div class="absolute top-2 right-2">
            <svg class="h-5 w-5 text-gray-900" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
            </svg>
          </div>
        {/if}
      </button>
    {/each}
  </div>

  {#if selectedMode}
    <div class="grid grid-cols-2 gap-4 p-4 bg-surface-50 rounded-lg">
      <div>
        <h5 class="text-xs font-medium text-green-700 mb-2">Advantages</h5>
        <ul class="space-y-1">
          {#each selectedMode.pros as pro}
            <li class="flex items-center text-xs text-surface-700">
              <svg class="h-3 w-3 text-green-500 mr-2 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/>
              </svg>
              {pro}
            </li>
          {/each}
        </ul>
      </div>
      <div>
        <h5 class="text-xs font-medium text-amber-700 mb-2">Considerations</h5>
        <ul class="space-y-1">
          {#each selectedMode.cons as con}
            <li class="flex items-center text-xs text-surface-700">
              <svg class="h-3 w-3 text-amber-500 mr-2 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
              </svg>
              {con}
            </li>
          {/each}
        </ul>
      </div>
    </div>
  {/if}
</div>
