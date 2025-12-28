<script lang="ts">
	import { accessibilityStore } from '$lib/stores/accessibilityStore';

	function handleBreakIntervalChange(e: Event) {
		const target = e.target as HTMLInputElement;
		accessibilityStore.updateSetting('breakIntervalMinutes', parseInt(target.value));
	}
</script>

<div class="space-y-6">
	<p class="text-sm text-surface-600">
		Focus mode helps reduce distractions and improve concentration. Ideal for users with ADHD.
	</p>

	<!-- Focus Mode Toggle -->
	<div class="p-4 bg-white rounded-lg border border-surface-200">
		<div class="flex items-start justify-between">
			<div class="flex-1">
				<h4 class="text-sm font-medium text-surface-900">Enable Focus Mode (AD04)</h4>
				<p class="text-sm text-surface-600 mt-1">
					Hides non-essential UI elements and creates a distraction-free environment.
				</p>
			</div>
			<label class="relative inline-flex items-center cursor-pointer ml-4">
				<input
					type="checkbox"
					checked={$accessibilityStore.focusModeEnabled}
					on:change={() => accessibilityStore.updateSetting('focusModeEnabled', !$accessibilityStore.focusModeEnabled)}
					class="sr-only peer"
				/>
				<div class="w-11 h-6 bg-surface-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-100 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-surface-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
			</label>
		</div>
	</div>

	<!-- ADHD Support Options -->
	<div class="space-y-4">
		<h4 class="text-sm font-medium text-surface-900">ADHD Support Features</h4>

		<!-- Progress Bars (AD02) -->
		<label class="flex items-center justify-between p-4 bg-white rounded-lg border border-surface-200">
			<div>
				<span class="text-sm text-surface-900">Show Progress Bars (AD02)</span>
				<p class="text-xs text-surface-600">Visual progress indicators for all tasks</p>
			</div>
			<input
				type="checkbox"
				checked={$accessibilityStore.showProgressBars}
				on:change={() => accessibilityStore.updateSetting('showProgressBars', !$accessibilityStore.showProgressBars)}
				class="h-4 w-4 rounded border-surface-300 text-primary-600 focus:ring-primary-500"
			/>
		</label>

		<!-- Micro-celebrations (AD03) -->
		<label class="flex items-center justify-between p-4 bg-white rounded-lg border border-surface-200">
			<div>
				<span class="text-sm text-surface-900">Micro-celebrations (AD03)</span>
				<p class="text-xs text-surface-600">Subtle animations when completing tasks</p>
			</div>
			<input
				type="checkbox"
				checked={$accessibilityStore.microCelebrations}
				on:change={() => accessibilityStore.updateSetting('microCelebrations', !$accessibilityStore.microCelebrations)}
				class="h-4 w-4 rounded border-surface-300 text-primary-600 focus:ring-primary-500"
			/>
		</label>

		<!-- Break Reminders (AD05) -->
		<div class="p-4 bg-white rounded-lg border border-surface-200 space-y-3">
			<label class="flex items-center justify-between">
				<div>
					<span class="text-sm text-surface-900">Break Reminders (AD05)</span>
					<p class="text-xs text-surface-600">Pomodoro-style reminders to take breaks</p>
				</div>
				<input
					type="checkbox"
					checked={$accessibilityStore.breakReminders}
					on:change={() => accessibilityStore.updateSetting('breakReminders', !$accessibilityStore.breakReminders)}
					class="h-4 w-4 rounded border-surface-300 text-primary-600 focus:ring-primary-500"
				/>
			</label>

			{#if $accessibilityStore.breakReminders}
				<div class="pt-3 border-t border-surface-100">
					<div class="flex items-center justify-between mb-2">
						<label for="break-interval" class="text-sm text-surface-700">Break interval</label>
						<span class="text-sm text-surface-600">{$accessibilityStore.breakIntervalMinutes} minutes</span>
					</div>
					<input
						id="break-interval"
						type="range"
						min="15"
						max="60"
						step="5"
						value={$accessibilityStore.breakIntervalMinutes}
						on:input={handleBreakIntervalChange}
						class="w-full h-2 bg-surface-200 rounded-lg appearance-none cursor-pointer"
					/>
				</div>
			{/if}
		</div>

		<!-- Max Bullet Points (AD01) -->
		<div class="p-4 bg-white rounded-lg border border-surface-200">
			<div class="flex items-center justify-between mb-2">
				<div>
					<span class="text-sm text-surface-900">Max Bullet Points (AD01)</span>
					<p class="text-xs text-surface-600">Limit information density per section</p>
				</div>
				<span class="text-sm text-surface-600">{$accessibilityStore.maxBulletPoints}</span>
			</div>
			<input
				type="range"
				min="3"
				max="10"
				step="1"
				value={$accessibilityStore.maxBulletPoints}
				on:input={(e) => accessibilityStore.updateSetting('maxBulletPoints', parseInt((e.target as HTMLInputElement).value))}
				class="w-full h-2 bg-surface-200 rounded-lg appearance-none cursor-pointer"
			/>
			<p class="text-xs text-surface-500 mt-1">Recommended: 4 points max for ADHD support</p>
		</div>
	</div>

	<!-- Focus Mode Preview -->
	{#if $accessibilityStore.focusModeEnabled}
		<div class="p-4 bg-green-50 border border-green-200 rounded-lg">
			<div class="flex items-start space-x-3">
				<svg class="w-5 h-5 text-green-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
				</svg>
				<div>
					<h4 class="text-sm font-medium text-green-900">Focus Mode Active</h4>
					<ul class="text-sm text-green-700 mt-1 space-y-1">
						<li>Sidebar collapsed by default</li>
						<li>Notifications minimized</li>
						<li>Non-essential widgets hidden</li>
						<li>Keyboard shortcuts available: Esc to exit</li>
					</ul>
				</div>
			</div>
		</div>
	{/if}
</div>
