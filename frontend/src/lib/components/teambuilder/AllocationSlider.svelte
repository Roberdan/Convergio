<script lang="ts">
	import { createEventDispatcher } from 'svelte';

	export let value = 100;
	export let maxAvailable = 100;
	export let min = 10;
	export let step = 10;

	const dispatch = createEventDispatcher<{ change: number }>();

	$: effectiveMax = Math.min(maxAvailable, 100);
	$: displayValue = Math.min(value, effectiveMax);

	function handleChange(event: Event) {
		const target = event.target as HTMLInputElement;
		const newValue = parseInt(target.value, 10);
		dispatch('change', newValue);
	}
</script>

<div class="allocation-slider">
	<div class="flex items-center justify-between mb-1">
		<span class="text-xs text-surface-600">Allocation</span>
		<span class="text-xs font-medium {displayValue >= effectiveMax ? 'text-warning-600' : 'text-surface-900'}">
			{displayValue}%
			{#if effectiveMax < 100}
				<span class="text-surface-400">(max {effectiveMax}%)</span>
			{/if}
		</span>
	</div>

	<div class="relative">
		<input
			type="range"
			value={displayValue}
			min={min}
			max={effectiveMax}
			{step}
			on:input={handleChange}
			class="w-full h-2 bg-surface-200 rounded-lg appearance-none cursor-pointer slider"
		/>
	</div>

	<div class="flex justify-between mt-1 text-xs text-surface-400">
		<span>{min}%</span>
		<span>{effectiveMax}%</span>
	</div>
</div>

<style>
	.slider::-webkit-slider-thumb {
		-webkit-appearance: none;
		appearance: none;
		width: 16px;
		height: 16px;
		border-radius: 50%;
		background: #3b82f6;
		cursor: pointer;
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
	}

	.slider::-moz-range-thumb {
		width: 16px;
		height: 16px;
		border-radius: 50%;
		background: #3b82f6;
		cursor: pointer;
		border: none;
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
	}

	.slider:focus {
		outline: none;
	}

	.slider:focus::-webkit-slider-thumb {
		box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.3);
	}

	.slider:focus::-moz-range-thumb {
		box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.3);
	}
</style>
