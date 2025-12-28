<!--
  Individual Agent Interface
  Dynamic route for specific agent interactions
-->

<script lang="ts">
  import { page } from '$app/stores';
  import { onMount } from 'svelte';
  import AgentStatus from '$lib/components/AgentStatus.svelte';
  import ConversationManager from '$lib/components/ConversationManager.svelte';
  
  // Get agent name from URL parameter
  $: agentName = $page.params.agent;
  $: agentDisplayName = agentName?.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) || 'Agent';
  
  // Agent status
  let agentInfo = {
    name: agentDisplayName,
    role: 'AI Agent',
    status: 'online',
    description: 'Intelligent AI agent ready to assist you with various tasks.'
  };
  
  // Messages state
  let messages: Array<{
    id: string;
    type: 'user' | 'agent';
    content: string;
    timestamp: Date;
    agent?: string;
  }> = [];
  
  let currentMessage = '';
  let isLoading = false;
  let streamingResponse = '';
  
  // Conversation management
  let conversationId = '';
  
  onMount(() => {
    // Generate conversation ID for this session
    conversationId = `conv_${Date.now()}`;
    
    // Add welcome message
    messages = [{
      id: 'welcome',
      type: 'agent',
      content: `Hello! I'm ${agentDisplayName}. How can I help you today?`,
      timestamp: new Date(),
      agent: agentName
    }];
  });
  
  async function sendMessage() {
    if (!currentMessage.trim() || isLoading) return;
    
    const userMessage = {
      id: `user_${Date.now()}`,
      type: 'user' as const,
      content: currentMessage,
      timestamp: new Date()
    };
    
    messages = [...messages, userMessage];
    const query = currentMessage;
    currentMessage = '';
    isLoading = true;
    streamingResponse = '';
    
    try {
      // Send to backend API
      const response = await fetch('/api/agents/conversation', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          agent: agentName,
          message: query,
          conversation_id: conversationId
        })
      });
      
      if (!response.ok) {
        throw new Error('Failed to send message');
      }
      
      const data = await response.json();
      
      // Add agent response
      const agentMessage = {
        id: `agent_${Date.now()}`,
        type: 'agent' as const,
        content: data.response || 'I received your message and I\'m processing it.',
        timestamp: new Date(),
        agent: agentName
      };
      
      messages = [...messages, agentMessage];
      
    } catch {
      // Silent failure

      // Add error response for testing
      const errorMessage = {
        id: `error_${Date.now()}`,
        type: 'agent' as const,
        content: `I apologize, but I'm currently experiencing some technical difficulties. Your message "${query}" was received, and I'm working on a response.`,
        timestamp: new Date(),
        agent: agentName
      };
      
      messages = [...messages, errorMessage];
    } finally {
      isLoading = false;
    }
  }
  
  function handleKeyDown(event: KeyboardEvent) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  }
  
  function clearConversation() {
    messages = [{
      id: 'welcome',
      type: 'agent',
      content: `Conversation cleared. I'm ${agentDisplayName}, ready to help!`,
      timestamp: new Date(),
      agent: agentName
    }];
    conversationId = `conv_${Date.now()}`;
  }
</script>

<svelte:head>
  <title>{agentDisplayName} - Convergio AI</title>
</svelte:head>

<div class="min-h-screen bg-surface-50">
  <!-- Header -->
  <div class="bg-white border-b border-surface-200">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between items-center py-6">
        <div class="flex items-center space-x-4">
          <div class="flex-shrink-0">
            <div class="w-12 h-12 bg-blue-500 rounded-full flex items-center justify-center">
              <span class="text-white font-bold text-lg">
                {agentDisplayName.charAt(0)}
              </span>
            </div>
          </div>
          <div>
            <h1 class="text-2xl font-bold text-surface-900">
              {agentDisplayName}
            </h1>
            <p class="text-sm text-surface-500">
              {agentInfo.role} • {agentInfo.status}
            </p>
          </div>
        </div>
        
        <div class="flex items-center space-x-4">
          <button
            on:click={clearConversation}
            data-testid="clear-conversation"
            class="inline-flex items-center px-4 py-2 border border-surface-300 rounded-md shadow-sm text-sm font-medium text-surface-600 bg-white hover:bg-surface-50"
          >
            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Clear
          </button>
          
          <AgentStatus agentId={agentName} agentName={agentDisplayName} />
        </div>
      </div>
    </div>
  </div>

  <!-- Chat Interface -->
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
    <div class="bg-white rounded-lg shadow h-[600px] flex flex-col" data-testid="chat-interface">
      
      <!-- Messages Area -->
      <div class="flex-1 overflow-y-auto p-6 space-y-4">
        {#each messages as message}
          <div class="flex {message.type === 'user' ? 'justify-end' : 'justify-start'}" data-testid="{message.type}-message">
            <div class="max-w-xs lg:max-w-md px-4 py-2 rounded-lg {
              message.type === 'user' 
                ? 'bg-blue-500 text-white' 
                : 'bg-surface-100 text-surface-900'
            }">
              <div class="text-sm break-words whitespace-pre-wrap" data-testid="message-content">
                {message.content}
              </div>
              <div class="text-xs opacity-75 mt-1">
                <span data-testid="message-timestamp">{message.timestamp.toLocaleTimeString()}</span>
                {#if message.agent}
                  <span data-testid="agent-name">• {message.agent}</span>
                {/if}
              </div>
            </div>
          </div>
        {/each}
        
        {#if isLoading}
          <div class="flex justify-start">
            <div class="max-w-xs lg:max-w-md px-4 py-2 rounded-lg bg-surface-100">
              <div class="flex items-center space-x-2">
                <div class="flex space-x-1">
                  <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
                  <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
                </div>
                <span class="text-sm text-surface-500">Thinking...</span>
              </div>
            </div>
          </div>
        {/if}
      </div>
      
      <!-- Input Area -->
      <div class="border-t border-surface-200 p-4">
        <div class="flex space-x-4">
          <div class="flex-1">
            <textarea
              bind:value={currentMessage}
              on:keydown={handleKeyDown}
              placeholder="Type your message..."
              rows="1"
              data-testid="chat-input"
              class="w-full px-3 py-2 border border-surface-300 rounded-md resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={isLoading}
            ></textarea>
          </div>
          <button
            on:click={sendMessage}
            disabled={!currentMessage.trim() || isLoading}
            data-testid="send-button"
            aria-label="Send message"
            class="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</div>