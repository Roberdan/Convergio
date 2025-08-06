<script lang="ts">
  import { onMount } from 'svelte';
  import AgentIcons from '$lib/components/AgentIcons.svelte';

  interface Agent {
    id: number;
    name: string;
    role: string;
    description: string;
    specialty: string;
    personality: string;
    is_featured: boolean;
  }

  interface Message {
    id: number;
    type: string;
    content: string;
    timestamp: Date;
    agents_used?: string[];
  }

  // Search functionality
  let searchQuery = '';
  let selectedSkill = '';
  
  // Complete AI agents list (40+)
  const allAgents: Agent[] = [
    {
      id: 1,
      name: "Ali",
      key: "ali_chief_of_staff",  // Backend agent key
      role: "Chief of Staff",
      description: "Strategic coordinator and master orchestrator",
      specialty: "Executive assistance, team coordination, strategic planning",
      personality: "Diplomatic, strategic, always sees the bigger picture",
      is_featured: true
    },
    {
      id: 2,
      name: "Amy",
      role: "CFO",
      description: "Financial analysis and strategic planning",
      specialty: "Financial modeling, budgeting, investment analysis",
      personality: "Analytical, detail-oriented, fiscally responsible",
      is_featured: true
    },
    {
      id: 3,
      name: "Baccio",
      role: "Tech Architect",
      description: "System architecture and technical strategy",
      specialty: "Cloud architecture, scalability, technical decision-making",
      personality: "Innovative, pragmatic, loves elegant solutions",
      is_featured: true
    },
    {
      id: 4,
      name: "Sofia",
      role: "Marketing Strategist",
      description: "Marketing campaigns and growth strategies",
      specialty: "Brand positioning, digital marketing, customer acquisition",
      personality: "Creative, data-driven, customer-focused",
      is_featured: true
    },
    {
      id: 5,
      name: "Luca",
      role: "Security Expert",
      description: "Cybersecurity and risk management",
      specialty: "Security audits, risk assessment, compliance",
      personality: "Vigilant, thorough, security-first mindset",
      is_featured: true
    },
    {
      id: 6,
      name: "Giulia",
      role: "HR Director",
      description: "Human resources and talent management",
      specialty: "Recruitment, team development, organizational culture",
      personality: "Empathetic, people-focused, culture builder",
      is_featured: true
    },
    // Executive Team
    {
      id: 7,
      name: "Marco",
      role: "Operations Director",
      description: "Operational excellence and process optimization",
      specialty: "Operations management, process improvement, supply chain",
      personality: "Efficient, systematic, results-driven",
      is_featured: false
    },
    {
      id: 8,
      name: "Francesco",
      role: "Legal Advisor",
      description: "Legal compliance and risk management",
      specialty: "Corporate law, contracts, compliance, intellectual property",
      personality: "Meticulous, analytical, risk-aware",
      is_featured: false
    },
    // Technical Team
    {
      id: 9,
      name: "Davide",
      role: "Project Manager",
      description: "Project coordination and delivery management",
      specialty: "Agile methodologies, team coordination, timeline management",
      personality: "Organized, collaborative, deadline-focused",
      is_featured: false
    },
    {
      id: 10,
      name: "Omri",
      role: "Data Scientist",
      description: "Data analysis and machine learning insights",
      specialty: "Predictive analytics, data mining, ML algorithms, statistical analysis",
      personality: "Curious, methodical, insight-driven",
      is_featured: false
    },
    {
      id: 11,
      name: "Elena",
      role: "DevOps Engineer",
      description: "Infrastructure and deployment automation",
      specialty: "CI/CD, cloud infrastructure, monitoring, containerization",
      personality: "Reliable, automation-focused, performance-oriented",
      is_featured: false
    },
    // Marketing & Sales
    {
      id: 12,
      name: "Andrea",
      role: "Sales Director",
      description: "Revenue generation and customer acquisition",
      specialty: "B2B sales, customer relationship management, pipeline optimization",
      personality: "Persuasive, relationship-focused, target-driven",
      is_featured: false
    },
    {
      id: 13,
      name: "Chiara",
      role: "UX Designer",
      description: "User experience and interface design",
      specialty: "User research, wireframing, prototyping, accessibility",
      personality: "Empathetic, creative, user-centered",
      is_featured: false
    },
    {
      id: 14,
      name: "Valentina",
      role: "Content Creator",
      description: "Content strategy and brand storytelling",
      specialty: "Content marketing, copywriting, brand voice, SEO",
      personality: "Creative, strategic, brand-conscious",
      is_featured: false
    },
    // Specialists
    {
      id: 15,
      name: "Matteo",
      role: "Financial Analyst",
      description: "Advanced financial modeling and forecasting",
      specialty: "Financial planning, investment analysis, budget forecasting",
      personality: "Analytical, detail-oriented, numbers-focused",
      is_featured: false
    },
    {
      id: 16,
      name: "Serena",
      role: "Customer Success",
      description: "Customer satisfaction and retention specialist",
      specialty: "Customer onboarding, support, retention strategies",
      personality: "Customer-centric, problem-solver, empathetic",
      is_featured: false
    },
    // Additional specialists (17-40)
    {
      id: 17,
      name: "Roberto",
      role: "CEO Advisor",
      description: "Executive strategy and business transformation",
      specialty: "Strategic planning, digital transformation, C-suite advisory",
      personality: "Visionary, decisive, transformation-focused",
      is_featured: false
    },
    {
      id: 18,
      name: "Alice",
      role: "Innovation Manager",
      description: "Innovation strategies and emerging technologies",
      specialty: "Innovation management, emerging tech, R&D strategy",
      personality: "Forward-thinking, creative, technology-savvy",
      is_featured: false
    },
    {
      id: 19,
      name: "Tomaso",
      role: "Business Analyst",
      description: "Business process optimization and analysis",
      specialty: "Process analysis, business intelligence, KPI optimization",
      personality: "Analytical, process-oriented, efficiency-focused",
      is_featured: false
    },
    {
      id: 20,
      name: "Diana",
      role: "Quality Assurance",
      description: "Quality management and process improvement",
      specialty: "QA processes, compliance, continuous improvement",
      personality: "Meticulous, quality-focused, systematic",
      is_featured: false
    },
    {
      id: 21,
      name: "Filippo",
      role: "Supply Chain Manager",
      description: "Supply chain optimization and logistics",
      specialty: "Supply chain, logistics, vendor management, procurement",
      personality: "Strategic, relationship-focused, cost-conscious",
      is_featured: false
    },
    {
      id: 22,
      name: "Camila",
      role: "Brand Manager",
      description: "Brand strategy and market positioning",
      specialty: "Brand development, market research, positioning strategy",
      personality: "Creative, brand-conscious, market-savvy",
      is_featured: false
    },
    {
      id: 23,
      name: "Giovanni",
      role: "Risk Manager",
      description: "Risk assessment and mitigation strategies",
      specialty: "Risk analysis, compliance, business continuity planning",
      personality: "Cautious, analytical, prevention-focused",
      is_featured: false
    },
    {
      id: 24,
      name: "Lucia",
      role: "Training Coordinator",
      description: "Employee development and training programs",
      specialty: "Training design, skill development, learning management",
      personality: "Educational, supportive, growth-oriented",
      is_featured: false
    },
    {
      id: 25,
      name: "Alessandro",
      role: "Product Manager",
      description: "Product strategy and development lifecycle",
      specialty: "Product roadmaps, user research, competitive analysis",
      personality: "Strategic, user-focused, market-driven",
      is_featured: false
    },
    {
      id: 26,
      name: "Federica",
      role: "Social Media Manager",
      description: "Social media strategy and community management",
      specialty: "Social media marketing, content strategy, community building",
      personality: "Creative, social-savvy, engagement-focused",
      is_featured: false
    },
    {
      id: 27,
      name: "Riccardo",
      role: "Business Intelligence",
      description: "Data-driven business insights and reporting",
      specialty: "BI tools, data visualization, predictive analytics",
      personality: "Data-driven, insight-oriented, strategic",
      is_featured: false
    },
    {
      id: 28,
      name: "Silvia",
      role: "Compliance Officer",
      description: "Regulatory compliance and governance",
      specialty: "Regulatory compliance, governance, audit management",
      personality: "Detail-oriented, ethical, regulation-focused",
      is_featured: false
    },
    {
      id: 29,
      name: "Massimo",
      role: "Partnership Manager",
      description: "Strategic partnerships and business development",
      specialty: "Partnership development, B2B relationships, alliance management",
      personality: "Relationship-builder, strategic, collaboration-focused",
      is_featured: false
    },
    {
      id: 30,
      name: "Paola",
      role: "Change Management",
      description: "Organizational change and transformation",
      specialty: "Change management, organizational development, culture transformation",
      personality: "Empathetic, change-oriented, people-focused",
      is_featured: false
    },
    {
      id: 31,
      name: "Stefano",
      role: "Network Engineer",
      description: "Network infrastructure and security",
      specialty: "Network architecture, cybersecurity, infrastructure management",
      personality: "Technical, security-focused, reliability-oriented",
      is_featured: false
    },
    {
      id: 32,
      name: "Laura",
      role: "Event Coordinator",
      description: "Corporate events and stakeholder engagement",
      specialty: "Event planning, stakeholder management, corporate communications",
      personality: "Organized, people-oriented, detail-focused",
      is_featured: false
    },
    {
      id: 33,
      name: "Vincenzo",
      role: "Treasury Manager",
      description: "Cash management and financial operations",
      specialty: "Cash flow management, treasury operations, financial planning",
      personality: "Precise, financially-savvy, risk-aware",
      is_featured: false
    },
    {
      id: 34,
      name: "Elisabetta",
      role: "Corporate Communications",
      description: "Internal and external communications strategy",
      specialty: "Corporate communications, public relations, crisis communication",
      personality: "Articulate, strategic, reputation-conscious",
      is_featured: false
    },
    {
      id: 35,
      name: "Antonio",
      role: "Database Administrator",
      description: "Database management and optimization",
      specialty: "Database administration, performance tuning, data backup",
      personality: "Technical, methodical, reliability-focused",
      is_featured: false
    },
    {
      id: 36,
      name: "Martina",
      role: "Market Research Analyst",
      description: "Market intelligence and competitive analysis",
      specialty: "Market research, competitive intelligence, trend analysis",
      personality: "Analytical, curious, market-focused",
      is_featured: false
    },
    {
      id: 37,
      name: "Daniele",
      role: "System Administrator",
      description: "IT infrastructure and system maintenance",
      specialty: "System administration, server management, IT support",
      personality: "Technical, problem-solver, maintenance-focused",
      is_featured: false
    },
    {
      id: 38,
      name: "Claudia",
      role: "Sustainability Manager",
      description: "Environmental sustainability and ESG initiatives",
      specialty: "Sustainability strategy, ESG reporting, environmental compliance",
      personality: "Purpose-driven, environmentally-conscious, strategic",
      is_featured: false
    },
    {
      id: 39,
      name: "Fabio",
      role: "Procurement Specialist",
      description: "Strategic procurement and vendor management",
      specialty: "Procurement strategy, vendor negotiation, cost optimization",
      personality: "Negotiation-focused, cost-conscious, relationship-oriented",
      is_featured: false
    },
    {
      id: 40,
      name: "Francesca",
      role: "Business Development",
      description: "Growth strategies and market expansion",
      specialty: "Business development, market expansion, strategic partnerships",
      personality: "Growth-oriented, strategic, opportunity-focused",
      is_featured: false
    }
    // Total: 40 agents
  ];

  // Function to capitalize first letter of each specialty
  function capitalizeSpecialty(specialty: string): string {
    return specialty.split(', ').map(skill => 
      skill.charAt(0).toUpperCase() + skill.slice(1)
    ).join(', ');
  }

  // Extract unique skills for filter
  const allSkills = [...new Set(allAgents.map(agent => agent.specialty.split(', ')).flat())]
    .map(skill => skill.charAt(0).toUpperCase() + skill.slice(1));

  // Featured agents (top 6)
  const featuredAgents = allAgents.filter(agent => agent.is_featured);

  // Filtered agents based on search
  $: filteredAgents = allAgents.filter(agent => {
    const matchesSearch = !searchQuery || 
      agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      agent.role.toLowerCase().includes(searchQuery.toLowerCase()) ||
      agent.specialty.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesSkill = !selectedSkill || 
      agent.specialty.toLowerCase().includes(selectedSkill.toLowerCase());
    
    return matchesSearch && matchesSkill;
  });

  let currentMessage = '';
  let messages: Message[] = [];
  let selectedAgent = featuredAgents[0];
  let isLoading = false;
  
  // View Mode variables
  let isOversightMode = false;
  let oversightIterations: any[] = [];
  let websocket: WebSocket | null = null;

  function selectAgent(agent: Agent) {
    selectedAgent = agent;
    messages = [{
      id: Date.now(),
      type: 'ai',
      content: `Hello! I'm ${agent.name}, your ${agent.role}. ${agent.description}. How can I assist you with ${capitalizeSpecialty(agent.specialty).toLowerCase()} today?`,
      timestamp: new Date()
    }];
  }

  async function sendMessage() {
    if (!currentMessage.trim()) return;
    
    // Add user message
    messages = [...messages, {
      id: Date.now(),
      type: 'user',
      content: currentMessage.trim(),
      timestamp: new Date()
    }];
    
    const messageToSend = currentMessage.trim();
    currentMessage = '';
    isLoading = true;
    
    // Check if we're in Oversight Mode with Ali
    if (isOversightMode && selectedAgent.name === 'Ali') {
      await sendOversightModeMessage(messageToSend);
    } else {
      await sendExecutiveModeMessage(messageToSend);
    }
  }

  async function sendExecutiveModeMessage(messageToSend: string) {
    try {
      const response = await fetch('http://localhost:9000/api/v1/agents/conversation', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message: `[${selectedAgent.role} ${selectedAgent.name}] ${messageToSend}`,
          user_id: 'user-agent-interaction',
          context: {
            agent_id: selectedAgent.id,
            agent_name: selectedAgent.key || selectedAgent.name,  // Use backend key
            agent_role: selectedAgent.role,
            agent_specialty: selectedAgent.specialty
          }
        })
      });

      if (response.ok) {
        const result = await response.json();
        messages = [...messages, {
          id: Date.now() + 1,
          type: 'ai',
          content: result.response,
          timestamp: new Date(),
          agents_used: result.agents_used
        }];
      } else {
        messages = [...messages, {
          id: Date.now() + 1,
          type: 'ai',
          content: `I'm experiencing some technical difficulties. Let me get back to you with a comprehensive response shortly.`,
          timestamp: new Date()
        }];
      }
    } catch (error) {
      console.error('Agent conversation error:', error);
      messages = [...messages, {
        id: Date.now() + 1,
        type: 'ai', 
        content: `I'm having trouble connecting right now. Please try again, and I'll coordinate with the team to provide you with the insights you need.`,
        timestamp: new Date()
      }];
    } finally {
      isLoading = false;
    }
  }

  async function sendOversightModeMessage(messageToSend: string) {
    try {
      // Clear previous oversight iterations
      oversightIterations = [];
      
      // Start WebSocket connection for real-time agent updates
      const conversationId = `oversight-${Date.now()}`;
      const wsUrl = `ws://localhost:9000/api/v1/agents/ws/conversation/${conversationId}`;
      
      websocket = new WebSocket(wsUrl);
      
      websocket.onopen = () => {
        console.log('WebSocket connected for oversight mode');
        // Send conversation start message
        websocket?.send(JSON.stringify({
          type: 'start_conversation',
          message: messageToSend,
          user_id: 'debug-user',
          context: {
            agent_id: selectedAgent.id,
            agent_name: selectedAgent.name,
            agent_role: selectedAgent.role
          }
        }));
      };
      
      websocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('WebSocket message:', data);
        
        switch (data.type) {
          case 'connection_established':
            console.log('Oversight mode connection established');
            break;
            
          case 'conversation_started':
            console.log('Oversight conversation started');
            break;
            
          case 'agent_status':
          case 'agent_response':
            // Add or update agent iteration
            oversightIterations = [...oversightIterations, data];
            break;
            
          case 'conversation_completed':
            isLoading = false;
            // Add final Ali response to regular messages
            messages = [...messages, {
              id: Date.now() + 1,
              type: 'ai',
              content: data.final_response,
              timestamp: new Date(),
              agents_used: data.agents_used || []
            }];
            websocket?.close();
            break;
            
          case 'error':
            console.error('WebSocket error:', data.message);
            isLoading = false;
            messages = [...messages, {
              id: Date.now() + 1,
              type: 'ai',
              content: `Oversight mode error: ${data.message}`,
              timestamp: new Date()
            }];
            break;
        }
      };
      
      websocket.onerror = (error) => {
        console.error('WebSocket error:', error);
        isLoading = false;
        messages = [...messages, {
          id: Date.now() + 1,
          type: 'ai',
          content: `Oversight mode connection failed. Falling back to executive mode.`,
          timestamp: new Date()
        }];
      };
      
    } catch (error) {
      console.error('Oversight mode error:', error);
      isLoading = false;
      // Fallback to executive mode
      await sendExecutiveModeMessage(messageToSend);
    }
  }

  function handleKeyPress(event: KeyboardEvent) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  }

  onMount(() => {
    // Initialize with Ali's welcome message
    selectAgent(featuredAgents[0]);
  });
</script>

<svelte:head>
  <title>AI Team - platform.Convergio.io</title>
</svelte:head>

<!-- AI Agents Page -->
<div class="space-y-6">
  <!-- Header -->
  <div>
    <h1 class="text-lg font-medium text-gray-900">AI Team</h1>
    <p class="mt-1 text-xs text-gray-500">Your specialized AI agents powered by Microsoft AutoGen</p>
  </div>

  <div class="grid lg:grid-cols-5 gap-8">
    <!-- Agents List with integrated search -->
    <div class="lg:col-span-2">
      <div class="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
        <!-- Search in header -->
        <div class="p-4 border-b border-gray-100 bg-gray-50">
          <h3 class="font-semibold text-gray-900 mb-3">AI Team</h3>
          <div class="space-y-3">
            <input
              type="text"
              bind:value={searchQuery}
              placeholder="Search agents by name, role, or skills..."
              class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
            />
            <select
              bind:value={selectedSkill}
              class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
            >
              <option value="">All Specialties</option>
              {#each allSkills.slice(0, 12) as skill}
                <option value={skill}>{skill}</option>
              {/each}
            </select>
          </div>
          
          <div class="flex items-center justify-between text-xs mt-3 pt-3 border-t border-gray-200">
            <span class="text-gray-600">{filteredAgents.length} of {allAgents.length} available</span>
            <div class="flex items-center space-x-1 text-blue-600">
              <div class="w-1.5 h-1.5 bg-blue-500 rounded-full animate-pulse"></div>
              <span>Powered by AutoGen</span>
            </div>
          </div>
        </div>
        
        <!-- Agents List -->
        <div class="max-h-[500px] overflow-y-auto">
          <div class="divide-y divide-gray-100">
            {#each filteredAgents as agent}
              <button
                on:click={() => selectAgent(agent)}
                class="w-full p-3 hover:bg-gray-50 transition-colors text-left group {selectedAgent.id === agent.id ? 'bg-blue-50 border-r-2 border-blue-500' : ''}"
              >
                <div class="flex items-center space-x-3">
                  <div class="w-8 h-8 rounded-lg flex items-center justify-center border border-gray-200 bg-white group-hover:border-blue-300 transition-colors">
                    <AgentIcons agentName={agent.name} size="w-4 h-4" />
                  </div>
                  <div class="flex-1 min-w-0">
                    <div class="font-medium text-gray-900 text-sm">{agent.name}</div>
                    <div class="text-xs text-gray-500">{agent.role}</div>
                    <div class="text-xs text-gray-400 truncate mt-0.5">{capitalizeSpecialty(agent.specialty)}</div>
                  </div>
                  {#if agent.is_featured}
                    <span class="px-2 py-1 bg-blue-100 text-blue-700 rounded-full text-xs font-medium">Featured</span>
                  {:else if selectedAgent.id === agent.id}
                    <div class="w-2 h-2 bg-blue-500 rounded-full"></div>
                  {/if}
                </div>
              </button>
            {/each}
            
            {#if filteredAgents.length === 0}
              <div class="text-center py-8 text-gray-500">
                <div class="text-sm mb-2">No agents found</div>
                <button 
                  on:click={() => { searchQuery = ''; selectedSkill = ''; }}
                  class="text-blue-600 hover:text-blue-800 underline text-sm font-medium"
                >
                  Clear filters
                </button>
              </div>
            {/if}
          </div>
        </div>
      </div>
    </div>

    <!-- Enlarged Chat Interface -->
    <div class="lg:col-span-3">
      <div class="bg-white border border-gray-200 rounded-xl shadow-sm h-[600px] flex flex-col">
        <!-- Chat Header -->
        <div class="px-6 py-4 border-b border-gray-100 bg-gradient-to-r from-blue-50 to-indigo-50">
          <div class="flex items-center justify-between">
            <div class="flex items-center space-x-3">
              <div class="w-10 h-10 rounded-lg flex items-center justify-center border border-blue-200 bg-white">
                <AgentIcons agentName={selectedAgent.name} size="w-5 h-5" />
              </div>
              <div class="flex-1">
                <div class="text-lg font-semibold text-gray-900">{selectedAgent.name}</div>
                <div class="text-sm text-blue-600">{selectedAgent.role}</div>
                <div class="text-xs text-gray-500 mt-1">{capitalizeSpecialty(selectedAgent.specialty)}</div>
              </div>
            </div>
            
            <!-- Executive/Oversight Mode Toggle (only for Ali) -->
            {#if selectedAgent.name === 'Ali'}
              <div class="flex items-center space-x-2 bg-white rounded-lg px-3 py-2 border border-blue-200">
                <span class="text-xs font-medium text-gray-600">View:</span>
                <button
                  on:click={() => isOversightMode = false}
                  class="px-3 py-1 text-xs font-medium rounded transition-colors {!isOversightMode ? 'bg-blue-600 text-white shadow-sm' : 'text-gray-600 hover:text-blue-600'}"
                >
                  Executive
                </button>
                <button
                  on:click={() => isOversightMode = true}
                  class="px-3 py-1 text-xs font-medium rounded transition-colors {isOversightMode ? 'bg-purple-600 text-white shadow-sm' : 'text-gray-600 hover:text-purple-600'}"
                >
                  Oversight
                </button>
              </div>
            {/if}
          </div>
        </div>

        <!-- Messages / Oversight Timeline -->
        <div class="flex-1 overflow-y-auto p-6 space-y-4">
          
          {#if !isOversightMode || selectedAgent.name !== 'Ali'}
            <!-- Executive Mode: Regular Messages -->
            {#each messages as message}
              <div class="flex {message.type === 'user' ? 'justify-end' : 'justify-start'}">
                <div class="max-w-lg">
                  {#if message.type === 'user'}
                    <div class="bg-blue-500 text-white p-4 rounded-xl rounded-br-sm">
                      <div class="font-medium mb-1 opacity-75 text-sm">You</div>
                      <div class="text-sm leading-relaxed">{message.content}</div>
                    </div>
                  {:else}
                    <div class="bg-gray-50 p-4 rounded-xl rounded-bl-sm border">
                      <div class="flex items-center space-x-2 mb-2">
                        <AgentIcons agentName={selectedAgent.name} size="w-4 h-4" />
                        <span class="font-medium text-gray-900 text-sm">{selectedAgent.name}</span>
                        {#if message.agents_used && message.agents_used.length > 1}
                          <span class="text-xs text-blue-600">• Team coordination</span>
                        {/if}
                      </div>
                      <div class="text-gray-800 text-sm leading-relaxed">{message.content}</div>
                    </div>
                  {/if}
                </div>
              </div>
            {/each}
            
            {#if isLoading}
              <div class="flex justify-start">
                <div class="bg-gray-50 p-4 rounded-xl border max-w-lg">
                  <div class="flex items-center space-x-2 mb-2">
                    <AgentIcons agentName={selectedAgent.name} size="w-4 h-4" />
                    <span class="text-sm text-gray-600">{selectedAgent.name} is thinking...</span>
                  </div>
                  <div class="flex space-x-1">
                    <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
                    <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
                  </div>
                </div>
              </div>
            {/if}
          {:else}
            <!-- Oversight Mode: Timeline with Agent Iterations -->
            <div class="oversight-timeline">
              <h3 class="text-sm font-semibold text-gray-700 mb-4 flex items-center">
                <div class="w-2 h-2 bg-purple-600 rounded-full mr-2 animate-pulse"></div>
                Oversight Mode: Team Coordination Timeline
              </h3>
              
              <!-- User Message -->
              {#each messages.filter(m => m.type === 'user') as userMessage}
                <div class="timeline-item mb-6">
                  <div class="flex items-start space-x-3">
                    <div class="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                      <span class="text-white text-xs font-bold">You</span>
                    </div>
                    <div class="flex-1 bg-blue-50 border-l-4 border-blue-500 p-4 rounded-r-lg">
                      <div class="font-medium text-blue-900 text-sm mb-1">Your Request</div>
                      <div class="text-blue-800 text-sm">{userMessage.content}</div>
                    </div>
                  </div>
                </div>
              {/each}
              
              <!-- Agent Iterations -->
              {#each oversightIterations as iteration, i}
                <div class="timeline-item mb-4 relative">
                  <!-- Timeline connector -->
                  {#if i < oversightIterations.length - 1}
                    <div class="absolute left-4 top-12 w-0.5 h-8 bg-gray-200"></div>
                  {/if}
                  
                  <div class="flex items-start space-x-3">
                    <!-- Agent Avatar with Status -->
                    <div class="relative">
                      <div class="w-8 h-8 rounded-full flex items-center justify-center border-2" style="background-color: {iteration.color}20; border-color: {iteration.color}">
                        <AgentIcons agentName={iteration.agent_name} size="w-4 h-4" />
                      </div>
                      
                      <!-- Status Indicator -->
                      {#if iteration.status === 'thinking'}
                        <div class="absolute -top-1 -right-1 w-3 h-3 bg-yellow-400 rounded-full animate-pulse"></div>
                      {:else if iteration.status === 'completed'}
                        <div class="absolute -top-1 -right-1 w-3 h-3 bg-green-500 rounded-full">
                          <svg class="w-2 h-2 text-white absolute top-0.5 left-0.5" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
                          </svg>
                        </div>
                      {:else if iteration.status === 'active'}
                        <div class="absolute -top-1 -right-1 w-3 h-3 bg-blue-500 rounded-full animate-bounce"></div>
                      {/if}
                    </div>
                    
                    <!-- Agent Content -->
                    <div class="flex-1 border-l-4 p-3 rounded-r-lg" style="background-color: {iteration.color}05; border-left-color: {iteration.color}">
                      <div class="flex items-center space-x-2 mb-2">
                        <span class="font-medium text-sm" style="color: {iteration.color}">{iteration.agent_name}</span>
                        <span class="text-xs text-gray-500">{iteration.agent_role}</span>
                        <div class="text-xs px-2 py-1 rounded-full" style="background-color: {iteration.color}20; color: {iteration.color}">
                          Turn {iteration.turn}
                        </div>
                      </div>
                      
                      {#if iteration.status === 'thinking'}
                        <div class="text-sm text-gray-600 italic">{iteration.message || `${iteration.agent_name} is analyzing your request...`}</div>
                      {:else}
                        <div class="text-sm text-gray-800">{iteration.content}</div>
                      {/if}
                      
                      <div class="text-xs text-gray-400 mt-2">
                        {new Date(iteration.timestamp).toLocaleTimeString()}
                      </div>
                    </div>
                  </div>
                </div>
              {/each}
              
              <!-- Loading state in oversight mode -->
              {#if isLoading}
                <div class="timeline-item mb-4">
                  <div class="flex items-start space-x-3">
                    <div class="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center animate-pulse">
                      <AgentIcons agentName="Ali" size="w-4 h-4" />
                    </div>
                    <div class="flex-1 bg-gray-50 border-l-4 border-gray-200 p-3 rounded-r-lg">
                      <div class="text-sm text-gray-600">Ali is coordinating the team response...</div>
                      <div class="flex space-x-1 mt-2">
                        <div class="w-2 h-2 bg-purple-400 rounded-full animate-bounce"></div>
                        <div class="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
                        <div class="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
                      </div>
                    </div>
                  </div>
                </div>
              {/if}
            </div>
          {/if}
        </div>

        <!-- Enhanced Input -->
        <div class="p-6 border-t border-gray-100 bg-gray-50">
          <div class="flex space-x-3">
            <textarea
              bind:value={currentMessage}
              on:keydown={handleKeyPress}
              placeholder="Ask {selectedAgent.name} about strategy, analysis, or anything in their expertise area..."
              class="flex-1 px-4 py-3 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
              rows="2"
              disabled={isLoading}
            ></textarea>
            <button
              on:click={sendMessage}
              disabled={!currentMessage.trim() || isLoading}
              class="px-6 py-3 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-300 text-white rounded-lg transition-colors font-medium"
            >
              Send
            </button>
          </div>
          <div class="text-xs text-gray-500 mt-2">
            Press Shift+Enter for new line, Enter to send
          </div>
        </div>
      </div>
    </div>
  </div>

</div>