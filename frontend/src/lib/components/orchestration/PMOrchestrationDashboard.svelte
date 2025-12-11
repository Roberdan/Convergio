<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { writable } from 'svelte/store';
  import ProjectJourneyVisualization from './ProjectJourneyVisualization.svelte';
  import AgentCollaborationPanel from './AgentCollaborationPanel.svelte';
  import OrchestrationMetricsCard from './OrchestrationMetricsCard.svelte';
  import RealTimeStreamingMonitor from './RealTimeStreamingMonitor.svelte';
  import TouchpointTimeline from './TouchpointTimeline.svelte';
  import { Card, Button, Badge, LoadingSpinner } from '$lib/components/ui';
  
  export let projectId: string = '';
  
  // State management
  let orchestrationData = writable(null);
  let loading = true;
  let error = '';
  let selectedView: 'overview' | 'journey' | 'agents' | 'metrics' | 'realtime' = 'overview';
  let websocketConnection: WebSocket | null = null;
  
  // Orchestration data structure
  interface OrchestrationData {
    id: string;
    orchestration_status: string;
    current_stage: string;
    primary_agent: string;
    ai_efficiency_score: number;
    agent_collaboration_score: number;
    satisfaction_score: number;
    touchpoint_count: number;
    agent_assignments: AgentAssignment[];
    journey_stages: JourneyStage[];
    recent_touchpoints: Touchpoint[];
    real_time_metrics: any;
  }
  
  interface AgentAssignment {
    agent_name: string;
    agent_role: string;
    efficiency_score: number;
    collaboration_score: number;
    tasks_completed: number;
    cost_incurred: number;
    active: boolean;
  }
  
  interface JourneyStage {
    stage_name: string;
    status: string;
    progress_percentage: number;
    satisfaction_score: number;
    start_date: string;
    primary_agents: string[];
  }
  
  interface Touchpoint {
    id: string;
    touchpoint_type: string;
    title: string;
    initiated_by: string;
    interaction_date: string;
    satisfaction_score: number;
    participants: string[];
  }
  
  onMount(async () => {
    if (projectId) {
      await loadOrchestrationData();
      setupRealTimeConnection();
    }
  });
  
  onDestroy(() => {
    if (websocketConnection) {
      websocketConnection.close();
    }
  });
  
  async function loadOrchestrationData() {
    loading = true;
    error = '';
    
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:9000';
      
      // Load orchestration status
      const response = await fetch(`${apiUrl}/api/v1/pm/orchestration/projects/${projectId}`);
      
      if (!response.ok) {
        throw new Error(`Failed to load orchestration data: ${response.status}`);
      }
      
      const data = await response.json();
      orchestrationData.set(data);
      
    } catch (err) {
      console.error('Error loading orchestration data:', err);
      error = err instanceof Error ? err.message : 'Failed to load orchestration data';
      
      // Fallback to mock data for development
      orchestrationData.set(getMockOrchestrationData());
    } finally {
      loading = false;
    }
  }
  
  function setupRealTimeConnection() {
    try {
      const wsUrl = `ws://localhost:9000/api/v1/pm/realtime/projects/${projectId}/ws`;
      websocketConnection = new WebSocket(wsUrl);
      
      websocketConnection.onopen = () => {
        console.log('✅ Real-time connection established');
      };
      
      websocketConnection.onmessage = (event) => {
        try {
          const update = JSON.parse(event.data);
          handleRealTimeUpdate(update);
        } catch (error) {
          console.error('Error parsing real-time update:', error);
        }
      };
      
      websocketConnection.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
      
      websocketConnection.onclose = () => {
        console.log('Real-time connection closed');
        // Attempt to reconnect after 5 seconds
        setTimeout(() => {
          if (projectId) {
            setupRealTimeConnection();
          }
        }, 5000);
      };
      
    } catch (error) {
      console.error('Failed to setup WebSocket connection:', error);
    }
  }
  
  function handleRealTimeUpdate(update: any) {
    orchestrationData.update(current => {
      if (!current) return current;
      
      switch (update.type) {
        case 'orchestration_update':
          return { ...current, ...update.data };
        case 'agent_conversation':
          // Update agent activity indicators
          return current;
        case 'metrics':
          return { ...current, real_time_metrics: update.data.metrics };
        case 'stage_transition':
          return { ...current, current_stage: update.data.to_stage };
        default:
          return current;
      }
    });
  }
  
  function getMockOrchestrationData(): OrchestrationData {
    return {
      id: projectId || '550e8400-e29b-41d4-a716-446655440000', // Use proper UUID format
      orchestration_status: 'active',
      current_stage: 'execution',
      primary_agent: 'Marcus PM',
      ai_efficiency_score: 0.87,
      agent_collaboration_score: 0.92,
      satisfaction_score: 0.89,
      touchpoint_count: 24,
      agent_assignments: [
        {
          agent_name: 'Marcus PM',
          agent_role: 'primary',
          efficiency_score: 0.91,
          collaboration_score: 0.88,
          tasks_completed: 15,
          cost_incurred: 2450.00,
          active: true
        },
        {
          agent_name: 'Sara UX Designer',
          agent_role: 'contributor',
          efficiency_score: 0.85,
          collaboration_score: 0.95,
          tasks_completed: 12,
          cost_incurred: 1850.00,
          active: true
        },
        {
          agent_name: 'Baccio Tech Architect',
          agent_role: 'consultant',
          efficiency_score: 0.89,
          collaboration_score: 0.83,
          tasks_completed: 8,
          cost_incurred: 3200.00,
          active: true
        }
      ],
      journey_stages: [
        {
          stage_name: 'discovery',
          status: 'completed',
          progress_percentage: 100,
          satisfaction_score: 0.91,
          start_date: '2024-01-15T09:00:00Z',
          primary_agents: ['Marcus PM', 'Sara UX Designer']
        },
        {
          stage_name: 'planning',
          status: 'completed',
          progress_percentage: 100,
          satisfaction_score: 0.88,
          start_date: '2024-01-22T09:00:00Z',
          primary_agents: ['Marcus PM', 'Baccio Tech Architect']
        },
        {
          stage_name: 'execution',
          status: 'active',
          progress_percentage: 67,
          satisfaction_score: 0.85,
          start_date: '2024-02-01T09:00:00Z',
          primary_agents: ['Marcus PM', 'Sara UX Designer', 'Baccio Tech Architect']
        }
      ],
      recent_touchpoints: [
        {
          id: '1',
          touchpoint_type: 'client_checkin',
          title: 'Weekly Progress Review',
          initiated_by: 'Marcus PM',
          interaction_date: '2024-02-14T14:00:00Z',
          satisfaction_score: 0.92,
          participants: ['Marcus PM', 'Sara UX Designer', 'Client']
        },
        {
          id: '2',
          touchpoint_type: 'agent_interaction',
          title: 'Design System Architecture Discussion',
          initiated_by: 'Baccio Tech Architect',
          interaction_date: '2024-02-13T10:30:00Z',
          satisfaction_score: 0.88,
          participants: ['Baccio Tech Architect', 'Sara UX Designer']
        }
      ],
      real_time_metrics: {
        active_conversations: 2,
        avg_response_time: 1.2,
        current_cost_rate: 125.50,
        efficiency_trend: 'up'
      }
    };
  }
  
  async function optimizeProject() {
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:9000';
      const response = await fetch(`${apiUrl}/api/v1/pm/orchestration/projects/${projectId}/optimize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          optimization_type: 'performance',
          constraints: [],
          goals: ['efficiency', 'collaboration', 'cost']
        })
      });
      
      if (response.ok) {
        // Reload data to reflect optimization
        await loadOrchestrationData();
        // Could show optimization results in a modal
      }
    } catch (error) {
      console.error('Error optimizing project:', error);
    }
  }
  
  function getStatusColor(status: string): string {
    switch (status) {
      case 'active': return 'bg-green-500';
      case 'paused': return 'bg-yellow-500';
      case 'optimizing': return 'bg-blue-500';
      case 'completed': return 'bg-purple-500';
      case 'failed': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  }
  
  function getStageColor(stage: string): string {
    switch (stage) {
      case 'discovery': return 'bg-blue-100 text-blue-800';
      case 'planning': return 'bg-yellow-100 text-yellow-800';
      case 'execution': return 'bg-green-100 text-green-800';
      case 'validation': return 'bg-purple-100 text-purple-800';
      case 'delivery': return 'bg-indigo-100 text-indigo-800';
      case 'closure': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  }
  
  $: currentData = $orchestrationData;
</script>

<!-- PM Orchestration Dashboard -->
<div class="space-y-6">
  <!-- Header with Project Status -->
  {#if loading}
    <div class="flex items-center justify-center py-12">
      <LoadingSpinner />
      <span class="ml-3 text-surface-600 ">Loading orchestration data...</span>
    </div>
  {:else if error}
    <Card>
      <div class="text-center py-8">
        <div class="text-red-600 text-lg font-medium mb-2">Failed to Load Orchestration Data</div>
        <div class="text-red-500 mb-4">{error}</div>
        <Button variant="secondary" on:click={loadOrchestrationData}>
          Try Again
        </Button>
      </div>
    </Card>
  {:else if currentData}
    <!-- Status Header -->
    <Card>
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-4">
          <div class="flex items-center space-x-2">
            <div class="w-3 h-3 rounded-full {getStatusColor(currentData.orchestration_status)}"></div>
            <span class="font-medium text-surface-900 ">
              AI Orchestration {currentData.orchestration_status.charAt(0).toUpperCase() + currentData.orchestration_status.slice(1)}
            </span>
          </div>
          <Badge class="{getStageColor(currentData.current_stage)}">
            {currentData.current_stage.charAt(0).toUpperCase() + currentData.current_stage.slice(1)} Stage
          </Badge>
          <span class="text-sm text-surface-600 ">
            Primary Agent: <span class="font-medium">{currentData.primary_agent}</span>
          </span>
        </div>
        
        <div class="flex items-center space-x-3">
          <!-- Performance Indicators -->
          <div class="flex items-center space-x-4 text-sm">
            <div class="text-center">
              <div class="text-xs text-surface-500">AI Efficiency</div>
              <div class="font-medium text-green-600">{Math.round(currentData.ai_efficiency_score * 100)}%</div>
            </div>
            <div class="text-center">
              <div class="text-xs text-surface-500">Collaboration</div>
              <div class="font-medium text-blue-600">{Math.round(currentData.agent_collaboration_score * 100)}%</div>
            </div>
            <div class="text-center">
              <div class="text-xs text-surface-500">Satisfaction</div>
              <div class="font-medium text-purple-600">{Math.round(currentData.satisfaction_score * 100)}%</div>
            </div>
          </div>
          
          <Button variant="primary" on:click={optimizeProject}>
            🚀 Optimize Project
          </Button>
        </div>
      </div>
    </Card>
    
    <!-- Navigation Tabs -->
    <div class="flex space-x-1 bg-surface-200  rounded-lg p-1">
      <button
        on:click={() => selectedView = 'overview'}
        class="px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 {selectedView === 'overview' 
          ? 'bg-surface-50 text-surface-900  shadow-sm' 
          : 'text-surface-600  hover:text-surface-900'}"
      >
        📊 Overview
      </button>
      <button
        on:click={() => selectedView = 'journey'}
        class="px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 {selectedView === 'journey' 
          ? 'bg-surface-50 text-surface-900  shadow-sm' 
          : 'text-surface-600  hover:text-surface-900'}"
      >
        🛤️ Journey
      </button>
      <button
        on:click={() => selectedView = 'agents'}
        class="px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 {selectedView === 'agents' 
          ? 'bg-surface-50 text-surface-900  shadow-sm' 
          : 'text-surface-600  hover:text-surface-900'}"
      >
        🤖 Agents
      </button>
      <button
        on:click={() => selectedView = 'metrics'}
        class="px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 {selectedView === 'metrics' 
          ? 'bg-surface-50 text-surface-900  shadow-sm' 
          : 'text-surface-600  hover:text-surface-900'}"
      >
        📈 Metrics
      </button>
      <button
        on:click={() => selectedView = 'realtime'}
        class="px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 {selectedView === 'realtime' 
          ? 'bg-surface-50 text-surface-900  shadow-sm' 
          : 'text-surface-600  hover:text-surface-900'}"
      >
        📡 Real-time
      </button>
    </div>
    
    <!-- View Content -->
    <div class="grid grid-cols-12 gap-6">
      {#if selectedView === 'overview'}
        <!-- Overview: Key metrics and recent activity -->
        <div class="col-span-12 lg:col-span-8">
          <ProjectJourneyVisualization 
            journeyStages={currentData.journey_stages}
            currentStage={currentData.current_stage}
          />
        </div>
        <div class="col-span-12 lg:col-span-4">
          <TouchpointTimeline 
            touchpoints={currentData.recent_touchpoints}
            orchestrationId={currentData.id}
          />
        </div>
        
      {:else if selectedView === 'journey'}
        <!-- Journey: Detailed stage progression and analytics -->
        <div class="col-span-12">
          <ProjectJourneyVisualization 
            journeyStages={currentData.journey_stages}
            currentStage={currentData.current_stage}
            detailed={true}
          />
        </div>
        
      {:else if selectedView === 'agents'}
        <!-- Agents: Collaboration panel and performance -->
        <div class="col-span-12">
          <AgentCollaborationPanel 
            agentAssignments={currentData.agent_assignments}
            orchestrationId={currentData.id}
          />
        </div>
        
      {:else if selectedView === 'metrics'}
        <!-- Metrics: Performance analytics and optimization -->
        <div class="col-span-12">
          <OrchestrationMetricsCard 
            orchestrationData={currentData}
            timeRange="30d"
          />
        </div>
        
      {:else if selectedView === 'realtime'}
        <!-- Real-time: Live monitoring and streaming -->
        <div class="col-span-12">
          <RealTimeStreamingMonitor 
            orchestrationId={currentData.id}
            websocketConnection={websocketConnection}
            realTimeMetrics={currentData.real_time_metrics}
          />
        </div>
      {/if}
    </div>
  {/if}
</div>

<style>
  /* Smooth transitions for tab switching */
  .transition-all {
    transition: all 0.2s ease-in-out;
  }
  
  /* Status indicator pulse animation */
  .w-3.h-3.rounded-full {
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
</style>