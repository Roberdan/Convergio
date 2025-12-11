<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { Button } from './index';

	interface QuickAction {
		id: string;
		label: string;
		icon: string;
		variant?: 'primary' | 'secondary' | 'success' | 'warning' | 'error';
		disabled?: boolean;
		badge?: {
			text: string;
			variant?: 'primary' | 'success' | 'warning' | 'error' | 'info' | 'gray';
		};
		href?: string;
		keyboard?: string; // Keyboard shortcut
	}

	interface $$Props {
		actions: QuickAction[];
		position?: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left' | 'center';
		layout?: 'vertical' | 'horizontal' | 'grid';
		size?: 'sm' | 'md' | 'lg';
		expandDirection?: 'up' | 'down' | 'left' | 'right';
		trigger?: 'hover' | 'click' | 'always';
		mainAction?: QuickAction;
		maxVisible?: number;
	}

	export let actions: $$Props['actions'];
	export let position: NonNullable<$$Props['position']> = 'bottom-right';
	export let layout: NonNullable<$$Props['layout']> = 'vertical';
	export let size: NonNullable<$$Props['size']> = 'md';
	export let expandDirection: NonNullable<$$Props['expandDirection']> = 'up';
	export let trigger: NonNullable<$$Props['trigger']> = 'hover';
	export let mainAction: $$Props['mainAction'] = undefined;
	export let maxVisible: $$Props['maxVisible'] = undefined;

	const dispatch = createEventDispatcher<{
		action: { action: QuickAction };
		mainAction: { action: QuickAction };
	}>();

	let isExpanded = trigger === 'always';
	let containerRef: HTMLElement;

	// Compute visible actions
	$: visibleActions = maxVisible ? actions.slice(0, maxVisible) : actions;
	$: hasMoreActions = maxVisible && actions.length > maxVisible;

	// Position classes
	$: positionClasses = {
		'bottom-right': 'fixed bottom-6 right-6',
		'bottom-left': 'fixed bottom-6 left-6',
		'top-right': 'fixed top-6 right-6', 
		'top-left': 'fixed top-6 left-6',
		'center': 'fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2'
	}[position];

	// Layout classes
	$: layoutClasses = {
		vertical: 'flex-col',
		horizontal: 'flex-row',
		grid: 'grid grid-cols-2 gap-2'
	}[layout];

	// Size classes
	$: sizeClasses = {
		sm: 'w-10 h-10',
		md: 'w-12 h-12', 
		lg: 'w-14 h-14'
	}[size];

	// Expand direction classes
	$: expandClasses = {
		up: 'flex-col-reverse',
		down: 'flex-col',
		left: 'flex-row-reverse',
		right: 'flex-row'
	}[expandDirection];

	function handleMainAction() {
		if (mainAction) {
			dispatch('mainAction', { action: mainAction });
		} else if (trigger === 'click') {
			isExpanded = !isExpanded;
		}
	}

	function handleAction(action: QuickAction) {
		if (action.disabled) return;
		
		if (action.href) {
			window.location.href = action.href;
		}
		
		dispatch('action', { action });
		
		// Auto-collapse after action (except for always trigger)
		if (trigger === 'click') {
			isExpanded = false;
		}
	}

	function handleMouseEnter() {
		if (trigger === 'hover') {
			isExpanded = true;
		}
	}

	function handleMouseLeave() {
		if (trigger === 'hover') {
			isExpanded = false;
		}
	}

	// Keyboard shortcuts
	function handleKeydown(event: KeyboardEvent) {
		actions.forEach(action => {
			if (action.keyboard && event.key === action.keyboard && (event.ctrlKey || event.metaKey)) {
				event.preventDefault();
				handleAction(action);
			}
		});
	}
</script>

<svelte:window on:keydown={handleKeydown} />

<div 
	bind:this={containerRef}
	class="quick-actions {positionClasses}"
	on:mouseenter={handleMouseEnter}
	on:mouseleave={handleMouseLeave}
>
	<div class="actions-container flex gap-3 {layout === 'grid' ? '' : expandClasses} {layoutClasses}">
		<!-- Main Action Button (FAB) -->
		{#if mainAction || trigger === 'click'}
			<button
				type="button"
				class="main-action-btn {sizeClasses}"
				class:expanded={isExpanded}
				on:click={handleMainAction}
				aria-label={mainAction?.label || 'Toggle quick actions'}
				aria-expanded={isExpanded}
				title={mainAction?.label || 'Quick actions'}
			>
				{#if mainAction?.icon}
					<span class="icon-{mainAction.icon}" aria-hidden="true"></span>
				{:else}
					<span class="icon-{isExpanded ? 'x' : 'plus'}" aria-hidden="true"></span>
				{/if}
				
				{#if mainAction?.badge}
					<span class="action-badge badge-{mainAction.badge.variant || 'primary'}">
						{mainAction.badge.text}
					</span>
				{/if}
			</button>
		{/if}

		<!-- Action Buttons -->
		{#if isExpanded}
			<div class="actions-list flex gap-2 {layout === 'grid' ? 'grid grid-cols-2' : expandClasses}">
				{#each visibleActions as action, index (action.id)}
					<button
						type="button"
						class="action-btn {sizeClasses} {action.disabled ? 'disabled' : ''} variant-{action.variant || 'secondary'}"
						on:click={() => handleAction(action)}
						disabled={action.disabled}
						aria-label={action.label}
						title="{action.label}{action.keyboard ? ` (${action.keyboard})` : ''}"
						style="animation-delay: {index * 0.05}s"
					>
						<span class="icon-{action.icon}" aria-hidden="true"></span>
						
						{#if action.badge}
							<span class="action-badge badge-{action.badge.variant || 'primary'}">
								{action.badge.text}
							</span>
						{/if}
					</button>
				{/each}

				<!-- More actions indicator -->
				{#if hasMoreActions}
					<button
						type="button"
						class="action-btn more-btn {sizeClasses}"
						aria-label="More actions"
						title="More actions"
					>
						<span class="icon-dots" aria-hidden="true"></span>
					</button>
				{/if}
			</div>
		{/if}
	</div>

	<!-- Tooltip/Labels for actions -->
	{#if trigger === 'hover' && isExpanded}
		<div class="actions-labels">
			{#each visibleActions as action (action.id)}
				<div class="action-label">
					{action.label}
					{#if action.keyboard}
						<kbd class="keyboard-shortcut">{action.keyboard}</kbd>
					{/if}
				</div>
			{/each}
		</div>
	{/if}
</div>

<style>
	.quick-actions {
		@apply z-50;
	}

	.actions-container {
		@apply relative;
	}

	.main-action-btn {
		@apply relative bg-primary-600 hover:bg-primary-700 text-white rounded-full shadow-lg hover:shadow-xl transition-all duration-300 flex items-center justify-center focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2;
		transform: scale(1);
	}

	.main-action-btn:hover {
		transform: scale(1.05);
	}

	.main-action-btn.expanded {
		@apply bg-primary-700;
		transform: rotate(45deg) scale(1.05);
	}

	.action-btn {
		@apply relative bg-white text-gray-700 border border-gray-200 rounded-full shadow-md hover:shadow-lg transition-all duration-200 flex items-center justify-center focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2;
		animation: quickActionFadeIn 0.3s ease-out forwards;
		opacity: 0;
		transform: translateY(10px);
	}

	.dark .action-btn:focus {
		@apply ring-offset-gray-900;
	}

	.action-btn:hover {
		@apply bg-gray-50 border-gray-300;
		transform: translateY(0) scale(1.05);
	}

	.action-btn.disabled {
		@apply opacity-50 cursor-not-allowed pointer-events-none;
	}

	/* Variant styles */
	.variant-primary {
		@apply bg-primary-600 hover:bg-primary-700 text-white border-primary-600;
	}

	.variant-success {
		@apply bg-success-600 hover:bg-success-700 text-white border-success-600;
	}

	.variant-warning {
		@apply bg-warning-600 hover:bg-warning-700 text-white border-warning-600;
	}

	.variant-error {
		@apply bg-error-600 hover:bg-error-700 text-white border-error-600;
	}

	.more-btn {
		@apply bg-gray-100 text-gray-500;
	}

	.action-badge {
		@apply absolute -top-1 -right-1 w-5 h-5 text-xs font-bold rounded-full flex items-center justify-center;
	}

	.badge-primary {
		@apply bg-primary-600 text-white;
	}

	.badge-success {
		@apply bg-success-600 text-white;
	}

	.badge-warning {
		@apply bg-warning-600 text-white;
	}

	.badge-error {
		@apply bg-error-600 text-white;
	}

	.badge-info {
		@apply bg-info-600 text-white;
	}

	.badge-gray {
		@apply bg-gray-600 text-white;
	}

	.actions-labels {
		@apply absolute pointer-events-none;
	}

	.action-label {
		@apply bg-gray-900 text-white text-xs px-2 py-1 rounded shadow-lg whitespace-nowrap flex items-center gap-2;
		font-family: var(--font-primary);
	}

	.keyboard-shortcut {
		@apply bg-gray-700 px-1 py-0.5 rounded text-2xs font-mono;
	}

	/* Icon styles */
	[class^="icon-"] {
		display: inline-block;
		background-color: currentColor;
		mask-size: contain;
		mask-repeat: no-repeat;
		mask-position: center;
	}

	.w-10 [class^="icon-"], .h-10 [class^="icon-"] {
		@apply w-5 h-5;
	}

	.w-12 [class^="icon-"], .h-12 [class^="icon-"] {
		@apply w-6 h-6;
	}

	.w-14 [class^="icon-"], .h-14 [class^="icon-"] {
		@apply w-7 h-7;
	}

	/* Common icons */
	.icon-plus {
		mask-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='1.5' stroke='currentColor'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='M12 4.5v15m7.5-7.5h-15' /%3e%3c/svg%3e");
	}

	.icon-x {
		mask-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='1.5' stroke='currentColor'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='M6 18 18 6M6 6l12 12' /%3e%3c/svg%3e");
	}

	.icon-chat {
		mask-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='1.5' stroke='currentColor'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='M8.625 12a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0H8.25m4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0H12m4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 0 1-2.555-.337A5.972 5.972 0 0 1 5.41 20.97a5.969 5.969 0 0 1-.474-.065 4.48 4.48 0 0 0 .978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25Z' /%3e%3c/svg%3e");
	}

	.icon-user-plus {
		mask-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='1.5' stroke='currentColor'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='M18 7.5v3m0 0v3m0-3h3m-3 0h-3m-2.25-4.125a3.375 3.375 0 1 1-6.75 0 3.375 3.375 0 0 1 6.75 0ZM3 19.235v-.11a6.375 6.375 0 0 1 12.75 0v.109A12.318 12.318 0 0 1 9.374 21c-2.331 0-4.512-.645-6.374-1.766Z' /%3e%3c/svg%3e");
	}

	.icon-document-plus {
		mask-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='1.5' stroke='currentColor'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m3.75 9v6m3-3H9m1.5-12H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z' /%3e%3c/svg%3e");
	}

	.icon-dots {
		mask-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='1.5' stroke='currentColor'%3e%3cpath stroke-linecap='round' stroke-linejoin='round' d='M6.75 12a.75.75 0 1 1-1.5 0 .75.75 0 0 1 1.5 0ZM12.75 12a.75.75 0 1 1-1.5 0 .75.75 0 0 1 1.5 0ZM18.75 12a.75.75 0 1 1-1.5 0 .75.75 0 0 1 1.5 0Z' /%3e%3c/svg%3e");
	}

	/* Animations */
	@keyframes quickActionFadeIn {
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}

	/* Responsive adjustments */
	@media (max-width: 640px) {
		.quick-actions {
			@apply bottom-4 right-4;
		}

		.w-12, .h-12 {
			@apply w-11 h-11;
		}

		.w-14, .h-14 {
			@apply w-12 h-12;
		}
	}
</style>