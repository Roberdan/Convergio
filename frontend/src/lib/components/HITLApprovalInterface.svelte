<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { writable } from 'svelte/store';
  
  export let userId: string = '';
  export let onApproval: (_approvalId: string, _decision: ApprovalDecision) => void = () => {};
  
  interface ApprovalRequest {
    id: string;
    timestamp: Date;
    agentId: string;
    agentName: string;
    action: string;
    description: string;
    context: any;
    riskLevel: 'low' | 'medium' | 'high' | 'critical';
    status: 'pending' | 'approved' | 'rejected' | 'expired';
    expiresAt: Date;
    reasoning?: string;
    alternatives?: string[];
    impact?: string;
  }
  
  interface ApprovalDecision {
    approved: boolean;
    reason?: string;
    modifiedAction?: string;
    timestamp: Date;
  }
  
  interface ApprovalStats {
    pending: number;
    approved: number;
    rejected: number;
    avgResponseTime: number;
  }
  
  let approvals = writable<ApprovalRequest[]>([]);
  let selectedApproval: ApprovalRequest | null = null;
  let stats: ApprovalStats = {
    pending: 0,
    approved: 0,
    rejected: 0,
    avgResponseTime: 0
  };
  
  let decisionReason = '';
  let modifiedAction = '';
  let filter: 'all' | 'pending' | 'completed' = 'pending';
  let searchQuery = '';
  let ws: WebSocket | null = null;
  let isConnected = false;
  let autoApproveEnabled = false;
  let autoApproveRules: Array<{pattern: string, action: 'approve' | 'reject'}> = [];
  
  const riskColors = {
    low: '#10b981',
    medium: '#f59e0b',
    high: '#ef4444',
    critical: '#991b1b'
  };
  
  function connectWebSocket() {
    const wsUrl = `ws://localhost:9000/ws/approvals?user=${userId}`;
    ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
      isConnected = true;
      loadApprovals();
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'new_approval') {
        handleNewApproval(data.approval);
      } else if (data.type === 'approval_update') {
        updateApproval(data.approval);
      }
    };
    
    ws.onclose = () => {
      isConnected = false;
      setTimeout(connectWebSocket, 5000);
    };
  }
  
  function handleNewApproval(approval: ApprovalRequest) {
    approvals.update(list => {
      const newList = [approval, ...list];
      
      // Check auto-approve rules
      if (autoApproveEnabled) {
        for (const rule of autoApproveRules) {
          if (approval.action.includes(rule.pattern)) {
            handleDecision(approval.id, rule.action === 'approve', 'Auto-approved by rule');
            return newList;
          }
        }
      }
      
      // Show notification for high-risk approvals
      if (approval.riskLevel === 'high' || approval.riskLevel === 'critical') {
        showNotification(approval);
      }
      
      return newList;
    });
    
    updateStats();
  }
  
  function updateApproval(updatedApproval: ApprovalRequest) {
    approvals.update(list => 
      list.map(a => a.id === updatedApproval.id ? updatedApproval : a)
    );
    
    if (selectedApproval?.id === updatedApproval.id) {
      selectedApproval = updatedApproval;
    }
    
    updateStats();
  }
  
  async function loadApprovals() {
    try {
      const response = await fetch(`/api/approvals?user=${userId}`);
      if (response.ok) {
        const data = await response.json();
        approvals.set(data.map((a: any) => ({
          ...a,
          timestamp: new Date(a.timestamp),
          expiresAt: new Date(a.expiresAt)
        })));
        updateStats();
      }
    } catch {
      // Silent failure
    }
  }
  
  async function handleDecision(approvalId: string, approved: boolean, reason?: string) {
    const decision: ApprovalDecision = {
      approved,
      reason: reason || decisionReason,
      modifiedAction: approved && modifiedAction ? modifiedAction : undefined,
      timestamp: new Date()
    };
    
    try {
      const response = await fetch(`/api/approvals/${approvalId}/decision`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(decision)
      });
      
      if (response.ok) {
        approvals.update(list => 
          list.map(a => a.id === approvalId 
            ? { ...a, status: approved ? 'approved' : 'rejected' }
            : a
          )
        );
        
        onApproval(approvalId, decision);
        
        // Clear form
        decisionReason = '';
        modifiedAction = '';
        selectedApproval = null;

        updateStats();
      }
    } catch {
      // Silent failure
    }
  }
  
  function updateStats() {
    approvals.subscribe(list => {
      stats.pending = list.filter(a => a.status === 'pending').length;
      stats.approved = list.filter(a => a.status === 'approved').length;
      stats.rejected = list.filter(a => a.status === 'rejected').length;
      
      // Calculate avg response time
      const completed = list.filter(a => a.status !== 'pending');
      if (completed.length > 0) {
        const totalTime = completed.reduce((sum, a) => {
          const responseTime = new Date().getTime() - a.timestamp.getTime();
          return sum + responseTime;
        }, 0);
        stats.avgResponseTime = Math.round(totalTime / completed.length / 1000 / 60);
      }
    })();
  }
  
  function showNotification(approval: ApprovalRequest) {
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification(`High Risk Action Requires Approval`, {
        body: `${approval.agentName} wants to: ${approval.action}`,
        icon: '⚠️',
        tag: approval.id
      });
    }
  }
  
  function requestNotificationPermission() {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission();
    }
  }
  
  function getFilteredApprovals(list: ApprovalRequest[]) {
    let filtered = list;
    
    if (filter === 'pending') {
      filtered = list.filter(a => a.status === 'pending');
    } else if (filter === 'completed') {
      filtered = list.filter(a => a.status !== 'pending');
    }
    
    if (searchQuery) {
      filtered = filtered.filter(a => 
        a.action.toLowerCase().includes(searchQuery.toLowerCase()) ||
        a.agentName.toLowerCase().includes(searchQuery.toLowerCase()) ||
        a.description.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }
    
    return filtered;
  }
  
  function formatTimeRemaining(expiresAt: Date): string {
    const now = new Date();
    const diff = expiresAt.getTime() - now.getTime();
    
    if (diff <= 0) return 'Expired';
    
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    
    if (hours > 0) return `${hours}h ${minutes % 60}m`;
    return `${minutes}m`;
  }
  
  onMount(() => {
    connectWebSocket();
    requestNotificationPermission();
    
    // Auto-refresh expired approvals
    const interval = setInterval(() => {
      approvals.update(list => 
        list.map(a => {
          if (a.status === 'pending' && new Date() > a.expiresAt) {
            return { ...a, status: 'expired' };
          }
          return a;
        })
      );
    }, 60000);
    
    return () => clearInterval(interval);
  });
  
  onDestroy(() => {
    if (ws) {
      ws.close();
    }
  });
</script>

<div class="hitl-interface">
  <div class="interface-header">
    <div class="header-title">
      <h2>👁️ Human-in-the-Loop Approvals</h2>
      <div class="connection-indicator" class:connected={isConnected}>
        {isConnected ? '🟢' : '🔴'} {isConnected ? 'Live' : 'Offline'}
      </div>
    </div>
    
    <div class="header-stats">
      <div class="stat">
        <span class="stat-value" style="color: #f59e0b">{stats.pending}</span>
        <span class="stat-label">Pending</span>
      </div>
      <div class="stat">
        <span class="stat-value" style="color: #10b981">{stats.approved}</span>
        <span class="stat-label">Approved</span>
      </div>
      <div class="stat">
        <span class="stat-value" style="color: #ef4444">{stats.rejected}</span>
        <span class="stat-label">Rejected</span>
      </div>
      <div class="stat">
        <span class="stat-value">{stats.avgResponseTime}m</span>
        <span class="stat-label">Avg Response</span>
      </div>
    </div>
  </div>
  
  <div class="interface-controls">
    <div class="filter-controls">
      <button
        class="filter-btn"
        class:active={filter === 'all'}
        on:click={() => filter = 'all'}
      >
        All
      </button>
      <button
        class="filter-btn"
        class:active={filter === 'pending'}
        on:click={() => filter = 'pending'}
      >
        Pending ({stats.pending})
      </button>
      <button
        class="filter-btn"
        class:active={filter === 'completed'}
        on:click={() => filter = 'completed'}
      >
        Completed
      </button>
    </div>
    
    <input
      type="search"
      bind:value={searchQuery}
      placeholder="Search approvals..."
      class="search-input"
    />
    
    <label class="auto-approve-toggle">
      <input type="checkbox" bind:checked={autoApproveEnabled} />
      <span>Auto-Approve</span>
    </label>
  </div>
  
  <div class="interface-content">
    <div class="approvals-list">
      {#each getFilteredApprovals($approvals) as approval (approval.id)}
        <div
          class="approval-card"
          class:selected={selectedApproval?.id === approval.id}
          class:expired={approval.status === 'expired'}
          role="button"
          tabindex="0"
          on:click={() => selectedApproval = approval}
          on:keydown={(e) => (e.key === 'Enter' || e.key === ' ') && (selectedApproval = approval)}
        >
          <div class="approval-header">
            <div class="approval-agent">
              <span class="agent-icon">🤖</span>
              <span class="agent-name">{approval.agentName}</span>
            </div>
            <div 
              class="risk-badge"
              style="background: {riskColors[approval.riskLevel]}"
            >
              {approval.riskLevel.toUpperCase()}
            </div>
          </div>
          
          <div class="approval-action">
            {approval.action}
          </div>
          
          <div class="approval-description">
            {approval.description}
          </div>
          
          <div class="approval-footer">
            <span class="approval-time">
              {approval.timestamp.toLocaleTimeString()}
            </span>
            {#if approval.status === 'pending'}
              <span class="time-remaining">
                ⏱️ {formatTimeRemaining(approval.expiresAt)}
              </span>
            {:else}
              <span class="approval-status {approval.status}">
                {approval.status === 'approved' ? '✅' : approval.status === 'rejected' ? '❌' : '⏰'} 
                {approval.status}
              </span>
            {/if}
          </div>
        </div>
      {/each}
      
      {#if getFilteredApprovals($approvals).length === 0}
        <div class="empty-state">
          <span class="empty-icon">📭</span>
          <p>No approvals to show</p>
        </div>
      {/if}
    </div>
    
    {#if selectedApproval}
      <div class="approval-details">
        <h3>Approval Details</h3>
        
        <div class="detail-section">
          <h4>Agent Information</h4>
          <div class="detail-row">
            <span class="detail-label">Agent:</span>
            <span class="detail-value">{selectedApproval.agentName}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Agent ID:</span>
            <span class="detail-value">{selectedApproval.agentId}</span>
          </div>
        </div>
        
        <div class="detail-section">
          <h4>Requested Action</h4>
          <div class="action-box">
            {selectedApproval.action}
          </div>
          <p class="action-description">{selectedApproval.description}</p>
        </div>
        
        {#if selectedApproval.reasoning}
          <div class="detail-section">
            <h4>Agent's Reasoning</h4>
            <p class="reasoning-text">{selectedApproval.reasoning}</p>
          </div>
        {/if}
        
        {#if selectedApproval.impact}
          <div class="detail-section">
            <h4>Potential Impact</h4>
            <p class="impact-text">{selectedApproval.impact}</p>
          </div>
        {/if}
        
        {#if selectedApproval.alternatives && selectedApproval.alternatives.length > 0}
          <div class="detail-section">
            <h4>Alternative Actions</h4>
            <ul class="alternatives-list">
              {#each selectedApproval.alternatives as alt}
                <li>{alt}</li>
              {/each}
            </ul>
          </div>
        {/if}
        
        {#if selectedApproval.context}
          <div class="detail-section">
            <h4>Context Data</h4>
            <pre class="context-data">{JSON.stringify(selectedApproval.context, null, 2)}</pre>
          </div>
        {/if}
        
        {#if selectedApproval.status === 'pending'}
          <div class="decision-section">
            <h4>Your Decision</h4>
            
            <div class="form-group">
              <label for="reason">Reason for Decision</label>
              <textarea
                id="reason"
                bind:value={decisionReason}
                placeholder="Explain your decision..."
                rows="3"
              ></textarea>
            </div>
            
            <div class="form-group">
              <label for="modified">Modified Action (Optional)</label>
              <textarea
                id="modified"
                bind:value={modifiedAction}
                placeholder="Suggest an alternative action..."
                rows="2"
              ></textarea>
            </div>
            
            <div class="decision-actions">
              <button
                class="btn btn-reject"
                on:click={() => selectedApproval && handleDecision(selectedApproval.id, false)}
              >
                ❌ Reject
              </button>
              <button
                class="btn btn-approve"
                on:click={() => selectedApproval && handleDecision(selectedApproval.id, true)}
              >
                ✅ Approve
              </button>
            </div>
          </div>
        {/if}
      </div>
    {/if}
  </div>
</div>

<style>
  .hitl-interface {
    height: 100vh;
    display: flex;
    flex-direction: column;
    background: #f9fafb;
  }
  
  .interface-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.5rem 2rem;
    background: white;
    border-bottom: 1px solid #e5e7eb;
  }
  
  .header-title {
    display: flex;
    align-items: center;
    gap: 1rem;
  }
  
  .header-title h2 {
    margin: 0;
    font-size: 1.5rem;
  }
  
  .connection-indicator {
    padding: 0.25rem 0.75rem;
    background: #fee2e2;
    border-radius: 20px;
    font-size: 0.875rem;
  }
  
  .connection-indicator.connected {
    background: #dcfce7;
  }
  
  .header-stats {
    display: flex;
    gap: 2rem;
  }
  
  .stat {
    display: flex;
    flex-direction: column;
    align-items: center;
  }
  
  .stat-value {
    font-size: 1.5rem;
    font-weight: 600;
  }
  
  .stat-label {
    font-size: 0.875rem;
    color: #6b7280;
  }
  
  .interface-controls {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1rem 2rem;
    background: white;
    border-bottom: 1px solid #e5e7eb;
  }
  
  .filter-controls {
    display: flex;
    gap: 0.5rem;
  }
  
  .filter-btn {
    padding: 0.5rem 1rem;
    background: white;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .filter-btn.active {
    background: #4f46e5;
    color: white;
    border-color: #4f46e5;
  }
  
  .search-input {
    flex: 1;
    padding: 0.5rem 1rem;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    font-size: 1rem;
  }
  
  .auto-approve-toggle {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    cursor: pointer;
  }
  
  .interface-content {
    flex: 1;
    display: flex;
    overflow: hidden;
  }
  
  .approvals-list {
    flex: 1;
    padding: 1rem;
    overflow-y: auto;
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 1rem;
    align-content: start;
  }
  
  .approval-card {
    background: white;
    border: 2px solid #e5e7eb;
    border-radius: 8px;
    padding: 1rem;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .approval-card:hover {
    border-color: #d1d5db;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  }
  
  .approval-card.selected {
    border-color: #4f46e5;
    box-shadow: 0 4px 8px rgba(79, 70, 229, 0.1);
  }
  
  .approval-card.expired {
    opacity: 0.6;
    background: #f9fafb;
  }
  
  .approval-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.75rem;
  }
  
  .approval-agent {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  
  .agent-icon {
    font-size: 1.25rem;
  }
  
  .agent-name {
    font-weight: 500;
  }
  
  .risk-badge {
    padding: 0.25rem 0.5rem;
    color: white;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
  }
  
  .approval-action {
    font-weight: 600;
    margin-bottom: 0.5rem;
  }
  
  .approval-description {
    color: #6b7280;
    font-size: 0.875rem;
    margin-bottom: 0.75rem;
    line-height: 1.4;
  }
  
  .approval-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.875rem;
    color: #9ca3af;
  }
  
  .approval-status {
    font-weight: 500;
  }
  
  .approval-status.approved {
    color: #10b981;
  }
  
  .approval-status.rejected {
    color: #ef4444;
  }
  
  .approval-status.expired {
    color: #6b7280;
  }
  
  .empty-state {
    grid-column: 1 / -1;
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
  
  .approval-details {
    width: 400px;
    background: white;
    border-left: 1px solid #e5e7eb;
    padding: 1.5rem;
    overflow-y: auto;
  }
  
  .approval-details h3 {
    margin: 0 0 1.5rem 0;
    font-size: 1.25rem;
  }
  
  .detail-section {
    margin-bottom: 1.5rem;
  }
  
  .detail-section h4 {
    margin: 0 0 0.75rem 0;
    font-size: 0.95rem;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  
  .detail-row {
    display: flex;
    justify-content: space-between;
    margin-bottom: 0.5rem;
  }
  
  .detail-label {
    color: #6b7280;
  }
  
  .detail-value {
    font-weight: 500;
  }
  
  .action-box {
    padding: 1rem;
    background: #f3f4f6;
    border-radius: 6px;
    font-weight: 500;
    margin-bottom: 0.5rem;
  }
  
  .action-description,
  .reasoning-text,
  .impact-text {
    color: #4b5563;
    line-height: 1.5;
  }
  
  .alternatives-list {
    margin: 0;
    padding-left: 1.5rem;
    color: #4b5563;
  }
  
  .alternatives-list li {
    margin-bottom: 0.5rem;
  }
  
  .context-data {
    padding: 0.75rem;
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 4px;
    font-size: 0.75rem;
    overflow-x: auto;
  }
  
  .decision-section {
    margin-top: 2rem;
    padding-top: 1.5rem;
    border-top: 2px solid #e5e7eb;
  }
  
  .form-group {
    margin-bottom: 1rem;
  }
  
  .form-group label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
    color: #4b5563;
  }
  
  .form-group textarea {
    width: 100%;
    padding: 0.5rem;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    font-size: 0.875rem;
    resize: vertical;
  }
  
  .decision-actions {
    display: flex;
    gap: 1rem;
    margin-top: 1rem;
  }
  
  .btn {
    flex: 1;
    padding: 0.75rem;
    border: none;
    border-radius: 6px;
    font-size: 1rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .btn-approve {
    background: #10b981;
    color: white;
  }
  
  .btn-approve:hover {
    background: #059669;
  }
  
  .btn-reject {
    background: #ef4444;
    color: white;
  }
  
  .btn-reject:hover {
    background: #dc2626;
  }
</style>