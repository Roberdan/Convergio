<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import AliAssistant from '$lib/components/AliAssistant.svelte';

  let healthStatus: any = null;
  let loading = true;
  const APP_VERSION: string = (typeof __APP_VERSION__ !== 'undefined' ? __APP_VERSION__ : (typeof __VERSION__ !== 'undefined' ? __VERSION__ : '0.0.0')) as unknown as string;

  onMount(async () => {
    try {
      // Add 3 second timeout for health check
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 3000);
      
      const response = await fetch('http://localhost:9000/health', {
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      
      if (response.ok) {
        healthStatus = await response.json();
      } else {
        healthStatus = { status: "unknown" };
      }
    } catch (error) {
      healthStatus = { status: "offline" };
    }
    loading = false;
  });
</script>

<svelte:head>
  <title>platform.Convergio.io - AI-Native Enterprise Platform</title>
</svelte:head>

<!-- Clean Landing Page - Light Theme -->
<div class="min-h-screen bg-white font-mono">
  <!-- Simple Top Navigation -->
  <div class="bg-surface-50 border-b border-surface-200">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between items-center h-16">
        <!-- Logo & Title -->
        <div class="flex items-center">
          <span class="text-surface-900 font-medium tracking-tight">platform.Convergio.io</span>
        </div>

        <!-- Status & Version -->
        <div class="flex items-center space-x-4 text-xs">
          <div class="flex items-center space-x-2">
            {#if loading}
              <div class="h-1.5 w-1.5 bg-gray-400 rounded-full animate-pulse"></div>
              <span class="text-surface-500">Checking...</span>
            {:else if healthStatus?.status === "healthy" || healthStatus?.status === "ok"}
              <div class="h-1.5 w-1.5 bg-green-500 rounded-full"></div>
              <span class="text-surface-600">Online</span>
            {:else}
              <div class="h-1.5 w-1.5 bg-yellow-500 rounded-full"></div>
              <span class="text-surface-500">Starting...</span>
            {/if}
          </div>
          <span class="text-xs text-surface-500 font-mono" title="Version: {APP_VERSION} Build: {healthStatus?.build || 'unknown'}">
            v{APP_VERSION}
          </span>
        </div>
      </div>
    </div>
  </div>

  <!-- Hero Section - Business Focused -->
  <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
    <!-- Main Hero with Logo -->
    <div class="text-center mb-12">
      <img src="/convergio_logo.png" alt="Platform Convergio" class="h-32 w-auto mx-auto mb-6" />
      <h1 class="text-3xl lg:text-4xl font-bold text-surface-900 mb-6 leading-tight">
        Convergio.io is not software that you <em class="text-blue-600">use</em>,<br/>
        but a team that you <em class="text-blue-600">direct</em>.
      </h1>
      <p class="text-xl text-surface-600 mb-8 max-w-3xl mx-auto leading-relaxed">
        Imagine having a super-intelligent command center with 40+ AI specialists. You are the CEO, they are your best team.
      </p>
      <div class="flex flex-col sm:flex-row gap-4 justify-center">
        <button
          on:click={() => goto('/dashboard')}
          class="flex items-center justify-center px-8 py-4 bg-blue-600 text-white text-lg font-semibold rounded-xl hover:bg-blue-700 transition-all transform hover:scale-[1.02] shadow-lg"
        >
          <img src="/convergio_icons/dashboard.svg" alt="" class="mr-3 h-5 w-5" />
          Start Your Command Center
        </button>
        <button
          on:click={() => goto('/agents')}
          class="flex items-center justify-center px-8 py-4 border-2 border-blue-600 text-blue-600 text-lg font-semibold rounded-xl hover:bg-blue-50 transition-all"
        >
          <img src="/convergio_icons/users.svg" alt="" class="mr-3 h-5 w-5" />
          Meet Your AI Team
        </button>
      </div>
    </div>

    <!-- Business Value Cards -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
      <!-- AI Agents -->
      <div class="bg-gradient-to-br from-blue-50 to-indigo-100 rounded-2xl p-8 text-center border border-blue-200/50">
        <div class="w-16 h-16 bg-blue-500 rounded-2xl flex items-center justify-center mx-auto mb-4">
          <img src="/convergio_icons/users.svg" alt="" class="h-8 w-8" />
        </div>
        <h3 class="text-xl font-bold text-surface-900 mb-3">40+ AI Specialists</h3>
        <p class="text-surface-600 mb-4 text-sm leading-relaxed">
          From CFOs to CTOs, from Marketing to HR - your complete C-suite team, available instantly.
        </p>
        <div class="text-xs text-blue-700 font-medium">
          Powered by <a href="https://microsoft.github.io/autogen/stable/index.html" target="_blank" rel="noopener noreferrer" class="underline hover:text-blue-900">Microsoft AutoGen</a>
        </div>
      </div>

      <!-- No-Code -->
      <div class="bg-gradient-to-br from-emerald-50 to-green-100 rounded-2xl p-8 text-center border border-emerald-200/50">
        <div class="w-16 h-16 bg-emerald-500 rounded-2xl flex items-center justify-center mx-auto mb-4">
          <img src="/convergio_icons/heart.svg" alt="" class="h-8 w-8" />
        </div>
        <h3 class="text-xl font-bold text-surface-900 mb-3">Zero Technical Skills</h3>
        <p class="text-surface-600 mb-4 text-sm leading-relaxed">
          Focus on strategy, not syntax. Communicate in plain English - your AI team handles the execution.
        </p>
        <div class="text-xs text-emerald-700 font-medium">
          Business-First Approach
        </div>
      </div>

      <!-- Enterprise -->
      <div class="bg-gradient-to-br from-purple-50 to-violet-100 rounded-2xl p-8 text-center border border-purple-200/50">
        <div class="w-16 h-16 bg-purple-500 rounded-2xl flex items-center justify-center mx-auto mb-4">
          <img src="/convergio_icons/dashboard.svg" alt="" class="h-8 w-8" />
        </div>
        <h3 class="text-xl font-bold text-surface-900 mb-3">Enterprise Ready</h3>
        <p class="text-surface-600 mb-4 text-sm leading-relaxed">
          Scale from startup to Fortune 500. Your AI team grows with your ambitions.
        </p>
        <div class="text-xs text-purple-700 font-medium">
          24/7 • 2s Response • 99.9% Uptime
        </div>
      </div>
    </div>
  </div>

  <!-- Agentic Manifesto Section - More Prominent -->
  <div class="bg-gradient-to-b from-gray-50 to-white py-16">
    <div class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="text-center mb-16">
        <div class="inline-flex items-center justify-center w-16 h-16 bg-blue-100 rounded-full mb-6">
          <img src="/convergio_icons/heart.svg" alt="" class="h-8 w-8" />
        </div>
        <h2 class="text-3xl lg:text-4xl font-bold text-surface-900 mb-4">
          The Agentic Manifesto
        </h2>
        <p class="text-xl text-blue-600 font-medium italic mb-2">
          Human purpose. AI momentum.
        </p>
        <p class="text-sm text-surface-500">Milano — 23 June 2025</p>
      </div>

      <div class="grid md:grid-cols-2 gap-10">
        <!-- What we believe -->
        <div class="bg-white border border-blue-100 rounded-xl p-8 shadow-sm">
          <h3 class="text-lg font-bold text-surface-900 mb-6 flex items-center">
            <div class="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center mr-3">
              <img src="/convergio_icons/heart.svg" alt="" class="h-4 w-4" />
            </div>
            What we believe
          </h3>
          <ol class="space-y-4 text-sm text-surface-700">
            <li class="flex items-start">
              <span class="inline-flex items-center justify-center w-6 h-6 bg-blue-100 text-blue-600 text-sm font-bold rounded-full mr-3 mt-0.5 flex-shrink-0">1</span>
              <span><strong>Intent is human, momentum is agent.</strong></span>
            </li>
            <li class="flex items-start">
              <span class="inline-flex items-center justify-center w-6 h-6 bg-blue-100 text-blue-600 text-sm font-bold rounded-full mr-3 mt-0.5 flex-shrink-0">2</span>
              <span><strong>Impact must reach every mind and body.</strong></span>
            </li>
            <li class="flex items-start">
              <span class="inline-flex items-center justify-center w-6 h-6 bg-blue-100 text-blue-600 text-sm font-bold rounded-full mr-3 mt-0.5 flex-shrink-0">3</span>
              <span><strong>Trust grows from transparent provenance.</strong></span>
            </li>
            <li class="flex items-start">
              <span class="inline-flex items-center justify-center w-6 h-6 bg-blue-100 text-blue-600 text-sm font-bold rounded-full mr-3 mt-0.5 flex-shrink-0">4</span>
              <span><strong>Progress is judged by outcomes, not output.</strong></span>
            </li>
          </ol>
        </div>

        <!-- How we act -->
        <div class="bg-white border border-blue-100 rounded-xl p-8 shadow-sm">
          <h3 class="text-lg font-bold text-surface-900 mb-6 flex items-center">
            <div class="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center mr-3">
              <img src="/convergio_icons/launch_mission.svg" alt="" class="h-4 w-4" />
            </div>
            How we act
          </h3>
          <ol class="space-y-4 text-sm text-surface-700">
            <li class="flex items-start">
              <span class="inline-flex items-center justify-center w-6 h-6 bg-blue-100 text-blue-600 text-sm font-bold rounded-full mr-3 mt-0.5 flex-shrink-0">1</span>
              <span><strong>Humans stay accountable for decisions and effects.</strong></span>
            </li>
            <li class="flex items-start">
              <span class="inline-flex items-center justify-center w-6 h-6 bg-blue-100 text-blue-600 text-sm font-bold rounded-full mr-3 mt-0.5 flex-shrink-0">2</span>
              <span><strong>Agents amplify capability, never identity.</strong></span>
            </li>
            <li class="flex items-start">
              <span class="inline-flex items-center justify-center w-6 h-6 bg-blue-100 text-blue-600 text-sm font-bold rounded-full mr-3 mt-0.5 flex-shrink-0">3</span>
              <span><strong>We design from the edge first: disability, language, connectivity.</strong></span>
            </li>
            <li class="flex items-start">
              <span class="inline-flex items-center justify-center w-6 h-6 bg-blue-100 text-blue-600 text-sm font-bold rounded-full mr-3 mt-0.5 flex-shrink-0">4</span>
              <span><strong>Safety rails precede scale.</strong></span>
            </li>
            <li class="flex items-start">
              <span class="inline-flex items-center justify-center w-6 h-6 bg-blue-100 text-blue-600 text-sm font-bold rounded-full mr-3 mt-0.5 flex-shrink-0">5</span>
              <span><strong>Learn in small loops, ship value early.</strong></span>
            </li>
            <li class="flex items-start">
              <span class="inline-flex items-center justify-center w-6 h-6 bg-blue-100 text-blue-600 text-sm font-bold rounded-full mr-3 mt-0.5 flex-shrink-0">6</span>
              <span><strong>Bias is a bug—we detect, test, and fix continuously.</strong></span>
            </li>
          </ol>
        </div>
      </div>

      <!-- Signature -->
      <div class="text-center mt-8 p-4 bg-surface-100 rounded">
        <p class="text-xs text-surface-600 italic">
          <em>Signed in Milano, 23 June 2025 — Roberto · Claude 3 · OpenAI o3. Designed with ❤️ for Mario</em>
        </p>
      </div>
    </div>
  </div>
  
  <!-- Ali Assistant (always present) -->
  <AliAssistant />
</div>