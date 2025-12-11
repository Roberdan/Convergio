<script lang="ts">
  import { onMount } from 'svelte';
  import { Card, Badge, Button } from '$lib/components/ui';
  import { slide, scale } from 'svelte/transition';
  
  export let touchpoints: any[] = [];
  export let orchestrationId: string = '';
  export let compact: boolean = false;
  
  interface Touchpoint {
    id: string;
    touchpoint_type: string;
    title: string;
    summary?: string;
    initiated_by: string;
    participants: string[];
    interaction_date: string;
    duration_minutes?: number;
    satisfaction_score?: number;
    productivity_score?: number;
    key_decisions?: string[];
    action_items?: string[];
    impact_level: string;
    related_stage?: string;
  }
  
  let allTouchpoints: Touchpoint[] = [];
  let loading = false;
  let selectedTouchpoint: string | null = null;
  let filterType = 'all';
  let sortBy: 'date' | 'satisfaction' | 'impact' = 'date';
  let showCreateForm = false;
  let newTouchpoint = {
    touchpoint_type: 'client_checkin',
    title: '',
    summary: '',
    participants: [],
    duration_minutes: 30
  };
  
  const touchpointTypes = [
    { id: 'all', label: 'All Types', icon: '📋', color: 'gray' },
    { id: 'agent_interaction', label: 'Agent Interaction', icon: '🤖', color: 'blue' },
    { id: 'client_checkin', label: 'Client Check-in', icon: '👥', color: 'green' },
    { id: 'milestone_review', label: 'Milestone Review', icon: '🎯', color: 'purple' },
    { id: 'status_update', label: 'Status Update', icon: '📊', color: 'yellow' },
    { id: 'decision_point', label: 'Decision Point', icon: '⚖️', color: 'orange' },
    { id: 'quality_gate', label: 'Quality Gate', icon: '✅', color: 'green' },
    { id: 'escalation', label: 'Escalation', icon: '🚨', color: 'red' }
  ];
  
  const agentProfiles = {
    'Marcus PM': { avatar: '👨‍💼', color: 'blue' },
    'Sara UX Designer': { avatar: '👩‍🎨', color: 'purple' },
    'Baccio Tech Architect': { avatar: '👨‍💻', color: 'green' },
    'Dan Engineer': { avatar: '👨‍🔧', color: 'orange' },
    'Thor QA Guardian': { avatar: '⚡', color: 'red' },
    'Ali Chief of Staff': { avatar: '🎯', color: 'indigo' },
    'Client': { avatar: '🏢', color: 'gray' }
  };
  
  onMount(async () => {
    allTouchpoints = touchpoints;
    if (orchestrationId && (!touchpoints || touchpoints.length === 0)) {
      await loadTouchpoints();
    }
  });
  
  async function loadTouchpoints() {
    loading = true;
    
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:9000';
      const response = await fetch(`${apiUrl}/api/v1/pm/orchestration/projects/${orchestrationId}/touchpoints`);
      
      if (response.ok) {
        const data = await response.json();
        allTouchpoints = data.touchpoints || [];
      } else {
        // Fallback to mock data
        allTouchpoints = generateMockTouchpoints();
      }
    } catch (error) {
      console.error('Error loading touchpoints:', error);
      allTouchpoints = generateMockTouchpoints();
    } finally {
      loading = false;
    }
  }
  
  function generateMockTouchpoints(): Touchpoint[] {
    return [
      {
        id: '1',
        touchpoint_type: 'client_checkin',
        title: 'Weekly Progress Review',
        summary: 'Reviewed current sprint progress and upcoming milestones with the client team.',
        initiated_by: 'Marcus PM',
        participants: ['Marcus PM', 'Sara UX Designer', 'Client'],
        interaction_date: '2024-02-14T14:00:00Z',
        duration_minutes: 45,
        satisfaction_score: 0.92,
        productivity_score: 0.88,
        key_decisions: ['Approved design direction', 'Extended timeline by 2 days'],
        action_items: ['Sara to refine wireframes', 'Marcus to update project timeline'],
        impact_level: 'high',
        related_stage: 'execution'
      },
      {
        id: '2',
        touchpoint_type: 'agent_interaction',
        title: 'Design System Architecture Discussion',
        summary: 'Technical discussion about design system implementation and component library structure.',
        initiated_by: 'Baccio Tech Architect',
        participants: ['Baccio Tech Architect', 'Sara UX Designer'],
        interaction_date: '2024-02-13T10:30:00Z',
        duration_minutes: 60,
        satisfaction_score: 0.88,
        productivity_score: 0.95,
        key_decisions: ['Use Storybook for component documentation', 'Implement atomic design methodology'],
        action_items: ['Baccio to set up component library', 'Sara to create design tokens'],
        impact_level: 'medium',
        related_stage: 'execution'
      },
      {
        id: '3',
        touchpoint_type: 'milestone_review',
        title: 'Sprint 3 Milestone Review',
        summary: 'End of sprint review covering completed features, challenges, and next sprint planning.',
        initiated_by: 'Marcus PM',
        participants: ['Marcus PM', 'Dan Engineer', 'Thor QA Guardian'],
        interaction_date: '2024-02-12T16:00:00Z',
        duration_minutes: 90,
        satisfaction_score: 0.85,
        productivity_score: 0.82,
        key_decisions: ['Prioritize performance optimization', 'Add automated testing'],
        action_items: ['Dan to optimize API responses', 'Thor to implement test suite'],
        impact_level: 'high',
        related_stage: 'execution'
      },
      {
        id: '4',
        touchpoint_type: 'quality_gate',
        title: 'Security Review Checkpoint',
        summary: 'Security assessment and approval for the authentication system implementation.',
        initiated_by: 'Thor QA Guardian',
        participants: ['Thor QA Guardian', 'Baccio Tech Architect', 'Dan Engineer'],
        interaction_date: '2024-02-11T09:00:00Z',
        duration_minutes: 75,
        satisfaction_score: 0.91,
        productivity_score: 0.89,
        key_decisions: ['Approved authentication flow', 'Required additional encryption'],
        action_items: ['Dan to implement 2FA', 'Baccio to review security protocols'],
        impact_level: 'high',
        related_stage: 'validation'
      }
    ];
  }
  
  function getTouchpointConfig(type: string) {
    return touchpointTypes.find(t => t.id === type) || touchpointTypes[0];
  }
  
  function getAgentProfile(agentName: string) {
    return agentProfiles[agentName] || { avatar: '🤖', color: 'gray' };
  }
  
  function getImpactColor(level: string): string {
    switch (level) {
      case 'critical': return 'bg-red-100 text-red-800 border-red-300';
      case 'high': return 'bg-orange-100 text-orange-800 border-orange-300';
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'low': return 'bg-green-100 text-green-800 border-green-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  }
  
  function getSatisfactionColor(score: number): string {
    if (score >= 0.9) return 'text-green-600';
    if (score >= 0.8) return 'text-blue-600';
    if (score >= 0.7) return 'text-yellow-600';
    return 'text-red-600';
  }
  
  function getSatisfactionEmoji(score: number): string {
    if (score >= 0.9) return '😍';
    if (score >= 0.8) return '😊';
    if (score >= 0.7) return '🙂';
    if (score >= 0.6) return '😐';
    return '😞';
  }
  
  function formatDate(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }
  
  function getRelativeTime(dateString: string): string {
    const date = new Date(dateString);
    const now = new Date();
    const diffHours = Math.abs(now.getTime() - date.getTime()) / (1000 * 60 * 60);
    
    if (diffHours < 1) return 'Just now';
    if (diffHours < 24) return `${Math.floor(diffHours)} hours ago`;
    const diffDays = Math.floor(diffHours / 24);
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    return formatDate(dateString);
  }
  
  function sortTouchpoints(touchpoints: Touchpoint[], sortBy: string): Touchpoint[] {
    return [...touchpoints].sort((a, b) => {
      switch (sortBy) {
        case 'date':
          return new Date(b.interaction_date).getTime() - new Date(a.interaction_date).getTime();
        case 'satisfaction':
          return (b.satisfaction_score || 0) - (a.satisfaction_score || 0);
        case 'impact':
          const impactOrder = { critical: 4, high: 3, medium: 2, low: 1 };
          return (impactOrder[b.impact_level] || 0) - (impactOrder[a.impact_level] || 0);
        default:
          return 0;
      }
    });
  }
  
  function filterTouchpoints(touchpoints: Touchpoint[], filterType: string): Touchpoint[] {
    if (filterType === 'all') return touchpoints;
    return touchpoints.filter(tp => tp.touchpoint_type === filterType);
  }
  
  async function createTouchpoint() {
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:9000';
      const response = await fetch(`${apiUrl}/api/v1/pm/orchestration/projects/${orchestrationId}/touchpoints`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newTouchpoint)
      });
      
      if (response.ok) {
        await loadTouchpoints();
        showCreateForm = false;
        resetForm();
      }
    } catch (error) {
      console.error('Error creating touchpoint:', error);
    }
  }
  
  function resetForm() {
    newTouchpoint = {
      touchpoint_type: 'client_checkin',
      title: '',
      summary: '',
      participants: [],
      duration_minutes: 30
    };
  }
  
  $: filteredAndSortedTouchpoints = sortTouchpoints(filterTouchpoints(allTouchpoints, filterType), sortBy);
</script>

<!-- Touchpoint Timeline -->
<Card>
  <div class="p-4">
    <!-- Header -->
    <div class="flex items-center justify-between mb-4">
      <div>
        <h3 class="text-lg font-semibold text-surface-900 ">
          📞 Touchpoint Timeline
        </h3>
        {#if !compact}
          <p class="text-sm text-surface-600  mt-1">
            CRM-style interaction history and collaboration analytics
          </p>
        {/if}
      </div>
      
      {#if !compact}
        <div class="flex items-center space-x-2">
          <!-- Filter and Sort Controls -->
          <select 
            bind:value={filterType}
            class="text-sm border border-surface-300  rounded-md px-2 py-1 
                   bg-surface-50  text-surface-900 "
          >
            {#each touchpointTypes as type}
              <option value={type.id}>{type.icon} {type.label}</option>
            {/each}
          </select>
          
          <select 
            bind:value={sortBy}
            class="text-sm border border-surface-300  rounded-md px-2 py-1 
                   bg-surface-50  text-surface-900 "
          >
            <option value="date">Sort by Date</option>
            <option value="satisfaction">Sort by Satisfaction</option>
            <option value="impact">Sort by Impact</option>
          </select>
          
          <Button variant="primary" size="sm" on:click={() => showCreateForm = true}>
            + Add Touchpoint
          </Button>
        </div>
      {/if}
    </div>
    
    <!-- Create Touchpoint Form -->
    {#if showCreateForm}
      <div class="bg-surface-50  rounded-lg p-4 mb-4" transition:slide>
        <div class="flex items-center justify-between mb-3">
          <h4 class="font-medium text-surface-900 ">Create New Touchpoint</h4>
          <button on:click={() => showCreateForm = false} class="text-surface-400 hover:text-surface-600">✕</button>
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div>
            <label class="block text-sm font-medium text-surface-700  mb-1">Type</label>
            <select 
              bind:value={newTouchpoint.touchpoint_type}
              class="w-full border border-surface-300  rounded-md px-3 py-2 
                     bg-surface-50  text-surface-900 "
            >
              {#each touchpointTypes.slice(1) as type}
                <option value={type.id}>{type.icon} {type.label}</option>
              {/each}
            </select>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-surface-700  mb-1">Duration (minutes)</label>
            <input 
              type="number" 
              bind:value={newTouchpoint.duration_minutes}
              class="w-full border border-surface-300  rounded-md px-3 py-2 
                     bg-surface-50  text-surface-900 "
            />
          </div>
          
          <div class="md:col-span-2">
            <label class="block text-sm font-medium text-surface-700  mb-1">Title</label>
            <input 
              type="text" 
              bind:value={newTouchpoint.title}
              placeholder="Touchpoint title..."
              class="w-full border border-surface-300  rounded-md px-3 py-2 
                     bg-surface-50  text-surface-900 "
            />
          </div>
          
          <div class="md:col-span-2">
            <label class="block text-sm font-medium text-surface-700  mb-1">Summary</label>
            <textarea 
              bind:value={newTouchpoint.summary}
              placeholder="Brief summary of the interaction..."
              rows="2"
              class="w-full border border-surface-300  rounded-md px-3 py-2 
                     bg-surface-50  text-surface-900 "
            ></textarea>
          </div>
        </div>
        
        <div class="flex justify-end space-x-2 mt-3">
          <Button variant="outline" size="sm" on:click={() => showCreateForm = false}>
            Cancel
          </Button>
          <Button variant="primary" size="sm" on:click={createTouchpoint}>
            Create Touchpoint
          </Button>
        </div>
      </div>
    {/if}
    
    <!-- Summary Stats -->
    {#if !compact && filteredAndSortedTouchpoints.length > 0}
      <div class="grid grid-cols-1 md:grid-cols-4 gap-3 mb-4">
        <div class="bg-blue-50 rounded-lg p-3">
          <div class="text-sm text-blue-600 font-medium">Total Touchpoints</div>
          <div class="text-xl font-bold text-blue-700">
            {filteredAndSortedTouchpoints.length}
          </div>
        </div>
        
        <div class="bg-green-50 rounded-lg p-3">
          <div class="text-sm text-green-600 font-medium">Avg Satisfaction</div>
          <div class="text-xl font-bold text-green-700">
            {Math.round((filteredAndSortedTouchpoints.reduce((sum, tp) => sum + (tp.satisfaction_score || 0), 0) / 
                       Math.max(filteredAndSortedTouchpoints.length, 1)) * 100)}%
          </div>
        </div>
        
        <div class="bg-purple-50 rounded-lg p-3">
          <div class="text-sm text-purple-600 font-medium">Total Duration</div>
          <div class="text-xl font-bold text-purple-700">
            {Math.round(filteredAndSortedTouchpoints.reduce((sum, tp) => sum + (tp.duration_minutes || 0), 0) / 60)}h
          </div>
        </div>
        
        <div class="bg-yellow-50 rounded-lg p-3">
          <div class="text-sm text-yellow-600 font-medium">High Impact</div>
          <div class="text-xl font-bold text-yellow-700">
            {filteredAndSortedTouchpoints.filter(tp => tp.impact_level === 'high' || tp.impact_level === 'critical').length}
          </div>
        </div>
      </div>
    {/if}
    
    <!-- Timeline -->
    <div class="space-y-3 {compact ? 'max-h-64 overflow-y-auto' : ''}">
      {#if loading}
        <div class="text-center py-8">
          <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto"></div>
          <p class="text-sm text-surface-600  mt-2">Loading touchpoints...</p>
        </div>
      {:else if filteredAndSortedTouchpoints.length === 0}
        <div class="text-center py-8 text-surface-500 ">
          <div class="text-4xl mb-2">📞</div>
          <p>No touchpoints yet. Start tracking interactions to build the timeline.</p>
        </div>
      {:else}
        {#each filteredAndSortedTouchpoints as touchpoint (touchpoint.id)}
          <div class="relative pl-6 border-l-2 border-surface-200  pb-4 last:pb-0">
            <!-- Timeline dot -->
            <div class="absolute -left-2 top-1 w-4 h-4 rounded-full bg-{getTouchpointConfig(touchpoint.touchpoint_type).color}-500 border-2 border-white"></div>
            
            <!-- Touchpoint card -->
            <div class="bg-surface-50  rounded-lg p-3 hover:shadow-md transition-shadow">
              <div class="flex items-start justify-between">
                <div class="flex-1">
                  <!-- Header -->
                  <div class="flex items-center space-x-2 mb-2">
                    <span class="text-lg">{getTouchpointConfig(touchpoint.touchpoint_type).icon}</span>
                    <h4 class="font-medium text-surface-900 ">
                      {touchpoint.title}
                    </h4>
                    <Badge class="{getImpactColor(touchpoint.impact_level)}">
                      {touchpoint.impact_level}
                    </Badge>
                  </div>
                  
                  <!-- Summary -->
                  {#if touchpoint.summary && !compact}
                    <p class="text-sm text-surface-700  mb-2">
                      {touchpoint.summary}
                    </p>
                  {/if}
                  
                  <!-- Participants -->
                  <div class="flex items-center space-x-2 mb-2">
                    <span class="text-xs text-surface-500">Participants:</span>
                    <div class="flex space-x-1">
                      {#each touchpoint.participants as participant}
                        <div class="flex items-center space-x-1 bg-surface-100  rounded px-2 py-1">
                          <span class="text-sm">{getAgentProfile(participant).avatar}</span>
                          <span class="text-xs font-medium text-surface-700 ">
                            {participant}
                          </span>
                        </div>
                      {/each}
                    </div>
                  </div>
                  
                  <!-- Metrics -->
                  <div class="flex items-center space-x-4 text-xs text-surface-600 ">
                    <span>{getRelativeTime(touchpoint.interaction_date)}</span>
                    {#if touchpoint.duration_minutes}
                      <span>{touchpoint.duration_minutes} min</span>
                    {/if}
                    {#if touchpoint.satisfaction_score}
                      <span class="flex items-center space-x-1">
                        <span>{getSatisfactionEmoji(touchpoint.satisfaction_score)}</span>
                        <span class="{getSatisfactionColor(touchpoint.satisfaction_score)}">
                          {Math.round(touchpoint.satisfaction_score * 100)}%
                        </span>
                      </span>
                    {/if}
                  </div>
                </div>
                
                <!-- Expand button -->
                {#if !compact}
                  <button
                    on:click={() => selectedTouchpoint = selectedTouchpoint === touchpoint.id ? null : touchpoint.id}
                    class="text-surface-400 hover:text-surface-600 p-1"
                  >
                    {selectedTouchpoint === touchpoint.id ? '▲' : '▼'}
                  </button>
                {/if}
              </div>
              
              <!-- Expanded details -->
              {#if selectedTouchpoint === touchpoint.id}
                <div class="mt-3 pt-3 border-t border-surface-200 " transition:slide>
                  <!-- Key Decisions -->
                  {#if touchpoint.key_decisions && touchpoint.key_decisions.length > 0}
                    <div class="mb-3">
                      <h5 class="text-sm font-medium text-surface-900  mb-1">
                        🎯 Key Decisions
                      </h5>
                      <ul class="space-y-1">
                        {#each touchpoint.key_decisions as decision}
                          <li class="text-sm text-surface-700  flex items-start">
                            <span class="text-green-500 mr-2">•</span>
                            {decision}
                          </li>
                        {/each}
                      </ul>
                    </div>
                  {/if}
                  
                  <!-- Action Items -->
                  {#if touchpoint.action_items && touchpoint.action_items.length > 0}
                    <div class="mb-3">
                      <h5 class="text-sm font-medium text-surface-900  mb-1">
                        ✅ Action Items
                      </h5>
                      <ul class="space-y-1">
                        {#each touchpoint.action_items as action}
                          <li class="text-sm text-surface-700  flex items-start">
                            <span class="text-blue-500 mr-2">→</span>
                            {action}
                          </li>
                        {/each}
                      </ul>
                    </div>
                  {/if}
                  
                  <!-- Performance Metrics -->
                  {#if touchpoint.productivity_score}
                    <div class="grid grid-cols-2 gap-3 text-sm">
                      <div>
                        <span class="text-surface-500">Productivity Score:</span>
                        <span class="font-medium {getSatisfactionColor(touchpoint.productivity_score)}">
                          {Math.round(touchpoint.productivity_score * 100)}%
                        </span>
                      </div>
                      {#if touchpoint.related_stage}
                        <div>
                          <span class="text-surface-500">Related Stage:</span>
                          <span class="font-medium text-surface-700  capitalize">
                            {touchpoint.related_stage}
                          </span>
                        </div>
                      {/if}
                    </div>
                  {/if}
                </div>
              {/if}
            </div>
          </div>
        {/each}
      {/if}
    </div>
  </div>
</Card>

<style>
  /* Smooth transitions */
  .transition-shadow {
    transition: box-shadow 0.2s ease-in-out;
  }
  
  /* Loading animation */
  .animate-spin {
    animation: spin 1s linear infinite;
  }
  
  @keyframes spin {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
    }
  }
  
  /* Custom scrollbar for compact mode */
  .overflow-y-auto::-webkit-scrollbar {
    width: 6px;
  }
  
  .overflow-y-auto::-webkit-scrollbar-track {
    background: transparent;
  }
  
  .overflow-y-auto::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 3px;
  }
  
  .overflow-y-auto::-webkit-scrollbar-thumb:hover {
    background: #94a3b8;
  }
</style>