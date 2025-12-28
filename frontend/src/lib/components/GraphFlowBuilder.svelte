<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  
  export let workflowId: string = '';
  // eslint-disable-next-line no-unused-vars
  export let onSave: (_w: Workflow) => void = () => {};
  
  interface Node {
    id: string;
    type: 'agent' | 'condition' | 'action' | 'input' | 'output';
    label: string;
    position: { x: number; y: number };
    data: any;
    inputs?: string[];
    outputs?: string[];
  }
  
  interface Edge {
    id: string;
    source: string;
    target: string;
    label?: string;
    condition?: string;
  }
  
  interface Workflow {
    id: string;
    name: string;
    description: string;
    nodes: Node[];
    edges: Edge[];
    metadata: any;
  }
  
  let workflow: Workflow = {
    id: workflowId || crypto.randomUUID(),
    name: 'New Workflow',
    description: '',
    nodes: [],
    edges: [],
    metadata: {}
  };
  
  let canvas: SVGSVGElement;
  let selectedNode: Node | null = null;
  let selectedEdge: Edge | null = null;
  let isDragging = false;
  let isConnecting = false;
  let dragOffset = { x: 0, y: 0 };
  let connectionStart: { nodeId: string; type: 'input' | 'output' } | null = null;
  let tempConnection = { x1: 0, y1: 0, x2: 0, y2: 0 };
  let zoom = 1;
  let pan = { x: 0, y: 0 };
  let showProperties = false;
  let showNodeLibrary = true;
  
  function handleKeyDown(e: KeyboardEvent) {
    if ((e.key === 'Delete' || e.key === 'Backspace') && selectedEdge) {
      deleteEdge(selectedEdge.id);
      e.preventDefault();
    }
  }
  
  const nodeTemplates = [
    { type: 'agent', label: 'AI Agent', icon: '🤖', color: '#4f46e5' },
    { type: 'condition', label: 'Condition', icon: '🔀', color: '#10b981' },
    { type: 'action', label: 'Action', icon: '⚡', color: '#f59e0b' },
    { type: 'input', label: 'Input', icon: '📥', color: '#8b5cf6' },
    { type: 'output', label: 'Output', icon: '📤', color: '#ef4444' }
  ];
  
  const availableAgents = [
    'Ali - Chief of Staff',
    'Amy - CFO',
    'Baccio - Tech Architect',
    'Sofia - Marketing',
    'Luca - Security',
    'Sam - Startup Expert'
  ];
  
  function addNode(type: string, label: string) {
    const newNode: Node = {
      id: `node_${Date.now()}`,
      type: type as Node['type'],
      label: label,
      position: { x: 100 + workflow.nodes.length * 50, y: 100 + workflow.nodes.length * 30 },
      data: {},
      inputs: type === 'output' ? ['in'] : type === 'input' ? [] : ['in'],
      outputs: type === 'input' ? ['out'] : type === 'output' ? [] : ['out']
    };
    
    workflow.nodes = [...workflow.nodes, newNode];
    selectedNode = newNode;
    showProperties = true;
  }
  
  function deleteNode(nodeId: string) {
    workflow.nodes = workflow.nodes.filter(n => n.id !== nodeId);
    workflow.edges = workflow.edges.filter(e => e.source !== nodeId && e.target !== nodeId);
    selectedNode = null;
  }
  
  function deleteEdge(edgeId: string) {
    workflow.edges = workflow.edges.filter(e => e.id !== edgeId);
    selectedEdge = null;
  }
  
  function startDragging(node: Node, event: MouseEvent) {
    isDragging = true;
    selectedNode = node;
    dragOffset = {
      x: event.clientX - node.position.x,
      y: event.clientY - node.position.y
    };
    event.preventDefault();
  }
  
  function handleMouseMove(event: MouseEvent) {
    if (isDragging && selectedNode) {
      selectedNode.position.x = event.clientX - dragOffset.x;
      selectedNode.position.y = event.clientY - dragOffset.y;
      workflow.nodes = [...workflow.nodes];
    }
    
    if (isConnecting) {
      const rect = canvas.getBoundingClientRect();
      tempConnection.x2 = (event.clientX - rect.left) / zoom - pan.x;
      tempConnection.y2 = (event.clientY - rect.top) / zoom - pan.y;
    }
  }
  
  function handleMouseUp() {
    isDragging = false;
    isConnecting = false;
    connectionStart = null;
  }
  
  function startConnection(nodeId: string, type: 'input' | 'output', event: MouseEvent) {
    isConnecting = true;
    connectionStart = { nodeId, type };
    const node = workflow.nodes.find(n => n.id === nodeId);
    if (node) {
      const rect = canvas.getBoundingClientRect();
      tempConnection.x1 = node.position.x + (type === 'output' ? 180 : 20);
      tempConnection.y1 = node.position.y + 30;
      tempConnection.x2 = (event.clientX - rect.left) / zoom - pan.x;
      tempConnection.y2 = (event.clientY - rect.top) / zoom - pan.y;
    }
    event.stopPropagation();
  }
  
  function endConnection(nodeId: string, type: 'input' | 'output') {
    if (isConnecting && connectionStart) {
      if (connectionStart.nodeId !== nodeId && connectionStart.type !== type) {
        const newEdge: Edge = {
          id: `edge_${Date.now()}`,
          source: connectionStart.type === 'output' ? connectionStart.nodeId : nodeId,
          target: connectionStart.type === 'input' ? connectionStart.nodeId : nodeId,
          label: ''
        };
        workflow.edges = [...workflow.edges, newEdge];
      }
    }
    isConnecting = false;
    connectionStart = null;
  }
  
  function handleZoom(delta: number) {
    zoom = Math.max(0.5, Math.min(2, zoom + delta));
  }
  
  function validateWorkflow(): boolean {
    // Check for disconnected nodes
    const connectedNodes = new Set<string>();
    workflow.edges.forEach(edge => {
      connectedNodes.add(edge.source);
      connectedNodes.add(edge.target);
    });
    
    const disconnected = workflow.nodes.filter(n => !connectedNodes.has(n.id));
    if (disconnected.length > 0 && workflow.nodes.length > 1) {
      alert('Warning: Some nodes are not connected');
      return false;
    }
    
    // Check for cycles (simplified)
    // In production, implement proper cycle detection
    
    return true;
  }
  
  async function saveWorkflow() {
    if (!validateWorkflow()) return;
    
    try {
      const response = await fetch(`/api/workflows/${workflow.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(workflow)
      });
      
      if (response.ok) {
        onSave(workflow);
      }
    } catch {
      // Silent failure
    }
  }
  
  async function loadWorkflow() {
    if (!workflowId) return;
    
    try {
      const response = await fetch(`/api/workflows/${workflowId}`);
      if (response.ok) {
        workflow = await response.json();
      }
    } catch {
      // Silent failure
    }
  }
  
  function exportWorkflow() {
    const dataStr = JSON.stringify(workflow, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileDefaultName = `${workflow.name.replace(/\s+/g, '_')}_workflow.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  }
  
  onMount(() => {
    loadWorkflow();
    
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
  window.addEventListener('keydown', handleKeyDown);
  });
  
  onDestroy(() => {
    window.removeEventListener('mousemove', handleMouseMove);
    window.removeEventListener('mouseup', handleMouseUp);
  window.removeEventListener('keydown', handleKeyDown);
  });
</script>

<div class="graphflow-builder">
  <div class="builder-header">
    <div class="header-left">
      <h2>🔄 GraphFlow Workflow Builder</h2>
      <input
        type="text"
        bind:value={workflow.name}
        class="workflow-name"
        placeholder="Workflow Name"
      />
    </div>
    <div class="header-actions">
      <button class="btn btn-icon" on:click={() => showNodeLibrary = !showNodeLibrary} title="Toggle Library">
        📚
      </button>
      <button class="btn btn-icon" on:click={() => handleZoom(0.1)} title="Zoom In">
        🔍+
      </button>
      <button class="btn btn-icon" on:click={() => handleZoom(-0.1)} title="Zoom Out">
        🔍-
      </button>
      <button class="btn btn-secondary" on:click={exportWorkflow}>
        Export
      </button>
      <button class="btn btn-primary" on:click={saveWorkflow}>
        Save Workflow
      </button>
    </div>
  </div>
  
  <div class="builder-container">
    {#if showNodeLibrary}
      <div class="node-library">
        <h3>Node Library</h3>
        
        <div class="node-templates">
          {#each nodeTemplates as template}
            <button
              class="node-template"
              style="border-color: {template.color}"
              on:click={() => addNode(template.type, template.label)}
            >
              <span class="icon">{template.icon}</span>
              <span class="label">{template.label}</span>
            </button>
          {/each}
        </div>
        
        <div class="agent-list">
          <h4>Available Agents</h4>
          {#each availableAgents as agent}
            <button
              class="agent-item"
              on:click={() => {
                addNode('agent', agent);
              }}
            >
              🤖 {agent}
            </button>
          {/each}
        </div>
      </div>
    {/if}
    
  <div class="canvas-container">
      <svg
        bind:this={canvas}
        class="workflow-canvas"
        style="transform: scale({zoom}) translate({pan.x}px, {pan.y}px)"
      >
        <!-- Grid Background -->
        <defs>
          <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#e5e7eb" stroke-width="1"/>
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#grid)" />
        
        <!-- Edges -->
        {#each workflow.edges as edge}
          {@const sourceNode = workflow.nodes.find(n => n.id === edge.source)}
          {@const targetNode = workflow.nodes.find(n => n.id === edge.target)}
          {#if sourceNode && targetNode}
      <g class="edge" class:selected={selectedEdge?.id === edge.id}>
              <path
                d="M {sourceNode.position.x + 180} {sourceNode.position.y + 30}
                   C {sourceNode.position.x + 250} {sourceNode.position.y + 30},
                     {targetNode.position.x - 50} {targetNode.position.y + 30},
                     {targetNode.position.x + 20} {targetNode.position.y + 30}"
                stroke="#94a3b8"
                stroke-width="2"
                fill="none"
        role="button"
        tabindex="0"
        on:click={() => selectedEdge = edge}
        on:keydown={(e) => (e.key === 'Enter' || e.key === ' ') && (selectedEdge = edge)}
              />
              {#if edge.label}
                <text
                  x={(sourceNode.position.x + targetNode.position.x) / 2 + 100}
                  y={(sourceNode.position.y + targetNode.position.y) / 2 + 30}
                  text-anchor="middle"
                  class="edge-label"
                >
                  {edge.label}
                </text>
              {/if}
            </g>
          {/if}
        {/each}
        
        <!-- Temporary Connection -->
        {#if isConnecting}
          <line
            x1={tempConnection.x1}
            y1={tempConnection.y1}
            x2={tempConnection.x2}
            y2={tempConnection.y2}
            stroke="#4f46e5"
            stroke-width="2"
            stroke-dasharray="5,5"
          />
        {/if}
      </svg>
      
      <!-- Nodes (HTML overlay) -->
      <div class="nodes-overlay" style="transform: scale({zoom}) translate({pan.x}px, {pan.y}px)">
        {#each workflow.nodes as node}
          <div
            class="workflow-node {node.type}"
            class:selected={selectedNode?.id === node.id}
            style="left: {node.position.x}px; top: {node.position.y}px"
            role="button"
            aria-label={`Workflow node ${node.label}`}
            tabindex="0"
            on:keydown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                selectedNode = node;
                e.preventDefault();
              }
            }}
            on:mousedown={(e) => startDragging(node, e)}
          >
            <div class="node-header">
              <span class="node-icon">
                {nodeTemplates.find(t => t.type === node.type)?.icon || '📦'}
              </span>
              <span class="node-label">{node.label}</span>
              <button 
                class="node-delete"
                on:click|stopPropagation={() => deleteNode(node.id)}
              >
                ×
              </button>
            </div>
            
            {#if node.inputs && node.inputs.length > 0}
              <div
                class="node-port input"
                role="button"
                aria-label="Input port"
                tabindex="0"
                on:mouseup={() => endConnection(node.id, 'input')}
                on:mousedown|stopPropagation={(e) => startConnection(node.id, 'input', e)}
                on:keydown|stopPropagation={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    endConnection(node.id, 'input');
                    e.preventDefault();
                  }
                }}
              ></div>
            {/if}

            {#if node.outputs && node.outputs.length > 0}
              <div
                class="node-port output"
                role="button"
                aria-label="Output port"
                tabindex="0"
                on:mouseup={() => endConnection(node.id, 'output')}
                on:mousedown|stopPropagation={(e) => startConnection(node.id, 'output', e)}
                on:keydown|stopPropagation={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    endConnection(node.id, 'output');
                    e.preventDefault();
                  }
                }}
              ></div>
            {/if}
          </div>
        {/each}
      </div>
    </div>
    
    {#if showProperties && selectedNode}
      <div class="properties-panel">
        <h3>Node Properties</h3>
        <button class="close-btn" on:click={() => showProperties = false}>×</button>
        
        <div class="property-group">
          <label for="prop-id">ID</label>
          <input id="prop-id" type="text" value={selectedNode.id} disabled />
        </div>
        
        <div class="property-group">
          <label for="prop-label">Label</label>
          <input id="prop-label" type="text" bind:value={selectedNode.label} />
        </div>
        
        <div class="property-group">
          <label for="prop-type">Type</label>
          <select id="prop-type" bind:value={selectedNode.type}>
            {#each nodeTemplates as template}
              <option value={template.type}>{template.label}</option>
            {/each}
          </select>
        </div>
        
        {#if selectedNode.type === 'agent'}
          <div class="property-group">
            <label for="prop-agent">Agent</label>
            <select id="prop-agent" bind:value={selectedNode.data.agentName}>
              {#each availableAgents as agent}
                <option value={agent}>{agent}</option>
              {/each}
            </select>
          </div>
        {/if}
        
        {#if selectedNode.type === 'condition'}
          <div class="property-group">
            <label for="prop-expression">Condition Expression</label>
            <textarea
              id="prop-expression"
              bind:value={selectedNode.data.expression}
              placeholder="e.g., result.score > 0.8"
              rows="3"
            ></textarea>
          </div>
        {/if}
        
        <div class="property-group">
          <div class="field-label">Position</div>
          <div class="position-inputs">
            <input
              type="number"
              bind:value={selectedNode.position.x}
              placeholder="X"
              aria-label="Position X"
            />
            <input
              type="number"
              bind:value={selectedNode.position.y}
              placeholder="Y"
              aria-label="Position Y"
            />
          </div>
        </div>
      </div>
    {/if}
  </div>
</div>

<style>
  .graphflow-builder {
    height: 100vh;
    display: flex;
    flex-direction: column;
    background: #f9fafb;
  }
  
  .builder-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 2rem;
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
  }
  
  .workflow-name {
    padding: 0.5rem;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    font-size: 1rem;
    width: 200px;
  }
  
  .header-actions {
    display: flex;
    gap: 0.5rem;
  }
  
  .builder-container {
    flex: 1;
    display: flex;
    overflow: hidden;
  }
  
  .node-library {
    width: 250px;
    background: white;
    border-right: 1px solid #e5e7eb;
    padding: 1rem;
    overflow-y: auto;
  }
  
  .node-library h3 {
    margin: 0 0 1rem 0;
    font-size: 1.1rem;
  }
  
  .node-library h4 {
    margin: 1.5rem 0 0.75rem 0;
    font-size: 0.95rem;
    color: #6b7280;
  }
  
  .node-templates {
    display: grid;
    gap: 0.5rem;
  }
  
  .node-template {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem;
    background: white;
    border: 2px solid;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .node-template:hover {
    transform: translateX(4px);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }
  
  .node-template .icon {
    font-size: 1.25rem;
  }
  
  .agent-list {
    margin-top: 1rem;
  }
  
  .agent-item {
    display: block;
    width: 100%;
    text-align: left;
    padding: 0.5rem;
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 4px;
    margin-bottom: 0.25rem;
    cursor: pointer;
    transition: background 0.2s;
  }
  
  .agent-item:hover {
    background: #f3f4f6;
  }
  
  .canvas-container {
    flex: 1;
    position: relative;
    overflow: hidden;
    background: white;
  }
  
  .workflow-canvas {
    width: 100%;
    height: 100%;
    cursor: grab;
  }
  
  .workflow-canvas:active {
    cursor: grabbing;
  }
  
  .nodes-overlay {
    position: absolute;
    top: 0;
    left: 0;
    pointer-events: none;
  }
  
  .workflow-node {
    position: absolute;
    width: 200px;
    background: white;
    border: 2px solid #d1d5db;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    pointer-events: all;
    cursor: move;
    transition: box-shadow 0.2s;
  }
  
  .workflow-node.selected {
    border-color: #4f46e5;
    box-shadow: 0 4px 8px rgba(79, 70, 229, 0.2);
  }
  
  .workflow-node.agent {
    border-color: #4f46e5;
  }
  
  .workflow-node.condition {
    border-color: #10b981;
  }
  
  .workflow-node.action {
    border-color: #f59e0b;
  }
  
  .workflow-node.input {
    border-color: #8b5cf6;
  }
  
  .workflow-node.output {
    border-color: #ef4444;
  }
  
  .node-header {
    display: flex;
    align-items: center;
    padding: 0.75rem;
    gap: 0.5rem;
  }
  
  .node-icon {
    font-size: 1.25rem;
  }
  
  .node-label {
    flex: 1;
    font-weight: 500;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  
  .node-delete {
    width: 24px;
    height: 24px;
    border: none;
    background: #ef4444;
    color: white;
    border-radius: 50%;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.25rem;
    line-height: 1;
    opacity: 0;
    transition: opacity 0.2s;
  }
  
  .workflow-node:hover .node-delete {
    opacity: 1;
  }
  
  .node-port {
    position: absolute;
    width: 16px;
    height: 16px;
    background: white;
    border: 2px solid #4f46e5;
    border-radius: 50%;
  cursor: crosshair;
  }
  
  .node-port.input {
    left: -8px;
    top: 50%;
    transform: translateY(-50%);
  }
  
  .node-port.output {
    right: -8px;
    top: 50%;
    transform: translateY(-50%);
  }
  
  .node-port:hover {
    background: #4f46e5;
  }
  
  .edge.selected path {
    stroke: #4f46e5;
    stroke-width: 3;
  }
  
  .edge-label {
    fill: #6b7280;
    font-size: 0.875rem;
  }
  
  .properties-panel {
    width: 300px;
    background: white;
    border-left: 1px solid #e5e7eb;
    padding: 1rem;
    overflow-y: auto;
    position: relative;
  }
  
  .properties-panel h3 {
    margin: 0 0 1rem 0;
    font-size: 1.1rem;
  }
  
  .close-btn {
    position: absolute;
    top: 1rem;
    right: 1rem;
    width: 24px;
    height: 24px;
    border: none;
    background: #f3f4f6;
    border-radius: 50%;
    cursor: pointer;
    font-size: 1.25rem;
    line-height: 1;
  }
  
  .property-group {
    margin-bottom: 1rem;
  }
  
  .property-group label {
    display: block;
    margin-bottom: 0.25rem;
    font-weight: 500;
    color: #6b7280;
    font-size: 0.875rem;
  }
  
  .property-group input,
  .property-group select,
  .property-group textarea {
    width: 100%;
    padding: 0.5rem;
    border: 1px solid #d1d5db;
    border-radius: 4px;
    font-size: 0.875rem;
  }
  
  .position-inputs {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.5rem;
  }
  
  .btn {
    padding: 0.5rem 1rem;
    border: none;
    border-radius: 6px;
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .btn-icon {
    padding: 0.5rem;
    background: white;
    border: 1px solid #d1d5db;
  }
  
  .btn-icon:hover {
    background: #f3f4f6;
  }
  
  .btn-primary {
    background: #4f46e5;
    color: white;
  }
  
  .btn-primary:hover {
    background: #4338ca;
  }
  
  .btn-secondary {
    background: #6b7280;
    color: white;
  }
  
  .btn-secondary:hover {
    background: #4b5563;
  }
</style>