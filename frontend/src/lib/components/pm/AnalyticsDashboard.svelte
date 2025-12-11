<script lang="ts">
	import { onMount } from 'svelte';
	import { projectsService } from '$lib/services/projectsService';

	// Props
	export let projectId: string | undefined = undefined;

	// Interfaces
	interface ProjectMetrics {
		velocity: number;
		burnRate: number;
		cycleTime: number;
		leadTime: number;
		defectRate: number;
		reworkPercentage: number;
		teamUtilization: number;
		aiUtilization: number;
		costVariance: number;
		roi: number;
		predictedCompletion: string;
		riskScore: number;
	}

	interface TimeSeriesData {
		date: string;
		value: number;
		target?: number;
	}

	interface TeamMember {
		name: string;
		tasksCompleted: number;
		efficiency: number;
		hoursLogged: number;
	}

	// State
	let metrics: ProjectMetrics | null = null;
	let velocityData: TimeSeriesData[] = [];
	let burndownData: TimeSeriesData[] = [];
	let teamPerformance: TeamMember[] = [];
	let loading = false;
	let selectedMetric = 'overview';

	// Mock data for demonstration
	const mockMetrics: ProjectMetrics = {
		velocity: 34,
		burnRate: 15000,
		cycleTime: 3.2,
		leadTime: 7.8,
		defectRate: 2.1,
		reworkPercentage: 8.5,
		teamUtilization: 87,
		aiUtilization: 65,
		costVariance: -5.2,
		roi: 142,
		predictedCompletion: '2024-06-15',
		riskScore: 23
	};

	const mockVelocityData: TimeSeriesData[] = [
		{ date: '2024-01-15', value: 28, target: 30 },
		{ date: '2024-01-22', value: 32, target: 30 },
		{ date: '2024-01-29', value: 29, target: 30 },
		{ date: '2024-02-05', value: 35, target: 32 },
		{ date: '2024-02-12', value: 38, target: 32 },
		{ date: '2024-02-19', value: 34, target: 32 }
	];

	const mockBurndownData: TimeSeriesData[] = [
		{ date: '2024-01-01', value: 100, target: 100 },
		{ date: '2024-01-15', value: 85, target: 87 },
		{ date: '2024-02-01', value: 68, target: 75 },
		{ date: '2024-02-15', value: 52, target: 62 },
		{ date: '2024-03-01', value: 38, target: 50 },
		{ date: '2024-03-15', value: 25, target: 37 }
	];

	const mockTeamPerformance: TeamMember[] = [
		{ name: 'Alice Chen', tasksCompleted: 12, efficiency: 94, hoursLogged: 160 },
		{ name: 'Bob Wilson', tasksCompleted: 15, efficiency: 89, hoursLogged: 180 },
		{ name: 'Carol Davis', tasksCompleted: 8, efficiency: 91, hoursLogged: 140 },
		{ name: 'Eva Rodriguez', tasksCompleted: 11, efficiency: 87, hoursLogged: 165 },
		{ name: 'Ali AI Agent', tasksCompleted: 45, efficiency: 98, hoursLogged: 24 }
	];

	onMount(async () => {
		await loadAnalytics();
	});

	async function loadAnalytics() {
		loading = true;
		try {
			// TODO: Load real analytics data from backend
			await new Promise(resolve => setTimeout(resolve, 800));
			
			metrics = mockMetrics;
			velocityData = mockVelocityData;
			burndownData = mockBurndownData;
			teamPerformance = mockTeamPerformance;
		} catch (error) {
			console.error('Error loading analytics:', error);
		} finally {
			loading = false;
		}
	}

	function getMetricColor(value: number, isGood: boolean = true) {
		if (isGood) {
			return value >= 80 ? 'text-success-600' : value >= 60 ? 'text-warning-600' : 'text-error-600';
		} else {
			return value <= 20 ? 'text-success-600' : value <= 40 ? 'text-warning-600' : 'text-error-600';
		}
	}

	function getRiskColor(score: number) {
		if (score <= 25) return 'text-success-600 bg-success-50 border-success-200';
		if (score <= 50) return 'text-warning-600 bg-warning-50 border-warning-200';
		return 'text-error-600 bg-error-50 border-error-200';
	}

	function formatCurrency(value: number) {
		return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value);
	}

	function formatDate(dateStr: string) {
		return new Date(dateStr).toLocaleDateString('en-US', { 
			month: 'short', 
			day: 'numeric',
			year: 'numeric'
		});
	}
</script>

<div class="analytics-dashboard bg-white rounded-xl shadow-sm border border-surface-200  overflow-hidden">
	<!-- Header -->
	<div class="p-6 border-b border-surface-200  bg-surface-50 ">
		<div class="flex items-center justify-between">
			<div>
				<h3 class="text-lg font-semibold text-surface-900 ">Project Analytics</h3>
				<p class="text-sm text-surface-600 ">Performance metrics, insights, and predictive analytics</p>
			</div>
			<div class="flex items-center space-x-3">
				<select bind:value={selectedMetric} class="input input-sm">
					<option value="overview">Overview</option>
					<option value="velocity">Velocity Trends</option>
					<option value="burndown">Burndown Chart</option>
					<option value="team">Team Performance</option>
					<option value="quality">Quality Metrics</option>
				</select>
				<button class="btn-secondary btn-sm">
					<svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3M3 17V7a2 2 0 012-2h6l2 2h6a2 2 0 012 2v10a2 2 0 01-2 2H5a2 2 0 01-2-2z" />
					</svg>
					Export Report
				</button>
			</div>
		</div>
	</div>

	{#if loading}
		<div class="flex items-center justify-center py-12">
			<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
		</div>
	{:else if metrics}
		<div class="p-6">
			{#if selectedMetric === 'overview'}
				<!-- Overview Metrics -->
				<div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 mb-8">
					<div class="metric-card p-4 border border-surface-200  rounded-lg">
						<div class="text-xs text-surface-500 mb-1">Velocity</div>
						<div class="text-2xl font-bold {getMetricColor(metrics.velocity, true)}">{metrics.velocity}</div>
						<div class="text-xs text-surface-400">story points/sprint</div>
					</div>
					<div class="metric-card p-4 border border-surface-200  rounded-lg">
						<div class="text-xs text-surface-500 mb-1">Burn Rate</div>
						<div class="text-2xl font-bold text-surface-900 ">{formatCurrency(metrics.burnRate)}</div>
						<div class="text-xs text-surface-400">per sprint</div>
					</div>
					<div class="metric-card p-4 border border-surface-200  rounded-lg">
						<div class="text-xs text-surface-500 mb-1">Cycle Time</div>
						<div class="text-2xl font-bold {getMetricColor(100 - metrics.cycleTime * 10, true)}">{metrics.cycleTime}</div>
						<div class="text-xs text-surface-400">days</div>
					</div>
					<div class="metric-card p-4 border border-surface-200  rounded-lg">
						<div class="text-xs text-surface-500 mb-1">Lead Time</div>
						<div class="text-2xl font-bold {getMetricColor(100 - metrics.leadTime * 10, true)}">{metrics.leadTime}</div>
						<div class="text-xs text-surface-400">days</div>
					</div>
					<div class="metric-card p-4 border border-surface-200  rounded-lg">
						<div class="text-xs text-surface-500 mb-1">Team Utilization</div>
						<div class="text-2xl font-bold {getMetricColor(metrics.teamUtilization, true)}">{metrics.teamUtilization}%</div>
						<div class="text-xs text-surface-400">capacity used</div>
					</div>
					<div class="metric-card p-4 border border-surface-200  rounded-lg">
						<div class="text-xs text-surface-500 mb-1">ROI</div>
						<div class="text-2xl font-bold {getMetricColor(metrics.roi, true)}">{metrics.roi}%</div>
						<div class="text-xs text-surface-400">return on investment</div>
					</div>
				</div>

				<!-- Quality & Risk Metrics -->
				<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
					<div class="card">
						<div class="card-header">
							<h4 class="font-semibold">Quality Metrics</h4>
						</div>
						<div class="card-content space-y-3">
							<div class="flex items-center justify-between">
								<span class="text-sm text-surface-600 ">Defect Rate</span>
								<span class="text-sm font-medium {getMetricColor(100 - metrics.defectRate * 10, false)}">{metrics.defectRate}%</span>
							</div>
							<div class="flex items-center justify-between">
								<span class="text-sm text-surface-600 ">Rework</span>
								<span class="text-sm font-medium {getMetricColor(100 - metrics.reworkPercentage * 2, false)}">{metrics.reworkPercentage}%</span>
							</div>
						</div>
					</div>

					<div class="card">
						<div class="card-header">
							<h4 class="font-semibold">AI Integration</h4>
						</div>
						<div class="card-content space-y-3">
							<div class="flex items-center justify-between">
								<span class="text-sm text-surface-600 ">AI Utilization</span>
								<span class="text-sm font-medium {getMetricColor(metrics.aiUtilization, true)}">{metrics.aiUtilization}%</span>
							</div>
							<div class="w-full bg-surface-200  rounded-full h-2">
								<div class="bg-purple-500 h-2 rounded-full transition-all duration-500" style="width: {metrics.aiUtilization}%"></div>
							</div>
						</div>
					</div>

					<div class="card">
						<div class="card-header">
							<h4 class="font-semibold">Risk Assessment</h4>
						</div>
						<div class="card-content">
							<div class="flex items-center justify-between mb-2">
								<span class="text-sm text-surface-600 ">Risk Score</span>
								<span class="px-2 py-1 rounded-full text-xs font-medium border {getRiskColor(metrics.riskScore)}">
									{metrics.riskScore}
								</span>
							</div>
							<div class="text-xs text-surface-500">
								Predicted completion: {formatDate(metrics.predictedCompletion)}
							</div>
						</div>
					</div>
				</div>

				<!-- Charts Preview -->
				<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
					<div class="card">
						<div class="card-header">
							<h4 class="font-semibold">Velocity Trend</h4>
						</div>
						<div class="card-content">
							<div class="chart-container h-32 bg-surface-50  rounded-lg flex items-center justify-center">
								<div class="text-surface-500 text-sm">📈 Velocity trending upward (+12% this sprint)</div>
							</div>
						</div>
					</div>

					<div class="card">
						<div class="card-header">
							<h4 class="font-semibold">Burndown Progress</h4>
						</div>
						<div class="card-content">
							<div class="chart-container h-32 bg-surface-50  rounded-lg flex items-center justify-center">
								<div class="text-surface-500 text-sm">📉 On track (3% ahead of schedule)</div>
							</div>
						</div>
					</div>
				</div>

			{:else if selectedMetric === 'velocity'}
				<!-- Velocity Analysis -->
				<div class="space-y-6">
					<div class="card">
						<div class="card-header">
							<h4 class="font-semibold">Sprint Velocity Analysis</h4>
							<p class="text-sm text-surface-600 ">Story points completed per sprint</p>
						</div>
						<div class="card-content">
							<div class="chart-container h-64 bg-surface-50  rounded-lg p-4">
								<div class="grid grid-cols-6 gap-4 h-full">
									{#each velocityData as data, i}
										<div class="flex flex-col items-center justify-end space-y-2">
											<div class="text-xs text-surface-500">{data.value}</div>
											<div class="w-full bg-primary-500 rounded-t" style="height: {(data.value / 40) * 100}%"></div>
											<div class="w-full h-1 bg-surface-300 rounded" style="height: {((data.target || 0) / 40) * 100}%"></div>
											<div class="text-xs text-surface-400 transform rotate-45 origin-left">{data.date.slice(5)}</div>
										</div>
									{/each}
								</div>
							</div>
						</div>
					</div>
				</div>

			{:else if selectedMetric === 'team'}
				<!-- Team Performance -->
				<div class="space-y-6">
					<div class="card">
						<div class="card-header">
							<h4 class="font-semibold">Team Performance Breakdown</h4>
						</div>
						<div class="card-content">
							<div class="space-y-4">
								{#each teamPerformance as member}
									<div class="flex items-center justify-between p-4 bg-surface-50  rounded-lg">
										<div class="flex items-center space-x-3">
											<div class="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-600 rounded-full flex items-center justify-center">
												<span class="text-white font-semibold text-sm">
													{member.name.includes('AI') ? '🤖' : member.name.charAt(0)}
												</span>
											</div>
											<div>
												<div class="font-medium text-surface-900 ">{member.name}</div>
												<div class="text-sm text-surface-600 ">{member.hoursLogged}h logged</div>
											</div>
										</div>
										<div class="grid grid-cols-2 gap-6 text-center">
											<div>
												<div class="text-sm text-surface-500">Tasks</div>
												<div class="font-semibold text-surface-900 ">{member.tasksCompleted}</div>
											</div>
											<div>
												<div class="text-sm text-surface-500">Efficiency</div>
												<div class="font-semibold {getMetricColor(member.efficiency, true)}">{member.efficiency}%</div>
											</div>
										</div>
									</div>
								{/each}
							</div>
						</div>
					</div>
				</div>

			{:else if selectedMetric === 'quality'}
				<!-- Quality Metrics Detail -->
				<div class="space-y-6">
					<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
						<div class="card">
							<div class="card-header">
								<h4 class="font-semibold">Code Quality</h4>
							</div>
							<div class="card-content space-y-4">
								<div class="flex items-center justify-between">
									<span class="text-sm text-surface-600 ">Defect Rate</span>
									<span class="text-lg font-semibold {getMetricColor(100 - metrics.defectRate * 10, false)}">{metrics.defectRate}%</span>
								</div>
								<div class="flex items-center justify-between">
									<span class="text-sm text-surface-600 ">Rework Percentage</span>
									<span class="text-lg font-semibold {getMetricColor(100 - metrics.reworkPercentage * 2, false)}">{metrics.reworkPercentage}%</span>
								</div>
								<div class="flex items-center justify-between">
									<span class="text-sm text-surface-600 ">Code Coverage</span>
									<span class="text-lg font-semibold text-success-600">87%</span>
								</div>
							</div>
						</div>

						<div class="card">
							<div class="card-header">
								<h4 class="font-semibold">Process Efficiency</h4>
							</div>
							<div class="card-content space-y-4">
								<div class="flex items-center justify-between">
									<span class="text-sm text-surface-600 ">Cycle Time</span>
									<span class="text-lg font-semibold {getMetricColor(100 - metrics.cycleTime * 10, true)}">{metrics.cycleTime} days</span>
								</div>
								<div class="flex items-center justify-between">
									<span class="text-sm text-surface-600 ">Lead Time</span>
									<span class="text-lg font-semibold {getMetricColor(100 - metrics.leadTime * 10, true)}">{metrics.leadTime} days</span>
								</div>
								<div class="flex items-center justify-between">
									<span class="text-sm text-surface-600 ">Deployment Frequency</span>
									<span class="text-lg font-semibold text-success-600">2.3/week</span>
								</div>
							</div>
						</div>
					</div>
				</div>
			{/if}
		</div>
	{/if}
</div>

<style>
	.metric-card {
		background: linear-gradient(135deg, rgb(248 250 252) 0%, rgb(241 245 249) 100%);
		transition: transform 0.2s ease, box-shadow 0.2s ease;
	}
	
	.metric-card:hover {
		transform: translateY(-2px);
		box-shadow: 0 4px 12px rgb(0 0 0 / 0.1);
	}
	
	:global(.dark) .metric-card {
		background: linear-gradient(135deg, rgb(15 23 42) 0%, rgb(30 41 59) 100%);
	}
	
	.chart-container {
		min-height: 200px;
	}
</style>