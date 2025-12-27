"""
Agent Framework Tools - Decorated with @ai_function
Migrates from AutoGen FunctionTool/BaseTool to Agent Framework decorator pattern
"""

from typing import Any, Dict, List, Optional, Literal
import json
import asyncio
import os
from datetime import datetime
import structlog
import httpx

try:
    from agent_framework import ai_function
    AGENT_FRAMEWORK_AVAILABLE = True
except ImportError:
    # Fallback decorator for when AF is not installed
    def ai_function(func):
        return func
    AGENT_FRAMEWORK_AVAILABLE = False

from sqlalchemy import text
from src.core.database import get_async_session
from src.models.talent import Talent

logger = structlog.get_logger()


# ================================
# 🌐 WEB SEARCH TOOLS
# ================================

@ai_function
async def web_search(
    query: str,
    max_results: int = 5,
    search_type: Literal["general", "news", "financial", "technical"] = "general"
) -> str:
    """
    Search the internet for current information, news, financial data, or technical documentation.

    Args:
        query: The search query string
        max_results: Maximum number of results to return (default: 5)
        search_type: Type of search - general, news, financial, or technical

    Returns:
        Markdown formatted search results with links and summaries
    """
    try:
        logger.info(f"🔍 Web search: {query}", search_type=search_type)

        # Check for Perplexity API key
        api_key = os.getenv("PERPLEXITY_API_KEY")
        if not api_key:
            return "❌ **Web Search Error**: PERPLEXITY_API_KEY not configured. Please set the API key to enable web search."

        # Use Perplexity's Sonar model for web search
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "sonar",
            "messages": [
                {
                    "role": "user",
                    "content": f"Search for: {query}. Provide concise, factual information with sources."
                }
            ],
            "max_tokens": 1000,
            "temperature": 0.2
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers=headers,
                json=payload
            )

            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

                if content:
                    return f"## 🌐 Web Search Results for: '{query}'\n\n{content}"
                else:
                    return f"❌ No results found for query: '{query}'"

            elif response.status_code == 401:
                return "❌ **Authentication Error**: Invalid Perplexity API key."

            else:
                return f"❌ **Web Search Failed**: Status {response.status_code} - {response.text[:200]}"

    except httpx.TimeoutException:
        return "❌ **Web search timed out** - the search service did not respond in time."
    except Exception as e:
        logger.error(f"Web search error: {e}")
        return f"❌ **Web Search Error**: {str(e)}"


@ai_function
async def search_news(query: str, max_results: int = 5) -> str:
    """
    Search specifically for news articles related to the query.

    Args:
        query: News search query
        max_results: Maximum number of news articles

    Returns:
        Latest news articles with dates and sources
    """
    return await web_search(query, max_results, search_type="news")


@ai_function
async def search_financial(query: str, max_results: int = 5) -> str:
    """
    Search for financial market data, stock prices, economic indicators.

    Args:
        query: Financial search query (e.g., "AAPL stock price", "EUR/USD exchange rate")
        max_results: Maximum number of results

    Returns:
        Financial data and market information
    """
    return await web_search(query, max_results, search_type="financial")


# ================================
# 🗄️ DATABASE TOOLS
# ================================

@ai_function
async def get_talents_summary() -> str:
    """
    Get a comprehensive summary of all talents in the database with statistics.

    Returns:
        JSON string with talent statistics including total count, active count, and distributions
    """
    try:
        async with get_async_session() as db:
            talents = await Talent.get_all(db, limit=1000, is_active=True)

            active_count = sum(1 for t in talents if not t.deleted_at)
            admin_count = sum(1 for t in talents if t.is_admin)

            result = {
                "total_talents": len(talents),
                "active_talents": active_count,
                "admin_count": admin_count,
                "latest_talent": talents[0].email if talents else None,
                "status": "success",
                "timestamp": datetime.utcnow().isoformat()
            }

            return json.dumps(result, indent=2)

    except Exception as e:
        logger.error(f"Database query failed: {e}")
        return json.dumps({
            "error": f"Database query failed: {str(e)}",
            "status": "error"
        })


@ai_function
async def get_talent_by_username(username: str) -> str:
    """
    Get detailed information about a specific talent by their username.

    Args:
        username: The talent's username

    Returns:
        JSON string with talent details or error message
    """
    try:
        async with get_async_session() as db:
            talent = await Talent.get_by_username(db, username)

            if not talent:
                return json.dumps({
                    "error": f"Talent not found: {username}",
                    "status": "not_found"
                })

            result = {
                "username": talent.username,
                "email": talent.email,
                "is_admin": talent.is_admin,
                "is_active": not talent.deleted_at,
                "created_at": talent.created_at.isoformat() if talent.created_at else None,
                "status": "success"
            }

            return json.dumps(result, indent=2)

    except Exception as e:
        logger.error(f"Database query failed: {e}")
        return json.dumps({
            "error": f"Database query failed: {str(e)}",
            "status": "error"
        })


@ai_function
async def search_talents(
    search_term: str,
    limit: int = 10,
    active_only: bool = True
) -> str:
    """
    Search for talents by email, username, or other criteria.

    Args:
        search_term: Search term to match against talent fields
        limit: Maximum number of results (default: 10)
        active_only: Only return active talents (default: True)

    Returns:
        JSON string with matching talents
    """
    try:
        async with get_async_session() as db:
            # Simple search implementation
            talents = await Talent.get_all(db, limit=limit * 2, is_active=active_only)

            # Filter by search term
            search_lower = search_term.lower()
            matching_talents = [
                t for t in talents
                if (search_lower in (t.username or "").lower() or
                    search_lower in (t.email or "").lower())
            ][:limit]

            results = [
                {
                    "username": t.username,
                    "email": t.email,
                    "is_admin": t.is_admin,
                    "is_active": not t.deleted_at
                }
                for t in matching_talents
            ]

            return json.dumps({
                "search_term": search_term,
                "total_found": len(results),
                "results": results,
                "status": "success"
            }, indent=2)

    except Exception as e:
        logger.error(f"Database search failed: {e}")
        return json.dumps({
            "error": f"Database search failed: {str(e)}",
            "status": "error"
        })


# ================================
# 🔍 VECTOR SEARCH TOOLS
# ================================

@ai_function
async def vector_search(
    query: str,
    top_k: int = 5,
    search_type: Literal["semantic", "hybrid", "keyword"] = "semantic"
) -> str:
    """
    Perform semantic search on the knowledge base using vector embeddings.

    Args:
        query: Search query for semantic matching
        top_k: Number of results to return (default: 5)
        search_type: Type of search - semantic (vector), hybrid, or keyword

    Returns:
        Markdown formatted search results with relevance scores
    """
    try:
        logger.info(f"🔍 Vector search: {query}", top_k=top_k, search_type=search_type)

        base_url = os.getenv("BACKEND_URL", "http://localhost:9000")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{base_url}/api/v1/vector/search",
                json={
                    "query": query,
                    "top_k": top_k,
                    "search_type": search_type,
                    "filters": {}
                }
            )

            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])

                if not results:
                    return f"🔍 **No results found** for query: '{query}'"

                markdown_results = [f"## 🔍 Search Results for: '{query}'\n"]
                markdown_results.append(f"**Found {len(results)} relevant documents** ({search_type} search)\n")

                for i, result in enumerate(results[:top_k], 1):
                    title = result.get("title", "Untitled")
                    content = result.get("content", "")
                    score = result.get("similarity_score", 0.0)

                    content_preview = content[:300] + ("..." if len(content) > 300 else "")

                    markdown_results.append(f"### {i}. {title}")
                    markdown_results.append(f"**Relevance Score:** {score:.2f}")
                    markdown_results.append(f"{content_preview}\n")

                return "\n".join(markdown_results)

            elif response.status_code == 404:
                return "❌ **Vector search service not available** - the vector database endpoint is not running."

            else:
                return f"❌ **Vector search failed** with status {response.status_code}"

    except httpx.TimeoutException:
        return "❌ **Vector search timed out** - the search service did not respond in time."
    except Exception as e:
        logger.error(f"Vector search error: {e}")
        return f"❌ **Vector Search Error**: {str(e)}"


@ai_function
async def semantic_knowledge_search(query: str, top_k: int = 3) -> str:
    """
    Search the knowledge base for relevant information using semantic understanding.

    Args:
        query: Natural language query
        top_k: Number of most relevant results

    Returns:
        Relevant knowledge base articles and documentation
    """
    return await vector_search(query, top_k, search_type="semantic")


# ================================
# 📊 UTILITY TOOLS
# ================================

@ai_function
async def get_current_date() -> str:
    """
    Get the current date and time.

    Returns:
        Current date and time in ISO format
    """
    return datetime.now().isoformat()


@ai_function
async def format_as_json(data: Dict[str, Any]) -> str:
    """
    Format data as pretty-printed JSON.

    Args:
        data: Dictionary to format

    Returns:
        Pretty-printed JSON string
    """
    return json.dumps(data, indent=2)


# ================================
# ANALYTICS TOOLS
# ================================

@ai_function
async def get_engagement_analytics(
    analysis_type: Literal["summary", "dashboard", "trends"] = "summary"
) -> str:
    """
    Analyze engagement data and business metrics.

    Args:
        analysis_type: Type of analysis - summary (counts), dashboard (stats), or trends (over time)

    Returns:
        JSON string with engagement analytics data
    """
    try:
        logger.info(f"Fetching engagement analytics", analysis_type=analysis_type)
        base_url = os.getenv("BACKEND_URL", "http://localhost:9000")

        async with httpx.AsyncClient(timeout=30.0) as client:
            if analysis_type == "summary":
                response = await client.get(f"{base_url}/api/v1/engagements")
                if response.status_code == 200:
                    data = response.json()
                    engagements = data if isinstance(data, list) else data.get("data", [])
                    return json.dumps({
                        "total_engagements": len(engagements),
                        "active": sum(1 for e in engagements if str(e.get("status", "")).lower() in ["active", "in_progress"]),
                        "completed": sum(1 for e in engagements if str(e.get("status", "")).lower() in ["completed", "done"]),
                        "status": "success"
                    }, indent=2)
                else:
                    return json.dumps({"error": f"API returned {response.status_code}", "status": "error"})

            elif analysis_type == "dashboard":
                response = await client.get(f"{base_url}/api/v1/dashboard/stats")
                if response.status_code == 200:
                    return json.dumps(response.json(), indent=2)
                else:
                    return json.dumps({"error": "Dashboard stats not available", "status": "error"})

            elif analysis_type == "trends":
                response = await client.get(f"{base_url}/api/v1/engagements")
                if response.status_code == 200:
                    data = response.json()
                    engagements = data if isinstance(data, list) else data.get("data", [])
                    return json.dumps({
                        "total_engagements": len(engagements),
                        "analysis_date": datetime.now().isoformat(),
                        "trends_data": engagements[:10],  # Last 10 for trends
                        "status": "success"
                    }, indent=2)
                else:
                    return json.dumps({"error": f"API returned {response.status_code}", "status": "error"})

    except httpx.TimeoutException:
        return json.dumps({"error": "Request timed out", "status": "error"})
    except Exception as e:
        logger.error(f"Engagement analytics error: {e}")
        return json.dumps({"error": str(e), "status": "error"})


@ai_function
async def get_business_intelligence(
    focus_area: Literal["overview", "talents", "performance", "insights"] = "overview"
) -> str:
    """
    Generate comprehensive business intelligence reports.

    Args:
        focus_area: Focus of the report - overview (all), talents, performance, or insights

    Returns:
        JSON string with business intelligence data
    """
    try:
        logger.info(f"Generating business intelligence", focus_area=focus_area)
        base_url = os.getenv("BACKEND_URL", "http://localhost:9000")

        report = {
            "business_intelligence_report": {
                "generated_at": datetime.now().isoformat(),
                "focus_area": focus_area
            }
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            if focus_area in ["overview", "talents"]:
                # Get talent data
                response = await client.get(f"{base_url}/api/v1/talents")
                if response.status_code == 200:
                    talents = response.json()
                    if isinstance(talents, list):
                        report["talent_analysis"] = {
                            "total": len(talents),
                            "active": sum(1 for t in talents if t.get("is_active", True)),
                            "admins": sum(1 for t in talents if t.get("is_admin", False))
                        }
                else:
                    report["talent_analysis"] = {"error": "Unable to fetch talent data"}

            if focus_area in ["overview", "performance"]:
                # Get performance data
                response = await client.get(f"{base_url}/api/v1/dashboard/stats")
                if response.status_code == 200:
                    report["performance_metrics"] = response.json()
                else:
                    report["performance_metrics"] = {"error": "Dashboard stats unavailable"}

            if focus_area == "insights":
                # Search for insights
                insights_result = await vector_search("business insights performance metrics", top_k=3)
                report["ai_insights"] = insights_result

        return json.dumps(report, indent=2)

    except Exception as e:
        logger.error(f"Business intelligence error: {e}")
        return json.dumps({"error": str(e), "status": "error"})


# ================================
# TOOL REGISTRATION
# ================================

def get_all_agent_framework_tools() -> List[Any]:
    """
    Get all @ai_function decorated tools for Agent Framework.

    Returns:
        List of tool functions
    """
    return [
        # Web search tools
        web_search,
        search_news,
        search_financial,

        # Database tools
        get_talents_summary,
        get_talent_by_username,
        search_talents,

        # Vector search tools
        vector_search,
        semantic_knowledge_search,

        # Analytics tools
        get_engagement_analytics,
        get_business_intelligence,

        # Utility tools
        get_current_date,
        format_as_json,
    ]


def _get_tool_name(tool) -> str:
    """Get name from tool (works with AIFunction and regular functions)."""
    if hasattr(tool, 'name'):
        return tool.name
    return getattr(tool, '__name__', str(tool))


def _get_tool_description(tool) -> str:
    """Get description from tool (works with AIFunction and regular functions)."""
    if hasattr(tool, 'description') and tool.description:
        return tool.description
    doc = getattr(tool, '__doc__', None)
    if doc:
        return doc.strip()
    return "No description"


def get_tool_descriptions() -> Dict[str, str]:
    """
    Get descriptions of all available tools.

    Returns:
        Dictionary mapping tool names to descriptions
    """
    tools = get_all_agent_framework_tools()
    return {
        _get_tool_name(func): _get_tool_description(func)
        for func in tools
    }
