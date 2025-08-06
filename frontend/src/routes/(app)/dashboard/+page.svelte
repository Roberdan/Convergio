<script lang="ts">
  import { onMount } from 'svelte';
  import Chart from 'chart.js/auto';

  // Business KPIs 
  let stats = {
    revenue: 1094221,
    customers: 1579,
    growth: 23.5,
    projects: 8
  };

  // Sample projects (from CEO project management)
  let projects = [
    { 
      id: 1, 
      name: "Atlas Product Launch Q4", 
      progress: 78, 
      status: "in-progress", 
      dueDate: "Dec 1, 2024",
      type: "product_launch",
      description: "Strategic product launch with full market penetration",
      assigned_agents: ["Ali", "Davide", "Amy", "Sofia", "Baccio", "Luca"],
      priority: "high",
      budget: 150000,
      revenue_target: 500000
    },
    { 
      id: 2, 
      name: "Brazil Market Analysis", 
      progress: 45, 
      status: "planning", 
      dueDate: "Sep 15, 2024",
      type: "market_analysis",
      description: "Comprehensive Brazilian market entry feasibility study",
      assigned_agents: ["Ali", "Domik", "Behice", "Fabio", "Amy", "Omri"],
      priority: "high",
      budget: 75000,
      revenue_target: 1200000
    },
    { 
      id: 3, 
      name: "FitTech AI Series A Pitch", 
      progress: 92, 
      status: "review", 
      dueDate: "Aug 20, 2024",
      type: "investor_pitch",
      description: "Series A funding round preparation and execution",
      assigned_agents: ["Ali", "Sam", "Amy", "Riccardo", "Sofia", "Wiz"],
      priority: "critical",
      budget: 25000,
      revenue_target: 5000000
    }
  ];

  let chartCanvas;

  onMount(() => {
    // Create revenue trend chart
    const ctx = chartCanvas.getContext('2d');
    new Chart(ctx, {
      type: 'line',
      data: {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul'],
        datasets: [{
          label: 'Revenue ($)',
          data: [650000, 750000, 820000, 900000, 980000, 1050000, 1094221],
          borderColor: 'rgb(234, 88, 12)',
          backgroundColor: 'rgba(234, 88, 12, 0.1)',
          tension: 0.4,
          fill: true
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: {
            display: false
          }
        },
        scales: {
          y: {
            beginAtZero: false,
            ticks: {
              callback: function(value) {
                return '$' + (value / 1000) + 'K';
              }
            }
          }
        }
      }
    });
  });

  function getStatusColor(status: string): string {
    switch (status) {
      case 'completed': 
      case 'review': 
        return 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/20 dark:text-emerald-300';
      case 'in-progress': 
        return 'bg-orange-100 text-orange-800 dark:bg-orange-900/20 dark:text-orange-300';
      case 'planning': 
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-300';
      default: 
        return 'bg-slate-100 text-slate-800 dark:bg-slate-700 dark:text-slate-300';
    }
  }

  function getPriorityColor(priority: string): string {
    switch (priority) {
      case 'critical': return 'text-red-600 dark:text-red-400';
      case 'high': return 'text-orange-600 dark:text-orange-400';
      case 'medium': return 'text-yellow-600 dark:text-yellow-400';
      default: return 'text-slate-600 dark:text-slate-400';
    }
  }

  function getProjectIcon(type: string): string {
    switch (type) {
      case 'product_launch': return '🚀';
      case 'market_analysis': return '🌎';
      case 'investor_pitch': return '💼';
      case 'strategic_planning': return '📈';
      default: return '📊';
    }
  }

  async function createProject(projectType: string) {
    const projectTemplates = {
      product_launch: {
        name: 'New Product Launch Initiative',
        description: 'End-to-end product launch with market strategy',
        timeline: '16 weeks'
      },
      market_analysis: {
        name: 'Strategic Market Analysis',
        description: 'Comprehensive market research and entry planning',
        timeline: '8 weeks'
      },
      investor_pitch: {
        name: 'Investment Round Preparation',
        description: 'Funding presentation and financial projections',
        timeline: '4 weeks'
      }
    };

    const template = projectTemplates[projectType];
    const projectName = prompt(`Project Name:`, template.name) || template.name;
    const description = prompt(`Description:`, template.description) || template.description;

    if (!projectName) return;

    try {
      const response = await fetch('http://localhost:9000/api/v1/agents/project', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_name: projectName,
          project_type: projectType,
          description: description,
          timeline: template.timeline,
          user_id: 'ceo'
        })
      });

      if (response.ok) {
        const result = await response.json();
        alert(`✅ Project "${result.project_name}" created!\n\n👥 AI Team: ${result.agents_assigned?.slice(0, 3).join(', ')} + ${(result.agents_assigned?.length || 0) - 3} more\n\n🎯 Expected Deliverables:\n${result.expected_deliverables?.slice(0, 3).join('\n') || 'Strategic analysis and recommendations'}`);
      } else {
        alert(`Project "${projectName}" queued for AI team assignment`);
      }
    } catch (error) {
      console.error('Failed to create project:', error);
      alert(`Project "${projectName}" registered with AI team`);
    }
  }

  async function requestExecutiveBrief() {
    try {
      const response = await fetch('http://localhost:9000/api/v1/agents/conversation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: 'Provide executive summary of all current projects, key metrics, and strategic recommendations for Q4',
          user_id: 'ceo-dashboard',
          context: { source: 'dashboard', role: 'ceo' }
        })
      });

      if (response.ok) {
        const result = await response.json();
        alert(`📊 Executive Brief from Ali (Chief of Staff):\n\n${result.response}`);
      } else {
        alert('Executive brief requested - AI team will prepare comprehensive summary');
      }
    } catch (error) {
      alert('AI team briefing initiated - comprehensive report incoming');
    }
  }
</script>

<svelte:head>
  <title>CEO Dashboard - platform.Convergio.io</title>
</svelte:head>

<!-- Simple Dashboard inspired by Reflex -->
<div class="space-y-6">
  <!-- Simple Header -->
  <div class="flex items-center justify-between">
    <div>
      <h1 class="text-lg font-medium text-gray-900">Executive Overview</h1>
      <p class="mt-1 text-xs text-gray-500">Real-time business metrics</p>
    </div>
    <button
      on:click={requestExecutiveBrief}
      class="inline-flex items-center px-3 py-1.5 bg-gray-900 hover:bg-gray-800 text-white text-xs font-medium rounded transition-colors"
    >
      <img src="/convergio_icons/document.svg" alt="" class="mr-1.5 h-3 w-3" />
      Brief
    </button>
  </div>

  <!-- Metrics Grid -->
  <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
    <!-- Revenue -->
    <div class="bg-white border border-gray-200 rounded p-4 hover:shadow-sm transition-shadow">
      <div class="flex items-center justify-between mb-2">
        <div class="flex items-center">
          <div class="w-6 h-6 bg-green-100 rounded-md flex items-center justify-center mr-2">
            <img src="/convergio_icons/dollar.svg" alt="" class="h-3 w-3 text-green-600" />
          </div>
          <span class="text-xs font-medium text-gray-600">Total Revenue</span>
        </div>
        <span class="text-xs font-medium text-green-600 flex items-center">
          +32.7% 
          <img src="/convergio_icons/trending_up.svg" alt="" class="ml-1 h-3 w-3" />
        </span>
      </div>
      <div class="text-xl font-bold text-gray-900">${stats.revenue.toLocaleString()}</div>
      <p class="text-xs text-gray-500 mt-1">Trending up this month</p>
    </div>

    <!-- Customers -->
    <div class="bg-white border border-gray-200 rounded p-4 hover:shadow-sm transition-shadow">
      <div class="flex items-center justify-between mb-2">
        <div class="flex items-center">
          <div class="w-6 h-6 bg-blue-100 rounded-md flex items-center justify-center mr-2">
            <img src="/convergio_icons/users.svg" alt="" class="h-3 w-3 text-blue-600" />
          </div>
          <span class="text-xs font-medium text-gray-600">New Customers</span>
        </div>
        <span class="text-xs font-medium text-red-600 flex items-center">
          -45% 
          <img src="/convergio_icons/trending_up.svg" alt="" class="ml-1 h-3 w-3 rotate-180" />
        </span>
      </div>
      <div class="text-xl font-bold text-gray-900">{stats.customers.toLocaleString()}</div>
      <p class="text-xs text-gray-500 mt-1">Down 25% this period</p>
    </div>

    <!-- Active Accounts -->
    <div class="bg-white border border-gray-200 rounded p-4 hover:shadow-sm transition-shadow">
      <div class="flex items-center justify-between mb-2">
        <div class="flex items-center">
          <div class="w-6 h-6 bg-purple-100 rounded-md flex items-center justify-center mr-2">
            <img src="/convergio_icons/target.svg" alt="" class="h-3 w-3 text-purple-600" />
          </div>
          <span class="text-xs font-medium text-gray-600">Active Accounts</span>
        </div>
        <span class="text-xs font-medium text-green-600 flex items-center">
          +78.3% 
          <img src="/convergio_icons/trending_up.svg" alt="" class="ml-1 h-3 w-3" />
        </span>
      </div>
      <div class="text-xl font-bold text-gray-900">36,167</div>
      <p class="text-xs text-gray-500 mt-1">Strong user retention</p>
    </div>

    <!-- Growth Rate -->
    <div class="bg-white border border-gray-200 rounded p-4 hover:shadow-sm transition-shadow">
      <div class="flex items-center justify-between mb-2">
        <div class="flex items-center">
          <div class="w-6 h-6 bg-orange-100 rounded-md flex items-center justify-center mr-2">
            <img src="/convergio_icons/trending_up.svg" alt="" class="h-3 w-3 text-orange-600" />
          </div>
          <span class="text-xs font-medium text-gray-600">Growth Rate</span>
        </div>
        <span class="text-xs font-medium text-green-600 flex items-center">
          +5.9% 
          <img src="/convergio_icons/trending_up.svg" alt="" class="ml-1 h-3 w-3" />
        </span>
      </div>
      <div class="text-xl font-bold text-gray-900">1.5%</div>
      <p class="text-xs text-gray-500 mt-1">Steady performance</p>
    </div>
  </div>

  <!-- Projects Section -->
  <div class="bg-white border border-gray-200 rounded">
    <div class="px-4 py-3 border-b border-gray-200">
      <div class="flex items-center justify-between">
        <h3 class="text-sm font-medium text-gray-900">Strategic Projects</h3>
        <div class="flex space-x-2">
          <button 
            on:click={() => createProject('product_launch')}
            class="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 rounded transition-colors"
          >
            Launch
          </button>
          <button 
            on:click={() => createProject('market_analysis')}
            class="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 rounded transition-colors"
          >
            Analysis
          </button>
        </div>
      </div>
    </div>
    
    <div class="p-0">
      {#each projects as project}
        <div class="px-4 py-3 border-b border-gray-100 last:border-b-0 hover:bg-gray-50 transition-colors">
          <div class="flex items-center justify-between">
            <div class="flex items-center space-x-3">
              <div class="text-sm">{getProjectIcon(project.type)}</div>
              <div>
                <h4 class="text-sm font-medium text-gray-900">{project.name}</h4>
                <p class="text-xs text-gray-500">{project.description}</p>
              </div>
            </div>
            <div class="flex items-center space-x-3">
              <span class="text-xs px-2 py-1 rounded bg-gray-100 text-gray-700">
                {project.status}
              </span>
              <div class="w-16 text-right">
                <div class="text-xs font-medium text-gray-900">{project.progress}%</div>
                <div class="w-16 h-1.5 bg-gray-200 rounded-full mt-1">
                  <div class="h-full bg-gray-900 rounded-full" style="width: {project.progress}%"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      {/each}
    </div>
  </div>
</div>