<script lang="ts">
	import { accessibilityStore } from '$lib/stores/accessibilityStore';
</script>

<div class="space-y-6">
	<p class="text-sm text-surface-600">
		Control animations and motion effects throughout the application.
	</p>

	<!-- Reduce Motion -->
	<div class="p-4 bg-white rounded-lg border border-surface-200">
		<div class="flex items-start justify-between">
			<div class="flex-1">
				<h4 class="text-sm font-medium text-surface-900">Reduce Motion (AU04)</h4>
				<p class="text-sm text-surface-600 mt-1">
					Minimizes animations, transitions, and moving elements. Recommended for users sensitive to motion or with vestibular disorders.
				</p>
			</div>
			<label class="relative inline-flex items-center cursor-pointer ml-4">
				<input
					type="checkbox"
					checked={$accessibilityStore.reduceMotion}
					on:change={() => accessibilityStore.updateSetting('reduceMotion', !$accessibilityStore.reduceMotion)}
					class="sr-only peer"
				/>
				<div class="w-11 h-6 bg-surface-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-100 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-surface-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
			</label>
		</div>

		{#if $accessibilityStore.reduceMotion}
			<div class="mt-3 p-3 bg-green-50 rounded-lg">
				<div class="flex items-center text-green-700 text-sm">
					<svg class="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
						<path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
					</svg>
					Motion reduced - animations are now minimal
				</div>
			</div>
		{/if}
	</div>

	<!-- Demo Area -->
	<div class="p-4 bg-surface-50 rounded-lg border border-surface-200">
		<h4 class="text-sm font-medium text-surface-900 mb-3">Animation Preview</h4>
		<div class="flex items-center space-x-4">
			<div
				class="w-12 h-12 bg-primary-500 rounded-lg {$accessibilityStore.reduceMotion ? '' : 'animate-bounce'}"
			></div>
			<div>
				<p class="text-sm text-surface-600">
					{#if $accessibilityStore.reduceMotion}
						Animations are disabled
					{:else}
						Animations are enabled
					{/if}
				</p>
			</div>
		</div>
	</div>

	<!-- System Preference Notice -->
	<div class="p-4 bg-blue-50 border border-blue-200 rounded-lg">
		<div class="flex items-start space-x-3">
			<svg class="w-5 h-5 text-blue-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
			</svg>
			<div>
				<p class="text-sm text-blue-900">
					Your operating system's "Reduce Motion" preference is automatically detected.
					You can override it here.
				</p>
			</div>
		</div>
	</div>

	<!-- What Gets Affected -->
	<div class="p-4 bg-white rounded-lg border border-surface-200">
		<h4 class="text-sm font-medium text-surface-900 mb-3">What changes with reduced motion:</h4>
		<ul class="space-y-2 text-sm text-surface-600">
			<li class="flex items-center">
				<svg class="w-4 h-4 mr-2 text-surface-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
				</svg>
				Page transitions become instant
			</li>
			<li class="flex items-center">
				<svg class="w-4 h-4 mr-2 text-surface-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
				</svg>
				Loading spinners are simplified
			</li>
			<li class="flex items-center">
				<svg class="w-4 h-4 mr-2 text-surface-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
				</svg>
				Hover effects are reduced
			</li>
			<li class="flex items-center">
				<svg class="w-4 h-4 mr-2 text-surface-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
				</svg>
				Auto-scrolling is disabled
			</li>
		</ul>
	</div>
</div>
