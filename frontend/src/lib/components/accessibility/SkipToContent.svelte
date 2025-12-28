<script lang="ts">
	/**
	 * Skip to Content Link (WS5-C2)
	 * Provides keyboard-accessible skip links for screen reader users
	 */
	export let links: { href: string; label: string }[] = [
		{ href: '#main-content', label: 'Skip to main content' },
		{ href: '#navigation', label: 'Skip to navigation' }
	];
</script>

<div class="skip-links">
	{#each links as link}
		<a
			href={link.href}
			class="skip-link sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-[10000] focus:px-4 focus:py-2 focus:bg-primary-600 focus:text-white focus:rounded-lg focus:shadow-lg focus:outline-none focus:ring-2 focus:ring-primary-400 focus:ring-offset-2"
		>
			{link.label}
		</a>
	{/each}
</div>

<style>
	.sr-only {
		position: absolute;
		width: 1px;
		height: 1px;
		padding: 0;
		margin: -1px;
		overflow: hidden;
		clip: rect(0, 0, 0, 0);
		white-space: nowrap;
		border: 0;
	}

	.skip-link:focus {
		position: absolute;
		width: auto;
		height: auto;
		padding: 0.5rem 1rem;
		margin: 0;
		overflow: visible;
		clip: auto;
		white-space: normal;
	}
</style>
