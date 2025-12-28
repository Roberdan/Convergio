<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { writable } from 'svelte/store';
  import { notify } from '$lib/stores/notifications';
  
  export let refreshInterval: number = 5000; // 5 seconds
  export let wsEndpoint: string = 'ws://localhost:9000/ws/metrics';
  
  interface Metric {
    id: string;
    name: string;
    value: number;
    unit: string;
    trend: 'up' | 'down' | 'stable';
    change: number;
    sparkline: number[];
    timestamp: Date;
  }
  
  interface SystemMetrics {
    cpu: number;
    memory: number;
    disk: number;
    network: {
      in: number;
      out: number;
    };
  }
  
  interface AgentMetrics {
    totalAgents: number;
    activeAgents: number;
    totalExecutions: number;
    avgResponseTime: number;
    successRate: number;
    errorRate: number;
  }
  
  interface CostMetrics {
    totalCost: number;
    costPerHour: number;
    tokensUsed: number;
    apiCalls: number;
    projectedMonthlyCost: number;
  }
  
  interface ActivityMetrics {
    activeUsers: number;
    totalSessions: number;
    avgSessionDuration: number;
    peakConcurrentUsers: number;
    requestsPerMinute: number;
  }
  
  let ws: WebSocket | null = null;
  let isConnected = false;
  let lastUpdate = new Date();
  let autoRefresh = true;
  let refreshTimer: NodeJS.Timeout;
  
  // Metrics stores
  let systemMetrics = writable<SystemMetrics>({
    cpu: 0,
    memory: 0,
    disk: 0,
    network: { in: 0, out: 0 }
  });
  
  let agentMetrics = writable<AgentMetrics>({
    totalAgents: 0,
    activeAgents: 0,
    totalExecutions: 0,
    avgResponseTime: 0,
    successRate: 0,
    errorRate: 0
  });
  
  let costMetrics = writable<CostMetrics>({
    totalCost: 0,
    costPerHour: 0,
    tokensUsed: 0,
    apiCalls: 0,
    projectedMonthlyCost: 0
  });
  
  let activityMetrics = writable<ActivityMetrics>({
    activeUsers: 0,
    totalSessions: 0,
    avgSessionDuration: 0,
    peakConcurrentUsers: 0,
    requestsPerMinute: 0
  });
  
  let customMetrics = writable<Metric[]>([]);
  
  // Chart data
  let chartData = {
    cpu: Array(20).fill(0),
    memory: Array(20).fill(0),
    requests: Array(20).fill(0),
    responseTime: Array(20).fill(0)
  };
  
  function connectWebSocket() {
    if (ws) {
      ws.close();
    }
    
    ws = new WebSocket(wsEndpoint);
    
    ws.onopen = () => {
      isConnected = true;
      notify.success('Metrics Connected', 'Real-time metrics stream established');
      requestMetrics();
    };
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleMetricsUpdate(data);
      } catch {
        // Silent failure
      }
    };

    ws.onerror = () => {
      notify.error('Connection Error', 'Failed to connect to metrics stream');
    };

    ws.onclose = () => {
      isConnected = false;
      // Reconnect after 5 seconds
      setTimeout(() => {
        if (autoRefresh) {
          connectWebSocket();
        }
      }, 5000);
    };
  }
  
  function handleMetricsUpdate(data: any) {
    lastUpdate = new Date();
    
    switch (data.type) {
      case 'system':
        systemMetrics.set(data.metrics);
        updateChart('cpu', data.metrics.cpu);
        updateChart('memory', data.metrics.memory);
        break;
        
      case 'agents':
        agentMetrics.set(data.metrics);
        updateChart('responseTime', data.metrics.avgResponseTime);
        break;
        
      case 'costs':
        costMetrics.set(data.metrics);
        break;
        
      case 'activity':
        activityMetrics.set(data.metrics);
        updateChart('requests', data.metrics.requestsPerMinute);
        break;
        
      case 'custom':
        customMetrics.update(metrics => {
          const existing = metrics.find(m => m.id === data.metric.id);
          if (existing) {
            return metrics.map(m => 
              m.id === data.metric.id ? data.metric : m
            );
          } else {
            return [...metrics, data.metric];
          }
        });
        break;
        
      default:
        // Handle all metrics update
        if (data.system) systemMetrics.set(data.system);
        if (data.agents) agentMetrics.set(data.agents);
        if (data.costs) costMetrics.set(data.costs);
        if (data.activity) activityMetrics.set(data.activity);
        if (data.custom) customMetrics.set(data.custom);
    }
  }
  
  function updateChart(key: keyof typeof chartData, value: number) {
    chartData[key] = [...chartData[key].slice(1), value];
  }
  
  function requestMetrics() {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ action: 'get_metrics' }));
    }
  }
  
  async function fetchMetrics() {
    try {
      const response = await fetch('/api/metrics');
      if (response.ok) {
        const data = await response.json();
        handleMetricsUpdate(data);
      }
    } catch {
      // Silent failure
    }
  }
  
  function formatNumber(num: number): string {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K';
    }
    return num.toFixed(0);
  }
  
  function formatDuration(seconds: number): string {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`;
    }
    return `${secs}s`;
  }
  
  function getSparklinePath(data: number[], width: number, height: number): string {
    if (data.length < 2) return '';
    
    const max = Math.max(...data);
    const min = Math.min(...data);
    const range = max - min || 1;
    
    const points = data.map((value, index) => {
      const x = (index / (data.length - 1)) * width;
      const y = height - ((value - min) / range) * height;
      return `${x},${y}`;
    });
    
    return `M ${points.join(' L ')}`;
  }
  
  function toggleAutoRefresh() {
    autoRefresh = !autoRefresh;
    if (autoRefresh) {
      startAutoRefresh();
      connectWebSocket();
    } else {
      stopAutoRefresh();
      if (ws) ws.close();
    }
  }
  
  function startAutoRefresh() {
    refreshTimer = setInterval(() => {
      if (!isConnected) {
        fetchMetrics();
      }
    }, refreshInterval);
  }
  
  function stopAutoRefresh() {
    if (refreshTimer) {
      clearInterval(refreshTimer);
    }
  }
  
  onMount(() => {
    connectWebSocket();
    startAutoRefresh();
  });
  
  onDestroy(() => {
    stopAutoRefresh();
    if (ws) {
      ws.close();
    }
  });
</script>

<div class="metrics-dashboard">
  <div class="dashboard-header">
    <div class="header-left">
      <h2>📊 Real-time Metrics Dashboard</h2>
      <div class="connection-status" class:connected={isConnected}>
        {isConnected ? '🟢 Live' : '🔴 Offline'}
      </div>
      <span class="last-update">
        Last update: {lastUpdate.toLocaleTimeString()}
      </span>
    </div>
    <div class="header-actions">
      <button 
        class="refresh-toggle"
        class:active={autoRefresh}
        on:click={toggleAutoRefresh}
      >
        {autoRefresh ? '⏸️ Pause' : '▶️ Resume'} Auto-refresh
      </button>
      <button 
        class="manual-refresh"
        on:click={fetchMetrics}
        disabled={isConnected}
      >
        🔄 Refresh
      </button>
    </div>
  </div>
  
  <!-- System Metrics -->
  <div class="metrics-section">
    <h3>System Resources</h3>
    <div class="metrics-grid">
      <div class="metric-card">
        <div class="metric-header">
          <span class="metric-label">CPU Usage</span>
          <span class="metric-value">{$systemMetrics.cpu.toFixed(1)}%</span>
        </div>
        <div class="metric-chart">
          <svg viewBox="0 0 100 40" class="sparkline">
            <path 
              d={getSparklinePath(chartData.cpu, 100, 40)}
              fill="none"
              stroke="#3b82f6"
              stroke-width="2"
            />
          </svg>
        </div>
        <div class="metric-bar">
          <div 
            class="metric-bar-fill"
            style="width: {$systemMetrics.cpu}%; background: {$systemMetrics.cpu > 80 ? '#ef4444' : $systemMetrics.cpu > 60 ? '#f59e0b' : '#10b981'}"
          ></div>
        </div>
      </div>
      
      <div class="metric-card">
        <div class="metric-header">
          <span class="metric-label">Memory</span>
          <span class="metric-value">{$systemMetrics.memory.toFixed(1)}%</span>
        </div>
        <div class="metric-chart">
          <svg viewBox="0 0 100 40" class="sparkline">
            <path 
              d={getSparklinePath(chartData.memory, 100, 40)}
              fill="none"
              stroke="#8b5cf6"
              stroke-width="2"
            />
          </svg>
        </div>
        <div class="metric-bar">
          <div 
            class="metric-bar-fill"
            style="width: {$systemMetrics.memory}%; background: {$systemMetrics.memory > 85 ? '#ef4444' : $systemMetrics.memory > 70 ? '#f59e0b' : '#10b981'}"
          ></div>
        </div>
      </div>
      
      <div class="metric-card">
        <div class="metric-header">
          <span class="metric-label">Disk Usage</span>
          <span class="metric-value">{$systemMetrics.disk.toFixed(1)}%</span>
        </div>
        <div class="metric-stat">
          <div class="stat-icon">💾</div>
          <div class="stat-details">
            <span class="stat-label">Available</span>
            <span class="stat-value">{(100 - $systemMetrics.disk).toFixed(1)}%</span>
          </div>
        </div>
      </div>
      
      <div class="metric-card">
        <div class="metric-header">
          <span class="metric-label">Network I/O</span>
          <span class="metric-value">
            ↓ {formatNumber($systemMetrics.network.in)} / ↑ {formatNumber($systemMetrics.network.out)}
          </span>
        </div>
        <div class="metric-stat">
          <div class="stat-icon">🌐</div>
          <div class="stat-details">
            <span class="stat-label">Total</span>
            <span class="stat-value">
              {formatNumber($systemMetrics.network.in + $systemMetrics.network.out)} KB/s
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
  
  <!-- Agent Metrics -->
  <div class="metrics-section">
    <h3>Agent Performance</h3>
    <div class="metrics-grid">
      <div class="metric-card">
        <div class="metric-header">
          <span class="metric-label">Active Agents</span>
          <span class="metric-value">{$agentMetrics.activeAgents} / {$agentMetrics.totalAgents}</span>
        </div>
        <div class="metric-stat">
          <div class="stat-icon">🤖</div>
          <div class="stat-details">
            <span class="stat-label">Utilization</span>
            <span class="stat-value">
              {(($agentMetrics.activeAgents / $agentMetrics.totalAgents) * 100).toFixed(0)}%
            </span>
          </div>
        </div>
      </div>
      
      <div class="metric-card">
        <div class="metric-header">
          <span class="metric-label">Executions</span>
          <span class="metric-value">{formatNumber($agentMetrics.totalExecutions)}</span>
        </div>
        <div class="metric-stat">
          <div class="stat-icon">⚡</div>
          <div class="stat-details">
            <span class="stat-label">Success Rate</span>
            <span class="stat-value" style="color: {$agentMetrics.successRate > 95 ? '#10b981' : '#f59e0b'}">
              {$agentMetrics.successRate.toFixed(1)}%
            </span>
          </div>
        </div>
      </div>
      
      <div class="metric-card">
        <div class="metric-header">
          <span class="metric-label">Avg Response Time</span>
          <span class="metric-value">{$agentMetrics.avgResponseTime.toFixed(0)}ms</span>
        </div>
        <div class="metric-chart">
          <svg viewBox="0 0 100 40" class="sparkline">
            <path 
              d={getSparklinePath(chartData.responseTime, 100, 40)}
              fill="none"
              stroke="#10b981"
              stroke-width="2"
            />
          </svg>
        </div>
      </div>
      
      <div class="metric-card">
        <div class="metric-header">
          <span class="metric-label">Error Rate</span>
          <span class="metric-value" style="color: {$agentMetrics.errorRate > 5 ? '#ef4444' : '#10b981'}">
            {$agentMetrics.errorRate.toFixed(2)}%
          </span>
        </div>
        <div class="metric-stat">
          <div class="stat-icon">⚠️</div>
          <div class="stat-details">
            <span class="stat-label">Last Hour</span>
            <span class="stat-value">{Math.round($agentMetrics.totalExecutions * $agentMetrics.errorRate / 100)} errors</span>
          </div>
        </div>
      </div>
    </div>
  </div>
  
  <!-- Cost Metrics -->
  <div class="metrics-section">
    <h3>Cost Analysis</h3>
    <div class="metrics-grid">
      <div class="metric-card highlight">
        <div class="metric-header">
          <span class="metric-label">Total Cost Today</span>
          <span class="metric-value">${$costMetrics.totalCost.toFixed(2)}</span>
        </div>
        <div class="metric-stat">
          <div class="stat-icon">💰</div>
          <div class="stat-details">
            <span class="stat-label">Per Hour</span>
            <span class="stat-value">${$costMetrics.costPerHour.toFixed(2)}</span>
          </div>
        </div>
      </div>
      
      <div class="metric-card">
        <div class="metric-header">
          <span class="metric-label">Tokens Used</span>
          <span class="metric-value">{formatNumber($costMetrics.tokensUsed)}</span>
        </div>
        <div class="metric-stat">
          <div class="stat-icon">📝</div>
          <div class="stat-details">
            <span class="stat-label">API Calls</span>
            <span class="stat-value">{formatNumber($costMetrics.apiCalls)}</span>
          </div>
        </div>
      </div>
      
      <div class="metric-card">
        <div class="metric-header">
          <span class="metric-label">Projected Monthly</span>
          <span class="metric-value">${$costMetrics.projectedMonthlyCost.toFixed(0)}</span>
        </div>
        <div class="metric-trend" class:up={$costMetrics.projectedMonthlyCost > 1000}>
          {$costMetrics.projectedMonthlyCost > 1000 ? '📈' : '📉'} 
          {$costMetrics.projectedMonthlyCost > 1000 ? 'Above' : 'Below'} budget
        </div>
      </div>
    </div>
  </div>
  
  <!-- Activity Metrics -->
  <div class="metrics-section">
    <h3>User Activity</h3>
    <div class="metrics-grid">
      <div class="metric-card">
        <div class="metric-header">
          <span class="metric-label">Active Users</span>
          <span class="metric-value">{$activityMetrics.activeUsers}</span>
        </div>
        <div class="metric-stat">
          <div class="stat-icon">👥</div>
          <div class="stat-details">
            <span class="stat-label">Peak Today</span>
            <span class="stat-value">{$activityMetrics.peakConcurrentUsers}</span>
          </div>
        </div>
      </div>
      
      <div class="metric-card">
        <div class="metric-header">
          <span class="metric-label">Sessions</span>
          <span class="metric-value">{formatNumber($activityMetrics.totalSessions)}</span>
        </div>
        <div class="metric-stat">
          <div class="stat-icon">📊</div>
          <div class="stat-details">
            <span class="stat-label">Avg Duration</span>
            <span class="stat-value">{formatDuration($activityMetrics.avgSessionDuration)}</span>
          </div>
        </div>
      </div>
      
      <div class="metric-card">
        <div class="metric-header">
          <span class="metric-label">Requests/min</span>
          <span class="metric-value">{$activityMetrics.requestsPerMinute}</span>
        </div>
        <div class="metric-chart">
          <svg viewBox="0 0 100 40" class="sparkline">
            <path 
              d={getSparklinePath(chartData.requests, 100, 40)}
              fill="none"
              stroke="#f59e0b"
              stroke-width="2"
            />
          </svg>
        </div>
      </div>
    </div>
  </div>
  
  <!-- Custom Metrics -->
  {#if $customMetrics.length > 0}
    <div class="metrics-section">
      <h3>Custom Metrics</h3>
      <div class="metrics-grid">
        {#each $customMetrics as metric (metric.id)}
          <div class="metric-card">
            <div class="metric-header">
              <span class="metric-label">{metric.name}</span>
              <span class="metric-value">
                {metric.value.toFixed(2)} {metric.unit}
              </span>
            </div>
            {#if metric.sparkline && metric.sparkline.length > 0}
              <div class="metric-chart">
                <svg viewBox="0 0 100 40" class="sparkline">
                  <path 
                    d={getSparklinePath(metric.sparkline, 100, 40)}
                    fill="none"
                    stroke="#6366f1"
                    stroke-width="2"
                  />
                </svg>
              </div>
            {/if}
            <div class="metric-trend-indicator">
              {#if metric.trend === 'up'}
                <span class="trend up">↑ {metric.change.toFixed(1)}%</span>
              {:else if metric.trend === 'down'}
                <span class="trend down">↓ {metric.change.toFixed(1)}%</span>
              {:else}
                <span class="trend stable">→ Stable</span>
              {/if}
            </div>
          </div>
        {/each}
      </div>
    </div>
  {/if}
</div>

<style>
  .metrics-dashboard {
    padding: 2rem;
    background: #f9fafb;
    min-height: 100vh;
  }
  
  .dashboard-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
    padding: 1.5rem;
    background: white;
    border-radius: 12px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  }
  
  .header-left {
    display: flex;
    align-items: center;
    gap: 1rem;
  }
  
  .header-left h2 {
    margin: 0;
    font-size: 1.5rem;
    color: #1f2937;
  }
  
  .connection-status {
    padding: 0.25rem 0.75rem;
    background: #fee2e2;
    border-radius: 20px;
    font-size: 0.875rem;
    font-weight: 500;
  }
  
  .connection-status.connected {
    background: #dcfce7;
  }
  
  .last-update {
    color: #6b7280;
    font-size: 0.875rem;
  }
  
  .header-actions {
    display: flex;
    gap: 0.5rem;
  }
  
  .refresh-toggle,
  .manual-refresh {
    padding: 0.5rem 1rem;
    border: 1px solid #d1d5db;
    background: white;
    border-radius: 6px;
    font-size: 0.875rem;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .refresh-toggle.active {
    background: #4f46e5;
    color: white;
    border-color: #4f46e5;
  }
  
  .manual-refresh:hover:not(:disabled) {
    background: #f3f4f6;
  }
  
  .manual-refresh:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  .metrics-section {
    margin-bottom: 2rem;
  }
  
  .metrics-section h3 {
    margin: 0 0 1rem 0;
    font-size: 1.25rem;
    color: #374151;
  }
  
  .metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 1rem;
  }
  
  .metric-card {
    padding: 1.25rem;
    background: white;
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    transition: transform 0.2s, box-shadow 0.2s;
  }
  
  .metric-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  }
  
  .metric-card.highlight {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
  }
  
  .metric-card.highlight .metric-label,
  .metric-card.highlight .stat-label {
    color: rgba(255, 255, 255, 0.9);
  }
  
  .metric-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }
  
  .metric-label {
    font-size: 0.875rem;
    color: #6b7280;
    font-weight: 500;
  }
  
  .metric-value {
    font-size: 1.5rem;
    font-weight: 600;
    color: #1f2937;
  }
  
  .metric-chart {
    height: 40px;
    margin: 1rem 0;
  }
  
  .sparkline {
    width: 100%;
    height: 100%;
  }
  
  .metric-bar {
    height: 6px;
    background: #e5e7eb;
    border-radius: 3px;
    overflow: hidden;
    margin-top: 1rem;
  }
  
  .metric-bar-fill {
    height: 100%;
    transition: width 0.3s ease;
    border-radius: 3px;
  }
  
  .metric-stat {
    display: flex;
    align-items: center;
    gap: 1rem;
  }
  
  .stat-icon {
    font-size: 2rem;
  }
  
  .stat-details {
    display: flex;
    flex-direction: column;
  }
  
  .stat-label {
    font-size: 0.75rem;
    color: #9ca3af;
  }
  
  .stat-value {
    font-size: 1.125rem;
    font-weight: 600;
    color: #1f2937;
  }
  
  .metric-trend {
    padding: 0.25rem 0.5rem;
    background: #fef3c7;
    color: #92400e;
    border-radius: 4px;
    font-size: 0.875rem;
    text-align: center;
    margin-top: 0.5rem;
  }
  
  .metric-trend.up {
    background: #fee2e2;
    color: #991b1b;
  }
  
  .metric-trend-indicator {
    margin-top: 0.75rem;
  }
  
  .trend {
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.875rem;
    font-weight: 500;
  }
  
  .trend.up {
    background: #dcfce7;
    color: #166534;
  }
  
  .trend.down {
    background: #fee2e2;
    color: #991b1b;
  }
  
  .trend.stable {
    background: #e0e7ff;
    color: #3730a3;
  }
</style>