<script lang="ts">
  import { onMount } from 'svelte';
  import { Card, Badge, Button } from '$lib/components/ui';
  import { scale, slide } from 'svelte/transition';
  
  export let journeyStages: any[] = [];
  export let currentStage: string = '';
  export let detailed: boolean = false;
  
  interface JourneyStage {
    stage_name: string;
    status: string;
    progress_percentage: number;
    satisfaction_score: number;
    start_date: string;
    end_date?: string;
    primary_agents: string[];
    deliverables?: string[];
    blockers?: string[];
  }
  
  type StageColor = 'blue' | 'yellow' | 'green' | 'purple' | 'indigo' | 'gray';
  type StageName = 'discovery' | 'planning' | 'execution' | 'validation' | 'delivery' | 'closure';

  // Stage definitions with icons and descriptions
  const stageDefinitions: Record<StageName, {
    icon: string;
    title: string;
    description: string;
    color: StageColor;
    expectedDuration: string;
  }> = {
    discovery: {
      icon: '🔍',
      title: 'Discovery',
      description: 'Requirements gathering and stakeholder analysis',
      color: 'blue',
      expectedDuration: '1-2 weeks'
    },
    planning: {
      icon: '📋',
      title: 'Planning',
      description: 'Project planning and architecture design',
      color: 'yellow',
      expectedDuration: '1-3 weeks'
    },
    execution: {
      icon: '⚡',
      title: 'Execution',
      description: 'Development and implementation',
      color: 'green',
      expectedDuration: '4-8 weeks'
    },
    validation: {
      icon: '✅',
      title: 'Validation',
      description: 'Testing and quality assurance',
      color: 'purple',
      expectedDuration: '1-2 weeks'
    },
    delivery: {
      icon: '🚀',
      title: 'Delivery',
      description: 'Deployment and go-live activities',
      color: 'indigo',
      expectedDuration: '1 week'
    },
    closure: {
      icon: '🎯',
      title: 'Closure',
      description: 'Project wrap-up and documentation',
      color: 'gray',
      expectedDuration: '1 week'
    }
  };
  
  let selectedStage: string | null = null;
  let stageTimeline: any[] = [];
  
  onMount(() => {
    buildStageTimeline();
  });
  
  function buildStageTimeline() {
    const stages = Object.keys(stageDefinitions) as StageName[];
    stageTimeline = stages.map(stageName => {
      const stageData = journeyStages.find(s => s.stage_name === stageName);
      const definition = stageDefinitions[stageName];

      return {
        name: stageName,
        ...definition,
        data: stageData,
        isActive: stageName === currentStage,
        isCompleted: stageData?.status === 'completed',
        isPending: !stageData || stageData.status === 'pending',
        isBlocked: stageData?.status === 'blocked'
      };
    });
  }
  
  function getStageProgress(stage: any): number {
    if (stage.isCompleted) return 100;
    if (stage.data?.progress_percentage) return stage.data.progress_percentage;
    if (stage.isActive) return 50; // Default for active stage
    return 0;
  }
  
  function getStageColorClasses(stage: any, type: 'bg' | 'border' | 'text' = 'bg') {
    const baseColors: Record<StageColor, { bg: string; border: string; text: string }> = {
      blue: { bg: 'bg-blue-500', border: 'border-blue-500', text: 'text-blue-600' },
      yellow: { bg: 'bg-yellow-500', border: 'border-yellow-500', text: 'text-yellow-600' },
      green: { bg: 'bg-green-500', border: 'border-green-500', text: 'text-green-600' },
      purple: { bg: 'bg-purple-500', border: 'border-purple-500', text: 'text-purple-600' },
      indigo: { bg: 'bg-indigo-500', border: 'border-indigo-500', text: 'text-indigo-600' },
      gray: { bg: 'bg-gray-500', border: 'border-gray-500', text: 'text-gray-600' }
    };

    if (stage.isBlocked) {
      return type === 'bg' ? 'bg-red-500' : type === 'border' ? 'border-red-500' : 'text-red-600';
    }

    if (stage.isCompleted) {
      return baseColors[stage.color as StageColor][type];
    }

    if (stage.isActive) {
      return type === 'bg' ? `${baseColors[stage.color as StageColor][type]} animate-pulse` : baseColors[stage.color as StageColor][type];
    }

    return type === 'bg' ? 'bg-gray-300' : type === 'border' ? 'border-gray-300' : 'text-gray-500';
  }
  
  function formatDate(dateString: string): string {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  }
  
  function getSatisfactionEmoji(score: number): string {
    if (score >= 0.9) return '😍';
    if (score >= 0.8) return '😊';
    if (score >= 0.7) return '🙂';
    if (score >= 0.6) return '😐';
    return '😞';
  }
  
  $: {
    if (journeyStages) {
      buildStageTimeline();
    }
  }
</script>

<!-- Project Journey Visualization -->
<Card>
  <div class="p-6">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h3 class="text-lg font-semibold text-surface-900 ">
          🛤️ Project Journey
        </h3>
        <p class="text-sm text-surface-600  mt-1">
          CRM-style project progression with AI insights
        </p>
      </div>
      
      {#if detailed}
        <div class="flex items-center space-x-2 text-sm">
          <span class="text-surface-500">Legend:</span>
          <div class="flex items-center space-x-1">
            <div class="w-3 h-3 bg-gray-300 rounded-full"></div>
            <span class="text-xs text-surface-600">Pending</span>
          </div>
          <div class="flex items-center space-x-1">
            <div class="w-3 h-3 bg-blue-500 rounded-full animate-pulse"></div>
            <span class="text-xs text-surface-600">Active</span>
          </div>
          <div class="flex items-center space-x-1">
            <div class="w-3 h-3 bg-green-500 rounded-full"></div>
            <span class="text-xs text-surface-600">Completed</span>
          </div>
          <div class="flex items-center space-x-1">
            <div class="w-3 h-3 bg-red-500 rounded-full"></div>
            <span class="text-xs text-surface-600">Blocked</span>
          </div>
        </div>
      {/if}
    </div>
    
    <!-- Journey Timeline -->
    <div class="relative">
      <!-- Progress Line -->
      <div class="absolute top-12 left-8 right-8 h-0.5 bg-gray-200"></div>
      
      <!-- Journey Stages -->
      <div class="flex justify-between relative">
        {#each stageTimeline as stage, index}
          <div class="flex flex-col items-center relative" style="z-index: 10;">
            <!-- Stage Circle -->
            <button
              on:click={() => selectedStage = selectedStage === stage.name ? null : stage.name}
              class="w-16 h-16 rounded-full border-4 {getStageColorClasses(stage, 'border')} 
                     bg-surface-50  hover:scale-110 transition-all duration-200 
                     flex items-center justify-center text-2xl shadow-lg hover:shadow-xl"
              class:ring-4={stage.isActive}
              class:ring-blue-200={stage.isActive}
            >
              {stage.icon}
            </button>
            
            <!-- Stage Name and Status -->
            <div class="mt-2 text-center min-w-[120px]">
              <div class="font-medium text-sm text-surface-900 ">
                {stage.title}
              </div>
              
              <!-- Progress Bar -->
              {#if !detailed}
                <div class="mt-1 w-full bg-gray-200 rounded-full h-1.5">
                  <div 
                    class="h-1.5 rounded-full transition-all duration-500 {getStageColorClasses(stage, 'bg')}"
                    style="width: {getStageProgress(stage)}%"
                  ></div>
                </div>
                <div class="text-xs text-surface-500 mt-1">
                  {getStageProgress(stage)}%
                </div>
              {:else}
                <!-- Detailed Status -->
                <div class="mt-1">
                  {#if stage.data}
                    <Badge class="{stage.isCompleted ? 'bg-green-100 text-green-800' : 
                                  stage.isActive ? 'bg-blue-100 text-blue-800' : 
                                  stage.isBlocked ? 'bg-red-100 text-red-800' : 
                                  'bg-gray-100 text-gray-800'}">
                      {stage.data.status}
                    </Badge>
                    
                    <!-- Satisfaction Score -->
                    {#if stage.data.satisfaction_score}
                      <div class="flex items-center justify-center mt-1 text-xs">
                        <span class="mr-1">{getSatisfactionEmoji(stage.data.satisfaction_score)}</span>
                        <span class="text-surface-600">{Math.round(stage.data.satisfaction_score * 100)}%</span>
                      </div>
                    {/if}
                  {:else}
                    <Badge class="bg-gray-100 text-gray-600">Pending</Badge>
                  {/if}
                </div>
              {/if}
            </div>
            
            <!-- Stage Details (Expanded) -->
            {#if selectedStage === stage.name}
              <div 
                class="absolute top-20 left-1/2 transform -translate-x-1/2 mt-4 bg-surface-50  
                       border border-surface-200  rounded-lg p-4 shadow-lg min-w-[280px] z-20"
                transition:scale={{ duration: 200 }}
              >
                <!-- Close Button -->
                <button
                  on:click={() => selectedStage = null}
                  class="absolute top-2 right-2 text-surface-400 hover:text-surface-600"
                >
                  ✕
                </button>
                
                <div class="space-y-3">
                  <!-- Stage Header -->
                  <div class="flex items-center space-x-2">
                    <span class="text-2xl">{stage.icon}</span>
                    <div>
                      <h4 class="font-semibold text-surface-900 ">
                        {stage.title}
                      </h4>
                      <p class="text-xs text-surface-600 ">
                        {stage.description}
                      </p>
                    </div>
                  </div>
                  
                  <!-- Stage Metrics -->
                  {#if stage.data}
                    <div class="grid grid-cols-2 gap-3 text-sm">
                      <div>
                        <span class="text-surface-500">Progress:</span>
                        <div class="font-medium {getStageColorClasses(stage, 'text')}">
                          {stage.data.progress_percentage}%
                        </div>
                      </div>
                      
                      {#if stage.data.satisfaction_score}
                        <div>
                          <span class="text-surface-500">Satisfaction:</span>
                          <div class="font-medium flex items-center">
                            <span class="mr-1">{getSatisfactionEmoji(stage.data.satisfaction_score)}</span>
                            {Math.round(stage.data.satisfaction_score * 100)}%
                          </div>
                        </div>
                      {/if}
                      
                      {#if stage.data.start_date}
                        <div>
                          <span class="text-surface-500">Started:</span>
                          <div class="font-medium">{formatDate(stage.data.start_date)}</div>
                        </div>
                      {/if}
                      
                      <div>
                        <span class="text-surface-500">Duration:</span>
                        <div class="font-medium text-surface-600">{stage.expectedDuration}</div>
                      </div>
                    </div>
                  {:else}
                    <div class="text-sm text-surface-600 ">
                      <p class="mb-2">Expected Duration: <span class="font-medium">{stage.expectedDuration}</span></p>
                      <p class="text-xs">{stage.description}</p>
                    </div>
                  {/if}
                  
                  <!-- Primary Agents -->
                  {#if stage.data?.primary_agents && stage.data.primary_agents.length > 0}
                    <div>
                      <span class="text-sm text-surface-500">Primary Agents:</span>
                      <div class="flex flex-wrap gap-1 mt-1">
                        {#each stage.data.primary_agents as agent}
                          <Badge class="bg-blue-100 text-blue-800 text-xs">
                            🤖 {agent}
                          </Badge>
                        {/each}
                      </div>
                    </div>
                  {/if}
                  
                  <!-- Blockers (if any) -->
                  {#if stage.isBlocked && stage.data?.blockers}
                    <div class="bg-red-50 border border-red-200 rounded p-2">
                      <span class="text-sm font-medium text-red-800">⚠️ Blockers:</span>
                      <ul class="text-xs text-red-700 mt-1 space-y-1">
                        {#each stage.data.blockers as blocker}
                          <li>• {blocker}</li>
                        {/each}
                      </ul>
                    </div>
                  {/if}
                </div>
              </div>
            {/if}
          </div>
        {/each}
      </div>
    </div>
    
    <!-- Overall Journey Metrics (Detailed View) -->
    {#if detailed}
      <div class="mt-8 pt-6 border-t border-surface-200 ">
        <h4 class="font-medium text-surface-900  mb-4">Journey Analytics</h4>
        
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
          <!-- Overall Progress -->
          <div class="bg-blue-50 rounded-lg p-3">
            <div class="text-sm text-blue-600 font-medium">Overall Progress</div>
            <div class="text-2xl font-bold text-blue-700">
              {Math.round((stageTimeline.filter(s => s.isCompleted).length / stageTimeline.length) * 100)}%
            </div>
            <div class="text-xs text-blue-600">
              {stageTimeline.filter(s => s.isCompleted).length} of {stageTimeline.length} stages complete
            </div>
          </div>
          
          <!-- Average Satisfaction -->
          <div class="bg-purple-50 rounded-lg p-3">
            <div class="text-sm text-purple-600 font-medium">Avg Satisfaction</div>
            <div class="text-2xl font-bold text-purple-700">
              {Math.round((journeyStages.reduce((sum, stage) => sum + (stage.satisfaction_score || 0), 0) / 
                         Math.max(journeyStages.length, 1)) * 100)}%
            </div>
            <div class="text-xs text-purple-600">
              Across completed stages
            </div>
          </div>
          
          <!-- Active Stage Progress -->
          <div class="bg-green-50 rounded-lg p-3">
            <div class="text-sm text-green-600 font-medium">Current Stage</div>
            <div class="text-lg font-bold text-green-700">
              {currentStage.charAt(0).toUpperCase() + currentStage.slice(1)}
            </div>
            <div class="text-xs text-green-600">
              {getStageProgress(stageTimeline.find(s => s.isActive))}% complete
            </div>
          </div>
          
          <!-- Journey Velocity -->
          <div class="bg-yellow-50 rounded-lg p-3">
            <div class="text-sm text-yellow-600 font-medium">Velocity</div>
            <div class="text-2xl font-bold text-yellow-700">Normal</div>
            <div class="text-xs text-yellow-600">
              On track for delivery
            </div>
          </div>
        </div>
      </div>
    {/if}
  </div>
</Card>

<style>
  /* Pulse animation for active stage */
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
  
  /* Smooth hover transitions */
  .transition-all {
    transition: all 0.2s ease-in-out;
  }
  
  /* Progress bar animation */
  .h-1\.5 {
    transition: width 0.5s ease-in-out;
  }
</style>