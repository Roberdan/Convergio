<!-- 
🚧 ROADMAP: Agent Management - Advanced CRUD Operations
======================================================

This feature is planned for future implementation and includes:
- Complete agent CRUD (Create, Read, Update, Delete) operations  
- Real-time agent editor with syntax highlighting
- Advanced filtering and search capabilities
- Agent tier management and categorization
- Hot-reloading of agent definitions
- Visual agent relationship mapping

Current Status: COMMENTED OUT for MVP simplification
Timeline: Phase 2 development (Q2 2025)
Dependencies: Agent definition standardization, advanced UI components
-->

<script lang="ts">
	import { onMount } from 'svelte';
	import { writable, type Writable } from 'svelte/store';
	import type { Agent } from '$lib/services/agentsService';
	// import AgentEditor from '$lib/components/AgentEditor.svelte';
	
	// Stores with proper typing
	let agents: Writable<Agent[]> = writable([]);
	let selectedAgent: Writable<Agent | null> = writable(null);
	let showEditor = writable(false);
	let isNewAgent = writable(false);
	
	// UI State
	let isLoading = false;
	let searchQuery = '';
	let selectedTier = '';
	let sortBy = 'name';
	let sortOrder = 'asc';
	let notification: { message: string; type: 'success' | 'error' | 'info' } | null = null;
	
	// Reactive filtered agents
	$: filteredAgents = $agents
		.filter(agent => {
			const matchesSearch = !searchQuery || 
				agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
				(agent.description && agent.description.toLowerCase().includes(searchQuery.toLowerCase()));
			const matchesTier = !selectedTier || agent.tier === selectedTier;
			return matchesSearch && matchesTier;
		})
		.sort((a, b) => {
			const aVal = (a as any)[sortBy] || '';
			const bVal = (b as any)[sortBy] || '';
			const compareResult = aVal < bVal ? -1 : aVal > bVal ? 1 : 0;
			return sortOrder === 'asc' ? compareResult : -compareResult;
		});
	
	$: availableTiers = [...new Set($agents.map(agent => agent.tier).filter(Boolean))].sort();
	
	onMount(async () => {
		await loadAgents();
	});
	
	async function loadAgents() {
		isLoading = true;
		try {
			const response = await fetch('/api/v1/agent-management/agents');
			if (!response.ok) throw new Error('Failed to load agents');
			
			const data = await response.json();
			agents.set(data.agents);
		} catch {
			// Silent failure
			showNotification('Failed to load agents', 'error');
		} finally {
			isLoading = false;
		}
	}
	
	async function createNewAgent() {
		selectedAgent.set(null);
		isNewAgent.set(true);
		showEditor.set(true);
	}

	async function editAgent(agent: Agent) {
		selectedAgent.set(agent);
		isNewAgent.set(false);
		showEditor.set(true);
	}

	async function deleteAgent(agent: Agent) {
		if (!confirm(`Are you sure you want to delete agent "${agent.name}"? This action cannot be undone.`)) {
			return;
		}
		
		try {
			const response = await fetch(`/api/v1/agent-management/agents/${agent.agent_key}`, {
				method: 'DELETE'
			});
			
			if (!response.ok) throw new Error('Failed to delete agent');
			
			const result = await response.json();
			showNotification(result.message, 'success');
			await loadAgents();
		} catch {
			// Silent failure
			showNotification('Failed to delete agent', 'error');
		}
	}
	
	async function hotReloadAgents() {
		try {
			const response = await fetch('/api/v1/agent-management/agents/hot-reload', {
				method: 'POST'
			});
			
			if (!response.ok) throw new Error('Failed to reload agents');
			
			const result = await response.json();
			showNotification(`${result.message} (${result.agent_count} agents)`, 'success');
			await loadAgents();
		} catch {
			// Silent failure
			showNotification('Failed to reload agents', 'error');
		}
	}
	
	function closeEditor() {
		showEditor.set(false);
		selectedAgent.set(null);
	}
	
	function showNotification(message: string, type: 'success' | 'error' | 'info' = 'info') {
		notification = { message, type };
		setTimeout(() => notification = null, 5000);
	}

	function getTierColor(tier: string): string {
		const colors: Record<string, string> = {
			'Strategic Leadership': 'bg-purple-100 text-purple-800',
			'Technology & Engineering': 'bg-blue-100 text-blue-800',
			'User Experience & Design': 'bg-green-100 text-green-800',
			'Data & Analytics': 'bg-yellow-100 text-yellow-800',
			'Execution & Operations': 'bg-orange-100 text-orange-800',
			'Business & People': 'bg-pink-100 text-pink-800',
			'Compliance & Risk': 'bg-red-100 text-red-800',
			'Specialized Services': 'bg-surface-100 text-surface-800'
		};
		return colors[tier] || 'bg-surface-100 text-surface-800';
	}
	
	function getAgentInitials(name: string) {
		return name.split('-')
			.map(word => word[0]?.toUpperCase())
			.join('')
			.slice(0, 2);
	}
</script>

<style>
	.sr-only {
		position: absolute;
		width: 1px;
		height: 1px;
		padding: 0;
		margin: -1px;
		overflow: hidden;
		clip: rect(0, 0, 0, 0);
		white-space: nowrap;
		border: 0;
	}
</style>

<svelte:head>
	<title>Agent Management | Convergio</title>
</svelte:head>

{#if $showEditor}
	<div class="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-start justify-center overflow-y-auto">
		<div class="bg-white rounded-lg shadow-xl m-4 w-full max-w-6xl max-h-screen overflow-y-auto">
			<div class="sticky top-0 bg-white border-b px-6 py-4 flex justify-between items-center">
				<h2 class="text-xl font-semibold">
					{$isNewAgent ? 'Create New Agent' : `Edit ${$selectedAgent?.name || ''}`}
				</h2>
				<button
					on:click={closeEditor}
					class="p-2 hover:bg-surface-100 rounded-lg transition-colors"
					aria-label="Close editor"
				>
					<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
					</svg>
				</button>
			</div>
			<div class="p-0">
				<!-- AgentEditor component will be added in Phase 2 -->
				<div class="p-4 text-surface-500">
					Agent editor component coming soon...
				</div>
			</div>
		</div>
	</div>
{/if}

<div class="min-h-screen bg-surface-50">
	<!-- Header -->
	<div class="bg-white shadow-sm border-b">
		<div class="max-w-7xl mx-auto px-6 py-6">
			<div class="flex justify-between items-start">
				<div>
					<h1 class="text-3xl font-bold text-surface-900 mb-2">Agent Management</h1>
					<p class="text-surface-600">Manage your AI agent ecosystem with CRUD operations and real-time assistance from Ali</p>
				</div>
				<div class="flex space-x-3">
					<button
						on:click={hotReloadAgents}
						class="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors flex items-center"
					>
						<svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
						</svg>
						Hot Reload
					</button>
					<button
						on:click={createNewAgent}
						class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center"
					>
						<svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/>
						</svg>
						Create Agent
					</button>
				</div>
			</div>
		</div>
	</div>

	<!-- Notification -->
	{#if notification}
		<div class="fixed top-4 right-4 z-40 max-w-sm">
			<div class="rounded-lg shadow-lg border p-4"
				 class:bg-green-50={notification.type === 'success'}
				 class:border-green-200={notification.type === 'success'}
				 class:text-green-800={notification.type === 'success'}
				 class:bg-red-50={notification.type === 'error'}
				 class:border-red-200={notification.type === 'error'}
				 class:text-red-800={notification.type === 'error'}
				 class:bg-blue-50={notification.type === 'info'}
				 class:border-blue-200={notification.type === 'info'}
				 class:text-blue-800={notification.type === 'info'}>
				<div class="flex justify-between items-start">
					<p class="text-sm font-medium">{notification.message}</p>
					<button
						on:click={() => notification = null}
						class="ml-2 text-gray-400 hover:text-surface-600"
						aria-label="Close notification"
					>
						<svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
							<path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
						</svg>
					</button>
				</div>
			</div>
		</div>
	{/if}

	<!-- Filters and Search -->
	<div class="max-w-7xl mx-auto px-6 py-6">
		<div class="bg-white rounded-lg shadow-sm border p-6 mb-6">
			<div class="grid grid-cols-1 md:grid-cols-4 gap-4">
				<div>
					<label for="search-agents" class="block text-sm font-medium text-surface-600 mb-1">Search Agents</label>
					<input
						id="search-agents"
						type="text"
						bind:value={searchQuery}
						placeholder="Search by name or description..."
						class="w-full px-3 py-2 border border-surface-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
						aria-describedby="search-help"
					/>
					<div id="search-help" class="sr-only">Search agents by name or description</div>
				</div>
				<div>
					<label for="filter-tier" class="block text-sm font-medium text-surface-600 mb-1">Filter by Tier</label>
					<select
						id="filter-tier"
						bind:value={selectedTier}
						class="w-full px-3 py-2 border border-surface-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
						aria-describedby="tier-help"
					>
						<option value="">All Tiers</option>
						{#each availableTiers as tier}
							<option value={tier}>{tier}</option>
						{/each}
					</select>
					<div id="tier-help" class="sr-only">Filter agents by organizational tier</div>
				</div>
				<div>
					<label for="sort-by" class="block text-sm font-medium text-surface-600 mb-1">Sort By</label>
					<select
						id="sort-by"
						bind:value={sortBy}
						class="w-full px-3 py-2 border border-surface-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
						aria-describedby="sort-help"
					>
						<option value="name">Name</option>
						<option value="tier">Tier</option>
						<option value="tools_count">Tools Count</option>
						<option value="expertise_count">Expertise Count</option>
					</select>
					<div id="sort-help" class="sr-only">Sort agents by selected criteria</div>
				</div>
				<div>
					<label for="sort-order" class="block text-sm font-medium text-surface-600 mb-1">Order</label>
					<select
						id="sort-order"
						bind:value={sortOrder}
						class="w-full px-3 py-2 border border-surface-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
						aria-describedby="order-help"
					>
						<option value="asc">Ascending</option>
						<option value="desc">Descending</option>
					</select>
					<div id="order-help" class="sr-only">Choose ascending or descending order</div>
				</div>
			</div>
		</div>

		<!-- Agents Grid -->
		{#if isLoading}
			<div class="flex items-center justify-center py-12" role="status" aria-live="polite">
				<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" aria-hidden="true"></div>
				<span class="ml-3 text-surface-600">Loading agents...</span>
			</div>
		{:else}
			<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
				{#each filteredAgents as agent (agent.agent_key)}
					<article class="bg-white rounded-lg shadow-sm border hover:shadow-md transition-shadow" aria-labelledby="agent-{agent.agent_key}-name">
						<!-- Agent Header -->
						<div class="p-4 border-b">
							<div class="flex items-center space-x-3 mb-3">
								<div 
									class="w-12 h-12 rounded-lg flex items-center justify-center text-white font-bold text-lg"
									style="background-color: #4A90E2"
									role="img"
									aria-label="Agent avatar for {agent.name}"
								>
									{getAgentInitials(agent.name)}
								</div>
								<div class="flex-1 min-w-0">
									<h3 id="agent-{agent.agent_key}-name" class="font-semibold text-surface-900 truncate" title={agent.name}>
										{agent.name.replace(/-/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase())}
									</h3>
									<p class="text-sm text-surface-500 truncate" title={agent.description || 'No description available'}>
										{agent.description || 'No description available'}
									</p>
								</div>
							</div>
							<div class="flex items-center justify-between">
								<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {getTierColor(agent.tier || 'junior')}" aria-label="Agent tier: {agent.tier || 'junior'}">
									{agent.tier || 'junior'}
								</span>
								<div class="flex space-x-1" aria-label="Agent capabilities">
									<span class="text-xs text-surface-500">{agent.tools_count || 0} tools</span>
									<span class="text-xs text-gray-400" aria-hidden="true">•</span>
									<span class="text-xs text-surface-500">{agent.expertise_count || 0} areas</span>
								</div>
							</div>
						</div>
						
						<!-- Agent Actions -->
						<div class="p-4">
							<div class="flex space-x-2">
								<button
									on:click={() => editAgent(agent)}
									class="flex-1 px-3 py-2 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition-colors flex items-center justify-center"
									aria-label="Edit agent {agent.name}"
								>
									<svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
									</svg>
									Edit
								</button>
								<button
									on:click={() => deleteAgent(agent)}
									class="px-3 py-2 border border-red-300 text-red-700 text-sm rounded hover:bg-red-50 transition-colors flex items-center justify-center"
									aria-label="Delete agent {agent.name}"
								>
									<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
									</svg>
								</button>
							</div>
						</div>
					</article>
				{/each}
			</div>
			
			{#if filteredAgents.length === 0}
				<div class="text-center py-12" role="status" aria-live="polite">
					<svg class="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true" role="presentation">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2 2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"/>
					</svg>
					<h3 class="text-lg font-medium text-surface-900 mb-2">No agents found</h3>
					<p class="text-surface-500">Try adjusting your search or filter criteria.</p>
				</div>
			{/if}
		{/if}

		<!-- Summary Stats -->
		<section class="mt-8 bg-white rounded-lg shadow-sm border p-6" aria-labelledby="stats-heading">
			<h2 id="stats-heading" class="text-lg font-semibold mb-4">Agent Statistics</h2>
			<div class="grid grid-cols-2 md:grid-cols-4 gap-6" role="list">
				<div class="text-center" role="listitem">
					<div class="text-2xl font-bold text-blue-600" aria-label="{$agents.length} total agents">{$agents.length}</div>
					<div class="text-sm text-surface-500">Total Agents</div>
				</div>
				<div class="text-center" role="listitem">
					<div class="text-2xl font-bold text-green-600" aria-label="{filteredAgents.length} filtered results">{filteredAgents.length}</div>
					<div class="text-sm text-surface-500">Filtered Results</div>
				</div>
				<div class="text-center" role="listitem">
					<div class="text-2xl font-bold text-purple-600" aria-label="{availableTiers.length} available tiers">{availableTiers.length}</div>
					<div class="text-sm text-surface-500">Available Tiers</div>
				</div>
				<div class="text-center" role="listitem">
					<div class="text-2xl font-bold text-orange-600" aria-label="{$agents.reduce((sum, agent) => sum + (agent.tools_count || 0), 0)} total tools">
						{$agents.reduce((sum, agent) => sum + (agent.tools_count || 0), 0)}
					</div>
					<div class="text-sm text-surface-500">Total Tools</div>
				</div>
			</div>
		</section>
	</div>
</div>