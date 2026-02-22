<script lang="ts">
  import { onMount } from 'svelte';

  type ManagedAgent = {
    id: string;
    name: string;
    ownerEmail: string;
    status: 'active' | 'disabled';
  };

  let agents = $state<ManagedAgent[]>([]);
  let loading = $state(false);
  let error = $state('');

  async function fetchAgents() {
    loading = true;
    error = '';
    try {
      const response = await fetch('/api/v1/admin/agents', {
        credentials: 'include'
      });
      if (!response.ok) throw new Error('Unable to load agents');
      agents = await response.json();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Failed to load agents';
    } finally {
      loading = false;
    }
  }

  async function toggleAgent(agent: ManagedAgent) {
    const nextStatus = agent.status === 'active' ? 'disabled' : 'active';
    try {
      const response = await fetch(`/api/v1/admin/agents/${agent.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ status: nextStatus })
      });
      if (!response.ok) throw new Error('Failed to update agent');
      await fetchAgents();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Failed to update agent';
    }
  }

  onMount(fetchAgents);
</script>

<div class="space-y-4">
  <header>
    <h2 class="text-2xl font-semibold text-slate-900">Agent Management</h2>
    <p class="text-sm text-slate-600">Enable, disable, and monitor workspace agents.</p>
  </header>

  {#if error}
    <p class="rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</p>
  {/if}

  {#if loading}
    <p class="text-sm text-slate-500">Loading agents...</p>
  {:else}
    <div class="overflow-x-auto rounded-lg border border-slate-200">
      <table class="min-w-full divide-y divide-slate-200 text-sm">
        <thead class="bg-slate-50">
          <tr>
            <th class="px-3 py-2 text-left font-medium text-slate-600">Agent</th>
            <th class="px-3 py-2 text-left font-medium text-slate-600">Owner</th>
            <th class="px-3 py-2 text-left font-medium text-slate-600">Status</th>
            <th class="px-3 py-2 text-left font-medium text-slate-600">Action</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-200 bg-white">
          {#each agents as agent}
            <tr>
              <td class="px-3 py-2 text-slate-800">{agent.name}</td>
              <td class="px-3 py-2 text-slate-700">{agent.ownerEmail}</td>
              <td class="px-3 py-2 text-slate-700">{agent.status}</td>
              <td class="px-3 py-2">
                <button
                  class="rounded-md px-3 py-1 text-xs font-semibold text-white {agent.status === 'active' ? 'bg-red-600' : 'bg-green-600'}"
                  onclick={() => toggleAgent(agent)}
                >
                  {agent.status === 'active' ? 'Disable' : 'Enable'}
                </button>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</div>
