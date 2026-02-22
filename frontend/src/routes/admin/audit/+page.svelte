<script lang="ts">
  import { onMount } from 'svelte';

  type AuditEvent = {
    id: string;
    actor: string;
    action: string;
    createdAt: string;
    details?: string;
  };

  let events = $state<AuditEvent[]>([]);
  let actorFilter = $state('');
  let actionFilter = $state('');
  let loading = $state(false);
  let error = $state('');

  async function fetchAuditLog() {
    loading = true;
    error = '';
    try {
      const params = new URLSearchParams();
      if (actorFilter) params.set('actor', actorFilter);
      if (actionFilter) params.set('action', actionFilter);

      const response = await fetch(`/api/v1/admin/audit-log?${params.toString()}`, {
        credentials: 'include'
      });
      if (!response.ok) throw new Error('Unable to load audit log');
      events = await response.json();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Failed to load audit log';
    } finally {
      loading = false;
    }
  }

  onMount(fetchAuditLog);
</script>

<div class="space-y-4">
  <header>
    <h2 class="text-2xl font-semibold text-slate-900">Audit Log</h2>
    <p class="text-sm text-slate-600">Review administrative events and filter by actor/action.</p>
  </header>

  <div class="grid gap-2 md:grid-cols-3">
    <input class="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Actor" bind:value={actorFilter} />
    <input class="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Action" bind:value={actionFilter} />
    <button class="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white" onclick={fetchAuditLog}>Apply Filters</button>
  </div>

  {#if error}
    <p class="rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</p>
  {/if}

  {#if loading}
    <p class="text-sm text-slate-500">Loading events...</p>
  {:else}
    <div class="overflow-x-auto rounded-lg border border-slate-200">
      <table class="min-w-full divide-y divide-slate-200 text-sm">
        <thead class="bg-slate-50">
          <tr>
            <th class="px-3 py-2 text-left font-medium text-slate-600">When</th>
            <th class="px-3 py-2 text-left font-medium text-slate-600">Actor</th>
            <th class="px-3 py-2 text-left font-medium text-slate-600">Action</th>
            <th class="px-3 py-2 text-left font-medium text-slate-600">Details</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-200 bg-white">
          {#each events as event}
            <tr>
              <td class="px-3 py-2 text-slate-800">{new Date(event.createdAt).toLocaleString()}</td>
              <td class="px-3 py-2 text-slate-700">{event.actor}</td>
              <td class="px-3 py-2 text-slate-700">{event.action}</td>
              <td class="px-3 py-2 text-slate-600">{event.details ?? '-'}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</div>
