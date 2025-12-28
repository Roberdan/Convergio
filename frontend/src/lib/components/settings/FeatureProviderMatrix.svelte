<script lang="ts">
  import { createEventDispatcher } from 'svelte';

  export let overrides: Record<string, { provider: string; model: string }> = {};
  export let currentMode: string = 'ollama_only';
  export let disabled: boolean = false;

  const dispatch = createEventDispatcher();

  const features = [
    { id: 'chat_simple', name: 'Simple Chat', description: 'Basic Q&A, greetings' },
    { id: 'chat_complex', name: 'Complex Chat', description: 'Multi-turn reasoning' },
    { id: 'function_calling', name: 'Function Calling', description: 'Tool use, API calls' },
    { id: 'code_review', name: 'Code Review', description: 'Code analysis, suggestions' },
    { id: 'code_generation', name: 'Code Generation', description: 'Write new code' },
    { id: 'embeddings', name: 'Embeddings', description: 'Vector search, RAG' },
    { id: 'vision', name: 'Vision/Images', description: 'Image analysis' },
    { id: 'voice_realtime', name: 'Voice/Realtime', description: 'Streaming voice' }
  ];

  const providers = [
    { id: 'default', name: 'Default', description: 'Use mode default' },
    { id: 'ollama', name: 'Ollama', description: 'Local' },
    { id: 'azure_openai', name: 'Azure OpenAI', description: 'Enterprise' },
    { id: 'openai', name: 'OpenAI', description: 'Direct API' },
    { id: 'anthropic', name: 'Anthropic', description: 'Claude' }
  ];

  const modelsByProvider: Record<string, string[]> = {
    ollama: ['llama3.2:latest', 'qwen2.5-coder:14b', 'mixtral:latest', 'nomic-embed-text:latest'],
    azure_openai: ['gpt-4o', 'gpt-4-turbo', 'gpt-35-turbo'],
    openai: ['gpt-4o', 'gpt-4-turbo', 'gpt-3.5-turbo'],
    anthropic: ['claude-3-5-sonnet', 'claude-3-opus', 'claude-3-haiku']
  };

  function getOverride(featureId: string) {
    return overrides[featureId] || { provider: 'default', model: '' };
  }

  function updateOverride(featureId: string, field: 'provider' | 'model', value: string) {
    if (disabled) return;

    const current = getOverride(featureId);
    const updated = { ...current, [field]: value };

    if (field === 'provider' && value !== current.provider) {
      updated.model = value === 'default' ? '' : (modelsByProvider[value]?.[0] || '');
    }

    if (value === 'default' && field === 'provider') {
      delete overrides[featureId];
    } else {
      overrides[featureId] = updated;
    }

    overrides = { ...overrides };
    dispatch('change', { overrides });
  }

  function isProviderAvailable(providerId: string): boolean {
    if (providerId === 'default') return true;
    if (currentMode === 'ollama_only') return providerId === 'ollama';
    if (currentMode === 'azure_only') return providerId === 'azure_openai';
    return true;
  }
</script>

<div class="border rounded-lg overflow-hidden">
  <div class="px-4 py-3 bg-surface-50 border-b border-surface-200">
    <h4 class="text-sm font-medium text-surface-900">Feature-Provider Mapping</h4>
    <p class="text-xs text-surface-500 mt-1">Override which provider handles each feature type</p>
  </div>

  <div class="overflow-x-auto">
    <table class="w-full text-sm">
      <thead class="bg-surface-50">
        <tr>
          <th class="px-4 py-2 text-left text-xs font-medium text-surface-500 uppercase">Feature</th>
          <th class="px-4 py-2 text-left text-xs font-medium text-surface-500 uppercase">Provider</th>
          <th class="px-4 py-2 text-left text-xs font-medium text-surface-500 uppercase">Model</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-surface-200">
        {#each features as feature}
          {@const override = getOverride(feature.id)}
          <tr class="hover:bg-surface-50">
            <td class="px-4 py-3">
              <div>
                <span class="font-medium text-surface-900">{feature.name}</span>
                <p class="text-xs text-surface-500">{feature.description}</p>
              </div>
            </td>
            <td class="px-4 py-3">
              <select
                value={override.provider}
                on:change={(e) => updateOverride(feature.id, 'provider', e.currentTarget.value)}
                disabled={disabled}
                class="w-full px-2 py-1.5 text-sm border border-surface-300 rounded focus:ring-1 focus:ring-gray-900 focus:border-gray-900 disabled:opacity-50 disabled:bg-surface-100"
              >
                {#each providers as provider}
                  <option
                    value={provider.id}
                    disabled={!isProviderAvailable(provider.id)}
                  >
                    {provider.name}
                    {#if !isProviderAvailable(provider.id)}
                      (blocked)
                    {/if}
                  </option>
                {/each}
              </select>
            </td>
            <td class="px-4 py-3">
              {#if override.provider !== 'default' && modelsByProvider[override.provider]}
                <select
                  value={override.model}
                  on:change={(e) => updateOverride(feature.id, 'model', e.currentTarget.value)}
                  disabled={disabled}
                  class="w-full px-2 py-1.5 text-sm border border-surface-300 rounded focus:ring-1 focus:ring-gray-900 focus:border-gray-900 disabled:opacity-50 disabled:bg-surface-100"
                >
                  {#each modelsByProvider[override.provider] as model}
                    <option value={model}>{model}</option>
                  {/each}
                </select>
              {:else}
                <span class="text-xs text-surface-400 italic">—</span>
              {/if}
            </td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
</div>
