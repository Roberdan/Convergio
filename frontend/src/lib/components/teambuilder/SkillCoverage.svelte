<script lang="ts">
	export let skillCoverage: {
		covered: string[];
		missing: string[];
		coverage: number;
		skillDetails: Array<{
			skill: string;
			covered: boolean;
			resources: string[];
			bestLevel: string;
		}>;
	};

	function getLevelColor(level: string) {
		switch (level) {
			case 'expert': return 'text-purple-600';
			case 'advanced': return 'text-blue-600';
			case 'intermediate': return 'text-green-600';
			case 'beginner': return 'text-yellow-600';
			default: return 'text-surface-600';
		}
	}

	function getCoverageColor(coverage: number) {
		if (coverage >= 90) return 'text-success-600';
		if (coverage >= 70) return 'text-warning-600';
		if (coverage >= 50) return 'text-orange-600';
		return 'text-error-600';
	}

	function getCoverageBarColor(coverage: number) {
		if (coverage >= 90) return 'bg-success-500';
		if (coverage >= 70) return 'bg-warning-500';
		if (coverage >= 50) return 'bg-orange-500';
		return 'bg-error-500';
	}
</script>

<div class="skill-coverage bg-white rounded-xl shadow-sm border border-surface-200 p-4">
	<div class="flex items-center justify-between mb-4">
		<h3 class="text-sm font-semibold text-surface-700 uppercase tracking-wider">Skill Coverage</h3>
		<span class="text-lg font-bold {getCoverageColor(skillCoverage.coverage)}">
			{skillCoverage.coverage}%
		</span>
	</div>

	<!-- Coverage Bar -->
	<div class="mb-4">
		<div class="w-full bg-surface-200 rounded-full h-3">
			<div
				class="h-3 rounded-full transition-all duration-500 {getCoverageBarColor(skillCoverage.coverage)}"
				style="width: {skillCoverage.coverage}%"
			></div>
		</div>
		<div class="flex justify-between mt-1 text-xs text-surface-500">
			<span>{skillCoverage.covered.length} covered</span>
			<span>{skillCoverage.missing.length} missing</span>
		</div>
	</div>

	<!-- Skill Details -->
	<div class="space-y-2 max-h-[200px] overflow-y-auto">
		{#each skillCoverage.skillDetails as skill}
			<div class="flex items-center gap-2 p-2 rounded-lg {skill.covered ? 'bg-success-50' : 'bg-error-50'}">
				{#if skill.covered}
					<svg class="w-4 h-4 text-success-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
					</svg>
				{:else}
					<svg class="w-4 h-4 text-error-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
					</svg>
				{/if}
				<div class="flex-1 min-w-0">
					<div class="flex items-center gap-2">
						<span class="text-sm font-medium text-surface-900">{skill.skill}</span>
						{#if skill.covered}
							<span class="text-xs {getLevelColor(skill.bestLevel)}">({skill.bestLevel})</span>
						{/if}
					</div>
					{#if skill.covered && skill.resources.length > 0}
						<div class="text-xs text-surface-500 truncate">
							{skill.resources.slice(0, 2).join(', ')}
							{#if skill.resources.length > 2}
								+{skill.resources.length - 2}
							{/if}
						</div>
					{/if}
				</div>
			</div>
		{/each}
	</div>

	<!-- Missing Skills Warning -->
	{#if skillCoverage.missing.length > 0}
		<div class="mt-4 p-3 bg-warning-50 border border-warning-100 rounded-lg">
			<div class="flex items-start gap-2">
				<svg class="w-4 h-4 text-warning-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
				</svg>
				<div>
					<div class="text-sm font-medium text-warning-700">Missing Skills</div>
					<div class="text-xs text-warning-600 mt-1">
						Consider adding resources with: {skillCoverage.missing.join(', ')}
					</div>
				</div>
			</div>
		</div>
	{/if}
</div>
