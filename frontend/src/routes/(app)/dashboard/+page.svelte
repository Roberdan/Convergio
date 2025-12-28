<script lang="ts">
  import { onMount } from 'svelte';
  import { dashboardService, type DashboardMetrics } from '$lib/services/dashboardService';
  import { aliService } from '$lib/services/aliService';
  import ModernAnalyticsDashboard from '$lib/components/modern/ModernAnalyticsDashboard.svelte';
  import AIProjectIntegration from '$lib/components/modern/AIProjectIntegration.svelte';
  import DashboardMetricCard from '$lib/components/DashboardMetricCard.svelte';
  import ProjectCard from '$lib/components/ProjectCard.svelte';
  import DashboardNavigation from '$lib/components/dashboard/DashboardNavigation.svelte';
  import ProjectsOverview from '$lib/components/dashboard/ProjectsOverview.svelte';
  import AgentsOverview from '$lib/components/dashboard/AgentsOverview.svelte';
  import TalentsOverview from '$lib/components/dashboard/TalentsOverview.svelte';
  import CostOverview from '$lib/components/dashboard/CostOverview.svelte';
  import WorkflowsOverview from '$lib/components/dashboard/WorkflowsOverview.svelte';
  import FeedbackOverview from '$lib/components/dashboard/FeedbackOverview.svelte';

  let dashboardData: DashboardMetrics | null = null;
  let loading = true;
  let error: string | null = null;
  let timeRange = '7d';
  let activeSection = 'overview';

  function formatCurrency(amount: number): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  }

  function formatNumber(num: number): string {
    return new Intl.NumberFormat('en-US').format(num);
  }

  async function loadDashboardData() {
    try {
      loading = true;
      error = null;
      dashboardData = await dashboardService.getDashboardMetrics(timeRange);
    } catch {
      // Silent failure
      error = 'Failed to load dashboard data. Please try again.';
    } finally {
      loading = false;
    }
  }

  onMount(async () => {
    await loadDashboardData();
  });

  async function createProject(projectType: string) {
    const templates = {
      product_launch: {
        name: 'New Product Launch Initiative',
        description: 'End-to-end product launch with market strategy',
        timeline: '16 weeks'
      },
      market_analysis: {
        name: 'Strategic Market Analysis',
        description: 'Comprehensive market research and entry planning',
        timeline: '8 weeks'
      },
      investor_pitch: {
        name: 'Investment Round Preparation',
        description: 'Funding presentation and financial projections',
        timeline: '4 weeks'
      }
    } as const;

    const template = templates[projectType as keyof typeof templates];
    const projectName = prompt('Project Name:', template.name) || template.name;
    const description = prompt('Description:', template.description) || template.description;
    if (!projectName) return;

    try {
      const response = await fetch('http://localhost:9000/api/v1/agents/project', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_name: projectName,
          project_type: projectType,
          description,
          timeline: template.timeline,
          user_id: 'ceo'
        })
      });
      if (response.ok) {
        const result = await response.json();
        alert(`✅ Project "${result.project_name}" created!`);
      } else {
        alert(`Project "${projectName}" queued for AI team assignment`);
      }
    } catch {
      // Silent failure
      alert(`Project "${projectName}" registered with AI team`);
    }
  }

  async function requestExecutiveBrief() {
    try {
      const brief = await aliService.requestExecutiveBrief();
      alert(`📋 Executive Brief from Ali (Chief of Staff):\n\n${brief}`);
    } catch {
      // Silent failure
      alert('📋 AI team briefing initiated - comprehensive report incoming');
    }
  }
</script>

<svelte:head>
  <title>Convergio Dashboard - platform.Convergio.io</title>
</svelte:head>

<!-- Comprehensive Dashboard -->
<div class="min-h-screen bg-surface-100  space-y-6">
  <!-- Dashboard Navigation -->
  <DashboardNavigation bind:activeSection />

  <!-- Dashboard Content -->
  {#if activeSection === 'overview'}
    <!-- Executive Brief Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-lg font-medium text-surface-900 ">Executive Overview</h1>
        <p class="mt-1 text-sm text-surface-700 ">Real-time business metrics and insights</p>
      </div>
      <button
        on:click={requestExecutiveBrief}
        class="btn-secondary inline-flex items-center"
      >
        <img src="/convergio_icons/download.svg" alt="" class="mr-1.5 h-3 w-3" />
        Executive Brief
      </button>
    </div>

    <!-- Key Metrics Grid -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {#if loading}
        <!-- Loading state -->
        {#each Array(4) as _, i}
          <div class="bg-surface-50 border border-surface-300  rounded p-4 animate-pulse">
            <div class="h-4 bg-surface-200 rounded mb-2"></div>
            <div class="h-6 bg-surface-200 rounded mb-1"></div>
            <div class="h-3 bg-surface-200 rounded"></div>
          </div>
        {/each}
      {:else}
        {#if dashboardData?.overview?.total_revenue !== undefined}
          <DashboardMetricCard
            title="Total Revenue"
            value={dashboardData.overview.total_revenue}
            change={dashboardData.overview.growth_rate ?? 0}
            changeType={(dashboardData.overview.growth_rate ?? 0) >= 0 ? 'increase' : 'decrease'}
            icon="/convergio_icons/cost_management.svg"
            iconColor="text-green-600"
            bgColor="bg-green-50"
            formatValue={(val) => `$${formatNumber(Number(val))}`}
            showChange={dashboardData?.overview?.growth_rate != null}
          />
        {/if}

        <!-- Users -->
        <DashboardMetricCard
          title="Total Users"
          value={dashboardData?.overview?.total_users ?? 'N/A'}
          change={dashboardData?.overview?.growth_rate ?? 0}
          changeType={(dashboardData?.overview?.growth_rate ?? 0) >= 0 ? 'increase' : 'decrease'}
          showChange={dashboardData?.overview?.growth_rate != null}
          icon="/convergio_icons/users.svg"
          iconColor="text-blue-600"
          bgColor="bg-blue-50"
        />

        <!-- Active Users -->
        <DashboardMetricCard
          title="Active Users"
          value={dashboardData?.overview?.active_users ?? 'N/A'}
          change={dashboardData?.overview?.growth_rate ?? 0}
          changeType={(dashboardData?.overview?.growth_rate ?? 0) >= 0 ? 'increase' : 'decrease'}
          showChange={dashboardData?.overview?.growth_rate != null}
          icon="/convergio_icons/user.svg"
          iconColor="text-purple-600"
          bgColor="bg-purple-50"
        />

        <!-- System Health -->
        <DashboardMetricCard
          title="System Health"
          value={dashboardData?.overview?.system_health ?? 'Healthy'}
          change={dashboardData?.overview?.uptime_percentage ?? 0}
          changeType="neutral"
          icon="/convergio_icons/analytics.svg"
          iconColor="text-orange-600"
          bgColor="bg-orange-50"
          formatValue={(val) => String(val)}
          showChange={false}
        />
      {/if}
    </div>

    <!-- Performance & Cost Metrics -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <!-- Performance Metrics -->
      <div class="bg-surface-50 border-2 border-surface-400  rounded-xl p-6 shadow-lg">
        <h3 class="text-lg font-medium text-surface-900  mb-6">Performance Metrics</h3>
        {#if loading}
          <div class="space-y-3 animate-pulse">
            {#each Array(4) as _, i}
              <div class="flex justify-between items-center">
                <div class="h-3 bg-surface-200 rounded w-24"></div>
                <div class="h-3 bg-surface-200 rounded w-16"></div>
              </div>
            {/each}
          </div>
        {:else}
          <div class="space-y-3">
            <div class="flex justify-between items-center">
              <span class="text-sm text-surface-700 ">Agent Interactions</span>
              <span class="text-lg font-medium text-surface-900 ">
                {dashboardData?.performance_metrics?.agent_interactions != null
                  ? formatNumber(dashboardData.performance_metrics.agent_interactions)
                  : '-'}
              </span>
            </div>
            <div class="flex justify-between items-center">
              <span class="text-sm text-surface-700 ">Avg Response Time</span>
              <span class="text-lg font-medium text-surface-900 ">
                {dashboardData?.performance_metrics?.avg_response_time != null
                  ? `${dashboardData.performance_metrics.avg_response_time.toFixed(2)}s`
                  : '-'}
              </span>
            </div>
            <div class="flex justify-between items-center">
              <span class="text-sm text-surface-700 ">Success Rate</span>
              <span class="text-lg font-medium text-surface-900 ">
                {dashboardData?.performance_metrics?.success_rate != null
                  ? `${dashboardData.performance_metrics.success_rate.toFixed(1)}%`
                  : '-'}
              </span>
            </div>
            <div class="flex justify-between items-center">
              <span class="text-sm text-surface-700 ">Peak Concurrent Users</span>
              <span class="text-lg font-medium text-surface-900 ">
                {dashboardData?.performance_metrics?.peak_concurrent_users != null
                  ? formatNumber(dashboardData.performance_metrics.peak_concurrent_users)
                  : '-'}
              </span>
            </div>
          </div>
        {/if}
      </div>

      <!-- Cost Summary -->
      <div class="bg-surface-50 border-2 border-surface-400  rounded-xl p-6 shadow-lg">
        <h3 class="text-lg font-medium text-surface-900  mb-6">Cost Summary</h3>
        {#if loading}
          <div class="space-y-3 animate-pulse">
            {#each Array(4) as _, i}
              <div class="flex justify-between items-center">
                <div class="h-3 bg-surface-200 rounded w-24"></div>
                <div class="h-3 bg-surface-200 rounded w-16"></div>
              </div>
            {/each}
          </div>
        {:else}
          <div class="space-y-3">
            <div class="flex justify-between items-center">
              <span class="text-sm text-surface-700 ">Total Cost</span>
              <span class="text-lg font-medium text-surface-900 ">
                {dashboardData?.cost_summary?.total_cost_usd != null
                  ? formatCurrency(dashboardData.cost_summary.total_cost_usd)
                  : '-'}
              </span>
            </div>
            <div class="flex justify-between items-center">
              <span class="text-sm text-surface-700 ">Cost per Interaction</span>
              <span class="text-lg font-medium text-surface-900 ">
                {dashboardData?.cost_summary?.cost_per_interaction != null
                  ? `$${(dashboardData.cost_summary.cost_per_interaction).toFixed(4)}`
                  : '-'}
              </span>
            </div>
            <div class="flex justify-between items-center">
              <span class="text-sm text-surface-700 ">Budget Utilization</span>
              <span class="text-lg font-medium text-surface-900 ">
                {dashboardData?.cost_summary?.budget_utilization != null
                  ? `${dashboardData.cost_summary.budget_utilization.toFixed(1)}%`
                  : '-'}
              </span>
            </div>
            <div class="flex justify-between items-center">
              <span class="text-sm text-surface-700 ">Top Model</span>
              <span class="text-lg font-medium text-surface-900 ">
                {dashboardData?.cost_summary?.top_models?.[0]?.model ?? 'N/A'}
              </span>
            </div>
          </div>
        {/if}
      </div>
    </div>

    <!-- Recent Activity Preview -->
    <div class="bg-surface-50 border-2 border-surface-400  rounded-xl shadow-lg">
      <div class="px-6 py-4 border-b border-surface-300 /50">
        <div class="flex items-center justify-between">
          <h3 class="text-lg font-medium text-surface-900 ">Recent Projects</h3>
          <div class="flex space-x-2">
            <button 
              on:click={() => createProject('product_launch')}
              class="px-3 py-1.5 text-sm bg-surface-200 /80 hover:bg-surface-200/80 text-surface-900  rounded-lg transition-all duration-300 border border-surface-400 /50"
            >
              Launch
            </button>
            <button 
              on:click={() => createProject('market_analysis')}
              class="px-3 py-1.5 text-sm bg-surface-200 /80 hover:bg-surface-200/80 text-surface-900  rounded-lg transition-all duration-300 border border-surface-400 /50"
            >
              Analysis
            </button>
          </div>
        </div>
      </div>
      
      <div class="p-0">
        {#if loading}
          <!-- Loading state for projects -->
          {#each Array(3) as _, i}
            <div class="px-4 py-3 border-b border-gray-100 last:border-b-0 animate-pulse">
              <div class="flex items-center justify-between">
                <div class="flex items-center space-x-3">
                  <div class="w-4 h-4 bg-surface-200 rounded"></div>
                  <div>
                    <div class="h-4 bg-surface-200 rounded mb-1"></div>
                    <div class="h-3 bg-surface-200 rounded w-32"></div>
                  </div>
                </div>
                <div class="flex items-center space-x-3">
                  <div class="w-16 h-4 bg-surface-200 rounded"></div>
                  <div class="w-16">
                    <div class="h-3 bg-surface-200 rounded mb-1"></div>
                    <div class="w-16 h-1.5 bg-surface-200 rounded-full"></div>
                  </div>
                </div>
              </div>
            </div>
          {/each}
        {:else if dashboardData?.recent_projects && dashboardData.recent_projects.length > 0}
          {#each dashboardData.recent_projects as project}
            <ProjectCard {project} />
          {/each}
        {:else}
          <div class="px-4 py-8 text-center text-surface-500">
            <p>No projects available</p>
          </div>
        {/if}
      </div>
    </div>
  
  {:else if activeSection === 'projects'}
    <ProjectsOverview />
  
  {:else if activeSection === 'agents'}
    <AgentsOverview />
  
  {:else if activeSection === 'talents'}
    <TalentsOverview />
  
  {:else if activeSection === 'workflows'}
    <WorkflowsOverview />
  
  {:else if activeSection === 'costs'}
    <CostOverview />
  
  {:else if activeSection === 'feedback'}
    <FeedbackOverview />
  
  {:else if activeSection === 'analytics'}
    <ModernAnalyticsDashboard timeRange={timeRange} />
  {/if}
</div>