<script lang="ts">
  import { onMount } from 'svelte';

  type BillingUsage = {
    tier: string;
    agents_used: number;
    agents_limit: number;
    conversations_used: number;
    conversations_limit: number;
  };

  let usage = $state<BillingUsage>({
    tier: 'free',
    agents_used: 0,
    agents_limit: 0,
    conversations_used: 0,
    conversations_limit: 0
  });

  let loadingUsage = $state(true);
  let loadingCheckout = $state(false);
  let loadingPortal = $state(false);
  let errorMessage = $state('');

  onMount(async () => {
    await loadUsage();
  });

  async function loadUsage() {
    loadingUsage = true;
    errorMessage = '';

    try {
      const response = await fetch('/api/v1/billing/usage', {
        credentials: 'include'
      });

      if (!response.ok) {
        throw new Error('Failed to load billing usage');
      }

      usage = await response.json();
    } catch {
      errorMessage = 'Unable to load billing usage right now. Please try again.';
    } finally {
      loadingUsage = false;
    }
  }

  async function openStripeCheckout() {
    loadingCheckout = true;
    errorMessage = '';

    try {
      const response = await fetch('/api/v1/billing/checkout-session', {
        method: 'POST',
        credentials: 'include'
      });

      if (!response.ok) {
        throw new Error('Failed to create checkout session');
      }

      const data = await response.json() as { url?: string };
      if (!data.url) {
        throw new Error('Missing checkout url');
      }

      window.location.href = data.url;
    } catch {
      errorMessage = 'Unable to open upgrade flow. Please try again.';
    } finally {
      loadingCheckout = false;
    }
  }

  async function openStripePortal() {
    loadingPortal = true;
    errorMessage = '';

    try {
      const response = await fetch('/api/v1/billing/portal-session', {
        method: 'POST',
        credentials: 'include'
      });

      if (!response.ok) {
        throw new Error('Failed to create portal session');
      }

      const data = await response.json() as { url?: string };
      if (!data.url) {
        throw new Error('Missing portal url');
      }

      window.location.href = data.url;
    } catch {
      errorMessage = 'Unable to open subscription management. Please try again.';
    } finally {
      loadingPortal = false;
    }
  }

  function percent(used: number, limit: number) {
    if (limit <= 0) {
      return 0;
    }

    return Math.min(100, Math.round((used / limit) * 100));
  }
</script>

<svelte:head>
  <title>Billing - platform.Convergio.io</title>
</svelte:head>

<div class="space-y-6">
  <header>
    <h1 class="text-lg font-medium text-surface-900">Billing</h1>
    <p class="mt-1 text-xs text-surface-500">
      Manage your plan, monitor usage, and continue in stripe for subscription actions.
    </p>
  </header>

  {#if errorMessage}
    <div class="rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700" role="alert">
      {errorMessage}
    </div>
  {/if}

  <section class="rounded border border-surface-200 bg-white p-4">
    <h2 class="text-sm font-semibold text-surface-900">Current Tier</h2>

    {#if loadingUsage}
      <p class="mt-2 text-sm text-surface-500">Loading usage...</p>
    {:else}
      <p class="mt-2 text-sm text-surface-700 capitalize">{usage.tier}</p>
    {/if}
  </section>

  <section class="space-y-4 rounded border border-surface-200 bg-white p-4">
    <h2 class="text-sm font-semibold text-surface-900">Usage</h2>

    <div class="space-y-2">
      <div class="flex items-center justify-between text-xs text-surface-700">
        <span>Agents</span>
        <span>{usage.agents_used} / {usage.agents_limit}</span>
      </div>
      <div class="h-2 w-full overflow-hidden rounded-full bg-surface-100">
        <div class="h-full bg-blue-600" style={`width: ${percent(usage.agents_used, usage.agents_limit)}%`}></div>
      </div>
    </div>

    <div class="space-y-2">
      <div class="flex items-center justify-between text-xs text-surface-700">
        <span>Conversations</span>
        <span>{usage.conversations_used} / {usage.conversations_limit}</span>
      </div>
      <div class="h-2 w-full overflow-hidden rounded-full bg-surface-100">
        <div class="h-full bg-emerald-600" style={`width: ${percent(usage.conversations_used, usage.conversations_limit)}%`}></div>
      </div>
    </div>
  </section>

  <section class="flex flex-wrap gap-3">
    <button
      type="button"
      class="rounded bg-gray-900 px-4 py-2 text-xs font-medium text-white transition-colors hover:bg-gray-800 disabled:cursor-not-allowed disabled:bg-surface-300"
      onclick={openStripeCheckout}
      disabled={loadingCheckout || loadingPortal}
    >
      {#if loadingCheckout}
        Opening upgrade...
      {:else}
        Upgrade
      {/if}
    </button>

    <button
      type="button"
      class="rounded border border-surface-300 bg-white px-4 py-2 text-xs font-medium text-surface-700 transition-colors hover:bg-surface-50 disabled:cursor-not-allowed disabled:bg-surface-100"
      onclick={openStripePortal}
      disabled={loadingCheckout || loadingPortal}
    >
      {#if loadingPortal}
        Opening portal...
      {:else}
        Manage Subscription
      {/if}
    </button>
  </section>
</div>
