<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { workflowsService } from '$lib/services/workflowsService';
  
  export let workflowId: string | null = null;
  export let onSave: any = () => {};
  export let onClose: () => void = () => {};
  
  let canvas: HTMLDivElement;
  let workflow: any = {
    workflow_id: '',
    name: '',
    description: '',
    steps: [],
    edges: []
  };
  
  let selectedNode: any = null;
  // let selectedEdge: any = null; // unused
  let isConnecting = false;
  let connectingFrom: any = null;
  let mousePos = { x: 0, y: 0 };
  let draggedNode: any = null;
  let dragOffset = { x: 0, y: 0 };
  
  // Available agents from Convergio
  const availableAgents = [
    { id: 'ali_chief_of_staff', name: 'Ali - Chief of Staff', color: '#3B82F6' },
    { id: 'domik_mckinsey_strategic_decision_maker', name: 'Domik - McKinsey Strategist', color: '#8B5CF6' },
    { id: 'amy_cfo', name: 'Amy - CFO', color: '#10B981' },
    { id: 'socrates_first_principles_reasoning', name: 'Socrates - First Principles', color: '#F59E0B' },
    { id: 'roee_ceo', name: 'Roee - CEO', color: '#EF4444' },
    { id: 'alon_cto', name: 'Alon - CTO', color: '#6366F1' },
    { id: 'tamar_cpo', name: 'Tamar - CPO', color: '#EC4899' },
    { id: 'mikey_lead_sales', name: 'Mikey - Lead Sales', color: '#14B8A6' },
    { id: 'omri_data_scientist', name: 'Omri - Data Scientist', color: '#F97316' }
  ];
  
  // Step types for AutoGen
  const stepTypes = [
    { value: 'analysis', label: 'Analysis', icon: '📊' },
    { value: 'decision', label: 'Decision', icon: '🎯' },
    { value: 'research', label: 'Research', icon: '🔍' },
    { value: 'planning', label: 'Planning', icon: '📋' },
    { value: 'execution', label: 'Execution', icon: '⚡' },
    { value: 'validation', label: 'Validation', icon: '✅' },
    { value: 'coordination', label: 'Coordination', icon: '🤝' }
  ];
  
  onMount(async () => {
    if (workflowId) {
      await loadWorkflow(workflowId);
    } else {
      // Initialize empty workflow
      workflow = {
        workflow_id: `workflow_${Date.now()}`,
        name: 'New Workflow',
        description: 'Custom AutoGen workflow',
        steps: [],
        edges: []
      };
    }
    
    // Add event listeners
    if (canvas) {
      canvas.addEventListener('mousemove', handleMouseMove);
      canvas.addEventListener('mouseup', handleMouseUp);
    }
  });
  
  onDestroy(() => {
    if (canvas) {
      canvas.removeEventListener('mousemove', handleMouseMove);
      canvas.removeEventListener('mouseup', handleMouseUp);
    }
  });
  
  async function loadWorkflow(id: string) {
    try {
      const data = await workflowsService.getWorkflowDetails(id);
      // Convert to editor format
      workflow = {
        workflow_id: data.workflow_id,
        name: data.name,
        description: data.description,
        steps: data.steps?.map((step: any, index: number) => ({
          id: step.step_id,
          agent_name: step.agent_name,
          step_type: step.step_type,
          description: step.description,
          x: 100 + (index % 3) * 250,
          y: 100 + Math.floor(index / 3) * 200,
          inputs: step.inputs || [],
          outputs: step.outputs || []
        })) || [],
        edges: []
      };
      
      // Rebuild edges from dependencies
      if (data.steps) {
        data.steps.forEach((step: any) => {
          if (step.dependencies) {
            step.dependencies.forEach((dep: string) => {
              workflow.edges.push({
                from: dep,
                to: step.step_id
              });
            });
          }
        });
      }
    } catch {
      // Silent failure
    }
  }
  
  function handleMouseMove(e: MouseEvent) {
    const rect = canvas.getBoundingClientRect();
    mousePos = {
      x: e.clientX - rect.left,
      y: e.clientY - rect.top
    };
    
    if (draggedNode) {
      draggedNode.x = mousePos.x - dragOffset.x;
      draggedNode.y = mousePos.y - dragOffset.y;
      workflow = workflow; // Trigger reactivity
    }
  }
  
  function handleMouseUp() {
    draggedNode = null;
    if (isConnecting) {
      isConnecting = false;
      connectingFrom = null;
    }
  }
  
  function startNodeDrag(node: any, e: MouseEvent) {
    draggedNode = node;
    const rect = canvas.getBoundingClientRect();
    dragOffset = {
      x: e.clientX - rect.left - node.x,
      y: e.clientY - rect.top - node.y
    };
    e.stopPropagation();
  }
  
  function addNode(agent: any) {
    const newNode = {
      id: `step_${Date.now()}`,
      agent_name: agent.id,
      agent_display: agent.name,
      agent_color: agent.color,
      step_type: 'analysis',
      description: `${agent.name} step`,
      x: 150 + workflow.steps.length * 50,
      y: 150 + workflow.steps.length * 30,
      inputs: [],
      outputs: [],
      estimated_duration_minutes: 30
    };
    workflow.steps = [...workflow.steps, newNode];
  }
  
  function deleteNode(node: any) {
    workflow.steps = workflow.steps.filter((n: any) => n.id !== node.id);
    workflow.edges = workflow.edges.filter((e: any) => e.from !== node.id && e.to !== node.id);
  }
  
  function startConnection(node: any) {
    isConnecting = true;
    connectingFrom = node;
  }
  
  function completeConnection(node: any) {
    if (isConnecting && connectingFrom && connectingFrom.id !== node.id) {
      // Check if edge already exists
      const exists = workflow.edges.some((e: any) => 
        e.from === connectingFrom.id && e.to === node.id
      );
      
      if (!exists) {
        workflow.edges = [...workflow.edges, {
          from: connectingFrom.id,
          to: node.id
        }];
      }
    }
    isConnecting = false;
    connectingFrom = null;
  }
  
  function deleteEdge(edge: any) {
    workflow.edges = workflow.edges.filter((e: any) => 
      !(e.from === edge.from && e.to === edge.to)
    );
  }
  
  function getNodeById(id: string) {
    return workflow.steps.find((n: any) => n.id === id);
  }
  
  function saveWorkflow() {
    // Convert to AutoGen format
    const autoGenWorkflow = {
      ...workflow,
      steps: workflow.steps.map((step: any) => ({
        step_id: step.id,
        agent_name: step.agent_name,
        step_type: step.step_type,
        description: step.description,
        inputs: step.inputs,
        outputs: step.outputs,
        dependencies: workflow.edges
          .filter((e: any) => e.to === step.id)
          .map((e: any) => e.from),
        estimated_duration_minutes: step.estimated_duration_minutes || 30
      }))
    };
    
    onSave(autoGenWorkflow);
  }
</script>

<div class="fixed inset-0 bg-surface-50 bg-opacity-50 z-50 flex">
  <!-- Editor Container -->
  <div class="flex-1 bg-white flex flex-col">
    <!-- Header -->
    <div class="bg-surface-100 text-white px-6 py-4 flex items-center justify-between">
      <div class="flex items-center space-x-4">
        <h2 class="text-lg font-medium">AutoGen GraphFlow Editor</h2>
        <input 
          type="text" 
          bind:value={workflow.name}
          class="px-3 py-1 bg-surface-200 text-white rounded text-sm"
          placeholder="Workflow name"
        />
      </div>
      <div class="flex items-center space-x-3">
        <button 
          on:click={saveWorkflow}
          class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm"
        >
          Save Workflow
        </button>
        <button 
          on:click={onClose}
          class="px-4 py-2 bg-surface-600 hover:bg-surface-200 text-white rounded text-sm"
        >
          Close
        </button>
      </div>
    </div>
    
    <!-- Main Editor Area -->
    <div class="flex-1 flex">
      <!-- Agent Palette -->
      <div class="w-64 bg-surface-100 p-4 overflow-y-auto">
        <h3 class="text-sm font-medium text-surface-900 mb-3">Available Agents</h3>
        <div class="space-y-2">
          {#each availableAgents as agent}
            <button 
              on:click={() => addNode(agent)}
              class="w-full text-left px-3 py-2 bg-white hover:bg-surface-50 rounded border border-surface-200 text-xs"
              style="border-left: 4px solid {agent.color}"
            >
              {agent.name}
            </button>
          {/each}
        </div>
        
        <h3 class="text-sm font-medium text-surface-900 mt-6 mb-3">Instructions</h3>
        <div class="text-xs text-surface-600 space-y-2">
          <p>• Click an agent to add it to the workflow</p>
          <p>• Drag nodes to reposition them</p>
          <p>• Click "Connect" then click another node to create a dependency</p>
          <p>• Right-click nodes or edges to delete</p>
          <p>• The workflow executes from top to bottom following the connections</p>
        </div>
      </div>
      
      <!-- Canvas -->
      <div 
        bind:this={canvas}
        class="flex-1 relative bg-surface-50 overflow-auto"
        style="background-image: radial-gradient(circle, #e5e7eb 1px, transparent 1px); background-size: 20px 20px;"
      >
        <!-- SVG for edges -->
  <svg class="absolute inset-0 pointer-events-none" style="width: 100%; height: 100%;">
          <!-- Draw edges -->
          {#each workflow.edges as edge}
            {@const fromNode = getNodeById(edge.from)}
            {@const toNode = getNodeById(edge.to)}
            {#if fromNode && toNode}
              <g>
                <line 
                  x1={fromNode.x + 100}
                  y1={fromNode.y + 40}
                  x2={toNode.x + 100}
                  y2={toNode.y}
                  stroke="#6B7280"
                  stroke-width="2"
                  marker-end="url(#arrowhead)"
                  class="pointer-events-auto cursor-pointer hover:stroke-red-500"
                  role="button"
                  tabindex="0"
                  aria-label="Delete edge"
                  on:keydown={(e) => (e.key === 'Enter' || e.key === ' ') && deleteEdge(edge)}
                  on:contextmenu|preventDefault={() => deleteEdge(edge)}
                />
              </g>
            {/if}
          {/each}
          
          <!-- Draw connecting line while dragging -->
          {#if isConnecting && connectingFrom}
            <line 
              x1={connectingFrom.x + 100}
              y1={connectingFrom.y + 40}
              x2={mousePos.x}
              y2={mousePos.y}
              stroke="#3B82F6"
              stroke-width="2"
              stroke-dasharray="5,5"
            />
          {/if}
          
          <!-- Arrow marker definition -->
          <defs>
            <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto">
              <polygon points="0 0, 10 3.5, 0 7" fill="#6B7280" />
            </marker>
          </defs>
        </svg>
        
        <!-- Nodes -->
        {#each workflow.steps as node}
          <div 
            class="absolute bg-white rounded-lg shadow-lg border-2 p-3 cursor-move select-none"
            style="left: {node.x}px; top: {node.y}px; width: 200px; border-color: {node.agent_color || '#6B7280'}"
            on:mousedown={(e) => startNodeDrag(node, e)}
            on:contextmenu|preventDefault={() => deleteNode(node)}
            role="button"
            tabindex="0"
            aria-label={`Node ${node.agent_display || node.agent_name}`}
            on:keydown={(e) => (e.key === 'Delete' || e.key === 'Backspace') && deleteNode(node)}
          >
            <div class="flex items-center justify-between mb-2">
              <span class="text-xs font-medium text-surface-600">{node.agent_display || node.agent_name}</span>
              <select 
                bind:value={node.step_type}
                class="text-xs px-1 py-0.5 border rounded"
                on:click|stopPropagation
                on:mousedown|stopPropagation
              >
                {#each stepTypes as type}
                  <option value={type.value}>{type.icon} {type.label}</option>
                {/each}
              </select>
            </div>
            <input 
              type="text"
              bind:value={node.description}
              class="w-full text-xs px-2 py-1 border rounded"
              placeholder="Step description"
              on:click|stopPropagation
              on:mousedown|stopPropagation
            />
            <div class="flex justify-between mt-2">
              <button 
                on:click|stopPropagation={() => startConnection(node)}
                on:mousedown|stopPropagation
                class="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
              >
                Connect →
              </button>
              {#if isConnecting && connectingFrom !== node}
                <button 
                  on:click|stopPropagation={() => completeConnection(node)}
                  on:mousedown|stopPropagation
                  class="text-xs px-2 py-1 bg-green-100 text-green-700 rounded hover:bg-green-200"
                >
                  → Here
                </button>
              {/if}
            </div>
          </div>
        {/each}
      </div>
      
      <!-- Properties Panel -->
      {#if selectedNode}
        <div class="w-80 bg-white border-l border-surface-200 p-4">
          <h3 class="text-sm font-medium text-surface-900 mb-4">Node Properties</h3>
          <div class="space-y-3">
            <div>
              <label class="text-xs text-surface-600" for="agent-name">Agent</label>
              <input id="agent-name" type="text" value={selectedNode.agent_name} class="w-full px-2 py-1 border rounded text-sm" readonly />
            </div>
            <div>
              <label class="text-xs text-surface-600" for="node-description">Description</label>
              <textarea 
                id="node-description"
                bind:value={selectedNode.description}
                class="w-full px-2 py-1 border rounded text-sm"
                rows="3"
              ></textarea>
            </div>
            <div>
              <label class="text-xs text-surface-600" for="duration-minutes">Duration (minutes)</label>
              <input 
                id="duration-minutes"
                type="number"
                bind:value={selectedNode.estimated_duration_minutes}
                class="w-full px-2 py-1 border rounded text-sm"
              />
            </div>
            <div>
              <label class="text-xs text-surface-600" for="node-inputs">Inputs (comma-separated)</label>
              <input
                id="node-inputs"
                type="text"
                value={selectedNode.inputs?.join(', ')}
                on:input={(e) => {
                  const target = e.target as HTMLInputElement;
                  selectedNode.inputs = target.value.split(',').map((s: string) => s.trim());
                }}
                class="w-full px-2 py-1 border rounded text-sm"
              />
            </div>
            <div>
              <label class="text-xs text-surface-600" for="node-outputs">Outputs (comma-separated)</label>
              <input
                id="node-outputs"
                type="text"
                value={selectedNode.outputs?.join(', ')}
                on:input={(e) => {
                  const target = e.target as HTMLInputElement;
                  selectedNode.outputs = target.value.split(',').map((s: string) => s.trim());
                }}
                class="w-full px-2 py-1 border rounded text-sm"
              />
            </div>
          </div>
        </div>
      {/if}
    </div>
    
    <!-- Status Bar -->
    <div class="bg-surface-100 text-white px-6 py-2 text-xs flex items-center justify-between">
      <span>Nodes: {workflow.steps.length} | Edges: {workflow.edges.length}</span>
      <span>AutoGen GraphFlow - DiGraphBuilder Compatible</span>
    </div>
  </div>
</div>

<style>
  /* Custom styles for the editor */
  :global(.workflow-node) {
    transition: all 0.2s ease;
  }
  
  :global(.workflow-node:hover) {
    transform: scale(1.05);
  }
</style>