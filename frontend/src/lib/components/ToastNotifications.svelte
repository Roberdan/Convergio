<script lang="ts">
  import { onMount } from 'svelte';
  import { fly, scale } from 'svelte/transition';
  import { flip } from 'svelte/animate';
  import { 
    activeNotifications, 
    notificationConfig,
    removeNotification,
    type Notification,
    type NotificationPosition 
  } from '$lib/stores/notifications';
  
  let mounted = $state(false);
  
  const icons = {
    success: '✅',
    error: '❌',
    warning: '⚠️',
    info: 'ℹ️'
  };
  
  const colors = {
    success: '#10b981',
    error: '#ef4444',
    warning: '#f59e0b',
    info: '#3b82f6'
  };
  
  function getPositionClasses(position: NotificationPosition): string {
    const classes = {
      'top-right': 'top-4 right-4',
      'top-left': 'top-4 left-4',
      'bottom-right': 'bottom-4 right-4',
      'bottom-left': 'bottom-4 left-4',
      'top-center': 'top-4 left-1/2 -translate-x-1/2',
      'bottom-center': 'bottom-4 left-1/2 -translate-x-1/2'
    };
    return classes[position] || classes['top-right'];
  }
  
  function getTransitionParams(position: NotificationPosition) {
    const isTop = position.includes('top');
    const isRight = position.includes('right');
    const isLeft = position.includes('left');
    
    return {
      y: isTop ? -100 : 100,
      x: isRight ? 100 : isLeft ? -100 : 0,
      duration: 300
    };
  }
  
  function handleActionClick(notification: Notification, action: any) {
    action.action();
    if (!notification.persistent) {
      removeNotification(notification.id);
    }
  }
  
  onMount(() => {
    mounted = true;
  });
</script>

{#if mounted}
  <div 
    class="toast-container {getPositionClasses($notificationConfig.position)}"
    aria-live="polite"
    aria-atomic="true"
  >
    {#each $activeNotifications as notification (notification.id)}
      <div
        class="toast"
        style="--accent-color: {colors[notification.type]}"
        in:fly={getTransitionParams($notificationConfig.position)}
        out:scale={{ duration: 200, start: 0.9 }}
        animate:flip={{ duration: 300 }}
      >
        <div class="toast-header">
          <span class="toast-icon">
            {notification.icon || icons[notification.type]}
          </span>
          <div class="toast-title">
            {notification.title}
          </div>
          <button
            class="toast-close"
            onclick={() => removeNotification(notification.id)}
            aria-label="Close notification"
          >
            ×
          </button>
        </div>
        
        {#if notification.message}
          <div class="toast-message">
            {notification.message}
          </div>
        {/if}
        
        {#if notification.progress !== undefined}
          <div class="toast-progress-bar">
            <div 
              class="toast-progress-fill"
              style="width: {notification.progress}%"
            ></div>
          </div>
        {/if}
        
        {#if notification.actions && notification.actions.length > 0}
          <div class="toast-actions">
            {#each notification.actions as action}
              <button
                class="toast-action {action.style || 'secondary'}"
                onclick={() => handleActionClick(notification, action)}
              >
                {action.label}
              </button>
            {/each}
          </div>
        {/if}
        
        {#if !notification.persistent && notification.duration}
          <div 
            class="toast-timer"
            style="animation-duration: {notification.duration}ms"
          ></div>
        {/if}
      </div>
    {/each}
  </div>
{/if}

<style>
  .toast-container {
    position: fixed;
    z-index: 9999;
    pointer-events: none;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    max-width: 420px;
    width: 100%;
  }
  
  @media (max-width: 640px) {
    .toast-container {
      max-width: calc(100vw - 2rem);
      left: 1rem !important;
      right: 1rem !important;
      transform: none !important;
    }
  }
  
  .toast {
    background: white;
    border-radius: 8px;
    box-shadow: 
      0 10px 25px rgba(0, 0, 0, 0.1),
      0 4px 10px rgba(0, 0, 0, 0.05);
    pointer-events: all;
    overflow: hidden;
    position: relative;
    border-left: 4px solid var(--accent-color);
    animation: slideIn 0.3s ease;
  }
  
  @keyframes slideIn {
    from {
      opacity: 0;
      transform: translateX(100%);
    }
    to {
      opacity: 1;
      transform: translateX(0);
    }
  }
  
  .toast-header {
    display: flex;
    align-items: center;
    padding: 0.75rem 1rem;
    gap: 0.75rem;
  }
  
  .toast-icon {
    font-size: 1.25rem;
    flex-shrink: 0;
  }
  
  .toast-title {
    flex: 1;
    font-weight: 600;
    color: #1f2937;
    font-size: 0.95rem;
  }
  
  .toast-close {
    width: 24px;
    height: 24px;
    border: none;
    background: transparent;
    color: #6b7280;
    font-size: 1.5rem;
    line-height: 1;
    cursor: pointer;
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
  }
  
  .toast-close:hover {
    background: #f3f4f6;
    color: #1f2937;
  }
  
  .toast-message {
    padding: 0 1rem 0.75rem 3.5rem;
    color: #4b5563;
    font-size: 0.875rem;
    line-height: 1.5;
  }
  
  .toast-progress-bar {
    height: 4px;
    background: #e5e7eb;
    margin: 0.5rem 1rem;
    border-radius: 2px;
    overflow: hidden;
  }
  
  .toast-progress-fill {
    height: 100%;
    background: var(--accent-color);
    transition: width 0.3s ease;
    border-radius: 2px;
  }
  
  .toast-actions {
    display: flex;
    gap: 0.5rem;
    padding: 0.75rem 1rem;
    background: #f9fafb;
    border-top: 1px solid #e5e7eb;
  }
  
  .toast-action {
    padding: 0.375rem 0.75rem;
    border: none;
    border-radius: 6px;
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .toast-action.primary {
    background: var(--accent-color);
    color: white;
  }
  
  .toast-action.primary:hover {
    opacity: 0.9;
  }
  
  .toast-action.secondary {
    background: white;
    color: #4b5563;
    border: 1px solid #d1d5db;
  }
  
  .toast-action.secondary:hover {
    background: #f3f4f6;
  }
  
  .toast-action.danger {
    background: #ef4444;
    color: white;
  }
  
  .toast-action.danger:hover {
    background: #dc2626;
  }
  
  .toast-timer {
    position: absolute;
    bottom: 0;
    left: 0;
    height: 3px;
    background: var(--accent-color);
    opacity: 0.3;
    animation: timer linear forwards;
  }
  
  @keyframes timer {
    from {
      width: 100%;
    }
    to {
      width: 0%;
    }
  }
  
  /* Dark mode support */
  :global(.dark) .toast {
    background: #1f2937;
    box-shadow: 
      0 10px 25px rgba(0, 0, 0, 0.3),
      0 4px 10px rgba(0, 0, 0, 0.2);
  }
  
  :global(.dark) .toast-title {
    color: #f3f4f6;
  }
  
  :global(.dark) .toast-message {
    color: #d1d5db;
  }
  
  :global(.dark) .toast-close {
    color: #9ca3af;
  }
  
  :global(.dark) .toast-close:hover {
    background: #374151;
    color: #f3f4f6;
  }
  
  :global(.dark) .toast-actions {
    background: #111827;
    border-top-color: #374151;
  }
  
  :global(.dark) .toast-action.secondary {
    background: #374151;
    color: #f3f4f6;
    border-color: #4b5563;
  }
  
  :global(.dark) .toast-action.secondary:hover {
    background: #4b5563;
  }
</style>