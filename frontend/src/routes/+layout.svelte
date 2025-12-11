<script lang="ts">
  import '../app.css';
  import { page } from '$app/stores';
  import { onMount } from 'svelte';
  import { initializeTheme } from '$lib/stores/themeStore';

  // Dynamic page title based on route
  $: pageTitle = getPageTitle($page.route.id);

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

  // Inizializza sistema temi
  onMount(() => {
    initializeTheme();
  });
</script>

<svelte:head>
  <title>{pageTitle} - Convergio</title>
  <meta name="description" content="Convergio - Unified AI-Native Enterprise Platform (No Auth Required)" />
</svelte:head>

<!-- Root Layout - Super Clean, No Auth -->
<div class="min-h-screen bg-surface-900 text-surface-900  transition-colors duration-300">
  <slot />
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