"""
Tools module for Convergio Agents
Provides functional tools for agents to interact with backend services and data
"""

from .backend_api_client import (
    query_talents_count,
    query_engagements_summary, 
    query_dashboard_stats,
    query_skills_overview,
    get_backend_client
)

from .vector_search_client import (
    get_vector_client,
    embed_text,
    search_similar
)

__all__ = [
    # Backend API tools
    "query_talents_count",
    "query_engagements_summary", 
    "query_dashboard_stats",
    "query_skills_overview",
    "get_backend_client",
    
    # Vector Search tools
    "get_vector_client",
    "embed_text",
    "search_similar"
]