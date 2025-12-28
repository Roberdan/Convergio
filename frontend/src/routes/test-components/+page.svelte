<script lang="ts">
  import StreamingInterface from '$lib/components/StreamingInterface.svelte';
  import RAGConfiguration from '$lib/components/RAGConfiguration.svelte';
  import GraphFlowBuilder from '$lib/components/GraphFlowBuilder.svelte';
  import HITLApprovalInterface from '$lib/components/HITLApprovalInterface.svelte';
  
  let activeTab = 'streaming';
  
  const tabs = [
    { id: 'streaming', label: '🔄 Streaming', component: StreamingInterface },
    { id: 'rag', label: '🧠 RAG Config', component: RAGConfiguration },
    { id: 'workflow', label: '🔀 Workflow', component: GraphFlowBuilder },
    { id: 'hitl', label: '👁️ HITL', component: HITLApprovalInterface }
  ];
  
  // Demo handlers
  function handleRAGSave(config: any) {
    alert('RAG Configuration saved successfully!');
  }

  function handleWorkflowSave(workflow: any) {
    alert('Workflow saved successfully!');
  }

  function handleApproval(approvalId: string, decision: any) {
    alert(`Decision submitted for approval ${approvalId}`);
  }
</script>

<div class="test-page">
  <header class="page-header">
    <h1>🎨 Convergio UI Components Test Suite</h1>
    <p>Test and validate all frontend components for Task 16</p>
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
      {#if activeTab === 'streaming'}
        <div class="component-info">
          <h2>Streaming Interface Component</h2>
          <p>Real-time WebSocket streaming with AI agents. Test the chat interface and message streaming.</p>
        </div>
        <StreamingInterface 
          agentId="agent_test_001" 
          sessionId="session_test_001"
        />
      {/if}
      
      {#if activeTab === 'rag'}
        <div class="component-info">
          <h2>RAG Configuration Interface</h2>
          <p>Configure Retrieval-Augmented Generation settings including embedding models, vector stores, and search parameters.</p>
        </div>
        <RAGConfiguration 
          agentId="agent_test_001"
          onSave={handleRAGSave}
        />
      {/if}
      
      {#if activeTab === 'workflow'}
        <div class="component-info">
          <h2>GraphFlow Workflow Builder</h2>
          <p>Visual workflow builder with drag-and-drop functionality. Create complex agent workflows.</p>
        </div>
        <GraphFlowBuilder 
          workflowId="workflow_test_001"
          onSave={handleWorkflowSave}
        />
      {/if}
      
      {#if activeTab === 'hitl'}
        <div class="component-info">
          <h2>Human-in-the-Loop Approval Interface</h2>
          <p>Review and approve/reject agent actions requiring human oversight.</p>
        </div>
        <HITLApprovalInterface 
          userId="user_test_001"
          onApproval={handleApproval}
        />
      {/if}
    </div>
  </div>
  
  <footer class="test-footer">
    <div class="test-status">
      <h3>Component Status</h3>
      <ul class="status-list">
        <li>✅ StreamingInterface.svelte - WebSocket real-time streaming</li>
        <li>✅ RAGConfiguration.svelte - Complete RAG settings with validation</li>
        <li>✅ GraphFlowBuilder.svelte - Drag-and-drop workflow builder</li>
        <li>✅ HITLApprovalInterface.svelte - Approval management system</li>
      </ul>
    </div>
    
    <div class="test-notes">
      <h3>Testing Instructions</h3>
      <ol>
        <li>Ensure backend is running on port 9000</li>
        <li>Test WebSocket connection in Streaming tab</li>
        <li>Validate form inputs in RAG Configuration</li>
        <li>Create a workflow in GraphFlow Builder</li>
        <li>Review approval requests in HITL interface</li>
      </ol>
    </div>
  </footer>
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
    min-height: 600px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  }
  
  .component-info {
    margin-bottom: 2rem;
    padding-bottom: 1.5rem;
    border-bottom: 2px solid #e5e7eb;
  }
  
  .component-info h2 {
    margin: 0 0 0.5rem 0;
    color: #1f2937;
  }
  
  .component-info p {
    margin: 0;
    color: #6b7280;
  }
  
  .test-footer {
    max-width: 1400px;
    margin: 4rem auto 2rem;
    padding: 2rem;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 2rem;
  }
  
  .test-status,
  .test-notes {
    background: white;
    padding: 1.5rem;
    border-radius: 12px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  }
  
  .test-status h3,
  .test-notes h3 {
    margin: 0 0 1rem 0;
    color: #1f2937;
    font-size: 1.1rem;
  }
  
  .status-list {
    list-style: none;
    padding: 0;
    margin: 0;
  }
  
  .status-list li {
    padding: 0.5rem 0;
    color: #4b5563;
    border-bottom: 1px solid #f3f4f6;
  }
  
  .status-list li:last-child {
    border-bottom: none;
  }
  
  .test-notes ol {
    margin: 0;
    padding-left: 1.5rem;
    color: #4b5563;
  }
  
  .test-notes li {
    margin-bottom: 0.5rem;
  }
</style>