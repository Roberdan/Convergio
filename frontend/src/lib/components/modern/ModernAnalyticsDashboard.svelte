<script lang="ts">
  import { onMount } from 'svelte';
  import { writable } from 'svelte/store';
  
  export let projectId: string = '';
  export let timeRange: string = '30d';
  
  let loading = true;
  let selectedMetric = 'overview';
  let realTimeData = writable({});
  let chartData: any = {};
  let kpiMetrics: any = {};
  let aiInsights: any[] = [];
  
  // Mock KPI data with AI insights
  const mockKPIMetrics = {
    overview: {
      totalProjects: { value: 24, change: +12, target: 30 },
      activeAgents: { value: 48, change: +3, target: 50 },
      completionRate: { value: 87.5, change: +5.2, target: 90 },
      averageVelocity: { value: 42, change: -2.1, target: 45 },
      costEfficiency: { value: 94.2, change: +3.8, target: 95 },
      clientSatisfaction: { value: 4.8, change: +0.3, target: 5.0 }
    },
    performance: {
      taskThroughput: { value: 156, change: +23, target: 180 },
      averageResponseTime: { value: 2.4, change: -0.6, target: 2.0 },
      errorRate: { value: 0.8, change: -0.3, target: 0.5 },
      systemUptime: { value: 99.94, change: +0.02, target: 99.95 },
      aiOptimizationScore: { value: 92.1, change: +4.5, target: 95 },
      resourceUtilization: { value: 78.3, change: +2.1, target: 80 }
    },
    business: {
      revenue: { value: 245000, change: +18500, target: 300000 },
      profitMargin: { value: 34.2, change: +2.8, target: 35 },
      customerAcquisition: { value: 89, change: +12, target: 100 },
      retentionRate: { value: 96.8, change: +1.2, target: 97 },
      marketingROI: { value: 4.2, change: +0.8, target: 5.0 },
      timeToMarket: { value: 21, change: -3, target: 18 }
    }
  };
  
  // Mock AI insights with proactive recommendations
  const mockAIInsights = [
    {
      type: 'optimization',
      priority: 'high',
      title: 'Project Velocity Optimization',
      message: 'Ali detected 15% velocity improvement opportunity by reallocating Marcus PM and Sara UX Designer to parallel tracks',
      confidence: 0.94,
      estimatedImpact: '+6.3 story points/sprint',
      recommendation: 'Implement parallel workflow for design and development phases',
      agent: 'Ali Chief of Staff'
    },
    {
      type: 'resource',
      priority: 'medium',
      title: 'Resource Bottleneck Alert',
      message: 'Thor QA Guardian is operating at 95% capacity - consider load balancing or additional QA resources',
      confidence: 0.87,
      estimatedImpact: '-12% delivery risk',
      recommendation: 'Schedule Luca Security Expert for cross-functional QA support',
      agent: 'Marcus PM'
    },
    {
      type: 'cost',
      priority: 'high',
      title: 'Cost Efficiency Opportunity',
      message: 'AI model optimization could reduce operational costs by 23% while maintaining quality standards',
      confidence: 0.91,
      estimatedImpact: '$18,500/month savings',
      recommendation: 'Implement dynamic model selection based on task complexity',
      agent: 'Amy CFO'
    },
    {
      type: 'quality',
      priority: 'medium',
      title: 'Quality Assurance Enhancement',
      message: 'Pattern analysis suggests implementing automated testing will increase delivery quality by 28%',
      confidence: 0.83,
      estimatedImpact: '+28% quality score',
      recommendation: 'Deploy Thor QA Guardian automated testing pipeline',
      agent: 'Baccio Tech Architect'
    }
  ];
  
  // Mock chart data for visualizations
  const mockChartData = {
    projectVelocity: {
      labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
      datasets: [
        { label: 'Completed', data: [12, 19, 15, 22], color: '#10b981' },
        { label: 'In Progress', data: [8, 12, 10, 15], color: '#2563eb' },
        { label: 'Planned', data: [15, 18, 20, 25], color: '#f59e0b' }
      ]
    },
    agentUtilization: {
      labels: ['Marcus PM', 'Sara UX', 'Baccio Arch', 'Dan Eng', 'Thor QA', 'Ali Chief'],
      datasets: [
        { label: 'Utilization %', data: [85, 92, 78, 88, 95, 72], color: '#8b5cf6' }
      ]
    },
    costTrends: {
      labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
      datasets: [
        { label: 'AI Costs', data: [12500, 13200, 11800, 14100, 13600, 12900], color: '#ef4444' },
        { label: 'Infrastructure', data: [8500, 8800, 8200, 8900, 8600, 8400], color: '#06b6d4' },
        { label: 'Revenue', data: [45000, 48500, 42000, 52000, 49500, 51200], color: '#10b981' }
      ]
    }
  };
  
  onMount(async () => {
    await loadAnalyticsData();
    await loadAIInsights();
    setupRealTimeUpdates();
    loading = false;
  });
  
  async function loadAnalyticsData() {
    try {
      if (projectId) {
        const response = await fetch(`/api/v1/analytics/project/${projectId}?range=${timeRange}`);
        if (response.ok) {
          const data = await response.json();
          kpiMetrics = data.kpis || mockKPIMetrics;
          chartData = data.charts || mockChartData;
        }
      } else {
        // Global analytics
        const response = await fetch(`/api/v1/analytics/global?range=${timeRange}`);
        if (response.ok) {
          const data = await response.json();
          kpiMetrics = data.kpis || mockKPIMetrics;
          chartData = data.charts || mockChartData;
        }
      }
    } catch (error) {
      console.error('Failed to load analytics:', error);
      kpiMetrics = mockKPIMetrics;
      chartData = mockChartData;
    }
  }
  
  async function loadAIInsights() {
    try {
      const response = await fetch('/api/v1/agents/ali/analytics-insights', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_id: projectId,
          metrics: kpiMetrics,
          time_range: timeRange
        })
      });
      
      if (response.ok) {
        aiInsights = await response.json();
      }
    } catch (error) {
      console.error('Failed to load AI insights:', error);
      aiInsights = mockAIInsights;
    }
  }
  
  function setupRealTimeUpdates() {
    // Simulate real-time metric updates
    setInterval(() => {
      realTimeData.update(data => ({
        ...data,
        timestamp: new Date(),
        activeUsers: Math.floor(Math.random() * 50) + 150,
        systemLoad: Math.random() * 100,
        throughput: Math.floor(Math.random() * 20) + 40
      }));
    }, 5000);
  }
  
  function formatMetricValue(value: number, type: string): string {
    switch (type) {
      case 'currency':
        return new Intl.NumberFormat('en-US', { 
          style: 'currency', 
          currency: 'USD',
          minimumFractionDigits: 0,
          maximumFractionDigits: 0
        }).format(value);
      case 'percentage':
        return `${value.toFixed(1)}%`;
      case 'decimal':
        return value.toFixed(2);
      case 'rating':
        return `${value.toFixed(1)}/5.0`;
      case 'days':
        return `${value} days`;
      default:
        return value.toLocaleString();
    }
  }
  
  function getChangeIcon(change: number): string {
    if (change > 0) return '📈';
    if (change < 0) return '📉';
    return '➖';
  }
  
  function getPriorityColor(priority: string): string {
    switch (priority) {
      case 'high': return '#ef4444';
      case 'medium': return '#f59e0b';
      case 'low': return '#10b981';
      default: return '#2563eb';
    }
  }
  
  function getInsightIcon(type: string): string {
    switch (type) {
      case 'optimization': return '⚡';
      case 'resource': return '👥';
      case 'cost': return '💰';
      case 'quality': return '🎯';
      case 'risk': return '⚠️';
      default: return '🧠';
    }
  }
  
  async function implementRecommendation(insight: any) {
    try {
      const response = await fetch('/api/v1/agents/implement-recommendation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          recommendation: insight.recommendation,
          agent: insight.agent,
          project_id: projectId
        })
      });
      
      if (response.ok) {
        alert(`✅ ${insight.agent} is implementing: ${insight.recommendation}`);
        // Reload insights
        await loadAIInsights();
      }
    } catch (error) {
      console.error('Failed to implement recommendation:', error);
      alert(`🤖 ${insight.agent} has been notified to implement the recommendation`);
    }
  }
  
  $: currentMetrics = kpiMetrics[selectedMetric] || {};
</script>

<div class="analytics-container">
  <!-- Header with Controls -->
  <div class="content-section">
    <div class="analytics-header">
      <div class="header-left">
        <h2 class="heading-lg">
          <span class="title-icon">📊</span>
          Analytics Intelligence
        </h2>
        <p class="body-md text-muted">AI-powered insights and performance metrics</p>
      </div>
      
      <div class="header-controls">
        <!-- Time Range Selector -->
        <div class="control-group">
          <select bind:value={timeRange} on:change={loadAnalyticsData} class="input-field">
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
            <option value="90d">Last 3 Months</option>
            <option value="1y">Last Year</option>
          </select>
        </div>
        
        <!-- Metric Category Tabs -->
        <div class="metric-tabs">
          <button 
            class="btn-secondary {selectedMetric === 'overview' ? 'btn-primary' : ''}"
            on:click={() => selectedMetric = 'overview'}
          >
            Overview
          </button>
          <button 
            class="btn-secondary {selectedMetric === 'performance' ? 'btn-primary' : ''}"
            on:click={() => selectedMetric = 'performance'}
          >
            Performance
          </button>
          <button 
            class="btn-secondary {selectedMetric === 'business' ? 'btn-primary' : ''}"
            on:click={() => selectedMetric = 'business'}
          >
            Business
          </button>
        </div>
        
        <!-- Real-time indicator -->
        <div class="real-time-status">
          <div class="pulse-dot"></div>
          <span class="body-sm">Live</span>
        </div>
      </div>
    </div>
  </div>
  
  <!-- AI Insights Panel -->
  {#if aiInsights.length > 0}
    <div class="content-section">
      <div class="card-header">
        <h3 class="heading-md">
          <span class="ai-icon">🧠</span>
          AI Strategic Insights
        </h3>
        <p class="body-md text-muted">Proactive recommendations from your AI team</p>
      </div>
      
      <div class="insights-grid">
        {#each aiInsights as insight}
          <div class="card insight-card" style="border-left: 4px solid {getPriorityColor(insight.priority)}">
            <div class="insight-header">
              <div class="insight-meta">
                <span class="insight-icon">{getInsightIcon(insight.type)}</span>
                <span class="insight-type body-xs">{insight.type.toUpperCase()}</span>
                <span class="priority-badge body-xs" style="background: {getPriorityColor(insight.priority)}">
                  {insight.priority.toUpperCase()}
                </span>
              </div>
              <div class="confidence-score body-xs">
                {Math.round(insight.confidence * 100)}% confidence
              </div>
            </div>
            
            <h4 class="heading-xs insight-title">{insight.title}</h4>
            <p class="body-md insight-message">{insight.message}</p>
            
            <div class="insight-impact">
              <span class="body-xs text-muted">Estimated Impact:</span>
              <span class="body-xs font-bold text-green-700">{insight.estimatedImpact}</span>
            </div>
            
            <div class="insight-recommendation">
              <span class="body-xs font-bold text-blue-700">Recommendation:</span>
              <p class="body-sm">{insight.recommendation}</p>
            </div>
            
            <div class="insight-actions">
              <span class="body-xs text-muted">by {insight.agent}</span>
              <button 
                class="btn-primary btn-sm"
                on:click={() => implementRecommendation(insight)}
              >
                Implement
              </button>
            </div>
          </div>
        {/each}
      </div>
    </div>
  {/if}
  
  <!-- KPI Metrics Grid -->
  <div class="content-section">
    <div class="kpi-grid">
      {#each Object.entries(currentMetrics) as [key, metric]}
        <div class="card kpi-card">
          <div class="kpi-header">
            <h4 class="heading-xs">{key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}</h4>
            <span class="change-indicator text-2xl">
              {getChangeIcon(metric.change)}
            </span>
          </div>
          
          <div class="kpi-value heading-lg">
            {#if key === 'revenue'}
              {formatMetricValue(metric.value, 'currency')}
            {:else if key.includes('Rate') || key.includes('Margin') || key.includes('Efficiency') || key.includes('Uptime')}
              {formatMetricValue(metric.value, 'percentage')}
            {:else if key.includes('Satisfaction')}
              {formatMetricValue(metric.value, 'rating')}
            {:else if key.includes('Time') && key.includes('Response')}
              {formatMetricValue(metric.value, 'decimal')}s
            {:else if key.includes('Time')}
              {formatMetricValue(metric.value, 'days')}
            {:else}
              {formatMetricValue(metric.value, 'number')}
            {/if}
          </div>
          
          <div class="kpi-meta">
            <div class="change-info">
              <span class="body-sm font-bold {metric.change > 0 ? 'text-green-700' : metric.change < 0 ? 'text-red-700' : 'text-surface-600'}">
                {metric.change > 0 ? '+' : ''}{formatMetricValue(Math.abs(metric.change), 
                  key === 'revenue' ? 'currency' : 
                  key.includes('Rate') || key.includes('Margin') || key.includes('Efficiency') ? 'percentage' : 'number')}
              </span>
              <span class="body-sm text-muted">vs last period</span>
            </div>
            
            <div class="target-progress">
              <div class="progress-bar">
                <div 
                  class="progress-fill bg-blue-600" 
                  style="width: {Math.min((metric.value / metric.target) * 100, 100)}%"
                ></div>
              </div>
              <span class="body-xs text-muted">Target: {formatMetricValue(metric.target, 
                key === 'revenue' ? 'currency' : 
                key.includes('Rate') || key.includes('Margin') || key.includes('Efficiency') ? 'percentage' : 'number')}</span>
            </div>
          </div>
        </div>
      {/each}
    </div>
  </div>
  
  <!-- Charts Section -->
  <div class="content-section">
    <div class="charts-section">
      <div class="card">
        <h3 class="heading-md">Project Velocity Trends</h3>
        <div class="chart-container">
          <!-- Simplified chart visualization -->
          <div class="simple-chart">
            {#each chartData.projectVelocity?.datasets || [] as dataset, i}
              <div class="chart-legend-item">
                <div class="legend-color" style="background: {dataset.color}"></div>
                <span class="body-sm">{dataset.label}</span>
              </div>
            {/each}
            <div class="chart-bars">
              {#each chartData.projectVelocity?.labels || [] as label, i}
                <div class="bar-group">
                  <div class="bar-label body-xs text-muted">{label}</div>
                  {#each chartData.projectVelocity?.datasets || [] as dataset, j}
                    <div 
                      class="chart-bar" 
                      style="height: {(dataset.data[i] / 30) * 100}%; background: {dataset.color}"
                    ></div>
                  {/each}
                </div>
              {/each}
            </div>
          </div>
        </div>
      </div>
      
      <div class="card">
        <h3 class="heading-md">Agent Utilization</h3>
        <div class="chart-container">
          <div class="utilization-chart">
            {#each chartData.agentUtilization?.labels || [] as agent, i}
              {@const utilization = chartData.agentUtilization?.datasets[0]?.data[i] || 0}
              <div class="utilization-row">
                <div class="agent-name body-sm">{agent}</div>
                <div class="utilization-bar">
                  <div 
                    class="utilization-fill" 
                    style="width: {utilization}%; background: {utilization > 90 ? '#ef4444' : utilization > 80 ? '#f59e0b' : '#10b981'}"
                  ></div>
                </div>
                <div class="utilization-value body-sm font-bold">{utilization}%</div>
              </div>
            {/each}
          </div>
        </div>
      </div>
    </div>
  </div>
  
  <!-- Real-time Metrics -->
  {#if $realTimeData.timestamp}
    <div class="content-section">
      <h3 class="heading-md">
        <span class="pulse-icon">📡</span>
        Real-time Metrics
      </h3>
      
      <div class="realtime-grid">
        <div class="realtime-metric card">
          <span class="body-sm text-muted">Active Users</span>
          <span class="heading-md">{$realTimeData.activeUsers}</span>
        </div>
        
        <div class="realtime-metric card">
          <span class="body-sm text-muted">System Load</span>
          <span class="heading-md">{$realTimeData.systemLoad?.toFixed(1)}%</span>
        </div>
        
        <div class="realtime-metric card">
          <span class="body-sm text-muted">Throughput</span>
          <span class="heading-md">{$realTimeData.throughput}/min</span>
        </div>
        
        <div class="realtime-metric card">
          <span class="body-sm text-muted">Last Update</span>
          <span class="body-md">{$realTimeData.timestamp?.toLocaleTimeString()}</span>
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  .analytics-container {
    background: var(--bg-secondary);
    min-height: 100vh;
    padding: 24px;
  }
  
  .analytics-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 24px;
  }
  
  .header-left {
    flex: 1;
  }
  
  .title-icon {
    font-size: 36px;
    margin-right: 12px;
  }
  
  .header-controls {
    display: flex;
    align-items: center;
    gap: 16px;
    flex-wrap: wrap;
  }
  
  .control-group select {
    min-width: 150px;
  }
  
  .metric-tabs {
    display: flex;
    gap: 8px;
  }
  
  .real-time-status {
    display: flex;
    align-items: center;
    gap: 8px;
    color: #10b981;
    font-weight: 600;
  }
  
  .pulse-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #10b981;
    animation: pulse 2s infinite;
  }
  
  @keyframes pulse {
    0% { opacity: 1; }
    50% { opacity: 0.5; }
    100% { opacity: 1; }
  }
  
  .insights-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
    gap: 20px;
  }
  
  .insight-card {
    position: relative;
  }
  
  .insight-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
  }
  
  .insight-meta {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  
  .insight-icon {
    font-size: 18px;
  }
  
  .insight-type {
    color: var(--primary-blue);
    text-transform: uppercase;
    letter-spacing: 1px;
    font-weight: 700;
  }
  
  .priority-badge {
    padding: 4px 8px;
    border-radius: 6px;
    color: white;
    font-weight: 700;
  }
  
  .confidence-score {
    color: #10b981;
    font-weight: 600;
  }
  
  .insight-title {
    margin-bottom: 8px;
  }
  
  .insight-message {
    margin-bottom: 12px;
  }
  
  .insight-impact {
    display: flex;
    justify-content: space-between;
    margin-bottom: 12px;
  }
  
  .insight-recommendation {
    background: var(--bg-accent);
    border: 2px solid var(--border-default);
    border-radius: 8px;
    padding: 12px;
    margin-bottom: 16px;
  }
  
  .insight-actions {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .btn-sm {
    padding: 6px 12px;
    font-size: 12px;
  }
  
  .kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 20px;
  }
  
  .kpi-card {
    transition: all 0.3s ease;
  }
  
  .kpi-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-xl);
  }
  
  .kpi-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
  }
  
  .kpi-value {
    margin-bottom: 16px;
    line-height: 1;
  }
  
  .kpi-meta {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  
  .change-info {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  .target-progress {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  
  .progress-bar {
    width: 100%;
    height: 8px;
    background: var(--bg-accent);
    border-radius: 4px;
    overflow: hidden;
  }
  
  .progress-fill {
    height: 100%;
    transition: width 0.5s ease;
  }
  
  .charts-section {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
    gap: 24px;
  }
  
  .simple-chart {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }
  
  .chart-legend-item {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  .legend-color {
    width: 12px;
    height: 12px;
    border-radius: 2px;
  }
  
  .chart-bars {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    height: 150px;
    gap: 12px;
  }
  
  .bar-group {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    flex: 1;
  }
  
  .chart-bar {
    width: 100%;
    min-height: 4px;
    border-radius: 2px;
    transition: height 0.5s ease;
  }
  
  .utilization-chart {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  
  .utilization-row {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  
  .agent-name {
    min-width: 100px;
  }
  
  .utilization-bar {
    flex: 1;
    height: 8px;
    background: var(--bg-accent);
    border-radius: 4px;
    overflow: hidden;
  }
  
  .utilization-fill {
    height: 100%;
    transition: width 0.5s ease;
  }
  
  .utilization-value {
    min-width: 45px;
    text-align: right;
  }
  
  .realtime-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
  }
  
  .realtime-metric {
    display: flex;
    flex-direction: column;
    gap: 8px;
    text-align: center;
    padding: 16px;
  }
  
  .pulse-icon {
    animation: pulse 2s infinite;
  }
</style>