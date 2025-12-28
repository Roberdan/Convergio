<script lang="ts">
	import type { UnifiedResource } from '$lib/types/resource';

	export let resources: UnifiedResource[] = [];

	interface SkillData {
		name: string;
		count: number;
		levels: { beginner: number; intermediate: number; advanced: number; expert: number };
		resources: string[];
	}

	// Calculate skill matrix from resources
	$: skillMatrix = calculateSkillMatrix(resources);

	function calculateSkillMatrix(resources: UnifiedResource[]): SkillData[] {
		const skillMap = new Map<string, SkillData>();

		resources.forEach(resource => {
			resource.skills.forEach(skill => {
				const existing = skillMap.get(skill.name) || {
					name: skill.name,
					count: 0,
					levels: { beginner: 0, intermediate: 0, advanced: 0, expert: 0 },
					resources: []
				};

				existing.count++;
				existing.levels[skill.level]++;
				existing.resources.push(resource.name);
				skillMap.set(skill.name, existing);
			});
		});

		return Array.from(skillMap.values())
			.sort((a, b) => b.count - a.count)
			.slice(0, 12); // Top 12 skills
	}

	function getLevelColor(level: string) {
		switch (level) {
			case 'expert': return 'bg-purple-500';
			case 'advanced': return 'bg-blue-500';
			case 'intermediate': return 'bg-green-500';
			case 'beginner': return 'bg-yellow-500';
			default: return 'bg-surface-300';
		}
	}
</script>

<div class="skill-matrix bg-white rounded-xl shadow-sm border border-surface-200 p-6">
	<div class="flex items-center justify-between mb-4">
		<h3 class="text-lg font-semibold text-surface-900">Skill Distribution</h3>
		<div class="flex items-center gap-4 text-xs">
			<div class="flex items-center gap-1">
				<div class="w-3 h-3 rounded-full bg-purple-500"></div>
				<span>Expert</span>
			</div>
			<div class="flex items-center gap-1">
				<div class="w-3 h-3 rounded-full bg-blue-500"></div>
				<span>Advanced</span>
			</div>
			<div class="flex items-center gap-1">
				<div class="w-3 h-3 rounded-full bg-green-500"></div>
				<span>Intermediate</span>
			</div>
			<div class="flex items-center gap-1">
				<div class="w-3 h-3 rounded-full bg-yellow-500"></div>
				<span>Beginner</span>
			</div>
		</div>
	</div>

	{#if skillMatrix.length === 0}
		<div class="text-center py-8 text-surface-500">
			No skill data available
		</div>
	{:else}
		<div class="space-y-3">
			{#each skillMatrix as skill}
				<div class="skill-row">
					<div class="flex items-center justify-between mb-1">
						<span class="text-sm font-medium text-surface-900">{skill.name}</span>
						<span class="text-sm text-surface-600">{skill.count} resource{skill.count !== 1 ? 's' : ''}</span>
					</div>
					<div class="flex h-4 rounded-full overflow-hidden bg-surface-100">
						{#if skill.levels.expert > 0}
							<div
								class="bg-purple-500"
								style="width: {(skill.levels.expert / skill.count) * 100}%"
								title="{skill.levels.expert} Expert"
							></div>
						{/if}
						{#if skill.levels.advanced > 0}
							<div
								class="bg-blue-500"
								style="width: {(skill.levels.advanced / skill.count) * 100}%"
								title="{skill.levels.advanced} Advanced"
							></div>
						{/if}
						{#if skill.levels.intermediate > 0}
							<div
								class="bg-green-500"
								style="width: {(skill.levels.intermediate / skill.count) * 100}%"
								title="{skill.levels.intermediate} Intermediate"
							></div>
						{/if}
						{#if skill.levels.beginner > 0}
							<div
								class="bg-yellow-500"
								style="width: {(skill.levels.beginner / skill.count) * 100}%"
								title="{skill.levels.beginner} Beginner"
							></div>
						{/if}
					</div>
					<div class="mt-1 flex flex-wrap gap-1">
						{#each skill.resources.slice(0, 4) as resourceName}
							<span class="text-xs text-surface-500">{resourceName}</span>
							{#if skill.resources.indexOf(resourceName) < Math.min(skill.resources.length - 1, 3)}
								<span class="text-xs text-surface-400">-</span>
							{/if}
						{/each}
						{#if skill.resources.length > 4}
							<span class="text-xs text-surface-400">+{skill.resources.length - 4} more</span>
						{/if}
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>
