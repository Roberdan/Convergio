<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	
	interface Insight {
		id: string;
		type: string;
		severity: 'info' | 'warning' | 'critical' | 'success';
		title: string;
		description: string;
		recommendations: string[];
		metrics: Record<string, any>;
		timestamp: string;
		confidence: number;
		is_actionable: boolean;
	}
	
	interface ProactiveAction {
		id: string;
		type: string;
		status: string;
		title: string;
		description: string;
		priority: number;
		executed_at?: string;
		result?: any;
		error?: string;
	}
	
	interface SystemMetrics {
		events_processed: number;
		patterns_detected: number;
		insights_generated: number;
		actions_executed: number;
		actions_completed: number;
		actions_failed: number;
		system_health: number;
	}
	
	let insights: Insight[] = [];
	let actions: ProactiveAction[] = [];
	let metrics: SystemMetrics = {
		events_processed: 0,
		patterns_detected: 0,
		insights_generated: 0,
		actions_executed: 0,
		actions_completed: 0,
		actions_failed: 0,
		system_health: 100
	};
	
	let selectedInsight: Insight | null = null;
	let filterSeverity: string = 'all';
	let filterType: string = 'all';
	let autoRefresh = true;
	let refreshInterval: any;
	
	// WebSocket for real-time updates
	let ws: WebSocket | null = null;
	
	onMount(async () => {
		await loadInitialData();
		connectWebSocket();
		
		if (autoRefresh) {
			refreshInterval = setInterval(loadMetrics, 5000);
		}
	});
	
	onDestroy(() => {
		if (refreshInterval) {
			clearInterval(refreshInterval);
		}
		if (ws) {
			ws.close();
		}
	});
	
	async function loadInitialData() {
		await Promise.all([
			loadInsights(),
			loadActions(),
			loadMetrics()
		]);
	}
	
	async function loadInsights() {
		try {
			const response = await fetch('/api/v1/insights');
			if (response.ok) {
				insights = await response.json();
			}
		} catch (error) {
			console.error('Failed to load insights:', error);
		}
	}
	
	async function loadActions() {
		try {
			const response = await fetch('/api/v1/proactive-actions');
			if (response.ok) {
				actions = await response.json();
			}
		} catch (error) {
			console.error('Failed to load actions:', error);
		}
	}
	
	async function loadMetrics() {
		try {
			const response = await fetch('/api/v1/system-metrics');
			if (response.ok) {
				metrics = await response.json();
			}
		} catch (error) {
			console.error('Failed to load metrics:', error);
		}
	}
	
	function connectWebSocket() {
		const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
		ws = new WebSocket(`${protocol}//${window.location.host}/ws/coach`);
		
		ws.onmessage = (event) => {
			const data = JSON.parse(event.data);
			
			if (data.type === 'insight') {
				insights = [data.payload, ...insights].slice(0, 100);
			} else if (data.type === 'action') {
				actions = [data.payload, ...actions].slice(0, 100);
			} else if (data.type === 'metrics') {
				metrics = data.payload;
			}
		};
		
		ws.onerror = (error) => {
			console.error('WebSocket error:', error);
		};
		
		ws.onclose = () => {
			// Reconnect after 5 seconds
			setTimeout(connectWebSocket, 5000);
		};
	}
	
	async function takeAction(insight: Insight) {
		try {
			const response = await fetch('/api/v1/proactive-actions', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					insight_id: insight.id,
					auto_execute: true
				})
			});
			
			if (response.ok) {
				await loadActions();
			}
		} catch (error) {
			console.error('Failed to take action:', error);
		}
	}
	
	async function dismissInsight(insight: Insight) {
		insights = insights.filter(i => i.id !== insight.id);
		// In real implementation, would also update server
	}
	
	function getSeverityColor(severity: string): string {
		switch (severity) {
			case 'critical': return 'text-red-600 bg-red-100';
			case 'warning': return 'text-yellow-600 bg-yellow-100';
			case 'info': return 'text-blue-600 bg-blue-100';
			case 'success': return 'text-green-600 bg-green-100';
			default: return 'text-surface-600 bg-surface-100';
		}
	}
	
	function getSeverityIcon(severity: string): string {
		switch (severity) {
			case 'critical': return '🚨';
			case 'warning': return '⚠️';
			case 'info': return 'ℹ️';
			case 'success': return '✅';
			default: return '📌';
		}
	}
	
	function getActionStatusColor(status: string): string {
		switch (status) {
			case 'completed': return 'text-green-600';
			case 'executing': return 'text-blue-600';
			case 'failed': return 'text-red-600';
			case 'pending': return 'text-yellow-600';
			default: return 'text-surface-600';
		}
	}
	
	function formatTimestamp(timestamp: string): string {
		const date = new Date(timestamp);
		const now = new Date();
		const diff = now.getTime() - date.getTime();
		
		if (diff < 60000) return 'Just now';
		if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
		if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
		return date.toLocaleDateString();
	}
	
	$: filteredInsights = insights.filter(insight => {
		if (filterSeverity !== 'all' && insight.severity !== filterSeverity) return false;
		if (filterType !== 'all' && insight.type !== filterType) return false;
		return true;
	});
	
	$: systemHealthColor = metrics.system_health > 80 ? 'text-green-600' : 
	                       metrics.system_health > 60 ? 'text-yellow-600' : 'text-red-600';
</script>

<div class="coach-panel">
	<!-- Header -->
	<div class="panel-header">
		<div class="header-content">
			<h1 class="text-2xl font-bold">🤖 Ali's Coach Panel</h1>
			<p class="text-surface-600">Proactive System Intelligence & Insights</p>
		</div>
		
		<div class="header-actions">
			<label class="flex items-center gap-2">
				<input
					type="checkbox"
					bind:checked={autoRefresh}
					on:change={() => {
						if (autoRefresh) {
							refreshInterval = setInterval(loadMetrics, 5000);
						} else {
							clearInterval(refreshInterval);
						}
					}}
				/>
				Auto-refresh
			</label>
		</div>
	</div>
	
	<!-- Metrics Bar -->
	<div class="metrics-bar">
		<div class="metric-card">
			<div class="metric-value {systemHealthColor}">{metrics.system_health}%</div>
			<div class="metric-label">System Health</div>
		</div>
		
		<div class="metric-card">
			<div class="metric-value">{metrics.events_processed.toLocaleString()}</div>
			<div class="metric-label">Events Processed</div>
		</div>
		
		<div class="metric-card">
			<div class="metric-value">{metrics.insights_generated}</div>
			<div class="metric-label">Insights Generated</div>
		</div>
		
		<div class="metric-card">
			<div class="metric-value">{metrics.patterns_detected}</div>
			<div class="metric-label">Patterns Detected</div>
		</div>
		
		<div class="metric-card">
			<div class="metric-value text-green-600">{metrics.actions_completed}</div>
			<div class="metric-label">Actions Completed</div>
		</div>
		
		{#if metrics.actions_failed > 0}
			<div class="metric-card">
				<div class="metric-value text-red-600">{metrics.actions_failed}</div>
				<div class="metric-label">Actions Failed</div>
			</div>
		{/if}
	</div>
	
	<!-- Main Content -->
	<div class="main-content">
		<!-- Insights Section -->
		<div class="insights-section">
			<div class="section-header">
				<h2 class="text-lg font-semibold">System Insights</h2>
				
				<div class="filters">
					<select bind:value={filterSeverity} class="filter-select">
						<option value="all">All Severities</option>
						<option value="critical">Critical</option>
						<option value="warning">Warning</option>
						<option value="info">Info</option>
						<option value="success">Success</option>
					</select>
					
					<select bind:value={filterType} class="filter-select">
						<option value="all">All Types</option>
						<option value="performance">Performance</option>
						<option value="bottleneck">Bottleneck</option>
						<option value="risk">Risk</option>
						<option value="opportunity">Opportunity</option>
						<option value="anomaly">Anomaly</option>
					</select>
				</div>
			</div>
			
			<div class="insights-list">
				{#each filteredInsights as insight}
					<div
						class="insight-card"
						class:selected={selectedInsight?.id === insight.id}
						on:click={() => selectedInsight = insight}
						on:keydown={() => {}}
						role="button"
						tabindex="0"
					>
						<div class="insight-header">
							<span class="severity-badge {getSeverityColor(insight.severity)}">
								{getSeverityIcon(insight.severity)} {insight.severity}
							</span>
							<span class="insight-type">{insight.type}</span>
							<span class="insight-time">{formatTimestamp(insight.timestamp)}</span>
						</div>
						
						<h3 class="insight-title">{insight.title}</h3>
						<p class="insight-description">{insight.description}</p>
						
						<div class="insight-footer">
							<span class="confidence">
								Confidence: {Math.round(insight.confidence * 100)}%
							</span>
							
							{#if insight.is_actionable}
								<div class="insight-actions">
									<button
										on:click|stopPropagation={() => takeAction(insight)}
										class="btn-action"
									>
										Take Action
									</button>
									<button
										on:click|stopPropagation={() => dismissInsight(insight)}
										class="btn-dismiss"
									>
										Dismiss
									</button>
								</div>
							{/if}
						</div>
					</div>
				{/each}
				
				{#if filteredInsights.length === 0}
					<div class="empty-state">
						<p>No insights matching current filters</p>
					</div>
				{/if}
			</div>
		</div>
		
		<!-- Actions Section -->
		<div class="actions-section">
			<div class="section-header">
				<h2 class="text-lg font-semibold">Proactive Actions</h2>
			</div>
			
			<div class="actions-list">
				{#each actions as action}
					<div class="action-card">
						<div class="action-header">
							<span class="action-status {getActionStatusColor(action.status)}">
								{action.status}
							</span>
							<span class="action-priority">P{action.priority}</span>
						</div>
						
						<h4 class="action-title">{action.title}</h4>
						<p class="action-description">{action.description}</p>
						
						{#if action.executed_at}
							<div class="action-meta">
								Executed: {formatTimestamp(action.executed_at)}
							</div>
						{/if}
						
						{#if action.error}
							<div class="action-error">
								Error: {action.error}
							</div>
						{/if}
					</div>
				{/each}
				
				{#if actions.length === 0}
					<div class="empty-state">
						<p>No recent actions</p>
					</div>
				{/if}
			</div>
		</div>
	</div>
	
	<!-- Insight Details Panel -->
	{#if selectedInsight}
		<div class="detail-panel">
			<div class="panel-header">
				<h3 class="font-semibold">Insight Details</h3>
				<button on:click={() => selectedInsight = null} class="close-btn">×</button>
			</div>
			
			<div class="panel-content">
				<div class="detail-section">
					<h4>Description</h4>
					<p>{selectedInsight.description}</p>
				</div>
				
				{#if selectedInsight.recommendations.length > 0}
					<div class="detail-section">
						<h4>Recommendations</h4>
						<ul class="recommendations-list">
							{#each selectedInsight.recommendations as rec}
								<li>{rec}</li>
							{/each}
						</ul>
					</div>
				{/if}
				
				{#if Object.keys(selectedInsight.metrics).length > 0}
					<div class="detail-section">
						<h4>Metrics</h4>
						<div class="metrics-grid">
							{#each Object.entries(selectedInsight.metrics) as [key, value]}
								<div class="metric-item">
									<span class="metric-key">{key}:</span>
									<span class="metric-value">{value}</span>
								</div>
							{/each}
						</div>
					</div>
				{/if}
			</div>
		</div>
	{/if}
</div>

<style>
	.coach-panel {
		height: 100vh;
		display: flex;
		flex-direction: column;
		background: #f9fafb;
		position: relative;
	}
	
	.panel-header {
		background: white;
		padding: 1.5rem 2rem;
		border-bottom: 1px solid #e5e7eb;
		display: flex;
		justify-content: space-between;
		align-items: center;
	}
	
	.metrics-bar {
		background: white;
		padding: 1rem 2rem;
		border-bottom: 1px solid #e5e7eb;
		display: flex;
		gap: 2rem;
	}
	
	.metric-card {
		text-align: center;
	}
	
	.metric-value {
		font-size: 1.5rem;
		font-weight: bold;
	}
	
	.metric-label {
		font-size: 0.75rem;
		color: #6b7280;
		margin-top: 0.25rem;
	}
	
	.main-content {
		flex: 1;
		display: grid;
		grid-template-columns: 2fr 1fr;
		gap: 1.5rem;
		padding: 1.5rem;
		overflow: hidden;
	}
	
	.insights-section, .actions-section {
		background: white;
		border-radius: 8px;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}
	
	.section-header {
		padding: 1rem 1.5rem;
		border-bottom: 1px solid #e5e7eb;
		display: flex;
		justify-content: space-between;
		align-items: center;
	}
	
	.filters {
		display: flex;
		gap: 0.5rem;
	}
	
	.filter-select {
		padding: 0.25rem 0.5rem;
		border: 1px solid #e5e7eb;
		border-radius: 4px;
		font-size: 0.875rem;
	}
	
	.insights-list, .actions-list {
		flex: 1;
		overflow-y: auto;
		padding: 1rem;
	}
	
	.insight-card {
		background: #f9fafb;
		border: 1px solid #e5e7eb;
		border-radius: 6px;
		padding: 1rem;
		margin-bottom: 0.75rem;
		cursor: pointer;
		transition: all 0.2s;
	}
	
	.insight-card:hover {
		background: #f3f4f6;
		border-color: #d1d5db;
	}
	
	.insight-card.selected {
		background: #eff6ff;
		border-color: #3b82f6;
	}
	
	.insight-header {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		margin-bottom: 0.5rem;
		font-size: 0.75rem;
	}
	
	.severity-badge {
		padding: 0.125rem 0.5rem;
		border-radius: 12px;
		font-weight: 500;
	}
	
	.insight-type {
		color: #6b7280;
	}
	
	.insight-time {
		margin-left: auto;
		color: #9ca3af;
	}
	
	.insight-title {
		font-weight: 600;
		margin-bottom: 0.25rem;
	}
	
	.insight-description {
		color: #6b7280;
		font-size: 0.875rem;
		margin-bottom: 0.75rem;
	}
	
	.insight-footer {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}
	
	.confidence {
		font-size: 0.75rem;
		color: #6b7280;
	}
	
	.insight-actions {
		display: flex;
		gap: 0.5rem;
	}
	
	.btn-action, .btn-dismiss {
		padding: 0.25rem 0.75rem;
		border-radius: 4px;
		font-size: 0.75rem;
		border: none;
		cursor: pointer;
		transition: all 0.2s;
	}
	
	.btn-action {
		background: #3b82f6;
		color: white;
	}
	
	.btn-action:hover {
		background: #2563eb;
	}
	
	.btn-dismiss {
		background: #e5e7eb;
		color: #6b7280;
	}
	
	.btn-dismiss:hover {
		background: #d1d5db;
	}
	
	.action-card {
		background: #f9fafb;
		border: 1px solid #e5e7eb;
		border-radius: 6px;
		padding: 0.75rem;
		margin-bottom: 0.5rem;
	}
	
	.action-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 0.5rem;
		font-size: 0.75rem;
	}
	
	.action-status {
		font-weight: 500;
		text-transform: uppercase;
	}
	
	.action-priority {
		color: #6b7280;
	}
	
	.action-title {
		font-weight: 600;
		font-size: 0.875rem;
		margin-bottom: 0.25rem;
	}
	
	.action-description {
		color: #6b7280;
		font-size: 0.75rem;
	}
	
	.action-meta {
		font-size: 0.625rem;
		color: #9ca3af;
		margin-top: 0.5rem;
	}
	
	.action-error {
		font-size: 0.75rem;
		color: #ef4444;
		margin-top: 0.5rem;
	}
	
	.detail-panel {
		position: absolute;
		right: 0;
		top: 0;
		bottom: 0;
		width: 400px;
		background: white;
		border-left: 1px solid #e5e7eb;
		box-shadow: -4px 0 6px rgba(0, 0, 0, 0.05);
		z-index: 10;
		display: flex;
		flex-direction: column;
	}
	
	.detail-panel .panel-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1rem 1.5rem;
		border-bottom: 1px solid #e5e7eb;
	}
	
	.close-btn {
		background: none;
		border: none;
		font-size: 24px;
		cursor: pointer;
		color: #6b7280;
	}
	
	.panel-content {
		flex: 1;
		overflow-y: auto;
		padding: 1.5rem;
	}
	
	.detail-section {
		margin-bottom: 1.5rem;
	}
	
	.detail-section h4 {
		font-weight: 600;
		margin-bottom: 0.5rem;
		color: #374151;
	}
	
	.recommendations-list {
		list-style: disc;
		margin-left: 1.5rem;
		color: #6b7280;
		font-size: 0.875rem;
	}
	
	.recommendations-list li {
		margin-bottom: 0.25rem;
	}
	
	.metrics-grid {
		display: grid;
		gap: 0.5rem;
		font-size: 0.875rem;
	}
	
	.metric-item {
		display: flex;
		justify-content: space-between;
	}
	
	.metric-key {
		color: #6b7280;
	}
	
	.metric-value {
		font-weight: 500;
		color: #111827;
	}
	
	.empty-state {
		text-align: center;
		padding: 2rem;
		color: #9ca3af;
	}
</style>