<script lang="ts">
	import { accessibilityStore, type ColorTheme } from '$lib/stores/accessibilityStore';

	const themes: { value: ColorTheme; label: string; description: string; preview: { bg: string; text: string } }[] = [
		{
			value: 'light',
			label: 'Light',
			description: 'Standard light theme',
			preview: { bg: '#ffffff', text: '#1f2937' }
		},
		{
			value: 'dark',
			label: 'Dark',
			description: 'Reduced eye strain in low light',
			preview: { bg: '#1f2937', text: '#f9fafb' }
		},
		{
			value: 'cream',
			label: 'Cream (DY04)',
			description: 'Warm background reduces visual stress for dyslexia',
			preview: { bg: '#FFF8DC', text: '#1f2937' }
		},
		{
			value: 'high-contrast',
			label: 'High Contrast',
			description: 'Maximum contrast for low vision',
			preview: { bg: '#000000', text: '#ffffff' }
		},
		{
			value: 'blue-light',
			label: 'Blue Light Filter',
			description: 'Warmer tones reduce blue light exposure',
			preview: { bg: '#fef3e2', text: '#1f2937' }
		}
	];

	function selectTheme(theme: ColorTheme) {
		accessibilityStore.updateSetting('colorTheme', theme);
	}
</script>

<div class="space-y-6">
	<p class="text-sm text-surface-600">
		Choose a color theme that works best for your visual needs.
	</p>

	<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
		{#each themes as theme}
			<button
				on:click={() => selectTheme(theme.value)}
				class="p-4 rounded-lg border-2 transition-all text-left {$accessibilityStore.colorTheme === theme.value
					? 'border-primary-500 ring-2 ring-primary-200'
					: 'border-surface-200 hover:border-surface-300'}"
			>
				<!-- Preview Box -->
				<div
					class="w-full h-16 rounded-lg mb-3 flex items-center justify-center border"
					style="background-color: {theme.preview.bg}; color: {theme.preview.text}; border-color: {theme.value === 'light' ? '#e5e7eb' : theme.preview.bg}"
				>
					<span class="text-sm font-medium">Aa Bb Cc</span>
				</div>

				<div class="font-medium text-surface-900">{theme.label}</div>
				<div class="text-xs text-surface-600 mt-1">{theme.description}</div>

				{#if $accessibilityStore.colorTheme === theme.value}
					<div class="mt-2 flex items-center text-primary-600 text-sm">
						<svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
							<path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
						</svg>
						Active
					</div>
				{/if}
			</button>
		{/each}
	</div>

	<!-- Additional Options -->
	<div class="p-4 bg-surface-50 rounded-lg border border-surface-200 space-y-4">
		<h4 class="text-sm font-medium text-surface-900">Additional Visual Options</h4>

		<label class="flex items-center space-x-3">
			<input
				type="checkbox"
				checked={$accessibilityStore.reduceTransparency}
				on:change={() => accessibilityStore.updateSetting('reduceTransparency', !$accessibilityStore.reduceTransparency)}
				class="h-4 w-4 rounded border-surface-300 text-primary-600 focus:ring-primary-500"
			/>
			<div>
				<span class="text-sm text-surface-900">Reduce transparency</span>
				<p class="text-xs text-surface-600">Remove blur and transparency effects</p>
			</div>
		</label>
	</div>

	<!-- Accessibility Note -->
	<div class="p-4 bg-blue-50 border border-blue-200 rounded-lg">
		<div class="flex items-start space-x-3">
			<svg class="w-5 h-5 text-blue-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
			</svg>
			<div>
				<p class="text-sm text-blue-900">
					<strong>Cream background (DY04)</strong> is specifically recommended for users with dyslexia.
					The warm tone reduces visual stress and improves reading comfort.
				</p>
			</div>
		</div>
	</div>
</div>
