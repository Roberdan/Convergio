<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { accessibilityStore, type AccessibilityProfile } from '$lib/stores/accessibilityStore';
	import FontSettings from './FontSettings.svelte';
	import ColorTheme from './ColorTheme.svelte';
	import MotionSettings from './MotionSettings.svelte';
	import FocusMode from './FocusMode.svelte';

	const dispatch = createEventDispatcher<{ save: void }>();

	let activeSection: 'profile' | 'font' | 'color' | 'motion' | 'focus' = 'profile';

	const profiles: { id: AccessibilityProfile; name: string; description: string }[] = [
		{
			id: 'default',
			name: 'Default',
			description: 'Standard settings for most users'
		},
		{
			id: 'dyslexia',
			name: 'Dyslexia Support',
			description: 'OpenDyslexic font, increased spacing, cream background'
		},
		{
			id: 'adhd',
			name: 'ADHD Support',
			description: 'Focus mode, reduced distractions, progress indicators'
		},
		{
			id: 'autism',
			name: 'Autism Support',
			description: 'Reduced animations, predictable layouts, clear language'
		},
		{
			id: 'motor',
			name: 'Motor Impairment',
			description: 'Large touch targets, keyboard navigation, extended timeouts'
		},
		{
			id: 'low-vision',
			name: 'Low Vision',
			description: 'High contrast, large text, enhanced focus indicators'
		}
	];

	function selectProfile(profileId: AccessibilityProfile) {
		accessibilityStore.setProfile(profileId);
	}

	function handleSave() {
		dispatch('save');
	}
</script>

<div class="accessibility-settings bg-white rounded-xl shadow-sm border border-surface-200 overflow-hidden">
	<!-- Header -->
	<div class="p-6 border-b border-surface-200 bg-surface-50">
		<h2 class="text-lg font-semibold text-surface-900">Accessibility Settings</h2>
		<p class="text-sm text-surface-600 mt-1">
			Customize your experience for better readability and usability
		</p>
	</div>

	<!-- Navigation Tabs -->
	<div class="border-b border-surface-200">
		<nav class="flex space-x-1 px-4" aria-label="Accessibility settings sections">
			<button
				on:click={() => activeSection = 'profile'}
				class="px-4 py-3 text-sm font-medium border-b-2 transition-colors {activeSection === 'profile'
					? 'border-primary-600 text-primary-600'
					: 'border-transparent text-surface-600 hover:text-surface-900'}"
			>
				Profiles
			</button>
			<button
				on:click={() => activeSection = 'font'}
				class="px-4 py-3 text-sm font-medium border-b-2 transition-colors {activeSection === 'font'
					? 'border-primary-600 text-primary-600'
					: 'border-transparent text-surface-600 hover:text-surface-900'}"
			>
				Font & Text
			</button>
			<button
				on:click={() => activeSection = 'color'}
				class="px-4 py-3 text-sm font-medium border-b-2 transition-colors {activeSection === 'color'
					? 'border-primary-600 text-primary-600'
					: 'border-transparent text-surface-600 hover:text-surface-900'}"
			>
				Colors
			</button>
			<button
				on:click={() => activeSection = 'motion'}
				class="px-4 py-3 text-sm font-medium border-b-2 transition-colors {activeSection === 'motion'
					? 'border-primary-600 text-primary-600'
					: 'border-transparent text-surface-600 hover:text-surface-900'}"
			>
				Motion
			</button>
			<button
				on:click={() => activeSection = 'focus'}
				class="px-4 py-3 text-sm font-medium border-b-2 transition-colors {activeSection === 'focus'
					? 'border-primary-600 text-primary-600'
					: 'border-transparent text-surface-600 hover:text-surface-900'}"
			>
				Focus Mode
			</button>
		</nav>
	</div>

	<!-- Content -->
	<div class="p-6">
		{#if activeSection === 'profile'}
			<div class="space-y-4">
				<p class="text-sm text-surface-600">
					Select a profile to quickly apply recommended settings for your needs.
				</p>
				<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
					{#each profiles as profile}
						<button
							on:click={() => selectProfile(profile.id)}
							class="p-4 text-left rounded-lg border-2 transition-all {$accessibilityStore.profile === profile.id
								? 'border-primary-500 bg-primary-50'
								: 'border-surface-200 hover:border-surface-300'}"
						>
							<div class="font-medium text-surface-900">{profile.name}</div>
							<div class="text-sm text-surface-600 mt-1">{profile.description}</div>
							{#if $accessibilityStore.profile === profile.id}
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
			</div>
		{:else if activeSection === 'font'}
			<FontSettings />
		{:else if activeSection === 'color'}
			<ColorTheme />
		{:else if activeSection === 'motion'}
			<MotionSettings />
		{:else if activeSection === 'focus'}
			<FocusMode />
		{/if}
	</div>

	<!-- Footer -->
	<div class="p-4 border-t border-surface-200 bg-surface-50 flex justify-between items-center">
		<button
			on:click={() => accessibilityStore.reset()}
			class="text-sm text-surface-600 hover:text-surface-900"
		>
			Reset to defaults
		</button>
		<button
			on:click={handleSave}
			class="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white text-sm font-medium rounded-lg transition-colors"
		>
			Save Settings
		</button>
	</div>
</div>
