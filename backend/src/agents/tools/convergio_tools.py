"""
🔧 Convergio Custom AutoGen Tools
Advanced tools that integrate AutoGen agents with Convergio backend APIs
"""

from typing import Any, Dict, List, Optional
import json
import asyncio
from datetime import datetime

import structlog
from autogen_ext.tools import BaseTool
import httpx

from .backend_api_client import (
    query_talents_count, 
    query_engagements_summary, 
    query_dashboard_stats, 
    query_skills_overview
)
from .vector_search_client import search_similar, embed_text

logger = structlog.get_logger()


class TalentsQueryTool(BaseTool):
    """Tool for querying talent information from Convergio database"""
    
    name = "query_talents"
    description = "Query talent information from the Convergio database. Returns talent count, departments, skills overview."
    
    def __init__(self):
        super().__init__()
    
    async def run(self, query_type: str = "count") -> str:
        """
        Query talent information
        
        Args:
            query_type: Type of query - "count", "departments", "skills", "all"
        """
        try:
            if query_type == "count":
                result = await query_talents_count()
                return f"Total talents: {result.get('total', 0)}"
            
            elif query_type == "skills":
                result = await query_skills_overview()
                return f"Skills overview: {json.dumps(result, indent=2)}"
            
            elif query_type == "all":
                # Get comprehensive talent information
                async with httpx.AsyncClient() as client:
                    response = await client.get("http://localhost:9000/api/v1/talents")
                    if response.status_code == 200:
                        talents = response.json()
                        summary = {
                            "total_talents": len(talents),
                            "active_talents": len([t for t in talents if t.get("is_active", True)]),
                            "admins": len([t for t in talents if t.get("is_admin", False)]),
                            "departments": list(set([t.get("department", "Unknown") for t in talents])),
                            "recent_talents": [t for t in talents[-3:]]  # Last 3
                        }
                        return json.dumps(summary, indent=2)
            
            return "No data found for the specified query type"
            
        except Exception as e:
            logger.error("❌ TalentsQueryTool error", error=str(e))
            return f"Error querying talents: {str(e)}"


class VectorSearchTool(BaseTool):
    """Tool for semantic search using vector embeddings"""
    
    name = "vector_search"
    description = "Perform semantic search across Convergio knowledge base using vector embeddings"
    
    def __init__(self):
        super().__init__()
    
    async def run(self, query: str, top_k: int = 5) -> str:
        """
        Perform vector search
        
        Args:
            query: Search query text
            top_k: Number of results to return
        """
        try:
            # Embed the query
            query_embedding = await embed_text(query)
            
            # Search for similar content
            results = await search_similar(query_embedding, top_k=top_k)
            
            if not results:
                return f"No relevant results found for: {query}"
            
            formatted_results = []
            for i, result in enumerate(results, 1):
                formatted_results.append(f"{i}. {result.get('content', 'No content')[:200]}...")
            
            return f"Vector search results for '{query}':\n" + "\n".join(formatted_results)
            
        except Exception as e:
            logger.error("❌ VectorSearchTool error", error=str(e))
            return f"Error performing vector search: {str(e)}"


class EngagementAnalyticsTool(BaseTool):
    """Tool for analyzing engagement data and business metrics"""
    
    name = "engagement_analytics"
    description = "Analyze engagement data, business metrics, and dashboard statistics"
    
    def __init__(self):
        super().__init__()
    
    async def run(self, analysis_type: str = "summary") -> str:
        """
        Analyze engagements and business metrics
        
        Args:
            analysis_type: Type of analysis - "summary", "dashboard", "trends"
        """
        try:
            if analysis_type == "summary":
                result = await query_engagements_summary()
                return f"Engagement summary: {json.dumps(result, indent=2)}"
            
            elif analysis_type == "dashboard":
                result = await query_dashboard_stats()
                return f"Dashboard stats: {json.dumps(result, indent=2)}"
            
            elif analysis_type == "trends":
                # Get trend data from multiple sources
                summary = await query_engagements_summary()
                dashboard = await query_dashboard_stats()
                
                trends = {
                    "engagement_trends": summary,
                    "performance_metrics": dashboard,
                    "analysis_date": datetime.now().isoformat(),
                    "key_insights": [
                        "Engagement metrics collected",
                        "Dashboard performance tracked",
                        "Real-time analytics available"
                    ]
                }
                return json.dumps(trends, indent=2)
            
            return "No analytics data available for the specified type"
            
        except Exception as e:
            logger.error("❌ EngagementAnalyticsTool error", error=str(e))
            return f"Error analyzing engagements: {str(e)}"


class BusinessIntelligenceTool(BaseTool):
    """Advanced business intelligence tool combining multiple data sources"""
    
    name = "business_intelligence"
    description = "Comprehensive business intelligence analysis combining talents, engagements, and performance data"
    
    def __init__(self):
        super().__init__()
        self.talents_tool = TalentsQueryTool()
        self.analytics_tool = EngagementAnalyticsTool()
        self.vector_tool = VectorSearchTool()
    
    async def run(self, focus_area: str = "overview") -> str:
        """
        Generate business intelligence report
        
        Args:
            focus_area: Focus area - "overview", "talents", "performance", "insights"
        """
        try:
            report = {
                "business_intelligence_report": {
                    "generated_at": datetime.now().isoformat(),
                    "focus_area": focus_area
                }
            }
            
            if focus_area == "overview" or focus_area == "talents":
                talents_data = await self.talents_tool.run("all")
                report["talent_analysis"] = talents_data
            
            if focus_area == "overview" or focus_area == "performance":
                performance_data = await self.analytics_tool.run("dashboard")
                report["performance_metrics"] = performance_data
            
            if focus_area == "insights":
                # Generate insights using vector search
                insights_query = f"business insights {focus_area} performance metrics trends"
                insights = await self.vector_tool.run(insights_query)
                report["ai_insights"] = insights
            
            return json.dumps(report, indent=2)
            
        except Exception as e:
            logger.error("❌ BusinessIntelligenceTool error", error=str(e))
            return f"Error generating business intelligence: {str(e)}"


# Export available tools
CONVERGIO_TOOLS = [
    TalentsQueryTool(),
    VectorSearchTool(),
    EngagementAnalyticsTool(),
    BusinessIntelligenceTool(),
]