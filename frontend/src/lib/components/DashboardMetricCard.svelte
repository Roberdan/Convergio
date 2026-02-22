<script lang="ts">
  import { run } from 'svelte/legacy';

  import { createEventDispatcher } from 'svelte';
  
  
  interface Props {
    title: string;
    // eslint-disable-next-line no-unused-vars
    value: string | number;
    change: number;
    changeType?: 'increase' | 'decrease' | 'neutral';
    icon: string;
    iconColor?: string;
    bgColor?: string;
    formatValue?: any;
    showChange?: boolean;
    loading?: boolean;
  }

  let {
    title,
    value,
    change,
    changeType = 'neutral',
    icon,
    iconColor = 'text-blue-600',
    bgColor = 'bg-blue-50',
    formatValue = (val: string | number) => String(val),
    showChange = true,
    loading = false
  }: Props = $props();
  
  run(() => {
    void value;
  });

  const dispatch = createEventDispatcher();

  let changeIcon = $derived(changeType === 'increase' ? '/convergio_icons/up.svg' : 
                   changeType === 'decrease' ? '/convergio_icons/down.svg' : 
                   '/convergio_icons/minus.svg');
  
  let changeTextColor = $derived(changeType === 'increase' ? 'text-green-700' : 
                       changeType === 'decrease' ? 'text-red-700' : 
                       'text-surface-600');

  function handleClick() {
    dispatch('click');
  }
</script>

<div
  class="rounded-xl border-2 border-surface-200 bg-white p-6 shadow-lg hover:shadow-xl hover:border-blue-500 transition-all duration-300 cursor-pointer {loading ? 'opacity-60' : ''}"
  onclick={handleClick}
  onkeydown={(e) => e.key === 'Enter' || e.key === ' ' ? handleClick() : null}
  role="button"
  tabindex="0"
  aria-label={`Dashboard metric card for ${title}`}
>
  <div class="flex items-center justify-between">
    <div class="flex items-center space-x-4">
      <div class="rounded-lg {bgColor} p-3 border-2 border-blue-200">
        <img src={icon} alt="" class="h-6 w-6 {iconColor}" />
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
