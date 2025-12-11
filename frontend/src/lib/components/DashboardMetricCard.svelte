<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  
  export let title: string;
  // eslint-disable-next-line no-unused-vars
  export let value: string | number;
  export let change: number;
  export let changeType: 'increase' | 'decrease' | 'neutral' = 'neutral';
  export let icon: string;
  export const iconColor: string = 'text-blue-600';
  export const bgColor: string = 'bg-blue-50';
  export const valueColor: string = 'text-surface-100 dark:text-surface-900';
  export const changeColor: string = 'text-green-600';
  export let formatValue = (val: string | number) => String(val);
  export let showChange: boolean = true;
  export let loading: boolean = false;
  
  $: void value;

  const dispatch = createEventDispatcher();

  $: changeIcon = changeType === 'increase' ? '/convergio_icons/up.svg' : 
                   changeType === 'decrease' ? '/convergio_icons/down.svg' : 
                   '/convergio_icons/minus.svg';
  
  $: changeTextColor = changeType === 'increase' ? 'text-green-700' : 
                       changeType === 'decrease' ? 'text-red-700' : 
                       'text-surface-300 dark:text-surface-700';

  function handleClick() {
    dispatch('click');
  }
</script>

<div
  class="rounded-xl border-2 border-surface-200 bg-white p-6 shadow-lg hover:shadow-xl hover:border-blue-500 transition-all duration-300 cursor-pointer {loading ? 'opacity-60' : ''}"
  on:click={handleClick}
  on:keydown={(e) => e.key === 'Enter' || e.key === ' ' ? handleClick() : null}
  role="button"
  tabindex="0"
  aria-label={`Dashboard metric card for ${title}`}
>
  <div class="flex items-center justify-between">
    <div class="flex items-center space-x-4">
      <div class="rounded-lg bg-blue-100 p-3 border-2 border-blue-200">
        <img src={icon} alt="" class="h-6 w-6 text-blue-600" />
      </div>
      <div>
        <p class="text-sm font-bold text-surface-600 mb-1">{title}</p>
        <p class="text-2xl font-bold text-surface-900">
          {loading ? '...' : formatValue(value)}
        </p>
      </div>
    </div>

    {#if showChange && !loading}
      <div class="flex items-center space-x-2 bg-surface-100 px-3 py-2 rounded-lg">
        <img src={changeIcon} alt="" class="h-4 w-4" />
        <span class="text-sm font-bold {changeTextColor}">
          {change > 0 ? '+' : ''}{change}%
        </span>
      </div>
    {/if}
  </div>
</div>