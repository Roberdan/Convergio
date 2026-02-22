<script lang="ts">
  import { onMount } from 'svelte';

  type Tier = {
    id: string;
    name: string;
    priceMonthly: number;
    maxAgents: number;
  };

  let tiers = $state<Tier[]>([]);
  let loading = $state(false);
  let error = $state('');

  async function fetchTiers() {
    loading = true;
    error = '';
    try {
      const response = await fetch('/api/v1/admin/tiers', {
        credentials: 'include'
      });
      if (!response.ok) throw new Error('Unable to load tiers');
      tiers = await response.json();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Failed to load tiers';
    } finally {
      loading = false;
    }
  }

  async function saveTier(tier: Tier) {
    try {
      const response = await fetch(`/api/v1/admin/tiers/${tier.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(tier)
      });
      if (!response.ok) throw new Error('Failed to save tier');
    } catch (err) {
      error = err instanceof Error ? err.message : 'Failed to save tier';
    }
  }

  onMount(fetchTiers);
</script>

<div class="space-y-4">
  <header>
    <h2 class="text-2xl font-semibold text-slate-900">Tier Configuration</h2>
    <p class="text-sm text-slate-600">Manage pricing and limits for each subscription tier.</p>
  </header>

  {#if error}
    <p class="rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</p>
  {/if}

  {#if loading}
    <p class="text-sm text-slate-500">Loading tiers...</p>
  {:else}
    <div class="space-y-3">
      {#each tiers as tier}
        <article class="rounded-lg border border-slate-200 p-4">
          <div class="grid gap-3 md:grid-cols-4 md:items-end">
            <label class="text-sm">
              <span class="mb-1 block text-slate-600">Name</span>
              <input class="w-full rounded-md border border-slate-300 px-3 py-2" bind:value={tier.name} />
            </label>
            <label class="text-sm">
              <span class="mb-1 block text-slate-600">Monthly Price</span>
              <input class="w-full rounded-md border border-slate-300 px-3 py-2" type="number" bind:value={tier.priceMonthly} />
            </label>
            <label class="text-sm">
              <span class="mb-1 block text-slate-600">Max Agents</span>
              <input class="w-full rounded-md border border-slate-300 px-3 py-2" type="number" bind:value={tier.maxAgents} />
            </label>
            <button class="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white" onclick={() => saveTier(tier)}>
              Save
            </button>
          </div>
        </article>
      {/each}
    </div>
  {/if}
</div>
