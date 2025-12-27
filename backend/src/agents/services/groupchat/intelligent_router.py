"""
Intelligent Agent Router
Routes queries to the most appropriate single agent based on expertise
"""

import re
import structlog
from typing import List, Optional, Dict, Any

# Optional AutoGen import
try:
    from autogen_agentchat.agents import AssistantAgent
except ImportError:
    AssistantAgent = None  # type: ignore

logger = structlog.get_logger()


class IntelligentAgentRouter:
    """Routes queries to the most appropriate agent based on expertise matching"""
    
    # Agent expertise mapping
    AGENT_EXPERTISE = {
        'amy_cfo': {
            'keywords': ['revenue', 'earnings', 'financial', 'profit', 'budget', 'roi', 'investment', 
                        'cash flow', 'margin', 'capital', 'fiscal', 'quarter', 'fy20', 'q1', 'q2', 'q3', 'q4'],
            'priority': 10,  # High priority for financial queries
            'description': 'CFO - Financial analysis and reporting'
        },
        'ali_chief_of_staff': {
            'keywords': ['strategy', 'coordination', 'overview', 'summary', 'general', 'help', 
                        'plan', 'organize', 'manage', 'coordinate'],
            'priority': 5,  # Medium priority - general coordinator
            'description': 'Chief of Staff - Strategic coordination'
        },
        'sofia_social_media': {
            'keywords': ['social media', 'marketing', 'campaign', 'brand', 'engagement', 
                        'content', 'audience', 'viral', 'instagram', 'twitter', 'linkedin'],
            'priority': 8,
            'description': 'Social Media Manager'
        },
        'baccio_tech_architect': {
            'keywords': ['technical', 'architecture', 'system', 'api', 'database', 'infrastructure',
                        'microservice', 'backend', 'frontend', 'code', 'software'],
            'priority': 8,
            'description': 'Technical Architect'
        },
        'luca_security': {
            'keywords': ['security', 'vulnerability', 'threat', 'audit', 'compliance', 'gdpr',
                        'encryption', 'authentication', 'firewall', 'breach'],
            'priority': 9,
            'description': 'Security Specialist'
        },
        'diana_performance_dashboard': {
            'keywords': ['dashboard', 'metrics', 'kpi', 'performance', 'analytics', 'report',
                        'visualization', 'chart', 'graph', 'monitoring'],
            'priority': 7,
            'description': 'Performance Dashboard Specialist'
        },
        'davide-project-manager': {
            'keywords': ['project', 'timeline', 'milestone', 'deliverable', 'sprint', 'agile',
                        'scrum', 'task', 'deadline', 'resource'],
            'priority': 7,
            'description': 'Project Manager'
        }
    }
    
    @classmethod
    def select_best_agent(
        cls, 
        query: str, 
        available_agents: List[AssistantAgent],
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[AssistantAgent]:
        """
        Select the single best agent for the query.
        
        Args:
            query: The user query
            available_agents: List of available agents
            context: Optional context with hints (e.g., specific agent requested)
        
        Returns:
            The best agent for the query, or None if no good match
        """
        query_lower = query.lower()
        
        # Check if user specifically requested an agent
        if context and 'agent_name' in context:
            requested = context['agent_name'].lower()
            for agent in available_agents:
                if agent.name.lower() == requested:
                    logger.info(f"🎯 User requested specific agent: {agent.name}")
                    return agent
        
        # Score each agent based on keyword matches
        agent_scores = {}
        
        for agent in available_agents:
            agent_name = agent.name.lower()
            score = 0
            
            # Get expertise for this agent
            if agent_name in cls.AGENT_EXPERTISE:
                expertise = cls.AGENT_EXPERTISE[agent_name]
                
                # Count keyword matches
                for keyword in expertise['keywords']:
                    if keyword in query_lower:
                        score += 2  # Each keyword match adds 2 points
                        
                # Add priority bonus
                if score > 0:
                    score += expertise['priority']
                    
                agent_scores[agent.name] = score
                
                if score > 0:
                    logger.debug(f"Agent {agent.name} scored {score} for query")
        
        # If no matches, check for general patterns
        if not any(agent_scores.values()):
            # Financial queries → Amy
            if any(word in query_lower for word in ['revenue', 'earnings', 'financial', 'money', 'cost']):
                for agent in available_agents:
                    if 'amy' in agent.name.lower() or 'cfo' in agent.name.lower():
                        logger.info(f"📊 Routing financial query to {agent.name}")
                        return agent
            
            # Technical queries → Baccio
            elif any(word in query_lower for word in ['code', 'api', 'technical', 'system', 'bug']):
                for agent in available_agents:
                    if 'baccio' in agent.name.lower() or 'tech' in agent.name.lower():
                        logger.info(f"🔧 Routing technical query to {agent.name}")
                        return agent
            
            # Default to Ali for general queries
            for agent in available_agents:
                if 'ali' in agent.name.lower():
                    logger.info(f"📋 Routing general query to {agent.name}")
                    return agent
        
        # Return the highest scoring agent
        if agent_scores:
            best_agent_name = max(agent_scores, key=agent_scores.get)
            best_score = agent_scores[best_agent_name]
            
            for agent in available_agents:
                if agent.name == best_agent_name:
                    logger.info(
                        f"✅ Selected {agent.name} (score: {best_score}) for query: {query[:50]}..."
                    )
                    return agent
        
        # Fallback to first available agent
        if available_agents:
            logger.info(f"⚠️ No specific match, using fallback agent: {available_agents[0].name}")
            return available_agents[0]
        
        return None
    
    @classmethod
    def should_use_single_agent(cls, query: str) -> bool:
        """
        Determine if query should be handled by a single agent vs group discussion.
        
        Most queries should use single agent for efficiency.
        Only complex, multi-faceted queries need group discussion.
        """
        query_lower = query.lower()
        
        # Patterns that might benefit from multiple agents
        multi_agent_patterns = [
            r'compare.*and',  # Comparisons might need multiple perspectives
            r'pros and cons',  # Multiple viewpoints helpful
            r'team.*opinion',  # Explicitly asking for team input
            r'everyone.*think',  # Asking for group consensus
            r'discuss',  # Wants discussion
        ]
        
        for pattern in multi_agent_patterns:
            if re.search(pattern, query_lower):
                logger.info("🤝 Query benefits from multiple agents")
                return False
        
        # Default: use single agent for efficiency
        logger.info("👤 Query should use single agent for efficiency")
        return True