<script lang="ts">
  let {
    variant = 'primary',
    size = 'md',
    disabled = false,
    loading = false,
    ariaLabel = '',
    ariaDescribedBy = '',
    type = 'button',
    tabIndex = 0,
    class: className = ''
  }: {
    variant?: 'primary' | 'secondary' | 'danger';
    size?: 'sm' | 'md' | 'lg';
    disabled?: boolean;
    loading?: boolean;
    ariaLabel?: string;
    ariaDescribedBy?: string;
    type?: 'button' | 'submit' | 'reset';
    tabIndex?: number;
    class?: string;
  } = $props();

  // For external reference only; not used in template
  export const accessKey = '';

  let buttonClass = $derived(
    `
      accessible-button
      accessible-button--${variant}
      accessible-button--${size}
      ${disabled || loading ? 'accessible-button--disabled' : ''}
      ${className}
    `.trim()
  );

  function handleKeydown(event: KeyboardEvent) {
    // Handle Enter and Space for accessibility
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      if (!disabled && !loading && event.currentTarget) {
        (event.currentTarget as HTMLElement).dispatchEvent(new Event('click', { bubbles: true }));
      }
    }
  }
</script>

<button
  class={buttonClass}
  {type}
  {disabled}
  aria-label={ariaLabel || undefined}
  aria-describedby={ariaDescribedBy || undefined}
  aria-busy={loading}
  aria-disabled={disabled || loading}
  tabindex={tabIndex}
  onkeydown={handleKeydown}
>
  {#if loading}
    <span class="loading-spinner" aria-hidden="true"></span>
    <span class="sr-only">Loading...</span>
  {/if}
  
  <slot />
</button>

<style>
  .accessible-button {
    position: relative;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    border: 2px solid transparent;
    border-radius: 0.375rem;
    font-weight: 500;
    text-align: center;
    transition: all 0.2s ease-in-out;
    cursor: pointer;
    outline: none;
  }

  /* Size variants */
  .accessible-button--sm {
    padding: 0.375rem 0.75rem;
    font-size: 0.875rem;
    min-height: 2rem;
  }

  .accessible-button--md {
    padding: 0.5rem 1rem;
    font-size: 1rem;
    min-height: 2.5rem;
  }

  .accessible-button--lg {
    padding: 0.75rem 1.5rem;
    font-size: 1.125rem;
    min-height: 3rem;
  }

  /* Color variants */
  .accessible-button--primary {
    background-color: #3b82f6;
    color: white;
    border-color: #3b82f6;
  }

  .accessible-button--primary:hover:not(.accessible-button--disabled) {
    background-color: #2563eb;
    border-color: #2563eb;
    transform: translateY(-1px);
  }

  .accessible-button--secondary {
    background-color: transparent;
    color: #374151;
    border-color: #d1d5db;
  }

  .accessible-button--secondary:hover:not(.accessible-button--disabled) {
    background-color: #f9fafb;
    border-color: #9ca3af;
  }

  .accessible-button--danger {
    background-color: #ef4444;
    color: white;
    border-color: #ef4444;
  }

  .accessible-button--danger:hover:not(.accessible-button--disabled) {
    background-color: #dc2626;
    border-color: #dc2626;
  }

  /* Focus styles - WCAG 2.1 compliant */
  .accessible-button:focus-visible {
    outline: 3px solid #fbbf24;
    outline-offset: 2px;
    box-shadow: 0 0 0 3px rgba(251, 191, 36, 0.3);
  }

  /* High contrast mode support */
  @media (prefers-contrast: high) {
    .accessible-button {
      border-width: 3px;
    }
    
    .accessible-button:focus-visible {
      outline-width: 4px;
    }
  }

  /* Disabled state */
  .accessible-button--disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none !important;
  }

  /* Loading spinner */
  .loading-spinner {
    width: 1rem;
    height: 1rem;
    border: 2px solid transparent;
    border-top: 2px solid currentColor;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  /* Screen reader only content */
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

  /* Motion preference respect */
  @media (prefers-reduced-motion: reduce) {
    .accessible-button {
      transition: none;
    }
    
    .loading-spinner {
      animation: none;
    }
    
    .accessible-button:hover:not(.accessible-button--disabled) {
      transform: none;
    }
  }
</style>
