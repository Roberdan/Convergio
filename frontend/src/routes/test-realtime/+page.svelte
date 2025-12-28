<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import ToastNotifications from '$lib/components/ToastNotifications.svelte';
  import RealTimeMetricsDashboard from '$lib/components/RealTimeMetricsDashboard.svelte';
  import ActivityTimeline from '$lib/components/ActivityTimeline.svelte';
  import { notify, requestNotificationPermission } from '$lib/stores/notifications';
  import { createConnection, disconnectAll } from '$lib/services/websocket-manager';
  import { MessageQueue, Priority, getGlobalQueue } from '$lib/services/message-queue';
  
  let activeTab = 'notifications';
  let connections: any[] = [];
  let connectionStats = {
    total: 0,
    connected: 0,
    disconnected: 0,
    errors: 0
  };
  
  let messageQueue: MessageQueue;
  let queueStats: any = {};
  
  const tabs = [
    { id: 'notifications', label: '🔔 Notifications' },
    { id: 'metrics', label: '📊 Metrics Dashboard' },
    { id: 'timeline', label: '📋 Activity Timeline' },
    { id: 'connections', label: '🔌 Connection Test' },
    { id: 'queue', label: '📬 Message Queue' }
  ];
  
  // Test notification functions
  function testSuccessNotification() {
    notify.success('Success!', 'Operation completed successfully', {
      duration: 5000,
      actions: [
        {
          label: 'View Details',
          action: () => {},
          style: 'primary'
        }
      ]
    });
  }
  
  function testErrorNotification() {
    notify.error('Error Occurred', 'Failed to process request. Please try again.', {
      persistent: true,
      actions: [
        {
          label: 'Retry',
          action: () => {},
          style: 'primary'
        },
        {
          label: 'Dismiss',
          action: () => {},
          style: 'secondary'
        }
      ]
    });
  }
  
  function testWarningNotification() {
    notify.warning('Warning', 'This action may have consequences', {
      duration: 7000
    });
  }
  
  function testInfoNotification() {
    notify.info('Information', 'New updates are available', {
      duration: 4000
    });
  }
  
  function testProgressNotification() {
    const id = notify.loading('Processing', 'Please wait...');
    let progress = 0;
    
    const interval = setInterval(() => {
      progress += 10;
      notify.progress(id, progress, `Processing... ${progress}%`);
      
      if (progress >= 100) {
        clearInterval(interval);
        setTimeout(() => {
          notify.success('Complete!', 'Processing finished successfully');
        }, 500);
      }
    }, 500);
  }
  
  // WebSocket connection testing
  function createTestConnection(index: number) {
    const wsManager = createConnection(`test-${index}`, {
      url: `ws://localhost:9000/ws/test-${index}`,
      reconnect: true,
      reconnectInterval: 3000,
      maxReconnectAttempts: 5,
      heartbeatInterval: 10000,
      debug: true
    });
    
    wsManager.state.subscribe(state => {
      updateConnectionStats();
    });
    
    wsManager.on('message', (data) => {
      // Message received
    });
    
    wsManager.connect().catch(() => {
      // Silent failure
    });
    
    return wsManager;
  }
  
  function testMultipleConnections() {
    disconnectAll();
    connections = [];
    
    for (let i = 0; i < 5; i++) {
      const conn = createTestConnection(i);
      connections.push({
        id: i,
        manager: conn,
        status: 'connecting'
      });
    }
    
    updateConnectionStats();
  }
  
  function updateConnectionStats() {
    connectionStats = {
      total: connections.length,
      connected: connections.filter(c => c.manager.isConnected()).length,
      disconnected: connections.filter(c => !c.manager.isConnected()).length,
      errors: connections.filter(c => c.manager.getState().status === 'error').length
    };
  }
  
  function disconnectAllConnections() {
    disconnectAll();
    connections = [];
    updateConnectionStats();
  }
  
  // Message queue testing
  function setupMessageQueue() {
    messageQueue = getGlobalQueue();
    
    // Set up processor
    messageQueue.setProcessor(async (message) => {
      // Simulate processing delay
      await new Promise(resolve => setTimeout(resolve, Math.random() * 2000));
      
      // Randomly fail some messages for testing
      if (Math.random() > 0.8) {
        throw new Error('Random processing error');
      }
      
      return { processed: true, data: message };
    });
    
    // Subscribe to stats
    messageQueue.statsStore.subscribe(stats => {
      queueStats = stats;
    });
  }
  
  function addTestMessage(priority: number = 0) {
    const messageId = messageQueue.enqueue(
      {
        type: 'test',
        content: `Test message ${Date.now()}`,
        timestamp: new Date()
      },
      {
        priority,
        callback: (result) => {
          notify.success('Message Processed', `Message completed: ${result.data.content}`);
        },
        errorCallback: (error) => {
          notify.error('Processing Failed', error.message);
        }
      }
    );
    
    notify.info('Message Queued', `Added message with ID: ${messageId.slice(0, 8)}...`);
  }
  
  function addBulkMessages() {
    for (let i = 0; i < 10; i++) {
      const priority = Math.floor(Math.random() * 3) - 1; // -1 to 1
      addTestMessage(priority);
    }
  }
  
  onMount(async () => {
    // Request notification permission
    const granted = await requestNotificationPermission();
    if (granted) {
      notify.info('Notifications Enabled', 'Desktop notifications are now enabled');
    }
    
    // Setup message queue
    setupMessageQueue();
  });
  
  onDestroy(() => {
    disconnectAllConnections();
  });
</script>

<div class="test-page">
  <ToastNotifications />
  
  <header class="page-header">
    <h1>🚀 Real-time Features Test Suite</h1>
    <p>Test WebSocket connections, notifications, metrics, and message queuing</p>
  </header>
  
  <div class="tabs-container">
    <div class="tabs">
      {#each tabs as tab}
        <button
          class="tab"
          class:active={activeTab === tab.id}
          on:click={() => activeTab = tab.id}
        >
          {tab.label}
        </button>
      {/each}
    </div>
    
    <div class="tab-content">
      {#if activeTab === 'notifications'}
        <div class="section">
          <h2>Toast Notification System</h2>
          <p>Test different types of notifications with various configurations</p>
          
          <div class="button-grid">
            <button class="test-btn success" on:click={testSuccessNotification}>
              ✅ Success Notification
            </button>
            <button class="test-btn error" on:click={testErrorNotification}>
              ❌ Error Notification
            </button>
            <button class="test-btn warning" on:click={testWarningNotification}>
              ⚠️ Warning Notification
            </button>
            <button class="test-btn info" on:click={testInfoNotification}>
              ℹ️ Info Notification
            </button>
            <button class="test-btn progress" on:click={testProgressNotification}>
              📊 Progress Notification
            </button>
          </div>
        </div>
      {/if}
      
      {#if activeTab === 'metrics'}
        <div class="section">
          <h2>Real-time Metrics Dashboard</h2>
          <RealTimeMetricsDashboard 
            refreshInterval={5000}
            wsEndpoint="ws://localhost:9000/ws/metrics"
          />
        </div>
      {/if}
      
      {#if activeTab === 'timeline'}
        <div class="section">
          <h2>Activity Monitoring Timeline</h2>
          <div style="height: 600px;">
            <ActivityTimeline 
              maxEvents={100}
              wsEndpoint="ws://localhost:9000/ws/activity"
              autoScroll={true}
            />
          </div>
        </div>
      {/if}
      
      {#if activeTab === 'connections'}
        <div class="section">
          <h2>WebSocket Connection Manager Test</h2>
          <p>Test multiple concurrent WebSocket connections with retry logic</p>
          
          <div class="connection-stats">
            <div class="stat-card">
              <span class="stat-label">Total Connections</span>
              <span class="stat-value">{connectionStats.total}</span>
            </div>
            <div class="stat-card">
              <span class="stat-label">Connected</span>
              <span class="stat-value success">{connectionStats.connected}</span>
            </div>
            <div class="stat-card">
              <span class="stat-label">Disconnected</span>
              <span class="stat-value warning">{connectionStats.disconnected}</span>
            </div>
            <div class="stat-card">
              <span class="stat-label">Errors</span>
              <span class="stat-value error">{connectionStats.errors}</span>
            </div>
          </div>
          
          <div class="button-group">
            <button class="test-btn primary" on:click={testMultipleConnections}>
              🔌 Create 5 Connections
            </button>
            <button class="test-btn danger" on:click={disconnectAllConnections}>
              ❌ Disconnect All
            </button>
          </div>
          
          {#if connections.length > 0}
            <div class="connections-list">
              <h3>Active Connections</h3>
              {#each connections as conn}
                <div class="connection-item">
                  <span class="conn-id">Connection #{conn.id}</span>
                  <span class="conn-status {conn.manager.getState().status}">
                    {conn.manager.getState().status}
                  </span>
                  <span class="conn-attempts">
                    Reconnect attempts: {conn.manager.getState().reconnectAttempts}
                  </span>
                </div>
              {/each}
            </div>
          {/if}
        </div>
      {/if}
      
      {#if activeTab === 'queue'}
        <div class="section">
          <h2>Message Queue System</h2>
          <p>Reliable message processing with retry logic and persistence</p>
          
          <div class="queue-stats">
            <div class="stat-card">
              <span class="stat-label">Total Messages</span>
              <span class="stat-value">{queueStats.totalMessages || 0}</span>
            </div>
            <div class="stat-card">
              <span class="stat-label">Pending</span>
              <span class="stat-value warning">{queueStats.pendingMessages || 0}</span>
            </div>
            <div class="stat-card">
              <span class="stat-label">Processing</span>
              <span class="stat-value info">{queueStats.processingMessages || 0}</span>
            </div>
            <div class="stat-card">
              <span class="stat-label">Completed</span>
              <span class="stat-value success">{queueStats.completedMessages || 0}</span>
            </div>
            <div class="stat-card">
              <span class="stat-label">Failed</span>
              <span class="stat-value error">{queueStats.failedMessages || 0}</span>
            </div>
            <div class="stat-card">
              <span class="stat-label">Success Rate</span>
              <span class="stat-value">{(queueStats.successRate || 0).toFixed(1)}%</span>
            </div>
          </div>
          
          <div class="button-group">
            <button class="test-btn" on:click={() => addTestMessage(Priority.LOW)}>
              ➕ Add Low Priority
            </button>
            <button class="test-btn" on:click={() => addTestMessage(Priority.NORMAL)}>
              ➕ Add Normal Priority
            </button>
            <button class="test-btn" on:click={() => addTestMessage(Priority.HIGH)}>
              ➕ Add High Priority
            </button>
            <button class="test-btn primary" on:click={addBulkMessages}>
              📦 Add 10 Messages
            </button>
            <button class="test-btn" on:click={() => messageQueue.retryAllFailed()}>
              🔄 Retry Failed
            </button>
            <button class="test-btn danger" on:click={() => messageQueue.clearQueue()}>
              🗑️ Clear Queue
            </button>
            {#if messageQueue?.isPaused()}
              <button class="test-btn success" on:click={() => messageQueue.resume()}>
                ▶️ Resume Processing
              </button>
            {:else}
              <button class="test-btn warning" on:click={() => messageQueue.pause()}>
                ⏸️ Pause Processing
              </button>
            {/if}
          </div>
        </div>
      {/if}
    </div>
  </div>
</div>

<style>
  .test-page {
    min-height: 100vh;
    background: #f9fafb;
  }
  
  .page-header {
    padding: 2rem;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    text-align: center;
  }
  
  .page-header h1 {
    margin: 0 0 0.5rem 0;
    font-size: 2rem;
  }
  
  .page-header p {
    margin: 0;
    opacity: 0.9;
  }
  
  .tabs-container {
    max-width: 1400px;
    margin: 2rem auto;
    padding: 0 2rem;
  }
  
  .tabs {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 2rem;
    background: white;
    padding: 0.5rem;
    border-radius: 12px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  }
  
  .tab {
    flex: 1;
    padding: 0.75rem 1.5rem;
    background: transparent;
    border: none;
    border-radius: 8px;
    font-size: 1rem;
    font-weight: 500;
    color: #6b7280;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .tab:hover {
    background: #f3f4f6;
  }
  
  .tab.active {
    background: #4f46e5;
    color: white;
  }
  
  .tab-content {
    background: white;
    border-radius: 12px;
    padding: 2rem;
    min-height: 400px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  }
  
  .section {
    animation: fadeIn 0.3s ease;
  }
  
  @keyframes fadeIn {
    from {
      opacity: 0;
      transform: translateY(10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
  
  .section h2 {
    margin: 0 0 1rem 0;
    color: #1f2937;
  }
  
  .section p {
    color: #6b7280;
    margin-bottom: 1.5rem;
  }
  
  .button-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
  }
  
  .button-group {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-top: 1rem;
  }
  
  .test-btn {
    padding: 0.75rem 1.5rem;
    border: none;
    border-radius: 8px;
    font-size: 1rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
    background: #f3f4f6;
    color: #1f2937;
  }
  
  .test-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  }
  
  .test-btn.success {
    background: #10b981;
    color: white;
  }
  
  .test-btn.error,
  .test-btn.danger {
    background: #ef4444;
    color: white;
  }
  
  .test-btn.warning {
    background: #f59e0b;
    color: white;
  }
  
  .test-btn.info {
    background: #3b82f6;
    color: white;
  }
  
  .test-btn.progress {
    background: #8b5cf6;
    color: white;
  }
  
  .test-btn.primary {
    background: #4f46e5;
    color: white;
  }
  
  .connection-stats,
  .queue-stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 1rem;
    margin-bottom: 2rem;
  }
  
  .stat-card {
    padding: 1rem;
    background: #f9fafb;
    border-radius: 8px;
    text-align: center;
  }
  
  .stat-label {
    display: block;
    font-size: 0.875rem;
    color: #6b7280;
    margin-bottom: 0.5rem;
  }
  
  .stat-value {
    display: block;
    font-size: 1.5rem;
    font-weight: 600;
    color: #1f2937;
  }
  
  .stat-value.success {
    color: #10b981;
  }
  
  .stat-value.warning {
    color: #f59e0b;
  }
  
  .stat-value.error {
    color: #ef4444;
  }
  
  .stat-value.info {
    color: #3b82f6;
  }
  
  .connections-list {
    margin-top: 2rem;
  }
  
  .connections-list h3 {
    margin: 0 0 1rem 0;
    color: #374151;
  }
  
  .connection-item {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 0.75rem;
    background: #f9fafb;
    border-radius: 6px;
    margin-bottom: 0.5rem;
  }
  
  .conn-id {
    font-weight: 500;
  }
  
  .conn-status {
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.875rem;
    font-weight: 500;
  }
  
  .conn-status.connected {
    background: #dcfce7;
    color: #166534;
  }
  
  .conn-status.connecting {
    background: #fef3c7;
    color: #92400e;
  }
  
  .conn-status.disconnected {
    background: #fee2e2;
    color: #991b1b;
  }
  
  .conn-status.error {
    background: #fee2e2;
    color: #991b1b;
  }
  
  .conn-attempts {
    margin-left: auto;
    font-size: 0.875rem;
    color: #6b7280;
  }
</style>