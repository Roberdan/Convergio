<script lang="ts">
	import { onMount } from 'svelte';
	import { writable } from 'svelte/store';
	import { aliService, type AliResponse } from '$lib/services/aliService';
	import { projectsService, type Engagement } from '$lib/services/projectsService';

	// Props
	export let projectId: string;

	// Interfaces
	interface Message {
		id: string;
		type: 'user' | 'assistant';
		content: string;
		timestamp: Date;
		projectContext?: {
			taskId?: string;
			viewType?: string;
			data?: any;
		};
	}

	interface ProjectContext {
		projectName: string;
		currentPhase: string;
		teamMembers: string[];
		recentActivity: string[];
		blockers: string[];
		engagement?: Engagement;
		metrics: {
			progress: number;
			budget: number;
			timeline: string;
		};
	}

	// State
	let messages: Message[] = [];
	let newMessage = '';
	let loading = false;
	let isTyping = false;
	let chatContainer: HTMLElement;
	let projectContext: ProjectContext | null = null;
	let connectionStatus = 'disconnected';
	let aliLatency = 0;

	// Subscribe to Ali connection status
	aliService.connectionStatus.subscribe(status => {
		connectionStatus = status;
	});

	aliService.latency.subscribe(latency => {
		aliLatency = latency;
	});



	const welcomeMessage: Message = {
		id: '1',
		type: 'assistant',
		content: `Hello! I'm Ali, your AI Chief of Staff. I'm here to help you with project management and strategic coordination.

I can assist you with:
🎯 **Project insights** - Get summaries of progress, blockers, and next steps
📊 **Data analysis** - Analyze team performance, budget, and timeline
🔄 **Task management** - Help prioritize tasks and resolve bottlenecks
💡 **Strategic recommendations** - Suggest optimizations and best practices
🗣️ **Team communication** - Draft updates, meeting notes, and reports
🤖 **Agent coordination** - Orchestrate other AI agents for complex tasks

What would you like to know about your project?`,
		timestamp: new Date()
	};

	onMount(async () => {
		await loadProjectContext();
		messages = [welcomeMessage];
	});

	async function loadProjectContext() {
		loading = true;
		try {
			// Load real project data
			if (projectId) {
				const engagement = await projectsService.getEngagement(parseInt(projectId));
				const activities = await projectsService.getActivities();
				
				// Build project context from real data
				projectContext = {
					projectName: engagement.title,
					currentPhase: engagement.status === 'planning' ? 'Planning' : 
									 engagement.status === 'in-progress' ? 'Development' : 
									 engagement.status === 'review' ? 'Review' : 'Completed',
					teamMembers: ['Alice Chen', 'Bob Wilson', 'Carol Davis'], // TODO: Get from real team data
					recentActivity: activities.slice(0, 4).map(a => a.title),
					blockers: [], // TODO: Determine from task status
					engagement,
					metrics: {
						progress: engagement.progress || 0,
						budget: 180000, // TODO: Get from real budget data
						timeline: 'On track'
					}
				};
			} else {
				// Fallback context
				projectContext = {
					projectName: 'Project Dashboard',
					currentPhase: 'Active',
					teamMembers: [],
					recentActivity: [],
					blockers: [],
					metrics: {
						progress: 0,
						budget: 0,
						timeline: 'Unknown'
					}
				};
			}
		} catch (error) {
			console.error('Error loading project context:', error);
			// Use fallback context on error
			projectContext = {
				projectName: 'Project Dashboard',
				currentPhase: 'Error loading data',
				teamMembers: [],
				recentActivity: ['Error loading recent activity'],
				blockers: ['Unable to load project data'],
				metrics: {
					progress: 0,
					budget: 0,
					timeline: 'Error'
				}
			};
		} finally {
			loading = false;
		}
	}

	async function sendMessage() {
		if (!newMessage.trim()) return;

		const userMessage: Message = {
			id: Date.now().toString(),
			type: 'user',
			content: newMessage.trim(),
			timestamp: new Date()
		};

		messages = [...messages, userMessage];
		const userInput = newMessage.trim();
		newMessage = '';
		
		isTyping = true;
		scrollToBottom();

		// Send to real Ali agent
		try {
			const context = {
				projectId,
				projectContext,
				view: 'project_management',
				userRole: 'project_manager'
			};

			const aliResponse: AliResponse = await aliService.sendMessage(userInput, context);
			
			const assistantMessage: Message = {
				id: (Date.now() + 1).toString(),
				type: 'assistant',
				content: aliResponse.response,
				timestamp: new Date(),
				projectContext: {
					data: {
						agents_used: aliResponse.agents_used,
						confidence: aliResponse.confidence,
						suggestions: aliResponse.suggestions
					}
				}
			};
			
			messages = [...messages, assistantMessage];
		} catch (error) {
			console.error('Error communicating with Ali:', error);
			const errorMessage: Message = {
				id: (Date.now() + 1).toString(),
				type: 'assistant',
				content: `I apologize, but I'm having trouble connecting to my backend systems right now. Please check my connection status and try again.\n\nError: ${error instanceof Error ? error.message : 'Unknown error'}`,
				timestamp: new Date()
			};
			messages = [...messages, errorMessage];
		} finally {
			isTyping = false;
			scrollToBottom();
		}
	}

	// Remove the mock generateResponse function and helper data
	// All responses now come from real Ali agent

	function scrollToBottom() {
		setTimeout(() => {
			if (chatContainer) {
				chatContainer.scrollTop = chatContainer.scrollHeight;
			}
		}, 100);
	}

	function formatTime(date: Date) {
		return date.toLocaleTimeString('en-US', { 
			hour: '2-digit', 
			minute: '2-digit',
			hour12: false 
		});
	}

	function handleKeyPress(event: KeyboardEvent) {
		if (event.key === 'Enter' && !event.shiftKey) {
			event.preventDefault();
			sendMessage();
		}
	}

	// Quick action buttons - updated for real Ali capabilities
	const quickActions = [
		'What\'s our current project status?',
		'Analyze team performance and bottlenecks',
		'Identify project risks and mitigation strategies',
		'Optimize resource allocation',
		'Generate executive summary report',
		'Coordinate with other AI agents for complex analysis'
	];
</script>

<div class="ali-assistant bg-white rounded-xl shadow-sm border border-surface-200  overflow-hidden h-[600px] flex flex-col">
	<!-- Header -->
	<div class="p-4 border-b border-surface-200  bg-surface-50 ">
		<div class="flex items-center space-x-3">
			<div class="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-600 rounded-full flex items-center justify-center">
				<span class="text-white font-semibold text-lg">🤖</span>
			</div>
			<div>
				<h3 class="font-semibold text-surface-900 ">Ali AI Assistant</h3>
				<p class="text-sm text-surface-600 ">
					{#if projectContext}
						Project: {projectContext.projectName}
					{:else}
						Loading project context...
					{/if}
				</p>
			</div>
			<div class="flex-1"></div>
			<div class="flex items-center space-x-2">
				<div class="w-2 h-2 {connectionStatus === 'connected' ? 'bg-success-500' : connectionStatus === 'connecting' ? 'bg-warning-500' : 'bg-error-500'} rounded-full {connectionStatus === 'connecting' ? 'animate-pulse' : ''}"></div>
				<span class="text-xs text-surface-500 ">
					{connectionStatus === 'connected' ? `Online (${aliLatency}ms)` : 
					 connectionStatus === 'connecting' ? 'Connecting...' : 
					 connectionStatus === 'error' ? 'Connection Error' : 'Offline'}
				</span>
			</div>
		</div>
	</div>

	<!-- Messages -->
	<div bind:this={chatContainer} class="flex-1 overflow-y-auto p-4 space-y-4">
		{#each messages as message}
			<div class="message flex {message.type === 'user' ? 'justify-end' : 'justify-start'}">
				<div class="max-w-[80%] {message.type === 'user' ? 'order-last' : 'order-first'}">
					{#if message.type === 'assistant'}
						<div class="flex items-start space-x-3">
							<div class="w-8 h-8 bg-gradient-to-br from-primary-500 to-primary-600 rounded-full flex items-center justify-center flex-shrink-0">
								<span class="text-white text-sm">🤖</span>
							</div>
							<div>
								<div class="bg-surface-100  rounded-lg p-3 prose prose-sm max-w-none">
									{@html message.content.replace(/\n/g, '<br>').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\*(.*?)\*/g, '<em>$1</em>')}
								</div>
								<div class="text-xs text-surface-500  mt-1 ml-1">
									{formatTime(message.timestamp)}
								</div>
							</div>
						</div>
					{:else}
						<div class="flex items-start space-x-3 justify-end">
							<div>
								<div class="bg-primary-500 text-white rounded-lg p-3">
									{message.content}
								</div>
								<div class="text-xs text-surface-500  mt-1 text-right mr-1">
									{formatTime(message.timestamp)}
								</div>
							</div>
						</div>
					{/if}
				</div>
			</div>
		{/each}

		{#if isTyping}
			<div class="message flex justify-start">
				<div class="flex items-start space-x-3">
					<div class="w-8 h-8 bg-gradient-to-br from-primary-500 to-primary-600 rounded-full flex items-center justify-center">
						<span class="text-white text-sm">🤖</span>
					</div>
					<div class="bg-surface-100  rounded-lg p-3">
						<div class="flex space-x-1">
							<div class="w-2 h-2 bg-surface-400 rounded-full animate-bounce"></div>
							<div class="w-2 h-2 bg-surface-400 rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
							<div class="w-2 h-2 bg-surface-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
						</div>
					</div>
				</div>
			</div>
		{/if}
	</div>

	<!-- Quick Actions -->
	{#if messages.length === 1}
		<div class="p-4 border-t border-surface-200  bg-surface-50 ">
			<div class="mb-2">
				<span class="text-xs font-medium text-surface-600 ">Quick Actions:</span>
			</div>
			<div class="flex flex-wrap gap-2">
				{#each quickActions as action}
					<button 
						on:click={() => { newMessage = action; sendMessage(); }}
						class="text-xs px-3 py-1 bg-surface-200  hover:bg-primary-100 text-surface-700  hover:text-primary-700 rounded-full transition-colors duration-200"
						aria-label="Send quick action: {action}"
					>
						{action}
					</button>
				{/each}
			</div>
		</div>
	{/if}

	<!-- Input -->
	<div class="p-4 border-t border-surface-200 ">
		<div class="flex space-x-3">
			<label for="ali-message-input" class="sr-only">Message to Ali AI Assistant</label>
			<textarea
				id="ali-message-input"
				bind:value={newMessage}
				on:keydown={handleKeyPress}
				placeholder="Ask Ali about your project..."
				class="flex-1 input resize-none"
				rows="1"
				disabled={isTyping}
				aria-describedby="ali-input-help"
			></textarea>
			<span id="ali-input-help" class="sr-only">Press Enter to send message, Shift+Enter for new line</span>
			<button 
				on:click={sendMessage}
				disabled={!newMessage.trim() || isTyping}
				class="btn-primary btn-icon flex-shrink-0"
				aria-label="Send message to Ali"
				title="Send message"
			>
				<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
				</svg>
			</button>
		</div>
	</div>
</div>

<style>
	.message {
		animation: fadeInUp 0.3s ease-out;
	}
	
	@keyframes fadeInUp {
		from {
			opacity: 0;
			transform: translateY(10px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}
	
	.prose {
		color: inherit;
	}
</style>