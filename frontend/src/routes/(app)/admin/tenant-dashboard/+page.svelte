<script lang="ts">
  import { onMount } from 'svelte';
  import { writable } from 'svelte/store';
  
  interface Tenant {
    id: string;
    name: string;
    status: 'active' | 'suspended' | 'trial' | 'cancelled';
    subscription_plan: 'free' | 'professional' | 'enterprise';
    billing_period: 'monthly' | 'yearly';
    created_at: string;
    trial_ends_at?: string;
    current_users: number;
    max_users: number;
    current_projects: number;
    max_projects: number;
    current_workflows: number;
    max_workflows: number;
    current_api_calls: number;
    max_api_calls: number;
    current_storage_gb: number;
    max_storage_gb: number;
    current_ai_tokens: number;
    max_ai_tokens: number;
    monthly_cost: number;
    usage_charges: number;
    total_cost: number;
    stripe_customer_id?: string;
    stripe_subscription_id?: string;
  }
  
  interface UsageMetric {
    date: string;
    api_calls: number;
    ai_tokens: number;
    storage_gb: number;
    cost: number;
  }
  
  let tenants = writable<Tenant[]>([]);
  let selectedTenant = writable<Tenant | null>(null);
  let usageMetrics = writable<UsageMetric[]>([]);
  let loading = false;
  let showCreateModal = false;
  let showEditModal = false;
  let searchQuery = '';
  let filterStatus = 'all';
  let filterPlan = 'all';
  
  // Form data for creating/editing tenant
  let formData = {
    name: '',
    status: 'trial' as Tenant['status'],
    subscription_plan: 'free' as Tenant['subscription_plan'],
    billing_period: 'monthly' as Tenant['billing_period'],
    max_users: 5,
    max_projects: 10,
    max_workflows: 50,
    max_api_calls: 10000,
    max_storage_gb: 10,
    max_ai_tokens: 100000
  };
  
  onMount(async () => {
    await loadTenants();
  });
  
  async function loadTenants() {
    loading = true;
    try {
      const response = await fetch('/api/v1/admin/tenants');
      if (response.ok) {
        const data = await response.json();
        tenants.set(data.tenants);
      }
    } catch (error) {
      console.error('Failed to load tenants:', error);
    } finally {
      loading = false;
    }
  }
  
  async function loadTenantUsage(tenantId: string) {
    try {
      const response = await fetch(`/api/v1/admin/tenants/${tenantId}/usage`);
      if (response.ok) {
        const data = await response.json();
        usageMetrics.set(data.metrics);
      }
    } catch (error) {
      console.error('Failed to load tenant usage:', error);
    }
  }
  
  async function createTenant() {
    try {
      const response = await fetch('/api/v1/admin/tenants', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      
      if (response.ok) {
        await loadTenants();
        showCreateModal = false;
        resetForm();
      }
    } catch (error) {
      console.error('Failed to create tenant:', error);
    }
  }
  
  async function updateTenant() {
    if (!$selectedTenant) return;
    
    try {
      const response = await fetch(`/api/v1/admin/tenants/${$selectedTenant.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      
      if (response.ok) {
        await loadTenants();
        showEditModal = false;
        resetForm();
      }
    } catch (error) {
      console.error('Failed to update tenant:', error);
    }
  }
  
  async function suspendTenant(tenantId: string) {
    if (!confirm('Are you sure you want to suspend this tenant?')) return;
    
    try {
      const response = await fetch(`/api/v1/admin/tenants/${tenantId}/suspend`, {
        method: 'POST'
      });
      
      if (response.ok) {
        await loadTenants();
      }
    } catch (error) {
      console.error('Failed to suspend tenant:', error);
    }
  }
  
  async function activateTenant(tenantId: string) {
    try {
      const response = await fetch(`/api/v1/admin/tenants/${tenantId}/activate`, {
        method: 'POST'
      });
      
      if (response.ok) {
        await loadTenants();
      }
    } catch (error) {
      console.error('Failed to activate tenant:', error);
    }
  }
  
  async function exportTenantData(tenantId: string, format: 'csv' | 'json') {
    window.open(`/api/v1/export/tenants/${tenantId}/usage?format=${format}`, '_blank');
  }
  
  function resetForm() {
    formData = {
      name: '',
      status: 'trial',
      subscription_plan: 'free',
      billing_period: 'monthly',
      max_users: 5,
      max_projects: 10,
      max_workflows: 50,
      max_api_calls: 10000,
      max_storage_gb: 10,
      max_ai_tokens: 100000
    };
  }
  
  function selectTenant(tenant: Tenant) {
    selectedTenant.set(tenant);
    loadTenantUsage(tenant.id);
  }
  
  function openEditModal(tenant: Tenant) {
    selectedTenant.set(tenant);
    formData = {
      name: tenant.name,
      status: tenant.status,
      subscription_plan: tenant.subscription_plan,
      billing_period: tenant.billing_period,
      max_users: tenant.max_users,
      max_projects: tenant.max_projects,
      max_workflows: tenant.max_workflows,
      max_api_calls: tenant.max_api_calls,
      max_storage_gb: tenant.max_storage_gb,
      max_ai_tokens: tenant.max_ai_tokens
    };
    showEditModal = true;
  }
  
  function getStatusColor(status: Tenant['status']) {
    switch (status) {
      case 'active': return 'text-green-600 bg-green-50';
      case 'trial': return 'text-blue-600 bg-blue-50';
      case 'suspended': return 'text-red-600 bg-red-50';
      case 'cancelled': return 'text-surface-600 bg-surface-50';
      default: return 'text-surface-600 bg-surface-50';
    }
  }
  
  function getPlanColor(plan: Tenant['subscription_plan']) {
    switch (plan) {
      case 'enterprise': return 'text-purple-600 bg-purple-50';
      case 'professional': return 'text-indigo-600 bg-indigo-50';
      case 'free': return 'text-surface-600 bg-surface-50';
      default: return 'text-surface-600 bg-surface-50';
    }
  }
  
  function getUsagePercentage(current: number, max: number): number {
    return max > 0 ? (current / max) * 100 : 0;
  }
  
  function getUsageColor(percentage: number): string {
    if (percentage >= 90) return 'bg-red-500';
    if (percentage >= 75) return 'bg-yellow-500';
    return 'bg-green-500';
  }
  
  $: filteredTenants = $tenants.filter(tenant => {
    const matchesSearch = tenant.name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = filterStatus === 'all' || tenant.status === filterStatus;
    const matchesPlan = filterPlan === 'all' || tenant.subscription_plan === filterPlan;
    return matchesSearch && matchesStatus && matchesPlan;
  });
  
  $: totalRevenue = $tenants.reduce((sum, tenant) => sum + tenant.total_cost, 0);
  $: activeTenantsCount = $tenants.filter(t => t.status === 'active').length;
  $: trialTenantsCount = $tenants.filter(t => t.status === 'trial').length;
</script>

<div class="p-6">
  <!-- Header -->
  <div class="mb-6">
    <h1 class="text-2xl font-bold text-surface-900">Tenant Dashboard</h1>
    <p class="text-surface-600">Manage multi-tenant subscriptions and usage</p>
  </div>
  
  <!-- Summary Cards -->
  <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
    <div class="bg-white rounded-lg shadow p-4">
      <div class="text-sm text-surface-600">Total Tenants</div>
      <div class="text-2xl font-bold">{$tenants.length}</div>
    </div>
    
    <div class="bg-white rounded-lg shadow p-4">
      <div class="text-sm text-surface-600">Active Tenants</div>
      <div class="text-2xl font-bold text-green-600">{activeTenantsCount}</div>
    </div>
    
    <div class="bg-white rounded-lg shadow p-4">
      <div class="text-sm text-surface-600">Trial Tenants</div>
      <div class="text-2xl font-bold text-blue-600">{trialTenantsCount}</div>
    </div>
    
    <div class="bg-white rounded-lg shadow p-4">
      <div class="text-sm text-surface-600">Monthly Revenue</div>
      <div class="text-2xl font-bold text-purple-600">${totalRevenue.toFixed(2)}</div>
    </div>
  </div>
  
  <!-- Filters and Actions -->
  <div class="bg-white rounded-lg shadow p-4 mb-6">
    <div class="flex flex-wrap gap-4 items-center">
      <input
        type="text"
        placeholder="Search tenants..."
        bind:value={searchQuery}
        class="px-3 py-2 border rounded-lg flex-1 min-w-[200px]"
      />
      
      <select
        bind:value={filterStatus}
        class="px-3 py-2 border rounded-lg"
      >
        <option value="all">All Status</option>
        <option value="active">Active</option>
        <option value="trial">Trial</option>
        <option value="suspended">Suspended</option>
        <option value="cancelled">Cancelled</option>
      </select>
      
      <select
        bind:value={filterPlan}
        class="px-3 py-2 border rounded-lg"
      >
        <option value="all">All Plans</option>
        <option value="free">Free</option>
        <option value="professional">Professional</option>
        <option value="enterprise">Enterprise</option>
      </select>
      
      <button
        on:click={() => showCreateModal = true}
        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
      >
        Create Tenant
      </button>
    </div>
  </div>
  
  <!-- Tenants Table -->
  <div class="bg-white rounded-lg shadow overflow-hidden">
    {#if loading}
      <div class="p-8 text-center text-surface-500">Loading tenants...</div>
    {:else if filteredTenants.length === 0}
      <div class="p-8 text-center text-surface-500">No tenants found</div>
    {:else}
      <table class="w-full">
        <thead class="bg-surface-50">
          <tr>
            <th class="px-4 py-3 text-left text-xs font-medium text-surface-500 uppercase">Tenant</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-surface-500 uppercase">Status</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-surface-500 uppercase">Plan</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-surface-500 uppercase">Usage</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-surface-500 uppercase">Cost</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-surface-500 uppercase">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200">
          {#each filteredTenants as tenant}
            <tr class="hover:bg-surface-50 cursor-pointer" on:click={() => selectTenant(tenant)}>
              <td class="px-4 py-3">
                <div>
                  <div class="font-medium text-surface-900">{tenant.name}</div>
                  <div class="text-sm text-surface-500">ID: {tenant.id}</div>
                </div>
              </td>
              
              <td class="px-4 py-3">
                <span class="px-2 py-1 text-xs font-medium rounded-full {getStatusColor(tenant.status)}">
                  {tenant.status}
                </span>
              </td>
              
              <td class="px-4 py-3">
                <span class="px-2 py-1 text-xs font-medium rounded-full {getPlanColor(tenant.subscription_plan)}">
                  {tenant.subscription_plan}
                </span>
              </td>
              
              <td class="px-4 py-3">
                <div class="space-y-1">
                  <div class="flex items-center gap-2">
                    <span class="text-xs text-surface-500">Users:</span>
                    <div class="flex-1 bg-surface-200 rounded-full h-2 max-w-[100px]">
                      <div 
                        class="h-2 rounded-full {getUsageColor(getUsagePercentage(tenant.current_users, tenant.max_users))}"
                        style="width: {getUsagePercentage(tenant.current_users, tenant.max_users)}%"
                      ></div>
                    </div>
                    <span class="text-xs">{tenant.current_users}/{tenant.max_users}</span>
                  </div>
                  
                  <div class="flex items-center gap-2">
                    <span class="text-xs text-surface-500">API:</span>
                    <div class="flex-1 bg-surface-200 rounded-full h-2 max-w-[100px]">
                      <div 
                        class="h-2 rounded-full {getUsageColor(getUsagePercentage(tenant.current_api_calls, tenant.max_api_calls))}"
                        style="width: {getUsagePercentage(tenant.current_api_calls, tenant.max_api_calls)}%"
                      ></div>
                    </div>
                    <span class="text-xs">{tenant.current_api_calls}/{tenant.max_api_calls}</span>
                  </div>
                </div>
              </td>
              
              <td class="px-4 py-3">
                <div>
                  <div class="font-medium">${tenant.total_cost.toFixed(2)}</div>
                  <div class="text-xs text-surface-500">{tenant.billing_period}</div>
                </div>
              </td>
              
              <td class="px-4 py-3">
                <div class="flex gap-2">
                  <button
                    on:click|stopPropagation={() => openEditModal(tenant)}
                    class="text-blue-600 hover:text-blue-800"
                    aria-label="Edit tenant"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                  </button>
                  
                  {#if tenant.status === 'active'}
                    <button
                      on:click|stopPropagation={() => suspendTenant(tenant.id)}
                      class="text-red-600 hover:text-red-800"
                      aria-label="Suspend tenant"
                    >
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
                      </svg>
                    </button>
                  {:else if tenant.status === 'suspended'}
                    <button
                      on:click|stopPropagation={() => activateTenant(tenant.id)}
                      class="text-green-600 hover:text-green-800"
                      aria-label="Activate tenant"
                    >
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </button>
                  {/if}
                  
                  <button
                    on:click|stopPropagation={() => exportTenantData(tenant.id, 'csv')}
                    class="text-surface-600 hover:text-surface-800"
                    aria-label="Export CSV"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10" />
                    </svg>
                  </button>
                </div>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    {/if}
  </div>
  
  <!-- Selected Tenant Details -->
  {#if $selectedTenant}
    <div class="mt-6 bg-white rounded-lg shadow p-6">
      <h2 class="text-lg font-semibold mb-4">Tenant Details: {$selectedTenant.name}</h2>
      
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <!-- Usage Metrics -->
        <div>
          <h3 class="text-sm font-medium text-surface-600 mb-3">Usage Metrics</h3>
          <div class="space-y-3">
            <div>
              <div class="flex justify-between text-sm mb-1">
                <span>Users</span>
                <span>{$selectedTenant.current_users} / {$selectedTenant.max_users}</span>
              </div>
              <div class="w-full bg-surface-200 rounded-full h-2">
                <div 
                  class="h-2 rounded-full {getUsageColor(getUsagePercentage($selectedTenant.current_users, $selectedTenant.max_users))}"
                  style="width: {getUsagePercentage($selectedTenant.current_users, $selectedTenant.max_users)}%"
                ></div>
              </div>
            </div>
            
            <div>
              <div class="flex justify-between text-sm mb-1">
                <span>Projects</span>
                <span>{$selectedTenant.current_projects} / {$selectedTenant.max_projects}</span>
              </div>
              <div class="w-full bg-surface-200 rounded-full h-2">
                <div 
                  class="h-2 rounded-full {getUsageColor(getUsagePercentage($selectedTenant.current_projects, $selectedTenant.max_projects))}"
                  style="width: {getUsagePercentage($selectedTenant.current_projects, $selectedTenant.max_projects)}%"
                ></div>
              </div>
            </div>
            
            <div>
              <div class="flex justify-between text-sm mb-1">
                <span>AI Tokens</span>
                <span>{$selectedTenant.current_ai_tokens.toLocaleString()} / {$selectedTenant.max_ai_tokens.toLocaleString()}</span>
              </div>
              <div class="w-full bg-surface-200 rounded-full h-2">
                <div 
                  class="h-2 rounded-full {getUsageColor(getUsagePercentage($selectedTenant.current_ai_tokens, $selectedTenant.max_ai_tokens))}"
                  style="width: {getUsagePercentage($selectedTenant.current_ai_tokens, $selectedTenant.max_ai_tokens)}%"
                ></div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Billing Information -->
        <div>
          <h3 class="text-sm font-medium text-surface-600 mb-3">Billing Information</h3>
          <div class="space-y-2">
            <div class="flex justify-between text-sm">
              <span class="text-surface-600">Monthly Base Cost:</span>
              <span class="font-medium">${$selectedTenant.monthly_cost.toFixed(2)}</span>
            </div>
            <div class="flex justify-between text-sm">
              <span class="text-surface-600">Usage Charges:</span>
              <span class="font-medium">${$selectedTenant.usage_charges.toFixed(2)}</span>
            </div>
            <div class="flex justify-between text-sm pt-2 border-t">
              <span class="text-surface-900 font-medium">Total Cost:</span>
              <span class="font-bold text-lg">${$selectedTenant.total_cost.toFixed(2)}</span>
            </div>
          </div>
          
          {#if $selectedTenant.stripe_customer_id}
            <div class="mt-4">
              <a 
                href="https://dashboard.stripe.com/customers/{$selectedTenant.stripe_customer_id}"
                target="_blank"
                class="text-blue-600 hover:text-blue-800 text-sm"
              >
                View in Stripe →
              </a>
            </div>
          {/if}
        </div>
      </div>
      
      <!-- Usage History Chart -->
      {#if $usageMetrics.length > 0}
        <div class="mt-6">
          <h3 class="text-sm font-medium text-surface-600 mb-3">Usage History (Last 30 Days)</h3>
          <div class="border rounded-lg p-4">
            <!-- Simple usage chart visualization -->
            <div class="space-y-2">
              {#each $usageMetrics.slice(-7) as metric}
                <div class="flex items-center gap-4 text-sm">
                  <span class="w-24 text-surface-600">{new Date(metric.date).toLocaleDateString()}</span>
                  <div class="flex-1 flex items-center gap-2">
                    <span class="text-xs">API:</span>
                    <div class="flex-1 bg-surface-200 rounded h-4 relative">
                      <div 
                        class="absolute inset-y-0 left-0 bg-blue-500 rounded"
                        style="width: {Math.min(100, (metric.api_calls / $selectedTenant.max_api_calls) * 100)}%"
                      ></div>
                      <span class="absolute inset-0 flex items-center justify-center text-xs">
                        {metric.api_calls.toLocaleString()}
                      </span>
                    </div>
                  </div>
                  <span class="text-surface-600 font-medium">${metric.cost.toFixed(2)}</span>
                </div>
              {/each}
            </div>
          </div>
        </div>
      {/if}
    </div>
  {/if}
  
  <!-- Create/Edit Modal -->
  {#if showCreateModal || showEditModal}
    <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg p-6 max-w-md w-full">
        <h2 class="text-lg font-semibold mb-4">
          {showCreateModal ? 'Create New Tenant' : 'Edit Tenant'}
        </h2>
        
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-surface-600 mb-1">
              Tenant Name
            </label>
            <input
              type="text"
              bind:value={formData.name}
              class="w-full px-3 py-2 border rounded-lg"
              placeholder="Enter tenant name"
            />
          </div>
          
          <div>
            <label class="block text-sm font-medium text-surface-600 mb-1">
              Status
            </label>
            <select bind:value={formData.status} class="w-full px-3 py-2 border rounded-lg">
              <option value="trial">Trial</option>
              <option value="active">Active</option>
              <option value="suspended">Suspended</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-surface-600 mb-1">
              Subscription Plan
            </label>
            <select bind:value={formData.subscription_plan} class="w-full px-3 py-2 border rounded-lg">
              <option value="free">Free</option>
              <option value="professional">Professional</option>
              <option value="enterprise">Enterprise</option>
            </select>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-surface-600 mb-1">
              Billing Period
            </label>
            <select bind:value={formData.billing_period} class="w-full px-3 py-2 border rounded-lg">
              <option value="monthly">Monthly</option>
              <option value="yearly">Yearly</option>
            </select>
          </div>
          
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-surface-600 mb-1">
                Max Users
              </label>
              <input
                type="number"
                bind:value={formData.max_users}
                class="w-full px-3 py-2 border rounded-lg"
              />
            </div>
            
            <div>
              <label class="block text-sm font-medium text-surface-600 mb-1">
                Max Projects
              </label>
              <input
                type="number"
                bind:value={formData.max_projects}
                class="w-full px-3 py-2 border rounded-lg"
              />
            </div>
          </div>
          
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-surface-600 mb-1">
                Max API Calls
              </label>
              <input
                type="number"
                bind:value={formData.max_api_calls}
                class="w-full px-3 py-2 border rounded-lg"
              />
            </div>
            
            <div>
              <label class="block text-sm font-medium text-surface-600 mb-1">
                Max AI Tokens
              </label>
              <input
                type="number"
                bind:value={formData.max_ai_tokens}
                class="w-full px-3 py-2 border rounded-lg"
              />
            </div>
          </div>
        </div>
        
        <div class="flex justify-end gap-3 mt-6">
          <button
            on:click={() => {
              showCreateModal = false;
              showEditModal = false;
              resetForm();
            }}
            class="px-4 py-2 text-surface-600 border rounded-lg hover:bg-surface-50"
          >
            Cancel
          </button>
          
          <button
            on:click={showCreateModal ? createTenant : updateTenant}
            class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            {showCreateModal ? 'Create' : 'Update'}
          </button>
        </div>
      </div>
    </div>
  {/if}
</div>