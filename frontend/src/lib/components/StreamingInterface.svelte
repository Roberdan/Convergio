<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { writable } from 'svelte/store';
  
  export let agentId: string = '';
  export let sessionId: string = '';
  
  interface StreamMessage {
    id: string;
    type: 'user' | 'agent' | 'system';
    content: string;
    timestamp: Date;
    metadata?: any;
  }
  
  let messages = writable<StreamMessage[]>([]);
  let inputMessage = '';
  let isStreaming = false;
  let isConnected = false;
  let ws: WebSocket | null = null;
  let streamContainer: HTMLElement;
  
  const connectWebSocket = () => {
    const wsUrl = `ws://localhost:9000/ws/stream?session=${sessionId}`;
    ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
      isConnected = true;
      addSystemMessage('Connected to streaming service');
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleStreamMessage(data);
    };
    
    ws.onerror = () => {
      // Silent failure
      addSystemMessage('Connection error occurred');
    };
    
    ws.onclose = () => {
      isConnected = false;
      addSystemMessage('Disconnected from streaming service');
    };
  };
  
  const handleStreamMessage = (data: any) => {
    if (data.type === 'message') {
      addAgentMessage(data.content, data.metadata);
    } else if (data.type === 'error') {
      addSystemMessage(`Error: ${data.message}`, 'error');
    } else if (data.type === 'complete') {
      isStreaming = false;
    }
  };
  
  const sendMessage = async () => {
    if (!inputMessage.trim() || !isConnected) return;
    
    const userMessage = inputMessage;
    inputMessage = '';
    
    addUserMessage(userMessage);
    isStreaming = true;
    
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type: 'message',
        content: userMessage,
        agentId: agentId,
        timestamp: new Date().toISOString()
      }));
    }
  };
  
  const addUserMessage = (content: string) => {
    messages.update(msgs => [...msgs, {
      id: crypto.randomUUID(),
      type: 'user',
      content,
      timestamp: new Date()
    }]);
    scrollToBottom();
  };
  
  const addAgentMessage = (content: string, metadata?: any) => {
    messages.update(msgs => {
      const lastMsg = msgs[msgs.length - 1];
      if (lastMsg && lastMsg.type === 'agent' && isStreaming) {
        // Append to existing streaming message
        return [
          ...msgs.slice(0, -1),
          { ...lastMsg, content: lastMsg.content + content }
        ];
      } else {
        // Add new message
        return [...msgs, {
          id: crypto.randomUUID(),
          type: 'agent',
          content,
          timestamp: new Date(),
          metadata
        }];
      }
    });
    scrollToBottom();
  };
  
  const addSystemMessage = (content: string, level: string = 'info') => {
    messages.update(msgs => [...msgs, {
      id: crypto.randomUUID(),
      type: 'system',
      content,
      timestamp: new Date(),
      metadata: { level }
    }]);
    scrollToBottom();
  };
  
  const scrollToBottom = () => {
    setTimeout(() => {
      if (streamContainer) {
        streamContainer.scrollTop = streamContainer.scrollHeight;
      }
    }, 50);
  };
  
  const clearMessages = () => {
    messages.set([]);
  };
  
  onMount(() => {
    connectWebSocket();
  });
  
  onDestroy(() => {
    if (ws) {
      ws.close();
    }
  });
</script>

<div class="streaming-interface">
  <div class="streaming-header">
    <h3>AI Agent Streaming</h3>
    <div class="connection-status" class:connected={isConnected}>
      {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
    </div>
  </div>
  
  <div class="messages-container" bind:this={streamContainer}>
    {#each $messages as message (message.id)}
      <div class="message {message.type}" class:streaming={isStreaming && message.type === 'agent'}>
        <div class="message-header">
          <span class="message-type">
            {#if message.type === 'user'}
              👤 You
            {:else if message.type === 'agent'}
              🤖 Agent
            {:else}
              ℹ️ System
            {/if}
          </span>
          <span class="message-time">
            {message.timestamp.toLocaleTimeString()}
          </span>
        </div>
        <div class="message-content">
          {message.content}
          {#if isStreaming && message.type === 'agent'}
            <span class="streaming-indicator">▊</span>
          {/if}
        </div>
      </div>
    {/each}
  </div>
  
  <div class="input-container">
    <input
      type="text"
      bind:value={inputMessage}
      on:keypress={(e) => e.key === 'Enter' && sendMessage()}
      placeholder="Type your message..."
      disabled={!isConnected || isStreaming}
      class="message-input"
    />
    <button
      on:click={sendMessage}
      disabled={!isConnected || isStreaming || !inputMessage.trim()}
      class="send-button"
    >
      {isStreaming ? '⏳' : '📤'} Send
    </button>
    <button
      on:click={clearMessages}
      class="clear-button"
      title="Clear messages"
    >
      🗑️
    </button>
  </div>
</div>

<style>
  .streaming-interface {
    display: flex;
    flex-direction: column;
    height: 600px;
    border: 1px solid var(--color-border, #e0e0e0);
    border-radius: 8px;
    overflow: hidden;
    background: var(--color-bg, white);
  }
  
  .streaming-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem;
    background: var(--color-primary, #4f46e5);
    color: white;
  }
  
  .streaming-header h3 {
    margin: 0;
    font-size: 1.1rem;
  }
  
  .connection-status {
    font-size: 0.9rem;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    background: rgba(255, 255, 255, 0.2);
  }
  
  .connection-status.connected {
    background: rgba(34, 197, 94, 0.2);
  }
  
  .messages-container {
    flex: 1;
    overflow-y: auto;
    padding: 1rem;
    background: var(--color-bg-secondary, #f9fafb);
  }
  
  .message {
    margin-bottom: 1rem;
    padding: 0.75rem;
    border-radius: 8px;
    animation: slideIn 0.3s ease;
  }
  
  .message.user {
    background: var(--color-user-msg, #e0e7ff);
    margin-left: 20%;
  }
  
  .message.agent {
    background: var(--color-agent-msg, #f3f4f6);
    margin-right: 20%;
  }
  
  .message.system {
    background: var(--color-system-msg, #fef3c7);
    font-size: 0.9rem;
    text-align: center;
    margin: 0.5rem auto;
    max-width: 70%;
  }
  
  .message-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 0.5rem;
    font-size: 0.85rem;
    opacity: 0.7;
  }
  
  .message-content {
    white-space: pre-wrap;
    word-wrap: break-word;
  }
  
  .streaming-indicator {
    animation: blink 1s infinite;
  }
  
  @keyframes blink {
    0%, 50% { opacity: 1; }
    51%, 100% { opacity: 0; }
  }
  
  @keyframes slideIn {
    from {
      opacity: 0;
      transform: translateY(10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
  
  .input-container {
    display: flex;
    gap: 0.5rem;
    padding: 1rem;
    background: white;
    border-top: 1px solid var(--color-border, #e0e0e0);
  }
  
  .message-input {
    flex: 1;
    padding: 0.75rem;
    border: 1px solid var(--color-border, #e0e0e0);
    border-radius: 8px;
    font-size: 1rem;
  }
  
  .message-input:focus {
    outline: none;
    border-color: var(--color-primary, #4f46e5);
  }
  
  .send-button, .clear-button {
    padding: 0.75rem 1.5rem;
    border: none;
    border-radius: 8px;
    font-size: 1rem;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .send-button {
    background: var(--color-primary, #4f46e5);
    color: white;
  }
  
  .send-button:hover:not(:disabled) {
    background: var(--color-primary-dark, #4338ca);
  }
  
  .send-button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  .clear-button {
    background: var(--color-secondary, #ef4444);
    color: white;
  }
  
  .clear-button:hover {
    background: var(--color-secondary-dark, #dc2626);
  }
</style>