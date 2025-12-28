"""
Multi-Agent Routing Fix
Ensures proper multi-agent conversation with turn_count > 1
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import structlog

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat, SelectorGroupChat
from autogen_agentchat.messages import TextMessage
from autogen_agentchat.conditions import MaxMessageTermination

from .intelligent_router import IntelligentAgentRouter
from .metrics import extract_agents_used

logger = structlog.get_logger()


class EnhancedMultiAgentRouter:
    """
    Enhanced router that ensures multi-agent conversations have proper turn counts.
    Fixes the issue where conversations end after a single turn.
    """
    
    def __init__(self):
        self.router = IntelligentAgentRouter()
        self.min_turns_for_complex = 2  # Minimum turns for complex queries
        self.max_turns = 10  # Maximum turns to prevent infinite loops
    
    def analyze_query_complexity(self, query: str) -> Tuple[bool, int]:
        """
        Analyze if a query requires multiple turns.
        
        Args:
            query: User query
        
        Returns:
            Tuple of (requires_multi_turn, suggested_min_turns)
        """
        
        query_lower = query.lower()
        
        # Patterns that definitely need multiple turns
        multi_turn_patterns = {
            # Complex analysis requests
            "analyze": 3,
            "compare": 3,
            "evaluate": 3,
            "assess": 3,
            "review": 3,
            
            # Multi-step processes
            "plan": 4,
            "strategy": 4,
            "roadmap": 4,
            "implement": 5,
            "design": 4,
            
            # Research and investigation
            "research": 3,
            "investigate": 3,
            "explore": 3,
            "study": 3,
            
            # Collaborative tasks
            "discuss": 3,
            "brainstorm": 4,
            "collaborate": 3,
            "coordinate": 3,
            
            # Financial/business analysis
            "forecast": 4,
            "budget": 4,
            "roi": 3,
            "revenue": 3,
            "cost analysis": 4,
            
            # Technical tasks
            "architecture": 4,
            "security audit": 5,
            "performance": 3,
            "optimize": 4,
            "debug": 3
        }
        
        # Check for multi-turn indicators
        for pattern, min_turns in multi_turn_patterns.items():
            if pattern in query_lower:
                logger.info(f"🔄 Query requires multi-turn: pattern='{pattern}', min_turns={min_turns}")
                return True, min_turns
        
        # Check for questions that need multiple perspectives
        if any(word in query_lower for word in ["how", "why", "what if", "should"]):
            if len(query.split()) > 10:  # Longer questions often need discussion
                return True, 2
        
        # Check if explicitly asking for multiple agents
        if any(phrase in query_lower for phrase in ["team", "everyone", "all agents", "discuss"]):
            return True, 3
        
        # Default: use single agent for efficiency
        return False, 1
    
    async def ensure_multi_turn_conversation(
        self,
        group_chat: Any,
        message: str,
        min_turns: int = 2,
        max_turns: int = 10
    ) -> Tuple[List[Any], int]:
        """
        Ensure a conversation has multiple turns.
        
        Args:
            group_chat: GroupChat instance
            message: Initial message
            min_turns: Minimum number of turns required
            max_turns: Maximum turns allowed
        
        Returns:
            Tuple of (messages, actual_turn_count)
        """
        
        messages = []
        turn_count = 0
        
        # Create termination conditions
        termination = MaxMessageTermination(max_turns)
        
        # Start the conversation
        task = TextMessage(content=message, source="user")
        
        try:
            # Run the group chat with proper termination
            result = await group_chat.run(
                task=task,
                termination_condition=termination
            )
            
            if hasattr(result, 'messages'):
                messages = result.messages
                turn_count = len([m for m in messages if hasattr(m, 'source') and m.source != "user"])
            
            # If we didn't reach minimum turns, prompt for continuation
            if turn_count < min_turns:
                logger.info(f"📈 Extending conversation: current={turn_count}, target={min_turns}")
                
                # Add a continuation prompt
                continuation_prompts = [
                    "Please provide more details and analysis.",
                    "What additional considerations should we explore?",
                    "Can you elaborate on the implementation details?",
                    "What are the potential risks and mitigation strategies?",
                    "How would this work in practice?"
                ]
                
                for i in range(min_turns - turn_count):
                    prompt = continuation_prompts[i % len(continuation_prompts)]
                    continuation_task = TextMessage(
                        content=prompt,
                        source="system"
                    )
                    
                    continuation_result = await group_chat.run(
                        task=continuation_task,
                        termination_condition=MaxMessageTermination(2)
                    )
                    
                    if hasattr(continuation_result, 'messages'):
                        messages.extend(continuation_result.messages)
                        turn_count += len([
                            m for m in continuation_result.messages 
                            if hasattr(m, 'source') and m.source not in ["user", "system"]
                        ])
                    
                    if turn_count >= min_turns:
                        break
            
            logger.info(f"✅ Multi-turn conversation completed: turns={turn_count}")
            
        except Exception as e:
            logger.error(f"Multi-turn conversation error: {e}")
        
        return messages, turn_count
    
    def should_use_multi_agent(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, int]:
        """
        Determine if multi-agent conversation is needed and minimum turns.
        
        Args:
            query: User query
            context: Optional context
        
        Returns:
            Tuple of (use_multi_agent, min_turns)
        """
        
        # Check if context explicitly requests multi-agent
        if context and context.get("force_multi_agent"):
            return True, context.get("min_turns", 3)
        
        # Analyze query complexity
        needs_multi, min_turns = self.analyze_query_complexity(query)
        
        if needs_multi:
            logger.info(f"🤝 Multi-agent conversation required: min_turns={min_turns}")
            return True, min_turns
        
        # Use single agent for simple queries
        if not self.router.should_use_single_agent(query):
            # Router says multi-agent but complexity analysis says simple
            # Use multi-agent with minimum 2 turns
            return True, 2
        
        return False, 1
    
    def select_agents_for_task(
        self,
        query: str,
        available_agents: List[AssistantAgent],
        max_agents: int = 4
    ) -> List[AssistantAgent]:
        """
        Select the best agents for a multi-agent task.
        
        Args:
            query: User query
            available_agents: List of available agents
            max_agents: Maximum number of agents to select
        
        Returns:
            List of selected agents
        """
        
        query_lower = query.lower()
        selected = []
        
        # Always include coordinator (Ali)
        for agent in available_agents:
            if "ali" in agent.name.lower() or "chief" in agent.name.lower():
                selected.append(agent)
                break
        
        # Add domain-specific agents based on query
        agent_keywords = {
            "financial": ["amy", "cfo"],
            "technical": ["baccio", "tech"],
            "security": ["luca", "security"],
            "project": ["davide", "project"],
            "marketing": ["sofia", "social"],
            "dashboard": ["diana", "performance"]
        }
        
        for domain, keywords in agent_keywords.items():
            if domain in query_lower:
                for agent in available_agents:
                    if any(kw in agent.name.lower() for kw in keywords):
                        if agent not in selected:
                            selected.append(agent)
                        break
        
        # If we don't have enough agents, add based on general expertise
        if len(selected) < 2:
            # Add the most versatile agents
            for agent in available_agents:
                if agent not in selected:
                    selected.append(agent)
                    if len(selected) >= max_agents:
                        break
        
        # Ensure we have at least 2 agents for multi-agent conversation
        if len(selected) < 2 and len(available_agents) >= 2:
            for agent in available_agents:
                if agent not in selected:
                    selected.append(agent)
                    if len(selected) >= 2:
                        break
        
        logger.info(f"✅ Selected {len(selected)} agents for task: {[a.name for a in selected]}")
        return selected[:max_agents]
    
    async def create_enhanced_group_chat(
        self,
        agents: List[AssistantAgent],
        selection_mode: str = "auto"
    ) -> Any:
        """
        Create an enhanced GroupChat with proper configuration.
        
        Args:
            agents: List of agents
            selection_mode: Selection mode (auto, round_robin, manual)
        
        Returns:
            Configured GroupChat instance
        """
        
        if len(agents) < 2:
            raise ValueError("Multi-agent chat requires at least 2 agents")
        
        if selection_mode == "round_robin":
            # Round-robin ensures all agents participate
            group_chat = RoundRobinGroupChat(
                participants=agents,
                max_turns=self.max_turns
            )
        else:
            # Selector chat for intelligent agent selection
            group_chat = SelectorGroupChat(
                participants=agents,
                model_client=agents[0].model_client,
                max_turns=self.max_turns,
                selector_prompt="""
                Select the next agent to speak based on the conversation context.
                Consider expertise, previous contributions, and the current question.
                Ensure diverse perspectives by rotating between agents when appropriate.
                """
            )
        
        logger.info(f"✅ Created {selection_mode} GroupChat with {len(agents)} agents")
        return group_chat


class MultiAgentConversationFixer:
    """
    Fixes multi-agent conversation issues to ensure proper turn counts.
    """
    
    def __init__(self):
        self.router = EnhancedMultiAgentRouter()
    
    async def fix_conversation_flow(
        self,
        orchestrator: Any,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Fix conversation flow to ensure multi-turn when needed.
        
        Args:
            orchestrator: Orchestrator instance
            message: User message
            context: Optional context
        
        Returns:
            Fixed conversation result
        """
        
        start_time = datetime.now()
        
        # Determine if multi-agent is needed
        use_multi, min_turns = self.router.should_use_multi_agent(message, context)
        
        if not use_multi:
            # Single agent is sufficient
            logger.info("👤 Using single agent for efficiency")
            return {
                "mode": "single_agent",
                "min_turns": 1
            }
        
        # Multi-agent conversation needed
        logger.info(f"🤝 Initiating multi-agent conversation with min_turns={min_turns}")
        
        # Select appropriate agents
        all_agents = list(orchestrator.agents.values())
        selected_agents = self.router.select_agents_for_task(
            message,
            all_agents,
            max_agents=4
        )
        
        # Create enhanced group chat
        group_chat = await self.router.create_enhanced_group_chat(
            selected_agents,
            selection_mode="auto"
        )
        
        # Run conversation with minimum turns
        messages, turn_count = await self.router.ensure_multi_turn_conversation(
            group_chat,
            message,
            min_turns=min_turns,
            max_turns=self.router.max_turns
        )
        
        # Extract results
        agents_used = extract_agents_used(messages)
        duration = (datetime.now() - start_time).total_seconds()
        
        # Build response
        final_response = ""
        for msg in reversed(messages):
            if hasattr(msg, 'content') and isinstance(msg.content, str):
                if hasattr(msg, 'source') and msg.source not in ["user", "system"]:
                    final_response = msg.content
                    break
        
        result = {
            "mode": "multi_agent",
            "response": final_response,
            "agents_used": agents_used,
            "turn_count": turn_count,
            "min_turns": min_turns,
            "duration_seconds": duration,
            "messages": messages
        }
        
        logger.info(
            "✅ Multi-agent conversation completed",
            turn_count=turn_count,
            agents_used=agents_used,
            duration=f"{duration:.2f}s"
        )
        
        return result


# Global fixer instance
_multi_agent_fixer = None


def get_multi_agent_fixer() -> MultiAgentConversationFixer:
    """Get singleton multi-agent fixer"""
    global _multi_agent_fixer
    if _multi_agent_fixer is None:
        _multi_agent_fixer = MultiAgentConversationFixer()
    return _multi_agent_fixer