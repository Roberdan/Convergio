<script lang="ts">
  import { onMount } from 'svelte';
  import { talentsService, type Talent } from '$lib/services/talentsService';

  let talents: Talent[] = [];
  let loading = true;
  let error: string | null = null;

  function formatDate(dateString?: string): string {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString();
  }

  async function loadTalents() {
    try {
      loading = true;
      error = null;
      talents = await talentsService.getTalents();
    } catch (err) {
      console.error('Failed to load talents:', err);
      error = 'Failed to load talents data';
    } finally {
      loading = false;
    }
  }

  onMount(loadTalents);

  $: activeTalents = talents.filter(t => t.is_active);
  $: adminTalents = talents.filter(t => t.is_admin);
</script>

<div class="bg-white border border-surface-200 rounded">
  <div class="px-4 py-3 border-b border-surface-200">
    <div class="flex items-center justify-between">
      <h3 class="text-sm font-medium text-surface-900">Team & Talents</h3>
      <button 
        on:click={loadTalents}
        class="text-xs text-surface-500 hover:text-surface-600 flex items-center space-x-1"
      >
        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        <span>Refresh</span>
      </button>
    </div>
  </div>

  <div class="p-4">
    {#if loading}
      <div class="animate-pulse space-y-4">
        <div class="grid grid-cols-3 gap-4 mb-6">
          {#each Array(3) as _}
            <div class="bg-surface-100 p-4 rounded">
              <div class="w-16 h-6 bg-surface-200 rounded mb-1"></div>
              <div class="w-12 h-4 bg-surface-200 rounded"></div>
            </div>
          {/each}
        </div>
        {#each Array(5) as _}
          <div class="flex items-center space-x-3 p-3 border border-surface-200 rounded">
            <div class="w-8 h-8 bg-surface-200 rounded-full"></div>
            <div class="flex-1">
              <div class="w-32 h-4 bg-surface-200 rounded mb-1"></div>
              <div class="w-48 h-3 bg-surface-200 rounded"></div>
            </div>
            <div class="w-16 h-4 bg-surface-200 rounded"></div>
          </div>
        {/each}
      </div>
    {:else if error}
      <div class="text-center text-red-600">
        <p>{error}</p>
        <button 
          on:click={loadTalents}
          class="mt-2 text-sm text-blue-600 hover:text-blue-800"
        >
          Try again
        </button>
      </div>
    {:else}
      <!-- Summary Stats -->
      <div class="grid grid-cols-3 gap-4 mb-6">
        <div class="bg-blue-50 p-4 rounded">
          <p class="text-2xl font-bold text-blue-600">{talents.length}</p>
          <p class="text-sm text-blue-600">Total Talents</p>
        </div>
        <div class="bg-green-50 p-4 rounded">
          <p class="text-2xl font-bold text-green-600">{activeTalents.length}</p>
          <p class="text-sm text-green-600">Active</p>
        </div>
        <div class="bg-purple-50 p-4 rounded">
          <p class="text-2xl font-bold text-purple-600">{adminTalents.length}</p>
          <p class="text-sm text-purple-600">Admins</p>
        </div>
      </div>

      <!-- Talents List -->
      {#if talents.length > 0}
        <div class="space-y-3">
          <h4 class="text-xs font-medium text-surface-600">Team Members</h4>
          {#each talents.slice(0, 10) as talent}
            <div class="flex items-center justify-between p-3 border border-surface-200 rounded hover:bg-surface-50">
              <div class="flex items-center space-x-3">
                <div class="w-8 h-8 bg-gradient-to-br from-blue-400 to-purple-500 rounded-full flex items-center justify-center">
                  <span class="text-white text-sm font-semibold">
                    {talent.full_name ? talent.full_name.charAt(0).toUpperCase() : talent.username.charAt(0).toUpperCase()}
                  </span>
                </div>
                <div>
                  <p class="text-sm font-medium text-surface-900">{talent.full_name || talent.username}</p>
                  <p class="text-xs text-surface-500">{talent.email}</p>
                </div>
              </div>
              <div class="flex items-center space-x-2">
                {#if talent.is_admin}
                  <span class="text-xs px-2 py-1 bg-purple-100 text-purple-700 rounded-full">Admin</span>
                {/if}
                <span class="text-xs px-2 py-1 rounded-full {talent.is_active ? 'bg-green-100 text-green-700' : 'bg-surface-100 text-surface-500'}">
                  {talent.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>
            </div>
          {/each}
          
          {#if talents.length > 10}
            <div class="text-center">
              <p class="text-xs text-surface-500">... and {talents.length - 10} more</p>
            </div>
          {/if}
        </div>
      {:else}
        <div class="text-center text-surface-500">
          <p class="text-xs">No talents available</p>
        </div>
      {/if}
    {/if}
  </div>
</div>