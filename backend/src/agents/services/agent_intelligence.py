"""
🧠 Agent Intelligence Service
Real AI-powered responses for individual autonomous agents
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
import httpx
import json
import os

import structlog
from src.agents.utils.config import get_settings
from src.api.user_keys import get_user_api_key, get_user_default_model

logger = structlog.get_logger()
settings = get_settings()


class AgentIntelligence:
    """AI intelligence for individual agents with intelligent decision making"""
    
    def __init__(self, agent_name: str, agent_metadata: Optional[Any] = None):
        self.agent_name = agent_name
        self.agent_metadata = agent_metadata
        self.decision_framework = self._load_decision_framework()
        
    def _load_decision_framework(self) -> str:
        """Load the decision framework from CommonValuesAndPrinciples.md"""
        try:
            import os
            values_path = os.path.join(
                os.path.dirname(__file__), 
                '../definitions/CommonValuesAndPrinciples.md'
            )
            with open(values_path, 'r') as f:
                return f.read()
        except Exception as e:
            logger.warning(f"Could not load CommonValuesAndPrinciples.md: {e}")
            return ""
    
    async def _analyze_intent_and_data_needs(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Analyze user intent and determine data source needs"""
        
        message_lower = message.lower()
        
        # Determine data needs
        needs_internal_data = any(word in message_lower for word in [
            'revenue', 'cost', 'metric', 'kpi', 'performance', 'history',
            'last month', 'last quarter', 'last year', 'trend', 'growth',
            'our', 'company', 'platform', 'convergio'
        ])
        
        needs_ai_analysis = any(word in message_lower for word in [
            'strategy', 'recommend', 'suggest', 'analyze', 'what if',
            'should', 'could', 'would', 'best', 'optimize', 'improve',
            'plan', 'forecast', 'predict', 'compare', 'evaluate'
        ])
        
        needs_clarification = '?' not in message and len(message.split()) < 5
        
        return {
            'needs_internal_data': needs_internal_data,
            'needs_ai_analysis': needs_ai_analysis or not needs_internal_data,
            'needs_clarification': needs_clarification,
            'confidence': 'high' if (needs_internal_data or needs_ai_analysis) else 'medium'
        }
    
    async def _fetch_internal_data(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Fetch relevant data from Convergio DB/Vector using REAL integrations"""
        try:
            logger.info(f"🔍 Fetching REAL internal data for: {message[:100]}")
            
            data_sources = []
            ml = message.lower()
            
            # 1. REAL DATABASE QUERIES
            if any(keyword in ml for keyword in ['talent', 'team', 'staff', 'employee', 'people']):
                from ..tools.database_tools import query_talents_count
                talent_data = query_talents_count()
                data_sources.append(f"📊 Database: {talent_data}")
            
            if any(keyword in ml for keyword in ['document', 'knowledge', 'file', 'content']):
                from ..tools.database_tools import query_knowledge_base
                kb_data = query_knowledge_base()
                data_sources.append(f"📚 Knowledge Base: {kb_data}")
            
            # 2. REAL VECTOR SEARCH (if service is available)
            try:
                import httpx
                async with httpx.AsyncClient() as client:
                    vector_response = await client.post(
                        'http://localhost:9000/api/v1/vector/search',
                        json={'query': message, 'top_k': 3},
                        timeout=5.0
                    )
                    if vector_response.status_code == 200:
                        vector_data = vector_response.json()
                        if vector_data.get('results'):
                            results_summary = f"Found {len(vector_data['results'])} relevant docs"
                            data_sources.append(f"🔍 Vector Search: {results_summary}")
            except Exception as e:
                logger.debug(f"Vector search not available: {e}")
            
            # 3. REAL PERPLEXITY SEARCH (if available)
            perplexity_key = os.getenv("PERPLEXITY_API_KEY")
            if perplexity_key and any(keyword in ml for keyword in ['market', 'competitor', 'trend', 'news', 'current']):
                try:
                    from ..tools.web_search_tool import WebSearchTool
                    from ..tools.web_search_tool import WebSearchArgs
                    
                    web_tool = WebSearchTool(perplexity_key)
                    search_args = WebSearchArgs(query=message, max_results=3)
                    web_result = await web_tool.run(search_args)
                    
                    if '"error"' not in web_result:
                        data_sources.append(f"🌐 Perplexity: Real-time web search completed")
                except Exception as e:
                    logger.debug(f"Perplexity search failed: {e}")
            
            # 4. COMBINE ALL REAL DATA
            if data_sources:
                combined_data = "\n\n".join(data_sources)
                logger.info(f"✅ REAL data fetched from {len(data_sources)} sources")
                return f"REAL DATA SOURCES:\n{combined_data}"
            
            # Only return None if NO real data is available
            logger.info("No real internal data available for this query")
            return None
            
        except Exception as e:
            logger.error(f"Failed to fetch internal data: {e}")
            return None
    
    async def generate_intelligent_response(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        request: Optional[Any] = None
    ) -> str:
        """Generate intelligent response following the decision framework"""
        
        # Step 1: Analyze intent and data needs
        intent_analysis = await self._analyze_intent_and_data_needs(message, context)
        
        # Step 2: Fetch internal data if needed
        internal_data = None
        if intent_analysis['needs_internal_data']:
            internal_data = await self._fetch_internal_data(message, context)
        
        # Step 3: Check if clarification is needed
        if intent_analysis['needs_clarification'] and not internal_data:
            return self._generate_clarification_request(message)
        
        try:
            # Get API key from settings or user session
            api_key = getattr(settings, 'openai_api_key', None) or getattr(settings, 'OPENAI_API_KEY', None)
            if request:
                user_api_key = get_user_api_key(request, "openai")
                api_key = user_api_key or api_key
                
            if not api_key:
                logger.warning(f"No API key available for agent {self.agent_name}")
                if getattr(settings, 'smart_fallback_enabled', False):
                    return self._generate_smart_fallback(message, context)
                return "AI response unavailable: missing API key and smart fallback is disabled"
            
            # Get agent-specific system prompt with internal data
            system_prompt = self._build_agent_system_prompt(internal_data)
            
            # Build enhanced user message with internal data context
            enhanced_message = message
            if internal_data:
                enhanced_message = f"{message}\n\n[Available Internal Data]:\n{internal_data}"
            
            # Prepare the request
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    'https://api.openai.com/v1/chat/completions',
                    headers={
                        'Authorization': f'Bearer {api_key}',
                        'Content-Type': 'application/json'
                    },
                    json={
                        'model': get_user_default_model(request) if request else getattr(settings, 'default_ai_model', 'gpt-4o-mini'),
                        'messages': [
                            {'role': 'system', 'content': system_prompt},
                            {'role': 'user', 'content': enhanced_message}
                        ],
                        'temperature': 0.7,
                        'max_tokens': 500,
                        'stream': False
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result['choices'][0]['message']['content']
                else:
                    logger.error(f"OpenAI API error: {response.status_code}")
                    if getattr(settings, 'smart_fallback_enabled', False):
                        return self._generate_smart_fallback(message, context)
                    return f"AI response error: {response.status_code} (smart fallback disabled)"
                    
        except Exception as e:
            logger.error(f"Failed to generate AI response for {self.agent_name}: {e}")
            if getattr(settings, 'smart_fallback_enabled', False):
                return self._generate_smart_fallback(message, context)
            return f"AI response failed: {e} (smart fallback disabled)"
    
    def _generate_clarification_request(self, message: str) -> str:
        """Generate a clarification request when intent is unclear"""
        
        agent_name = self.agent_name.replace('_', ' ').replace('-', ' ').title()
        
        clarifications = [
            f"I'm {agent_name}, and I want to provide you with the most accurate information.",
            "Could you please clarify a few things:",
            "",
            "• Are you looking for historical data or future projections?",
            "• Is this about our internal metrics or market analysis?",
            "• Would you like strategic recommendations or just data?",
            "",
            f"With more context, I can leverage both our internal data and AI analysis to give you comprehensive insights."
        ]
        
        return "\n".join(clarifications)
    
    def _build_agent_system_prompt(self, internal_data: Optional[str] = None) -> str:
        """Build system prompt based on agent metadata and internal data"""
        
        # Parse agent name to understand role
        agent_id = self.agent_name.lower().replace('_', '-')
        
        # Get agent details from metadata if available
        if self.agent_metadata:
            name = getattr(self.agent_metadata, 'name', self.agent_name)
            description = getattr(self.agent_metadata, 'description', '')
            tier = getattr(self.agent_metadata, 'tier', '')
            tools = getattr(self.agent_metadata, 'tools', [])
            expertise = getattr(self.agent_metadata, 'expertise', [])
        else:
            # Extract from agent name
            name = self.agent_name.replace('_', ' ').replace('-', ' ').title()
            description = ''
            tier = ''
            tools = []
            expertise = []
        
        # Special prompts for known agents
        agent_prompts = {
            'amy-cfo': """You are Amy, the Chief Financial Officer (CFO) of platform.Convergio.io.
You are an expert in financial analysis, budgeting, investment strategy, and financial reporting.
You have access to real financial data and market information.
Provide data-driven financial insights with specific numbers and trends when possible.
Be strategic, analytical, and precise in your financial guidance.""",
            
            'ali-chief-of-staff': """You are Ali, the Chief of Staff and master orchestrator for platform.Convergio.io.
You coordinate a team of 40+ specialized AI agents and provide strategic executive assistance.
You have comprehensive knowledge of the entire platform and can coordinate complex multi-agent operations.
Be strategic, insightful, and action-oriented in your responses.""",
            
            'baccio-tech-architect': """You are Baccio, the Technology Architect for platform.Convergio.io.
You specialize in cloud architecture, system design, scalability, and technical optimization.
Provide detailed technical insights about architecture, infrastructure, and system design.
Be precise, technical, and solution-oriented.""",
            
            'sofia-marketing-strategist': """You are Sofia, the Marketing Strategist for platform.Convergio.io.
You excel in brand positioning, digital marketing, market analysis, and growth strategies.
Provide creative marketing insights backed by data and market trends.
Be innovative, data-driven, and customer-focused.""",
            
            'luca-security-expert': """You are Luca, the Security Expert for platform.Convergio.io.
You specialize in cybersecurity, threat analysis, security audits, and risk assessment.
Provide comprehensive security insights and recommendations.
Be vigilant, thorough, and proactive about security matters.""",
            
            'domik-mckinsey-strategic-decision-maker': """You are Domik, a McKinsey-trained Strategic Decision Maker.
You apply elite consulting frameworks and methodologies to solve complex business problems.
Use structured thinking, data analysis, and strategic frameworks in your responses.
Be analytical, structured, and results-oriented.""",
            
            'omri-data-scientist': """You are Omri, the Data Scientist for platform.Convergio.io.
You specialize in data analysis, machine learning, statistical modeling, and predictive analytics.
Provide data-driven insights using advanced analytical techniques.
Be precise, analytical, and evidence-based.""",
            
            'davide-project-manager': """You are Davide, the Project Manager for platform.Convergio.io.
You excel in project planning, timeline management, resource allocation, and risk mitigation.
Provide structured project management insights and actionable plans.
Be organized, proactive, and detail-oriented."""
        }
        
        # Use specific prompt if available, otherwise build generic one
        if agent_id in agent_prompts:
            base_prompt = agent_prompts[agent_id]
        else:
            base_prompt = f"""You are {name}, a specialized AI agent for platform.Convergio.io.
{description if description else f'You are an expert specialist in your domain.'}
{f'Operating at the {tier} tier of the organization.' if tier else ''}
{f'Your tools include: {", ".join(tools)}' if tools else ''}
{f'Your areas of expertise: {", ".join(expertise)}' if expertise else ''}"""
        
        return f"""{base_prompt}

Current context:
- Platform: Convergio.io - AI-Native Enterprise Platform
- You are part of a 40+ agent ecosystem powered by Microsoft AutoGen
- Provide intelligent, specific, and actionable responses
- Use real data and examples when possible
- Be professional but conversational
- Reference your specific expertise and capabilities
- Timestamp: {datetime.utcnow().isoformat()}

Respond naturally and intelligently to the user's query, leveraging your specific expertise and role."""
    
    def _generate_smart_fallback(self, message: str, context: Optional[Dict[str, Any]]) -> str:
        """Generate a smart fallback response without AI"""
        
        # Parse agent name for context
        agent_id = self.agent_name.lower().replace('_', '-')
        name = self.agent_name.replace('_', ' ').replace('-', ' ').title()
        
        # Analyze message for keywords
        message_lower = message.lower()
        
        # Smart responses based on agent type and message content
        if 'amy' in agent_id or 'cfo' in agent_id:
            if any(word in message_lower for word in ['msft', 'microsoft', 'stock', 'market']):
                return f"As CFO, I need to analyze the latest financial data for Microsoft (MSFT). The stock has shown significant volatility this year. For accurate trend analysis, I would need to access real-time market data and perform a comprehensive financial review including revenue growth, profit margins, and market positioning."
            elif any(word in message_lower for word in ['budget', 'cost', 'expense']):
                return f"From a financial perspective, budget optimization is critical. I recommend conducting a detailed cost analysis across all departments, identifying areas for efficiency improvements, and implementing strategic cost controls while maintaining growth investments."
            else:
                return f"As Chief Financial Officer, I'll provide you with comprehensive financial analysis. {message} requires careful evaluation of financial metrics, market conditions, and strategic implications. Let me analyze the financial aspects and provide data-driven recommendations."
        
        elif 'ali' in agent_id:
            return f"As Chief of Staff, I'm coordinating our response to: {message}. I'll mobilize the appropriate specialist agents from our 40+ agent ecosystem to provide you with comprehensive insights and actionable recommendations. Our strategic approach will cover all critical aspects of your request."
        
        elif 'baccio' in agent_id or 'tech' in agent_id:
            return f"From a technical architecture perspective, {message} requires careful system design consideration. I recommend evaluating scalability requirements, infrastructure optimization, and implementing cloud-native solutions with proper monitoring and security measures."
        
        elif 'sofia' in agent_id or 'marketing' in agent_id:
            return f"From a marketing strategy standpoint, {message} presents interesting opportunities. I suggest developing a comprehensive go-to-market strategy, analyzing customer segments, and implementing data-driven marketing campaigns to maximize reach and conversion."
        
        elif 'luca' in agent_id or 'security' in agent_id:
            return f"From a security perspective, {message} requires thorough risk assessment. I recommend implementing comprehensive security measures including threat monitoring, access controls, encryption, and regular security audits to ensure robust protection."
        
        else:
            # Generic but intelligent response
            role = getattr(self.agent_metadata, 'description', 'specialist')[:50] if self.agent_metadata else 'specialist'
            return f"As {name} ({role}), I'm analyzing your request: {message}. Based on my expertise, I'll provide strategic insights and actionable recommendations tailored to your specific needs. Let me evaluate the key factors and provide a comprehensive response."