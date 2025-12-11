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


def create_sync_db_session():
    """Create a synchronous database session for use in tools.

    This bypasses the async session factory to avoid event loop conflicts.
    Uses a synchronous engine and session for simple database queries.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from core.config import get_settings

    settings = get_settings()
    sync_db_url = settings.DATABASE_URL_SYNC

    engine = create_engine(sync_db_url)
    Session = sessionmaker(bind=engine)
    return Session(), engine


def safe_run_sync_query(query_func):
    """Execute a synchronous database query function.

    Args:
        query_func: A function that takes (session, connection) and returns a result

    Returns:
        The result from query_func
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from core.config import get_settings

    settings = get_settings()
    sync_db_url = settings.DATABASE_URL_SYNC

    engine = create_engine(sync_db_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        result = query_func(session, engine.connect())
        session.commit()
        return result
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()
        engine.dispose()


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
                    talents =await Talent.get_by_department(db,department=department)
                    #talents = await Talent.get_all(db, limit=1000, department=department, is_active=True)
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
            from models.engagement import Engagement
            from sqlalchemy import select, func
            
            async with get_async_session() as db:
                # Get all engagements (projects) with basic stats
                stmt = select(Engagement)
                result = await db.execute(stmt)
                engagements = result.scalars().all()
                
                # Calculate stats
                total_projects = len(engagements)
                active_projects = sum(1 for p in engagements if getattr(p, 'status', None) == 'active')
                in_progress = sum(1 for p in engagements if getattr(p, 'status', None) == 'in_progress') 
                completed = sum(1 for p in engagements if getattr(p, 'status', None) == 'completed')
                planning = sum(1 for p in engagements if getattr(p, 'status', None) == 'planning')
                
                # Get clients count from engagements
                clients = set()
                for p in engagements:
                    if hasattr(p, 'client_id') and p.client_id:
                        clients.add(p.client_id)
                
                return {
                    "total_projects": total_projects,
                    "active_projects": active_projects + in_progress + planning, 
                    "in_progress": in_progress,
                    "planning": planning,
                    "completed": completed,
                    "total_clients": len(clients),
                    "latest_project": engagements[0].title if engagements and hasattr(engagements[0], 'title') else "No projects found",
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


# Tool functions for agent use - using synchronous queries
def query_talents_count() -> str:
    """Get the total number of talents and basic statistics"""
    try:
        from sqlalchemy import create_engine, text
        from core.config import get_settings

        settings = get_settings()
        engine = create_engine(settings.DATABASE_URL_SYNC)

        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM talents WHERE deleted_at IS NULL"))
            total = result.scalar() or 0

            result = conn.execute(text("SELECT COUNT(*) FROM talents WHERE is_admin = true"))
            admin_count = result.scalar() or 0

            result = conn.execute(text("SELECT email FROM talents ORDER BY created_at DESC LIMIT 1"))
            row = result.fetchone()
            latest = row[0] if row else None

        engine.dispose()

        return f"""✅ TALENT OVERVIEW FROM DATABASE:
• Total Talents in Database: {total}
• Active Talents: {total}
• Admins: {admin_count}
• Latest Addition: {latest or 'None'}"""

    except Exception as e:
        return f"❌ Query failed: {str(e)}"


def query_talent_details(username: str) -> str:
    """Get detailed information about a specific talent"""
    try:
        from sqlalchemy import create_engine, text
        from core.config import get_settings

        settings = get_settings()
        engine = create_engine(settings.DATABASE_URL_SYNC)

        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT id, username, full_name, email, position, department, is_active, created_at FROM talents WHERE username = :username"),
                {"username": username}
            )
            row = result.fetchone()

            if not row:
                engine.dispose()
                return f"❌ Talent '{username}' not found"

            talent = {
                "id": row[0],
                "username": row[1],
                "full_name": row[2],
                "email": row[3],
                "position": row[4],
                "department": row[5],
                "is_active": row[6],
                "created_at": row[7]
            }

        engine.dispose()

        return f"""✅ TALENT PROFILE: {talent['full_name']}
• Username: {talent['username']}
• Position: {talent['position'] or 'Not specified'}
• Department: {talent['department'] or 'Not assigned'}
• Email: {talent['email'] or 'Not provided'}
• Status: {'Active' if talent['is_active'] else 'Inactive'}"""

    except Exception as e:
        return f"❌ Query failed: {str(e)}"


def query_department_structure(department: str = None) -> str:
    """Get department overview and team structure"""
    try:
        from sqlalchemy import create_engine, text
        from core.config import get_settings

        settings = get_settings()
        engine = create_engine(settings.DATABASE_URL_SYNC)

        with engine.connect() as conn:
            if department:
                result = conn.execute(
                    text("SELECT COUNT(*) FROM talents WHERE department = :dept AND deleted_at IS NULL"),
                    {"dept": department}
                )
                total = result.scalar() or 0
                title = f"Department: {department}"
            else:
                result = conn.execute(text("SELECT COUNT(*) FROM talents WHERE deleted_at IS NULL"))
                total = result.scalar() or 0
                title = "All Departments Overview"

            result = conn.execute(text("""
                SELECT department, COUNT(*) as cnt
                FROM talents
                WHERE deleted_at IS NULL AND department IS NOT NULL
                GROUP BY department
                ORDER BY cnt DESC
                LIMIT 5
            """))
            dept_counts = result.fetchall()

        engine.dispose()

        summary = f"""✅ {title.upper()}:
• Total People: {total}"""

        if dept_counts:
            summary += "\n\nDEPARTMENTS:"
            for row in dept_counts:
                summary += f"\n• {row[0]}: {row[1]} people"

        return summary

    except Exception as e:
        return f"❌ Query failed: {str(e)}"


def query_knowledge_base() -> str:
    """Get knowledge base and documents overview"""
    try:
        from sqlalchemy import create_engine, text
        from core.config import get_settings

        settings = get_settings()
        engine = create_engine(settings.DATABASE_URL_SYNC)

        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM documents"))
            total_docs = result.scalar() or 0

            result = conn.execute(text("SELECT COALESCE(SUM(LENGTH(content)), 0) FROM documents"))
            total_content = result.scalar() or 0

            result = conn.execute(text("SELECT COUNT(*) FROM document_embeddings"))
            total_embeddings = result.scalar() or 0

            result = conn.execute(text("SELECT title, created_at FROM documents ORDER BY created_at DESC LIMIT 3"))
            recent_docs = result.fetchall()

        engine.dispose()

        recent_list = "\n".join([f'• {row[0]} ({str(row[1])[:10]})' for row in recent_docs]) if recent_docs else "No documents found"

        return f"""✅ KNOWLEDGE BASE STATUS:
• Total Documents: {total_docs}
• Total Content: {total_content:,} characters
• Vector Embeddings: {total_embeddings:,}

RECENT DOCUMENTS:
{recent_list}"""

    except Exception as e:
        return f"❌ Query failed: {str(e)}"


def search_knowledge(query: str) -> str:
    """Search for information in the knowledge base using vector search"""
    try:
        # Use direct vector search API instead of database async issues
        import requests
        
        response = requests.post(
            'http://localhost:9000/api/v1/vector/search',
            json={'query': query, 'top_k': 5},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            
            if not results:
                result = {"status": "success", "results_count": 0, "results": []}
            else:
                result = {
                    "status": "success", 
                    "results_count": len(results),
                    "results": [
                        {
                            "title": r.get("title", "Untitled"),
                            "snippet": r.get("content", "")[:200] + "..." if len(r.get("content", "")) > 200 else r.get("content", ""),
                            "id": r.get("document_id", "unknown"),
                            "similarity": r.get("similarity_score", 0)
                        }
                        for r in results[:3]
                    ]
                }
        else:
            result = {"status": "error", "error": f"Vector API returned {response.status_code}"}
        
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
        # Direct database query without async complications
        from sqlalchemy import create_engine, text
        from core.config import get_settings
        
        settings = get_settings()
        
        # Create synchronous engine
        sync_db_url = settings.DATABASE_URL_SYNC
        engine = create_engine(sync_db_url)
        
        with engine.connect() as conn:
            # Query engagements table directly
            result = conn.execute(text("SELECT COUNT(*) as total, status FROM engagements GROUP BY status"))
            rows = result.fetchall()
            
            total_projects = sum(row[0] for row in rows)
            status_counts = {row[1]: row[0] for row in rows}
            
            active_count = status_counts.get('active', 0) + status_counts.get('in_progress', 0) + status_counts.get('planning', 0)
            
            # Get latest project
            latest_result = conn.execute(text("SELECT title FROM engagements ORDER BY created_at DESC LIMIT 1"))
            latest_row = latest_result.fetchone()
            latest_project = latest_row[0] if latest_row else "No projects found"
            
            result_data = {
                "total_projects": total_projects,
                "active_projects": active_count,
                "completed": status_counts.get('completed', 0),
                "latest_project": latest_project,
                "status_breakdown": status_counts
            }
        
        return f"""✅ PROJECT OVERVIEW FROM DATABASE:
• Total Projects: {result_data['total_projects']}
• Active Projects: {result_data['active_projects']}
• Completed: {result_data['completed']}
• Latest Project: {result_data['latest_project']}
• Status Breakdown: {result_data['status_breakdown']}"""
            
    except Exception as e:
        return f"❌ Project query failed: {str(e)}"


def query_system_status() -> str:
    """Get comprehensive system health status"""
    try:
        from sqlalchemy import create_engine, text
        from core.config import get_settings
        from datetime import datetime

        settings = get_settings()
        engine = create_engine(settings.DATABASE_URL_SYNC)

        with engine.connect() as conn:
            # Test connectivity
            result = conn.execute(text("SELECT NOW()"))
            db_time = result.scalar()

            # Get table counts
            result = conn.execute(text("SELECT COUNT(*) FROM talents"))
            talent_count = result.scalar() or 0

            result = conn.execute(text("SELECT COUNT(*) FROM documents"))
            doc_count = result.scalar() or 0

            result = conn.execute(text("SELECT COUNT(*) FROM document_embeddings"))
            embedding_count = result.scalar() or 0

        engine.dispose()

        return f"""✅ SYSTEM STATUS: HEALTHY
• Database: Connected ✅
• Data Tables:
  - Talents: {talent_count}
  - Documents: {doc_count}
  - Embeddings: {embedding_count}
• Last Check: {datetime.utcnow().isoformat()[:19]}"""

    except Exception as e:
        return f"❌ SYSTEM STATUS: UNHEALTHY\nError: {str(e)}"