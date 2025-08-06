"""
📊 Create Sample Data for Convergio Database
Populates database with realistic sample data for talent management, documents, and vector embeddings
"""

import asyncio
import sys
from datetime import datetime, timedelta
from typing import List
import random

# Add backend to path
sys.path.append('.')

from src.core.database import get_db_session, init_db
from src.models.talent import Talent
from src.models.document import Document, DocumentEmbedding

async def create_sample_talents(db_session) -> List[Talent]:
    """Create sample talent data"""
    
    print("📊 Creating sample talents...")
    
    sample_talents = [
        {
            "username": "roberdan",
            "full_name": "Roberto Daniele",
            "email": "roberdan@convergio.io",
            "position": "CEO & Founder",
            "department": "Executive",
            "is_active": True,
            "subordinates": [],
        },
        {
            "username": "ali.chief",
            "full_name": "Ali Hassan",
            "email": "ali@convergio.io", 
            "position": "Chief of Staff",
            "department": "Executive",
            "is_active": True,
            "subordinates": [],
        },
        {
            "username": "amy.cfo",
            "full_name": "Amy Chen",
            "email": "amy@convergio.io",
            "position": "Chief Financial Officer",
            "department": "Finance",
            "is_active": True,
            "subordinates": [],
        },
        {
            "username": "baccio.tech",
            "full_name": "Baccio Rossi",
            "email": "baccio@convergio.io",
            "position": "Tech Architect",
            "department": "Engineering",
            "is_active": True,
            "subordinates": [],
        },
        {
            "username": "sofia.marketing",
            "full_name": "Sofia Martinez",
            "email": "sofia@convergio.io",
            "position": "Marketing Strategist",
            "department": "Marketing",
            "is_active": True,
            "subordinates": [],
        },
        {
            "username": "luca.security",
            "full_name": "Luca Neri",
            "email": "luca@convergio.io",
            "position": "Security Expert",
            "department": "Security",
            "is_active": True,
            "subordinates": [],
        },
        {
            "username": "giulia.hr",
            "full_name": "Giulia Verdi",
            "email": "giulia@convergio.io",
            "position": "HR Director",
            "department": "Human Resources",
            "is_active": True,
            "subordinates": [],
        },
        {
            "username": "marco.devops",
            "full_name": "Marco Bianchi",
            "email": "marco@convergio.io",
            "position": "DevOps Engineer",
            "department": "Engineering",
            "is_active": True,
            "subordinates": [],
        },
        {
            "username": "diana.analytics",
            "full_name": "Diana Kumar",
            "email": "diana@convergio.io",
            "position": "Performance Dashboard Specialist",
            "department": "Analytics",
            "is_active": True,
            "subordinates": [],
        },
        {
            "username": "omri.data",
            "full_name": "Omri Cohen",
            "email": "omri@convergio.io",
            "position": "Data Scientist",
            "department": "Data Science",
            "is_active": True,
            "subordinates": [],
        },
        # Additional team members
        {
            "username": "andrea.cs",
            "full_name": "Andrea Rossi",
            "email": "andrea@convergio.io",
            "position": "Customer Success Manager",
            "department": "Customer Success",
            "is_active": True,
            "subordinates": [],
        },
        {
            "username": "fabio.sales",
            "full_name": "Fabio Romano",
            "email": "fabio@convergio.io",
            "position": "Business Development",
            "department": "Sales",
            "is_active": True,
            "subordinates": [],
        },
    ]
    
    created_talents = []
    
    for talent_data in sample_talents:
        try:
            # Check if talent already exists
            existing = await Talent.get_by_username(db_session, talent_data["username"])
            if existing:
                print(f"  ⚠️  Talent {talent_data['username']} already exists, skipping...")
                created_talents.append(existing)
                continue
            
            talent = await Talent.create(
                db_session,
                username=talent_data["username"],
                full_name=talent_data["full_name"],
                email=talent_data["email"],
                position=talent_data["position"],
                department=talent_data["department"],
                is_active=talent_data["is_active"],
                subordinates=talent_data["subordinates"]
            )
            created_talents.append(talent)
            print(f"  ✅ Created talent: {talent.full_name} ({talent.position})")
            
        except Exception as e:
            print(f"  ❌ Failed to create talent {talent_data['username']}: {e}")
    
    await db_session.commit()
    return created_talents


async def create_sample_documents(db_session) -> List[Document]:
    """Create sample document data"""
    
    print("📚 Creating sample documents...")
    
    sample_documents = [
        {
            "title": "Convergio 2030 Strategic Vision",
            "content": """Convergio 2030 represents our ambitious vision for the future of AI-native business platforms. 
            Our platform consolidates talent management, project orchestration, and AI agent coordination into a single, 
            unified system. Key strategic priorities include: 1) Multi-agent AI orchestration with AutoGen, 
            2) Vector-based knowledge management, 3) Real-time business intelligence, 4) Scalable cloud architecture, 
            5) Advanced security and compliance frameworks. Target markets include enterprise organizations seeking 
            AI-first business operations, consulting firms, and technology companies building AI-native workflows.""",
            "document_type": "strategic_plan",
            "is_indexed": True
        },
        {
            "title": "AutoGen Integration Best Practices",
            "content": """AutoGen 0.7.1 integration guide for Convergio platform. Key implementation areas:
            1) Agent Definition Management: Store agent definitions in markdown format with specialized roles
            2) Conversation Management: Implement persistent conversation history with Redis and PostgreSQL
            3) Tool Integration: Custom tools for database queries, vector search, and business intelligence
            4) Memory System: Long-term memory using AutoGen Memory with embedding-based retrieval
            5) Security Framework: Multi-layer validation with prompt injection protection
            6) Performance Optimization: Async operations, connection pooling, and response streaming""",
            "document_type": "technical_guide",
            "is_indexed": True
        },
        {
            "title": "Team Organization Structure 2024",
            "content": """Convergio organizational structure focuses on cross-functional AI-augmented teams:
            
            Executive Team:
            - Roberto Daniele (CEO & Founder): Strategic vision and business leadership
            - Ali Hassan (Chief of Staff): Executive coordination and strategic planning
            - Amy Chen (CFO): Financial planning and investment analysis
            
            Technical Team:
            - Baccio Rossi (Tech Architect): System architecture and technical strategy
            - Marco Bianchi (DevOps Engineer): Infrastructure and deployment automation
            - Luca Neri (Security Expert): Cybersecurity and compliance
            
            Business Operations:
            - Sofia Martinez (Marketing Strategist): Brand positioning and customer acquisition
            - Giulia Verdi (HR Director): Talent management and organizational culture
            - Andrea Rossi (Customer Success): Client relationships and satisfaction
            - Fabio Romano (Business Development): Partnership and revenue growth
            
            Data & Analytics:
            - Diana Kumar (Performance Dashboard): Business intelligence and metrics
            - Omri Cohen (Data Scientist): Advanced analytics and machine learning""",
            "document_type": "organizational_chart",
            "is_indexed": True
        },
        {
            "title": "Q4 2024 Business Metrics",
            "content": """Convergio Q4 2024 Performance Summary:
            
            Financial Metrics:
            - Total Revenue: $1,094,221 (32.7% growth YoY)
            - Active Customers: 1,579 customers
            - Monthly Recurring Revenue: $145,000
            - Customer Acquisition Cost: $2,400
            - Customer Lifetime Value: $18,500
            
            Operational Metrics:
            - Active Projects: 8 strategic initiatives
            - Team Size: 12 core team members
            - AI Agents Deployed: 40+ specialized agents
            - Platform Uptime: 99.7%
            - Average Response Time: 180ms
            
            Strategic Initiatives:
            1) Atlas Product Launch Q4 - 78% complete, $500K revenue target
            2) Brazil Market Analysis - 45% complete, $1.2M opportunity
            3) FitTech AI Series A - 92% complete, $5M funding round""",
            "document_type": "business_metrics",
            "is_indexed": True
        },
        {
            "title": "AI Agent Coordination Protocols",
            "content": """Standard operating procedures for AI agent coordination within Convergio platform:
            
            Agent Hierarchy:
            - Ali (Chief of Staff): Primary coordinator and strategic oversight
            - Specialized Agents: Domain experts with specific tool access
            - Support Agents: Operational and administrative functions
            
            Coordination Patterns:
            1) Direct Delegation: Ali assigns tasks to appropriate specialists
            2) Collaborative Consultation: Multiple agents contribute expertise
            3) Sequential Workflows: Tasks flow through multiple agent checkpoints
            4) Parallel Processing: Independent agents work simultaneously
            
            Communication Protocols:
            - All agent interactions logged and traceable
            - Context sharing through AutoGen Memory system
            - Real-time status updates and progress tracking
            - Escalation procedures for complex decisions""",
            "document_type": "operational_procedures",
            "is_indexed": True
        }
    ]
    
    created_documents = []
    
    for doc_data in sample_documents:
        try:
            # Check if document already exists
            existing_docs = await Document.get_all(db_session, limit=100)
            if any(doc.title == doc_data["title"] for doc in existing_docs):
                print(f"  ⚠️  Document '{doc_data['title']}' already exists, skipping...")
                continue
            
            document = await Document.create(
                db_session,
                title=doc_data["title"],
                content=doc_data["content"],
                document_type=doc_data["document_type"],
                is_indexed=doc_data["is_indexed"]
            )
            created_documents.append(document)
            print(f"  ✅ Created document: {document.title}")
            
        except Exception as e:
            print(f"  ❌ Failed to create document '{doc_data['title']}': {e}")
    
    await db_session.commit()
    return created_documents


async def create_sample_embeddings(db_session, documents: List[Document]):
    """Create sample vector embeddings for documents"""
    
    print("🧠 Creating sample embeddings...")
    
    for document in documents:
        try:
            # Create sample chunks (in real implementation, would use proper text chunking)
            content = document.content
            chunks = [content[i:i+500] for i in range(0, len(content), 400)]  # Overlap chunks
            
            for i, chunk in enumerate(chunks):
                if len(chunk.strip()) < 50:  # Skip very short chunks
                    continue
                
                # Create sample embedding (in real implementation, would use actual embedding model)
                sample_embedding = [random.uniform(-1, 1) for _ in range(1536)]  # OpenAI embedding dimension
                
                # Check if embedding already exists
                existing_embeddings = await DocumentEmbedding.get_by_document_id(db_session, document.id)
                if any(emb.chunk_index == i for emb in existing_embeddings):
                    continue
                
                embedding = await DocumentEmbedding.create(
                    db_session,
                    document_id=document.id,
                    chunk_text=chunk,
                    chunk_index=i,
                    embedding_vector=sample_embedding
                )
                print(f"  ✅ Created embedding for '{document.title}' chunk {i+1}")
                
        except Exception as e:
            print(f"  ❌ Failed to create embeddings for '{document.title}': {e}")
    
    await db_session.commit()


async def main():
    """Main function to create all sample data"""
    
    print("🚀 Creating sample data for Convergio database...")
    
    # Initialize database
    await init_db()
    
    # Get database session
    async for db_session in get_db_session():
        try:
            # Create sample data
            talents = await create_sample_talents(db_session)
            documents = await create_sample_documents(db_session)
            await create_sample_embeddings(db_session, documents)
            
            print(f"""
✅ Sample data creation completed!

Summary:
- Talents created: {len(talents)}
- Documents created: {len(documents)}
- Database ready for AI agent queries
- Vector search enabled with sample embeddings
            """)
            
        except Exception as e:
            print(f"❌ Error creating sample data: {e}")
            await db_session.rollback()
            raise
        finally:
            await db_session.close()
        
        break  # Exit after first session


if __name__ == "__main__":
    asyncio.run(main())