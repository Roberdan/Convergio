<script lang="ts">
  import { onMount } from 'svelte';
  import AgentIcons from '$lib/components/AgentIcons.svelte';
  import AgentStatus from '$lib/components/AgentStatus.svelte';
  import ConversationManager from '$lib/components/ConversationManager.svelte';
  import MarkdownRenderer from '$lib/components/MarkdownRenderer.svelte';
  import { conversationManager, currentAgentId } from '$lib/stores/conversationStore';

  interface Agent {
    id: number;
    name: string;
    role: string;
    description: string;
    specialty: string;
    personality: string;
    is_featured: boolean;
    key?: string;  // Backend agent key
  }

  interface Message {
    id: number | string;
    type: string;
    content: string;
    timestamp: Date;
    agents_used?: string[];
  }

  // Search functionality
  let searchQuery = '';
  let selectedSkill = '';
  
  // Conversation management
  let showConversationManager = false;
  
  // Dynamic AI agents list - loaded from API
  let allAgents: Agent[] = [];
  let isLoadingAgents = true;
  let loadingError: string | null = null;
  
  // Show hire new agent form
  let showHireForm = false;
  
  // Agent creation form data
  let newAgentForm = {
    name: '',
    role: '',
    description: '',
    specialty: '',
    personality: ''
  };
  let isCreatingAgent = false;
  let creationError: string | null = null;
  let creationSuccess = false;
  
  // AI Generated agent preview
  let generatedAgent: any = null;
  let isGeneratingAgent = false;
  let showPreview = false;

  // Reset form
  function resetAgentForm() {
    newAgentForm = {
      name: '',
      role: '',
      description: '',
      specialty: '',
      personality: ''
    };
    creationError = null;
    creationSuccess = false;
    showPreview = false;
    generatedAgent = null;
    isGeneratingAgent = false;
    isCreatingAgent = false;
  }

  // Cancel agent creation
  function cancelAgentCreation() {
    resetAgentForm();
    showHireForm = false;
  }

  // Generate agent using AI
  async function generateAgent() {
    isGeneratingAgent = true;
    creationError = null;
    generatedAgent = null;

    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:9000';
      
      const response = await fetch(`${apiUrl}/api/v1/agents/generate-agent`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          basic_info: {
            name: newAgentForm.name,
            role: newAgentForm.role,
            description: newAgentForm.description,
            specialty: newAgentForm.specialty,
            personality: newAgentForm.personality
          },
          existing_agents: allAgents.slice(0, 10) // Send sample of existing agents for context
        })
      });

      if (response.ok) {
        const result = await response.json();
        generatedAgent = result.agent;
        showPreview = true;
        console.log('Agent generated:', generatedAgent);
      } else {
        const errorData = await response.json();
        throw new Error(errorData.message || `Failed to generate agent: ${response.statusText}`);
      }
    } catch (error) {
      console.error('Failed to generate agent:', error);
      creationError = error instanceof Error ? error.message : 'Failed to generate agent with AI';
    } finally {
      isGeneratingAgent = false;
    }
  }

  // Create the final agent after review
  async function createFinalAgent() {
    isCreatingAgent = true;
    creationError = null;

    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:9000';
      
      const response = await fetch(`${apiUrl}/api/v1/agents/create-agent`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          agent_data: generatedAgent
        })
      });

      if (response.ok) {
        const result = await response.json();
        console.log('Agent created successfully:', result);
        
        creationSuccess = true;
        
        // Reload agents to include the new one
        setTimeout(async () => {
          await loadAgentsFromAPI();
          resetAgentForm();
          showHireForm = false;
          showPreview = false;
          generatedAgent = null;
        }, 1500);
      } else {
        const errorData = await response.json();
        throw new Error(errorData.message || `Failed to create agent: ${response.statusText}`);
      }
    } catch (error) {
      console.error('Failed to create final agent:', error);
      creationError = error instanceof Error ? error.message : 'Failed to create agent';
    } finally {
      isCreatingAgent = false;
    }
  }

  // Back to editing
  function backToEdit() {
    showPreview = false;
    generatedAgent = null;
  }
  
  // Static fallback agents (kept for offline/error scenarios)
  const fallbackAgents: Agent[] = [
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
      key: "amy_cfo",
      role: "CFO", 
      description: "Financial analysis and strategic planning",
      specialty: "Financial modeling, budgeting, investment analysis",
      personality: "Analytical, detail-oriented, fiscally responsible",
      is_featured: true
    },
    {
      id: 3,
      name: "Baccio",
      key: "baccio_tech_architect",
      role: "Tech Architect",
      description: "System architecture and technical strategy",
      specialty: "Cloud architecture, scalability, technical decision-making",
      personality: "Innovative, pragmatic, loves elegant solutions",
      is_featured: true
    }
  ];

  // Function to capitalize first letter of each specialty
  function capitalizeSpecialty(specialty: string): string {
    return specialty.split(', ').map(skill => 
      skill.charAt(0).toUpperCase() + skill.slice(1)
    ).join(', ');
  }

  // Helper functions to get simple agent data
  function getSimpleRole(key: string): string {
    const roleMap: Record<string, string> = {
      'ali_chief_of_staff': 'Chief of Staff',
      'amy_cfo': 'CFO',
      'baccio_tech_architect': 'Tech Architect',
      'sofia_marketing_strategist': 'Marketing Strategist',
      'luca_security_expert': 'Security Expert',
      'giulia_hr_talent_acquisition': 'HR Director',
      'marco_devops_engineer': 'Operations Director',
      'elena_legal_compliance_expert': 'Legal Advisor',
      'davide_project_manager': 'Project Manager',
      'omri_data_scientist': 'Data Scientist',
      'dan_engineering_gm': 'DevOps Engineer',
      'andrea_customer_success_manager': 'Sales Director',
      'sara_ux_ui_designer': 'UX Designer',
      'riccardo_storyteller': 'Content Creator',
      'matteo_strategic_business_architect': 'Financial Analyst',
      'satya_board_of_directors': 'CEO Advisor',
      'antonio_strategy_expert': 'Innovation Manager',
      'diana_performance_dashboard': 'Quality Assurance'
    };
    return roleMap[key] || 'AI Agent';
  }

  function getSimpleDescription(key: string): string {
    const descMap: Record<string, string> = {
      'ali_chief_of_staff': 'Strategic coordinator and master orchestrator',
      'amy_cfo': 'Financial analysis and strategic planning',
      'baccio_tech_architect': 'System architecture and technical strategy',
      'sofia_marketing_strategist': 'Marketing campaigns and growth strategies',
      'luca_security_expert': 'Cybersecurity and risk management',
      'giulia_hr_talent_acquisition': 'Human resources and talent management',
      'marco_devops_engineer': 'Operational excellence and process optimization',
      'elena_legal_compliance_expert': 'Legal compliance and risk management',
      'davide_project_manager': 'Project coordination and delivery management',
      'omri_data_scientist': 'Data analysis and machine learning insights',
      'dan_engineering_gm': 'Infrastructure and deployment automation',
      'andrea_customer_success_manager': 'Revenue generation and customer acquisition',
      'sara_ux_ui_designer': 'User experience and interface design',
      'riccardo_storyteller': 'Content strategy and brand storytelling',
      'matteo_strategic_business_architect': 'Advanced financial modeling and forecasting',
      'satya_board_of_directors': 'Executive strategy and business transformation',
      'antonio_strategy_expert': 'Innovation strategies and emerging technologies',
      'diana_performance_dashboard': 'Quality management and process improvement'
    };
    return descMap[key] || 'AI-powered specialist';
  }

  function getSimpleSpecialty(key: string): string {
    const specMap: Record<string, string> = {
      'ali_chief_of_staff': 'Executive assistance, team coordination, strategic planning',
      'amy_cfo': 'Financial modeling, budgeting, investment analysis',
      'baccio_tech_architect': 'Cloud architecture, scalability, technical decision-making',
      'sofia_marketing_strategist': 'Brand positioning, digital marketing, customer acquisition',
      'luca_security_expert': 'Security audits, risk assessment, compliance',
      'giulia_hr_talent_acquisition': 'Recruitment, team development, organizational culture',
      'marco_devops_engineer': 'Operations management, process improvement, supply chain',
      'elena_legal_compliance_expert': 'Corporate law, contracts, compliance, intellectual property',
      'davide_project_manager': 'Agile methodologies, team coordination, timeline management',
      'omri_data_scientist': 'Predictive analytics, data mining, ML algorithms, statistical analysis',
      'dan_engineering_gm': 'CI/CD, cloud infrastructure, monitoring, containerization',
      'andrea_customer_success_manager': 'B2B sales, customer relationship management, pipeline optimization',
      'sara_ux_ui_designer': 'User research, wireframing, prototyping, accessibility',
      'riccardo_storyteller': 'Content marketing, copywriting, brand voice, SEO',
      'matteo_strategic_business_architect': 'Financial planning, investment analysis, budget forecasting',
      'satya_board_of_directors': 'Strategic planning, digital transformation, C-suite advisory',
      'antonio_strategy_expert': 'Innovation management, emerging tech, R&D strategy',
      'diana_performance_dashboard': 'QA processes, compliance, continuous improvement'
    };
    return specMap[key] || 'General AI assistance, problem solving';
  }

  function getSimplePersonality(key: string): string {
    const persMap: Record<string, string> = {
      'ali_chief_of_staff': 'Diplomatic, strategic, always sees the bigger picture',
      'amy_cfo': 'Analytical, detail-oriented, fiscally responsible',
      'baccio_tech_architect': 'Innovative, pragmatic, loves elegant solutions',
      'sofia_marketing_strategist': 'Creative, data-driven, customer-focused',
      'luca_security_expert': 'Vigilant, thorough, security-first mindset',
      'giulia_hr_talent_acquisition': 'Empathetic, people-focused, culture builder',
      'marco_devops_engineer': 'Efficient, systematic, results-driven',
      'elena_legal_compliance_expert': 'Meticulous, analytical, risk-aware',
      'davide_project_manager': 'Organized, collaborative, deadline-focused',
      'omri_data_scientist': 'Curious, methodical, insight-driven',
      'dan_engineering_gm': 'Reliable, automation-focused, performance-oriented',
      'andrea_customer_success_manager': 'Persuasive, relationship-focused, target-driven',
      'sara_ux_ui_designer': 'Empathetic, creative, user-centered',
      'riccardo_storyteller': 'Creative, strategic, brand-conscious',
      'matteo_strategic_business_architect': 'Analytical, detail-oriented, numbers-focused',
      'satya_board_of_directors': 'Visionary, decisive, transformation-focused',
      'antonio_strategy_expert': 'Forward-thinking, creative, technology-savvy',
      'diana_performance_dashboard': 'Meticulous, quality-focused, systematic'
    };
    return persMap[key] || 'Intelligent, helpful, specialized';
  }

  // Load agents from API
  async function loadAgentsFromAPI() {
    isLoadingAgents = true;
    loadingError = null;
    
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:9000';
      const response = await fetch(`${apiUrl}/api/v1/agent-management/agents`);
      if (response.ok) {
        const data = await response.json();
        
        // The backend now returns an array directly, not wrapped in {agents: [...]}
        const agentsArray = Array.isArray(data) ? data : (data.agents || []);
        
        // Transform backend agent data to frontend format with proper names and descriptions
        const transformedAgents = agentsArray.map((backendAgent: any, index: number) => {
          // Convert backend name to proper display name (ethan-ic6da -> Ethan)
          const displayName = backendAgent.name.split('-')[0].charAt(0).toUpperCase() + 
                              backendAgent.name.split('-')[0].slice(1);
          
          // Use backend data or fallback to helper functions
          const role = backendAgent.tier || getSimpleRole(backendAgent.id);
          const description = backendAgent.role || getSimpleDescription(backendAgent.id);
          // Map backend tier to specialty for consistency with fallback agents
          const specialty = backendAgent.tier || getSimpleSpecialty(backendAgent.id);
          const personality = getSimplePersonality(backendAgent.id);
          
          return {
            id: index + 1,
            name: displayName,
            key: backendAgent.id, // backend uses 'id' not 'key'
            role: role,
            description: description,
            specialty: specialty,
            personality: personality,
            is_featured: index < 6 // First 6 are featured
          };
        });
        
        // Sort agents so Ali is first
        transformedAgents.sort((a: Agent, b: Agent) => {
          // Ali Chief of Staff should be first
          if (a.key && a.key.includes('ali-chief-of-staff')) return -1;
          if (b.key && b.key.includes('ali-chief-of-staff')) return 1;
          
          // Then by alphabetical order of display name
          return a.name.localeCompare(b.name);
        });
        
        allAgents = transformedAgents;
        console.log(`✅ Loaded ${allAgents.length} agents from API (Ali first)`);
      } else {
        throw new Error(`API returned ${response.status}: ${response.statusText}`);
      }
    } catch (error) {
      console.error('Failed to load agents from API:', error);
      loadingError = error instanceof Error ? error.message : 'Unknown error';
      
      // Fallback to static agents
      allAgents = fallbackAgents;
      console.log('📋 Using fallback agents');
    } finally {
      isLoadingAgents = false;
    }
  }

  // Extract unique skills for filter (reactive)
  $: allSkills = [...new Set(allAgents.map(agent => {
    // Handle both comma-separated specialties and single tier values
    if (agent.specialty && agent.specialty.includes(',')) {
      return agent.specialty.split(', ').map(skill => skill.trim());
    } else if (agent.specialty) {
      return [agent.specialty.trim()];
    }
    return [];
  }).flat())].map(skill => skill.charAt(0).toUpperCase() + skill.slice(1)).sort();

  // Featured agents (reactive)
  $: featuredAgents = allAgents.filter(agent => agent.is_featured);

  // Filtered agents based on search
  $: filteredAgents = allAgents.filter(agent => {
    const matchesSearch = !searchQuery || 
      agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      agent.role.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (agent.specialty && agent.specialty.toLowerCase().includes(searchQuery.toLowerCase()));
    
    const matchesSkill = !selectedSkill || 
      (agent.specialty && agent.specialty.toLowerCase().includes(selectedSkill.toLowerCase()));
    
    return matchesSearch && matchesSkill;
  });

  let currentMessage = '';
  let messages: Message[] = [];
  let selectedAgent = fallbackAgents[0];
  let isLoading = false;
  let messagesContainer: HTMLElement;
  
  // View Mode variables
  let isOversightMode = false;
  let oversightIterations: any[] = [];
  let websocket: WebSocket | null = null;

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

  function selectAgent(agent: Agent) {
    selectedAgent = agent;
    showConversationManager = true;
    
    // Switch conversation context
    if (agent.key) {
      conversationManager.switchToAgent(agent.key);
      currentAgentId.set(agent.key);
    }
    
    // Load existing conversation or create welcome message
    const conversation = conversationManager.getConversation?.(agent.key || agent.name.toLowerCase());
    if (conversation && conversation.messages.length > 0) {
      // Convert conversation messages to local format
      messages = conversation.messages.map(msg => ({
        id: msg.id,
        type: msg.type === 'user' ? 'user' : 'ai',
        content: msg.content,
        timestamp: msg.timestamp,
        agents_used: []
      }));
    } else {
      // Start with empty conversation - agent will introduce itself intelligently if needed
      messages = [];
    }
  }

  async function sendMessage() {
    if (!currentMessage.trim()) return;
    
    // Add user message
    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: currentMessage.trim(),
      timestamp: new Date()
    };
    messages = [...messages, userMessage];
    
    // Save user message to conversation store
    if (selectedAgent?.key) {
      conversationManager.addMessage(selectedAgent.key, {
        agentId: selectedAgent.key,
        agentName: selectedAgent.name,
        content: userMessage.content,
        timestamp: userMessage.timestamp,
        type: 'user',
        status: 'sent'
      });
    }
    
    const messageToSend = currentMessage.trim();
    currentMessage = '';
    isLoading = true;
    
    // Check if we're in Oversight Mode with Ali
    if (isOversightMode && selectedAgent?.name === 'Ali') {
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
          message: `[${selectedAgent?.role || 'Agent'} ${selectedAgent?.name || 'Unknown'}] ${messageToSend}`,
          user_id: 'user-agent-interaction',
          context: {
            agent_id: selectedAgent?.id || 0,
            agent_name: selectedAgent?.key || selectedAgent?.name || 'unknown',  // Use backend key
            agent_role: selectedAgent?.role || 'Agent',
            agent_specialty: selectedAgent?.specialty || 'General assistance'
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
      
      // Save conversation to store
      if (selectedAgent?.key && messages.length > 0) {
        const lastMessage = messages[messages.length - 1];
        if (lastMessage.type === 'ai') {
          conversationManager.addMessage(selectedAgent.key, {
            agentId: selectedAgent.key,
            agentName: selectedAgent.name,
            content: lastMessage.content,
            timestamp: lastMessage.timestamp,
            type: 'agent',
            status: 'sent'
          });
        }
      }
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
            agent_id: selectedAgent?.id || 0,
            agent_name: selectedAgent?.name || 'Unknown',
            agent_role: selectedAgent?.role || 'Agent'
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
    // Load agents and initialize
    (async () => {
      await loadAgentsFromAPI();
      
      // Initialize conversations for all agents
      allAgents.forEach(agent => {
        if (agent.key) {
          conversationManager.initializeConversation(agent.key, agent.name);
        }
      });
      
      // Initialize with Ali as default agent (Ali is sorted first in line 354-361)
      setTimeout(() => {
        // Find Ali agent specifically
        const aliAgent = allAgents.find(agent => 
          agent.key?.includes('ali-chief-of-staff') || 
          agent.key?.includes('ali_chief_of_staff') ||
          agent.name?.toLowerCase() === 'ali'
        );
        
        if (aliAgent) {
          selectedAgent = aliAgent;
          selectAgent(aliAgent);
          console.log('✅ Ali set as default agent');
        } else if (featuredAgents.length > 0) {
          selectedAgent = featuredAgents[0];
          selectAgent(featuredAgents[0]);
        } else if (allAgents.length > 0) {
          selectedAgent = allAgents[0];
          selectAgent(allAgents[0]);
        }
      }, 100);
    })();
  });
</script>

<svelte:head>
  <title>AI Team - platform.Convergio.io</title>
</svelte:head>

<!-- AI Agents Page -->
<div class="min-h-screen bg-surface-100  space-y-8">

  <div class="px-6 pb-8">
    <div class="max-w-7xl mx-auto">
      <div class="grid lg:grid-cols-5 gap-8">
        <!-- Enhanced Agents List with integrated search -->
        <div class="lg:col-span-2">
          <div class="bg-surface-50 border border-surface-300  rounded-2xl overflow-hidden shadow-lg">
            <!-- Search in header -->
            <div class="p-6 border-b border-surface-300  bg-surface-100 ">
              <div class="flex items-center justify-between mb-6">
                <div>
                  <h3 class="text-xl font-bold text-surface-900  mb-1">AI Team</h3>
                  <p class="text-sm text-surface-600 ">Manage your specialized AI agents</p>
                </div>
                <!-- Hire New Agent Button -->
                <button
                  on:click={() => showHireForm = true}
                  on:keydown={(e) => e.key === 'Enter' || e.key === ' ' ? (e.preventDefault(), showHireForm = true) : null}
                  class="btn-primary flex items-center space-x-2 px-4 py-2.5 rounded-lg shadow-sm hover:shadow-md transition-all duration-200 transform hover:scale-105"
                  aria-label="Hire new AI agent"
                  tabindex="0"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
                  </svg>
                  <span class="font-medium">Hire Agent</span>
                </button>
              </div>
              
              <!-- Enhanced Filter Section -->
              <div class="space-y-4">
                <!-- Search Bar with Icon -->
                <div class="relative">
                  <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <svg class="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                    </svg>
                  </div>
                  <input
                    type="text"
                    bind:value={searchQuery}
                    placeholder="Search agents by name, role, or skills..."
                    class="w-full pl-10 pr-4 py-3 border border-surface-400  rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-surface-50 shadow-sm"
                    aria-label="Search agents by name, role, or skills"
                    role="searchbox"
                  />
                </div>
                
                <!-- Specialty Filter with Better Styling -->
                <div class="relative">
                  <label for="specialty-filter" class="block text-sm font-medium text-surface-700  mb-2">Filter by Tier & Specialty</label>
                  <div class="relative">
                    <select
                      id="specialty-filter"
                      bind:value={selectedSkill}
                      class="w-full px-4 py-3 border border-surface-400  rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-surface-50 shadow-sm appearance-none cursor-pointer"
                      aria-label="Filter agents by tier/specialty"
                      role="combobox"
                    >
                      <option value="">All Tiers & Specialties</option>
                      {#each allSkills.slice(0, 15) as skill}
                        <option value={skill}>{skill}</option>
                      {/each}
                    </select>
                    <div class="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
                      <svg class="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
                      </svg>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- Enhanced Status Bar -->
              <div class="flex items-center justify-between text-sm mt-6 pt-4 border-t border-surface-300 ">
                <div class="flex items-center space-x-4">
                  <div class="flex items-center space-x-2">
                    <div class="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span class="text-surface-700  font-medium">{filteredAgents.length} of {allAgents.length} agents available</span>
                  </div>
                  {#if isLoadingAgents}
                    <div class="flex items-center space-x-2 text-blue-600">
                      <div class="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                      <span class="text-sm">Loading...</span>
                    </div>
                  {:else if loadingError}
                    <div class="flex items-center space-x-2 text-amber-600">
                      <div class="w-2 h-2 bg-amber-500 rounded-full"></div>
                      <span class="text-sm">Fallback mode</span>
                    </div>
                  {/if}
                </div>
                
                <!-- Clear Filters Button -->
                {#if searchQuery || selectedSkill}
                  <button
                    on:click={() => { searchQuery = ''; selectedSkill = ''; }}
                    on:keydown={(e) => (e.key === 'Enter' || e.key === ' ') ? (e.preventDefault(), searchQuery = '', selectedSkill = '') : null}
                    class="text-sm text-surface-500 hover:text-surface-700  underline transition-colors duration-200"
                    aria-label="Clear search filters"
                    tabindex="0"
                  >
                    Clear filters
                  </button>
                {/if}
                
                <div class="flex items-center space-x-2 text-blue-600">
                  <div class="w-2 h-2 bg-blue-500 rounded-full"></div>
                  <span class="text-sm font-medium">Powered by AutoGen</span>
                </div>
              </div>
            </div>
            
            <!-- Agents List -->
            <div class="max-h-[600px] overflow-y-auto">
              <div class="divide-y divide-gray-100">
                {#each filteredAgents as agent}
                  <button
                    on:click={() => selectAgent(agent)}
                    on:keydown={(e) => (e.key === 'Enter' || e.key === ' ') ? (e.preventDefault(), selectAgent(agent)) : null}
                    class="w-full p-4 hover:bg-gradient-to-r hover:from-blue-50 hover:to-indigo-50 transition-all duration-200 text-left group {selectedAgent.id === agent.id ? 'bg-gradient-to-r from-blue-100 to-indigo-100 border-r-4 border-blue-500 shadow-sm' : ''}"
                    aria-label="Select {agent.name} - {agent.role}"
                    aria-pressed="{selectedAgent.id === agent.id}"
                    tabindex="0"
                  >
                    <div class="flex items-start space-x-4">
                      <!-- Agent Avatar with Enhanced Styling -->
                      <div class="w-12 h-12 rounded-xl flex items-center justify-center border-2 border-surface-300  bg-gradient-to-br from-gray-50 to-gray-100 group-hover:border-blue-400 group-hover:from-blue-50 group-hover:to-indigo-50 transition-all duration-200 shadow-sm">
                        <AgentIcons agentName={agent.name} size="w-6 h-6" />
                      </div>
                      
                      <!-- Agent Information -->
                      <div class="flex-1 min-w-0 space-y-2">
                        <div class="flex items-start justify-between">
                          <div class="flex-1 min-w-0">
                            <div class="text-lg font-semibold text-surface-900  group-hover:text-blue-900 transition-colors duration-200">{agent.name}</div>
                            <div class="text-sm font-medium text-blue-600 group-hover:text-blue-700 transition-colors duration-200">{agent.role}</div>
                          </div>
                          
                          <!-- Status Indicator -->
                          {#if agent.key}
                            <AgentStatus agentId={agent.key} agentName={agent.name} compact={true} />
                          {:else}
                            <div class="flex items-center space-x-2 px-3 py-1 bg-green-100 rounded-full">
                              <div class="w-2 h-2 bg-green-500 rounded-full"></div>
                              <span class="text-xs text-green-700 font-medium">Ready</span>
                            </div>
                          {/if}
                        </div>
                        
                        <!-- Description and Specialty -->
                        <div class="space-y-1">
                          <p class="text-sm text-surface-600  line-clamp-2 leading-relaxed">{agent.description}</p>
                          {#if agent.specialty}
                            <div class="flex items-center space-x-2">
                              <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 border border-blue-200">
                                {agent.specialty}
                              </span>
                            </div>
                          {/if}
                        </div>
                      </div>
                    </div>
                  </button>
                {/each}
                
                <!-- Enhanced Empty State -->
                {#if filteredAgents.length === 0}
                  <div class="text-center py-12 text-surface-500">
                    <div class="w-16 h-16 mx-auto mb-4 bg-surface-200  rounded-full flex items-center justify-center">
                      <svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                      </svg>
                    </div>
                    <div class="text-lg font-medium text-surface-900  mb-2">No agents found</div>
                    <p class="text-sm text-surface-600  mb-4">Try adjusting your search or filter criteria</p>
                    <button 
                      on:click={() => { searchQuery = ''; selectedSkill = ''; }}
                      on:keydown={(e) => (e.key === 'Enter' || e.key === ' ') ? (e.preventDefault(), searchQuery = '', selectedSkill = '') : null}
                      class="inline-flex items-center px-4 py-2 border border-surface-400  rounded-lg text-sm font-medium text-surface-700  bg-surface-50 hover:bg-surface-100  focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-all duration-200"
                      aria-label="Clear search filters"
                      tabindex="0"
                    >
                      <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                      </svg>
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
          <div class="bg-surface-50 border border-surface-300  rounded-2xl h-[700px] flex flex-col shadow-lg">
            <!-- Enhanced Chat Header -->
            <div class="px-6 py-5 border-b border-surface-300  bg-gradient-to-r from-blue-50 to-indigo-50">
              <div class="flex items-center justify-between">
                <div class="flex items-center space-x-4">
                  <div class="w-12 h-12 rounded-xl flex items-center justify-center border-2 border-blue-300 bg-surface-50 shadow-sm">
                    <AgentIcons agentName={selectedAgent?.name || ''} size="w-6 h-6" />
                  </div>
                  <div class="flex-1">
                    <div class="text-lg font-semibold text-surface-900 ">{selectedAgent?.name || 'Loading...'}</div>
                    <div class="text-sm font-medium text-blue-600">{selectedAgent?.role || ''}</div>
                    <div class="text-xs text-surface-600  mt-1 max-w-md truncate">{selectedAgent?.description || ''}</div>
                  </div>
                </div>
                
                <!-- Executive/Oversight Mode Toggle (only for Ali) -->
                {#if selectedAgent?.name === 'Ali'}
                  <div class="flex items-center space-x-2 bg-surface-50 border border-surface-300  rounded-xl px-4 py-2 shadow-sm">
                    <span class="text-xs font-medium text-surface-600 ">View Mode:</span>
                    <button
                      on:click={() => isOversightMode = false}
                      on:keydown={(e) => (e.key === 'Enter' || e.key === ' ') ? (e.preventDefault(), isOversightMode = false) : null}
                      class="px-3 py-1.5 text-xs font-medium rounded-lg transition-all duration-200 {!isOversightMode ? 'bg-blue-500 text-white shadow-sm' : 'text-surface-600  hover:text-blue-600 hover:bg-blue-50'}"
                      aria-label="Switch to Executive view mode"
                      aria-pressed="{!isOversightMode}"
                      tabindex="0"
                    >
                      Executive
                    </button>
                    <button
                      on:click={() => isOversightMode = true}
                      on:keydown={(e) => (e.key === 'Enter' || e.key === ' ') ? (e.preventDefault(), isOversightMode = true) : null}
                      class="px-3 py-1.5 text-xs font-medium rounded-lg transition-all duration-200 {isOversightMode ? 'bg-purple-500 text-white shadow-sm' : 'text-surface-600  hover:text-purple-600 hover:bg-purple-50'}"
                      aria-label="Switch to Oversight view mode"
                      aria-pressed="{isOversightMode}"
                      tabindex="0"
                    >
                      Oversight
                    </button>
                  </div>
                {/if}
              </div>
            </div>
            
            <!-- Enhanced Messages / Oversight Timeline -->
            <div bind:this={messagesContainer} class="flex-1 overflow-y-auto p-6 space-y-6">
              
              {#if !isOversightMode || selectedAgent?.name !== 'Ali'}
                <!-- Executive Mode: Regular Messages -->
                {#each messages as message}
                  <div class="flex {message.type === 'user' ? 'justify-end' : 'justify-start'}">
                    <div class="max-w-2xl">
                      {#if message.type === 'user'}
                        <div class="bg-gradient-to-r from-blue-500 to-blue-600 text-white p-4 rounded-2xl rounded-br-md shadow-sm">
                          <div class="font-medium mb-2 opacity-90 text-sm flex items-center">
                            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
                            </svg>
                            You
                          </div>
                          <div class="text-sm leading-relaxed">
                            <MarkdownRenderer content={message.content} />
                          </div>
                        </div>
                      {:else}
                        <div class="bg-gradient-to-r from-gray-50 to-blue-50 p-5 rounded-2xl rounded-bl-md border border-gray-100 shadow-sm">
                          <div class="flex items-center space-x-3 mb-3">
                            <div class="w-8 h-8 rounded-lg flex items-center justify-center border-2 border-blue-200 bg-surface-50">
                              <AgentIcons agentName={selectedAgent?.name || ''} size="w-4 h-4" />
                            </div>
                            <div class="flex items-center space-x-2">
                              <span class="font-semibold text-surface-900  text-sm">{selectedAgent?.name || ''}</span>
                              <span class="text-xs text-blue-600 bg-blue-100 px-2 py-1 rounded-full">{selectedAgent?.role || ''}</span>
                            </div>
                          </div>
                          <div class="text-surface-800  text-sm leading-relaxed">
                            <MarkdownRenderer content={message.content} />
                          </div>
                        </div>
                      {/if}
                    </div>
                  </div>
                {/each}
                
                {#if isLoading}
                  <div class="flex justify-start">
                    <div class="bg-gradient-to-r from-gray-50 to-blue-50 p-5 rounded-2xl border border-gray-100 max-w-2xl shadow-sm">
                      <div class="flex items-center space-x-3 mb-3">
                        <div class="w-8 h-8 rounded-lg flex items-center justify-center border-2 border-blue-200 bg-surface-50">
                          <AgentIcons agentName={selectedAgent?.name || ''} size="w-4 h-4" />
                        </div>
                        <span class="text-sm text-surface-600  font-medium">{selectedAgent?.name || 'Agent'} is thinking...</span>
                      </div>
                      <div class="flex space-x-2">
                        <div class="w-3 h-3 bg-blue-400 rounded-full animate-bounce"></div>
                        <div class="w-3 h-3 bg-blue-400 rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
                        <div class="w-3 h-3 bg-blue-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
                      </div>
                    </div>
                  </div>
                {/if}
              {:else}
                <!-- Oversight Mode: Timeline with Agent Iterations -->
                <div class="oversight-timeline">
                  <h3 class="text-lg font-semibold text-surface-800  mb-6 flex items-center">
                    <div class="w-3 h-3 bg-purple-600 rounded-full mr-3 animate-pulse"></div>
                    Oversight Mode: Team Coordination Timeline
                  </h3>
                  
                  <!-- User Message -->
                  {#each messages.filter(m => m.type === 'user') as userMessage}
                    <div class="timeline-item mb-8">
                      <div class="flex items-start space-x-4">
                        <div class="w-10 h-10 bg-gradient-to-r from-blue-500 to-blue-600 rounded-full flex items-center justify-center shadow-sm">
                          <span class="text-white text-sm font-bold">You</span>
                        </div>
                        <div class="flex-1 bg-gradient-to-r from-blue-50 to-indigo-50 border-l-4 border-blue-500 p-5 rounded-r-2xl shadow-sm">
                          <div class="font-semibold text-blue-900 text-sm mb-2">Your Request</div>
                          <div class="text-blue-800 text-sm">
                            <MarkdownRenderer content={userMessage.content} />
                          </div>
                        </div>
                      </div>
                    </div>
                  {/each}
                  
                  <!-- Agent Iterations -->
                  {#each oversightIterations as iteration, i}
                    <div class="timeline-item mb-6 relative">
                      <!-- Timeline connector -->
                      {#if i < oversightIterations.length - 1}
                        <div class="absolute left-5 top-14 w-0.5 h-12 bg-surface-200"></div>
                      {/if}
                      
                      <div class="flex items-start space-x-4">
                        <!-- Agent Avatar with Status -->
                        <div class="relative">
                          <div class="w-10 h-10 rounded-full flex items-center justify-center border-2 shadow-sm" style="background-color: {iteration.color}20; border-color: {iteration.color}">
                            <AgentIcons agentName={iteration.agent_name} size="w-5 h-5" />
                          </div>
                          
                          <!-- Status Indicator -->
                          {#if iteration.status === 'thinking'}
                            <div class="absolute -top-1 -right-1 w-4 h-4 bg-yellow-400 rounded-full animate-pulse border-2 border-surface-950"></div>
                          {:else if iteration.status === 'completed'}
                            <div class="absolute -top-1 -right-1 w-4 h-4 bg-green-500 rounded-full border-2 border-surface-950">
                              <svg class="w-2.5 h-2.5 text-white absolute top-0.5 left-0.5" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
                              </svg>
                            </div>
                          {:else if iteration.status === 'active'}
                            <div class="absolute -top-1 -right-1 w-4 h-4 bg-blue-500 rounded-full border-2 border-surface-950 animate-bounce"></div>
                          {/if}
                        </div>
                        
                        <!-- Agent Content -->
                        <div class="flex-1 border-l-4 p-4 rounded-r-2xl shadow-sm" style="background-color: {iteration.color}05; border-left-color: {iteration.color}">
                          <div class="flex items-center space-x-3 mb-3">
                            <span class="font-semibold text-sm" style="color: {iteration.color}">{iteration.agent_name}</span>
                            <span class="text-xs text-surface-500 bg-surface-200  px-2 py-1 rounded-full">{iteration.agent_role}</span>
                            <div class="text-xs px-3 py-1 rounded-full font-medium" style="background-color: {iteration.color}20; color: {iteration.color}">
                              Turn {iteration.turn}
                            </div>
                          </div>
                          
                          {#if iteration.status === 'thinking'}
                            <div class="text-sm text-surface-600  italic">{iteration.message || `${iteration.agent_name} is analyzing your request...`}</div>
                          {:else}
                            <div class="text-sm text-surface-800  leading-relaxed">{iteration.content}</div>
                          {/if}
                          
                          <div class="text-xs text-gray-400 mt-3 flex items-center">
                            <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                            </svg>
                            {new Date(iteration.timestamp).toLocaleTimeString()}
                          </div>
                        </div>
                      </div>
                    </div>
                  {/each}
                  
                  <!-- Loading state in oversight mode -->
                  {#if isLoading}
                    <div class="timeline-item mb-6">
                      <div class="flex items-start space-x-4">
                        <div class="w-10 h-10 bg-surface-200 rounded-full flex items-center justify-center animate-pulse">
                          <AgentIcons agentName="Ali" size="w-5 h-5" />
                        </div>
                        <div class="flex-1 bg-surface-100  border-l-4 border-surface-300  p-4 rounded-r-2xl">
                          <div class="text-sm text-surface-600  font-medium">Ali is coordinating the team response...</div>
                          <div class="flex space-x-2 mt-3">
                            <div class="w-3 h-3 bg-purple-400 rounded-full animate-bounce"></div>
                            <div class="w-3 h-3 bg-purple-400 rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
                            <div class="w-3 h-3 bg-purple-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
                          </div>
                        </div>
                      </div>
                    </div>
                  {/if}
                </div>
              {/if}
            </div>
            
            <!-- Enhanced Input Section -->
            <div class="p-6 border-t border-surface-300  bg-gradient-to-r from-gray-50 to-blue-50">
              <div class="flex space-x-4">
                <textarea
                  bind:value={currentMessage}
                  on:keydown={handleKeyPress}
                  placeholder="Ask {selectedAgent?.name || 'the agent'} about strategy, analysis, or anything in their expertise area..."
                  class="flex-1 resize-none border border-surface-400  rounded-xl px-4 py-3 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-surface-50 shadow-sm"
                  rows="3"
                  disabled={isLoading}
                  aria-label="Type your message to {selectedAgent?.name || 'the agent'}"
                ></textarea>
                <button
                  on:click={sendMessage}
                  on:keydown={(e) => (e.key === 'Enter' || e.key === ' ') && !(!currentMessage.trim() || isLoading) ? (e.preventDefault(), sendMessage()) : null}
                  disabled={!currentMessage.trim() || isLoading}
                  class="px-6 py-3 bg-gradient-to-r from-blue-500 to-blue-600 text-white font-medium rounded-xl hover:from-blue-600 hover:to-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-sm hover:shadow-md transform hover:scale-105"
                  aria-label="Send message to {selectedAgent?.name || 'agent'}"
                >
                  <div class="flex items-center space-x-2">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path>
                    </svg>
                    <span>Send</span>
                  </div>
                </button>
              </div>
              <div class="text-xs text-surface-500 mt-3 flex items-center justify-center">
                <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                Press Shift+Enter for new line, Enter to send
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Hire New Agent Modal -->
    {#if showHireForm}
      <div class="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="modal-title">
        <div class="modal-content max-w-md">
          <!-- Modal Header -->
          <div class="modal-header">
            <div class="flex items-center justify-between">
              <h2 id="modal-title" class="text-lg font-medium text-surface-900 ">Hire New Agent</h2>
              <button
                on:click={() => showHireForm = false}
                on:keydown={(e) => (e.key === 'Enter' || e.key === ' ') ? (e.preventDefault(), showHireForm = false) : null}
                class="text-surface-600  hover:text-surface-900  transition-colors"
                aria-label="Close modal"
                tabindex="0"
              >
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
              </button>
            </div>
          </div>
          
          <!-- Modal Body -->
          <div class="modal-body">
            {#if !showPreview}
              <!-- Initial Form -->
              <form on:submit|preventDefault={generateAgent} class="space-y-4">
                <!-- Agent Name -->
                <div>
                  <label for="agent-name" class="form-label">
                    Agent Name *
                  </label>
                  <input
                    id="agent-name"
                    type="text"
                    bind:value={newAgentForm.name}
                    placeholder="e.g., Mario, Elena, Giorgio..."
                    class="input-field"
                    required
                  />
                </div>

                <!-- Role -->
                <div>
                  <label for="agent-role" class="form-label">
                    Role *
                  </label>
                  <input
                    id="agent-role"
                    type="text"
                    bind:value={newAgentForm.role}
                    placeholder="e.g., Marketing Manager, Data Analyst..."
                    class="input-field"
                    required
                  />
                </div>

                <!-- Description -->
                <div>
                  <label for="agent-description" class="form-label">
                    Description *
                  </label>
                  <textarea
                    id="agent-description"
                    bind:value={newAgentForm.description}
                    placeholder="Brief description of what this agent does..."
                    rows="2"
                    class="input-field resize-none"
                    required
                  ></textarea>
                </div>

                <!-- Specialty -->
                <div>
                  <label for="agent-specialty" class="form-label">
                    Specialty *
                  </label>
                  <input
                    id="agent-specialty"
                    type="text"
                    bind:value={newAgentForm.specialty}
                    placeholder="e.g., Social media, financial planning..."
                    class="input-field"
                    required
                  />
                </div>

                <!-- Personality -->
                <div>
                  <label for="agent-personality" class="form-label">
                    Personality
                  </label>
                  <input
                    id="agent-personality"
                    type="text"
                    bind:value={newAgentForm.personality}
                    placeholder="e.g., Creative, analytical, detail-oriented..."
                    class="input-field"
                  />
                </div>

                <!-- Error Messages -->
                {#if creationError}
                  <div class="p-3 bg-red-50 border border-red-200 rounded-lg">
                    <p class="text-sm text-red-700">{creationError}</p>
                  </div>
                {/if}

                <!-- Buttons -->
                <div class="flex space-x-3 pt-4">
                  <button
                    type="button"
                    on:click={cancelAgentCreation}
                    on:keydown={(e) => (e.key === 'Enter' || e.key === ' ') && !isGeneratingAgent ? (e.preventDefault(), cancelAgentCreation()) : null}
                    class="btn-secondary flex-1"
                    disabled={isGeneratingAgent}
                    aria-label="Cancel agent creation"
                      >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    class="btn-primary flex-1"
                    disabled={isGeneratingAgent}
                    aria-label="Generate agent with AI"
                      >
                    {#if isGeneratingAgent}
                      <div class="flex items-center justify-center space-x-2">
                        <div class="w-4 h-4 border-2 border-surface-950 border-t-transparent rounded-full animate-spin"></div>
                        <span>AI Creating...</span>
                      </div>
                    {:else}
                      ✨ Generate with AI
                    {/if}
                  </button>
                </div>
                
                <div class="caption text-center pt-2">
                  AI will create a complete job description aligned with your team
                </div>
              </form>
              
            {:else}
              <!-- AI Generated Preview -->
              <div class="space-y-6">
                <div class="text-center">
                  <div class="inline-flex items-center space-x-2 px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-sm font-medium mb-4">
                    <span>🤖</span>
                    <span>AI Generated Agent</span>
                  </div>
                </div>
                
                {#if generatedAgent}
                  <!-- Agent Preview Card -->
                  <div class="border border-surface-300  rounded-lg p-4 bg-surface-100 ">
                    <div class="flex items-center space-x-3 mb-3">
                      <div class="w-10 h-10 rounded-lg flex items-center justify-center text-white font-bold text-lg" 
                           style="background-color: {generatedAgent.color || '#6366f1'}">
                        {generatedAgent.name?.charAt(0) || 'A'}
                      </div>
                      <div>
                        <h3 class="font-semibold text-surface-900 ">{generatedAgent.name}</h3>
                        <p class="text-sm text-blue-600">{generatedAgent.role}</p>
                      </div>
                    </div>
                    
                    <div class="space-y-3 text-sm">
                      <div>
                        <span class="font-medium text-surface-700 ">Description:</span>
                        <p class="text-surface-600  mt-1">{generatedAgent.description}</p>
                      </div>
                      
                      <div>
                        <span class="font-medium text-surface-700 ">Specialty:</span>
                        <p class="text-surface-600  mt-1">{generatedAgent.specialty}</p>
                      </div>
                      
                      <div>
                        <span class="font-medium text-surface-700 ">Personality:</span>
                        <p class="text-surface-600  mt-1">{generatedAgent.personality}</p>
                      </div>
                      
                      {#if generatedAgent.tools && generatedAgent.tools.length > 0}
                        <div>
                          <span class="font-medium text-surface-700 ">Tools:</span>
                          <div class="flex flex-wrap gap-1 mt-1">
                            {#each generatedAgent.tools.slice(0, 3) as tool}
                              <span class="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">{tool}</span>
                            {/each}
                            {#if generatedAgent.tools.length > 3}
                              <span class="px-2 py-1 bg-surface-200  text-surface-600  text-xs rounded-full">+{generatedAgent.tools.length - 3} more</span>
                            {/if}
                          </div>
                        </div>
                      {/if}
                    </div>
                  </div>
                {/if}

                <!-- Success Messages -->
                {#if creationSuccess}
                  <div class="p-3 bg-green-50 border border-green-200 rounded-lg">
                    <p class="text-sm text-green-700">Agent created successfully!</p>
                  </div>
                {/if}

                <!-- Error Messages -->
                {#if creationError}
                  <div class="p-3 bg-red-50 border border-red-200 rounded-lg">
                    <p class="text-sm text-red-700">{creationError}</p>
                  </div>
                {/if}

                <!-- Action Buttons -->
                <div class="flex space-x-3">
                  <button
                    type="button"
                    on:click={backToEdit}
                    on:keydown={(e) => (e.key === 'Enter' || e.key === ' ') && !isCreatingAgent ? (e.preventDefault(), backToEdit()) : null}
                    class="btn-secondary flex-1"
                    disabled={isCreatingAgent}
                    aria-label="Go back to edit agent details"
                      >
                  ← Edit Details
                </button>
                <button
                  type="button"
                  on:click={createFinalAgent}
                  on:keydown={(e) => (e.key === 'Enter' || e.key === ' ') && !isCreatingAgent ? (e.preventDefault(), createFinalAgent()) : null}
                  class="btn-primary flex-1 bg-green-500 hover:bg-green-600 disabled:bg-green-300"
                  disabled={isCreatingAgent}
                  aria-label="Hire this agent"
                      >
                  {#if isCreatingAgent}
                    <div class="flex items-center justify-center space-x-2">
                      <div class="w-4 h-4 border-2 border-surface-950 border-t-transparent rounded-full animate-spin"></div>
                      <span>Creating...</span>
                    </div>
                  {:else}
                    ✅ Hire This Agent
                  {/if}
                </button>
              </div>
            </div>
          {/if}
        </div>
      </div>
    </div>
  {/if}
  </div>
</div>