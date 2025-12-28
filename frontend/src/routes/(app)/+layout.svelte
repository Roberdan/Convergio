<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import AliAssistant from '$lib/components/AliAssistant.svelte';
  import CostDisplay from '$lib/components/CostDisplay.svelte';
  import ApiStatusDropdown from '$lib/components/ApiStatusDropdown.svelte';
  import { SkipToContent } from '$lib/components/accessibility';
  import { accessibilityStore } from '$lib/stores/accessibilityStore';
  import '$lib/styles/unified-design-system.css';
  import '$lib/styles/accessibility.css';
  
  // MVP navigation items (simplified for initial release)
  const navItems = [
    { href: '/agents', label: 'AI Team', iconPath: '/convergio_icons/users.svg' },
    { href: '/workforce', label: 'Workforce', iconPath: '/convergio_icons/talent_directory.svg' },
    { href: '/pm', label: 'Projects', iconPath: '/convergio_icons/projects.svg' },
    { href: '/dashboard', label: 'Analytics', iconPath: '/convergio_icons/analytics.svg' },
    { href: '/settings', label: 'Settings', iconPath: '/convergio_icons/settings.svg' }
  ];
  
  // 🚧 ROADMAP: Advanced features removed for MVP simplification
  // Future Phase 2 navigation items (Q2-Q3 2025):
  // - CEO Dashboard (Executive business intelligence)
  // - Agent Management (Advanced CRUD operations)  
  // - Swarm Coordination (Multi-agent orchestration)
  
  let healthStatus: any = null;
  const APP_VERSION: string = (typeof __APP_VERSION__ !== 'undefined' ? __APP_VERSION__ : (typeof __VERSION__ !== 'undefined' ? __VERSION__ : '0.0.0')) as unknown as string;
  
  onMount(async () => {
    // Initialize accessibility settings
    accessibilityStore.init();

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 3000);

      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:9000';
      const response = await fetch(`${apiUrl}/health`, {
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (response.ok) {
        healthStatus = await response.json();
      }
    } catch (error) {
      // No fallback - show real error state
      healthStatus = null;
      console.error('Failed to get health status:', error);
    }
  });
  
  // SEMPLICE: controlla se il path corrente inizia con l'href del menu
  function isActive(href: string): boolean {
    const currentPath = $page.url.pathname;
    
    // Per la home page
    if (href === '/') {
      return currentPath === '/';
    }
    
    // Per le altre pagine: controllo esatto del path
    return currentPath === href;
  }
</script>

<!-- Skip to Content Links (WS5-C2) -->
<SkipToContent />

<!-- Clean Professional Layout -->
<div class="min-h-screen bg-surface-50 font-sans text-base">
  <!-- Clean Professional Top Navigation -->
  <div class="bg-surface-50 border-b-2 border-surface-300 shadow-sm">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between items-center h-16">
        <!-- Logo & Title -->
        <div class="flex items-center space-x-4">
          <button on:click={() => goto('/')} class="flex items-center space-x-3 hover:opacity-75 transition-all">
            <div class="h-10 w-10 bg-blue-600 rounded-lg flex items-center justify-center text-white font-bold text-lg">
              C
            </div>
            <div class="flex flex-col">
              <span class="text-lg font-bold text-surface-900 leading-tight">Convergio</span>
              <span class="text-sm text-surface-600 leading-none">AI Agent Platform</span>
            </div>
          </button>
        </div>

        <!-- Clean Navigation -->
        <nav id="navigation" class="hidden md:flex items-center space-x-2" aria-label="Main navigation">
          {#each navItems as item}
            <a
              href={item.href}
              data-sveltekit-prefetch
              aria-current={isActive(item.href) ? 'page' : null}
              class="flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-bold transition-all duration-200 {isActive(item.href)
                ? 'bg-blue-600 text-white shadow-md'
                : 'text-surface-800 hover:text-blue-600 hover:bg-blue-50'}"
            >
              <img src={item.iconPath} alt="" class="h-4 w-4" />
              <span>{item.label}</span>
            </a>
          {/each}
        </nav>

        <!-- Status & Cost Indicators -->
        <div class="flex items-center space-x-3">
          <!-- Cost Display -->
          <CostDisplay />

          <!-- API Status Dropdown -->
          <ApiStatusDropdown />
        </div>
      </div>
    </div>
  </div>
  
  <!-- Content Area -->
  <main id="main-content" class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6" tabindex="-1">
    <slot />
  </main>
  
  <!-- Ali Assistant (always present) -->
  <AliAssistant />
</div>