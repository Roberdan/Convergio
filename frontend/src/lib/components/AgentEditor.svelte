<script lang="ts">
	import { createEventDispatcher, onMount } from 'svelte';
	import { writable } from 'svelte/store';
	import AliRealTimeAssistance from './AliRealTimeAssistance.svelte';

	const dispatch = createEventDispatcher();

	// Props
	export let agentKey: string = '';
	export let isNewAgent: boolean = false;
	export let initialData: any = null;

	// Type definitions
	interface FormData {
		metadata: {
			name: string;
			description: string;
			color: string;
			tools: string[];
		};
		content: {
			persona: string;
			expertise_areas: string[];
			additional_content: string;
		};
	}

	interface ValidationErrors {
		name?: string;
		description?: string;
		persona?: string;
		expertise?: string;
	}

	interface AliAssistance {
		error?: string;
		confidence_score?: number;
		estimated_improvement?: string;
		suggestions?: Record<string, string[]>;
		next_steps?: string[];
	}

	// Stores for form data
	let formData = writable<FormData>({
		metadata: {
			name: '',
			description: '',
			color: '#4A90E2',
			tools: [] as string[]
		},
		content: {
			persona: '',
			expertise_areas: [] as string[],
			additional_content: ''
		}
	});

	// UI state
	let isLoading = false;
	let isSaving = false;
	let aliAssistance: AliAssistance | null = null;
	let showAliHelp = false;
	let aliRealTimeActive = false;
	let validationErrors: ValidationErrors = {};
	let saveStatus = '';
	
	// Available tools list (could be fetched from API)
	const availableTools = [
		'Task', 'Read', 'Write', 'Edit', 'MultiEdit', 
		'Bash', 'Glob', 'Grep', 'LS', 'WebFetch', 'WebSearch',
		'TodoWrite', 'NotebookRead', 'NotebookEdit',
		'query_talents_count', 'query_talent_details', 
		'query_department_structure', 'query_system_status',
		'query_knowledge_base', 'search_knowledge',
		'security_validation', 'prompt_analysis', 
		'threat_detection', 'accessibility_check'
	];
	
	// Color presets
	const colorPresets = [
		'#4A90E2', '#50C878', '#FF6B6B', '#FFD93D', 
		'#6C5CE7', '#FD79A8', '#00B894', '#FDCB6E',
		'#E17055', '#74B9FF', '#A29BFE', '#FD79A8'
	];
	
	// Reactive form data
	$: currentData = $formData;
	$: isFormValid = currentData.metadata.name && 
					currentData.metadata.description && 
					currentData.content.persona;
	
	onMount(async () => {
		if (!isNewAgent && agentKey) {
			await loadAgentData();
		} else if (initialData) {
			formData.set(initialData);
		}
	});
	
	async function loadAgentData() {
		isLoading = true;
		try {
			const response = await fetch(`/api/v1/agent-management/agents/${agentKey}`);
			if (!response.ok) throw new Error('Failed to load agent data');
			
			const data = await response.json();
			formData.set({
				metadata: data.metadata,
				content: data.content
			});
		} catch {
			// Silent failure
			dispatch('error', { message: 'Failed to load agent data' });
		} finally {
			isLoading = false;
		}
	}
	
	async function saveAgent() {
		if (!isFormValid) {
			validateForm();
			return;
		}
		
		isSaving = true;
		saveStatus = 'saving';
		
		try {
			const url = isNewAgent 
				? '/api/v1/agent-management/agents'
				: `/api/v1/agent-management/agents/${agentKey}`;
			
			const method = isNewAgent ? 'POST' : 'PUT';
			
			const payload = isNewAgent 
				? { definition: currentData }
				: { 
					agent_key: agentKey, 
					definition: currentData,
					ali_improvements: aliAssistance
				};
			
			const response = await fetch(url, {
				method,
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(payload)
			});
			
			if (!response.ok) throw new Error('Failed to save agent');
			
			const result = await response.json();
			saveStatus = 'success';
			
			dispatch('saved', {
				agentKey: result.agent_key,
				isNew: isNewAgent,
				message: result.message
			});
			
			setTimeout(() => saveStatus = '', 3000);
			
		} catch {
			// Silent failure
			saveStatus = 'error';
			dispatch('error', { message: 'Failed to save agent' });
			setTimeout(() => saveStatus = '', 3000);
		} finally {
			isSaving = false;
		}
	}
	
	async function getAliAssistance() {
		showAliHelp = true;
		
		try {
			const response = await fetch('/api/v1/agent-management/agents/ali-assistance', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					agent_key: agentKey,
					current_definition: currentData,
					improvement_focus: 'general',
					user_intent: 'improve agent effectiveness'
				})
			});
			
			if (!response.ok) throw new Error('Failed to get Ali assistance');
			
			aliAssistance = await response.json();
		} catch {
			// Silent failure
			aliAssistance = { error: 'Failed to get assistance from Ali' };
		}
	}
	
	function applyAliSuggestion(category: string, suggestion: string) {
		// Apply Ali's suggestions to the form
		if (category === 'expertise_improvements' && suggestion.includes('expertise areas')) {
			// Add suggested expertise areas
			const newAreas: string[] = [...currentData.content.expertise_areas, 'advanced analytics', 'strategic planning'];
			formData.update(data => ({
				...data,
				content: { ...data.content, expertise_areas: newAreas }
			}));
		} else if (category === 'persona_enhancements') {
			// Enhance persona
			const enhancedPersona = currentData.content.persona +
				'\n\nYou excel at collaborative problem-solving and adapt your communication style to match user preferences.';
			formData.update(data => ({
				...data,
				content: { ...data.content, persona: enhancedPersona }
			}));
		} else if (category === 'tool_recommendations') {
			// Add recommended tools
			const recommendedTools = suggestion.match(/tools?: (.+)/i)?.[1]?.split(', ') || [];
			const newTools: string[] = [...new Set([...currentData.metadata.tools, ...recommendedTools])];
			formData.update(data => ({
				...data,
				metadata: { ...data.metadata, tools: newTools }
			}));
		}

		dispatch('ali-suggestion-applied', { category, suggestion });
	}
	
	function addExpertiseArea() {
		formData.update(data => ({
			...data,
			content: {
				...data.content,
				expertise_areas: [...data.content.expertise_areas, ''] as string[]
			}
		}));
	}

	function removeExpertiseArea(index: number) {
		formData.update(data => ({
			...data,
			content: {
				...data.content,
				expertise_areas: data.content.expertise_areas.filter((_, i) => i !== index)
			}
		}));
	}

	function toggleTool(tool: string) {
		formData.update(data => {
			const tools: string[] = data.metadata.tools.includes(tool)
				? data.metadata.tools.filter(t => t !== tool)
				: [...data.metadata.tools, tool];

			return {
				...data,
				metadata: { ...data.metadata, tools }
			};
		});
	}
	
	function validateForm() {
		const errors: ValidationErrors = {};

		if (!currentData.metadata.name) errors.name = 'Name is required';
		if (!currentData.metadata.description) errors.description = 'Description is required';
		if (!currentData.content.persona) errors.persona = 'Persona is required';
		if (currentData.content.expertise_areas.length === 0) {
			errors.expertise = 'At least one expertise area is required';
		}

		validationErrors = errors;
		return Object.keys(errors).length === 0;
	}
	
	function previewAgent() {
		dispatch('preview', { definition: currentData });
	}
	
	function resetForm() {
		if (initialData) {
			formData.set(initialData);
		} else {
			formData.set({
				metadata: { name: '', description: '', color: '#4A90E2', tools: [] },
				content: { persona: '', expertise_areas: [], additional_content: '' }
			});
		}
		validationErrors = {};
		aliAssistance = null;
	}
	
	// Ali Real-Time Assistance Handlers
	function handleAliSuggestion(event: CustomEvent) {
		const { suggestion, autoApply } = event.detail;

		if (autoApply) {
			applyAliSuggestionAutomatically(suggestion);
		} else {
			// Show suggestion for manual review
			aliAssistance = {
				suggestions: { [suggestion.category]: [suggestion.suggestion] },
				confidence_score: 0.8
			};
			showAliHelp = true;
		}

		dispatch('ali-suggestion-applied', { suggestion });
	}

	function applyAliSuggestionAutomatically(suggestion: any) {
		switch (suggestion.category) {
			case 'expertise':
				if (suggestion.title.includes('Expand Expertise')) {
					const newAreas: string[] = [...currentData.content.expertise_areas, 'advanced analytics', 'strategic planning'];
					formData.update(data => ({
						...data,
						content: { ...data.content, expertise_areas: newAreas }
					}));
				}
				break;

			case 'persona':
				if (suggestion.title.includes('Enrich Agent Persona')) {
					const enhancement = '\n\nYou excel at collaborative problem-solving and adapt your communication style to match user preferences.';
					formData.update(data => ({
						...data,
						content: { ...data.content, persona: data.content.persona + enhancement }
					}));
				}
				break;

			case 'tools':
				if (suggestion.recommendedTools) {
					const newTools: string[] = [...new Set([...currentData.metadata.tools, ...suggestion.recommendedTools])];
					formData.update(data => ({
						...data,
						metadata: { ...data.metadata, tools: newTools }
					}));
				}
				break;
			
			case 'coordination':
				if (suggestion.title.includes('Improve Coordination')) {
					const coordinationText = '\n\n## COORDINATION GUIDELINES\n- Escalate complex cross-domain requests to Ali for coordination\n- Collaborate with specialists when expertise overlap is needed\n- Provide clear status updates during multi-step processes';
					formData.update(data => ({
						...data,
						content: { ...data.content, additional_content: data.content.additional_content + coordinationText }
					}));
				}
				break;
		}
		
		// Show success message
		saveStatus = 'ali-applied';
		setTimeout(() => {
			if (saveStatus === 'ali-applied') saveStatus = '';
		}, 2000);
	}
	
	function activateAliRealTime() {
		aliRealTimeActive = true;
	}
	
	function handleRequestDeepAnalysis() {
		// Request comprehensive analysis from Ali
		getAliAssistance();
	}
</script>

<div class="agent-editor max-w-4xl mx-auto p-6">
	<!-- Header -->
	<div class="mb-8">
		<h1 class="text-3xl font-bold text-surface-900 mb-2">
			{isNewAgent ? 'Create New Agent' : `Edit ${agentKey}`}
		</h1>
		<p class="text-surface-600">
			{isNewAgent ? 'Design a new AI agent with specialized expertise' : 'Modify agent capabilities and behavior'}
		</p>
	</div>
	
	{#if isLoading}
		<div class="flex items-center justify-center py-12">
			<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
			<span class="ml-3 text-surface-600">Loading agent data...</span>
		</div>
	{:else}
		<div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
			<!-- Main Form -->
			<div class="lg:col-span-2 space-y-6">
				<!-- Basic Metadata -->
				<div class="bg-white rounded-lg shadow-sm border p-6">
					<h2 class="text-xl font-semibold mb-4 flex items-center">
						<span class="w-2 h-2 bg-blue-500 rounded-full mr-3"></span>
						Basic Information
					</h2>
					
					<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
						<div>
							<label for="agent-name" class="block text-sm font-medium text-surface-600 mb-1">
								Agent Name *
							</label>
							<input
								id="agent-name"
								type="text"
								bind:value={$formData.metadata.name}
								class="w-full px-3 py-2 border border-surface-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
								class:border-red-300={validationErrors.name}
								placeholder="e.g., expert-data-analyst"
							/>
							{#if validationErrors.name}
								<p class="text-red-500 text-xs mt-1">{validationErrors.name}</p>
							{/if}
						</div>
						
						<div>
							<label for="agent-color" class="block text-sm font-medium text-surface-600 mb-1">
								Color Theme
							</label>
							<div class="flex items-center space-x-2">
								<input
									id="agent-color"
									type="color"
									bind:value={$formData.metadata.color}
									class="w-12 h-10 border border-surface-300 rounded cursor-pointer"
								/>
								<div class="flex space-x-1">
									{#each colorPresets as color}
										<button
											type="button"
											aria-label="Select color {color}"
											class="w-6 h-6 rounded border border-surface-200 hover:border-gray-400 transition-colors"
											style="background-color: {color}"
											on:click={() => formData.update(data => ({ ...data, metadata: { ...data.metadata, color } }))}
										></button>
									{/each}
								</div>
							</div>
						</div>
					</div>
					
					<div class="mt-4">
						<label for="agent-description" class="block text-sm font-medium text-surface-600 mb-1">
							Description *
						</label>
						<textarea
							id="agent-description"
							bind:value={$formData.metadata.description}
							rows="3"
							class="w-full px-3 py-2 border border-surface-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
							class:border-red-300={validationErrors.description}
							placeholder="Brief description of the agent's role and capabilities..."
						></textarea>
						{#if validationErrors.description}
							<p class="text-red-500 text-xs mt-1">{validationErrors.description}</p>
						{/if}
					</div>
				</div>
				
				<!-- Persona & Identity -->
				<div class="bg-white rounded-lg shadow-sm border p-6">
					<h2 class="text-xl font-semibold mb-4 flex items-center">
						<span class="w-2 h-2 bg-green-500 rounded-full mr-3"></span>
						Persona & Identity
					</h2>
					
					<div>
						<label for="agent-persona" class="block text-sm font-medium text-surface-600 mb-1">
							Agent Persona *
						</label>
						<textarea
							id="agent-persona"
							bind:value={$formData.content.persona}
							rows="6"
							class="w-full px-3 py-2 border border-surface-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
							class:border-red-300={validationErrors.persona}
							placeholder="You are an expert in... Your personality is... You approach problems by..."
						></textarea>
						{#if validationErrors.persona}
							<p class="text-red-500 text-xs mt-1">{validationErrors.persona}</p>
						{/if}
						<p class="text-surface-500 text-xs mt-1">
							Define the agent's personality, approach, and core identity.
						</p>
					</div>
				</div>
				
				<!-- Expertise Areas -->
				<div class="bg-white rounded-lg shadow-sm border p-6">
					<div class="flex justify-between items-center mb-4">
						<h2 class="text-xl font-semibold flex items-center">
							<span class="w-2 h-2 bg-purple-500 rounded-full mr-3"></span>
							Expertise Areas
						</h2>
						<button
							type="button"
							on:click={addExpertiseArea}
							class="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition-colors"
						>
							+ Add Area
						</button>
					</div>
					
					{#each $formData.content.expertise_areas as _area, index}
						<div class="flex items-center space-x-2 mb-2">
							<input
								type="text"
								bind:value={$formData.content.expertise_areas[index]}
								class="flex-1 px-3 py-2 border border-surface-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
								placeholder="e.g., data visualization, predictive modeling"
							/>
							<button
								type="button"
								on:click={() => removeExpertiseArea(index)}
								class="px-2 py-2 text-red-600 hover:bg-red-50 rounded transition-colors"
							>
								×
							</button>
						</div>
					{/each}
					
					{#if validationErrors.expertise}
						<p class="text-red-500 text-xs mt-1">{validationErrors.expertise}</p>
					{/if}
				</div>
				
				<!-- Available Tools -->
				<div class="bg-white rounded-lg shadow-sm border p-6">
					<h2 class="text-xl font-semibold mb-4 flex items-center">
						<span class="w-2 h-2 bg-orange-500 rounded-full mr-3"></span>
						Available Tools
					</h2>
					
					<div class="grid grid-cols-2 md:grid-cols-3 gap-2">
						{#each availableTools as tool}
							<label class="flex items-center space-x-2 p-2 rounded hover:bg-surface-50 cursor-pointer">
								<input
									type="checkbox"
									checked={$formData.metadata.tools.includes(tool)}
									on:change={() => toggleTool(tool)}
									class="rounded text-blue-600 focus:ring-blue-500"
								/>
								<span class="text-sm font-mono text-surface-600">{tool}</span>
							</label>
						{/each}
					</div>
					
					<p class="text-surface-500 text-xs mt-2">
						Selected: {$formData.metadata.tools.length} tools
					</p>
				</div>
				
				<!-- Additional Content -->
				<div class="bg-white rounded-lg shadow-sm border p-6">
					<h2 class="text-xl font-semibold mb-4 flex items-center">
						<span class="w-2 h-2 bg-surface-500 rounded-full mr-3"></span>
						Additional Content
					</h2>
					
					<textarea
						bind:value={$formData.content.additional_content}
						rows="8"
						class="w-full px-3 py-2 border border-surface-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
						placeholder="Additional markdown content, special instructions, examples..."
					></textarea>
					<p class="text-surface-500 text-xs mt-1">
						Add any additional markdown content for the agent definition.
					</p>
				</div>
			</div>
			
			<!-- Sidebar -->
			<div class="space-y-6">
				<!-- Actions -->
				<div class="bg-white rounded-lg shadow-sm border p-6">
					<h3 class="text-lg font-semibold mb-4">Actions</h3>
					
					<div class="space-y-3">
						<button
							type="button"
							on:click={saveAgent}
							disabled={!isFormValid || isSaving}
							class="w-full px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-surface-600 disabled:cursor-not-allowed transition-colors flex items-center justify-center"
						>
							{#if isSaving}
								<div class="animate-spin rounded-full h-4 w-4 border-b-2 border-surface-950 mr-2"></div>
							{/if}
							{isSaving ? 'Saving...' : (isNewAgent ? 'Create Agent' : 'Update Agent')}
						</button>
						
						<button
							type="button"
							on:click={previewAgent}
							class="w-full px-4 py-2 border border-surface-300 text-surface-600 rounded hover:bg-surface-50 transition-colors"
						>
							Preview Agent
						</button>
						
						<button
							type="button"
							on:click={getAliAssistance}
							class="w-full px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition-colors flex items-center justify-center"
						>
							<span class="mr-2">🤖</span>
							Ask Ali for Help
						</button>
						
						<button
							type="button"
							on:click={activateAliRealTime}
							disabled={aliRealTimeActive}
							class="w-full px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center justify-center"
						>
							<span class="mr-2">{aliRealTimeActive ? '⚡' : '🔥'}</span>
							{aliRealTimeActive ? 'Ali Real-Time Active' : 'Activate Real-Time Ali'}
						</button>
						
						<button
							type="button"
							on:click={resetForm}
							class="w-full px-4 py-2 border border-red-300 text-red-700 rounded hover:bg-red-50 transition-colors"
						>
							Reset Form
						</button>
					</div>
					
					{#if saveStatus}
						<div class="mt-4 p-3 rounded text-sm text-center" 
							 class:bg-green-100={saveStatus === 'success'}
							 class:text-green-800={saveStatus === 'success'}
							 class:bg-red-100={saveStatus === 'error'}
							 class:text-red-800={saveStatus === 'error'}
							 class:bg-blue-100={saveStatus === 'saving'}
							 class:text-blue-800={saveStatus === 'saving'}
							 class:bg-purple-100={saveStatus === 'ali-applied'}
							 class:text-purple-800={saveStatus === 'ali-applied'}>
							{#if saveStatus === 'saving'}
								Saving agent...
							{:else if saveStatus === 'success'}
								✅ Agent saved successfully!
							{:else if saveStatus === 'error'}
								❌ Failed to save agent
							{:else if saveStatus === 'ali-applied'}
								🤖 Ali suggestion applied automatically!
							{/if}
						</div>
					{/if}
				</div>
				
				<!-- Ali Real-Time Assistance -->
				<AliRealTimeAssistance
					currentDefinition={currentData}
					isActive={aliRealTimeActive}
					on:apply-suggestion={handleAliSuggestion}
					on:activate-ali={activateAliRealTime}
					on:request-deep-analysis={handleRequestDeepAnalysis}
				/>
				
				<!-- Ali Manual Assistance -->
				{#if showAliHelp && !aliRealTimeActive}
					<div class="bg-blue-50 rounded-lg border border-blue-200 p-6">
						<h3 class="text-lg font-semibold mb-4 flex items-center">
							<span class="mr-2">🤖</span>
							Ali's Manual Assistance
						</h3>

						{#if aliAssistance}
							{#if aliAssistance.error}
								<p class="text-red-600 text-sm">{aliAssistance.error}</p>
							{:else}
								<div class="space-y-4">
									<p class="text-sm text-blue-800">
										Confidence: {((aliAssistance.confidence_score ?? 0) * 100).toFixed(0)}% |
										Expected improvement: {aliAssistance.estimated_improvement ?? 'N/A'}
									</p>

									{#if aliAssistance.suggestions}
										{#each Object.entries(aliAssistance.suggestions) as [category, suggestions]}
											{#if Array.isArray(suggestions) && suggestions.length > 0}
												<div>
													<h4 class="font-medium text-blue-900 mb-2 capitalize">
														{category.replace('_', ' ')}
													</h4>
													<ul class="space-y-2">
														{#each suggestions as suggestion}
															<li class="flex justify-between items-start">
																<p class="text-sm text-surface-600">{suggestion}</p>
																<button
																	type="button"
																	on:click={() => applyAliSuggestion(category, suggestion)}
																	class="ml-2 px-2 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 transition-colors flex-shrink-0"
																>
																	Apply
																</button>
															</li>
														{/each}
													</ul>
												</div>
											{/if}
										{/each}
									{/if}

									{#if aliAssistance.next_steps && Array.isArray(aliAssistance.next_steps)}
										<div>
											<h4 class="font-medium text-blue-900 mb-2">Next Steps</h4>
											<ul class="list-disc list-inside text-sm text-surface-600 space-y-1">
												{#each aliAssistance.next_steps as step}
													<li>{step}</li>
												{/each}
											</ul>
										</div>
									{/if}
								</div>
							{/if}
						{:else}
							<div class="flex items-center text-blue-600">
								<div class="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
								Getting assistance from Ali...
							</div>
						{/if}
					</div>
				{/if}
				
				<!-- Form Status -->
				<div class="bg-surface-50 rounded-lg p-4">
					<h3 class="text-sm font-medium text-surface-600 mb-2">Form Status</h3>
					<div class="space-y-2 text-sm">
						<div class="flex justify-between">
							<span>Valid:</span>
							<span class:text-green-600={isFormValid} class:text-red-600={!isFormValid}>
								{isFormValid ? '✓' : '✗'}
							</span>
						</div>
						<div class="flex justify-between">
							<span>Tools:</span>
							<span class="text-surface-600">{$formData.metadata.tools.length}</span>
						</div>
						<div class="flex justify-between">
							<span>Expertise Areas:</span>
							<span class="text-surface-600">{$formData.content.expertise_areas.length}</span>
						</div>
					</div>
				</div>
			</div>
		</div>
	{/if}
</div>

<style>
	.agent-editor {
		background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
		min-height: 100vh;
	}
</style>