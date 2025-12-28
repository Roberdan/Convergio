<script lang="ts">
  import { createEventDispatcher, onMount } from 'svelte';

  export let overrides: Record<string, { provider: string; model: string }> = {};
  export let currentMode: string = 'ollama_only';
  export let disabled: boolean = false;

  const dispatch = createEventDispatcher();

  interface Agent {
    id: string;
    name: string;
    category: string;
  }

  let agents: Agent[] = [];
  let loading = true;
  let searchQuery = '';
  let selectedCategory = 'all';

  const providers = [
    { id: 'default', name: 'Default' },
    { id: 'ollama', name: 'Ollama' },
    { id: 'azure_openai', name: 'Azure OpenAI' },
    { id: 'openai', name: 'OpenAI' },
    { id: 'anthropic', name: 'Anthropic' }
  ];

  const modelsByProvider: Record<string, string[]> = {
    ollama: ['llama3.2:latest', 'qwen2.5-coder:14b', 'mixtral:latest'],
    azure_openai: ['gpt-4o', 'gpt-4-turbo'],
    openai: ['gpt-4o', 'gpt-4-turbo'],
    anthropic: ['claude-3-5-sonnet', 'claude-3-opus']
  };

  onMount(async () => {
    try {
      const response = await fetch('http://localhost:9000/api/v1/agents');
      if (response.ok) {
        const data = await response.json();
        agents = data.map((a: { agent_id: string; name: string; category: string }) => ({
          id: a.agent_id,
          name: a.name,
          category: a.category
        }));
      }
    } catch (e) {
      console.error('Failed to load agents:', e);
    } finally {
      loading = false;
    }
  });

  function getOverride(agentId: string) {
    return overrides[agentId] || { provider: 'default', model: '' };
  }

  function updateOverride(agentId: string, field: 'provider' | 'model', value: string) {
    if (disabled) return;

    const current = getOverride(agentId);
    const updated = { ...current, [field]: value };

    if (field === 'provider' && value !== current.provider) {
      updated.model = value === 'default' ? '' : (modelsByProvider[value]?.[0] || '');
    }

    if (value === 'default' && field === 'provider') {
      delete overrides[agentId];
    } else {
      overrides[agentId] = updated;
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

  $: categories = ['all', ...new Set(agents.map(a => a.category))];

  $: filteredAgents = agents.filter(agent => {
    const matchesSearch = agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          agent.id.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = selectedCategory === 'all' || agent.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  $: overrideCount = Object.keys(overrides).length;
</script>

<div class="border rounded-lg overflow-hidden">
  <div class="px-4 py-3 bg-surface-50 border-b border-surface-200">
    <div class="flex items-center justify-between">
      <div>
        <h4 class="text-sm font-medium text-surface-900">Agent-Specific Providers</h4>
        <p class="text-xs text-surface-500 mt-1">Override provider for specific agents</p>
      </div>
      {#if overrideCount > 0}
        <span class="px-2 py-0.5 text-xs font-medium bg-blue-100 text-blue-800 rounded-full">
          {overrideCount} override{overrideCount !== 1 ? 's' : ''}
        </span>
      {/if}
    </div>
  </div>

  <div class="p-4 border-b border-surface-200 space-y-3">
    <div class="flex gap-3">
      <input
        type="text"
        bind:value={searchQuery}
        placeholder="Search agents..."
        class="flex-1 px-3 py-2 text-sm border border-surface-300 rounded focus:ring-1 focus:ring-gray-900 focus:border-gray-900"
      />
      <select
        bind:value={selectedCategory}
        class="px-3 py-2 text-sm border border-surface-300 rounded focus:ring-1 focus:ring-gray-900 focus:border-gray-900"
      >
        {#each categories as category}
          <option value={category}>
            {category === 'all' ? 'All Categories' : category}
          </option>
        {/each}
      </select>
    </div>
  </div>

  <div class="max-h-96 overflow-y-auto">
    {#if loading}
      <div class="p-8 text-center">
        <svg class="h-6 w-6 text-surface-400 animate-spin mx-auto" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
        </svg>
        <p class="mt-2 text-sm text-surface-500">Loading agents...</p>
      </div>
    {:else if filteredAgents.length === 0}
      <div class="p-8 text-center text-surface-500 text-sm">
        No agents found matching your criteria
      </div>
    {:else}
      <div class="divide-y divide-surface-200">
        {#each filteredAgents as agent}
          {@const override = getOverride(agent.id)}
          <div class="p-3 hover:bg-surface-50">
            <div class="flex items-center justify-between mb-2">
              <div>
                <span class="text-sm font-medium text-surface-900">{agent.name}</span>
                <span class="ml-2 px-1.5 py-0.5 text-xs bg-surface-100 text-surface-600 rounded">{agent.category}</span>
              </div>
              <span class="text-xs text-surface-400 font-mono">{agent.id}</span>
            </div>
            <div class="flex gap-2">
              <select
                value={override.provider}
                on:change={(e) => updateOverride(agent.id, 'provider', e.currentTarget.value)}
                disabled={disabled}
                class="flex-1 px-2 py-1 text-xs border border-surface-300 rounded focus:ring-1 focus:ring-gray-900 disabled:opacity-50"
              >
                {#each providers as provider}
                  <option
                    value={provider.id}
                    disabled={!isProviderAvailable(provider.id)}
                  >
                    {provider.name}
                  </option>
                {/each}
              </select>
              {#if override.provider !== 'default' && modelsByProvider[override.provider]}
                <select
                  value={override.model}
                  on:change={(e) => updateOverride(agent.id, 'model', e.currentTarget.value)}
                  disabled={disabled}
                  class="flex-1 px-2 py-1 text-xs border border-surface-300 rounded focus:ring-1 focus:ring-gray-900 disabled:opacity-50"
                >
                  {#each modelsByProvider[override.provider] as model}
                    <option value={model}>{model}</option>
                  {/each}
                </select>
              {/if}
            </div>
          </div>
        {/each}
      </div>
    {/if}
  </div>
</div>
