"""
Smart Tool Selector
Decides when to use web search vs regular chat based on query analysis
"""

import re
from typing import Dict
import structlog

logger = structlog.get_logger()


class SmartToolSelector:
    """Intelligently decides when tools are needed based on query analysis"""
    
    # Patterns that indicate need for current/real-time information
    REALTIME_PATTERNS = [
        r'\b(current|latest|recent|today|now|this (week|month|year|quarter))\b',
        r'\b(Q[1-4] (FY)?20\d{2})\b',  # Quarter references like Q4 FY2025
        r'\b(earnings|revenue|financial results|stock price)\b',
        r'\b(news|announcement|update|release)\b',
        r'\b(weather|temperature|forecast)\b',
        r'\b(live|real-time|streaming|ongoing)\b',
        r'\b(price|cost|rate|value) (of|for|today)\b',
    ]
    
    # Patterns that indicate need for factual/historical data that might need verification
    FACTUAL_PATTERNS = [
        r'\b(statistics|data|numbers|figures|metrics)\b',
        r'\b(market (share|size|cap|data))\b',
        r'\b(company|corporation|business) (revenue|earnings|profit|valuation)\b',
        r'\b(who (is|was)|when (did|was)|where (is|was)|what (happened|is happening))\b',
        r'\b(verify|confirm|check|validate)\b',
        r'\b(competitor|comparison|versus|vs\.?)\b',
    ]
    
    # Keywords for specific companies/topics that often need current data
    COMPANY_KEYWORDS = [
        'microsoft', 'msft', 'google', 'apple', 'amazon', 'meta', 'tesla',
        'nasdaq', 'dow jones', 's&p', 'stock', 'shares', 'ipo'
    ]
    
    # Date references that indicate time-sensitive queries
    DATE_PATTERNS = [
        r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+20\d{2}\b',
        r'\b20\d{2}[-/]\d{1,2}[-/]\d{1,2}\b',  # Dates like 2025-08-11
        r'\b(yesterday|tomorrow|last (week|month|year)|next (week|month|year))\b',
    ]
    
    # Patterns that DON'T need web search (general knowledge, explanations)
    GENERAL_KNOWLEDGE_PATTERNS = [
        r'\b(explain|describe|define|what (is|are)|how (does|do|to))\b',
        r'\b(difference between|compare|pros and cons)\b',
        r'\b(example|sample|template|format)\b',
        r'\b(best practices|tips|advice|recommendations)\b',
        r'\b(theory|concept|principle|fundamental)\b',
    ]
    
    @classmethod
    def analyze_query(cls, query: str) -> Dict[str, any]:
        """
        Analyze a query to determine what tools are needed
        
        Returns:
            Dict with:
            - needs_web_search: bool
            - confidence: float (0-1)
            - reason: str
            - suggested_tools: List[str]
        """
        query_lower = query.lower()
        
        # Check for real-time information needs
        needs_realtime = any(
            re.search(pattern, query_lower) 
            for pattern in cls.REALTIME_PATTERNS
        )
        
        # Check for factual data needs
        needs_factual = any(
            re.search(pattern, query_lower)
            for pattern in cls.FACTUAL_PATTERNS
        )
        
        # Check for company/financial keywords
        has_company = any(
            keyword in query_lower
            for keyword in cls.COMPANY_KEYWORDS
        )
        
        # Check for date references
        has_dates = any(
            re.search(pattern, query_lower)
            for pattern in cls.DATE_PATTERNS
        )
        
        # Check if it's general knowledge
        is_general = any(
            re.search(pattern, query_lower)
            for pattern in cls.GENERAL_KNOWLEDGE_PATTERNS
        )
        
        # Decision logic
        needs_web_search = False
        confidence = 0.0
        reason = ""
        suggested_tools = []
        
        # High confidence web search needed
        if needs_realtime or has_dates:
            needs_web_search = True
            confidence = 0.9
            reason = "Query requires current/time-sensitive information"
            suggested_tools = ["web_search"]
            
        # Medium-high confidence web search needed
        elif has_company and (needs_factual or 'revenue' in query_lower or 'earnings' in query_lower):
            needs_web_search = True
            confidence = 0.85
            reason = "Company financial data requested"
            suggested_tools = ["web_search"]
            
        # Medium confidence - might need web search
        elif needs_factual and not is_general:
            needs_web_search = True
            confidence = 0.7
            reason = "Factual data that may need verification"
            suggested_tools = ["web_search", "vector_search"]
            
        # Low confidence - probably don't need web search
        elif is_general and not needs_realtime:
            needs_web_search = False
            confidence = 0.8
            reason = "General knowledge question - AI can answer directly"
            suggested_tools = []
            
        # Check for database queries
        if any(word in query_lower for word in ['talent', 'employee', 'project', 'engagement', 'database', 'our data']):
            suggested_tools.append("database_query")
            if not needs_web_search:
                reason = "Internal database query"
                
        # Check for vector search needs
        if any(word in query_lower for word in ['similar', 'related', 'search for', 'find documents']):
            suggested_tools.append("vector_search")
            
        logger.info(
            "Query analysis complete",
            query=query[:100],
            needs_web_search=needs_web_search,
            confidence=confidence,
            reason=reason,
            tools=suggested_tools
        )
        
        return {
            "needs_web_search": needs_web_search,
            "confidence": confidence,
            "reason": reason,
            "suggested_tools": suggested_tools,
            "query_type": cls._classify_query_type(query_lower)
        }
    
    @classmethod
    def _classify_query_type(cls, query: str) -> str:
        """Classify the type of query"""
        if any(word in query for word in ['revenue', 'earnings', 'profit', 'financial']):
            return "financial"
        elif any(word in query for word in ['news', 'latest', 'announcement']):
            return "news"
        elif any(word in query for word in ['how to', 'explain', 'what is']):
            return "educational"
        elif any(word in query for word in ['talent', 'employee', 'project']):
            return "internal_data"
        elif any(word in query for word in ['weather', 'temperature']):
            return "weather"
        else:
            return "general"
    
    @classmethod
    def should_use_web_search(cls, query: str, threshold: float = 0.7) -> bool:
        """
        Simple boolean decision on whether to use web search
        
        Args:
            query: The user query
            threshold: Confidence threshold (0-1)
        
        Returns:
            True if web search should be used
        """
        analysis = cls.analyze_query(query)
        return analysis["needs_web_search"] and analysis["confidence"] >= threshold


# Example usage
def test_queries():
    """Test the smart selector with various queries"""
    
    test_cases = [
        # Should use web search
        "What is Microsoft's Q4 FY2025 revenue?",
        "Latest news about Tesla stock",
        "Current temperature in New York",
        "Apple earnings announcement today",
        
        # Should NOT use web search
        "Explain how machine learning works",
        "What is the difference between TCP and UDP?",
        "Best practices for Python programming",
        "How to write a good resume",
        
        # Database queries
        "How many talents do we have?",
        "Show me our current projects",
        
        # Mixed
        "Compare our revenue with Microsoft's latest earnings",
    ]
    
    selector = SmartToolSelector()
    
    for query in test_cases:
        result = selector.analyze_query(query)
        print(f"\nQuery: {query}")
        print(f"  Need Web: {result['needs_web_search']} (confidence: {result['confidence']:.0%})")
        print(f"  Reason: {result['reason']}")
        print(f"  Tools: {result['suggested_tools']}")


if __name__ == "__main__":
    test_queries()