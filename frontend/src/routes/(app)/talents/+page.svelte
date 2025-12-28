<script lang="ts">
  import { onMount } from 'svelte';
  import { talentsService, type Talent } from '$lib/services/talentsService';

  let talents: Talent[] = [];
  let filteredTalents: Talent[] = [];
  let loading = true;
  let error: string | null = null;
  let searchQuery = '';
  let filterStatus: 'all' | 'active' | 'inactive' = 'all';
  let filterRole: 'all' | 'admin' | 'member' = 'all';
  let sortBy: 'name' | 'email' | 'created' = 'name';
  let sortOrder: 'asc' | 'desc' = 'asc';

  function formatDate(dateString?: string): string {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  }

  async function loadTalents() {
    try {
      loading = true;
      error = null;
      talents = await talentsService.getTalents();
      applyFilters();
    } catch {
      // Silent failure
      error = 'Failed to load talents data';
    } finally {
      loading = false;
    }
  }

  function applyFilters() {
    let result = [...talents];

    // Search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      result = result.filter(t =>
        t.full_name?.toLowerCase().includes(query) ||
        t.email?.toLowerCase().includes(query) ||
        t.username?.toLowerCase().includes(query)
      );
    }

    // Status filter
    if (filterStatus === 'active') {
      result = result.filter(t => t.is_active);
    } else if (filterStatus === 'inactive') {
      result = result.filter(t => !t.is_active);
    }

    // Role filter
    if (filterRole === 'admin') {
      result = result.filter(t => t.is_admin);
    } else if (filterRole === 'member') {
      result = result.filter(t => !t.is_admin);
    }

    // Sort
    result.sort((a, b) => {
      let comparison = 0;
      switch (sortBy) {
        case 'name':
          comparison = (a.full_name || a.username).localeCompare(b.full_name || b.username);
          break;
        case 'email':
          comparison = a.email.localeCompare(b.email);
          break;
        case 'created':
          comparison = new Date(a.created_at || 0).getTime() - new Date(b.created_at || 0).getTime();
          break;
      }
      return sortOrder === 'asc' ? comparison : -comparison;
    });

    filteredTalents = result;
  }

  // Reactively apply filters when any filter changes
  $: if (talents.length >= 0) {
    searchQuery, filterStatus, filterRole, sortBy, sortOrder;
    applyFilters();
  }

  $: activeTalents = talents.filter(t => t.is_active);
  $: adminTalents = talents.filter(t => t.is_admin);

  onMount(loadTalents);
</script>

<svelte:head>
  <title>Team & Talents - Convergio</title>
</svelte:head>

<div class="min-h-screen bg-surface-100">
  <!-- Header -->
  <div class="bg-white border-b border-surface-200 px-6 py-4">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-bold text-surface-900">Team & Talents</h1>
        <p class="text-sm text-surface-600 mt-1">Manage your organization's team members</p>
      </div>
      <button
        on:click={loadTalents}
        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        <span>Refresh</span>
      </button>
    </div>
  </div>

  <div class="p-6 space-y-6">
    <!-- Stats Cards -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <div class="bg-white border border-surface-200 rounded-xl p-4">
        <div class="flex items-center space-x-3">
          <div class="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
            <svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
          </div>
          <div>
            <p class="text-2xl font-bold text-surface-900">{talents.length}</p>
            <p class="text-sm text-surface-600">Total Team</p>
          </div>
        </div>
      </div>

      <div class="bg-white border border-surface-200 rounded-xl p-4">
        <div class="flex items-center space-x-3">
          <div class="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
            <svg class="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <p class="text-2xl font-bold text-surface-900">{activeTalents.length}</p>
            <p class="text-sm text-surface-600">Active</p>
          </div>
        </div>
      </div>

      <div class="bg-white border border-surface-200 rounded-xl p-4">
        <div class="flex items-center space-x-3">
          <div class="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
            <svg class="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
          </div>
          <div>
            <p class="text-2xl font-bold text-surface-900">{adminTalents.length}</p>
            <p class="text-sm text-surface-600">Administrators</p>
          </div>
        </div>
      </div>

      <div class="bg-white border border-surface-200 rounded-xl p-4">
        <div class="flex items-center space-x-3">
          <div class="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
            <svg class="w-5 h-5 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <p class="text-2xl font-bold text-surface-900">{talents.length - activeTalents.length}</p>
            <p class="text-sm text-surface-600">Inactive</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Filters & Search -->
    <div class="bg-white border border-surface-200 rounded-xl p-4">
      <div class="flex flex-wrap gap-4 items-center">
        <!-- Search -->
        <div class="flex-1 min-w-[200px]">
          <div class="relative">
            <svg class="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-surface-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              type="text"
              bind:value={searchQuery}
              placeholder="Search by name, email, or username..."
              class="w-full pl-10 pr-4 py-2 border border-surface-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>

        <!-- Status Filter -->
        <select
          bind:value={filterStatus}
          class="px-4 py-2 border border-surface-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="all">All Status</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
        </select>

        <!-- Role Filter -->
        <select
          bind:value={filterRole}
          class="px-4 py-2 border border-surface-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="all">All Roles</option>
          <option value="admin">Administrators</option>
          <option value="member">Members</option>
        </select>

        <!-- Sort -->
        <select
          bind:value={sortBy}
          class="px-4 py-2 border border-surface-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="name">Sort by Name</option>
          <option value="email">Sort by Email</option>
          <option value="created">Sort by Created</option>
        </select>

        <button
          on:click={() => sortOrder = sortOrder === 'asc' ? 'desc' : 'asc'}
          class="p-2 border border-surface-200 rounded-lg hover:bg-surface-50 transition-colors"
          title={sortOrder === 'asc' ? 'Ascending' : 'Descending'}
          aria-label="Toggle sort order: {sortOrder === 'asc' ? 'Ascending' : 'Descending'}"
        >
          <svg class="w-5 h-5 text-surface-600 transition-transform {sortOrder === 'desc' ? 'rotate-180' : ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4h13M3 8h9m-9 4h6m4 0l4-4m0 0l4 4m-4-4v12" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Talents List -->
    <div class="bg-white border border-surface-200 rounded-xl overflow-hidden">
      {#if loading}
        <div class="p-6 space-y-4">
          {#each Array(5) as _}
            <div class="flex items-center space-x-4 animate-pulse">
              <div class="w-12 h-12 bg-surface-200 rounded-full"></div>
              <div class="flex-1">
                <div class="w-48 h-4 bg-surface-200 rounded mb-2"></div>
                <div class="w-64 h-3 bg-surface-200 rounded"></div>
              </div>
              <div class="w-20 h-6 bg-surface-200 rounded-full"></div>
            </div>
          {/each}
        </div>
      {:else if error}
        <div class="p-12 text-center">
          <div class="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg class="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <p class="text-red-600 font-medium">{error}</p>
          <button
            on:click={loadTalents}
            class="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Try Again
          </button>
        </div>
      {:else if filteredTalents.length === 0}
        <div class="p-12 text-center">
          <div class="w-16 h-16 bg-surface-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg class="w-8 h-8 text-surface-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
          </div>
          <p class="text-surface-600">No team members found</p>
          {#if searchQuery || filterStatus !== 'all' || filterRole !== 'all'}
            <p class="text-sm text-surface-500 mt-1">Try adjusting your filters</p>
          {/if}
        </div>
      {:else}
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead class="bg-surface-50 border-b border-surface-200">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-semibold text-surface-600 uppercase tracking-wider">Member</th>
                <th class="px-6 py-3 text-left text-xs font-semibold text-surface-600 uppercase tracking-wider">Email</th>
                <th class="px-6 py-3 text-left text-xs font-semibold text-surface-600 uppercase tracking-wider">Role</th>
                <th class="px-6 py-3 text-left text-xs font-semibold text-surface-600 uppercase tracking-wider">Status</th>
                <th class="px-6 py-3 text-left text-xs font-semibold text-surface-600 uppercase tracking-wider">Joined</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-surface-100">
              {#each filteredTalents as talent}
                <tr class="hover:bg-surface-50 transition-colors">
                  <td class="px-6 py-4 whitespace-nowrap">
                    <div class="flex items-center space-x-3">
                      <div class="w-10 h-10 bg-gradient-to-br from-blue-400 to-purple-500 rounded-full flex items-center justify-center flex-shrink-0">
                        <span class="text-white text-sm font-semibold">
                          {talent.full_name ? talent.full_name.charAt(0).toUpperCase() : talent.username.charAt(0).toUpperCase()}
                        </span>
                      </div>
                      <div>
                        <p class="text-sm font-medium text-surface-900">{talent.full_name || talent.username}</p>
                        <p class="text-xs text-surface-500">@{talent.username}</p>
                      </div>
                    </div>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap">
                    <p class="text-sm text-surface-600">{talent.email}</p>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap">
                    {#if talent.is_admin}
                      <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                        <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                        </svg>
                        Administrator
                      </span>
                    {:else}
                      <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                        </svg>
                        Member
                      </span>
                    {/if}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap">
                    {#if talent.is_active}
                      <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        <span class="w-1.5 h-1.5 bg-green-500 rounded-full mr-1.5"></span>
                        Active
                      </span>
                    {:else}
                      <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-surface-100 text-surface-600">
                        <span class="w-1.5 h-1.5 bg-surface-400 rounded-full mr-1.5"></span>
                        Inactive
                      </span>
                    {/if}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap">
                    <p class="text-sm text-surface-600">{formatDate(talent.created_at)}</p>
                  </td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>

        <!-- Results Summary -->
        <div class="px-6 py-3 bg-surface-50 border-t border-surface-200">
          <p class="text-sm text-surface-600">
            Showing <span class="font-medium">{filteredTalents.length}</span> of <span class="font-medium">{talents.length}</span> team members
          </p>
        </div>
      {/if}
    </div>
  </div>
</div>
