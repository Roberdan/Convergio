<!--
💬 Agent Status Component
Displays agent status indicators (active, waiting, idle, error) and conversation management
-->

<script lang="ts">
  import { agentStatuses, conversationManager } from '$lib/stores/conversationStore';
  import type { AgentStatus } from '$lib/stores/conversationStore';

  export let agentId: string;
  export let agentName: string;
  export let compact = false; // For list view vs detail view

  let status: AgentStatus | null = null;
  
  // Subscribe to agent status
  $: {
    const statusMap = $agentStatuses;
    status = statusMap.get(agentId) || null;
    
    // Initialize if not exists
    if (!status) {
      conversationManager.initializeConversation(agentId, agentName);
      status = statusMap.get(agentId) || null;
    }
  }

  function getStatusColor(statusType: string): string {
    switch (statusType) {
      case 'active':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'waiting':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'idle':
        return 'bg-surface-100 text-surface-600 border-surface-200';
      case 'error':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-surface-100 text-surface-600 border-surface-200';
    }
  }

  function getStatusIcon(statusType: string): string {
    switch (statusType) {
      case 'active':
        return '🟢'; // Active
      case 'waiting':
        return '🟡'; // Waiting for response
      case 'idle':
        return '⚪'; // Idle
      case 'error':
        return '🔴'; // Error
      default:
        return '⚪';
    }
  }

  function getStatusText(statusType: string): string {
    switch (statusType) {
      case 'active':
        return 'Working';
      case 'waiting':
        return 'Thinking...';
      case 'idle':
        return 'Available';
      case 'error':
        return 'Error';
      default:
        return 'Unknown';
    }
  }
</script>

{#if status}
  {#if compact}
    <!-- Compact status for agent list -->
    <div class="flex items-center space-x-1">
      <span class="text-xs">{getStatusIcon(status.status)}</span>
      <span class="text-xs font-medium {getStatusColor(status.status)} px-1.5 py-0.5 rounded-full border">
        {getStatusText(status.status)}
      </span>
    </div>
  {:else}
    <!-- Detailed status for agent detail view -->
    <div class="flex items-center justify-between p-3 bg-surface-50 rounded-lg border">
      <div class="flex items-center space-x-3">
        <div class="text-lg">{getStatusIcon(status.status)}</div>
        <div>
          <div class="text-sm font-medium text-surface-900">
            {getStatusText(status.status)}
          </div>
          <div class="text-xs text-surface-500">
            {status.conversationCount} messages • 
            Last: {status.lastActivity.toLocaleTimeString()}
          </div>
        </div>
      </div>
      
      <!-- Status indicator badge -->
      <div class="px-2 py-1 rounded-full text-xs font-medium border {getStatusColor(status.status)}">
        {status.status.toUpperCase()}
      </div>
    </div>
  {/if}
{:else}
  <!-- Loading state -->
  <div class="flex items-center space-x-1">
    <span class="text-xs">⚪</span>
    <span class="text-xs text-gray-400 px-1.5 py-0.5">Loading...</span>
  </div>
{/if}