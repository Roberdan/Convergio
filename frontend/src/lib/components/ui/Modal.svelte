<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { Button } from './index';

	interface $$Props {
		open: boolean;
		title?: string;
		description?: string;
		size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
		closable?: boolean;
		closeOnBackdrop?: boolean;
		closeOnEscape?: boolean;
		showHeader?: boolean;
		showFooter?: boolean;
		persistent?: boolean;
		loading?: boolean;
	}

	export let open: $$Props['open'] = false;
	export let title: $$Props['title'] = '';
	export let description: $$Props['description'] = '';
	export let size: NonNullable<$$Props['size']> = 'md';
	export let closable: $$Props['closable'] = true;
	export let closeOnBackdrop: $$Props['closeOnBackdrop'] = true;
	export let closeOnEscape: $$Props['closeOnEscape'] = true;
	export let showHeader: $$Props['showHeader'] = true;
	export let showFooter: $$Props['showFooter'] = false;
	export let persistent: $$Props['persistent'] = false;
	export let loading: $$Props['loading'] = false;

	const dispatch = createEventDispatcher<{
		close: void;
		cancel: void;
		confirm: void;
		backdropClick: void;
	}>();

	let modalRef: HTMLElement;
	let previousFocus: HTMLElement | null = null;

	// Size classes
	$: sizeClasses = {
		sm: 'max-w-sm',
		md: 'max-w-md',
		lg: 'max-w-lg',
		xl: 'max-w-xl',
		full: 'max-w-full mx-4'
	}[size];

	// Handle open/close
	$: if (open) {
		// Store previous focus
		previousFocus = document.activeElement as HTMLElement;
		
		// Prevent body scroll
		document.body.style.overflow = 'hidden';
		
		// Focus modal when opened
		setTimeout(() => {
			if (modalRef) {
				modalRef.focus();
			}
		}, 100);
	} else {
		// Restore body scroll
		document.body.style.overflow = '';
		
		// Restore previous focus
		if (previousFocus) {
			previousFocus.focus();
		}
	}

	function handleClose() {
		if (!persistent) {
			dispatch('close');
		}
	}

	function handleCancel() {
		dispatch('cancel');
		if (!persistent) {
			dispatch('close');
		}
	}

	function handleConfirm() {
		dispatch('confirm');
	}

	function handleBackdropClick(event: MouseEvent) {
		if (event.target === event.currentTarget) {
			dispatch('backdropClick');
			if (closeOnBackdrop && !persistent) {
				handleClose();
			}
		}
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape' && closeOnEscape && !persistent) {
			handleClose();
		}
		
		// Trap focus within modal
		if (event.key === 'Tab') {
			trapFocus(event);
		}
	}

	function trapFocus(event: KeyboardEvent) {
		if (!modalRef) return;
		
		const focusableElements = modalRef.querySelectorAll(
			'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
		);
		
		const firstElement = focusableElements[0] as HTMLElement;
		const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;
		
		if (event.shiftKey) {
			if (document.activeElement === firstElement) {
				lastElement.focus();
				event.preventDefault();
			}
		} else {
			if (document.activeElement === lastElement) {
				firstElement.focus();
				event.preventDefault();
			}
		}
	}
</script>

<svelte:window on:keydown={handleKeydown} />

{#if open}
	<!-- Backdrop -->
	<div 
		class="modal-backdrop"
		on:click={handleBackdropClick}
		aria-hidden="true"
	>
		<!-- Modal Container -->
		<div
			bind:this={modalRef}
			class="modal-container {sizeClasses}"
			role="dialog"
			aria-modal="true"
			aria-labelledby={title ? 'modal-title' : undefined}
			aria-describedby={description ? 'modal-description' : undefined}
			tabindex="-1"
		>
			{#if loading}
				<!-- Loading Overlay -->
				<div class="modal-loading">
					<div class="loading-spinner"></div>
				</div>
			{/if}

			<!-- Header -->
			{#if showHeader && (title || $$slots.header)}
				<div class="modal-header">
					{#if $$slots.header}
						<slot name="header" />
					{:else}
						<div class="header-content">
							<h2 id="modal-title" class="modal-title">{title}</h2>
							{#if description}
								<p id="modal-description" class="modal-description">{description}</p>
							{/if}
						</div>
					{/if}

					{#if closable}
						<button
							type="button"
							class="close-button"
							on:click={handleClose}
							aria-label="Close modal"
						>
							<span class="icon-x" aria-hidden="true"></span>
						</button>
					{/if}
				</div>
			{/if}

			<!-- Content -->
			<div class="modal-content">
				<slot />
			</div>

			<!-- Footer -->
			{#if showFooter || $$slots.footer}
				<div class="modal-footer">
					{#if $$slots.footer}
						<slot name="footer" />
					{:else}
						<div class="footer-actions">
							<Button variant="outline" on:click={handleCancel}>
								Cancel
							</Button>
							<Button variant="primary" on:click={handleConfirm}>
								Confirm
							</Button>
						</div>
					{/if}
				</div>
			{/if}
		</div>
	</div>
{/if}

<style>
	.modal-backdrop {
		@apply fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50;
		backdrop-filter: blur(4px);
		animation: backdropFadeIn 0.2s ease-out;
	}

	.modal-container {
		@apply relative w-full bg-white rounded-xl shadow-xl max-h-[90vh] flex flex-col;
		box-shadow: var(--shadow-xl);
		animation: modalSlideIn 0.3s ease-out;
	}

	.modal-loading {
		@apply absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center z-10 rounded-xl;
		backdrop-filter: blur(2px);
	}

	.modal-header {
		@apply flex items-start justify-between p-6 border-b border-gray-200;
	}

	.header-content {
		@apply flex-1 pr-4;
	}

	.modal-title {
		@apply text-lg font-semibold text-gray-900;
		font-family: var(--font-primary);
	}

	.modal-description {
		@apply mt-1 text-sm text-gray-600;
		font-family: var(--font-primary);
	}

	.close-button {
		@apply flex-shrink-0 w-8 h-8 flex items-center justify-center text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2;
	}

	.dark .close-button:focus {
		@apply ring-offset-gray-800;
	}

	.modal-content {
		@apply flex-1 p-6 overflow-y-auto;
	}

	.modal-footer {
		@apply px-6 py-4 border-t border-gray-200 bg-gray-50 rounded-b-xl;
	}

	.footer-actions {
		@apply flex items-center justify-end gap-3;
	}

	/* Icon styles */
	[class^="icon-"] {
		display: inline-block;
		width: 1rem;
		height: 1rem;
		background-color: currentColor;
		mask-size: contain;
		mask-repeat: no-repeat;
		mask-position: center;
	}

	.icon-x {
		mask-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='1.5' stroke='currentColor'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='M6 18 18 6M6 6l12 12' /%3e%3c/svg%3e");
	}

	/* Animations */
	@keyframes backdropFadeIn {
		from {
			opacity: 0;
		}
		to {
			opacity: 1;
		}
	}

	@keyframes modalSlideIn {
		from {
			opacity: 0;
			transform: translateY(-20px) scale(0.95);
		}
		to {
			opacity: 1;
			transform: translateY(0) scale(1);
		}
	}

	/* Responsive adjustments */
	@media (max-width: 640px) {
		.modal-container {
			@apply max-h-[95vh] mx-2;
		}

		.modal-header,
		.modal-content {
			@apply px-4;
		}

		.modal-footer {
			@apply px-4;
		}

		.footer-actions {
			@apply flex-col-reverse gap-2;
		}

		.footer-actions :global(button) {
			@apply w-full;
		}
	}

	/* Size variants */
	@media (min-width: 640px) {
		.max-w-full {
			@apply max-w-6xl;
		}
	}

	/* Reduce motion for accessibility */
	@media (prefers-reduced-motion: reduce) {
		.modal-backdrop,
		.modal-container {
			animation: none;
		}
	}
</style>