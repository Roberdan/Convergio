<script lang="ts">
  interface Props {
    title: string;
    description?: string;
    ariaLabelledBy?: string;
    ariaDescribedBy?: string;
    children?: import('svelte').Snippet;
  }

  let {
    title,
    description = '',
    ariaLabelledBy = '',
    ariaDescribedBy = '',
    children
  }: Props = $props();

  let formElement: HTMLFormElement = $state()!;
  
  function handleSubmit() {
    // Announce form submission to screen readers
    const liveRegion = document.getElementById('form-status');
    if (liveRegion) {
      liveRegion.textContent = 'Form submitted, processing...';
    }
  }
</script>

<div class="accessible-form-container">
  <!-- Form title and description -->
  <header class="form-header">
    <h2 id="form-title" class="form-title">
      {title}
    </h2>
    {#if description}
      <p id="form-description" class="form-description">
        {description}
      </p>
    {/if}
  </header>

  <!-- Form element with proper accessibility attributes -->
  <form 
    bind:this={formElement}
    class="accessible-form"
    aria-labelledby={ariaLabelledBy || "form-title"}
    aria-describedby={ariaDescribedBy || (description ? "form-description" : undefined)}
  onsubmit={handleSubmit}
  >
    {@render children?.()}
  </form>

  <!-- Live region for dynamic announcements -->
  <div 
    id="form-status" 
    class="sr-only" 
    aria-live="polite" 
    aria-atomic="true"
  ></div>
</div>

<style>
  .accessible-form-container {
    width: 100%;
    max-width: 32rem;
  }

  .form-header {
    margin-bottom: 1.5rem;
  }

  .form-title {
    font-size: 1.5rem;
    font-weight: 600;
    color: #111827;
    margin: 0 0 0.5rem 0;
    line-height: 1.4;
  }

  .form-description {
    font-size: 0.875rem;
    color: #6b7280;
    margin: 0;
    line-height: 1.5;
  }

  .accessible-form {
    display: flex;
    flex-direction: column;
    gap: 1rem;
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

  /* High contrast support */
  @media (prefers-contrast: high) {
    .form-title {
      color: #000000;
    }
    
    .form-description {
      color: #333333;
    }
  }
</style>