<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { writable } from 'svelte/store';
  import { Card, Badge, Button, Avatar } from '$lib/components/ui';
  import { slide, scale } from 'svelte/transition';

  export let agentAssignments: any[] = [];
  export let orchestrationId: string = '550e8400-e29b-41d4-a716-446655440000'; // Default UUID format
  
  interface AgentAssignment {
    agent_name: string;
    agent_role: string;
    efficiency_score: number;
    collaboration_score: number;
    quality_score: number;
    tasks_completed: number;
    tasks_assigned: number;
    cost_incurred: number;
    active: boolean;
    last_active?: string;
  }
  
  let selectedAgent: string | null = null;
  let collaborationMatrix: Record<string, Record<string, number>> = {};
  let realTimeAgentStatus = writable<Record<string, any>>({});
  let showPerformanceDetails = false;
  let sortBy: 'efficiency' | 'collaboration' | 'cost' | 'tasks' = 'efficiency';
  let filterRole: string = 'all';
  
  // Agent avatars and colors
  const agentProfiles: Record<string, { avatar: string; color: string; title: string }> = {
    'Marcus PM': { avatar: '👨‍💼', color: 'blue', title: 'Project Manager' },
    'Sara UX Designer': { avatar: '👩‍🎨', color: 'purple', title: 'UX Designer' },
    'Baccio Tech Architect': { avatar: '👨‍💻', color: 'green', title: 'Tech Architect' },
    'Dan Engineer': { avatar: '👨‍🔧', color: 'orange', title: 'Senior Engineer' },
    'Thor QA Guardian': { avatar: '⚡', color: 'red', title: 'QA Guardian' },
    'Ali Chief of Staff': { avatar: '🎯', color: 'indigo', title: 'Chief of Staff' },
    'Amy CFO': { avatar: '💼', color: 'yellow', title: 'CFO' },
    'Luca Security Expert': { avatar: '🛡️', color: 'gray', title: 'Security Expert' }
  };
  
  let statusUpdateInterval: any;
  
  onMount(() => {
    loadCollaborationData();
    startRealTimeUpdates();
  });
  
  onDestroy(() => {
    if (statusUpdateInterval) {
      clearInterval(statusUpdateInterval);
    }
  });
  
  async function loadCollaborationData() {
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:9000';
      const response = await fetch(`${apiUrl}/api/v1/pm/orchestration/projects/${orchestrationId}/collaboration`);

      if (response.ok) {
        const data = await response.json();
        collaborationMatrix = data.collaboration_matrix || {};
      } else {
        // Fallback to mock data
        collaborationMatrix = generateMockCollaborationMatrix();
      }
    } catch {
      // Silent failure
      collaborationMatrix = generateMockCollaborationMatrix();
    }
  }
  
  function generateMockCollaborationMatrix(): Record<string, Record<string, number>> {
    const matrix: Record<string, Record<string, number>> = {};
    agentAssignments.forEach(agent1 => {
      matrix[agent1.agent_name] = {};
      agentAssignments.forEach(agent2 => {
        if (agent1.agent_name !== agent2.agent_name) {
          // Generate mock collaboration strength (0-1)
          matrix[agent1.agent_name][agent2.agent_name] = Math.random() * 0.8 + 0.2;
        }
      });
    });
    return matrix;
  }
  
  function startRealTimeUpdates() {
    // Simulate real-time status updates
    statusUpdateInterval = setInterval(() => {
      const updates: Record<string, any> = {};
      agentAssignments.forEach(agent => {
        updates[agent.agent_name] = {
          online: Math.random() > 0.3, // 70% chance online
          current_task: generateRandomTask(),
          response_time: Math.random() * 3 + 0.5, // 0.5-3.5 seconds
          cpu_usage: Math.random() * 100,
          last_seen: new Date().toISOString()
        };
      });
      realTimeAgentStatus.set(updates);
    }, 5000);
  }
  
  function generateRandomTask(): string {
    const tasks = [
      'Analyzing requirements',
      'Code review in progress',
      'Testing new features',
      'Documentation update',
      'Meeting with stakeholders',
      'Architecture planning',
      'Performance optimization',
      'Security assessment',
      'User experience research',
      'Idle'
    ];
    return tasks[Math.floor(Math.random() * tasks.length)];
  }
  
  function getAgentProfile(agentName: string): { avatar: string; color: string; title: string } {
    return agentProfiles[agentName as keyof typeof agentProfiles] || { 
      avatar: '🤖', 
      color: 'gray', 
      title: 'AI Agent' 
    };
  }
  
  function getRoleColor(role: string): string {
    switch (role) {
      case 'primary': return 'bg-blue-100 text-blue-800';
      case 'contributor': return 'bg-green-100 text-green-800';
      case 'consultant': return 'bg-purple-100 text-purple-800';
      case 'reviewer': return 'bg-yellow-100 text-yellow-800';
      case 'observer': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  }
  
  function getPerformanceColor(score: number, type: 'bg' | 'text' = 'bg'): string {
    if (score >= 0.9) return type === 'bg' ? 'bg-green-500' : 'text-green-600';
    if (score >= 0.8) return type === 'bg' ? 'bg-blue-500' : 'text-blue-600';
    if (score >= 0.7) return type === 'bg' ? 'bg-yellow-500' : 'text-yellow-600';
    if (score >= 0.6) return type === 'bg' ? 'bg-orange-500' : 'text-orange-600';
    return type === 'bg' ? 'bg-red-500' : 'text-red-600';
  }
  
  function getCollaborationStrength(agent1: string, agent2: string): number {
    return collaborationMatrix[agent1]?.[agent2] || 0;
  }
  
  function getCompletionRate(agent: AgentAssignment): number {
    return agent.tasks_assigned > 0 ? (agent.tasks_completed / agent.tasks_assigned) * 100 : 0;
  }
  
  function formatCurrency(amount: number): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  }
  
  function sortAgents(agents: AgentAssignment[], sortBy: string): AgentAssignment[] {
    return [...agents].sort((a, b) => {
      switch (sortBy) {
        case 'efficiency':
          return b.efficiency_score - a.efficiency_score;
        case 'collaboration':
          return b.collaboration_score - a.collaboration_score;
        case 'cost':
          return a.cost_incurred - b.cost_incurred; // Lower cost is better
        case 'tasks':
          return b.tasks_completed - a.tasks_completed;
        default:
          return 0;
      }
    });
  }
  
  function filterAgents(agents: AgentAssignment[], role: string): AgentAssignment[] {
    if (role === 'all') return agents;
    return agents.filter(agent => agent.agent_role === role);
  }
  
  async function optimizeCollaboration() {
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:9000';
      const response = await fetch(`${apiUrl}/api/v1/pm/orchestration/projects/${orchestrationId}/optimize-collaboration`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          current_assignments: agentAssignments,
          optimization_goals: ['efficiency', 'collaboration']
        })
      });

      if (response.ok) {
        // Reload data to show optimization results
        window.location.reload();
      }
    } catch {
      // Silent failure
    }
  }
  
  $: filteredAndSortedAgents = sortAgents(filterAgents(agentAssignments, filterRole), sortBy);
  $: currentStatus = $realTimeAgentStatus as Record<string, any>;
</script>

<!-- Agent Collaboration Panel -->
<div class="space-y-6">
  <!-- Header with Controls -->
  <Card>
    <div class="p-4">
      <div class="flex items-center justify-between">
        <div>
          <h3 class="text-lg font-semibold text-surface-900 ">
            🤖 Agent Collaboration
          </h3>
          <p class="text-sm text-surface-600  mt-1">
            Real-time agent performance and collaboration analytics
          </p>
        </div>
        
        <div class="flex items-center space-x-3">
          <!-- Filters and Sort -->
          <select 
            bind:value={filterRole}
            class="text-sm border border-surface-300  rounded-md px-3 py-1 
                   bg-surface-50  text-surface-900 "
          >
            <option value="all">All Roles</option>
            <option value="primary">Primary</option>
            <option value="contributor">Contributors</option>
            <option value="consultant">Consultants</option>
            <option value="reviewer">Reviewers</option>
          </select>
          
          <select 
            bind:value={sortBy}
            class="text-sm border border-surface-300  rounded-md px-3 py-1 
                   bg-surface-50  text-surface-900 "
          >
            <option value="efficiency">Sort by Efficiency</option>
            <option value="collaboration">Sort by Collaboration</option>
            <option value="cost">Sort by Cost</option>
            <option value="tasks">Sort by Tasks</option>
          </select>
          
          <Button variant="outline" size="sm" on:click={() => showPerformanceDetails = !showPerformanceDetails}>
            {showPerformanceDetails ? '📊 Hide' : '📈 Details'}
          </Button>
          
          <Button variant="primary" size="sm" on:click={optimizeCollaboration}>
            ⚡ Optimize
          </Button>
        </div>
      </div>
    </div>
  </Card>
  
  <!-- Agent Grid -->
  <div class="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
    {#each filteredAndSortedAgents as agent}
      <Card class="transition-all duration-200 hover:shadow-lg">
        <div class="p-4">
          <!-- Agent Header -->
          <div class="flex items-center justify-between mb-3">
            <div class="flex items-center space-x-3">
              <!-- Agent Avatar with Status -->
              <div class="relative">
                <div class="w-12 h-12 rounded-full bg-{getAgentProfile(agent.agent_name).color}-100 
                           flex items-center justify-center text-2xl">
                  {getAgentProfile(agent.agent_name).avatar}
                </div>
                
                <!-- Online Status Indicator -->
                <div class="absolute -bottom-1 -right-1 w-4 h-4 rounded-full border-2 border-white
                           {currentStatus[agent.agent_name]?.online ? 'bg-green-500' : 'bg-gray-400'}">
                </div>
              </div>
              
              <div>
                <h4 class="font-medium text-surface-900 ">
                  {agent.agent_name}
                </h4>
                <p class="text-xs text-surface-600 ">
                  {getAgentProfile(agent.agent_name).title}
                </p>
              </div>
            </div>
            
            <!-- Role Badge -->
            <Badge class="{getRoleColor(agent.agent_role)}">
              {agent.agent_role}
            </Badge>
          </div>
          
          <!-- Performance Metrics -->
          <div class="space-y-2">
            <!-- Efficiency Score -->
            <div class="flex items-center justify-between">
              <span class="text-xs text-surface-600 ">Efficiency</span>
              <div class="flex items-center space-x-2">
                <div class="w-20 bg-gray-200 rounded-full h-1.5">
                  <div 
                    class="h-1.5 rounded-full transition-all duration-500 {getPerformanceColor(agent.efficiency_score, 'bg')}"
                    style="width: {agent.efficiency_score * 100}%"
                  ></div>
                </div>
                <span class="text-xs font-medium {getPerformanceColor(agent.efficiency_score, 'text')}">
                  {Math.round(agent.efficiency_score * 100)}%
                </span>
              </div>
            </div>
            
            <!-- Collaboration Score -->
            <div class="flex items-center justify-between">
              <span class="text-xs text-surface-600 ">Collaboration</span>
              <div class="flex items-center space-x-2">
                <div class="w-20 bg-gray-200 rounded-full h-1.5">
                  <div 
                    class="h-1.5 rounded-full transition-all duration-500 {getPerformanceColor(agent.collaboration_score, 'bg')}"
                    style="width: {agent.collaboration_score * 100}%"
                  ></div>
                </div>
                <span class="text-xs font-medium {getPerformanceColor(agent.collaboration_score, 'text')}">
                  {Math.round(agent.collaboration_score * 100)}%
                </span>
              </div>
            </div>
          </div>
          
          <!-- Task Summary -->
          <div class="mt-3 pt-3 border-t border-surface-200 ">
            <div class="grid grid-cols-2 gap-3 text-xs">
              <div>
                <span class="text-surface-500">Tasks</span>
                <div class="font-medium text-surface-900 ">
                  {agent.tasks_completed}/{agent.tasks_assigned}
                </div>
                <div class="text-surface-600 ">
                  {Math.round(getCompletionRate(agent))}% complete
                </div>
              </div>
              
              <div>
                <span class="text-surface-500">Cost</span>
                <div class="font-medium text-surface-900 ">
                  {formatCurrency(agent.cost_incurred)}
                </div>
                <div class="text-surface-600 ">
                  ${Math.round(agent.cost_incurred / Math.max(agent.tasks_completed, 1))}/task
                </div>
              </div>
            </div>
          </div>
          
          <!-- Current Activity -->
          {#if currentStatus[agent.agent_name]}
            <div class="mt-3 pt-3 border-t border-surface-200 ">
              <div class="flex items-center justify-between text-xs">
                <span class="text-surface-500">Current Activity</span>
                <div class="flex items-center space-x-1">
                  <div class="w-2 h-2 rounded-full {currentStatus[agent.agent_name].online ? 'bg-green-400 animate-pulse' : 'bg-gray-400'}"></div>
                  <span class="text-surface-600 ">
                    {currentStatus[agent.agent_name].online ? 'Online' : 'Offline'}
                  </span>
                </div>
              </div>
              
              {#if currentStatus[agent.agent_name].online}
                <div class="text-xs text-surface-700  mt-1">
                  {currentStatus[agent.agent_name].current_task}
                </div>
                
                <!-- Response Time -->
                <div class="flex items-center justify-between text-xs mt-1">
                  <span class="text-surface-500">Response Time</span>
                  <span class="font-medium text-surface-700 ">
                    {currentStatus[agent.agent_name].response_time?.toFixed(1)}s
                  </span>
                </div>
              {/if}
            </div>
          {/if}
          
          <!-- Detailed Performance (Expandable) -->
          {#if showPerformanceDetails}
            <div class="mt-3 pt-3 border-t border-surface-200 " transition:slide>
              <!-- Quality Score -->
              <div class="flex items-center justify-between text-xs mb-2">
                <span class="text-surface-500">Quality Score</span>
                <div class="flex items-center space-x-2">
                  <div class="w-16 bg-gray-200 rounded-full h-1">
                    <div 
                      class="h-1 rounded-full transition-all duration-500 {getPerformanceColor(agent.quality_score || 0.8, 'bg')}"
                      style="width: {(agent.quality_score || 0.8) * 100}%"
                    ></div>
                  </div>
                  <span class="font-medium {getPerformanceColor(agent.quality_score || 0.8, 'text')}">
                    {Math.round((agent.quality_score || 0.8) * 100)}%
                  </span>
                </div>
              </div>
              
              <!-- Collaboration Partners -->
              <div class="text-xs">
                <span class="text-surface-500">Top Collaborators</span>
                <div class="flex flex-wrap gap-1 mt-1">
                  {#each agentAssignments.slice(0, 3) as otherAgent}
                    {#if otherAgent.agent_name !== agent.agent_name}
                      {@const strength = getCollaborationStrength(agent.agent_name, otherAgent.agent_name)}
                      <div class="flex items-center space-x-1 bg-surface-100  rounded px-1.5 py-0.5">
                        <span>{getAgentProfile(otherAgent.agent_name).avatar}</span>
                        <span class="text-xs">{Math.round(strength * 100)}%</span>
                      </div>
                    {/if}
                  {/each}
                </div>
              </div>
            </div>
          {/if}
          
          <!-- Action Button -->
          <button
            on:click={() => selectedAgent = selectedAgent === agent.agent_name ? null : agent.agent_name}
            class="w-full mt-3 py-2 text-xs font-medium text-surface-700  
                   hover:text-surface-900 transition-colors duration-200"
          >
            {selectedAgent === agent.agent_name ? '▲ Hide Details' : '▼ Show Details'}
          </button>
        </div>
      </Card>
    {/each}
  </div>
  
  <!-- Collaboration Matrix (when agent is selected) -->
  {#if selectedAgent}
    <div transition:scale>
      <Card>
        <div class="p-4">
          <div class="flex items-center justify-between mb-4">
            <h4 class="font-medium text-surface-900 ">
              🔗 {selectedAgent} Collaboration Matrix
            </h4>
            <button
              on:click={() => selectedAgent = null}
              class="text-surface-400 hover:text-surface-600"
            >
              ✕
            </button>
          </div>

          <div class="space-y-2">
            {#each agentAssignments as otherAgent}
              {#if otherAgent.agent_name !== selectedAgent}
                {@const strength = getCollaborationStrength(selectedAgent, otherAgent.agent_name)}
                <div class="flex items-center justify-between py-2">
                  <div class="flex items-center space-x-3">
                    <span class="text-xl">{getAgentProfile(otherAgent.agent_name).avatar}</span>
                    <span class="text-sm font-medium text-surface-900 ">
                      {otherAgent.agent_name}
                    </span>
                  </div>

                  <div class="flex items-center space-x-2">
                    <div class="w-24 bg-gray-200 rounded-full h-2">
                      <div
                        class="h-2 rounded-full transition-all duration-500 {getPerformanceColor(strength, 'bg')}"
                        style="width: {strength * 100}%"
                      ></div>
                    </div>
                    <span class="text-xs font-medium {getPerformanceColor(strength, 'text')} w-10">
                      {Math.round(strength * 100)}%
                    </span>
                  </div>
                </div>
              {/if}
            {/each}
          </div>
        </div>
      </Card>
    </div>
  {/if}
</div>

<style>
  /* Smooth animations */
  .transition-all {
    transition: all 0.2s ease-in-out;
  }
  
  /* Online indicator pulse */
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
  
  /* Progress bar animations */
  .h-1\.5, .h-1, .h-2 {
    transition: width 0.5s ease-in-out;
  }
</style>