"""
🤖 Swarm Intelligence Coordination System
Advanced agent coordination with self-organizing patterns and intelligent task distribution
"""

import asyncio
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import structlog
from datetime import datetime

logger = structlog.get_logger()

class SwarmRole(Enum):
    """Agent roles in swarm coordination"""
    COORDINATOR = "coordinator"  # Ali as main coordinator
    SPECIALIST = "specialist"    # Domain experts
    EXECUTOR = "executor"        # Task executors
    MONITOR = "monitor"          # Quality assurance
    COMMUNICATOR = "communicator" # Cross-domain liaison

class TaskComplexity(Enum):
    """Task complexity levels for distribution"""
    SIMPLE = 1      # Single agent
    MODERATE = 2    # 2-3 agents
    COMPLEX = 3     # 4-7 agents  
    ENTERPRISE = 4  # 8+ agents with coordination

@dataclass
class SwarmAgent:
    """Agent representation in swarm context"""
    agent_key: str
    name: str
    role: SwarmRole
    expertise_areas: List[str]
    tools: List[str]
    current_load: float  # 0.0 to 1.0
    success_rate: float  # Historical success rate
    avg_response_time: float  # Average response time in seconds
    is_available: bool
    last_active: datetime
    coordination_score: float  # How well it coordinates with others

@dataclass
class SwarmTask:
    """Task representation for swarm processing"""
    task_id: str
    description: str
    complexity: TaskComplexity
    required_expertise: List[str]
    required_tools: List[str]
    estimated_duration: int  # minutes
    priority: int  # 1-10
    assigned_agents: List[str]
    status: str  # pending, in_progress, completed, failed
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    coordination_pattern: Optional[str] = None

class SwarmCoordinator:
    """Advanced swarm intelligence coordination system"""
    
    def __init__(self):
        self.agents: Dict[str, SwarmAgent] = {}
        self.active_tasks: Dict[str, SwarmTask] = {}
        self.coordination_patterns: Dict[str, Dict[str, Any]] = {}
        self.performance_metrics: Dict[str, Dict[str, float]] = {}
        self.task_counter = 0
        self.setup_coordination_patterns()
        
        logger.info("🤖 Swarm Coordinator initialized")

    def setup_coordination_patterns(self):
        """Setup predefined coordination patterns"""
        self.coordination_patterns = {
            "sequential": {
                "description": "Agents work in sequence, output of one feeds next",
                "best_for": ["analysis_pipelines", "multi_step_workflows"],
                "coordination_overhead": 0.2
            },
            "parallel": {
                "description": "Agents work simultaneously on different aspects",
                "best_for": ["broad_analysis", "multi_domain_tasks"],
                "coordination_overhead": 0.1
            },
            "hierarchical": {
                "description": "Lead agent coordinates sub-agents",
                "best_for": ["complex_projects", "enterprise_tasks"],
                "coordination_overhead": 0.3
            },
            "swarm": {
                "description": "Self-organizing swarm with emergent coordination",
                "best_for": ["creative_tasks", "exploration", "innovation"],
                "coordination_overhead": 0.4
            },
            "assembly_line": {
                "description": "Specialized agents in production chain",
                "best_for": ["content_creation", "data_processing"],
                "coordination_overhead": 0.15
            }
        }
        
    def register_agent(self, agent_data: Dict[str, Any]) -> SwarmAgent:
        """Register agent in swarm coordination system"""
        try:
            # Determine swarm role based on agent characteristics
            role = self._determine_swarm_role(agent_data)
            
            swarm_agent = SwarmAgent(
                agent_key=agent_data.get('key', ''),
                name=agent_data.get('name', ''),
                role=role,
                expertise_areas=agent_data.get('expertise_areas', []),
                tools=agent_data.get('tools', []),
                current_load=0.0,
                success_rate=0.95,  # Initial optimistic rate
                avg_response_time=2.5,  # Initial estimate
                is_available=True,
                last_active=datetime.now(),
                coordination_score=0.8  # Initial coordination ability
            )
            
            self.agents[agent_data['key']] = swarm_agent
            logger.info("Registered agent in swarm", agent_key=agent_data['key'], role=role.value)
            
            return swarm_agent
            
        except Exception as e:
            logger.error("Failed to register agent in swarm", error=str(e))
            raise

    def _determine_swarm_role(self, agent_data: Dict[str, Any]) -> SwarmRole:
        """Intelligently determine agent's role in swarm coordination"""
        name = agent_data.get('name', '').lower()
        expertise = agent_data.get('expertise_areas', [])
        agent_data.get('description', '').lower()
        
        # Ali is always the coordinator
        if 'ali' in name or 'chief' in name:
            return SwarmRole.COORDINATOR
            
        # Quality assurance agents
        if any(term in name for term in ['thor', 'guardian', 'quality', 'test']):
            return SwarmRole.MONITOR
            
        # Communication and coordination specialists
        if any(term in name for term in ['steve', 'communication', 'coordination', 'workflow']):
            return SwarmRole.COMMUNICATOR
            
        # Technical specialists
        if any(expertise_area in ['security', 'architecture', 'devops', 'data'] for expertise_area in expertise):
            return SwarmRole.SPECIALIST
            
        # Default to executor for general purpose agents
        return SwarmRole.EXECUTOR

    async def create_swarm_task(self, task_description: str, user_context: Dict[str, Any] = None) -> SwarmTask:
        """Create and analyze new swarm task"""
        try:
            self.task_counter += 1
            task_id = f"swarm_task_{self.task_counter}_{int(time.time())}"
            
            # Analyze task complexity and requirements
            analysis = await self._analyze_task_requirements(task_description, user_context or {})
            
            task = SwarmTask(
                task_id=task_id,
                description=task_description,
                complexity=analysis['complexity'],
                required_expertise=analysis['required_expertise'],
                required_tools=analysis['required_tools'],
                estimated_duration=analysis['estimated_duration'],
                priority=analysis['priority'],
                assigned_agents=[],
                status='pending',
                created_at=datetime.now()
            )
            
            self.active_tasks[task_id] = task
            
            logger.info("Created swarm task", 
                       task_id=task_id, 
                       complexity=analysis['complexity'].value,
                       required_expertise=analysis['required_expertise'])
            
            return task
            
        except Exception as e:
            logger.error("Failed to create swarm task", error=str(e))
            raise

    async def _analyze_task_requirements(self, description: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze task to determine requirements and complexity"""
        
        # Simple keyword-based analysis (could be enhanced with LLM)
        keywords = description.lower().split()
        
        # Determine complexity
        complexity_indicators = {
            TaskComplexity.SIMPLE: ['simple', 'quick', 'basic', 'single'],
            TaskComplexity.MODERATE: ['analyze', 'create', 'design', 'implement'],
            TaskComplexity.COMPLEX: ['complex', 'comprehensive', 'multi-step', 'coordinate'],
            TaskComplexity.ENTERPRISE: ['enterprise', 'strategic', 'full-scale', 'complete']
        }
        
        complexity = TaskComplexity.SIMPLE
        for level, indicators in complexity_indicators.items():
            if any(indicator in keywords for indicator in indicators):
                complexity = level
                
        # Determine required expertise
        expertise_mapping = {
            'security': ['security', 'vulnerability', 'threat', 'audit'],
            'data_analysis': ['data', 'analytics', 'insights', 'metrics'],
            'design': ['design', 'ui', 'ux', 'interface', 'visual'],
            'architecture': ['architecture', 'system', 'technical', 'infrastructure'],
            'business': ['business', 'strategy', 'financial', 'market'],
            'project_management': ['project', 'manage', 'coordinate', 'timeline'],
            'content': ['content', 'writing', 'documentation', 'communication']
        }
        
        required_expertise = []
        for expertise, indicators in expertise_mapping.items():
            if any(indicator in keywords for indicator in indicators):
                required_expertise.append(expertise)
        
        # Default to general if no specific expertise identified
        if not required_expertise:
            required_expertise = ['general']
            
        # Determine required tools (simplified)
        required_tools = []
        if any(tool_indicator in keywords for tool_indicator in ['search', 'web', 'research']):
            required_tools.extend(['WebSearch', 'WebFetch'])
        if any(tool_indicator in keywords for tool_indicator in ['write', 'create', 'document']):
            required_tools.extend(['Write', 'Edit'])
        if any(tool_indicator in keywords for tool_indicator in ['analyze', 'data', 'query']):
            required_tools.extend(['query_knowledge_base', 'search_knowledge'])
            
        # Estimate duration based on complexity
        duration_map = {
            TaskComplexity.SIMPLE: 5,
            TaskComplexity.MODERATE: 15,
            TaskComplexity.COMPLEX: 45,
            TaskComplexity.ENTERPRISE: 120
        }
        
        # Determine priority (default medium)
        priority_indicators = {
            10: ['urgent', 'critical', 'emergency'],
            8: ['important', 'priority', 'asap'],
            5: ['normal', 'standard'],
            3: ['low', 'when_possible', 'future']
        }
        
        priority = 5  # Default medium
        for pri_level, indicators in priority_indicators.items():
            if any(indicator in keywords for indicator in indicators):
                priority = pri_level
                break
                
        return {
            'complexity': complexity,
            'required_expertise': required_expertise,
            'required_tools': required_tools,
            'estimated_duration': duration_map[complexity],
            'priority': priority
        }

    async def assign_optimal_swarm(self, task_id: str) -> List[SwarmAgent]:
        """Assign optimal swarm of agents to task using intelligent selection"""
        try:
            task = self.active_tasks.get(task_id)
            if not task:
                raise ValueError(f"Task {task_id} not found")
            
            # Get available agents
            available_agents = [agent for agent in self.agents.values() 
                             if agent.is_available and agent.current_load < 0.8]
            
            # Select optimal swarm based on task requirements
            selected_agents = await self._select_optimal_agents(task, available_agents)
            
            # Determine best coordination pattern
            pattern = await self._select_coordination_pattern(task, selected_agents)
            task.coordination_pattern = pattern
            
            # Assign agents and update their status
            task.assigned_agents = [agent.agent_key for agent in selected_agents]
            for agent in selected_agents:
                agent.current_load += 0.2  # Approximate load increase
                agent.last_active = datetime.now()
                
            task.status = 'assigned'
            
            logger.info("Assigned optimal swarm to task",
                       task_id=task_id,
                       agents=[a.name for a in selected_agents],
                       pattern=pattern)
            
            return selected_agents
            
        except Exception as e:
            logger.error("Failed to assign swarm", task_id=task_id, error=str(e))
            raise

    async def _select_optimal_agents(self, task: SwarmTask, available_agents: List[SwarmAgent]) -> List[SwarmAgent]:
        """Select optimal agents based on expertise match and performance"""
        
        # Always include Ali as coordinator for complex tasks
        selected = []
        ali_agent = next((agent for agent in available_agents if agent.role == SwarmRole.COORDINATOR), None)
        if ali_agent and task.complexity.value >= 2:
            selected.append(ali_agent)
            
        # Score agents based on expertise match
        agent_scores = []
        for agent in available_agents:
            if agent in selected:
                continue
                
            score = self._calculate_agent_fitness_score(agent, task)
            agent_scores.append((agent, score))
            
        # Sort by score and select top agents
        agent_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Determine how many agents needed based on complexity
        agent_count_map = {
            TaskComplexity.SIMPLE: 1,
            TaskComplexity.MODERATE: 2,
            TaskComplexity.COMPLEX: 4,
            TaskComplexity.ENTERPRISE: 6
        }
        
        target_count = agent_count_map[task.complexity]
        remaining_slots = target_count - len(selected)
        
        # Add top scoring agents
        for agent, score in agent_scores[:remaining_slots]:
            selected.append(agent)
            
        return selected

    def _calculate_agent_fitness_score(self, agent: SwarmAgent, task: SwarmTask) -> float:
        """Calculate how well an agent fits a task"""
        score = 0.0
        
        # Expertise match (40% weight)
        expertise_match = len(set(agent.expertise_areas) & set(task.required_expertise))
        max_expertise = max(len(task.required_expertise), 1)
        score += (expertise_match / max_expertise) * 0.4
        
        # Tool availability (20% weight) 
        tool_match = len(set(agent.tools) & set(task.required_tools))
        max_tools = max(len(task.required_tools), 1)
        score += (tool_match / max_tools) * 0.2
        
        # Performance metrics (25% weight)
        score += agent.success_rate * 0.15
        score += (1.0 - agent.current_load) * 0.1  # Prefer less loaded agents
        
        # Coordination ability (15% weight)
        score += agent.coordination_score * 0.15
        
        return score

    async def _select_coordination_pattern(self, task: SwarmTask, agents: List[SwarmAgent]) -> str:
        """Select best coordination pattern for task and agents"""
        
        # Simple pattern selection based on task characteristics
        if task.complexity == TaskComplexity.SIMPLE:
            return "sequential"
        elif len(agents) <= 2:
            return "sequential"
        elif task.complexity == TaskComplexity.ENTERPRISE:
            return "hierarchical"
        elif 'creative' in task.description.lower() or 'innovation' in task.description.lower():
            return "swarm"
        elif len(agents) >= 4:
            return "parallel"
        else:
            return "sequential"

    async def execute_swarm_task(self, task_id: str) -> Dict[str, Any]:
        """Execute task with assigned swarm using selected coordination pattern"""
        try:
            task = self.active_tasks.get(task_id)
            if not task:
                raise ValueError(f"Task {task_id} not found")
                
            if not task.assigned_agents:
                await self.assign_optimal_swarm(task_id)
            
            task.status = 'in_progress'
            task.started_at = datetime.now()
            
            # Execute based on coordination pattern
            result = await self._execute_with_pattern(task)
            
            task.status = 'completed'
            task.completed_at = datetime.now()
            
            # Update agent performance metrics
            await self._update_agent_metrics(task, success=True)
            
            logger.info("Swarm task completed successfully",
                       task_id=task_id,
                       duration=(task.completed_at - task.started_at).total_seconds())
            
            return result
            
        except Exception as e:
            logger.error("Swarm task execution failed", task_id=task_id, error=str(e))
            task.status = 'failed'
            await self._update_agent_metrics(task, success=False)
            raise

    async def _execute_with_pattern(self, task: SwarmTask) -> Dict[str, Any]:
        """Execute task using the selected coordination pattern"""
        
        pattern = task.coordination_pattern
        
        if pattern == "sequential":
            return await self._execute_sequential(task)
        elif pattern == "parallel":
            return await self._execute_parallel(task)
        elif pattern == "hierarchical":
            return await self._execute_hierarchical(task)
        elif pattern == "swarm":
            return await self._execute_swarm_pattern(task)
        else:
            return await self._execute_sequential(task)  # Fallback

    async def _execute_sequential(self, task: SwarmTask) -> Dict[str, Any]:
        """Execute task with agents working in sequence"""
        results = []
        previous_output = task.description
        
        for agent_key in task.assigned_agents:
            agent = self.agents[agent_key]
            
            # Simulate agent processing (in real implementation, call actual agent)
            result = {
                'agent': agent.name,
                'input': previous_output,
                'output': f"{agent.name} processed: {previous_output[:100]}...",
                'execution_time': 2.5,
                'success': True
            }
            
            results.append(result)
            previous_output = result['output']
            
            # Small delay to simulate processing
            await asyncio.sleep(0.1)
            
        return {
            'pattern': 'sequential',
            'results': results,
            'final_output': previous_output
        }

    async def _execute_parallel(self, task: SwarmTask) -> Dict[str, Any]:
        """Execute task with agents working in parallel"""
        # Simulate parallel execution
        tasks_to_execute = []
        
        for agent_key in task.assigned_agents:
            agent = self.agents[agent_key]
            tasks_to_execute.append(self._simulate_agent_execution(agent, task))
        
        # Execute all tasks in parallel
        results = await asyncio.gather(*tasks_to_execute)
        
        return {
            'pattern': 'parallel',
            'results': results,
            'final_output': f"Parallel execution completed with {len(results)} agents"
        }

    async def _execute_hierarchical(self, task: SwarmTask) -> Dict[str, Any]:
        """Execute task with hierarchical coordination"""
        # Ali (coordinator) manages other agents
        coordinator = next((self.agents[key] for key in task.assigned_agents 
                          if self.agents[key].role == SwarmRole.COORDINATOR), None)
        
        if not coordinator:
            # Fallback to sequential if no coordinator
            return await self._execute_sequential(task)
            
        # Coordinator delegates subtasks to other agents
        subordinates = [self.agents[key] for key in task.assigned_agents 
                       if self.agents[key] != coordinator]
        
        coordination_result = {
            'coordinator': coordinator.name,
            'subordinate_results': []
        }
        
        for agent in subordinates:
            result = await self._simulate_agent_execution(agent, task)
            coordination_result['subordinate_results'].append(result)
            
        return {
            'pattern': 'hierarchical',
            'results': [coordination_result],
            'final_output': f"Hierarchical execution coordinated by {coordinator.name}"
        }

    async def _execute_swarm_pattern(self, task: SwarmTask) -> Dict[str, Any]:
        """Execute task with self-organizing swarm intelligence"""
        # Simulate emergent swarm behavior
        swarm_state = {
            'iteration': 0,
            'convergence': 0.0,
            'agent_interactions': []
        }
        
        # Multiple iterations with agent interactions
        for iteration in range(3):
            swarm_state['iteration'] = iteration
            iteration_results = []
            
            # Each agent contributes and influences others
            for agent_key in task.assigned_agents:
                agent = self.agents[agent_key]
                result = await self._simulate_swarm_agent_execution(agent, task, swarm_state)
                iteration_results.append(result)
                
            swarm_state['agent_interactions'].extend(iteration_results)
            swarm_state['convergence'] += 0.33  # Simulate convergence
            
        return {
            'pattern': 'swarm',
            'results': swarm_state['agent_interactions'],
            'final_output': f"Swarm intelligence convergence: {swarm_state['convergence']:.2f}"
        }

    async def _simulate_agent_execution(self, agent: SwarmAgent, task: SwarmTask) -> Dict[str, Any]:
        """Simulate individual agent execution (placeholder for real agent calls)"""
        # In real implementation, this would call the actual agent
        await asyncio.sleep(0.1)  # Simulate processing time
        
        return {
            'agent': agent.name,
            'role': agent.role.value,
            'output': f"{agent.name} contributed expertise in {', '.join(agent.expertise_areas[:2])}",
            'execution_time': 2.0 + (len(agent.tools) * 0.1),
            'success': True
        }

    async def _simulate_swarm_agent_execution(self, agent: SwarmAgent, task: SwarmTask, swarm_state: Dict) -> Dict[str, Any]:
        """Simulate agent execution in swarm context with interactions"""
        await asyncio.sleep(0.05)
        
        # Agents influence each other in swarm pattern
        interaction_factor = swarm_state['iteration'] * 0.1
        
        return {
            'agent': agent.name,
            'iteration': swarm_state['iteration'],
            'output': f"{agent.name} swarm contribution with {interaction_factor:.2f} interaction factor",
            'swarm_influence': interaction_factor,
            'success': True
        }

    async def _update_agent_metrics(self, task: SwarmTask, success: bool):
        """Update agent performance metrics based on task outcome"""
        for agent_key in task.assigned_agents:
            agent = self.agents[agent_key]
            
            # Update success rate (exponential moving average)
            if success:
                agent.success_rate = agent.success_rate * 0.9 + 0.1
            else:
                agent.success_rate = agent.success_rate * 0.9
                
            # Update current load (task completed)
            agent.current_load = max(0.0, agent.current_load - 0.2)
            agent.last_active = datetime.now()

    async def get_swarm_status(self) -> Dict[str, Any]:
        """Get comprehensive swarm coordination status"""
        try:
            active_tasks = [task for task in self.active_tasks.values() 
                          if task.status in ['pending', 'in_progress', 'assigned']]
            
            completed_tasks = [task for task in self.active_tasks.values() 
                             if task.status == 'completed']
            
            agent_utilization = {}
            for agent_key, agent in self.agents.items():
                agent_utilization[agent_key] = {
                    'name': agent.name,
                    'role': agent.role.value,
                    'current_load': agent.current_load,
                    'success_rate': agent.success_rate,
                    'is_available': agent.is_available
                }
            
            return {
                'total_agents': len(self.agents),
                'active_tasks': len(active_tasks),
                'completed_tasks': len(completed_tasks),
                'agent_utilization': agent_utilization,
                'coordination_patterns': list(self.coordination_patterns.keys()),
                'system_status': 'operational'
            }
            
        except Exception as e:
            logger.error("Failed to get swarm status", error=str(e))
            return {'system_status': 'error', 'error': str(e)}

# Global swarm coordinator instance
swarm_coordinator = SwarmCoordinator()