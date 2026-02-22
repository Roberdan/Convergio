<script lang="ts">
  import '../app.css';
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import { onMount } from 'svelte';
  import { initializeTheme } from '$lib/stores/themeStore';
  import { authStore } from '$lib/stores/auth';

  interface Props {
    children?: import('svelte').Snippet;
  }

  let { children }: Props = $props();

  function getPageTitle(routeId: string | null): string {
    if (routeId?.includes('dashboard')) return 'Dashboard';
    if (routeId?.includes('agents')) return 'AI Agents';
    if (routeId?.includes('talents')) return 'Talents';
    if (routeId?.includes('vector')) return 'Vector Search';
    if (routeId?.includes('analytics')) return 'Analytics';
    if (routeId?.includes('costs')) return 'Cost Management';
    if (routeId === '/') return 'Home';
    return 'Convergio';
  }

  onMount(async () => {
    initializeTheme();
    await authStore.initialize();
  });

  $effect(() => {
    if (
      $authStore.initialized &&
      !$authStore.loading &&
      $authStore.isAuthenticated &&
      $page.url.pathname === '/'
    ) {
      goto('/dashboard');
    }
  });

  let pageTitle = $derived(getPageTitle($page.route.id));
</script>

<svelte:head>
  <title>{pageTitle} - Convergio</title>
  <meta name="description" content="Convergio - Unified AI-Native Enterprise Platform" />
</svelte:head>

<div class="min-h-screen bg-surface-900 text-surface-900 transition-colors duration-300">
  {@render children?.()}
</div>

<style>
  :global(html) {
    font-family: 'Inter', sans-serif;
  }

  :global(body) {
    margin: 0;
    padding: 0;
  }
</style>
