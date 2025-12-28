<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { writable } from 'svelte/store';
  import { fly, fade } from 'svelte/transition';
  
  export let maxEvents: number = 100;
  export let wsEndpoint: string = 'ws://localhost:9000/ws/activity';
  export let autoScroll: boolean = true;

  type EventType = 'agent' | 'user' | 'system' | 'api' | 'workflow' | 'error';

  interface ActivityEvent {
    id: string;
    timestamp: Date;
    type: EventType;
    category: string;
    title: string;
    description?: string;
    userId?: string;
    userName?: string;
    agentId?: string;
    agentName?: string;
    metadata?: any;
    duration?: number;
    status?: 'success' | 'pending' | 'failed';
    relatedEvents?: string[];
  }
  
  interface ActivityFilter {
    types: Set<string>;
    categories: Set<string>;
    searchQuery: string;
    dateRange: {
      start: Date | null;
      end: Date | null;
    };
  }
  
  let events = writable<ActivityEvent[]>([]);
  let filteredEvents = writable<ActivityEvent[]>([]);
  let ws: WebSocket | null = null;
  let isConnected = false;
  let isPaused = false;
  let timelineContainer: HTMLElement;
  
  let filter: ActivityFilter = {
    types: new Set(['agent', 'user', 'system', 'api', 'workflow', 'error']),
    categories: new Set(),
    searchQuery: '',
    dateRange: {
      start: null,
      end: null
    }
  };

  const eventIcons: Record<EventType, string> = {
    agent: '🤖',
    user: '👤',
    system: '⚙️',
    api: '🔌',
    workflow: '🔄',
    error: '❌'
  };

  const eventColors: Record<EventType, string> = {
    agent: '#4f46e5',
    user: '#10b981',
    system: '#6b7280',
    api: '#3b82f6',
    workflow: '#8b5cf6',
    error: '#ef4444'
  };
  
  function connectWebSocket() {
    if (ws) ws.close();
    
    ws = new WebSocket(wsEndpoint);
    
    ws.onopen = () => {
      isConnected = true;
    };
    
    ws.onmessage = (event) => {
      if (!isPaused) {
        try {
          const data = JSON.parse(event.data);
          handleActivityEvent(data);
        } catch {
          // Silent failure
        }
      }
    };
    
    ws.onerror = () => {
      // Silent failure
    };
    
    ws.onclose = () => {
      isConnected = false;
      // Reconnect after 5 seconds
      setTimeout(connectWebSocket, 5000);
    };
  }
  
  function handleActivityEvent(data: any) {
    const event: ActivityEvent = {
      id: data.id || crypto.randomUUID(),
      timestamp: new Date(data.timestamp || Date.now()),
      type: data.type,
      category: data.category || 'general',
      title: data.title,
      description: data.description,
      userId: data.userId,
      userName: data.userName,
      agentId: data.agentId,
      agentName: data.agentName,
      metadata: data.metadata,
      duration: data.duration,
      status: data.status,
      relatedEvents: data.relatedEvents
    };
    
    events.update(e => {
      const updated = [event, ...e];
      // Keep only maxEvents
      if (updated.length > maxEvents) {
        updated.pop();
      }
      return updated;
    });
    
    applyFilters();
    
    if (autoScroll && timelineContainer) {
      setTimeout(() => {
        timelineContainer.scrollTop = 0;
      }, 100);
    }
  }
  
  function applyFilters() {
    events.update(e => {
      filteredEvents.set(e.filter(event => {
        // Type filter
        if (!filter.types.has(event.type)) return false;
        
        // Category filter
        if (filter.categories.size > 0 && !filter.categories.has(event.category)) {
          return false;
        }
        
        // Search filter
        if (filter.searchQuery) {
          const query = filter.searchQuery.toLowerCase();
          const searchableText = [
            event.title,
            event.description,
            event.userName,
            event.agentName
          ].filter(Boolean).join(' ').toLowerCase();
          
          if (!searchableText.includes(query)) return false;
        }
        
        // Date range filter
        if (filter.dateRange.start && event.timestamp < filter.dateRange.start) {
          return false;
        }
        if (filter.dateRange.end && event.timestamp > filter.dateRange.end) {
          return false;
        }
        
        return true;
      }));
      return e;
    });
  }
  
  function toggleTypeFilter(type: string) {
    if (filter.types.has(type)) {
      filter.types.delete(type);
    } else {
      filter.types.add(type);
    }
    applyFilters();
  }
  
  function clearFilters() {
    filter = {
      types: new Set(['agent', 'user', 'system', 'api', 'workflow', 'error']),
      categories: new Set(),
      searchQuery: '',
      dateRange: {
        start: null,
        end: null
      }
    };
    applyFilters();
  }
  
  function exportEvents() {
    const data = JSON.stringify($filteredEvents, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `activity-timeline-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }
  
  function formatTime(date: Date): string {
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit',
      second: '2-digit'
    });
  }
  
  function formatDuration(ms: number): string {
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    return `${(ms / 60000).toFixed(1)}m`;
  }
  
  function getRelativeTime(date: Date): string {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    
    if (diff < 60000) return 'just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return `${Math.floor(diff / 86400000)}d ago`;
  }
  
  // Load historical events
  async function loadHistory() {
    try {
      const response = await fetch('/api/activity/history?limit=50');
      if (response.ok) {
        const data = await response.json();
        events.set(data.map((e: any) => ({
          ...e,
          timestamp: new Date(e.timestamp)
        })));
        applyFilters();
      }
    } catch {
      // Silent failure
    }
  }
  
  onMount(() => {
    connectWebSocket();
    loadHistory();
  });
  
  onDestroy(() => {
    if (ws) ws.close();
  });
</script>

<div class="activity-timeline">
  <div class="timeline-header">
    <div class="header-left">
      <h2>📋 Activity Timeline</h2>
      <div class="connection-indicator" class:connected={isConnected}>
        {isConnected ? '🟢' : '🔴'}
      </div>
      <span class="event-count">
        {$filteredEvents.length} / {$events.length} events
      </span>
    </div>
    
    <div class="header-actions">
      <button
        class="pause-btn"
        class:active={isPaused}
        on:click={() => isPaused = !isPaused}
      >
        {isPaused ? '▶️ Resume' : '⏸️ Pause'}
      </button>
      <button
        class="scroll-btn"
        class:active={autoScroll}
        on:click={() => autoScroll = !autoScroll}
      >
        📜 Auto-scroll
      </button>
      <button
        class="export-btn"
        on:click={exportEvents}
      >
        💾 Export
      </button>
    </div>
  </div>
  
  <div class="timeline-filters">
    <fieldset class="filter-group">
      <legend>Event Types:</legend>
      <div class="filter-chips">
        {#each Object.entries(eventIcons) as [type, icon]}
          <button
            class="filter-chip"
            class:active={filter.types.has(type)}
            style="--chip-color: {eventColors[type as EventType]}"
            on:click={() => toggleTypeFilter(type)}
          >
            {icon} {type}
          </button>
        {/each}
      </div>
    </fieldset>
    
    <div class="filter-search">
      <input
        type="search"
        placeholder="Search events..."
        bind:value={filter.searchQuery}
        on:input={applyFilters}
        class="search-input"
      />
      <button
        class="clear-filters"
        on:click={clearFilters}
      >
        Clear Filters
      </button>
    </div>
  </div>
  
  <div class="timeline-container" bind:this={timelineContainer}>
    <div class="timeline-line"></div>
    
    {#each $filteredEvents as event, index (event.id)}
      <div 
        class="timeline-event"
        in:fly={{ x: -50, duration: 300, delay: index * 50 }}
        out:fade={{ duration: 200 }}
      >
        <div class="event-time">
          <div class="time-label">{formatTime(event.timestamp)}</div>
          <div class="time-relative">{getRelativeTime(event.timestamp)}</div>
        </div>
        
        <div
          class="event-marker"
          style="background: {eventColors[event.type]}"
        >
          <span class="event-icon">{eventIcons[event.type]}</span>
        </div>
        
        <div class="event-content">
          <div class="event-header">
            <h4 class="event-title">{event.title}</h4>
            {#if event.status}
              <span class="event-status {event.status}">
                {event.status === 'success' ? '✅' : event.status === 'failed' ? '❌' : '⏳'}
                {event.status}
              </span>
            {/if}
            {#if event.duration}
              <span class="event-duration">
                ⏱️ {formatDuration(event.duration)}
              </span>
            {/if}
          </div>
          
          {#if event.description}
            <p class="event-description">{event.description}</p>
          {/if}
          
          <div class="event-meta">
            {#if event.userName}
              <span class="meta-item">
                👤 {event.userName}
              </span>
            {/if}
            {#if event.agentName}
              <span class="meta-item">
                🤖 {event.agentName}
              </span>
            {/if}
            {#if event.category}
              <span class="meta-item category">
                📁 {event.category}
              </span>
            {/if}
          </div>
          
          {#if event.metadata && Object.keys(event.metadata).length > 0}
            <details class="event-details">
              <summary>View Details</summary>
              <pre class="event-metadata">{JSON.stringify(event.metadata, null, 2)}</pre>
            </details>
          {/if}
          
          {#if event.relatedEvents && event.relatedEvents.length > 0}
            <div class="related-events">
              <span class="related-label">Related:</span>
              {#each event.relatedEvents as relatedId}
                <span class="related-id">{relatedId}</span>
              {/each}
            </div>
          {/if}
        </div>
      </div>
    {/each}
    
    {#if $filteredEvents.length === 0}
      <div class="empty-state">
        <span class="empty-icon">📭</span>
        <p>No activity events to display</p>
        {#if filter.searchQuery || filter.types.size < 6}
          <button on:click={clearFilters} class="reset-btn">
            Reset Filters
          </button>
        {/if}
      </div>
    {/if}
  </div>
</div>

<style>
  .activity-timeline {
    height: 100%;
    display: flex;
    flex-direction: column;
    background: #f9fafb;
  }
  
  .timeline-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 1.5rem;
    background: white;
    border-bottom: 1px solid #e5e7eb;
  }
  
  .header-left {
    display: flex;
    align-items: center;
    gap: 1rem;
  }
  
  .header-left h2 {
    margin: 0;
    font-size: 1.25rem;
    color: #1f2937;
  }
  
  .connection-indicator {
    font-size: 0.75rem;
  }
  
  .event-count {
    color: #6b7280;
    font-size: 0.875rem;
  }
  
  .header-actions {
    display: flex;
    gap: 0.5rem;
  }
  
  .pause-btn,
  .scroll-btn,
  .export-btn {
    padding: 0.375rem 0.75rem;
    background: white;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    font-size: 0.875rem;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .pause-btn.active,
  .scroll-btn.active {
    background: #4f46e5;
    color: white;
    border-color: #4f46e5;
  }
  
  .pause-btn:hover,
  .scroll-btn:hover,
  .export-btn:hover {
    background: #f3f4f6;
  }
  
  .timeline-filters {
    padding: 1rem 1.5rem;
    background: white;
    border-bottom: 1px solid #e5e7eb;
  }
  
  .filter-group {
    margin-bottom: 1rem;
  }
  
  .filter-group legend {
    display: block;
    margin-bottom: 0.5rem;
    font-size: 0.875rem;
    font-weight: 500;
    color: #6b7280;
  }
  
  .filter-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }
  
  .filter-chip {
    padding: 0.25rem 0.75rem;
    background: white;
    border: 2px solid #e5e7eb;
    border-radius: 20px;
    font-size: 0.875rem;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .filter-chip.active {
    background: var(--chip-color);
    color: white;
    border-color: var(--chip-color);
  }
  
  .filter-search {
    display: flex;
    gap: 0.5rem;
  }
  
  .search-input {
    flex: 1;
    padding: 0.5rem 1rem;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    font-size: 0.875rem;
  }
  
  .clear-filters {
    padding: 0.5rem 1rem;
    background: #ef4444;
    color: white;
    border: none;
    border-radius: 6px;
    font-size: 0.875rem;
    cursor: pointer;
    transition: background 0.2s;
  }
  
  .clear-filters:hover {
    background: #dc2626;
  }
  
  .timeline-container {
    flex: 1;
    overflow-y: auto;
    padding: 2rem;
    position: relative;
  }
  
  .timeline-line {
    position: absolute;
    left: 8rem;
    top: 0;
    bottom: 0;
    width: 2px;
    background: #e5e7eb;
  }
  
  .timeline-event {
    display: flex;
    align-items: flex-start;
    margin-bottom: 2rem;
    position: relative;
  }
  
  .event-time {
    width: 6rem;
    text-align: right;
    padding-right: 1rem;
  }
  
  .time-label {
    font-size: 0.875rem;
    font-weight: 500;
    color: #1f2937;
  }
  
  .time-relative {
    font-size: 0.75rem;
    color: #9ca3af;
    margin-top: 0.25rem;
  }
  
  .event-marker {
    position: relative;
    width: 2.5rem;
    height: 2.5rem;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }
  
  .event-icon {
    font-size: 1.25rem;
  }
  
  .event-content {
    flex: 1;
    margin-left: 1.5rem;
    padding: 1rem;
    background: white;
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  .event-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 0.5rem;
  }
  
  .event-title {
    margin: 0;
    font-size: 1rem;
    font-weight: 600;
    color: #1f2937;
  }
  
  .event-status {
    padding: 0.125rem 0.5rem;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 500;
  }
  
  .event-status.success {
    background: #dcfce7;
    color: #166534;
  }
  
  .event-status.failed {
    background: #fee2e2;
    color: #991b1b;
  }
  
  .event-status.pending {
    background: #fef3c7;
    color: #92400e;
  }
  
  .event-duration {
    font-size: 0.75rem;
    color: #6b7280;
  }
  
  .event-description {
    margin: 0.5rem 0;
    color: #4b5563;
    font-size: 0.875rem;
    line-height: 1.5;
  }
  
  .event-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem;
    margin-top: 0.75rem;
  }
  
  .meta-item {
    font-size: 0.75rem;
    color: #6b7280;
  }
  
  .meta-item.category {
    padding: 0.125rem 0.5rem;
    background: #f3f4f6;
    border-radius: 4px;
  }
  
  .event-details {
    margin-top: 0.75rem;
  }
  
  .event-details summary {
    cursor: pointer;
    font-size: 0.875rem;
    color: #4f46e5;
    font-weight: 500;
  }
  
  .event-metadata {
    margin-top: 0.5rem;
    padding: 0.75rem;
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 4px;
    font-size: 0.75rem;
    overflow-x: auto;
  }
  
  .related-events {
    margin-top: 0.75rem;
    padding-top: 0.75rem;
    border-top: 1px solid #e5e7eb;
  }
  
  .related-label {
    font-size: 0.75rem;
    color: #6b7280;
    margin-right: 0.5rem;
  }
  
  .related-id {
    display: inline-block;
    padding: 0.125rem 0.375rem;
    background: #e0e7ff;
    color: #3730a3;
    border-radius: 4px;
    font-size: 0.75rem;
    margin-right: 0.25rem;
  }
  
  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 4rem;
    color: #9ca3af;
  }
  
  .empty-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
  }
  
  .reset-btn {
    margin-top: 1rem;
    padding: 0.5rem 1rem;
    background: #4f46e5;
    color: white;
    border: none;
    border-radius: 6px;
    cursor: pointer;
  }
</style>