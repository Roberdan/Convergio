<script lang="ts">
  import { onMount } from 'svelte';
  import { Card, Badge, Button } from '$lib/components/ui';
  import { slide } from 'svelte/transition';
  
  export let orchestrationData: any = {};
  export let timeRange: string = '30d';
  
  interface MetricValue {
    value: number;
    target?: number;
    budget?: number;
    trend: string;
    change: number;
  }
  
  interface MetricCategory {
    [key: string]: MetricValue;
  }
  
  interface MetricsData {
    efficiency_metrics: MetricCategory;
    collaboration_metrics: MetricCategory;
    cost_metrics: MetricCategory & { budget?: number };
    quality_metrics: MetricCategory;
    ai_insights: any[];
    trends: any;
  }
  
  let metricsData: MetricsData | null = null;
  let loading = true;
  let selectedMetricCategory = 'overview';
  let showAIInsights = true;
  
  const metricCategories = [
    { id: 'overview', label: '📊 Overview', icon: '📊' },
    { id: 'efficiency', label: '⚡ Efficiency', icon: '⚡' },
    { id: 'collaboration', label: '🤝 Collaboration', icon: '🤝' },
    { id: 'cost', label: '💰 Cost', icon: '💰' },
    { id: 'quality', label: '✨ Quality', icon: '✨' }
  ];
  
  onMount(async () => {
    await loadMetricsData();
  });
  
  async function loadMetricsData() {
    loading = true;
    
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:9000';
      // Ensure we have a valid orchestration ID (UUID format)
      const orchestrationId = orchestrationData.id || '550e8400-e29b-41d4-a716-446655440000';
      const response = await fetch(`${apiUrl}/api/v1/pm/orchestration/projects/${orchestrationId}/metrics?period_days=${getPeriodDays(timeRange)}`);
      
      if (response.ok) {
        metricsData = await response.json();
      } else {
        // Fallback to mock data
        metricsData = generateMockMetricsData();
      }
    } catch (error) {
      console.error('Error loading metrics:', error);
      metricsData = generateMockMetricsData();
    } finally {
      loading = false;
    }
  }
  
  function getPeriodDays(range: string): number {
    switch (range) {
      case '7d': return 7;
      case '30d': return 30;
      case '90d': return 90;
      default: return 30;
    }
  }
  
  function generateMockMetricsData(): MetricsData {
    return {
      efficiency_metrics: {
        overall_efficiency: { value: 87.5, target: 90, trend: 'up', change: 5.2 },
        task_completion_rate: { value: 94.2, target: 95, trend: 'up', change: 3.1 },
        average_response_time: { value: 1.8, target: 2.0, trend: 'down', change: -0.3 },
        throughput: { value: 156, target: 180, trend: 'up', change: 23 },
        automation_score: { value: 82.3, target: 85, trend: 'up', change: 7.5 }
      },
      collaboration_metrics: {
        team_synergy: { value: 91.2, target: 95, trend: 'up', change: 4.8 },
        communication_quality: { value: 88.7, target: 90, trend: 'up', change: 2.3 },
        conflict_resolution: { value: 96.1, target: 95, trend: 'stable', change: 0.8 },
        knowledge_sharing: { value: 84.5, target: 88, trend: 'up', change: 6.2 },
        coordination_score: { value: 89.3, target: 92, trend: 'up', change: 3.7 }
      },
      cost_metrics: {
        total_cost: { value: 15750, budget: 20000, trend: 'down', change: -2340 },
        cost_per_hour: { value: 125, target: 120, trend: 'down', change: -15 },
        efficiency_savings: { value: 3250, target: 2500, trend: 'up', change: 1100 },
        roi: { value: 3.2, target: 3.0, trend: 'up', change: 0.8 },
        budget_utilization: { value: 78.8, target: 85, trend: 'up', change: 12.3 }
      },
      quality_metrics: {
        deliverable_quality: { value: 92.1, target: 95, trend: 'up', change: 4.5 },
        client_satisfaction: { value: 4.7, target: 4.8, trend: 'up', change: 0.3 },
        defect_rate: { value: 0.8, target: 0.5, trend: 'down', change: -0.3 },
        review_score: { value: 89.4, target: 90, trend: 'up', change: 2.1 },
        standards_compliance: { value: 95.6, target: 95, trend: 'stable', change: 0.2 }
      },
      ai_insights: [
        {
          type: 'optimization',
          priority: 'high',
          title: 'Resource Reallocation Opportunity',
          message: 'AI analysis suggests reallocating Sara UX Designer to parallel design tasks could increase overall efficiency by 12%',
          confidence: 0.92,
          impact: '+12% efficiency',
          action: 'Implement parallel workflow',
          agent: 'Ali Chief of Staff'
        },
        {
          type: 'cost',
          priority: 'medium',
          title: 'Cost Optimization Available',
          message: 'Model selection optimization could reduce API costs by 18% while maintaining quality',
          confidence: 0.85,
          impact: '$2,850 monthly savings',
          action: 'Enable dynamic model selection',
          agent: 'Amy CFO'
        },
        {
          type: 'quality',
          priority: 'low',
          title: 'Quality Enhancement Detected',
          message: 'Implementing automated testing pipeline would improve delivery quality by 15%',
          confidence: 0.78,
          impact: '+15% quality score',
          action: 'Deploy automated testing',
          agent: 'Thor QA Guardian'
        }
      ],
      trends: {
        efficiency_trend: [82, 84, 86, 87, 88, 87, 88],
        cost_trend: [18000, 17200, 16800, 16200, 15900, 15750, 15600],
        satisfaction_trend: [4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.7]
      }
    };
  }
  
  function getMetricColor(value: number, target: number, reverse: boolean = false): string {
    const ratio = value / target;
    if (reverse) {
      // For metrics where lower is better (e.g., cost, response time)
      if (ratio <= 0.8) return 'text-green-600';
      if (ratio <= 0.95) return 'text-blue-600';
      if (ratio <= 1.05) return 'text-yellow-600';
      return 'text-red-600';
    } else {
      // For metrics where higher is better
      if (ratio >= 0.98) return 'text-green-600';
      if (ratio >= 0.9) return 'text-blue-600';
      if (ratio >= 0.8) return 'text-yellow-600';
      return 'text-red-600';
    }
  }
  
  function getMetricBgColor(value: number, target: number, reverse: boolean = false): string {
    const ratio = value / target;
    if (reverse) {
      if (ratio <= 0.8) return 'bg-green-50 border-green-200';
      if (ratio <= 0.95) return 'bg-blue-50 border-blue-200';
      if (ratio <= 1.05) return 'bg-yellow-50 border-yellow-200';
      return 'bg-red-50 border-red-200';
    } else {
      if (ratio >= 0.98) return 'bg-green-50 border-green-200';
      if (ratio >= 0.9) return 'bg-blue-50 border-blue-200';
      if (ratio >= 0.8) return 'bg-yellow-50 border-yellow-200';
      return 'bg-red-50 border-red-200';
    }
  }
  
  function getTrendIcon(trend: string): string {
    switch (trend) {
      case 'up': return '📈';
      case 'down': return '📉';
      case 'stable': return '➡️';
      default: return '📊';
    }
  }
  
  function formatMetricValue(value: number, type: string): string {
    switch (type) {
      case 'currency':
        return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 0 }).format(value);
      case 'percentage':
        return `${value.toFixed(1)}%`;
      case 'decimal':
        return value.toFixed(2);
      case 'rating':
        return `${value.toFixed(1)}/5.0`;
      case 'time':
        return `${value.toFixed(1)}s`;
      default:
        return value.toLocaleString();
    }
  }
  
  function getPriorityColor(priority: string): string {
    switch (priority) {
      case 'high': return 'bg-red-100 text-red-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'low': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  }
  
  function getInsightIcon(type: string): string {
    switch (type) {
      case 'optimization': return '⚡';
      case 'cost': return '💰';
      case 'quality': return '✨';
      case 'resource': return '👥';
      case 'timeline': return '⏰';
      default: return '💡';
    }
  }
  
  async function applyInsight(insight: any) {
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:9000';
      const response = await fetch(`${apiUrl}/api/v1/pm/orchestration/projects/${orchestrationData.id}/apply-insight`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ insight_id: insight.id, action: insight.action })
      });
      
      if (response.ok) {
        // Reload metrics to show updated data
        await loadMetricsData();
      }
    } catch (error) {
      console.error('Error applying insight:', error);
    }
  }
  
  $: selectedMetrics = metricsData ? (metricsData as any)[`${selectedMetricCategory}_metrics`] || metricsData.efficiency_metrics : null;
</script>

<!-- Orchestration Metrics Dashboard -->
<div class="space-y-6">
  {#if loading}
    <Card>
      <div class="flex items-center justify-center py-12">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span class="ml-3 text-surface-600 ">Loading metrics...</span>
      </div>
    </Card>
  {:else if metricsData}
    <!-- Metrics Header -->
    <Card>
      <div class="p-4">
        <div class="flex items-center justify-between">
          <div>
            <h3 class="text-lg font-semibold text-surface-900 ">
              📊 Orchestration Metrics
            </h3>
            <p class="text-sm text-surface-600  mt-1">
              AI-powered performance analytics and optimization insights
            </p>
          </div>
          
          <div class="flex items-center space-x-3">
            <!-- Time Range Selector -->
            <select 
              bind:value={timeRange}
              on:change={loadMetricsData}
              class="text-sm border border-surface-300  rounded-md px-3 py-1 
                     bg-surface-50  text-surface-900 "
            >
              <option value="7d">Last 7 days</option>
              <option value="30d">Last 30 days</option>
              <option value="90d">Last 90 days</option>
            </select>
            
            <Button variant="outline" size="sm" on:click={() => showAIInsights = !showAIInsights}>
              {showAIInsights ? '🤖 Hide AI' : '🧠 Show AI'}
            </Button>
          </div>
        </div>
      </div>
    </Card>
    
    <!-- Category Navigation -->
    <div class="flex space-x-1 bg-surface-200  rounded-lg p-1">
      {#each metricCategories as category}
        <button
          on:click={() => selectedMetricCategory = category.id}
          class="px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 {selectedMetricCategory === category.id 
            ? 'bg-surface-50 text-surface-900  shadow-sm' 
            : 'text-surface-600  hover:text-surface-900'}"
        >
          {category.label}
        </button>
      {/each}
    </div>
    
    <!-- Main Metrics Grid -->
    {#if selectedMetricCategory === 'overview'}
      <!-- Overview: Key metrics from all categories -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <!-- Overall Efficiency -->
        <Card class="{getMetricBgColor(metricsData.efficiency_metrics.overall_efficiency.value, metricsData.efficiency_metrics.overall_efficiency.target || 0)}">
          <div class="p-4">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-surface-600 ">Overall Efficiency</p>
                <p class="text-2xl font-bold {getMetricColor(metricsData.efficiency_metrics.overall_efficiency.value, metricsData.efficiency_metrics.overall_efficiency.target || 0)}">
                  {formatMetricValue(metricsData.efficiency_metrics.overall_efficiency.value, 'percentage')}
                </p>
                <p class="text-xs text-surface-500">
                  Target: {formatMetricValue(metricsData.efficiency_metrics.overall_efficiency.target || 0, 'percentage')}
                </p>
              </div>
              <div class="text-right">
                <span class="text-lg">{getTrendIcon(metricsData.efficiency_metrics.overall_efficiency.trend)}</span>
                <p class="text-xs {metricsData.efficiency_metrics.overall_efficiency.change > 0 ? 'text-green-600' : 'text-red-600'}">
                  {metricsData.efficiency_metrics.overall_efficiency.change > 0 ? '+' : ''}{metricsData.efficiency_metrics.overall_efficiency.change}%
                </p>
              </div>
            </div>
          </div>
        </Card>
        
        <!-- Team Synergy -->
        <Card class="{getMetricBgColor(metricsData.collaboration_metrics.team_synergy.value, metricsData.collaboration_metrics.team_synergy.target || 0)}">
          <div class="p-4">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-surface-600 ">Team Synergy</p>
                <p class="text-2xl font-bold {getMetricColor(metricsData.collaboration_metrics.team_synergy.value, metricsData.collaboration_metrics.team_synergy.target || 0)}">
                  {formatMetricValue(metricsData.collaboration_metrics.team_synergy.value, 'percentage')}
                </p>
                <p class="text-xs text-surface-500">
                  Target: {formatMetricValue(metricsData.collaboration_metrics.team_synergy.target || 0, 'percentage')}
                </p>
              </div>
              <div class="text-right">
                <span class="text-lg">{getTrendIcon(metricsData.collaboration_metrics.team_synergy.trend)}</span>
                <p class="text-xs {metricsData.collaboration_metrics.team_synergy.change > 0 ? 'text-green-600' : 'text-red-600'}">
                  {metricsData.collaboration_metrics.team_synergy.change > 0 ? '+' : ''}{metricsData.collaboration_metrics.team_synergy.change}%
                </p>
              </div>
            </div>
          </div>
        </Card>
        
        <!-- Total Cost -->
        <Card class="{getMetricBgColor(metricsData.cost_metrics.total_cost.value, metricsData.cost_metrics.budget || 0, true)}">
          <div class="p-4">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-surface-600 ">Total Cost</p>
                <p class="text-2xl font-bold {getMetricColor(metricsData.cost_metrics.total_cost.value, metricsData.cost_metrics.budget || 0, true)}">
                  {formatMetricValue(metricsData.cost_metrics.total_cost.value, 'currency')}
                </p>
                <p class="text-xs text-surface-500">
                  Budget: {formatMetricValue(metricsData.cost_metrics.budget || 0, 'currency')}
                </p>
              </div>
              <div class="text-right">
                <span class="text-lg">{getTrendIcon(metricsData.cost_metrics.total_cost.trend)}</span>
                <p class="text-xs {metricsData.cost_metrics.total_cost.change < 0 ? 'text-green-600' : 'text-red-600'}">
                  {formatMetricValue(metricsData.cost_metrics.total_cost.change, 'currency')}
                </p>
              </div>
            </div>
          </div>
        </Card>
        
        <!-- Client Satisfaction -->
        <Card class="{getMetricBgColor(metricsData.quality_metrics.client_satisfaction.value, metricsData.quality_metrics.client_satisfaction.target || 0)}">
          <div class="p-4">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-surface-600 ">Client Satisfaction</p>
                <p class="text-2xl font-bold {getMetricColor(metricsData.quality_metrics.client_satisfaction.value, metricsData.quality_metrics.client_satisfaction.target || 0)}">
                  {formatMetricValue(metricsData.quality_metrics.client_satisfaction.value, 'rating')}
                </p>
                <p class="text-xs text-surface-500">
                  Target: {formatMetricValue(metricsData.quality_metrics.client_satisfaction.target || 0, 'rating')}
                </p>
              </div>
              <div class="text-right">
                <span class="text-lg">{getTrendIcon(metricsData.quality_metrics.client_satisfaction.trend)}</span>
                <p class="text-xs {metricsData.quality_metrics.client_satisfaction.change > 0 ? 'text-green-600' : 'text-red-600'}">
                  {metricsData.quality_metrics.client_satisfaction.change > 0 ? '+' : ''}{metricsData.quality_metrics.client_satisfaction.change}
                </p>
              </div>
            </div>
          </div>
        </Card>
      </div>
    {:else if selectedMetrics}
      <!-- Category-specific metrics -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {#each Object.entries(selectedMetrics) as [key, metric]}
          {@const typedMetric = metric as MetricValue}
          <Card class="{getMetricBgColor(typedMetric.value, typedMetric.target || typedMetric.budget || 0, key.includes('cost') || key.includes('time') || key.includes('defect'))}">
            <div class="p-4">
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-sm text-surface-600  capitalize">
                    {key.replace(/_/g, ' ')}
                  </p>
                  <p class="text-xl font-bold {getMetricColor(typedMetric.value, typedMetric.target || typedMetric.budget || 0, key.includes('cost') || key.includes('time') || key.includes('defect'))}">
                    {formatMetricValue(typedMetric.value, 
                      key.includes('cost') || key.includes('savings') ? 'currency' :
                      key.includes('rate') || key.includes('score') || key.includes('efficiency') || key.includes('utilization') ? 'percentage' :
                      key.includes('satisfaction') || key.includes('rating') || key.includes('roi') ? 'decimal' :
                      key.includes('time') ? 'time' : 'default'
                    )}
                  </p>
                  {#if typedMetric.target || typedMetric.budget}
                    <p class="text-xs text-surface-500">
                      {typedMetric.target ? 'Target' : 'Budget'}: {formatMetricValue(typedMetric.target || typedMetric.budget || 0, 
                        key.includes('cost') || key.includes('savings') ? 'currency' :
                        key.includes('rate') || key.includes('score') || key.includes('efficiency') || key.includes('utilization') ? 'percentage' :
                        key.includes('satisfaction') || key.includes('rating') || key.includes('roi') ? 'decimal' :
                        key.includes('time') ? 'time' : 'default'
                      )}
                    </p>
                  {/if}
                </div>
                <div class="text-right">
                  <span class="text-lg">{getTrendIcon(typedMetric.trend)}</span>
                  <p class="text-xs {(typedMetric.change > 0 && !key.includes('cost') && !key.includes('time') && !key.includes('defect')) || 
                                   (typedMetric.change < 0 && (key.includes('cost') || key.includes('time') || key.includes('defect'))) ? 'text-green-600' : 'text-red-600'}">
                    {typedMetric.change > 0 ? '+' : ''}{typedMetric.change}{key.includes('cost') || key.includes('savings') ? '' : '%'}
                  </p>
                </div>
              </div>
            </div>
          </Card>
        {/each}
      </div>
    {/if}
    
    <!-- AI Insights Section -->
    {#if showAIInsights && metricsData.ai_insights}
      <div transition:slide>
        <Card>
          <div class="p-6">
          <div class="flex items-center justify-between mb-4">
            <h4 class="font-semibold text-surface-900 ">
              🧠 AI Insights & Recommendations
            </h4>
            <Badge class="bg-blue-100 text-blue-800">
              {metricsData.ai_insights.length} insights
            </Badge>
          </div>
          
          <div class="space-y-3">
            {#each metricsData.ai_insights as insight}
              <div class="border border-surface-200  rounded-lg p-4 hover:shadow-md transition-shadow">
                <div class="flex items-start justify-between">
                  <div class="flex-1">
                    <div class="flex items-center space-x-2 mb-2">
                      <span class="text-lg">{getInsightIcon(insight.type)}</span>
                      <h5 class="font-medium text-surface-900 ">
                        {insight.title}
                      </h5>
                      <Badge class="{getPriorityColor(insight.priority)}">
                        {insight.priority}
                      </Badge>
                    </div>
                    
                    <p class="text-sm text-surface-700  mb-2">
                      {insight.message}
                    </p>
                    
                    <div class="flex items-center space-x-4 text-xs text-surface-600 ">
                      <span>Confidence: <strong>{Math.round(insight.confidence * 100)}%</strong></span>
                      <span>Impact: <strong class="text-green-600">{insight.impact}</strong></span>
                      <span>By: <strong>{insight.agent}</strong></span>
                    </div>
                  </div>
                  
                  <div class="ml-4">
                    <Button variant="outline" size="sm" on:click={() => applyInsight(insight)}>
                      Apply
                    </Button>
                  </div>
                </div>
              </div>
            {/each}
          </div>
        </Card>
      </div>
    {/if}
  {/if}
</div>

<style>
  /* Smooth transitions */
  .transition-all {
    transition: all 0.2s ease-in-out;
  }
  
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
</style>