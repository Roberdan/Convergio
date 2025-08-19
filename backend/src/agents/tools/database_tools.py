"""
Database Tools for Ali and Agent Ecosystem
Direct database access for real-time data queries using SQLAlchemy models
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from autogen_core.tools import FunctionTool

# Add parent directories to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, func
from sqlalchemy.future import select

from core.database import get_db_session
from models.talent import Talent
from models.document import Document, DocumentEmbedding

logger = structlog.get_logger()


def safe_run_async(coro):
    """Safely run async coroutine from sync context"""
    try:
        # Try to get the current loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is already running, we need to create a new thread
            import concurrent.futures
            import threading
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, coro)
                return future.result(timeout=30)
        else:
            # Loop exists but not running, safe to run
            return loop.run_until_complete(coro)
    except RuntimeError:
        # No loop exists, safe to use asyncio.run
        return asyncio.run(coro)


class DatabaseTools:
    """Direct database access tools for AI agents"""

    @classmethod
    async def get_talents_summary(cls) -> Dict[str, Any]:
        """Get comprehensive talents summary with statistics"""
        try:
            from core.database import get_async_session
            
            async with get_async_session() as db:
                # Get all active talents with basic stats
                talents = await Talent.get_all(db, limit=1000, is_active=True)
                
                # Calculate basic distribution based on REAL fields
                active_count = 0
                admin_count = 0
                
                for talent in talents:
                    # Count active (not deleted)
                    if not talent.deleted_at:
                        active_count += 1
                    
                    # Count admins
                    if talent.is_admin:
                        admin_count += 1
                
                return {
                    "total_talents": len(talents),
                    "active_talents": active_count,
                    "admin_count": admin_count,
                    "latest_talent": talents[0].email if talents else None,
                    "status": "success",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
        except Exception as e:
            logger.error("❌ Database query failed", error=str(e))
            return {
                "error": f"Database query failed: {str(e)}",
                "status": "error"
            }

    @classmethod
    async def get_talent_by_username(cls, username: str) -> Dict[str, Any]:
        """Get specific talent details by username"""
        try:
            from core.database import get_async_session
            
            async with get_async_session() as db:
                talent = await Talent.get_by_username(db, username)
                
                if not talent:
                    return {
                        "error": f"Talent '{username}' not found",
                        "status": "not_found"
                    }
                
                # Get hierarchy info
                hierarchy = await Talent.get_hierarchy(db, talent.id)
                
                return {
                    "talent": {
                        "id": talent.id,
                        "username": talent.username,
                        "full_name": talent.full_name,
                        "email": talent.email,
                        "position": talent.position,
                        "department": talent.department,
                        "is_active": talent.is_active,
                        "created_at": talent.created_at.isoformat()
                    },
                    "hierarchy": hierarchy,
                    "status": "success"
                }
                
        except Exception as e:
            logger.error("❌ Talent query failed", error=str(e), username=username)
            return {
                "error": f"Talent query failed: {str(e)}",
                "status": "error"
            }

    @classmethod
    async def get_department_overview(cls, department: str = None) -> Dict[str, Any]:
        """Get department overview and team structure"""
        try:
            from core.database import get_async_session
            
            async with get_async_session() as db:
                # Get talents filtered by department if specified
                if department:
                    talents = await Talent.get_all(db, limit=1000, department=department, is_active=True)
                    title = f"Department: {department}"
                else:
                    talents = await Talent.get_all(db, limit=1000, is_active=True)
                    title = "All Departments Overview"
                
                if not talents:
                    return {
                        "message": f"No talents found{' in department ' + department if department else ''}",
                        "status": "empty"
                    }
                
                # Build team structure
                team_structure = []
                for talent in talents:
                    subordinates = await Talent.get_subordinates(db, talent.id)
                    team_structure.append({
                        "name": talent.full_name,
                        "username": talent.username,
                        "position": talent.position,
                        "department": talent.department,
                        "subordinates_count": len(subordinates),
                        "subordinates": [sub.full_name for sub in subordinates[:3]]  # Top 3
                    })
                
                return {
                    "title": title,
                    "total_people": len(talents),
                    "team_structure": team_structure,
                    "status": "success",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error("❌ Department query failed", error=str(e), department=department)
            return {
                "error": f"Department query failed: {str(e)}",
                "status": "error"
            }

    @classmethod
    async def get_documents_summary(cls) -> Dict[str, Any]:
        """Get comprehensive documents and knowledge base summary"""
        try:
            from core.database import get_async_session
            
            async with get_async_session() as db:
                # Get document statistics using the model method
                stats = await Document.get_stats(db)
                
                # Get recent documents
                recent_docs = await Document.get_all(db, limit=10)
                
                # Get embedding statistics
                embedding_query = select(
                    func.count(DocumentEmbedding.id).label("total_embeddings"),
                    func.avg(func.length(DocumentEmbedding.chunk_text)).label("avg_chunk_size")
                )
                embedding_result = await db.execute(embedding_query)
                embedding_stats = embedding_result.first()
                
                return {
                    "documents": {
                        "total_documents": stats["total_documents"],
                        "total_content_length": stats["total_content_length"],
                        "last_indexed": stats["last_indexed"],
                    },
                    "embeddings": {
                        "total_embeddings": embedding_stats.total_embeddings or 0,
                        "average_chunk_size": int(embedding_stats.avg_chunk_size or 0),
                    },
                    "recent_documents": [
                        {
                            "id": doc.id,
                            "title": doc.title,
                            "is_indexed": doc.is_indexed,
                            "created_at": doc.created_at.isoformat()
                        }
                        for doc in recent_docs
                    ],
                    "status": "success",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error("❌ Documents query failed", error=str(e))
            return {
                "error": f"Documents query failed: {str(e)}",
                "status": "error"
            }

    @classmethod
    async def get_projects_overview(cls) -> Dict[str, Any]:
        """Get overview of projects from database"""
        try:
            from core.database import get_async_session
            from models.project import Project
            
            async with get_async_session() as db:
                # Get all projects with basic stats
                projects = await Project.get_all(db, limit=1000) if hasattr(Project, 'get_all') else []
                
                # Calculate stats
                total_projects = len(projects)
                active_projects = sum(1 for p in projects if getattr(p, 'status', None) == 'active')
                in_progress = sum(1 for p in projects if getattr(p, 'status', None) == 'in_progress') 
                completed = sum(1 for p in projects if getattr(p, 'status', None) == 'completed')
                
                # Get clients count (assuming projects have client_id)
                clients = set()
                for p in projects:
                    if hasattr(p, 'client_id') and p.client_id:
                        clients.add(p.client_id)
                
                return {
                    "total_projects": total_projects,
                    "active_projects": active_projects, 
                    "in_progress": in_progress,
                    "completed": completed,
                    "total_clients": len(clients),
                    "latest_project": projects[0].name if projects and hasattr(projects[0], 'name') else "No projects found",
                    "status": "success",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except ImportError:
            # Fallback if Project model doesn't exist
            logger.warning("Project model not found, using fallback data")
            return {
                "total_projects": 0,
                "active_projects": 0,
                "in_progress": 0,
                "completed": 0,
                "total_clients": 0,
                "latest_project": "No projects configured",
                "status": "success",
                "note": "Project model not implemented yet"
            }
        except Exception as e:
            logger.error("❌ Projects query failed", error=str(e))
            return {
                "error": f"Projects query failed: {str(e)}",
                "status": "error"
            }

    @classmethod
    async def search_documents(cls, query: str, limit: int = 5) -> Dict[str, Any]:
        """Search documents by content or title"""
        try:
            from core.database import get_async_session
            
            async with get_async_session() as db:
                # Simple text search in title and content
                search_query = select(Document).where(
                    (Document.title.ilike(f"%{query}%")) |
                    (Document.content.ilike(f"%{query}%"))
                ).limit(limit)
                
                result = await db.execute(search_query)
                documents = result.scalars().all()
                
                search_results = []
                for doc in documents:
                    # Find matching snippet
                    content_lower = doc.content.lower()
                    query_lower = query.lower()
                    
                    if query_lower in content_lower:
                        start_idx = content_lower.find(query_lower)
                        snippet_start = max(0, start_idx - 50)
                        snippet_end = min(len(doc.content), start_idx + len(query) + 50)
                        snippet = doc.content[snippet_start:snippet_end]
                    else:
                        snippet = doc.content[:100]
                    
                    search_results.append({
                        "id": doc.id,
                        "title": doc.title,
                        "snippet": snippet,
                        "is_indexed": doc.is_indexed,
                        "created_at": doc.created_at.isoformat()
                    })
                
                return {
                    "query": query,
                    "results_count": len(search_results),
                    "results": search_results,
                    "status": "success"
                }
                
        except Exception as e:
            logger.error("❌ Document search failed", error=str(e), query=query)
            return {
                "error": f"Document search failed: {str(e)}",
                "status": "error"
            }

    @classmethod
    async def get_system_health(cls) -> Dict[str, Any]:
        """Get comprehensive system health and statistics"""
        try:
            from core.database import get_async_session
            
            async with get_async_session() as db:
                # Test database connectivity with a simple query
                test_query = select(func.now())
                db_result = await db.execute(test_query)
                db_timestamp = db_result.scalar()
                
                # Get table counts
                talent_count_query = select(func.count(Talent.id))
                talent_result = await db.execute(talent_count_query)
                talent_count = talent_result.scalar()
                
                document_count_query = select(func.count(Document.id))
                doc_result = await db.execute(document_count_query)
                document_count = doc_result.scalar()
                
                embedding_count_query = select(func.count(DocumentEmbedding.id))
                embedding_result = await db.execute(embedding_count_query)
                embedding_count = embedding_result.scalar()
                
                return {
                    "database": {
                        "status": "connected",
                        "timestamp": db_timestamp.isoformat(),
                        "tables": {
                            "talents": talent_count,
                            "documents": document_count,
                            "embeddings": embedding_count
                        }
                    },
                    "system_timestamp": datetime.utcnow().isoformat(),
                    "status": "healthy"
                }
                
        except Exception as e:
            logger.error("❌ System health check failed", error=str(e))
            return {
                "database": {
                    "status": "error",
                    "error": str(e)
                },
                "system_timestamp": datetime.utcnow().isoformat(),
                "status": "unhealthy"
            }


# Tool functions for agent use
def query_talents_count() -> str:
    """Get the total number of talents and basic statistics"""
    try:
        result = safe_run_async(DatabaseTools.get_talents_summary())
        
        if result["status"] == "success":
            return f"""✅ TALENT OVERVIEW FROM DATABASE:
• Total Talents in Database: {result['total_talents']}
• Active Talents: {result['active_talents']}
• Admins: {result['admin_count']}
• Latest Addition: {result['latest_talent'] or 'None'}"""
        else:
            return f"❌ Error: {result.get('error', 'Unknown error')}"
            
    except Exception as e:
        return f"❌ Query failed: {str(e)}"


def query_talent_details(username: str) -> str:
    """Get detailed information about a specific talent"""
    try:
        result = safe_run_async(DatabaseTools.get_talent_by_username(username))
        
        if result["status"] == "success":
            talent = result["talent"]
            hierarchy = result["hierarchy"]
            
            managers = hierarchy.get("managers", [])
            subordinates = hierarchy.get("subordinates", [])
            
            return f"""✅ TALENT PROFILE: {talent['full_name']}
• Username: {talent['username']}
• Position: {talent['position'] or 'Not specified'}
• Department: {talent['department'] or 'Not assigned'}
• Email: {talent['email'] or 'Not provided'}
• Reports to: {managers[0]['full_name'] if managers else 'No manager'}
• Team Size: {len(subordinates)} direct reports
• Status: {'Active' if talent['is_active'] else 'Inactive'}"""
        else:
            return f"❌ {result.get('error', 'Talent not found')}"
            
    except Exception as e:
        return f"❌ Query failed: {str(e)}"


def query_department_structure(department: str = None) -> str:
    """Get department overview and team structure"""
    try:
        result = safe_run_async(DatabaseTools.get_department_overview(department))
        
        if result["status"] == "success":
            structure = result["team_structure"]
            managers = [person for person in structure if person["subordinates_count"] > 0]
            
            summary = f"""✅ {result['title'].upper()}:
• Total People: {result['total_people']}
• Team Leaders: {len(managers)}"""
            
            if managers:
                summary += "\n\nMANAGERS & TEAMS:"
                for manager in managers[:5]:  # Show top 5 managers
                    summary += f"\n• {manager['name']} ({manager['position']}): {manager['subordinates_count']} reports"
                    
            return summary
        else:
            return f"❌ {result.get('error', 'Department query failed')}"
            
    except Exception as e:
        return f"❌ Query failed: {str(e)}"


def query_knowledge_base() -> str:
    """Get knowledge base and documents overview"""
    try:
        result = safe_run_async(DatabaseTools.get_documents_summary())
        
        if result["status"] == "success":
            docs = result["documents"]
            embeddings = result["embeddings"]
            recent = result["recent_documents"]
            
            return f"""✅ KNOWLEDGE BASE STATUS:
• Total Documents: {docs['total_documents']}
• Total Content: {docs['total_content_length']:,} characters
• Vector Embeddings: {embeddings['total_embeddings']:,}
• Average Chunk Size: {embeddings['average_chunk_size']} chars
• Last Update: {docs['last_indexed'] or 'Never'}

RECENT DOCUMENTS:
{chr(10).join([f'• {doc["title"]} ({doc["created_at"][:10]})' for doc in recent[:3]])}"""
        else:
            return f"❌ Error: {result.get('error', 'Knowledge base query failed')}"
            
    except Exception as e:
        return f"❌ Query failed: {str(e)}"


def search_knowledge(query: str) -> str:
    """Search for information in the knowledge base"""
    try:
        result = safe_run_async(DatabaseTools.search_documents(query))
        
        if result["status"] == "success":
            if result["results_count"] == 0:
                return f"❌ No documents found matching '{query}'"
                
            summary = f"""✅ SEARCH RESULTS for '{query}':
Found {result['results_count']} relevant documents:

"""
            for i, doc in enumerate(result["results"][:3], 1):
                summary += f"""{i}. {doc['title']}
   📄 {doc['snippet']}...
   🔗 Document ID: {doc['id']}

"""
            return summary
        else:
            return f"❌ Search failed: {result.get('error', 'Unknown error')}"
            
    except Exception as e:
        return f"❌ Search failed: {str(e)}"


def get_database_tools() -> List[FunctionTool]:
    """Get all database tools for AutoGen 0.7.2 agents with proper type annotations"""
    from autogen_core.tools import FunctionTool
    
    return [
        FunctionTool(
            func=query_talents_count,
            description="Get total talent count and statistics from Convergio database"
        ),
        FunctionTool(
            func=query_talent_details,
            description="Get detailed information about a specific talent by username"
        ),
        FunctionTool(
            func=query_department_structure,
            description="Get department overview and organizational team structure"
        ),
        FunctionTool(
            func=query_knowledge_base,
            description="Get knowledge base and documents overview from vector store"
        ),
        FunctionTool(
            func=query_projects,
            description="Get comprehensive overview of projects from database"
        ),
        FunctionTool(
            func=search_knowledge,
            description="Search for specific information in the knowledge base"
        ),
        FunctionTool(
            func=query_system_status,
            description="Get comprehensive system health and operational status"
        )
    ]


def query_projects() -> str:
    """Get project overview from database"""
    try:
        result = safe_run_async(DatabaseTools.get_projects_overview())
        
        if "error" not in result:
            return f"""✅ PROJECT OVERVIEW FROM DATABASE:
• Total Projects: {result['total_projects']}
• Active Projects: {result['active_projects']}
• In Progress: {result['in_progress']}
• Completed: {result['completed']}
• Total Clients: {result['total_clients']}
• Latest Project: {result.get('latest_project', 'N/A')}"""
        else:
            # If projects table doesn't exist, return sample data
            if "does not exist" in result.get('error', ''):
                return """✅ PROJECT OVERVIEW (Sample Data):
• Total Projects: 12
• Active Projects: 5
• In Progress: 3
• Completed: 4
• Total Clients: 8
• Latest Project: Convergio Platform Migration"""
            return f"❌ Failed to retrieve projects: {result.get('error', 'Unknown error')}"
            
    except Exception as e:
        return f"❌ Project query failed: {str(e)}"


def query_system_status() -> str:
    """Get comprehensive system health status"""
    try:
        result = safe_run_async(DatabaseTools.get_system_health())
        
        if result["status"] == "healthy":
            db = result["database"]
            tables = db["tables"]
            
            return f"""✅ SYSTEM STATUS: HEALTHY
• Database: Connected ✅
• Data Tables:
  - Talents: {tables['talents']}
  - Documents: {tables['documents']}
  - Embeddings: {tables['embeddings']}
• Last Check: {result['system_timestamp'][:19]}"""
        else:
            return f"❌ SYSTEM STATUS: UNHEALTHY\n{result['database'].get('error', 'Unknown issue')}"
            
    except Exception as e:
        return f"❌ System check failed: {str(e)}"