<script lang="ts">
  export let activeSection: string = 'overview';
  
  const sections = [
    { id: 'overview', label: 'Overview', icon: 'chart-bar' },
    { id: 'projects', label: 'Projects', icon: 'folder' },
    { id: 'agents', label: 'AI Agents', icon: 'cpu' },
    { id: 'talents', label: 'Team', icon: 'users' },
    { id: 'workflows', label: 'Workflows', icon: 'lightning-bolt' },
    { id: 'costs', label: 'Costs', icon: 'currency-dollar' },
    { id: 'feedback', label: 'Feedback', icon: 'chat' },
    { id: 'analytics', label: 'Analytics', icon: 'trending-up' }
  ];

  function getSvgPath(icon: string): string {
    const paths = {
      'chart-bar': 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z',
      'folder': 'M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z',
      'cpu': 'M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z',
      'users': 'M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a4 4 0 11-8 0 4 4 0 018 0z',
      'lightning-bolt': 'M13 10V3L4 14h7v7l9-11h-7z',
      'currency-dollar': 'M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1',
      'chat': 'M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z',
      'trending-up': 'M13 7h8m0 0v8m0-8l-8 8-4-4-6 6'
    };
    return paths[icon as keyof typeof paths] || paths['chart-bar'];
  }

  function handleSectionChange(sectionId: string) {
    activeSection = sectionId;
  }
</script>

<div class="bg-white border-2 border-surface-200 rounded-xl mb-6 shadow-lg">
  <div class="px-6 py-4 border-b-2 border-surface-200">
    <h2 class="text-lg font-bold text-surface-900">Dashboard</h2>
  </div>
  <div class="p-6">
    <nav class="flex flex-wrap gap-2">
      {#each sections as section}
        <button
          on:click={() => handleSectionChange(section.id)}
          class="flex items-center space-x-2 px-4 py-3 rounded-lg text-sm font-bold transition-all duration-200 {
            activeSection === section.id
              ? 'bg-blue-600 text-white border-2 border-blue-700 shadow-md'
              : 'text-surface-700 hover:text-blue-600 hover:bg-blue-50 border-2 border-surface-300 bg-white'
          }"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d={getSvgPath(section.icon)} />
          </svg>
          <span>{section.label}</span>
        </button>
      {/each}
    </nav>
  </div>
</div>