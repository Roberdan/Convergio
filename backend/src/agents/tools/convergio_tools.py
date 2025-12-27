"""
Convergio Custom Tools
Advanced tools that integrate agents with Convergio backend APIs.
Supports both Agent Framework (@ai_function) and AutoGen (BaseTool) patterns.
"""

from typing import Any, Dict, List, Optional, Literal
import json
import asyncio
from datetime import datetime

import structlog
from pydantic import BaseModel

# Optional autogen import for backward compatibility
try:
    from autogen_core.tools import BaseTool
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False
    # Create a placeholder class if autogen not available
    class BaseTool:
        """Placeholder BaseTool when AutoGen not installed."""
        def __init__(self, *args, **kwargs):
            pass
from .vector_search_client import search_similar, embed_text
from .web_search_tool import (
    WebSearchTool,
    WebBrowseTool,
    get_web_tools,
    WebSearchArgs,
    WebBrowseArgs,
)
import httpx

logger = structlog.get_logger()


class TalentsQueryArgs(BaseModel):
    query_type: Literal["count", "departments", "skills", "all"] = "count"


class TalentsQueryTool(BaseTool):
    """Tool for querying talent information from Convergio database"""
    
    def __init__(self):
        super().__init__(
            args_type=TalentsQueryArgs,
            return_type=str,
            name="query_talents",
            description="Query talent information from the Convergio database. Returns talent count, departments, skills overview."
        )
    
    async def run(self, args: TalentsQueryArgs, cancellation_token=None) -> str:
        """
        Query talent information
        
        Args:
            args: Query arguments containing query_type
            cancellation_token: Optional cancellation token for AutoGen
        """
        try:
            if args.query_type == "count":
                async with httpx.AsyncClient() as client:
                    r = await client.get("http://localhost:9000/api/v1/talents")
                    r.raise_for_status()
                    talents = r.json()
                    total = len(talents) if isinstance(talents, list) else len(talents.get("data", []))
                    return f"Total talents: {total}"
            
            elif args.query_type == "skills":
                async with httpx.AsyncClient() as client:
                    r = await client.get("http://localhost:9000/api/v1/skills")
                    if r.status_code != 200:
                        return "Skills endpoint not available"
                    data = r.json()
                    return f"Skills overview: {json.dumps(data, indent=2)}"
            
            elif args.query_type == "all":
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


class VectorSearchArgs(BaseModel):
    query: str
    top_k: int = 5


class VectorSearchTool(BaseTool):
    """Tool for semantic search using vector embeddings"""
    
    def __init__(self):
        super().__init__(
            args_type=VectorSearchArgs,
            return_type=str,
            name="vector_search",
            description="Perform semantic search across Convergio knowledge base using vector embeddings"
        )
    
    async def run(self, args: VectorSearchArgs, cancellation_token=None) -> str:
        """
        Perform vector search
        
        Args:
            args: Search arguments containing query and top_k
            cancellation_token: Optional cancellation token for AutoGen
        """
        try:
            # Embed the query and get raw vector
            query_vector = await embed_text(args.query)
            if not query_vector:
                return "Embedding failed or unavailable"

            # Search for similar content and format structured results
            search_result = await search_similar(query_vector, limit=args.top_k)
            if search_result.get("error"):
                return f"Vector search error: {search_result['error']}"

            results = search_result.get("results", [])
            if not results:
                return f"No relevant results found for: {args.query}"

            formatted_results = []
            for i, item in enumerate(results[:args.top_k], 1):
                text = item.get("text") or item.get("content") or ""
                score = item.get("similarity_score")
                formatted_results.append(f"{i}. {text[:200]}... (score: {score})")

            return f"Vector search results for '{args.query}':\n" + "\n".join(formatted_results)

        except Exception as e:
            logger.error("❌ VectorSearchTool error", error=str(e))
            return f"Error performing vector search: {str(e)}"


class EngagementAnalyticsArgs(BaseModel):
    analysis_type: Literal["summary", "dashboard", "trends"] = "summary"


class EngagementAnalyticsTool(BaseTool):
    """Tool for analyzing engagement data and business metrics"""
    
    def __init__(self):
        super().__init__(
            args_type=EngagementAnalyticsArgs,
            return_type=str,
            name="engagement_analytics",
            description="Analyze engagement data, business metrics, and dashboard statistics"
        )
    
    async def run(self, args: EngagementAnalyticsArgs, cancellation_token=None) -> str:
        """
        Analyze engagements and business metrics
        
        Args:
            args: Analysis arguments containing analysis_type
            cancellation_token: Optional cancellation token for AutoGen
        """
        try:
            if args.analysis_type == "summary":
                async with httpx.AsyncClient() as client:
                    r = await client.get("http://localhost:9000/api/v1/engagements")
                    r.raise_for_status()
                    data = r.json()
                    engagements = data if isinstance(data, list) else data.get("data", [])
                    total = len(engagements)
                    active = sum(1 for e in engagements if str(e.get("status", "")).lower() in ["active", "in_progress", "ongoing"])
                    completed = sum(1 for e in engagements if str(e.get("status", "")).lower() in ["completed", "finished", "done"])
                    return json.dumps({
                        "total_engagements": total,
                        "active_engagements": active,
                        "completed_engagements": completed
                    }, indent=2)
            
            elif args.analysis_type == "dashboard":
                async with httpx.AsyncClient() as client:
                    r = await client.get("http://localhost:9000/api/v1/dashboard/stats")
                    if r.status_code != 200:
                        return "Dashboard stats endpoint not available"
                    return f"Dashboard stats: {json.dumps(r.json(), indent=2)}"
            
            elif args.analysis_type == "trends":
                # Get trend data from multiple sources
                async with httpx.AsyncClient() as client:
                    sr = await client.get("http://localhost:9000/api/v1/engagements")
                    summary_data = []
                    if sr.status_code == 200:
                        data = sr.json()
                        summary_data = data if isinstance(data, list) else data.get("data", [])
                    dr = await client.get("http://localhost:9000/api/v1/dashboard/stats")
                    dashboard_data = dr.json() if dr.status_code == 200 else {}
                
                trends = {
                    "engagement_trends": summary_data,
                    "performance_metrics": dashboard_data,
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


class BusinessIntelligenceArgs(BaseModel):
    focus_area: Literal["overview", "talents", "performance", "insights"] = "overview"


class BusinessIntelligenceTool(BaseTool):
    """Advanced business intelligence tool combining multiple data sources"""
    
    def __init__(self):
        super().__init__(
            args_type=BusinessIntelligenceArgs,
            return_type=str,
            name="business_intelligence",
            description="Comprehensive business intelligence analysis combining talents, engagements, and performance data"
        )
        self.talents_tool = TalentsQueryTool()
        self.analytics_tool = EngagementAnalyticsTool()
        self.vector_tool = VectorSearchTool()
    
    async def run(self, args: BusinessIntelligenceArgs, cancellation_token=None) -> str:
        """
        Generate business intelligence report
        
        Args:
            args: Business intelligence arguments containing focus_area
            cancellation_token: Optional cancellation token for AutoGen
        """
        try:
            report = {
                "business_intelligence_report": {
                    "generated_at": datetime.now().isoformat(),
                    "focus_area": args.focus_area
                }
            }
            
            if args.focus_area == "overview" or args.focus_area == "talents":
                talents_data = await self.talents_tool.run(TalentsQueryArgs(query_type="all"), cancellation_token)
                report["talent_analysis"] = talents_data
            
            if args.focus_area == "overview" or args.focus_area == "performance":
                performance_data = await self.analytics_tool.run(EngagementAnalyticsArgs(analysis_type="dashboard"), cancellation_token)
                report["performance_metrics"] = performance_data
            
            if args.focus_area == "insights":
                # Generate insights using vector search
                insights_query = f"business insights {args.focus_area} performance metrics trends"
                insights = await self.vector_tool.run(VectorSearchArgs(query=insights_query), cancellation_token)
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
    WebSearchTool(),  # Web search for current information
    WebBrowseTool(),  # Web browsing for content extraction
]