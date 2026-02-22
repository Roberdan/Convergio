<script lang="ts">
  import { onMount } from 'svelte';

  type AdminUser = {
    id: string;
    email: string;
    role: string;
    tier: string;
    status?: string;
  };

  let users = $state<AdminUser[]>([]);
  let query = $state('');
  let loading = $state(false);
  let error = $state('');
  let savingUserId = $state<string | null>(null);

  let filteredUsers = $derived.by(() => {
    const term = query.trim().toLowerCase();
    if (!term) return users;
    return users.filter((user) => user.email.toLowerCase().includes(term) || user.id.includes(term));
  });

  async function fetchUsers() {
    loading = true;
    error = '';
    try {
      const response = await fetch('/api/v1/admin/users', {
        credentials: 'include'
      });
      if (!response.ok) throw new Error('Unable to load users');
      users = await response.json();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Unknown error';
    } finally {
      loading = false;
    }
  }

  async function updateUser(userId: string, payload: Record<string, string>) {
    savingUserId = userId;
    try {
      const response = await fetch(`/api/v1/admin/users/${userId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(payload)
      });
      if (!response.ok) throw new Error('Failed to update user');
      await fetchUsers();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Update failed';
    } finally {
      savingUserId = null;
    }
  }

  onMount(fetchUsers);
</script>

<div class="space-y-4">
  <header>
    <h2 class="text-2xl font-semibold text-slate-900">Users</h2>
    <p class="text-sm text-slate-600">Search users, change tiers, and manage roles.</p>
  </header>

  <div class="flex gap-2">
    <input
      class="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
      placeholder="Search by email or id"
      bind:value={query}
    />
    <button class="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white" onclick={fetchUsers}>
      Refresh
    </button>
  </div>

  {#if error}
    <p class="rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</p>
  {/if}

  {#if loading}
    <p class="text-sm text-slate-500">Loading users...</p>
  {:else}
    <div class="overflow-x-auto rounded-lg border border-slate-200">
      <table class="min-w-full divide-y divide-slate-200 text-sm">
        <thead class="bg-slate-50">
          <tr>
            <th class="px-3 py-2 text-left font-medium text-slate-600">Email</th>
            <th class="px-3 py-2 text-left font-medium text-slate-600">Role</th>
            <th class="px-3 py-2 text-left font-medium text-slate-600">Tier</th>
            <th class="px-3 py-2 text-left font-medium text-slate-600">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-200 bg-white">
          {#each filteredUsers as user}
            <tr>
              <td class="px-3 py-2 text-slate-800">{user.email}</td>
              <td class="px-3 py-2">
                <select
                  class="rounded-md border border-slate-300 px-2 py-1"
                  value={user.role}
                  onchange={(event) => {
                    const value = (event.currentTarget as HTMLSelectElement).value;
                    updateUser(user.id, { role: value });
                  }}
                >
                  <option value="member">member</option>
                  <option value="admin">admin</option>
                </select>
              </td>
              <td class="px-3 py-2">
                <select
                  class="rounded-md border border-slate-300 px-2 py-1"
                  value={user.tier}
                  onchange={(event) => {
                    const value = (event.currentTarget as HTMLSelectElement).value;
                    updateUser(user.id, { tier: value });
                  }}
                >
                  <option value="free">free</option>
                  <option value="starter">starter</option>
                  <option value="pro">pro</option>
                  <option value="enterprise">enterprise</option>
                </select>
              </td>
              <td class="px-3 py-2 text-slate-500">{savingUserId === user.id ? 'Saving...' : 'Ready'}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</div>
