<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import MarkdownRenderer from './MarkdownRenderer.svelte';
  import '../styles/ali-breathing.css';

  // Ali state
  let isOpen = false;
  let isMinimized = false;
  let isTyping = false;
  let isProactive = true;

  // Messages - start empty, Ali will respond intelligently when asked
  let messages: any[] = [];
  let messagesContainer: HTMLElement;
  
  let newMessage = '';

  // Auto-scroll function
  function scrollToBottom() {
    if (messagesContainer) {
      setTimeout(() => {
        messagesContainer.scrollTo({
          top: messagesContainer.scrollHeight,
          behavior: 'smooth'
        });
      }, 100);
    }
  }

  // Watch messages changes to auto-scroll
  $: if (messages.length > 0) {
    scrollToBottom();
  }

  onMount(async () => {
    startProactiveMode();
  });

  function startProactiveMode() {
  }

  function showProactiveHint() {
    // Skip proactive hints - let Ali be quiet until asked
    return;
  }

  async function sendMessage() {
    if (!newMessage.trim()) return;
    
    // Add user message
    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: newMessage.trim(),
      timestamp: new Date()
    };
    
    messages = [...messages, userMessage];
    const currentMessage = newMessage.trim();
    newMessage = '';
    
    // Show typing indicator
    isTyping = true;
    
    try {
        // Real API call with Ali Intelligence System
        const response = await fetch('http://localhost:9000/api/v1/agents/ali/intelligence', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            message: currentMessage,
            context: {
              source: 'ali_assistant',
              role: 'ceo',
              interface: 'floating_assistant'
            },
            use_vector_search: true,
            use_database_insights: true,
            include_strategic_analysis: true
          })
        });

        if (response.ok) {
          const result = await response.json();
          const aiResponse = {
            id: Date.now() + 1,
            type: 'ai',
            content: result.response,
            timestamp: new Date(),
            agents_used: result.agents_used
          };
          messages = [...messages, aiResponse];
        } else {
          const errorText = await response.text();
          const aiResponse = {
            id: Date.now() + 1,
            type: 'ai',
            content: `API Error (${response.status}): ${response.statusText}. Backend response: ${errorText.substring(0, 200)}...`,
            timestamp: new Date()
          };
          messages = [...messages, aiResponse];
        }
    } catch {
      // Silent failure
      const errorResponse = {
        id: Date.now() + 1,
        type: 'ai',
        content: `I encountered a brief connection issue while processing your request. Please try again, and I'll coordinate with the team to get you the strategic analysis you need.`,
        timestamp: new Date()
      };
      messages = [...messages, errorResponse];
    } finally {
      isTyping = false;
    }
  }

  function handleKeyPress(event: KeyboardEvent) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  }

  function toggleOpen() {
    isOpen = !isOpen;
    isMinimized = false;
  }

  function minimize() {
    isMinimized = true;
    isOpen = false;
  }

  function openFullChat() {
    goto('/agents');
  }
</script>

<style>
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
</style>

<!-- Ali Floating Assistant -->
<div class="fixed bottom-4 right-4 z-50 font-mono">
  {#if isOpen}
    <!-- Chat Window -->
    <div class="bg-white border border-surface-200 rounded-lg shadow-xl w-80 h-96 flex flex-col mb-4" role="dialog" aria-labelledby="ali-chat-title" aria-describedby="ali-chat-description">
      <!-- Header -->
      <div class="px-4 py-3 border-b border-surface-200 flex items-center justify-between bg-surface-50 rounded-t-lg">
        <div class="flex items-center space-x-2">
          <!-- Ali Enso Icon (Buddhist breathing) - Zen Style -->
          <div class="relative w-6 h-6 animate-zen-glow" role="img" aria-label="Ali assistant status indicator">
            <svg class="w-6 h-6 transform-gpu {isProactive ? 'ali-proactive' : 'ali-reactive'}" viewBox="0 0 24 24" aria-hidden="true">
              <defs>
                <linearGradient id="ensoZenGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" style="stop-color:#1e3a8a;stop-opacity:1" />
                  <stop offset="40%" style="stop-color:#3b82f6;stop-opacity:0.9" />
                  <stop offset="80%" style="stop-color:#60a5fa;stop-opacity:0.8" />
                  <stop offset="100%" style="stop-color:#e0f2fe;stop-opacity:0.7" />
                </linearGradient>
                <radialGradient id="ensoZenInner" cx="50%" cy="50%" r="50%">
                  <stop offset="0%" style="stop-color:#1e3a8a;stop-opacity:0.6" />
                  <stop offset="70%" style="stop-color:#3b82f6;stop-opacity:0.3" />
                  <stop offset="100%" style="stop-color:#e0f2fe;stop-opacity:0.1" />
                </radialGradient>
              </defs>
              <!-- Enso circle with gap (traditional zen circle) -->
              <circle 
                cx="12" 
                cy="12" 
                r="8" 
                fill="none" 
                stroke="url(#ensoZenGradient)" 
                stroke-width="2.5" 
                stroke-linecap="round"
                stroke-dasharray="42 8"
                class="animate-zen-breathing"
                transform-origin="12 12"
                style="transform: rotate(-15deg);"
              />
              <!-- Inner breathing light -->
              <circle 
                cx="12" 
                cy="12" 
                r="4" 
                fill="url(#ensoZenInner)" 
                class="animate-zen-breathing-inner"
                transform-origin="12 12"
              />
              <!-- Subtle zen pulse background -->
              <circle 
                cx="12" 
                cy="12" 
                r="10" 
                fill="none"
                stroke="url(#ensoZenGradient)" 
                stroke-width="0.5"
                opacity="0.2"
                class="animate-zen-pulse"
                transform-origin="12 12"
              />
            </svg>
          </div>
          <div>
            <h3 id="ali-chat-title" class="text-sm font-medium text-surface-900">Ali - Chief of Staff</h3>
            <p id="ali-chat-description" class="text-xs text-surface-500">AI Strategic Coordinator</p>
          </div>
        </div>
        <div class="flex items-center space-x-1">
          <button 
            on:click={minimize}
            class="p-1 hover:bg-surface-200 rounded text-surface-500"
            aria-label="Minimize Ali chat window"
          >
            <img src="/convergio_icons/minimize.svg" alt="" class="h-3 w-3" />
          </button>
          <button 
            on:click={openFullChat}
            class="p-1 hover:bg-surface-200 rounded text-surface-500"
            aria-label="Open full chat interface"
          >
            <img src="/convergio_icons/expand.svg" alt="" class="h-3 w-3" />
          </button>
          <button 
            on:click={toggleOpen}
            class="p-1 hover:bg-surface-200 rounded text-surface-500"
            aria-label="Close Ali chat window"
          >
            <img src="/convergio_icons/close.svg" alt="" class="h-3 w-3" />
          </button>
        </div>
      </div>

      <!-- Messages -->
      <div bind:this={messagesContainer} class="flex-1 overflow-y-auto p-3 space-y-3" role="log" aria-label="Chat conversation with Ali" aria-live="polite">
        {#each messages as message}
          <div class="flex {message.type === 'user' ? 'justify-end' : 'justify-start'}">
            <div class="max-w-xs">
              {#if message.type === 'user'}
                <div class="bg-gray-900 text-white p-2 rounded-lg rounded-br-sm text-xs" role="group" aria-label="Your message">
                  <div class="font-medium text-xs mb-1 opacity-75" aria-hidden="true">You (CEO)</div>
                  <MarkdownRenderer content={message.content} />
                </div>
              {:else}
                <div class="bg-surface-100 p-2 rounded-lg rounded-bl-sm text-xs" role="group" aria-label="Ali's response">
                  <div class="flex items-center space-x-1 mb-1">
                    <svg class="w-3 h-3 animate-breathing" viewBox="0 0 24 24" aria-hidden="true">
                      <circle cx="12" cy="12" r="8" fill="none" stroke="#1e3a8a" stroke-width="3" stroke-linecap="round" stroke-dasharray="45 5" style="transform: rotate(-10deg);" />
                    </svg>
                    <span class="font-medium text-xs text-surface-900">Ali</span>
                    <span class="text-xs text-surface-500">• Chief of Staff</span>
                  </div>
                  <div class="text-surface-900"><MarkdownRenderer content={message.content} /></div>
                </div>
              {/if}
              <div class="text-xs text-surface-500 mt-1 {message.type === 'user' ? 'text-right' : 'text-left'}" aria-label="Message sent at {message.timestamp.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}">
                <time datetime="{message.timestamp.toISOString()}">{message.timestamp.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</time>
              </div>
            </div>
          </div>
        {/each}
        
        {#if isTyping}
          <div class="flex justify-start">
            <div class="bg-surface-100 p-2 rounded-lg rounded-bl-sm max-w-xs" role="status" aria-live="polite" aria-label="Ali is typing">
              <div class="flex items-center space-x-1 mb-1">
                <svg class="w-3 h-3 ali-proactive" viewBox="0 0 24 24" aria-hidden="true">
                  <circle cx="12" cy="12" r="8" fill="none" stroke="#1e3a8a" stroke-width="3" stroke-linecap="round" stroke-dasharray="45 5" style="transform: rotate(-10deg);" />
                </svg>
                <span class="font-medium text-xs text-surface-900">Ali is analyzing...</span>
              </div>
              <div class="flex space-x-1" aria-hidden="true">
                <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
                <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
              </div>
            </div>
          </div>
        {/if}
      </div>

      <!-- Input -->
      <div class="p-3 border-t border-surface-200">
        <form on:submit|preventDefault={sendMessage}>
          <label for="ali-message-input" class="sr-only">Message for Ali</label>
          <div class="flex space-x-2">
            <textarea
              id="ali-message-input"
              bind:value={newMessage}
              on:keydown={handleKeyPress}
              placeholder="Ask Ali for strategic insights..."
              class="flex-1 p-2 text-xs border border-surface-300 rounded resize-none focus:ring-1 focus:ring-gray-900 focus:border-gray-900"
              rows="1"
              aria-describedby="ali-input-help"
            ></textarea>
            <button
              type="submit"
              on:click={sendMessage}
              disabled={!newMessage.trim() || isTyping}
              class="px-2 py-2 bg-gray-900 hover:bg-gray-800 disabled:bg-surface-600 text-white rounded transition-colors disabled:cursor-not-allowed"
              aria-label="Send message to Ali"
            >
              <img src="/convergio_icons/forward.svg" alt="" class="h-3 w-3 text-white" />
            </button>
          </div>
          <div id="ali-input-help" class="sr-only">Press Enter to send message, Shift+Enter for new line</div>
        </form>
      </div>
    </div>
  {/if}

  {#if isMinimized}
    <!-- Minimized State -->
    <button
      on:click={toggleOpen}
      class="bg-gray-900 hover:bg-gray-800 text-white rounded-full w-12 h-12 flex items-center justify-center shadow-lg mb-4 transition-colors"
      aria-label="Expand Ali chat - Your AI Chief of Staff"
    >
      <svg class="w-6 h-6 {isProactive ? 'ali-proactive' : 'ali-reactive'} animate-enso-glow" viewBox="0 0 24 24" aria-hidden="true">
        <defs>
          <linearGradient id="ensoGradientMin" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:#ffffff;stop-opacity:1" />
            <stop offset="50%" style="stop-color:#3b82f6;stop-opacity:0.9" />
            <stop offset="100%" style="stop-color:#e0f2fe;stop-opacity:0.8" />
          </linearGradient>
        </defs>
        <circle cx="12" cy="12" r="8" fill="none" stroke="url(#ensoGradientMin)" stroke-width="2.5" stroke-linecap="round" stroke-dasharray="45 5" style="transform: rotate(-10deg);" />
        <circle cx="12" cy="12" r="3" fill="url(#ensoGradientMin)" opacity="0.3" class="animate-breathing-inner" />
      </svg>
    </button>
  {/if}

  {#if !isOpen && !isMinimized}
    <!-- Ali Toggle Button -->
    <button
      on:click={toggleOpen}
      class="bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-full w-14 h-14 flex items-center justify-center shadow-lg hover:from-blue-700 hover:to-blue-800 transition-all transform hover:scale-105"
      aria-label="Open Ali chat - Your AI Chief of Staff"
    >
      <svg class="w-8 h-8 {isProactive ? 'ali-proactive' : 'ali-reactive'} animate-enso-glow" viewBox="0 0 24 24" aria-hidden="true">
        <defs>
          <linearGradient id="ensoGradientMain" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:#ffffff;stop-opacity:1" />
            <stop offset="30%" style="stop-color:#3b82f6;stop-opacity:0.9" />
            <stop offset="70%" style="stop-color:#60a5fa;stop-opacity:0.8" />
            <stop offset="100%" style="stop-color:#e0f2fe;stop-opacity:0.7" />
          </linearGradient>
        </defs>
        <!-- Main Enso circle -->
        <circle 
          cx="12" 
          cy="12" 
          r="9" 
          fill="none" 
          stroke="url(#ensoGradientMain)" 
          stroke-width="2.5" 
          stroke-linecap="round"
          stroke-dasharray="50 5"
          style="transform: rotate(-10deg);"
        />
        <!-- Inner breathing light -->
        <circle 
          cx="12" 
          cy="12" 
          r="4" 
          fill="url(#ensoGradientMain)" 
          opacity="0.4"
          class="animate-breathing-inner"
        />
      </svg>
    </button>
  {/if}
</div>