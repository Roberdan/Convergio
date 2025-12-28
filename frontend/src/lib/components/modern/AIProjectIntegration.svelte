<script lang="ts">
  import { onMount } from 'svelte';
  import { writable } from 'svelte/store';
  
  export let projectId: string = '';
  export let taskId: string = '';
  
  interface ChatMessage {
    id: string;
    agent: string;
    message: string;
    timestamp: Date;
    type: string;
  }

  let availableAgents: any[] = [];
  let activeAssignments: any[] = [];
  let aiRecommendations: any[] = [];
  // removed unused selectedAgent
  let agentChat = writable<ChatMessage[]>([]);
  let newMessage = '';
  // removed unused loading flag (kept internal state via onMount end)
  let showAgentSelector = false;
  let realTimeCollaboration = true;
  
  // Modern glassmorphism colors
  const colors = {
    primary: '#6366f1',
    secondary: '#8b5cf6',
    success: '#10b981',
    warning: '#f59e0b',
    danger: '#ef4444',
    background: 'rgba(15, 23, 42, 1)',
    glass: 'rgba(255, 255, 255, 0.1)',
    text: '#f8fafc',
    textSecondary: '#cbd5e1'
  };
  
  // Available AI Agents with specializations
  const agentCatalog = [
    {
      id: 'ali_chief_of_staff',
      name: 'Ali',
      role: 'Chief of Staff',
      specialization: 'Strategic Planning & Coordination',
      avatar: '👤',
      color: '#6366f1',
      capabilities: ['Project Strategy', 'Team Coordination', 'Risk Assessment', 'Executive Planning'],
      availability: 'available',
      currentProjects: 3,
      avgResponseTime: '2.4s',
      successRate: '94%'
    },
    {
      id: 'marcus_pm',
      name: 'Marcus',
      role: 'Project Manager',
      specialization: 'Agile Project Management',
      avatar: '📋',
      color: '#10b981',
      capabilities: ['Sprint Planning', 'Resource Allocation', 'Timeline Management', 'Stakeholder Communication'],
      availability: 'busy',
      currentProjects: 5,
      avgResponseTime: '3.1s',
      successRate: '92%'
    },
    {
      id: 'sara_ux_designer',
      name: 'Sara',
      role: 'UX Designer',
      specialization: 'User Experience & Interface Design',
      avatar: '🎨',
      color: '#ec4899',
      capabilities: ['User Research', 'Wireframing', 'Prototyping', 'Design Systems'],
      availability: 'available',
      currentProjects: 2,
      avgResponseTime: '4.2s',
      successRate: '96%'
    },
    {
      id: 'baccio_tech_architect',
      name: 'Baccio',
      role: 'Tech Architect',
      specialization: 'System Architecture & Engineering',
      avatar: '🏗️',
      color: '#f59e0b',
      capabilities: ['System Design', 'Technical Planning', 'Architecture Review', 'Performance Optimization'],
      availability: 'available',
      currentProjects: 4,
      avgResponseTime: '5.1s',
      successRate: '89%'
    },
    {
      id: 'thor_qa_guardian',
      name: 'Thor',
      role: 'QA Guardian',
      specialization: 'Quality Assurance & Testing',
      avatar: '🛡️',
      color: '#8b5cf6',
      capabilities: ['Test Planning', 'Quality Review', 'Bug Analysis', 'Performance Testing'],
      availability: 'busy',
      currentProjects: 6,
      avgResponseTime: '3.8s',
      successRate: '98%'
    },
    {
      id: 'amy_cfo',
      name: 'Amy',
      role: 'CFO',
      specialization: 'Financial Planning & Analysis',
      avatar: '💰',
      color: '#10b981',
      capabilities: ['Budget Planning', 'Cost Analysis', 'ROI Calculation', 'Financial Reporting'],
      availability: 'available',
      currentProjects: 2,
      avgResponseTime: '2.8s',
      successRate: '91%'
    }
  ];
  
  // Mock AI recommendations for agent assignments
  const mockRecommendations = [
    {
      id: 'rec1',
      type: 'agent_assignment',
      priority: 'high',
      title: 'Optimal Agent Assignment',
      message: 'Based on project requirements and agent workload, Ali + Marcus + Sara would provide 87% efficiency boost',
      recommendedAgents: ['ali_chief_of_staff', 'marcus_pm', 'sara_ux_designer'],
      reasoning: 'Strategic oversight (Ali) + Project management (Marcus) + UX expertise (Sara) covers all critical project dimensions',
      expectedOutcome: '23% faster delivery, 15% higher quality score',
      confidence: 0.87
    },
    {
      id: 'rec2',
      type: 'workload_optimization',
      priority: 'medium',
      title: 'Workload Balancing',
      message: 'Thor QA Guardian is at 95% capacity - consider redistributing testing tasks or adding support',
      recommendedAction: 'Reassign 2 testing tasks to Baccio Tech Architect who has testing capabilities',
      reasoning: 'Prevents bottleneck in QA phase and maintains quality standards',
      expectedOutcome: '18% reduction in testing delays',
      confidence: 0.79
    },
    {
      id: 'rec3',
      type: 'skill_matching',
      priority: 'high',
      title: 'Perfect Skill Match',
      message: 'Sara UX Designer\'s wireframing expertise perfectly matches current UI redesign requirements',
      recommendedAgents: ['sara_ux_designer'],
      reasoning: 'Project needs advanced prototyping skills - Sara has 96% success rate in similar projects',
      expectedOutcome: 'Design phase completion 12 days earlier',
      confidence: 0.94
    }
  ];
  
  // Mock chat messages
  const mockChatHistory = [
    {
      id: '1',
      agent: 'ali_chief_of_staff',
      message: 'I\'ve analyzed the project requirements. The scope looks ambitious but achievable with proper resource allocation.',
      timestamp: new Date(Date.now() - 3600000),
      type: 'analysis'
    },
    {
      id: '2',
      agent: 'marcus_pm',
      message: 'Agreed with Ali. I recommend breaking this into 3 sprints: Foundation (3 weeks), Core Features (4 weeks), Polish (2 weeks).',
      timestamp: new Date(Date.now() - 3000000),
      type: 'planning'
    },
    {
      id: '3',
      agent: 'sara_ux_designer',
      message: 'I can start on wireframes immediately. The user flow analysis suggests we need 5 key screens with 3 interaction patterns.',
      timestamp: new Date(Date.now() - 1800000),
      type: 'design'
    },
    {
      id: '4',
      agent: 'user',
      message: 'Sounds great! What about the technical architecture?',
      timestamp: new Date(Date.now() - 1200000),
      type: 'question'
    },
    {
      id: '5',
      agent: 'baccio_tech_architect',
      message: 'I\'ve prepared a microservices architecture proposal. It scales well and aligns with the team\'s expertise.',
      timestamp: new Date(Date.now() - 600000),
      type: 'technical'
    }
  ];
  
  onMount(async () => {
    await loadProjectAgents();
    await loadAIRecommendations();
    agentChat.set(mockChatHistory);
    setupRealTimeUpdates();
  // finished initial load
  });
  
  async function loadProjectAgents() {
    try {
      const response = await fetch(`/api/v1/pm/projects/${projectId}/agents`);
      if (response.ok) {
        activeAssignments = await response.json();
      }
    } catch {
      // Silent failure
      // Use mock data
      activeAssignments = [
        { agentId: 'ali_chief_of_staff', role: 'lead', assignedAt: new Date(Date.now() - 86400000) },
        { agentId: 'marcus_pm', role: 'manager', assignedAt: new Date(Date.now() - 3600000) },
        { agentId: 'sara_ux_designer', role: 'contributor', assignedAt: new Date(Date.now() - 1800000) }
      ];
    }
    
    availableAgents = agentCatalog;
  }
  
  async function loadAIRecommendations() {
    try {
      const response = await fetch('/api/v1/agents/ali/agent-recommendations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_id: projectId,
          task_id: taskId,
          current_assignments: activeAssignments
        })
      });
      
      if (response.ok) {
        aiRecommendations = await response.json();
      }
    } catch {
      // Silent failure
      aiRecommendations = mockRecommendations;
    }
  }
  
  function setupRealTimeUpdates() {
    if (!realTimeCollaboration) return;
    
    // Simulate real-time agent messages
    setInterval(() => {
      if (Math.random() > 0.95) { // 5% chance every interval
        const agents = activeAssignments.map(a => a.agentId);
        const randomAgent = agents[Math.floor(Math.random() * agents.length)];
        const agent = availableAgents.find(a => a.id === randomAgent);
        
        if (agent) {
          const messages = [
            'Making progress on the assigned tasks.',
            'Identified an optimization opportunity.',
            'Ready for the next phase.',
            'Quality check completed successfully.',
            'Updated project timeline estimates.'
          ];
          
          const newMsg = {
            id: Date.now().toString(),
            agent: randomAgent,
            message: messages[Math.floor(Math.random() * messages.length)],
            timestamp: new Date(),
            type: 'update'
          };
          
          agentChat.update(chat => [...chat, newMsg]);
        }
      }
    }, 10000);
  }
  
  async function assignAgent(agentId: string, role: string = 'contributor') {
    try {
      const response = await fetch(`/api/v1/pm/projects/${projectId}/agents`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          agent_id: agentId,
          role: role,
          task_id: taskId
        })
      });
      
      if (response.ok) {
        await loadProjectAgents();
        showAgentSelector = false;
        
        // Add assignment notification to chat
        const agent = availableAgents.find(a => a.id === agentId);
        if (agent) {
          agentChat.update(chat => [...chat, {
            id: Date.now().toString(),
            agent: agentId,
            message: `I've been assigned to this project as ${role}. Ready to contribute!`,
            timestamp: new Date(),
            type: 'assignment'
          }]);
        }
      }
    } catch {
      // Silent failure
      alert(`${agentId} has been notified and will join the project shortly.`);
    }
  }
  
  async function removeAgent(agentId: string) {
    try {
      const response = await fetch(`/api/v1/pm/projects/${projectId}/agents/${agentId}`, {
        method: 'DELETE'
      });
      
      if (response.ok) {
        await loadProjectAgents();
      }
    } catch {
      // Silent failure
      activeAssignments = activeAssignments.filter(a => a.agentId !== agentId);
    }
  }
  
  async function sendMessage() {
    if (!newMessage.trim()) return;
    
    const userMsg = {
      id: Date.now().toString(),
      agent: 'user',
      message: newMessage,
      timestamp: new Date(),
      type: 'message'
    };
    
    agentChat.update(chat => [...chat, userMsg]);
    
    // Send to agents
    try {
      const response = await fetch('/api/v1/agents/chat/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_id: projectId,
          message: newMessage,
          recipients: activeAssignments.map(a => a.agentId)
        })
      });
      
      if (response.ok) {
        const agentResponses = await response.json();
        // Add agent responses
        agentResponses.forEach((resp: any) => {
          agentChat.update(chat => [...chat, {
            id: Date.now().toString() + resp.agent,
            agent: resp.agent,
            message: resp.message,
            timestamp: new Date(),
            type: 'response'
          }]);
        });
      }
    } catch {
      // Silent failure
      // Simulate agent response
      setTimeout(() => {
        if (activeAssignments.length > 0) {
          const randomAssignment = activeAssignments[Math.floor(Math.random() * activeAssignments.length)];
          agentChat.update(chat => [...chat, {
            id: Date.now().toString() + 'resp',
            agent: randomAssignment.agentId,
            message: 'I understand your request and will work on it immediately.',
            timestamp: new Date(),
            type: 'response'
          }]);
        }
      }, 2000);
    }
    
    newMessage = '';
  }
  
  function getAgentInfo(agentId: string) {
    return availableAgents.find(a => a.id === agentId) || { name: agentId, avatar: '👤', color: '#6366f1' };
  }
  
  function getAvailabilityColor(availability: string): string {
    switch (availability) {
      case 'available': return colors.success;
      case 'busy': return colors.warning;
      case 'offline': return colors.danger;
      default: return colors.textSecondary;
    }
  }
  
  function getPriorityColor(priority: string): string {
    switch (priority) {
      case 'high': return colors.danger;
      case 'medium': return colors.warning;
      case 'low': return colors.success;
      default: return colors.primary;
    }
  }
  
  function formatTimestamp(timestamp: Date): string {
    const now = new Date();
    const diff = now.getTime() - timestamp.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    
    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    return timestamp.toLocaleDateString();
  }
  
  async function implementRecommendation(recommendation: any) {
    try {
      if (recommendation.recommendedAgents) {
        // Auto-assign recommended agents
        for (const agentId of recommendation.recommendedAgents) {
          await assignAgent(agentId, 'contributor');
        }
        alert(`✅ Implemented: ${recommendation.title}`);
      } else {
        alert(`🤖 AI recommendation noted: ${recommendation.recommendedAction}`);
      }
      
      // Remove implemented recommendation
      aiRecommendations = aiRecommendations.filter(r => r.id !== recommendation.id);
    } catch {
      // Silent failure
    }
  }
</script>

<div class="ai-integration-container">
  <!-- Header -->
  <div class="integration-header">
    <div class="header-left">
      <h2 class="integration-title">
        <span class="title-icon">🤖</span>
        AI Agent Integration
      </h2>
      <p class="integration-subtitle">Intelligent collaboration with your AI team</p>
    </div>
    
    <div class="header-actions">
      <button 
        class="assign-agent-btn"
        on:click={() => showAgentSelector = true}
      >
        <span class="plus-icon">+</span>
        Assign Agent
      </button>
      
      <div class="collaboration-toggle">
        <input 
          type="checkbox" 
          id="realtime" 
          bind:checked={realTimeCollaboration}
        />
        <label for="realtime">Real-time Collaboration</label>
      </div>
    </div>
  </div>
  
  <!-- AI Recommendations -->
  {#if aiRecommendations.length > 0}
    <div class="recommendations-panel">
      <div class="panel-header">
        <h3>
          <span class="ai-icon">🧠</span>
          AI Agent Recommendations
        </h3>
        <p>Smart suggestions for optimal team composition</p>
      </div>
      
      <div class="recommendations-grid">
        {#each aiRecommendations as rec}
          <div class="recommendation-card" style="border-left: 4px solid {getPriorityColor(rec.priority)}">
            <div class="rec-header">
              <div class="rec-meta">
                <span class="rec-type">{rec.type.replace('_', ' ').toUpperCase()}</span>
                <span class="priority-badge" style="background: {getPriorityColor(rec.priority)}">
                  {rec.priority.toUpperCase()}
                </span>
              </div>
              <span class="confidence">
                {Math.round(rec.confidence * 100)}% confidence
              </span>
            </div>
            
            <h4 class="rec-title">{rec.title}</h4>
            <p class="rec-message">{rec.message}</p>
            
            {#if rec.recommendedAgents}
              <div class="recommended-agents">
                <span class="agents-label">Recommended Agents:</span>
                <div class="agents-list">
                  {#each rec.recommendedAgents as agentId}
                    {@const agent = getAgentInfo(agentId)}
                    <div class="agent-chip" style="border-color: {agent.color}">
                      <span class="agent-avatar">{agent.avatar}</span>
                      <span class="agent-name">{agent.name}</span>
                    </div>
                  {/each}
                </div>
              </div>
            {/if}
            
            {#if rec.reasoning}
              <div class="reasoning">
                <span class="reasoning-label">AI Reasoning:</span>
                <p class="reasoning-text">{rec.reasoning}</p>
              </div>
            {/if}
            
            {#if rec.expectedOutcome}
              <div class="expected-outcome">
                <span class="outcome-label">Expected Outcome:</span>
                <span class="outcome-value">{rec.expectedOutcome}</span>
              </div>
            {/if}
            
            <div class="rec-actions">
              <button 
                class="implement-btn"
                on:click={() => implementRecommendation(rec)}
              >
                Implement
              </button>
              <button 
                class="dismiss-btn"
                on:click={() => aiRecommendations = aiRecommendations.filter(r => r.id !== rec.id)}
              >
                Dismiss
              </button>
            </div>
          </div>
        {/each}
      </div>
    </div>
  {/if}
  
  <!-- Current Agent Assignments -->
  <div class="agents-panel">
    <div class="panel-header">
      <h3>
        <span class="team-icon">👥</span>
        Active AI Team
      </h3>
      <p>{activeAssignments.length} agents currently assigned</p>
    </div>
    
    <div class="agents-grid">
      {#each activeAssignments as assignment}
        {@const agent = getAgentInfo(assignment.agentId)}
        <div class="agent-card">
          <div class="agent-header">
            <div class="agent-info">
              <div class="agent-avatar-large" style="background: {agent.color}">
                {agent.avatar}
              </div>
              <div class="agent-details">
                <h4 class="agent-name">{agent.name}</h4>
                <p class="agent-role">{agent.role}</p>
                <p class="agent-specialization">{agent.specialization}</p>
              </div>
            </div>
            
            <div class="agent-status">
              <div class="availability-indicator" style="background: {getAvailabilityColor(agent.availability)}"></div>
              <span class="availability-text">{agent.availability}</span>
            </div>
          </div>
          
          <div class="agent-metrics">
            <div class="metric">
              <span class="metric-label">Response Time</span>
              <span class="metric-value">{agent.avgResponseTime}</span>
            </div>
            <div class="metric">
              <span class="metric-label">Success Rate</span>
              <span class="metric-value">{agent.successRate}</span>
            </div>
            <div class="metric">
              <span class="metric-label">Projects</span>
              <span class="metric-value">{agent.currentProjects}</span>
            </div>
          </div>
          
          <div class="agent-capabilities">
            <span class="capabilities-label">Capabilities:</span>
            <div class="capabilities-list">
              {#each agent.capabilities as capability}
                <span class="capability-tag">{capability}</span>
              {/each}
            </div>
          </div>
          
          <div class="agent-actions">
            <span class="assignment-info">
              Assigned {formatTimestamp(assignment.assignedAt)} as {assignment.role}
            </span>
            <button 
              class="remove-btn"
              on:click={() => removeAgent(assignment.agentId)}
            >
              Remove
            </button>
          </div>
        </div>
      {/each}
    </div>
  </div>
  
  <!-- Agent Chat Interface -->
  <div class="chat-panel">
    <div class="chat-header">
      <h3>
        <span class="chat-icon">💬</span>
        AI Team Chat
      </h3>
      <div class="chat-status">
        <div class="online-indicator"></div>
        <span>{activeAssignments.length} agents online</span>
      </div>
    </div>
    
    <div class="chat-messages">
      {#each $agentChat as message}
        {@const agent = message.agent === 'user' ? { name: 'You', avatar: '👤', color: '#6366f1' } : getAgentInfo(message.agent)}
        <div class="message" class:user-message={message.agent === 'user'}>
          <div class="message-avatar" style="background: {agent.color}">
            {agent.avatar}
          </div>
          <div class="message-content">
            <div class="message-header">
              <span class="message-sender">{agent.name}</span>
              <span class="message-time">{formatTimestamp(message.timestamp)}</span>
              <span class="message-type type-{message.type}">{message.type}</span>
            </div>
            <p class="message-text">{message.message}</p>
          </div>
        </div>
      {/each}
    </div>
    
    <div class="chat-input">
      <input 
        type="text" 
        placeholder="Send a message to your AI team..."
        bind:value={newMessage}
        on:keypress={(e) => e.key === 'Enter' && sendMessage()}
      />
      <button class="send-btn" on:click={sendMessage}>
        <span class="send-icon">📤</span>
      </button>
    </div>
  </div>
  
  <!-- Agent Selector Modal -->
  {#if showAgentSelector}
    <div
      class="modal-overlay"
      role="dialog"
      aria-modal="true"
      aria-labelledby="agent-selector-title"
  tabindex="0"
  on:click={(e) => { if (e.currentTarget === e.target) showAgentSelector = false; }}
  on:keydown={(e) => { if (e.key === 'Escape' || e.key === 'Enter' || e.key === ' ') { e.stopPropagation(); showAgentSelector = false; } }}
    >
      <div
        class="agent-selector-modal"
        role="document"
      >
        <div class="modal-header">
          <h3 id="agent-selector-title">Select AI Agent</h3>
          <button class="close-btn" on:click={() => showAgentSelector = false} aria-label="Close">×</button>
        </div>
        
        <div class="available-agents">
          {#each availableAgents as agent}
            {@const isAssigned = activeAssignments.some(a => a.agentId === agent.id)}
            <div class="agent-option" class:disabled={isAssigned} role="group" aria-label={`Agent ${agent.name}`}>
              <div class="agent-info">
                <div class="agent-avatar-medium" style="background: {agent.color}">
                  {agent.avatar}
                </div>
                <div class="agent-details">
                  <h4>{agent.name}</h4>
                  <p>{agent.role}</p>
                  <p class="specialization">{agent.specialization}</p>
                </div>
              </div>
              
              <div class="agent-stats">
                <div class="availability" style="color: {getAvailabilityColor(agent.availability)}">
                  {agent.availability}
                </div>
                <div class="stats-grid">
                  <span>Response: {agent.avgResponseTime}</span>
                  <span>Success: {agent.successRate}</span>
                </div>
              </div>
              
              <div class="assign-actions">
                {#if isAssigned}
                  <span class="assigned-label">Already Assigned</span>
                {:else}
                  <button 
                    class="assign-btn primary"
                    on:click={() => assignAgent(agent.id, 'lead')}
                    aria-label={`Assign ${agent.name} as Lead`}
                  >
                    Assign as Lead
                  </button>
                  <button 
                    class="assign-btn secondary"
                    on:click={() => assignAgent(agent.id, 'contributor')}
                    aria-label={`Assign ${agent.name} as Contributor`}
                  >
                    Assign as Contributor
                  </button>
                {/if}
              </div>
            </div>
          {/each}
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  .ai-integration-container {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    min-height: 100vh;
    padding: 24px;
    position: relative;
    overflow: hidden;
  }
  
  .ai-integration-container::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: 
      radial-gradient(circle at 20% 80%, rgba(99, 102, 241, 0.1) 0%, transparent 50%),
      radial-gradient(circle at 80% 20%, rgba(139, 92, 246, 0.1) 0%, transparent 50%);
    pointer-events: none;
    z-index: 0;
  }
  
  .integration-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 32px;
    position: relative;
    z-index: 1;
  }
  
  .integration-title {
    font-size: 32px;
    font-weight: 700;
    color: #f8fafc;
    margin: 0;
    display: flex;
    align-items: center;
    gap: 16px;
  }
  
  .title-icon {
    font-size: 36px;
  }
  
  .integration-subtitle {
    color: #cbd5e1;
    margin: 6px 0 0 52px;
    font-size: 16px;
  }
  
  .header-actions {
    display: flex;
    align-items: center;
    gap: 20px;
  }
  
  .assign-agent-btn {
    background: rgba(16, 185, 129, 0.2);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(16, 185, 129, 0.3);
    color: #10b981;
    padding: 12px 20px;
    border-radius: 12px;
    font-weight: 600;
    transition: all 0.3s ease;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  .assign-agent-btn:hover {
    background: rgba(16, 185, 129, 0.3);
    transform: translateY(-2px);
  }
  
  .collaboration-toggle {
    display: flex;
    align-items: center;
    gap: 8px;
    color: #cbd5e1;
    font-size: 14px;
  }
  
  .collaboration-toggle input[type="checkbox"] {
    width: 16px;
    height: 16px;
  }
  
  .recommendations-panel, .agents-panel, .chat-panel {
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 32px;
    position: relative;
    z-index: 1;
  }
  
  .panel-header h3 {
    color: #f8fafc;
    font-size: 20px;
    font-weight: 600;
    margin-bottom: 4px;
    display: flex;
    align-items: center;
    gap: 12px;
  }
  
  .panel-header p {
    color: #cbd5e1;
    font-size: 14px;
    margin-bottom: 20px;
  }
  
  .recommendations-grid, .agents-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
    gap: 20px;
  }
  
  .recommendation-card, .agent-card {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 20px;
    transition: all 0.3s ease;
  }
  
  .recommendation-card:hover, .agent-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
  }
  
  .rec-header, .agent-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
  }
  
  .rec-meta {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  
  .rec-type {
    font-size: 10px;
    font-weight: 700;
    color: #6366f1;
    text-transform: uppercase;
    letter-spacing: 1px;
  }
  
  .priority-badge {
    padding: 4px 8px;
    border-radius: 6px;
    font-size: 10px;
    font-weight: 700;
    color: white;
  }
  
  .confidence {
    color: #10b981;
    font-size: 12px;
    font-weight: 600;
  }
  
  .rec-title {
    color: #f8fafc;
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 8px;
  }
  
  .rec-message {
    color: #cbd5e1;
    font-size: 14px;
    line-height: 1.5;
    margin-bottom: 12px;
  }
  
  .recommended-agents {
    margin-bottom: 12px;
  }
  
  .agents-label {
    color: #94a3b8;
    font-size: 12px;
    font-weight: 600;
    display: block;
    margin-bottom: 8px;
  }
  
  .agents-list {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }
  
  .agent-chip {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid;
    border-radius: 20px;
    padding: 6px 12px;
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
  }
  
  .agent-avatar {
    font-size: 14px;
  }
  
  .agent-name {
    color: #f8fafc;
    font-weight: 500;
  }
  
  .reasoning, .expected-outcome {
    margin-bottom: 12px;
  }
  
  .reasoning-label, .outcome-label {
    color: #94a3b8;
    font-size: 12px;
    font-weight: 600;
    display: block;
    margin-bottom: 4px;
  }
  
  .reasoning-text {
    color: #a78bfa;
    font-size: 13px;
    line-height: 1.4;
    font-style: italic;
    margin: 0;
  }
  
  .outcome-value {
    color: #10b981;
    font-size: 13px;
    font-weight: 600;
  }
  
  .rec-actions {
    display: flex;
    gap: 12px;
    justify-content: flex-end;
  }
  
  .implement-btn, .dismiss-btn {
    padding: 6px 12px;
    border: none;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 600;
    transition: all 0.3s ease;
  }
  
  .implement-btn {
    background: rgba(99, 102, 241, 0.2);
    border: 1px solid rgba(99, 102, 241, 0.3);
    color: #6366f1;
  }
  
  .dismiss-btn {
    background: rgba(239, 68, 68, 0.2);
    border: 1px solid rgba(239, 68, 68, 0.3);
    color: #ef4444;
  }
  
  .agent-info {
    display: flex;
    gap: 12px;
  }
  
  .agent-avatar-large {
    width: 48px;
    height: 48px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    color: white;
  }
  
  .agent-details h4 {
    color: #f8fafc;
    font-size: 16px;
    font-weight: 600;
    margin: 0 0 4px 0;
  }
  
  .agent-role {
    color: #a78bfa;
    font-size: 13px;
    font-weight: 500;
    margin: 0 0 2px 0;
  }
  
  .agent-specialization {
    color: #94a3b8;
    font-size: 12px;
    margin: 0;
  }
  
  .agent-status {
    display: flex;
    align-items: center;
    gap: 6px;
  }
  
  .availability-indicator {
    width: 8px;
    height: 8px;
    border-radius: 50%;
  }
  
  .availability-text {
    color: #cbd5e1;
    font-size: 12px;
    text-transform: capitalize;
  }
  
  .agent-metrics {
    display: flex;
    justify-content: space-between;
    margin: 16px 0;
    padding: 12px 0;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  }
  
  .metric {
    text-align: center;
  }
  
  .metric-label {
    color: #94a3b8;
    font-size: 11px;
    display: block;
    margin-bottom: 4px;
  }
  
  .metric-value {
    color: #f8fafc;
    font-size: 14px;
    font-weight: 600;
  }
  
  .agent-capabilities {
    margin: 16px 0;
  }
  
  .capabilities-label {
    color: #94a3b8;
    font-size: 12px;
    font-weight: 600;
    display: block;
    margin-bottom: 8px;
  }
  
  .capabilities-list {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }
  
  .capability-tag {
    background: rgba(139, 92, 246, 0.2);
    color: #a78bfa;
    padding: 4px 8px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 500;
  }
  
  .agent-actions {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .assignment-info {
    color: #94a3b8;
    font-size: 11px;
  }
  
  .remove-btn {
    background: rgba(239, 68, 68, 0.2);
    border: 1px solid rgba(239, 68, 68, 0.3);
    color: #ef4444;
    padding: 6px 12px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 600;
    transition: all 0.3s ease;
  }
  
  .chat-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
  }
  
  .chat-status {
    display: flex;
    align-items: center;
    gap: 8px;
    color: #10b981;
    font-size: 14px;
  }
  
  .online-indicator {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #10b981;
    animation: pulse 2s infinite;
  }
  
  .chat-messages {
    height: 300px;
    overflow-y: auto;
    margin-bottom: 16px;
    padding-right: 8px;
  }
  
  .message {
    display: flex;
    gap: 12px;
    margin-bottom: 16px;
  }
  
  .message.user-message {
    flex-direction: row-reverse;
  }
  
  .message-avatar {
    width: 36px;
    height: 36px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
    color: white;
    flex-shrink: 0;
  }
  
  .message-content {
    flex: 1;
    max-width: 70%;
  }
  
  .user-message .message-content {
    text-align: right;
  }
  
  .message-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 4px;
  }
  
  .user-message .message-header {
    justify-content: flex-end;
  }
  
  .message-sender {
    color: #f8fafc;
    font-size: 13px;
    font-weight: 600;
  }
  
  .message-time {
    color: #94a3b8;
    font-size: 11px;
  }
  
  .message-type {
    background: rgba(99, 102, 241, 0.2);
    color: #a78bfa;
    padding: 2px 6px;
    border-radius: 10px;
    font-size: 9px;
    font-weight: 600;
    text-transform: uppercase;
  }
  
  .message-text {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 12px;
    color: #cbd5e1;
    font-size: 14px;
    line-height: 1.4;
    margin: 0;
  }
  
  .user-message .message-text {
    background: rgba(99, 102, 241, 0.2);
    border-color: rgba(99, 102, 241, 0.3);
    color: #ddd6fe;
  }
  
  .chat-input {
    display: flex;
    gap: 12px;
  }
  
  .chat-input input {
    flex: 1;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 12px;
    padding: 12px 16px;
    color: #f8fafc;
    font-size: 14px;
  }
  
  .chat-input input::placeholder {
    color: #94a3b8;
  }
  
  .send-btn {
    background: rgba(99, 102, 241, 0.2);
    border: 1px solid rgba(99, 102, 241, 0.3);
    border-radius: 12px;
    padding: 12px 16px;
    color: #6366f1;
    transition: all 0.3s ease;
  }
  
  .send-btn:hover {
    background: rgba(99, 102, 241, 0.3);
  }
  
  .modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.8);
    backdrop-filter: blur(8px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }
  
  .agent-selector-modal {
    background: rgba(15, 23, 42, 0.95);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 16px;
    width: 90%;
    max-width: 800px;
    max-height: 90vh;
    overflow: hidden;
  }
  
  .modal-header {
    background: rgba(99, 102, 241, 0.2);
    padding: 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .modal-header h3 {
    color: #f8fafc;
    font-size: 18px;
    font-weight: 600;
    margin: 0;
  }
  
  .close-btn {
    background: none;
    border: none;
    color: #f8fafc;
    font-size: 24px;
    cursor: pointer;
  }
  
  .available-agents {
    padding: 20px;
    max-height: calc(90vh - 140px);
    overflow-y: auto;
  }
  
  .agent-option {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 12px;
    transition: all 0.3s ease;
  }
  
  .agent-option:hover:not(.disabled) {
    background: rgba(255, 255, 255, 0.08);
  }
  
  .agent-option.disabled {
    opacity: 0.5;
    pointer-events: none;
  }
  
  .agent-avatar-medium {
    width: 40px;
    height: 40px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    color: white;
  }
  
  .agent-stats {
    text-align: center;
  }
  
  .availability {
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    margin-bottom: 4px;
  }
  
  .stats-grid {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }
  
  .stats-grid span {
    color: #94a3b8;
    font-size: 11px;
  }
  
  .assign-actions {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  
  .assign-btn {
    padding: 8px 16px;
    border: none;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 600;
    transition: all 0.3s ease;
  }
  
  .assign-btn.primary {
    background: #6366f1;
    color: white;
  }
  
  .assign-btn.secondary {
    background: rgba(255, 255, 255, 0.1);
    color: #f8fafc;
    border: 1px solid rgba(255, 255, 255, 0.2);
  }
  
  .assigned-label {
    color: #10b981;
    font-size: 12px;
    font-weight: 600;
    text-align: center;
    padding: 8px;
  }
</style>