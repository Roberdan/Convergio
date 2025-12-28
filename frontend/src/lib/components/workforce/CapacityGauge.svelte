<script lang="ts">
	import type { UnifiedResource } from '$lib/types/resource';

	export let resources: UnifiedResource[] = [];

	// Calculate capacity metrics
	$: metrics = calculateMetrics(resources);

	function calculateMetrics(resources: UnifiedResource[]) {
		const talents = resources.filter(r => r.type === 'talent');
		const agents = resources.filter(r => r.type === 'agent');

		const totalCapacity = resources.length * 100;
		const usedCapacity = resources.reduce((sum, r) => sum + r.utilization, 0);
		const availableCapacity = totalCapacity - usedCapacity;

		const talentCapacity = talents.reduce((sum, r) => sum + r.availability, 0);
		const agentCapacity = agents.reduce((sum, r) => sum + r.availability, 0);

		return {
			total: resources.length,
			talents: talents.length,
			agents: agents.length,
			totalCapacity,
			usedCapacity,
			availableCapacity,
			utilizationPercent: totalCapacity > 0 ? Math.round((usedCapacity / totalCapacity) * 100) : 0,
			talentCapacity,
			agentCapacity
		};
	}

	function getGaugeColor(percent: number) {
		if (percent >= 90) return '#ef4444'; // red
		if (percent >= 75) return '#f59e0b'; // amber
		if (percent >= 50) return '#3b82f6'; // blue
		return '#22c55e'; // green
	}

	$: gaugeColor = getGaugeColor(metrics.utilizationPercent);
	$: dashArray = `${metrics.utilizationPercent * 2.51327} 251.327`;
</script>

<div class="capacity-gauge bg-white rounded-xl shadow-sm border border-surface-200 p-6">
	<h3 class="text-lg font-semibold text-surface-900 mb-4">Capacity Overview</h3>

	<div class="flex items-center justify-center gap-8">
		<!-- Main Gauge -->
		<div class="relative w-40 h-40">
			<svg class="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
				<!-- Background circle -->
				<circle
					cx="50"
					cy="50"
					r="40"
					fill="none"
					stroke="#e5e7eb"
					stroke-width="8"
				/>
				<!-- Progress circle -->
				<circle
					cx="50"
					cy="50"
					r="40"
					fill="none"
					stroke={gaugeColor}
					stroke-width="8"
					stroke-linecap="round"
					stroke-dasharray={dashArray}
					class="transition-all duration-1000"
				/>
			</svg>
			<div class="absolute inset-0 flex flex-col items-center justify-center">
				<span class="text-3xl font-bold" style="color: {gaugeColor}">{metrics.utilizationPercent}%</span>
				<span class="text-xs text-surface-500">Utilized</span>
			</div>
		</div>

		<!-- Metrics -->
		<div class="space-y-4">
			<div>
				<div class="text-sm text-surface-600">Total Resources</div>
				<div class="text-2xl font-bold text-surface-900">{metrics.total}</div>
			</div>

			<div class="flex gap-4">
				<div>
					<div class="flex items-center gap-2">
						<div class="w-3 h-3 rounded-full bg-blue-500"></div>
						<span class="text-sm text-surface-600">Talents</span>
					</div>
					<div class="text-lg font-semibold text-surface-900">{metrics.talents}</div>
				</div>
				<div>
					<div class="flex items-center gap-2">
						<div class="w-3 h-3 rounded-full bg-purple-500"></div>
						<span class="text-sm text-surface-600">Agents</span>
					</div>
					<div class="text-lg font-semibold text-surface-900">{metrics.agents}</div>
				</div>
			</div>

			<div>
				<div class="text-sm text-surface-600">Available Capacity</div>
				<div class="text-lg font-semibold text-success-600">{metrics.availableCapacity}%</div>
			</div>
		</div>
	</div>

	<!-- Capacity Bars -->
	<div class="mt-6 pt-6 border-t border-surface-200">
		<div class="grid grid-cols-2 gap-4">
			<!-- Talent Capacity -->
			<div>
				<div class="flex items-center justify-between mb-1">
					<span class="text-sm text-surface-600">Talent Capacity</span>
					<span class="text-sm font-medium text-blue-600">{metrics.talentCapacity}%</span>
				</div>
				<div class="w-full bg-surface-200 rounded-full h-2">
					<div
						class="bg-blue-500 h-2 rounded-full transition-all duration-500"
						style="width: {Math.min(metrics.talentCapacity, 100)}%"
					></div>
				</div>
			</div>

			<!-- Agent Capacity -->
			<div>
				<div class="flex items-center justify-between mb-1">
					<span class="text-sm text-surface-600">Agent Capacity</span>
					<span class="text-sm font-medium text-purple-600">{metrics.agentCapacity}%</span>
				</div>
				<div class="w-full bg-surface-200 rounded-full h-2">
					<div
						class="bg-purple-500 h-2 rounded-full transition-all duration-500"
						style="width: {Math.min(metrics.agentCapacity, 100)}%"
					></div>
				</div>
			</div>
		</div>
	</div>
</div>
