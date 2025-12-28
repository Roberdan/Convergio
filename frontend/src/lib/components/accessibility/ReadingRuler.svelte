<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { accessibilityStore } from '$lib/stores/accessibilityStore';
	import { browser } from '$app/environment';

	let rulerElement: HTMLDivElement;
	let mouseY = 0;
	let isVisible = false;

	function handleMouseMove(e: MouseEvent) {
		if (!$accessibilityStore.readingRulerEnabled) return;
		mouseY = e.clientY;
		isVisible = true;
	}

	function handleMouseLeave() {
		isVisible = false;
	}

	function handleRulerHeightChange(e: Event) {
		const target = e.target as HTMLInputElement;
		accessibilityStore.updateSetting('readingRulerHeight', parseInt(target.value));
	}

	onMount(() => {
		if (browser) {
			document.addEventListener('mousemove', handleMouseMove);
			document.addEventListener('mouseleave', handleMouseLeave);
		}
	});

	onDestroy(() => {
		if (browser) {
			document.removeEventListener('mousemove', handleMouseMove);
			document.removeEventListener('mouseleave', handleMouseLeave);
		}
	});
</script>

<div class="space-y-6">
	<p class="text-sm text-surface-600">
		The reading ruler helps track your reading position, reducing line-skipping issues.
	</p>

	<!-- Toggle -->
	<div class="p-4 bg-white rounded-lg border border-surface-200">
		<div class="flex items-start justify-between">
			<div class="flex-1">
				<h4 class="text-sm font-medium text-surface-900">Enable Reading Ruler</h4>
				<p class="text-sm text-surface-600 mt-1">
					A horizontal line follows your cursor to help track reading position.
				</p>
			</div>
			<label class="relative inline-flex items-center cursor-pointer ml-4">
				<input
					type="checkbox"
					checked={$accessibilityStore.readingRulerEnabled}
					on:change={() => accessibilityStore.updateSetting('readingRulerEnabled', !$accessibilityStore.readingRulerEnabled)}
					class="sr-only peer"
				/>
				<div class="w-11 h-6 bg-surface-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-100 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-surface-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
			</label>
		</div>
	</div>

	<!-- Ruler Height -->
	{#if $accessibilityStore.readingRulerEnabled}
		<div class="p-4 bg-white rounded-lg border border-surface-200">
			<div class="flex items-center justify-between mb-2">
				<label for="ruler-height" class="text-sm font-medium text-surface-900">Ruler Height</label>
				<span class="text-sm text-surface-600">{$accessibilityStore.readingRulerHeight}px</span>
			</div>
			<input
				id="ruler-height"
				type="range"
				min="20"
				max="80"
				step="5"
				value={$accessibilityStore.readingRulerHeight}
				on:input={handleRulerHeightChange}
				class="w-full h-2 bg-surface-200 rounded-lg appearance-none cursor-pointer"
			/>
		</div>
	{/if}

	<!-- Text-to-Speech -->
	<div class="p-4 bg-white rounded-lg border border-surface-200">
		<div class="flex items-start justify-between">
			<div class="flex-1">
				<h4 class="text-sm font-medium text-surface-900">Text-to-Speech (DY05)</h4>
				<p class="text-sm text-surface-600 mt-1">
					Enable read-aloud functionality for selected text.
				</p>
			</div>
			<label class="relative inline-flex items-center cursor-pointer ml-4">
				<input
					type="checkbox"
					checked={$accessibilityStore.textToSpeechEnabled}
					on:change={() => accessibilityStore.updateSetting('textToSpeechEnabled', !$accessibilityStore.textToSpeechEnabled)}
					class="sr-only peer"
				/>
				<div class="w-11 h-6 bg-surface-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-100 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-surface-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
			</label>
		</div>

		{#if $accessibilityStore.textToSpeechEnabled}
			<div class="mt-3 p-3 bg-blue-50 rounded-lg">
				<p class="text-sm text-blue-700">
					Select any text and press <kbd class="px-1.5 py-0.5 bg-blue-100 rounded text-xs font-mono">Ctrl+Shift+S</kbd> to hear it spoken aloud.
				</p>
			</div>
		{/if}
	</div>

	<!-- Syllable Highlighting -->
	<div class="p-4 bg-white rounded-lg border border-surface-200">
		<div class="flex items-start justify-between">
			<div class="flex-1">
				<h4 class="text-sm font-medium text-surface-900">Syllable Highlighting (DY06)</h4>
				<p class="text-sm text-surface-600 mt-1">
					Highlight syllables during text-to-speech playback.
				</p>
			</div>
			<label class="relative inline-flex items-center cursor-pointer ml-4">
				<input
					type="checkbox"
					checked={$accessibilityStore.syllableHighlighting}
					on:change={() => accessibilityStore.updateSetting('syllableHighlighting', !$accessibilityStore.syllableHighlighting)}
					disabled={!$accessibilityStore.textToSpeechEnabled}
					class="sr-only peer"
				/>
				<div class="w-11 h-6 bg-surface-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-100 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-surface-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600 peer-disabled:opacity-50 peer-disabled:cursor-not-allowed"></div>
			</label>
		</div>
	</div>

	<!-- Preview Area -->
	<div class="p-4 bg-surface-50 rounded-lg border border-surface-200">
		<h4 class="text-sm font-medium text-surface-900 mb-3">Preview Area</h4>
		<p class="text-surface-700">
			Move your cursor over this text to see the reading ruler in action.
			The ruler helps you track your reading position line by line,
			making it easier to avoid skipping lines or losing your place.
		</p>
	</div>
</div>

<!-- Global Reading Ruler (rendered at document level) -->
{#if $accessibilityStore.readingRulerEnabled && isVisible}
	<div
		bind:this={rulerElement}
		class="fixed left-0 right-0 pointer-events-none z-[9999]"
		style="
			top: {mouseY - $accessibilityStore.readingRulerHeight / 2}px;
			height: {$accessibilityStore.readingRulerHeight}px;
			background: linear-gradient(
				to bottom,
				transparent 0%,
				rgba(255, 255, 0, 0.1) 20%,
				rgba(255, 255, 0, 0.2) 50%,
				rgba(255, 255, 0, 0.1) 80%,
				transparent 100%
			);
			border-top: 1px solid rgba(255, 200, 0, 0.3);
			border-bottom: 1px solid rgba(255, 200, 0, 0.3);
		"
	></div>
{/if}
