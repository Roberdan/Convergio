<script lang="ts">
	export let costEstimate: { hourly: number; daily: number; monthly: number };
	export let memberCount = 0;
</script>

<div class="team-cost-estimate bg-white rounded-xl shadow-sm border border-surface-200 p-4">
	<h3 class="text-sm font-semibold text-surface-700 uppercase tracking-wider mb-4">Cost Estimate</h3>

	{#if memberCount === 0}
		<div class="text-center py-4 text-surface-500 text-sm">
			Add team members to see cost estimate
		</div>
	{:else}
		<div class="space-y-3">
			<!-- Hourly -->
			<div class="flex items-center justify-between p-3 bg-surface-50 rounded-lg">
				<div>
					<div class="text-sm text-surface-600">Hourly Rate</div>
					<div class="text-xs text-surface-400">Per hour combined</div>
				</div>
				<div class="text-right">
					<div class="text-lg font-bold text-surface-900">${costEstimate.hourly.toLocaleString()}</div>
				</div>
			</div>

			<!-- Daily -->
			<div class="flex items-center justify-between p-3 bg-surface-50 rounded-lg">
				<div>
					<div class="text-sm text-surface-600">Daily Rate</div>
					<div class="text-xs text-surface-400">8 hours/day</div>
				</div>
				<div class="text-right">
					<div class="text-lg font-bold text-surface-900">${costEstimate.daily.toLocaleString()}</div>
				</div>
			</div>

			<!-- Monthly -->
			<div class="flex items-center justify-between p-3 bg-primary-50 rounded-lg border border-primary-100">
				<div>
					<div class="text-sm text-primary-700 font-medium">Monthly Estimate</div>
					<div class="text-xs text-primary-600">20 working days</div>
				</div>
				<div class="text-right">
					<div class="text-xl font-bold text-primary-700">${costEstimate.monthly.toLocaleString()}</div>
				</div>
			</div>
		</div>

		<!-- Team size note -->
		<div class="mt-4 pt-4 border-t border-surface-200 text-center">
			<span class="text-sm text-surface-600">
				Based on {memberCount} team member{memberCount !== 1 ? 's' : ''}
			</span>
		</div>
	{/if}
</div>
