<script lang="ts">
	import { onMount } from 'svelte';
	import { fade, slide } from 'svelte/transition';
	
	interface Workflow {
		workflow_id: string;
		name: string;
		description: string;
		category: string;
		complexity: string;
		estimated_duration_minutes: number;
		steps_count: number;
		success_rate: number;
		usage_count: number;
		tags: string[];
	}
	
	interface WorkflowExecution {
		execution_id: string;
		workflow_id: string;
		status: string;
		started_at: string;
		completed_at?: string;
		progress_percentage: number;
		current_step?: string;
		error_message?: string;
	}
	
	let workflows: Workflow[] = [];
	let executions: WorkflowExecution[] = [];
	let selectedWorkflow: Workflow | null = null;
	let isGenerating = false;
	let generationPrompt = '';
	let generationDomain = 'operations';
	let generationPriority = 'medium';
	let maxSteps = 10;
	let searchQuery = '';
	let filterDomain = '';
	let filterComplexity = '';
	let showGenerationPanel = false;
	let generationResult: any = null;
	let validationResult: any = null;
	
	// Stats for dashboard
	let stats = {
		totalWorkflows: 0,
		activeExecutions: 0,
		successRate: 0,
		avgDuration: 0
	};
	
	onMount(() => {
		(async () => {
			await loadWorkflows();
			await loadExecutions();
			updateStats();
		})();
		
		// Poll for execution updates
		const interval = setInterval(async () => {
			await loadExecutions();
		}, 5000);
		
		return () => clearInterval(interval);
	});
	
	async function loadWorkflows() {
		try {
			const response = await fetch('/api/v1/workflows/catalog');
			if (response.ok) {
				const data = await response.json();
				workflows = data.catalog || [];
			}
		} catch {
			// Silent failure
		}
	}
	
	async function loadExecutions() {
		try {
			const response = await fetch('/api/v1/workflows/executions/recent');
			if (response.ok) {
				const data = await response.json();
				executions = data.executions || [];
			}
		} catch {
			// Silent failure
		}
	}
	
	async function searchWorkflows() {
		try {
			const params = new URLSearchParams();
			if (searchQuery) params.append('query', searchQuery);
			if (filterDomain) params.append('domain', filterDomain);
			if (filterComplexity) params.append('complexity', filterComplexity);
			
			const response = await fetch(`/api/v1/workflows/search?${params}`);
			if (response.ok) {
				const data = await response.json();
				workflows = data.results || [];
			}
		} catch {
			// Silent failure
		}
	}
	
	async function validatePrompt() {
		if (!generationPrompt) return;
		
		try {
			const response = await fetch('/api/v1/workflows/validate', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ prompt: generationPrompt })
			});
			
			if (response.ok) {
				validationResult = await response.json();
			}
		} catch {
			// Silent failure
		}
	}
	
	async function generateWorkflow() {
		if (!generationPrompt) return;
		
		isGenerating = true;
		generationResult = null;
		
		try {
			const response = await fetch('/api/v1/workflows/generate', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					prompt: generationPrompt,
					business_domain: generationDomain,
					priority: generationPriority,
					max_steps: maxSteps,
					context: {}
				})
			});
			
			if (response.ok) {
				generationResult = await response.json();
				await loadWorkflows(); // Reload to show new workflow
				showGenerationPanel = false;
			} else {
				const error = await response.json();
				alert(`Generation failed: ${error.detail}`);
			}
		} catch {
			// Silent failure
			alert('Failed to generate workflow');
		} finally {
			isGenerating = false;
		}
	}
	
	async function executeWorkflow(workflowId: string) {
		const userRequest = prompt('Enter your request for this workflow:');
		if (!userRequest) return;
		
		try {
			const response = await fetch('/api/v1/workflows/execute', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					workflow_id: workflowId,
					user_request: userRequest,
					context: {}
				})
			});
			
			if (response.ok) {
				const result = await response.json();
				alert(`Workflow started! Execution ID: ${result.execution_id}`);
				await loadExecutions();
			} else {
				const error = await response.json();
				alert(`Execution failed: ${error.detail}`);
			}
		} catch {
			// Silent failure
			alert('Failed to execute workflow');
		}
	}
	
	async function cancelExecution(executionId: string) {
		if (!confirm('Cancel this execution?')) return;
		
		try {
			const response = await fetch(`/api/v1/workflows/execution/${executionId}/cancel`, {
				method: 'POST'
			});
			
			if (response.ok) {
				await loadExecutions();
			}
		} catch {
			// Silent failure
		}
	}
	
	function updateStats() {
		stats.totalWorkflows = workflows.length;
		stats.activeExecutions = executions.filter(e => e.status === 'running').length;
		
		const successfulWorkflows = workflows.filter(w => w.success_rate > 0);
		stats.successRate = successfulWorkflows.length > 0
			? successfulWorkflows.reduce((sum, w) => sum + w.success_rate, 0) / successfulWorkflows.length
			: 0;
		
		stats.avgDuration = workflows.length > 0
			? workflows.reduce((sum, w) => sum + w.estimated_duration_minutes, 0) / workflows.length
			: 0;
	}
	
	function getStatusColor(status: string): string {
		switch (status) {
			case 'completed': return 'text-green-600';
			case 'running': return 'text-blue-600';
			case 'failed': return 'text-red-600';
			case 'cancelled': return 'text-surface-600';
			default: return 'text-surface-500';
		}
	}
	
	function getComplexityColor(complexity: string): string {
		switch (complexity) {
			case 'low': return 'bg-green-100 text-green-800';
			case 'medium': return 'bg-yellow-100 text-yellow-800';
			case 'high': return 'bg-red-100 text-red-800';
			default: return 'bg-surface-100 text-surface-800';
		}
	}
</script>

<div class="container mx-auto px-4 py-8">
	<!-- Header -->
	<div class="mb-8">
		<h1 class="text-3xl font-bold text-surface-900 mb-2">
			GraphFlow Workflow Management
		</h1>
		<p class="text-surface-600">
			Generate, manage, and execute business workflows with AI-powered automation
		</p>
	</div>
	
	<!-- Stats Dashboard -->
	<div class="grid grid-cols-4 gap-4 mb-8">
		<div class="bg-white rounded-lg shadow p-6">
			<div class="text-sm text-surface-500 mb-1">Total Workflows</div>
			<div class="text-2xl font-bold text-surface-900">{stats.totalWorkflows}</div>
		</div>
		<div class="bg-white rounded-lg shadow p-6">
			<div class="text-sm text-surface-500 mb-1">Active Executions</div>
			<div class="text-2xl font-bold text-blue-600">{stats.activeExecutions}</div>
		</div>
		<div class="bg-white rounded-lg shadow p-6">
			<div class="text-sm text-surface-500 mb-1">Success Rate</div>
			<div class="text-2xl font-bold text-green-600">{(stats.successRate * 100).toFixed(1)}%</div>
		</div>
		<div class="bg-white rounded-lg shadow p-6">
			<div class="text-sm text-surface-500 mb-1">Avg Duration</div>
			<div class="text-2xl font-bold text-surface-900">{stats.avgDuration.toFixed(0)} min</div>
		</div>
	</div>
	
	<!-- Actions Bar -->
	<div class="bg-white rounded-lg shadow mb-6 p-4">
		<div class="flex items-center space-x-4">
			<button
				on:click={() => showGenerationPanel = !showGenerationPanel}
				class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
			>
				<span class="flex items-center">
					<svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
					</svg>
					Generate Workflow
				</span>
			</button>
			
			<div class="flex-1 flex items-center space-x-2">
				<input
					type="text"
					bind:value={searchQuery}
					placeholder="Search workflows..."
					class="flex-1 px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
					on:input={searchWorkflows}
				/>
				
				<select
					bind:value={filterDomain}
					on:change={searchWorkflows}
					class="px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
				>
					<option value="">All Domains</option>
					<option value="strategy">Strategy</option>
					<option value="operations">Operations</option>
					<option value="finance">Finance</option>
					<option value="marketing">Marketing</option>
					<option value="technology">Technology</option>
					<option value="hr">HR</option>
				</select>
				
				<select
					bind:value={filterComplexity}
					on:change={searchWorkflows}
					class="px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
				>
					<option value="">All Complexity</option>
					<option value="low">Low</option>
					<option value="medium">Medium</option>
					<option value="high">High</option>
				</select>
			</div>
		</div>
	</div>
	
	<!-- Generation Panel -->
	{#if showGenerationPanel}
		<div class="bg-white rounded-lg shadow mb-6 p-6" transition:slide>
			<h3 class="text-lg font-semibold mb-4">Generate New Workflow from Natural Language</h3>
			
			<div class="space-y-4">
				<div>
					<label for="workflow-description" class="block text-sm font-medium text-surface-600 mb-1">
						Workflow Description
					</label>
					<textarea
						id="workflow-description"
						bind:value={generationPrompt}
						on:blur={validatePrompt}
						placeholder="Describe the workflow you want to generate..."
						rows="4"
						class="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
					></textarea>
					
					{#if validationResult}
						<div class="mt-2 text-sm {validationResult.is_valid ? 'text-green-600' : 'text-red-600'}">
							{validationResult.is_valid ? '✓ Valid prompt' : `⚠ ${validationResult.reason}`}
						</div>
					{/if}
				</div>
				
				<div class="grid grid-cols-3 gap-4">
					<div>
						<label for="business-domain" class="block text-sm font-medium text-surface-600 mb-1">
							Business Domain
						</label>
						<select
							id="business-domain"
							bind:value={generationDomain}
							class="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
						>
							<option value="strategy">Strategy</option>
							<option value="operations">Operations</option>
							<option value="finance">Finance</option>
							<option value="marketing">Marketing</option>
							<option value="technology">Technology</option>
							<option value="hr">HR</option>
						</select>
					</div>
					
					<div>
						<label for="workflow-priority" class="block text-sm font-medium text-surface-600 mb-1">
							Priority
						</label>
						<select
							id="workflow-priority"
							bind:value={generationPriority}
							class="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
						>
							<option value="low">Low</option>
							<option value="medium">Medium</option>
							<option value="high">High</option>
							<option value="critical">Critical</option>
						</select>
					</div>
					
					<div>
						<label for="max-steps" class="block text-sm font-medium text-surface-600 mb-1">
							Max Steps
						</label>
						<input
							id="max-steps"
							type="number"
							bind:value={maxSteps}
							min="3"
							max="20"
							class="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
						/>
					</div>
				</div>
				
				<div class="flex justify-end space-x-2">
					<button
						on:click={() => showGenerationPanel = false}
						class="px-4 py-2 border border-surface-300 rounded-lg hover:bg-surface-50 transition-colors"
					>
						Cancel
					</button>
					<button
						on:click={generateWorkflow}
						disabled={!generationPrompt || isGenerating}
						class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
					>
						{isGenerating ? 'Generating...' : 'Generate Workflow'}
					</button>
				</div>
			</div>
		</div>
	{/if}
	
	<!-- Generation Result -->
	{#if generationResult}
		<div class="bg-green-50 border border-green-200 rounded-lg p-4 mb-6" transition:fade>
			<div class="flex items-start">
				<svg class="w-5 h-5 text-green-600 mt-0.5 mr-2" fill="currentColor" viewBox="0 0 20 20">
					<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
				</svg>
				<div class="flex-1">
					<h4 class="font-semibold text-green-900">Workflow Generated Successfully!</h4>
					<p class="text-sm text-green-700 mt-1">
						Created workflow "{generationResult.workflow.name}" with {generationResult.workflow.steps.length} steps.
						Estimated cost: ${generationResult.estimated_cost}
					</p>
				</div>
			</div>
		</div>
	{/if}
	
	<!-- Workflows Grid -->
	<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
		{#each workflows as workflow}
			<div class="bg-white rounded-lg shadow hover:shadow-lg transition-shadow p-6">
				<div class="mb-4">
					<h3 class="text-lg font-semibold text-surface-900 mb-1">
						{workflow.name}
					</h3>
					<p class="text-sm text-surface-600 line-clamp-2">
						{workflow.description}
					</p>
				</div>
				
				<div class="flex flex-wrap gap-2 mb-4">
					<span class="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800">
						{workflow.category}
					</span>
					<span class="px-2 py-1 text-xs rounded-full {getComplexityColor(workflow.complexity)}">
						{workflow.complexity}
					</span>
					<span class="px-2 py-1 text-xs rounded-full bg-surface-100 text-surface-800">
						{workflow.steps_count} steps
					</span>
				</div>
				
				<div class="grid grid-cols-2 gap-2 text-sm text-surface-600 mb-4">
					<div>Duration: {workflow.estimated_duration_minutes} min</div>
					<div>Success: {(workflow.success_rate * 100).toFixed(0)}%</div>
					<div>Used: {workflow.usage_count} times</div>
				</div>
				
				<div class="flex space-x-2">
					<button
						on:click={() => selectedWorkflow = workflow}
						class="flex-1 px-3 py-1 border border-surface-300 rounded hover:bg-surface-50 transition-colors text-sm"
					>
						View Details
					</button>
					<button
						on:click={() => executeWorkflow(workflow.workflow_id)}
						class="flex-1 px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors text-sm"
					>
						Execute
					</button>
				</div>
			</div>
		{/each}
	</div>
	
	<!-- Recent Executions -->
	<div class="bg-white rounded-lg shadow">
		<div class="px-6 py-4 border-b">
			<h2 class="text-lg font-semibold text-surface-900">Recent Executions</h2>
		</div>
		
		<div class="overflow-x-auto">
			<table class="w-full">
				<thead class="bg-surface-50">
					<tr>
						<th class="px-6 py-3 text-left text-xs font-medium text-surface-500 uppercase tracking-wider">
							Execution ID
						</th>
						<th class="px-6 py-3 text-left text-xs font-medium text-surface-500 uppercase tracking-wider">
							Workflow
						</th>
						<th class="px-6 py-3 text-left text-xs font-medium text-surface-500 uppercase tracking-wider">
							Status
						</th>
						<th class="px-6 py-3 text-left text-xs font-medium text-surface-500 uppercase tracking-wider">
							Progress
						</th>
						<th class="px-6 py-3 text-left text-xs font-medium text-surface-500 uppercase tracking-wider">
							Started
						</th>
						<th class="px-6 py-3 text-left text-xs font-medium text-surface-500 uppercase tracking-wider">
							Actions
						</th>
					</tr>
				</thead>
				<tbody class="bg-white divide-y divide-gray-200">
					{#each executions as execution}
						<tr>
							<td class="px-6 py-4 whitespace-nowrap text-sm text-surface-900">
								{execution.execution_id.slice(0, 8)}...
							</td>
							<td class="px-6 py-4 whitespace-nowrap text-sm text-surface-900">
								{execution.workflow_id}
							</td>
							<td class="px-6 py-4 whitespace-nowrap">
								<span class="text-sm font-medium {getStatusColor(execution.status)}">
									{execution.status}
								</span>
							</td>
							<td class="px-6 py-4 whitespace-nowrap">
								<div class="w-full bg-surface-200 rounded-full h-2.5">
									<div
										class="bg-blue-600 h-2.5 rounded-full"
										style="width: {execution.progress_percentage}%"
									></div>
								</div>
							</td>
							<td class="px-6 py-4 whitespace-nowrap text-sm text-surface-500">
								{new Date(execution.started_at).toLocaleString()}
							</td>
							<td class="px-6 py-4 whitespace-nowrap text-sm">
								{#if execution.status === 'running'}
									<button
										on:click={() => cancelExecution(execution.execution_id)}
										class="text-red-600 hover:text-red-900"
									>
										Cancel
									</button>
								{/if}
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	</div>
</div>

<style>
	.line-clamp-2 {
		display: -webkit-box;
		-webkit-line-clamp: 2;
		line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}
</style>