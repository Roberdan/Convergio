<script lang="ts">
	import { accessibilityStore, type FontFamily } from '$lib/stores/accessibilityStore';

	const fontOptions: { value: FontFamily; label: string; description: string }[] = [
		{ value: 'system', label: 'System Default', description: 'Uses your device\'s default font' },
		{ value: 'opendyslexic', label: 'OpenDyslexic', description: 'Designed for readers with dyslexia' },
		{ value: 'arial', label: 'Arial', description: 'Clean, easy-to-read sans-serif' },
		{ value: 'verdana', label: 'Verdana', description: 'Wide letters, good spacing' },
		{ value: 'times', label: 'Times New Roman', description: 'Traditional serif font' }
	];

	function handleFontSizeChange(e: Event) {
		const target = e.target as HTMLInputElement;
		accessibilityStore.updateSetting('fontSize', parseInt(target.value));
	}

	function handleLineHeightChange(e: Event) {
		const target = e.target as HTMLInputElement;
		accessibilityStore.updateSetting('lineHeight', parseFloat(target.value));
	}

	function handleLetterSpacingChange(e: Event) {
		const target = e.target as HTMLInputElement;
		accessibilityStore.updateSetting('letterSpacing', parseFloat(target.value));
	}

	function handleMaxWidthChange(e: Event) {
		const target = e.target as HTMLInputElement;
		accessibilityStore.updateSetting('maxLineWidth', parseInt(target.value));
	}
</script>

<div class="space-y-6">
	<!-- Font Family -->
	<div>
		<label class="block text-sm font-medium text-surface-900 mb-3">Font Family</label>
		<div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
			{#each fontOptions as font}
				<button
					on:click={() => accessibilityStore.updateSetting('fontFamily', font.value)}
					class="p-3 text-left rounded-lg border-2 transition-all {$accessibilityStore.fontFamily === font.value
						? 'border-primary-500 bg-primary-50'
						: 'border-surface-200 hover:border-surface-300'}"
				>
					<div class="font-medium text-surface-900" style="font-family: {font.value === 'system' ? 'inherit' : font.label}">{font.label}</div>
					<div class="text-xs text-surface-600 mt-1">{font.description}</div>
				</button>
			{/each}
		</div>
	</div>

	<!-- Font Size -->
	<div>
		<div class="flex items-center justify-between mb-2">
			<label for="font-size" class="text-sm font-medium text-surface-900">Font Size</label>
			<span class="text-sm text-surface-600">{$accessibilityStore.fontSize}%</span>
		</div>
		<input
			id="font-size"
			type="range"
			min="80"
			max="150"
			step="10"
			value={$accessibilityStore.fontSize}
			on:input={handleFontSizeChange}
			class="w-full h-2 bg-surface-200 rounded-lg appearance-none cursor-pointer"
		/>
		<div class="flex justify-between text-xs text-surface-500 mt-1">
			<span>Small (80%)</span>
			<span>Normal (100%)</span>
			<span>Large (150%)</span>
		</div>
	</div>

	<!-- Line Height (DY02) -->
	<div>
		<div class="flex items-center justify-between mb-2">
			<label for="line-height" class="text-sm font-medium text-surface-900">Line Spacing</label>
			<span class="text-sm text-surface-600">{$accessibilityStore.lineHeight}x</span>
		</div>
		<input
			id="line-height"
			type="range"
			min="1.2"
			max="2.5"
			step="0.1"
			value={$accessibilityStore.lineHeight}
			on:input={handleLineHeightChange}
			class="w-full h-2 bg-surface-200 rounded-lg appearance-none cursor-pointer"
		/>
		<div class="flex justify-between text-xs text-surface-500 mt-1">
			<span>Compact</span>
			<span>Normal (1.5x)</span>
			<span>Spacious</span>
		</div>
		<p class="text-xs text-surface-500 mt-2">
			Recommended: 1.5x or higher for dyslexia support (DY02)
		</p>
	</div>

	<!-- Letter Spacing -->
	<div>
		<div class="flex items-center justify-between mb-2">
			<label for="letter-spacing" class="text-sm font-medium text-surface-900">Letter Spacing</label>
			<span class="text-sm text-surface-600">{$accessibilityStore.letterSpacing}em</span>
		</div>
		<input
			id="letter-spacing"
			type="range"
			min="0"
			max="0.15"
			step="0.01"
			value={$accessibilityStore.letterSpacing}
			on:input={handleLetterSpacingChange}
			class="w-full h-2 bg-surface-200 rounded-lg appearance-none cursor-pointer"
		/>
	</div>

	<!-- Max Line Width (DY03) -->
	<div>
		<div class="flex items-center justify-between mb-2">
			<label for="max-width" class="text-sm font-medium text-surface-900">Maximum Line Width</label>
			<span class="text-sm text-surface-600">{$accessibilityStore.maxLineWidth} characters</span>
		</div>
		<input
			id="max-width"
			type="range"
			min="40"
			max="120"
			step="5"
			value={$accessibilityStore.maxLineWidth}
			on:input={handleMaxWidthChange}
			class="w-full h-2 bg-surface-200 rounded-lg appearance-none cursor-pointer"
		/>
		<p class="text-xs text-surface-500 mt-2">
			Recommended: 60 characters for optimal readability (DY03)
		</p>
	</div>

	<!-- Preview -->
	<div class="p-4 bg-surface-50 rounded-lg border border-surface-200">
		<div class="text-xs text-surface-500 mb-2">Preview</div>
		<p
			style="
				font-family: var(--a11y-font-family);
				font-size: calc(1rem * {$accessibilityStore.fontSize / 100});
				line-height: {$accessibilityStore.lineHeight};
				letter-spacing: {$accessibilityStore.letterSpacing}em;
				max-width: {$accessibilityStore.maxLineWidth}ch;
			"
			class="text-surface-900"
		>
			The quick brown fox jumps over the lazy dog. This sample text demonstrates how your font settings will appear throughout the application.
		</p>
	</div>
</div>
