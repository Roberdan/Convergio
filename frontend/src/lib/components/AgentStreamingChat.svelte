<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { writable } from 'svelte/store';
  import AgentHealthIndicator from './AgentHealthIndicator.svelte';
  
  export let agentName: string = 'ali_chief_of_staff';
  export const endpoint: string = '/api/v1/agents/ali/intelligence';
  
  // Connection states
  type ConnectionState = 'disconnected' | 'connecting' | 'connected' | 'error';
  
  // Message types
  interface Message {
    id: string;
    type: 'user' | 'agent' | 'error' | 'system';
    content: string;
    timestamp: Date;
    isStreaming?: boolean;
    tools?: string[];
  }
  
  // Component state
  let messages = writable<Message[]>([]);
  let connectionState = writable<ConnectionState>('disconnected');
  let isTyping = false;
  let newMessage = '';
  let messagesContainer: HTMLElement;
  let ws: WebSocket | null = null;
  let reconnectTimer: NodeJS.Timeout;
  let reconnectAttempts = 0;
  const MAX_RECONNECT_ATTEMPTS = 5;
  const RECONNECT_DELAY = 2000;
  
  // Streaming state
  let currentStreamingMessage: Message | null = null;
  let streamBuffer = '';
  
  // Auto-scroll
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
  
  // WebSocket connection with exponential backoff
  function connectWebSocket() {
    if (ws?.readyState === WebSocket.OPEN) return;
    
    connectionState.set('connecting');
    
    // Generate conversation ID
    const conversationId = `conv_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const userId = 'user_' + Math.random().toString(36).substr(2, 9);
    
    try {
      // Use the correct agent conversation WebSocket endpoint
      const wsUrl = `ws://localhost:9000/api/v1/agents/ws/conversation/${conversationId}?user_id=${userId}`;
      ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        connectionState.set('connected');
        reconnectAttempts = 0;
        
        // Send initial handshake
        ws?.send(JSON.stringify({
          type: 'handshake',
          agent: agentName,
          client: 'web'
        }));
      };
      
      ws.onmessage = (event) => {
        handleWebSocketMessage(event.data);
      };
      
      ws.onerror = () => {
        // Silent failure
        connectionState.set('error');
      };
      
      ws.onclose = () => {
        connectionState.set('disconnected');
        
        // Attempt reconnection with exponential backoff
        if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
          const delay = RECONNECT_DELAY * Math.pow(2, reconnectAttempts);
          reconnectTimer = setTimeout(() => {
            reconnectAttempts++;
            connectWebSocket();
          }, delay);
        }
      };
    } catch {
      // Silent failure
      connectionState.set('error');
    }
  }
  
  // Handle incoming WebSocket messages
  function handleWebSocketMessage(data: string) {
    try {
      const message = JSON.parse(data);
      
      switch (message.type) {
        case 'system':
          // System message (like connection confirmation)
          break;
          
        case 'typing':
          // Agent is typing
          isTyping = true;
          break;
          
        case 'response':
          // Full response from agent
          isTyping = false;
          messages.update(msgs => [...msgs, {
            id: Date.now().toString(),
            type: 'agent',
            content: message.message || '',
            timestamp: new Date(message.timestamp || Date.now()),
            tools: message.agents_used || []
          }]);
          scrollToBottom();
          break;
          
        case 'stream_start':
          // Start streaming a new message
          currentStreamingMessage = {
            id: message.id || Date.now().toString(),
            type: 'agent',
            content: '',
            timestamp: new Date(),
            isStreaming: true,
            tools: message.tools
          };
          messages.update(msgs => [...msgs, currentStreamingMessage!]);
          break;
          
        case 'stream_chunk':
          // Append to current streaming message
          if (currentStreamingMessage) {
            streamBuffer += message.content;
            currentStreamingMessage.content = streamBuffer;
            messages.update(msgs => msgs);
            scrollToBottom();
          }
          break;
          
        case 'stream_end':
          // Finalize streaming message
          if (currentStreamingMessage) {
            currentStreamingMessage.isStreaming = false;
            currentStreamingMessage = null;
            streamBuffer = '';
            messages.update(msgs => msgs);
          }
          isTyping = false;
          break;
          
        case 'tool_call':
          // Show tool execution
          messages.update(msgs => [...msgs, {
            id: Date.now().toString(),
            type: 'system',
            content: `🔧 Executing tool: ${message.tool_name}`,
            timestamp: new Date()
          }]);
          break;
          
        case 'error':
          // Show error message
          messages.update(msgs => [...msgs, {
            id: Date.now().toString(),
            type: 'error',
            content: message.error || 'An error occurred',
            timestamp: new Date()
          }]);
          isTyping = false;
          break;
      }
    } catch {
      // Silent failure
    }
  }
  
  // Send message (WebSocket or fallback to HTTP)
  async function sendMessage() {
    if (!newMessage.trim()) return;
    
    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: newMessage.trim(),
      timestamp: new Date()
    };
    
    messages.update(msgs => [...msgs, userMessage]);
    const currentMessage = newMessage.trim();
    newMessage = '';
    isTyping = true;
    
    // Try WebSocket first
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        message: currentMessage,  // Backend expects 'message' directly
        context: {
          agent_id: agentName,
          source: 'agent_chat'
        }
      }));
    } else {
      // Fallback to HTTP
      await sendHttpMessage(currentMessage);
    }
  }
  
  // HTTP fallback
  async function sendHttpMessage(message: string) {
    try {
      // Use the conversation endpoint instead
      const response = await fetch(`http://localhost:9000/api/v1/agents/conversation`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message,
          user_id: 'user_' + Math.random().toString(36).substr(2, 9),
          conversation_id: 'conv_' + Date.now(),
          mode: 'single',  // or 'multi' for multiple agents
          context: {
            source: 'agent_chat',
            agent_id: agentName
          }
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        messages.update(msgs => [...msgs, {
          id: Date.now().toString(),
          type: 'agent',
          content: result.response,
          timestamp: new Date(),
          tools: result.tools_used
        }]);
      } else {
        throw new Error(`HTTP ${response.status}`);
      }
    } catch (error) {
      messages.update(msgs => [...msgs, {
        id: Date.now().toString(),
        type: 'error',
        content: `Failed to send message: ${error}`,
        timestamp: new Date()
      }]);
    } finally {
      isTyping = false;
    }
  }
  
  // Cancel current streaming
  function cancelStreaming() {
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type: 'cancel_stream'
      }));
    }
    
    if (currentStreamingMessage) {
      currentStreamingMessage.isStreaming = false;
      currentStreamingMessage.content += ' [Cancelled]';
      currentStreamingMessage = null;
      streamBuffer = '';
      messages.update(msgs => msgs);
    }
    
    isTyping = false;
  }
  
  // Lifecycle
  onMount(() => {
    connectWebSocket();
  });
  
  onDestroy(() => {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer);
    }
    if (ws) {
      ws.close();
    }
  });
  
  // Reactive updates
  $: if ($messages.length > 0) {
    scrollToBottom();
  }
</script>

<div class="agent-chat-container">
  <!-- Header with health indicator -->
  <div class="chat-header">
    <h3 class="text-lg font-semibold">{agentName}</h3>
    <div class="flex items-center gap-4">
      <AgentHealthIndicator {agentName} showDetails={false} />
      
      <!-- Connection status -->
      <div class="connection-status">
        {#if $connectionState === 'connected'}
          <span class="text-green-500">● Connected</span>
        {:else if $connectionState === 'connecting'}
          <span class="text-yellow-500">● Connecting...</span>
        {:else if $connectionState === 'error'}
          <span class="text-red-500">● Error</span>
        {:else}
          <span class="text-surface-500">● Disconnected</span>
        {/if}
      </div>
    </div>
  </div>
  
  <!-- Messages container -->
  <div class="messages-container" bind:this={messagesContainer}>
    {#each $messages as message (message.id)}
      <div class="message {message.type}">
        {#if message.type === 'user'}
          <div class="user-message">
            {message.content}
          </div>
        {:else if message.type === 'agent'}
          <div class="agent-message">
            {#if message.isStreaming}
              <span class="streaming-indicator">●●●</span>
            {/if}
            {message.content}
            {#if message.tools && message.tools.length > 0}
              <div class="tools-used">
                Tools: {message.tools.join(', ')}
              </div>
            {/if}
          </div>
        {:else if message.type === 'error'}
          <div class="error-message">
            ⚠️ {message.content}
          </div>
        {:else if message.type === 'system'}
          <div class="system-message">
            {message.content}
          </div>
        {/if}
        <div class="timestamp">
          {message.timestamp.toLocaleTimeString()}
        </div>
      </div>
    {/each}
    
    {#if isTyping && !currentStreamingMessage}
      <div class="typing-indicator">
        <span>●</span>
        <span>●</span>
        <span>●</span>
      </div>
    {/if}
  </div>
  
  <!-- Input area -->
  <div class="chat-input">
    <input
      type="text"
      bind:value={newMessage}
      on:keydown={(e) => e.key === 'Enter' && sendMessage()}
      placeholder="Type your message..."
      disabled={isTyping || $connectionState === 'error'}
      class="input-field"
    />
    
    {#if isTyping && currentStreamingMessage}
      <button on:click={cancelStreaming} class="cancel-button">
        Cancel
      </button>
    {:else}
      <button 
        on:click={sendMessage} 
        disabled={!newMessage.trim() || isTyping}
        class="send-button"
      >
        Send
      </button>
    {/if}
  </div>
</div>

<style>
  .agent-chat-container {
    @apply flex flex-col h-full bg-white rounded-lg shadow-lg;
  }
  
  .chat-header {
    @apply flex justify-between items-center p-4 border-b;
  }
  
  .messages-container {
    @apply flex-1 overflow-y-auto p-4 space-y-4;
    max-height: 500px;
  }
  
  .message {
    @apply flex flex-col;
  }
  
  .user-message {
    @apply self-end bg-blue-500 text-white rounded-lg px-4 py-2 max-w-xs;
  }
  
  .agent-message {
    @apply self-start bg-surface-100 rounded-lg px-4 py-2 max-w-md;
  }
  
  .error-message {
    @apply self-center bg-red-100 text-red-700 rounded-lg px-4 py-2;
  }
  
  .system-message {
    @apply self-center text-surface-500 text-sm italic;
  }
  
  .timestamp {
    @apply text-xs text-gray-400 mt-1;
  }
  
  .tools-used {
    @apply text-xs text-surface-500 mt-2 pt-2 border-t;
  }
  
  .chat-input {
    @apply flex gap-2 p-4 border-t;
  }
  
  .input-field {
    @apply flex-1 px-4 py-2 rounded-lg border;
  }
  
  .send-button {
    @apply px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50;
  }
  
  .cancel-button {
    @apply px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600;
  }
  
  .typing-indicator {
    @apply flex gap-1 self-start px-4 py-2;
  }
  
  .typing-indicator span {
    @apply inline-block w-2 h-2 bg-gray-400 rounded-full;
    animation: typing 1.4s infinite;
  }
  
  .typing-indicator span:nth-child(2) {
    animation-delay: 0.2s;
  }
  
  .typing-indicator span:nth-child(3) {
    animation-delay: 0.4s;
  }
  
  .streaming-indicator {
    @apply inline-block text-blue-500;
    animation: pulse 1s infinite;
  }
  
  @keyframes typing {
    0%, 60%, 100% {
      transform: translateY(0);
    }
    30% {
      transform: translateY(-10px);
    }
  }
  
  @keyframes pulse {
    0%, 100% {
      opacity: 1;
    }
    50% {
      opacity: 0.5;
    }
  }
</style>