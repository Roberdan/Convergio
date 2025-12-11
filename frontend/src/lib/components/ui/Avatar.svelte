<script lang="ts">
	import type { HTMLAttributes } from 'svelte/elements';

	interface $$Props extends HTMLAttributes<HTMLDivElement> {
		src?: string;
		alt?: string;
		size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl';
		status?: 'online' | 'offline' | 'away' | 'busy' | null;
		fallback?: string;
		squared?: boolean;
		bordered?: boolean;
	}

	export let src: $$Props['src'] = '';
	export let alt: $$Props['alt'] = '';
	export let size: NonNullable<$$Props['size']> = 'md';
	export let status: $$Props['status'] = null;
	export let fallback: $$Props['fallback'] = '';
	export let squared: $$Props['squared'] = false;
	export let bordered: $$Props['bordered'] = false;

	let imageLoaded = false;
	let imageError = false;

	// Compute CSS classes
	$: sizeClasses = {
		xs: 'avatar-xs',
		sm: 'avatar-sm', 
		md: 'avatar-md',
		lg: 'avatar-lg',
		xl: 'avatar-xl',
		'2xl': 'avatar-2xl'
	};

	$: statusClasses = {
		online: 'avatar-status',
		offline: 'avatar-status offline',
		away: 'avatar-status away',
		busy: 'avatar-status busy'
	};

	$: classes = [
		'avatar',
		sizeClasses[size],
		status ? statusClasses[status] : '',
		squared ? 'rounded-lg' : '', // Override rounded-full from base avatar
		bordered ? 'ring-4 ring-white' : '',
		'relative overflow-hidden bg-gray-100'
	].filter(Boolean).join(' ');

	// Generate initials from fallback text
	$: initials = fallback
		? fallback
				.split(' ')
				.map(word => word.charAt(0))
				.join('')
				.toUpperCase()
				.slice(0, 2)
		: '';

	function handleImageLoad() {
		imageLoaded = true;
		imageError = false;
	}

	function handleImageError() {
		imageError = true;
		imageLoaded = false;
	}
</script>

<div class={classes} {...$$restProps}>
	{#if src && !imageError}
		<img
			{src}
			{alt}
			class="w-full h-full object-cover"
			on:load={handleImageLoad}
			on:error={handleImageError}
		/>
	{:else if initials}
		<div class="avatar-fallback w-full h-full flex items-center justify-center">
			<span class="avatar-initials text-gray-600 font-medium select-none">
				{initials}
			</span>
		</div>
	{:else}
		<!-- Default user icon -->
		<div class="avatar-fallback w-full h-full flex items-center justify-center">
			<span class="icon-user w-1/2 h-1/2 text-gray-400" aria-hidden="true"></span>
		</div>
	{/if}
</div>

<style>
	.avatar-fallback {
		background: linear-gradient(135deg, #f3f4f6, #e5e7eb);
	}

	.dark .avatar-fallback {
		background: linear-gradient(135deg, #374151, #4b5563);
	}

	.avatar-initials {
		font-family: var(--font-primary);
		font-size: 0.6em; /* Relative to avatar size */
	}

	/* Size-specific text sizes */
	.avatar-xs .avatar-initials {
		font-size: 0.5rem;
	}

	.avatar-sm .avatar-initials {
		font-size: 0.625rem;
	}

	.avatar-md .avatar-initials {
		font-size: 0.75rem;
	}

	.avatar-lg .avatar-initials {
		font-size: 0.875rem;
	}

	.avatar-xl .avatar-initials {
		font-size: 1rem;
	}

	.avatar-2xl .avatar-initials {
		font-size: 1.25rem;
	}

	/* Icon styles */
	.icon-user {
		display: inline-block;
		background-color: currentColor;
		mask-size: contain;
		mask-repeat: no-repeat;
		mask-position: center;
		mask-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='1.5' stroke='currentColor'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.501 20.118a7.5 7.5 0 0 1 14.998 0A17.933 17.933 0 0 1 12 21.75c-2.676 0-5.216-.584-7.499-1.632Z' /%3e%3c/svg%3e");
	}
</style>