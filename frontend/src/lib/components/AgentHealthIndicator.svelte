<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { writable } from 'svelte/store';

  export let agentName: string = '';
  export let showDetails: boolean = false;

  // Health states
  type HealthStatus = 'healthy' | 'degraded' | 'unhealthy' | 'checking';
  
  interface AgentHealth {
    status: HealthStatus;
    tools: {
      web_search: boolean;
      vector_search: boolean;
      database: boolean;
    };
    lastCheck: Date;
    message?: string;
  }

  let health = writable<AgentHealth>({
    status: 'checking',
    tools: {
      web_search: false,
      vector_search: false,
      database: false
    },
    lastCheck: new Date()
  });

  let intervalId: NodeJS.Timeout;

  async function checkHealth() {
    try {
      // Check ecosystem health
      const response = await fetch('http://localhost:9000/api/v1/agents/ecosystem');
      
      if (response.ok) {
        const data = await response.json();
        
  // Optionally filter for a specific agent if name provided (not used internally)
  // const agentData = agentName ? data.agents?.find((a: any) => a.name === agentName) : data;

        // Check tool availability
        const toolsHealthy = {
          web_search: data.tools?.web_search?.configured || false,
          vector_search: data.tools?.vector_search?.available || false,
          database: data.database?.healthy || false
        };

        // Determine overall status
        let status: HealthStatus = 'healthy';
        if (!toolsHealthy.web_search && !toolsHealthy.database) {
          status = 'unhealthy';
        } else if (!toolsHealthy.web_search || !toolsHealthy.vector_search) {
          status = 'degraded';
        }

        health.set({
          status,
          tools: toolsHealthy,
          lastCheck: new Date(),
          message: data.message
        });
      } else {
        health.set({
          status: 'unhealthy',
          tools: {
            web_search: false,
            vector_search: false,
            database: false
          },
          lastCheck: new Date(),
          message: 'Cannot connect to backend'
        });
      }
    } catch (error) {
      health.set({
        status: 'unhealthy',
        tools: {
          web_search: false,
          vector_search: false,
          database: false
        },
        lastCheck: new Date(),
        message: 'Health check failed'
      });
    }
  }

  onMount(() => {
    checkHealth();
    // Check health every 30 seconds
    intervalId = setInterval(checkHealth, 30000);
  });

  onDestroy(() => {
    if (intervalId) {
      clearInterval(intervalId);
    }
  });

  function getStatusColor(status: HealthStatus): string {
    switch(status) {
      case 'healthy': return 'text-green-500';
      case 'degraded': return 'text-yellow-500';
      case 'unhealthy': return 'text-red-500';
      case 'checking': return 'text-surface-500';
      default: return 'text-surface-500';
    }
  }

  function getStatusIcon(status: HealthStatus): string {
    switch(status) {
      case 'healthy': return '✓';
      case 'degraded': return '⚠';
      case 'unhealthy': return '✗';
      case 'checking': return '⟳';
      default: return '?';
    }
  }
</script>

<div class="agent-health-indicator">
  <div class="flex items-center gap-2">
    <span class="status-icon {getStatusColor($health.status)} text-lg">
      {getStatusIcon($health.status)}
    </span>
    
    {#if agentName}
      <span class="agent-name text-sm font-medium">{agentName}</span>
    {/if}
    
    <span class="status-text text-xs {getStatusColor($health.status)}">
      {$health.status}
    </span>
  </div>

  {#if showDetails}
    <div class="health-details mt-2 p-2 bg-surface-50 rounded text-xs">
      <div class="grid grid-cols-3 gap-2">
        <div class="tool-status">
          <span class="block text-surface-600">Web Search</span>
          <span class="{$health.tools.web_search ? 'text-green-500' : 'text-red-500'}">
            {$health.tools.web_search ? '✓' : '✗'}
          </span>
        </div>
        
        <div class="tool-status">
          <span class="block text-surface-600">Vector DB</span>
          <span class="{$health.tools.vector_search ? 'text-green-500' : 'text-red-500'}">
            {$health.tools.vector_search ? '✓' : '✗'}
          </span>
        </div>
        
        <div class="tool-status">
          <span class="block text-surface-600">Database</span>
          <span class="{$health.tools.database ? 'text-green-500' : 'text-red-500'}">
            {$health.tools.database ? '✓' : '✗'}
          </span>
        </div>
      </div>
      
      {#if $health.message}
        <div class="mt-2 text-surface-600">
          {$health.message}
        </div>
      {/if}
      
      <div class="mt-1 text-surface-500">
        Last check: {$health.lastCheck.toLocaleTimeString()}
      </div>
    </div>
  {/if}
</div>

<style>
  .agent-health-indicator {
    @apply inline-block;
  }
  
  .status-icon {
    animation: pulse 2s infinite;
  }
  
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
  }
</style>