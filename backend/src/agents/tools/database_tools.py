"""
Database Tools for Ali and Agent Ecosystem
Direct database access for real-time data queries using SQLAlchemy models
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Add parent directories to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, func
from sqlalchemy.future import select

from src.core.database import get_db_session
from src.models.talent import Talent
from src.models.document import Document, DocumentEmbedding

logger = structlog.get_logger()


class DatabaseTools:
    """Direct database access tools for AI agents"""
    
    @staticmethod
    async def get_database_session() -> AsyncSession:
        """Get async database session"""
        async for session in get_db_session():
            return session

    @classmethod
    async def get_talents_summary(cls) -> Dict[str, Any]:
        """Get comprehensive talents summary with statistics"""
        try:
            db = await cls.get_database_session()
            
            # Get all active talents with basic stats
            talents = await Talent.get_all(db, limit=1000, is_active=True)
            
            # Calculate department distribution
            departments = {}
            positions = {}
            managers_count = 0
            
            for talent in talents:
                # Department distribution
                dept = talent.department or "Unassigned"
                departments[dept] = departments.get(dept, 0) + 1
                
                # Position distribution
                pos = talent.position or "Unspecified"
                positions[pos] = positions.get(pos, 0) + 1
                
                # Count managers
                if talent.subordinates:  # Has subordinates
                    managers_count += 1
            
            await db.close()
            
            return {
                "total_talents": len(talents),
                "active_talents": len([t for t in talents if t.is_active]),
                "departments": departments,
                "positions": positions,
                "managers_count": managers_count,
                "latest_talent": talents[0].username if talents else None,
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
            db = await cls.get_database_session()
            
            talent = await Talent.get_by_username(db, username)
            
            if not talent:
                await db.close()
                return {
                    "error": f"Talent '{username}' not found",
                    "status": "not_found"
                }
            
            # Get hierarchy info
            hierarchy = await Talent.get_hierarchy(db, talent.id)
            
            await db.close()
            
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
            db = await cls.get_database_session()
            
            # Get talents filtered by department if specified
            if department:
                talents = await Talent.get_all(db, limit=1000, department=department, is_active=True)
                title = f"Department: {department}"
            else:
                talents = await Talent.get_all(db, limit=1000, is_active=True)
                title = "All Departments Overview"
            
            if not talents:
                await db.close()
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
            
            await db.close()
            
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
            db = await cls.get_database_session()
            
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
            
            await db.close()
            
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
    async def search_documents(cls, query: str, limit: int = 5) -> Dict[str, Any]:
        """Search documents by content or title"""
        try:
            db = await cls.get_database_session()
            
            # Simple text search in title and content
            search_query = select(Document).where(
                (Document.title.ilike(f"%{query}%")) |
                (Document.content.ilike(f"%{query}%"))
            ).limit(limit)
            
            result = await db.execute(search_query)
            documents = result.scalars().all()
            
            await db.close()
            
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
            db = await cls.get_database_session()
            
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
            
            await db.close()
            
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
        result = asyncio.run(DatabaseTools.get_talents_summary())
        
        if result["status"] == "success":
            departments = result["departments"]
            top_depts = sorted(departments.items(), key=lambda x: x[1], reverse=True)[:3]
            dept_summary = ", ".join([f"{dept}: {count}" for dept, count in top_depts])
            
            return f"""✅ TALENT OVERVIEW:
• Total Active Talents: {result['total_talents']}
• Managers: {result['managers_count']}
• Top Departments: {dept_summary}
• Latest Addition: {result['latest_talent'] or 'None'}"""
        else:
            return f"❌ Error: {result.get('error', 'Unknown error')}"
            
    except Exception as e:
        return f"❌ Query failed: {str(e)}"


def query_talent_details(username: str) -> str:
    """Get detailed information about a specific talent"""
    try:
        result = asyncio.run(DatabaseTools.get_talent_by_username(username))
        
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
        result = asyncio.run(DatabaseTools.get_department_overview(department))
        
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
        result = asyncio.run(DatabaseTools.get_documents_summary())
        
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
        result = asyncio.run(DatabaseTools.search_documents(query))
        
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


def query_system_status() -> str:
    """Get comprehensive system health status"""
    try:
        result = asyncio.run(DatabaseTools.get_system_health())
        
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