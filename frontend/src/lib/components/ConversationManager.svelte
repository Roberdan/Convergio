<!--
💬 Conversation Manager Component
Provides conversation management UI: reset, history, resume, delete
-->

<script lang="ts">
  import { conversations, conversationManager, currentConversation } from '$lib/stores/conversationStore';
  import type { ConversationMessage } from '$lib/stores/conversationStore';

  export let agentId: string;
  export let agentName: string;
  export let compact = false;

  let showHistory = false;
  let showConfirmDelete = false;

  $: conversation = $currentConversation;
  $: hasMessages = conversation?.messages && conversation.messages.length > 0;

  function handleReset() {
    conversationManager.resetConversation(agentId);
    showHistory = false;
  }

  function handleDelete() {
    conversationManager.deleteConversation(agentId);
    showConfirmDelete = false;
  }

  function handleShowHistory() {
    showHistory = !showHistory;
  }

  async function handleSaveToMemory() {
    await conversationManager.saveConversationToMemory(agentId);
    // Show success notification (could be implemented)
  }

  async function handleLoadFromMemory() {
    await conversationManager.loadConversationFromMemory(agentId);
  }

  function formatMessageTime(timestamp: Date): string {
    return timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  function truncateContent(content: string, maxLength = 100): string {
    return content.length > maxLength ? content.substring(0, maxLength) + '...' : content;
  }
</script>

<style>
  /* No custom styles needed */
</style>

{#if compact}
  <!-- Compact conversation controls -->
  <div class="flex items-center space-x-1" role="group" aria-label="Conversation controls">
    {#if hasMessages}
      <button
        on:click={handleShowHistory}
        class="p-1 text-surface-600 hover:text-surface-300 rounded"
        aria-label="Show conversation history"
      >
        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </button>
      <button
        on:click={handleReset}
        class="p-1 text-surface-600 hover:text-orange-600 rounded"
        aria-label="Reset conversation with {agentName}"
      >
        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
      </button>
    {/if}
  </div>
{:else}
  <!-- Full conversation management panel -->
  <section class="bg-white border rounded-lg p-4 space-y-4" aria-labelledby="conversation-manager-title">
    <div class="flex items-center justify-between">
      <h3 id="conversation-manager-title" class="text-sm font-medium text-surface-900">Conversation with {agentName}</h3>
      {#if conversation}
        <span class="text-xs text-surface-500" aria-label="{conversation.messages.length} messages in conversation">
          {conversation.messages.length} messages
        </span>
      {/if}
    </div>

    <!-- Action buttons -->
    <div class="flex flex-wrap gap-2" role="group" aria-label="Conversation management actions">
      {#if hasMessages}
        <button
          on:click={handleShowHistory}
          class="inline-flex items-center px-3 py-1.5 text-xs font-medium text-surface-600 bg-surface-100 hover:bg-surface-200 rounded-md transition-colors"
          aria-label="{showHistory ? 'Hide' : 'Show'} conversation history"
        >
          <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {showHistory ? 'Hide' : 'Show'} History
        </button>

        <button
          on:click={handleReset}
          class="inline-flex items-center px-3 py-1.5 text-xs font-medium text-orange-700 bg-orange-100 hover:bg-orange-200 rounded-md transition-colors"
          aria-label="Reset conversation with {agentName}"
        >
          <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Reset
        </button>

        <button
          on:click={handleSaveToMemory}
          class="inline-flex items-center px-3 py-1.5 text-xs font-medium text-blue-700 bg-blue-100 hover:bg-blue-200 rounded-md transition-colors"
          aria-label="Save conversation to memory"
        >
          <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3-3m0 0l-3 3m3-3v12" />
          </svg>
          Save
        </button>

        <button
          on:click={() => showConfirmDelete = true}
          class="inline-flex items-center px-3 py-1.5 text-xs font-medium text-red-700 bg-red-100 hover:bg-red-200 rounded-md transition-colors"
          aria-label="Delete conversation with {agentName}"
        >
          <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
          Delete
        </button>
      {/if}

      <button
        on:click={handleLoadFromMemory}
        class="inline-flex items-center px-3 py-1.5 text-xs font-medium text-green-700 bg-green-100 hover:bg-green-200 rounded-md transition-colors"
        aria-label="Load conversation from memory"
      >
        <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
        </svg>
        Load
      </button>
    </div>

    <!-- Conversation history -->
    {#if showHistory && conversation?.messages && conversation.messages.length > 0}
      <div class="border-t pt-4">
        <h4 id="conversation-history-title" class="text-xs font-medium text-surface-600 mb-2">Conversation History</h4>
        <div class="space-y-2 max-h-64 overflow-y-auto" role="log" aria-labelledby="conversation-history-title">
          {#each conversation.messages as message (message.id)}
            <div class="flex items-start space-x-2 p-2 rounded border-l-2 {message.type === 'user' ? 'border-blue-200 bg-blue-50' : 'border-green-200 bg-green-50'}" role="group" aria-label="{message.type === 'user' ? 'Your message' : message.agentName + ' message'}">
              <div class="text-xs text-surface-500 mt-0.5 w-12 flex-shrink-0" aria-label="Message time {formatMessageTime(message.timestamp)}">
                <time datetime="{message.timestamp.toISOString()}">{formatMessageTime(message.timestamp)}</time>
              </div>
              <div class="flex-1 min-w-0">
                <div class="text-xs font-medium text-surface-600 mb-1">
                  {message.type === 'user' ? 'You' : message.agentName}
                </div>
                <div class="text-xs text-surface-600 break-words">
                  {truncateContent(message.content)}
                </div>
              </div>
              <div class="text-xs text-surface-600" role="status">
                {#if message.status === 'sending'}
                  <span class="animate-spin" aria-label="Sending message">⏳</span>
                {:else if message.status === 'error'}
                  <span class="text-red-500" aria-label="Message failed">❌</span>
                {:else}
                  <span class="text-green-500" aria-label="Message delivered">✓</span>
                {/if}
              </div>
            </div>
          {/each}
        </div>
      </div>
    {/if}

    <!-- Delete confirmation modal -->
    {#if showConfirmDelete}
      <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" role="dialog" aria-labelledby="delete-modal-title" aria-describedby="delete-modal-description">
        <div class="bg-white rounded-lg p-6 max-w-sm mx-4">
          <h3 id="delete-modal-title" class="text-lg font-medium text-surface-900 mb-2">Delete Conversation?</h3>
          <p id="delete-modal-description" class="text-sm text-surface-600 mb-4">
            This will permanently delete your conversation with {agentName}. This action cannot be undone.
          </p>
          <div class="flex space-x-3">
            <button
              on:click={() => showConfirmDelete = false}
              class="flex-1 px-3 py-2 text-sm font-medium text-surface-600 bg-surface-100 hover:bg-surface-200 rounded-md transition-colors"
              aria-label="Cancel deletion"
            >
              Cancel
            </button>
            <button
              on:click={handleDelete}
              class="flex-1 px-3 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-md transition-colors"
              aria-label="Confirm deletion of conversation with {agentName}"
            >
              Delete
            </button>
          </div>
        </div>
      </div>
    {/if}
  </section>
{/if}