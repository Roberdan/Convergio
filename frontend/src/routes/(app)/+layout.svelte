<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import AliAssistant from '$lib/components/AliAssistant.svelte';
  
  // Simple navigation items
  const navItems = [
    { href: '/dashboard', label: 'Dashboard', iconPath: '/convergio_icons/dashboard.svg' },
    { href: '/agents', label: 'AI Team', iconPath: '/convergio_icons/users.svg' },
    { href: '/settings', label: 'Settings', iconPath: '/convergio_icons/settings.svg' }
  ];
  
  $: currentPath = $page.url.pathname;
  
  let healthStatus: any = null;
  
  onMount(async () => {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 3000);
      
      const response = await fetch('http://localhost:9000/health', {
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      
      if (response.ok) {
        healthStatus = await response.json();
      }
    } catch (error) {
      // Use fallback version
      healthStatus = { app_version: '0.3', build_number: '2' };
    }
  });
  
  function isActive(href: string): boolean {
    return currentPath === href;
  }
</script>

<!-- Clean Layout inspired by Reflex Dashboard -->
<div class="min-h-screen bg-gray-50 font-mono text-sm">
  <!-- Simple Top Navigation -->
  <div class="bg-white border-b border-gray-200">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between items-center h-14">
        <!-- Logo & Title -->
        <div class="flex items-center space-x-4">
          <button on:click={() => goto('/')} class="flex items-center space-x-3 hover:opacity-75">
            <img src="/convergio_logo.png" alt="Platform Convergio" class="h-8 w-auto" />
            <span class="text-gray-900 font-medium tracking-tight">platform.Convergio.io</span>
          </button>
          <div class="hidden md:block h-4 w-px bg-gray-300"></div>
          <div class="hidden md:block text-xs text-gray-500 tracking-wide">
            v{healthStatus?.app_version || '0.3'}.{healthStatus?.build_number || '2'} • {currentPath.replace('/', '') || 'home'}
          </div>
        </div>
        
        <!-- Simple Navigation -->
        <nav class="hidden md:flex items-center space-x-6">
          {#each navItems as item}
            <button
              on:click={() => goto(item.href)}
              class="flex items-center space-x-2 px-3 py-1.5 rounded-md text-xs font-medium transition-colors {isActive(item.href) 
                ? 'bg-gray-100 text-gray-900' 
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'}"
            >
              <img src={item.iconPath} alt="" class="h-3 w-3" />
              <span>{item.label}</span>
            </button>
          {/each}
        </nav>
        
        <!-- Status Indicator -->
        <div class="flex items-center space-x-2 text-xs text-green-600">
          <div class="h-1.5 w-1.5 bg-green-500 rounded-full"></div>
          <span class="hidden sm:inline">Online</span>
        </div>
      </div>
    </div>
  </div>
  
  <!-- Content Area -->
  <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
    <slot />
  </main>
  
  <!-- Ali Assistant (always present) -->
  <AliAssistant />
</div>