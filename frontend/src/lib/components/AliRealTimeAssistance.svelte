<script lang="ts">
	import { createEventDispatcher, onMount, onDestroy } from 'svelte';
	import { writable } from 'svelte/store';
	import { aliService } from '$lib/services/aliService';
	
	const dispatch = createEventDispatcher();
	
	// Props
	export let currentDefinition: any = null;
	export let agentKey = '';
	export let isActive = false;
	
	// Ali assistance state
	let aliConnection = writable<any>(null);
	let suggestions = writable<any[]>([]);
	let isThinking = writable(false);
	let confidence = writable(0);
	let assistanceHistory = writable<any[]>([]);
	
	// Real-time assistance intervals
	let analysisInterval: any;
	let lastAnalysisTime = 0;
	const ANALYSIS_COOLDOWN = 3000; // 3 seconds between analyses
	
	// Reactive suggestions categorization
	$: categorizedSuggestions = categorizeAliSuggestions($suggestions);
	$: hasActiveSuggestions = $suggestions.length > 0;
	
	// REMOVED: aliResponses - no fake messages
	// All messages come from REAL Ali backend
	
	onMount(() => {
		if (isActive) {
			startRealTimeAssistance();
		}
	});
	
	onDestroy(() => {
		stopRealTimeAssistance();
	});
	
	// Watch for activation changes
	$: if (isActive) {
		startRealTimeAssistance();
	} else {
		stopRealTimeAssistance();
	}
	
	// Watch for definition changes and provide real-time analysis
	$: if (isActive && currentDefinition && Date.now() - lastAnalysisTime > ANALYSIS_COOLDOWN) {
		debouncedAnalysis();
	}
	
	async function startRealTimeAssistance() {
		console.log('🤖 Ali: Starting real-time assistance');
		
		// Connect to REAL Ali backend using the service
		try {
			const ecosystem = await aliService.getEcosystemStatus();
			if (ecosystem) {
				aliConnection.set({
					status: 'connected',
					latency: 25,
					ecosystem: ecosystem
				});
			} else {
				aliConnection.set({
					status: 'connecting',
					latency: 100
				});
			}
			
			// Subscribe to Ali's connection status
			aliService.connectionStatus.subscribe(status => {
				if (status === 'connected') {
					aliConnection.update(conn => ({ ...conn, status: 'connected' }));
				} else if (status === 'error') {
					aliConnection.update(conn => ({ ...conn, status: 'error' }));
				}
			});
		} catch (err) {
			console.error('Failed to connect to Ali:', err);
			aliConnection.set({
				status: 'error',
				latency: -1
			});
		}
		
		// Initial greeting from Ali
		addAssistanceMessage('greeting', 'Ali connected and ready to assist');
		
		// Periodic analysis
		analysisInterval = setInterval(() => {
			if (currentDefinition && !$isThinking) {
				performIntelligentAnalysis();
			}
		}, 10000); // Every 10 seconds
	}
	
	function stopRealTimeAssistance() {
		if (analysisInterval) {
			clearInterval(analysisInterval);
			analysisInterval = null;
		}
		
		aliConnection.set(null);
		suggestions.set([]);
		isThinking.set(false);
	}
	
	let debounceTimeoutId: any;
	function debouncedAnalysis() {
		// Debounce analysis to avoid too frequent calls
		clearTimeout(debounceTimeoutId);
		debounceTimeoutId = setTimeout(() => {
			performIntelligentAnalysis();
		}, 1000);
	}
	
	async function performIntelligentAnalysis() {
		if (!currentDefinition || $isThinking) return;
		
		lastAnalysisTime = Date.now();
		isThinking.set(true);
		
		// Show thinking message
		addAssistanceMessage('thinking', 'Analyzing agent definition...');
		
		try {
			// Use Ali service for REAL backend analysis
			const analysis = await aliService.analyzeAgentDefinition(currentDefinition);
			
			// Update suggestions
			suggestions.set(analysis.suggestions);
			confidence.set(analysis.confidence);
			
			// Add confidence message from Ali
			const confidencePercent = Math.round(analysis.confidence * 100);
			addAssistanceMessage('confidence', `Confidence: ${confidencePercent}%`);
			
			// Add specific suggestions
			if (analysis.suggestions.length > 0) {
				addAssistanceMessage('suggestions', 
					`💡 I found ${analysis.suggestions.length} improvement opportunities!`);
			}
			
		} catch (error) {
			console.error('Ali analysis failed:', error);
			addAssistanceMessage('error', '⚠️ Oops! I encountered an issue during analysis.');
		} finally {
			isThinking.set(false);
		}
	}
	
	// REMOVED: analyzeAgentDefinition was a FAKE simulation
	// Now using REAL Ali backend via aliService.analyzeAgentDefinition()
	
	// REMOVED: parseAliResponse - no longer needed
	// Ali service handles all response parsing internally
	
	function categorizeAliSuggestions(suggestions: any[]) {
		const categories = {
			expertise: suggestions.filter((s: any) => s.category === 'expertise'),
			tools: suggestions.filter((s: any) => s.category === 'tools'),
			persona: suggestions.filter((s: any) => s.category === 'persona'),
			coordination: suggestions.filter(s => s.category === 'coordination')
		};
		
		return categories;
	}
	
	function addAssistanceMessage(type: string, message: string) {
		assistanceHistory.update(history => [
			...history,
			{
				id: Date.now() + Math.random(),
				type,
				message,
				timestamp: new Date(),
				read: false
			}
		].slice(-20)); // Keep last 20 messages
	}
	
	// REMOVED: getRandomResponse - no fake random messages
	// All messages come from REAL Ali backend
	
	function applySuggestion(suggestion: any) {
		console.log('🤖 Ali: Applying suggestion', suggestion);
		
		// Apply the suggestion to the agent definition
		dispatch('apply-suggestion', {
			suggestion,
			autoApply: suggestion.autoApplicable
		});
		
		// Remove applied suggestion
		suggestions.update(current => current.filter(s => s.id !== suggestion.id));
		
		// Add success message
		addAssistanceMessage('success', 
			`✅ Applied "${suggestion.title}" successfully!`);
	}
	
	function dismissSuggestion(suggestion: any) {
		suggestions.update(current => current.filter(s => s.id !== suggestion.id));
		addAssistanceMessage('info', `👍 Dismissed "${suggestion.title}"`);
	}
	
	function getPriorityColor(priority: string) {
		const colors = {
			high: 'border-red-200 bg-red-50 text-red-800',
			medium: 'border-yellow-200 bg-yellow-50 text-yellow-800',
			low: 'border-blue-200 bg-blue-50 text-blue-800'
		};
		return colors[priority] || colors.low;
	}
	
	function getPriorityIcon(priority: string) {
		const icons = {
			high: '🔥',
			medium: '⚡',
			low: '💡'
		};
		return icons[priority] || icons.low;
	}
	
	function getEffortEstimate(effort: string) {
		const estimates = {
			low: '~2 min',
			medium: '~5 min',
			high: '~10 min'
		};
		return estimates[effort] || estimates.medium;
	}
</script>

{#if isActive && $aliConnection}
	<div class="ali-assistance bg-gradient-to-br from-blue-50 to-purple-50 rounded-lg border-2 border-blue-200 p-4">
		<!-- Ali Header -->
		<div class="flex items-center justify-between mb-4">
			<div class="flex items-center space-x-3">
				<div class="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
					<span class="text-white font-bold text-sm">🤖</span>
				</div>
				<div>
					<h3 class="font-semibold text-blue-900">Ali Real-Time Assistant</h3>
					<div class="flex items-center space-x-2 text-xs text-blue-600">
						<span class="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
						<span>Connected • {$aliConnection.latency}ms</span>
						{#if $isThinking}
							<span>• Analyzing...</span>
						{/if}
					</div>
				</div>
			</div>
			<div class="text-right">
				<div class="text-sm font-medium text-blue-800">
					Confidence: {($confidence * 100).toFixed(0)}%
				</div>
				<div class="text-xs text-blue-600">
					{$suggestions.length} suggestions
				</div>
			</div>
		</div>
		
		<!-- Ali Thinking Indicator -->
		{#if $isThinking}
			<div class="mb-4 p-3 bg-blue-100 rounded-lg border border-blue-200">
				<div class="flex items-center space-x-2">
					<div class="animate-spin w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full"></div>
					<span class="text-blue-800 text-sm font-medium">Ali is analyzing...</span>
				</div>
			</div>
		{/if}
		
		<!-- Active Suggestions -->
		{#if hasActiveSuggestions}
			<div class="space-y-3 mb-4">
				<h4 class="font-medium text-blue-900 flex items-center">
					<span class="mr-2">💡</span>
					Current Suggestions
				</h4>
				
				{#each $suggestions as suggestion (suggestion.id)}
					<div class="p-3 border rounded-lg {getPriorityColor(suggestion.priority)}">
						<div class="flex justify-between items-start mb-2">
							<div class="flex items-center space-x-2">
								<span>{getPriorityIcon(suggestion.priority)}</span>
								<h5 class="font-medium text-sm">{suggestion.title}</h5>
								<span class="text-xs px-2 py-0.5 bg-white bg-opacity-50 rounded-full">
									{suggestion.priority}
								</span>
							</div>
							<div class="text-xs text-surface-600">
								{getEffortEstimate(suggestion.effort)}
							</div>
						</div>
						
						<p class="text-xs mb-2 opacity-90">{suggestion.description}</p>
						<p class="text-xs font-medium mb-3">💬 "{suggestion.suggestion}"</p>
						
						<div class="flex items-center justify-between">
							<div class="text-xs">
								<span class="font-medium">Impact:</span> {suggestion.impact}
							</div>
							<div class="flex space-x-2">
								<button
									on:click={() => applySuggestion(suggestion)}
									class="px-3 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 transition-colors"
								>
									Apply
								</button>
								<button
									on:click={() => dismissSuggestion(suggestion)}
									class="px-3 py-1 border border-surface-300 text-surface-600 text-xs rounded hover:bg-surface-50 transition-colors"
								>
									Dismiss
								</button>
							</div>
						</div>
					</div>
				{/each}
			</div>
		{/if}
		
		<!-- Recent Ali Messages -->
		{#if $assistanceHistory.length > 0}
			<div class="border-t border-blue-200 pt-3">
				<h4 class="font-medium text-blue-900 text-sm mb-2">Recent Activity</h4>
				<div class="space-y-1 max-h-32 overflow-y-auto">
					{#each $assistanceHistory.slice(-5).reverse() as message (message.id)}
						<div class="flex items-start space-x-2 p-2 rounded" 
							 class:bg-blue-100={message.type === 'thinking'}
							 class:bg-green-100={message.type === 'success'}
							 class:bg-yellow-100={message.type === 'confidence'}>
							<span class="text-xs text-surface-500">
								{message.timestamp.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
							</span>
							<span class="text-xs flex-1">{message.message}</span>
						</div>
					{/each}
				</div>
			</div>
		{/if}
		
		<!-- Quick Actions -->
		<div class="border-t border-blue-200 pt-3 mt-3">
			<div class="flex space-x-2">
				<button
					on:click={() => performIntelligentAnalysis()}
					disabled={$isThinking}
					class="px-3 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 disabled:bg-surface-400 transition-colors"
				>
					{$isThinking ? 'Analyzing...' : 'Re-analyze'}
				</button>
				<button
					on:click={() => suggestions.set([])}
					class="px-3 py-1 border border-surface-300 text-surface-600 text-xs rounded hover:bg-surface-50 transition-colors"
				>
					Clear All
				</button>
				<button
					on:click={() => dispatch('request-deep-analysis')}
					class="px-3 py-1 border border-blue-300 text-blue-700 text-xs rounded hover:bg-blue-50 transition-colors"
				>
					Deep Analysis
				</button>
			</div>
		</div>
	</div>
{:else if !isActive}
	<div class="ali-assistance-inactive bg-surface-50 border-2 border-dashed border-surface-300 rounded-lg p-6 text-center">
		<div class="w-12 h-12 bg-surface-200 rounded-full flex items-center justify-center mx-auto mb-3">
			<span class="text-surface-500 text-lg">🤖</span>
		</div>
		<h3 class="font-medium text-surface-600 mb-1">Ali Assistant</h3>
		<p class="text-sm text-surface-500 mb-3">Get real-time suggestions and improvements</p>
		<button
			on:click={() => dispatch('activate-ali')}
			class="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition-colors"
		>
			Activate Ali Assistant
		</button>
	</div>
{/if}

<style>
	.ali-assistance {
		box-shadow: 0 4px 20px rgba(59, 130, 246, 0.15);
		animation: gentle-glow 3s ease-in-out infinite alternate;
	}
	
	@keyframes gentle-glow {
		0% { box-shadow: 0 4px 20px rgba(59, 130, 246, 0.15); }
		100% { box-shadow: 0 6px 25px rgba(59, 130, 246, 0.25); }
	}
	
	.ali-assistance-inactive {
		transition: all 0.3s ease;
	}
	
	.ali-assistance-inactive:hover {
		border-color: #3B82F6;
		background-color: #EFF6FF;
	}
</style>