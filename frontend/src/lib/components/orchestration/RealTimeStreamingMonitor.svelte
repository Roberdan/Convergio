<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { writable } from 'svelte/store';
  import { Card, Badge, Button } from '$lib/components/ui';
  import { slide, fade } from 'svelte/transition';
  
  export let orchestrationId: string = '';
  export let websocketConnection: WebSocket | null = null;
  export let realTimeMetrics: any = {};
  
  interface StreamingUpdate {
    id: string;
    type: string;
    timestamp: string;
    data: any;
    agent?: string;
    priority: 'low' | 'medium' | 'high';
  }
  
  interface AgentActivity {
    agent_name: string;
    status: 'online' | 'offline' | 'busy';
    current_task: string;
    last_activity: string;
    response_time: number;
    message_count: number;
  }
  
  let realtimeUpdates = writable<StreamingUpdate[]>([]);
  let agentActivities = writable<AgentActivity[]>([]);
  let systemStatus = writable({
    connected: false,
    latency: 0,
    messages_received: 0,
    last_heartbeat: null
  });
  
  let selectedFilter = 'all';
  let autoScroll = true;
  let maxUpdates = 100;
  let connectionQuality = 'good';
  let streamingMetrics = {
    messages_per_minute: 0,
    active_conversations: 0,
    bandwidth_usage: 0,
    error_rate: 0
  };
  
  const updateTypes = [
    { id: 'all', label: 'All Updates', icon: '📡' },
    { id: 'orchestration_update', label: 'Orchestration', icon: '🎯' },
    { id: 'agent_conversation', label: 'Conversations', icon: '💬' },
    { id: 'metrics', label: 'Metrics', icon: '📊' },
    { id: 'stage_transition', label: 'Stages', icon: '🛤️' },
    { id: 'cost_update', label: 'Cost', icon: '💰' }
  ];
  
  let heartbeatInterval: any;
  let metricsInterval: any;
  let scrollContainer: HTMLElement;
  
  onMount(() => {
    initializeRealTimeMonitoring();
    startHeartbeat();
    startMetricsCollection();
    setupMockData(); // For development
  });
  
  onDestroy(() => {
    if (heartbeatInterval) clearInterval(heartbeatInterval);
    if (metricsInterval) clearInterval(metricsInterval);
  });
  
  function initializeRealTimeMonitoring() {
    if (websocketConnection) {
      setupWebSocketListeners();
    } else {
      // Fallback: poll for updates
      setupPollingFallback();
    }
    
    systemStatus.update(status => ({
      ...status,
      connected: !!websocketConnection
    }));
  }
  
  function setupWebSocketListeners() {
    if (!websocketConnection) return;
    
    const originalOnMessage = websocketConnection.onmessage;
    websocketConnection.onmessage = (event) => {
      try {
        const update = JSON.parse(event.data);
        handleStreamingUpdate(update);
        
        systemStatus.update(status => ({
          ...status,
          messages_received: status.messages_received + 1,
          last_heartbeat: new Date().toISOString()
        }));
        
        // Call original handler if it exists
        if (originalOnMessage) {
          originalOnMessage.call(websocketConnection, event);
        }
      } catch (error) {
        console.error('Error parsing streaming update:', error);
      }
    };
    
    websocketConnection.onopen = () => {
      systemStatus.update(status => ({ ...status, connected: true }));
      connectionQuality = 'good';
    };
    
    websocketConnection.onclose = () => {
      systemStatus.update(status => ({ ...status, connected: false }));
      connectionQuality = 'poor';
    };
    
    websocketConnection.onerror = () => {
      connectionQuality = 'poor';
    };
  }
  
  function setupPollingFallback() {
    // Poll for updates every 5 seconds as fallback
    setInterval(async () => {
      try {
        const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:9000';
        const response = await fetch(`${apiUrl}/api/v1/pm/orchestration/projects/${orchestrationId}/status`);
        
        if (response.ok) {
          const data = await response.json();
          // Convert status to streaming update format
          handleStreamingUpdate({
            type: 'orchestration_update',
            data: data,
            timestamp: new Date().toISOString()
          });
        }
      } catch (error) {
        console.error('Polling error:', error);
      }
    }, 5000);
  }
  
  function handleStreamingUpdate(update: any) {
    const streamingUpdate: StreamingUpdate = {
      id: Math.random().toString(36).substr(2, 9),
      type: update.type || 'unknown',
      timestamp: update.timestamp || new Date().toISOString(),
      data: update.data || update,
      agent: update.agent || extractAgentFromUpdate(update),
      priority: determinePriority(update)
    };
    
    realtimeUpdates.update(updates => {
      const newUpdates = [streamingUpdate, ...updates].slice(0, maxUpdates);
      
      // Update agent activities based on the update
      if (streamingUpdate.type === 'agent_conversation' || streamingUpdate.agent) {
        updateAgentActivity(streamingUpdate);
      }
      
      return newUpdates;
    });
    
    // Auto-scroll to latest if enabled
    if (autoScroll && scrollContainer) {
      setTimeout(() => {
        scrollContainer.scrollTop = 0;
      }, 100);
    }
  }
  
  function extractAgentFromUpdate(update: any): string | undefined {
    if (update.participant) return update.participant;
    if (update.data?.agent_name) return update.data.agent_name;
    if (update.data?.initiated_by) return update.data.initiated_by;
    return undefined;
  }
  
  function determinePriority(update: any): 'low' | 'medium' | 'high' {
    if (update.type === 'agent_conversation') return 'medium';
    if (update.type === 'stage_transition') return 'high';
    if (update.type === 'cost_update') return 'high';
    if (update.type === 'metrics') return 'low';
    return 'medium';
  }
  
  function updateAgentActivity(update: StreamingUpdate) {
    if (!update.agent) return;
    
    agentActivities.update(activities => {
      const existingIndex = activities.findIndex(a => a.agent_name === update.agent);
      const activity: AgentActivity = {
        agent_name: update.agent!,
        status: 'online',
        current_task: getTaskFromUpdate(update),
        last_activity: update.timestamp,
        response_time: Math.random() * 2 + 0.5, // Mock response time
        message_count: existingIndex >= 0 ? activities[existingIndex].message_count + 1 : 1
      };
      
      if (existingIndex >= 0) {
        activities[existingIndex] = activity;
      } else {
        activities.push(activity);
      }
      
      return activities;
    });
  }
  
  function getTaskFromUpdate(update: StreamingUpdate): string {
    switch (update.type) {
      case 'agent_conversation':
        return 'Having conversation';
      case 'stage_transition':
        return 'Managing stage transition';
      case 'metrics':
        return 'Updating metrics';
      case 'cost_update':
        return 'Processing cost data';
      default:
        return 'Active on project';
    }
  }
  
  function startHeartbeat() {
    heartbeatInterval = setInterval(() => {
      const now = new Date().toISOString();
      systemStatus.update(status => ({
        ...status,
        latency: Math.random() * 100 + 20, // Mock latency
        last_heartbeat: now
      }));
      
      // Update connection quality based on latency
      systemStatus.subscribe(status => {
        if (status.latency > 200) connectionQuality = 'poor';
        else if (status.latency > 100) connectionQuality = 'fair';
        else connectionQuality = 'good';
      });
    }, 5000);
  }
  
  function startMetricsCollection() {
    metricsInterval = setInterval(() => {
      realtimeUpdates.subscribe(updates => {
        const recentUpdates = updates.filter(u => 
          new Date(u.timestamp).getTime() > Date.now() - 60000 // Last minute
        );
        
        streamingMetrics = {
          messages_per_minute: recentUpdates.length,
          active_conversations: recentUpdates.filter(u => u.type === 'agent_conversation').length,
          bandwidth_usage: Math.random() * 1000 + 500, // Mock bandwidth
          error_rate: Math.random() * 5 // Mock error rate
        };
      });
    }, 10000);
  }
  
  function setupMockData() {
    // Generate some initial mock data for development
    const mockUpdates = [
      {
        type: 'agent_conversation',
        data: { conversation_id: '123', content: 'Starting design review session' },
        timestamp: new Date(Date.now() - 30000).toISOString(),
        agent: 'Sara UX Designer'
      },
      {
        type: 'stage_transition',
        data: { from_stage: 'planning', to_stage: 'execution', transition_reason: 'Planning phase completed' },
        timestamp: new Date(Date.now() - 60000).toISOString(),
        agent: 'Marcus PM'
      },
      {
        type: 'metrics',
        data: { efficiency_score: 0.88, collaboration_score: 0.92 },
        timestamp: new Date(Date.now() - 120000).toISOString()
      }
    ];
    
    mockUpdates.forEach(update => handleStreamingUpdate(update));
  }
  
  function getUpdateIcon(type: string): string {
    const typeConfig = updateTypes.find(t => t.id === type);
    return typeConfig?.icon || '📡';
  }
  
  function getPriorityColor(priority: string): string {
    switch (priority) {
      case 'high': return 'border-l-red-500 bg-red-50';
      case 'medium': return 'border-l-yellow-500 bg-yellow-50';
      case 'low': return 'border-l-green-500 bg-green-50';
      default: return 'border-l-gray-500 bg-gray-50';
    }
  }
  
  function getConnectionStatusColor(quality: string): string {
    switch (quality) {
      case 'good': return 'text-green-600';
      case 'fair': return 'text-yellow-600';
      case 'poor': return 'text-red-600';
      default: return 'text-gray-600';
    }
  }
  
  function formatTimestamp(timestamp: string): string {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit', 
      second: '2-digit' 
    });
  }
  
  function formatUpdateData(data: any, type: string): string {
    switch (type) {
      case 'agent_conversation':
        return data.content || data.message_content || 'Conversation activity';
      case 'stage_transition':
        return `Transitioned from ${data.from_stage} to ${data.to_stage}`;
      case 'metrics':
        return `Efficiency: ${Math.round((data.efficiency_score || 0) * 100)}%, Collaboration: ${Math.round((data.collaboration_score || 0) * 100)}%`;
      case 'cost_update':
        return `Cost update: $${data.amount || data.cost || 'N/A'}`;
      default:
        return JSON.stringify(data).slice(0, 100) + '...';
    }
  }
  
  function clearUpdates() {
    realtimeUpdates.set([]);
    systemStatus.update(status => ({ ...status, messages_received: 0 }));
  }
  
  function exportUpdates() {
    realtimeUpdates.subscribe(updates => {
      const dataStr = JSON.stringify(updates, null, 2);
      const dataBlob = new Blob([dataStr], { type: 'application/json' });
      const url = URL.createObjectURL(dataBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `orchestration-updates-${orchestrationId}-${Date.now()}.json`;
      link.click();
      URL.revokeObjectURL(url);
    });
  }
  
  $: filteredUpdates = selectedFilter === 'all' 
    ? $realtimeUpdates 
    : $realtimeUpdates.filter(update => update.type === selectedFilter);
</script>

<!-- Real-time Streaming Monitor -->
<div class="space-y-6">
  <!-- Status Header -->
  <Card>
    <div class="p-4">
      <div class="flex items-center justify-between">
        <div>
          <h3 class="text-lg font-semibold text-surface-900 ">
            📡 Real-time Monitoring
          </h3>
          <p class="text-sm text-surface-600  mt-1">
            Live updates, agent conversations, and system status
          </p>
        </div>
        
        <!-- Connection Status -->
        <div class="flex items-center space-x-4">
          <div class="flex items-center space-x-2">
            <div class="w-3 h-3 rounded-full {$systemStatus.connected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}"></div>
            <span class="text-sm {getConnectionStatusColor(connectionQuality)}">
              {$systemStatus.connected ? 'Connected' : 'Disconnected'} ({connectionQuality})
            </span>
          </div>
          
          {#if $systemStatus.connected}
            <div class="text-xs text-surface-600 ">
              Latency: {Math.round($systemStatus.latency)}ms
            </div>
          {/if}
          
          <div class="text-xs text-surface-600 ">
            {$systemStatus.messages_received} messages
          </div>
        </div>
      </div>
    </div>
  </Card>
  
  <!-- Streaming Metrics -->
  <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
    <Card class="bg-blue-50 border-blue-200">
      <div class="p-3">
        <div class="text-sm text-blue-600 font-medium">Messages/Min</div>
        <div class="text-xl font-bold text-blue-700">{streamingMetrics.messages_per_minute}</div>
      </div>
    </Card>
    
    <Card class="bg-green-50 border-green-200">
      <div class="p-3">
        <div class="text-sm text-green-600 font-medium">Active Conversations</div>
        <div class="text-xl font-bold text-green-700">{streamingMetrics.active_conversations}</div>
      </div>
    </Card>
    
    <Card class="bg-purple-50 border-purple-200">
      <div class="p-3">
        <div class="text-sm text-purple-600 font-medium">Bandwidth (KB/s)</div>
        <div class="text-xl font-bold text-purple-700">{Math.round(streamingMetrics.bandwidth_usage)}</div>
      </div>
    </Card>
    
    <Card class="bg-yellow-50 border-yellow-200">
      <div class="p-3">
        <div class="text-sm text-yellow-600 font-medium">Error Rate (%)</div>
        <div class="text-xl font-bold text-yellow-700">{streamingMetrics.error_rate.toFixed(1)}</div>
      </div>
    </Card>
  </div>
  
  <!-- Agent Activity Panel -->
  {#if $agentActivities.length > 0}
    <Card>
      <div class="p-4">
        <h4 class="font-medium text-surface-900  mb-3">
          🤖 Live Agent Activity
        </h4>
        
        <div class="space-y-2">
          {#each $agentActivities as activity}
            <div class="flex items-center justify-between py-2 border-b border-surface-200  last:border-b-0">
              <div class="flex items-center space-x-3">
                <div class="w-3 h-3 rounded-full {activity.status === 'online' ? 'bg-green-500' : 'bg-gray-400'}"></div>
                <span class="font-medium text-surface-900 ">
                  {activity.agent_name}
                </span>
                <span class="text-sm text-surface-600 ">
                  {activity.current_task}
                </span>
              </div>
              
              <div class="flex items-center space-x-4 text-xs text-surface-500">
                <span>Response: {activity.response_time.toFixed(1)}s</span>
                <span>Messages: {activity.message_count}</span>
                <span>{formatTimestamp(activity.last_activity)}</span>
              </div>
            </div>
          {/each}
        </div>
      </div>
    </Card>
  {/if}
  
  <!-- Filter Controls -->
  <Card>
    <div class="p-4">
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-2">
          <span class="text-sm font-medium text-surface-900 ">Filter:</span>
          <select 
            bind:value={selectedFilter}
            class="text-sm border border-surface-300  rounded-md px-3 py-1 
                   bg-surface-50  text-surface-900 "
          >
            {#each updateTypes as type}
              <option value={type.id}>{type.icon} {type.label}</option>
            {/each}
          </select>
          
          <Badge class="bg-blue-100 text-blue-800">
            {filteredUpdates.length} updates
          </Badge>
        </div>
        
        <div class="flex items-center space-x-2">
          <label class="flex items-center space-x-1 text-sm">
            <input type="checkbox" bind:checked={autoScroll} class="rounded" />
            <span class="text-surface-700 ">Auto-scroll</span>
          </label>
          
          <Button variant="outline" size="sm" on:click={clearUpdates}>
            Clear
          </Button>
          
          <Button variant="outline" size="sm" on:click={exportUpdates}>
            Export
          </Button>
        </div>
      </div>
    </div>
  </Card>
  
  <!-- Updates Stream -->
  <Card>
    <div class="p-4">
      <h4 class="font-medium text-surface-900  mb-4">
        📨 Live Updates Stream
      </h4>
      
      <div 
        bind:this={scrollContainer}
        class="max-h-96 overflow-y-auto space-y-2"
      >
        {#if filteredUpdates.length === 0}
          <div class="text-center py-8 text-surface-500 ">
            <div class="text-4xl mb-2">📡</div>
            <p>No updates yet. Waiting for real-time data...</p>
          </div>
        {:else}
          {#each filteredUpdates as update (update.id)}
            <div 
              class="border-l-4 {getPriorityColor(update.priority)} rounded-r-md p-3 transition-all duration-200 hover:shadow-md"
              transition:slide
            >
              <div class="flex items-start justify-between">
                <div class="flex-1">
                  <div class="flex items-center space-x-2 mb-1">
                    <span class="text-lg">{getUpdateIcon(update.type)}</span>
                    <span class="text-sm font-medium text-surface-900  capitalize">
                      {update.type.replace(/_/g, ' ')}
                    </span>
                    {#if update.agent}
                      <Badge class="bg-blue-100 text-blue-800 text-xs">
                        {update.agent}
                      </Badge>
                    {/if}
                    <Badge class="bg-gray-100 text-gray-600 text-xs">
                      {update.priority}
                    </Badge>
                  </div>
                  
                  <p class="text-sm text-surface-700 ">
                    {formatUpdateData(update.data, update.type)}
                  </p>
                </div>
                
                <div class="text-xs text-surface-500 ml-4">
                  {formatTimestamp(update.timestamp)}
                </div>
              </div>
            </div>
          {/each}
        {/if}
      </div>
    </div>
  </Card>
</div>

<style>
  /* Smooth animations */
  .transition-all {
    transition: all 0.2s ease-in-out;
  }
  
  /* Pulse animation for online indicators */
  .animate-pulse {
    animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
  }
  
  @keyframes pulse {
    0%, 100% {
      opacity: 1;
    }
    50% {
      opacity: .8;
    }
  }
  
  /* Scrollbar styling */
  .overflow-y-auto::-webkit-scrollbar {
    width: 8px;
  }
  
  .overflow-y-auto::-webkit-scrollbar-track {
    background: transparent;
  }
  
  .overflow-y-auto::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 4px;
  }
  
  .overflow-y-auto::-webkit-scrollbar-thumb:hover {
    background: #94a3b8;
  }
</style>