#!/usr/bin/env python3
"""
Complete database population script for ALL Convergio tables
Populates every single table with meaningful sample data
"""

import asyncio
import json
import random
import uuid
from datetime import datetime, timedelta
import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncpg
import structlog

logger = structlog.get_logger()

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/convergio_db")


class CompleteDBPopulator:
    """Populates ALL tables in the Convergio database"""
    
    def __init__(self):
        self.conn = None
        self.talent_ids = []
        self.client_ids = []
        self.engagement_ids = []
        self.activity_ids = []
        self.studio_ids = []
        self.area_ids = []
        self.organization_ids = []
        self.crew_ids = []
        self.document_ids = []
        
    async def connect(self):
        """Connect to database"""
        self.conn = await asyncpg.connect(DATABASE_URL)
        
    async def close(self):
        """Close database connection"""
        if self.conn:
            await self.conn.close()
            
    async def populate_all(self):
        """Main method to populate all tables"""
        try:
            await self.connect()
            logger.info("🚀 Starting COMPLETE database population...")
            
            # Get existing IDs
            await self.get_existing_ids()
            
            # Basic entities
            await self.populate_geographies()
            await self.populate_areas()
            await self.populate_locations()
            await self.populate_organizations()
            await self.populate_tenants()
            await self.populate_disciplines()
            await self.populate_skills()
            await self.populate_titles()
            
            # Core business entities
            await self.populate_client_industries()
            await self.populate_client_contacts()
            await self.populate_crews()
            await self.populate_initiatives()
            await self.populate_milestones()
            
            # Activity related
            await self.populate_activity_types()
            await self.populate_activity_statuses()
            await self.populate_activity_assignments()
            await self.populate_activity_updates()
            await self.populate_activity_reports()
            await self.populate_activity_feedbacks()
            await self.populate_activity_okrs()
            
            # Engagement related
            await self.populate_engagement_statuses()
            await self.populate_engagement_updates()
            await self.populate_engagement_financials()
            await self.populate_engagement_forecasts()
            await self.populate_engagement_feedbacks()
            await self.populate_engagement_tags()
            await self.populate_engagement_subscriptions()
            await self.populate_engagement_okr()
            
            # Financial
            await self.populate_fiscal_years()
            await self.populate_fiscal_periods()
            
            # Documents and knowledge
            await self.populate_documents()
            await self.populate_document_embeddings()
            await self.populate_knowledge_base()
            await self.populate_attachments()
            
            # Feedback and metrics
            await self.populate_feedbacks()
            await self.populate_kudos_categories()
            await self.populate_kudos()
            await self.populate_sentiment_tracking()
            
            # AI/LLM related
            await self.populate_llm_providers()
            await self.populate_llm_models()
            await self.populate_provider_pricing()
            await self.populate_ai_prompts()
            await self.populate_ai_agent_bindings()
            await self.populate_ai_agent_logs()
            
            # MCP related
            await self.populate_mcp_servers()
            await self.populate_mcp_agent_bindings()
            
            # Work management
            await self.populate_workload_assignments()
            await self.populate_daily_agenda()
            await self.populate_vacations()
            await self.populate_time_off_periods()
            
            # Risk and compliance
            await self.populate_risks()
            await self.populate_risk_thresholds()
            await self.populate_change_requests()
            
            # System related
            await self.populate_system_settings()
            await self.populate_organization_settings()
            await self.populate_notifications()
            await self.populate_audit_logs()
            await self.populate_backup_log()
            await self.populate_import_log()
            await self.populate_experimentation_logs()
            
            # User related
            await self.populate_users()
            await self.populate_bookmarks()
            await self.populate_chat_sessions()
            await self.populate_password_histories()
            await self.populate_account_securities()
            await self.populate_support_flags()
            
            # Talent related
            await self.populate_talent_skills()
            await self.populate_studio_areas()
            
            logger.info("="*60)
            logger.info("🎉 COMPLETE DATABASE POPULATION FINISHED!")
            logger.info("="*60)
            
        except Exception as e:
            logger.error(f"Population failed: {e}")
            import traceback
            traceback.print_exc()
            raise
        finally:
            await self.close()
            
    async def get_existing_ids(self):
        """Get IDs of existing records"""
        self.talent_ids = [r['id'] for r in await self.conn.fetch("SELECT id FROM talents")]
        self.client_ids = [r['id'] for r in await self.conn.fetch("SELECT id FROM clients")]
        self.engagement_ids = [r['id'] for r in await self.conn.fetch("SELECT id FROM engagements")]
        self.activity_ids = [r['id'] for r in await self.conn.fetch("SELECT id FROM activities")]
        self.studio_ids = [r['id'] for r in await self.conn.fetch("SELECT id FROM studios")]
        
        logger.info(f"Found existing: {len(self.talent_ids)} talents, {len(self.client_ids)} clients, "
                   f"{len(self.engagement_ids)} engagements, {len(self.activity_ids)} activities")
    
    # ==================== GEOGRAPHY & LOCATIONS ====================
    
    async def populate_geographies(self):
        """Populate geographies table"""
        logger.info("Populating geographies...")
        count = 0
        
        geos = [
            ("North America", "NA"), ("Europe", "EU"), ("Asia Pacific", "APAC"),
            ("Latin America", "LATAM"), ("Middle East", "ME"), ("Africa", "AF")
        ]
        
        for name, code in geos:
            try:
                await self.conn.execute(
                    "INSERT INTO geographies (name, code, created_at, updated_at) VALUES ($1, $2, $3, $4)",
                    name, code, datetime.now(), datetime.now()
                )
                count += 1
            except Exception:
                pass
        
        logger.info(f"✅ Created {count} geographies")
    
    async def populate_areas(self):
        """Populate areas table"""
        logger.info("Populating areas...")
        count = 0
        
        areas = ["Technology", "Finance", "Operations", "Marketing", "Sales", "Product", "Design", "Data"]
        
        for name in areas:
            try:
                result = await self.conn.fetchrow(
                    "INSERT INTO areas (name, created_at, updated_at) VALUES ($1, $2, $3) RETURNING id",
                    name, datetime.now(), datetime.now()
                )
                if result:
                    self.area_ids.append(result['id'])
                    count += 1
            except Exception:
                pass
        
        logger.info(f"✅ Created {count} areas")
    
    async def populate_locations(self):
        """Populate locations table"""
        logger.info("Populating locations...")
        count = 0
        
        locations = [
            ("Milan HQ", "Via Roma 1, Milano", "Italy"),
            ("Rome Office", "Piazza Navona 10, Roma", "Italy"),
            ("London Hub", "123 Oxford Street, London", "UK"),
            ("NYC Branch", "5th Avenue, New York", "USA"),
            ("Tokyo Office", "Shibuya 1-1, Tokyo", "Japan")
        ]
        
        for name, address, country in locations:
            try:
                await self.conn.execute(
                    "INSERT INTO locations (name, address, country, created_at, updated_at) VALUES ($1, $2, $3, $4, $5)",
                    name, address, country, datetime.now(), datetime.now()
                )
                count += 1
            except Exception:
                pass
        
        logger.info(f"✅ Created {count} locations")
    
    # ==================== ORGANIZATIONS & TENANTS ====================
    
    async def populate_organizations(self):
        """Populate organizations table"""
        logger.info("Populating organizations...")
        count = 0
        
        orgs = ["Convergio Corp", "Tech Division", "Innovation Lab", "Customer Success", "Operations Center"]
        
        for name in orgs:
            try:
                result = await self.conn.fetchrow(
                    "INSERT INTO organizations (name, created_at, updated_at) VALUES ($1, $2, $3) RETURNING id",
                    name, datetime.now(), datetime.now()
                )
                if result:
                    self.organization_ids.append(result['id'])
                    count += 1
            except Exception:
                pass
        
        logger.info(f"✅ Created {count} organizations")
    
    async def populate_tenants(self):
        """Populate tenants table"""
        logger.info("Populating tenants...")
        count = 0
        
        tenants = ["Default Tenant", "Enterprise", "Startup", "Agency", "Freelance"]
        
        for name in tenants:
            try:
                await self.conn.execute(
                    "INSERT INTO tenants (name, created_at, updated_at) VALUES ($1, $2, $3)",
                    name, datetime.now(), datetime.now()
                )
                count += 1
            except Exception:
                pass
        
        logger.info(f"✅ Created {count} tenants")
    
    # ==================== SKILLS & DISCIPLINES ====================
    
    async def populate_disciplines(self):
        """Populate disciplines table"""
        logger.info("Populating disciplines...")
        count = 0
        
        disciplines = [
            "Software Engineering", "Data Science", "Product Management",
            "UX Design", "DevOps", "Cloud Architecture", "Security",
            "Machine Learning", "Business Analysis", "Project Management"
        ]
        
        for name in disciplines:
            try:
                await self.conn.execute(
                    "INSERT INTO disciplines (name, created_at, updated_at) VALUES ($1, $2, $3)",
                    name, datetime.now(), datetime.now()
                )
                count += 1
            except Exception:
                pass
        
        logger.info(f"✅ Created {count} disciplines")
    
    async def populate_skills(self):
        """Populate skills table"""
        logger.info("Populating skills...")
        count = 0
        
        skills = [
            ("Python", "Programming"), ("JavaScript", "Programming"), ("React", "Framework"),
            ("Docker", "DevOps"), ("Kubernetes", "DevOps"), ("AWS", "Cloud"),
            ("PostgreSQL", "Database"), ("MongoDB", "Database"), ("Redis", "Cache"),
            ("Machine Learning", "AI"), ("Deep Learning", "AI"), ("NLP", "AI"),
            ("Agile", "Methodology"), ("Scrum", "Methodology"), ("CI/CD", "DevOps")
        ]
        
        for name, category in skills:
            try:
                await self.conn.execute(
                    "INSERT INTO skills (name, category, created_at, updated_at) VALUES ($1, $2, $3, $4)",
                    name, category, datetime.now(), datetime.now()
                )
                count += 1
            except Exception:
                pass
        
        logger.info(f"✅ Created {count} skills")
    
    async def populate_titles(self):
        """Populate titles table"""
        logger.info("Populating titles...")
        count = 0
        
        titles = [
            "Software Engineer", "Senior Developer", "Tech Lead", "Engineering Manager",
            "Product Manager", "Data Scientist", "UX Designer", "DevOps Engineer",
            "Solution Architect", "Business Analyst", "Project Manager", "Scrum Master"
        ]
        
        for name in titles:
            try:
                await self.conn.execute(
                    "INSERT INTO titles (name, created_at, updated_at) VALUES ($1, $2, $3)",
                    name, datetime.now(), datetime.now()
                )
                count += 1
            except Exception:
                pass
        
        logger.info(f"✅ Created {count} titles")
    
    # ==================== CLIENT RELATED ====================
    
    async def populate_client_industries(self):
        """Populate client_industries table"""
        logger.info("Populating client_industries...")
        count = 0
        
        industries = ["Technology", "Finance", "Healthcare", "Retail", "Manufacturing", 
                     "Telecommunications", "Energy", "Transportation", "Education", "Government"]
        
        for name in industries:
            try:
                await self.conn.execute(
                    "INSERT INTO client_industries (name, created_at, updated_at) VALUES ($1, $2, $3)",
                    name, datetime.now(), datetime.now()
                )
                count += 1
            except Exception:
                pass
        
        logger.info(f"✅ Created {count} client industries")
    
    async def populate_client_contacts(self):
        """Populate client_contacts table"""
        logger.info("Populating client_contacts...")
        count = 0
        
        if not self.client_ids:
            logger.warning("No clients found, skipping client_contacts")
            return
        
        first_names = ["John", "Jane", "Michael", "Sarah", "David", "Emma", "Robert", "Lisa"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Davis", "Miller", "Wilson", "Moore"]
        
        for client_id in self.client_ids[:10]:  # Add contacts for first 10 clients
            fname = random.choice(first_names)
            lname = random.choice(last_names)
            
            try:
                await self.conn.execute(
                    """INSERT INTO client_contacts 
                    (client_id, name, email, phone, role, created_at, updated_at) 
                    VALUES ($1, $2, $3, $4, $5, $6, $7)""",
                    client_id,
                    f"{fname} {lname}",
                    f"{fname.lower()}.{lname.lower()}@company.com",
                    f"+1-555-{random.randint(1000, 9999)}",
                    random.choice(["CEO", "CTO", "Product Manager", "Director", "VP Engineering"]),
                    datetime.now(),
                    datetime.now()
                )
                count += 1
            except Exception:
                pass
        
        logger.info(f"✅ Created {count} client contacts")
    
    # ==================== CREWS ====================
    
    async def populate_crews(self):
        """Populate crews table"""
        logger.info("Populating crews...")
        count = 0
        
        crews = ["Alpha Team", "Beta Squad", "Gamma Force", "Delta Unit", "Epsilon Group",
                "Zeta Crew", "Eta Team", "Theta Squad", "Iota Force", "Kappa Unit"]
        
        for name in crews:
            try:
                result = await self.conn.fetchrow(
                    "INSERT INTO crews (name, created_at, updated_at) VALUES ($1, $2, $3) RETURNING id",
                    name, datetime.now(), datetime.now()
                )
                if result:
                    self.crew_ids.append(result['id'])
                    count += 1
            except Exception:
                pass
        
        logger.info(f"✅ Created {count} crews")
    
    # ==================== INITIATIVES & MILESTONES ====================
    
    async def populate_initiatives(self):
        """Populate initiatives table"""
        logger.info("Populating initiatives...")
        count = 0
        
        if not self.engagement_ids:
            logger.warning("No engagements found, skipping initiatives")
            return
        
        initiatives = [
            "Cloud Migration Phase 1", "Security Audit Implementation", 
            "Performance Optimization", "User Experience Redesign",
            "Data Pipeline Construction", "API Gateway Setup",
            "Mobile App Development", "Analytics Dashboard", 
            "Compliance Framework", "Disaster Recovery Plan"
        ]
        
        for name in initiatives:
            try:
                await self.conn.execute(
                    """INSERT INTO initiatives 
                    (name, engagement_id, status, priority, created_at, updated_at) 
                    VALUES ($1, $2, $3, $4, $5, $6)""",
                    name,
                    random.choice(self.engagement_ids),
                    random.choice(['Planning', 'Active', 'Completed', 'On Hold']),
                    random.choice(['Low', 'Medium', 'High', 'Critical']),
                    datetime.now(),
                    datetime.now()
                )
                count += 1
            except Exception:
                pass
        
        logger.info(f"✅ Created {count} initiatives")
    
    async def populate_milestones(self):
        """Populate milestones table"""
        logger.info("Populating milestones...")
        count = 0
        
        if not self.engagement_ids:
            logger.warning("No engagements found, skipping milestones")
            return
        
        milestone_names = [
            "Project Kickoff", "Requirements Complete", "Design Approval",
            "Development Phase 1", "Testing Complete", "UAT Sign-off",
            "Production Deployment", "Post-Launch Review", "Optimization Phase",
            "Final Delivery"
        ]
        
        for engagement_id in self.engagement_ids[:10]:
            for i, name in enumerate(random.sample(milestone_names, random.randint(3, 6))):
                try:
                    await self.conn.execute(
                        """INSERT INTO milestones 
                        (name, engagement_id, due_date, status, created_at, updated_at) 
                        VALUES ($1, $2, $3, $4, $5, $6)""",
                        name,
                        engagement_id,
                        datetime.now() + timedelta(days=30 * (i + 1)),
                        random.choice(['Pending', 'In Progress', 'Completed', 'Delayed']),
                        datetime.now(),
                        datetime.now()
                    )
                    count += 1
                except Exception:
                    pass
        
        logger.info(f"✅ Created {count} milestones")
    
    # ==================== ACTIVITY RELATED ====================
    
    async def populate_activity_types(self):
        """Populate activity_types table"""
        logger.info("Populating activity_types...")
        count = 0
        
        types = [
            "Development", "Testing", "Documentation", "Meeting", "Review",
            "Planning", "Research", "Training", "Support", "Deployment"
        ]
        
        for name in types:
            try:
                await self.conn.execute(
                    "INSERT INTO activity_types (name, created_at, updated_at) VALUES ($1, $2, $3)",
                    name, datetime.now(), datetime.now()
                )
                count += 1
            except Exception:
                pass
        
        logger.info(f"✅ Created {count} activity types")
    
    async def populate_activity_statuses(self):
        """Populate activity_statuses table"""
        logger.info("Populating activity_statuses...")
        count = 0
        
        statuses = [
            ("Not Started", "Activity has not begun"),
            ("In Progress", "Activity is currently being worked on"),
            ("Completed", "Activity has been completed"),
            ("Blocked", "Activity is blocked by dependencies"),
            ("On Hold", "Activity is temporarily paused"),
            ("Cancelled", "Activity has been cancelled")
        ]
        
        for name, description in statuses:
            try:
                await self.conn.execute(
                    "INSERT INTO activity_statuses (name, description, created_at, updated_at) VALUES ($1, $2, $3, $4)",
                    name, description, datetime.now(), datetime.now()
                )
                count += 1
            except Exception:
                pass
        
        logger.info(f"✅ Created {count} activity statuses")
    
    async def populate_activity_assignments(self):
        """Populate activity_assignments table"""
        logger.info("Populating activity_assignments...")
        count = 0
        
        if not self.activity_ids or not self.talent_ids:
            logger.warning("No activities or talents found, skipping assignments")
            return
        
        for activity_id in self.activity_ids[:15]:
            num_assignments = random.randint(1, 3)
            for talent_id in random.sample(self.talent_ids, min(num_assignments, len(self.talent_ids))):
                try:
                    await self.conn.execute(
                        """INSERT INTO activity_assignments 
                        (activity_id, talent_id, role, allocation_percentage, created_at, updated_at) 
                        VALUES ($1, $2, $3, $4, $5, $6)""",
                        activity_id,
                        talent_id,
                        random.choice(['Lead', 'Contributor', 'Reviewer', 'Support']),
                        random.choice([25, 50, 75, 100]),
                        datetime.now(),
                        datetime.now()
                    )
                    count += 1
                except Exception:
                    pass
        
        logger.info(f"✅ Created {count} activity assignments")
    
    async def populate_activity_updates(self):
        """Populate activity_updates table"""
        logger.info("Populating activity_updates...")
        count = 0
        
        if not self.activity_ids or not self.talent_ids:
            logger.warning("No activities or talents found, skipping updates")
            return
        
        updates = [
            "Started working on this task",
            "Made good progress today",
            "Encountered a blocker, need assistance",
            "Completed initial implementation",
            "Ready for review",
            "Addressed review feedback",
            "Testing complete",
            "Task completed successfully"
        ]
        
        for activity_id in self.activity_ids[:10]:
            for _ in range(random.randint(1, 3)):
                try:
                    await self.conn.execute(
                        """INSERT INTO activity_updates 
                        (activity_id, update_text, posted_by, created_at) 
                        VALUES ($1, $2, $3, $4)""",
                        activity_id,
                        random.choice(updates),
                        random.choice(self.talent_ids),
                        datetime.now() - timedelta(days=random.randint(0, 30))
                    )
                    count += 1
                except Exception:
                    pass
        
        logger.info(f"✅ Created {count} activity updates")
    
    async def populate_activity_reports(self):
        """Populate activity_reports table"""
        logger.info("Populating activity_reports...")
        count = 0
        
        if not self.activity_ids:
            logger.warning("No activities found, skipping reports")
            return
        
        for activity_id in self.activity_ids[:10]:
            try:
                await self.conn.execute(
                    """INSERT INTO activity_reports 
                    (activity_id, report_data, created_at, updated_at) 
                    VALUES ($1, $2, $3, $4)""",
                    activity_id,
                    json.dumps({
                        "progress": random.randint(0, 100),
                        "hours_spent": random.randint(1, 40),
                        "status": random.choice(["on_track", "at_risk", "delayed"]),
                        "notes": "Weekly progress report"
                    }),
                    datetime.now(),
                    datetime.now()
                )
                count += 1
            except Exception:
                pass
        
        logger.info(f"✅ Created {count} activity reports")
    
    async def populate_activity_feedbacks(self):
        """Populate activity_feedbacks table"""
        logger.info("Populating activity_feedbacks...")
        count = 0
        
        if not self.activity_ids or not self.talent_ids:
            logger.warning("No activities or talents found, skipping feedbacks")
            return
        
        feedbacks = [
            "Great work on this task!",
            "Implementation looks solid",
            "Please address the review comments",
            "Excellent documentation",
            "Consider refactoring this section",
            "Performance could be improved",
            "Well structured approach",
            "Meets all requirements"
        ]
        
        for activity_id in self.activity_ids[:10]:
            try:
                await self.conn.execute(
                    """INSERT INTO activity_feedbacks 
                    (activity_id, feedback_text, given_by, rating, created_at) 
                    VALUES ($1, $2, $3, $4, $5)""",
                    activity_id,
                    random.choice(feedbacks),
                    random.choice(self.talent_ids),
                    random.randint(3, 5),
                    datetime.now()
                )
                count += 1
            except Exception:
                pass
        
        logger.info(f"✅ Created {count} activity feedbacks")
    
    async def populate_activity_okrs(self):
        """Populate activity_okrs table"""
        logger.info("Populating activity_okrs...")
        count = 0
        
        # Get OKR IDs
        okr_ids = [r['id'] for r in await self.conn.fetch("SELECT id FROM okrs LIMIT 10")]
        
        if not self.activity_ids or not okr_ids:
            logger.warning("No activities or OKRs found, skipping activity_okrs")
            return
        
        for activity_id in self.activity_ids[:10]:
            try:
                await self.conn.execute(
                    """INSERT INTO activity_okrs 
                    (activity_id, okr_id, contribution_percentage, created_at, updated_at) 
                    VALUES ($1, $2, $3, $4, $5)""",
                    activity_id,
                    random.choice(okr_ids),
                    random.randint(10, 100),
                    datetime.now(),
                    datetime.now()
                )
                count += 1
            except Exception:
                pass
        
        logger.info(f"✅ Created {count} activity OKR links")
    
    # ==================== ENGAGEMENT RELATED ====================
    
    async def populate_engagement_statuses(self):
        """Populate engagement_statuses table"""
        logger.info("Populating engagement_statuses...")
        count = 0
        
        statuses = [
            ("Active", "Engagement is currently active"),
            ("Planning", "In planning phase"),
            ("On Hold", "Temporarily paused"),
            ("Completed", "Successfully completed"),
            ("Cancelled", "Engagement cancelled")
        ]
        
        for name, description in statuses:
            try:
                await self.conn.execute(
                    "INSERT INTO engagement_statuses (name, description, created_at, updated_at) VALUES ($1, $2, $3, $4)",
                    name, description, datetime.now(), datetime.now()
                )
                count += 1
            except Exception:
                pass
        
        logger.info(f"✅ Created {count} engagement statuses")
    
    async def populate_engagement_updates(self):
        """Populate engagement_updates table"""
        logger.info("Populating engagement_updates...")
        count = 0
        
        if not self.engagement_ids or not self.talent_ids:
            logger.warning("No engagements or talents found, skipping updates")
            return
        
        updates = [
            "Project kickoff meeting completed",
            "Requirements gathering phase started",
            "Design review scheduled for next week",
            "Development sprint 1 completed",
            "Client demo went well",
            "Moving to testing phase",
            "Deployment planning in progress",
            "Project on track for delivery"
        ]
        
        for engagement_id in self.engagement_ids[:10]:
            for _ in range(random.randint(2, 5)):
                try:
                    await self.conn.execute(
                        """INSERT INTO engagement_updates 
                        (engagement_id, update_text, posted_by, created_at) 
                        VALUES ($1, $2, $3, $4)""",
                        engagement_id,
                        random.choice(updates),
                        random.choice(self.talent_ids),
                        datetime.now() - timedelta(days=random.randint(0, 60))
                    )
                    count += 1
                except Exception:
                    pass
        
        logger.info(f"✅ Created {count} engagement updates")
    
    async def populate_engagement_financials(self):
        """Populate engagement_financials table"""
        logger.info("Populating engagement_financials...")
        count = 0
        
        if not self.engagement_ids:
            logger.warning("No engagements found, skipping financials")
            return
        
        for engagement_id in self.engagement_ids[:10]:
            try:
                await self.conn.execute(
                    """INSERT INTO engagement_financials 
                    (engagement_id, budget, spent, revenue, margin, created_at, updated_at) 
                    VALUES ($1, $2, $3, $4, $5, $6, $7)""",
                    engagement_id,
                    random.randint(50000, 500000),
                    random.randint(10000, 200000),
                    random.randint(60000, 600000),
                    random.uniform(0.1, 0.4),
                    datetime.now(),
                    datetime.now()
                )
                count += 1
            except Exception:
                pass
        
        logger.info(f"✅ Created {count} engagement financials")
    
    async def populate_engagement_forecasts(self):
        """Populate engagement_forecasts table"""
        logger.info("Populating engagement_forecasts...")
        count = 0
        
        if not self.engagement_ids:
            logger.warning("No engagements found, skipping forecasts")
            return
        
        for engagement_id in self.engagement_ids[:10]:
            try:
                await self.conn.execute(
                    """INSERT INTO engagement_forecasts 
                    (engagement_id, forecast_date, forecasted_revenue, forecasted_cost, 
                    confidence_level, created_at, updated_at) 
                    VALUES ($1, $2, $3, $4, $5, $6, $7)""",
                    engagement_id,
                    datetime.now() + timedelta(days=random.randint(30, 180)),
                    random.randint(100000, 1000000),
                    random.randint(50000, 500000),
                    random.uniform(0.5, 0.95),
                    datetime.now(),
                    datetime.now()
                )
                count += 1
            except Exception:
                pass
        
        logger.info(f"✅ Created {count} engagement forecasts")
    
    async def populate_engagement_feedbacks(self):
        """Populate engagement_feedbacks table"""
        logger.info("Populating engagement_feedbacks...")
        count = 0
        
        if not self.engagement_ids:
            logger.warning("No engagements found, skipping feedbacks")
            return
        
        feedbacks = [
            "Excellent project delivery",
            "Great team collaboration",
            "Timely and within budget",
            "Good communication throughout",
            "Met all requirements",
            "Exceeded expectations",
            "Professional and efficient",
            "Would recommend to others"
        ]
        
        for engagement_id in self.engagement_ids[:10]:
            try:
                await self.conn.execute(
                    """INSERT INTO engagement_feedbacks 
                    (engagement_id, feedback_text, rating, created_at) 
                    VALUES ($1, $2, $3, $4)""",
                    engagement_id,
                    random.choice(feedbacks),
                    random.randint(4, 5),
                    datetime.now()
                )
                count += 1
            except Exception:
                pass
        
        logger.info(f"✅ Created {count} engagement feedbacks")
    
    async def populate_engagement_tags(self):
        """Populate engagement_tags table"""
        logger.info("Populating engagement_tags...")
        count = 0
        
        if not self.engagement_ids:
            logger.warning("No engagements found, skipping tags")
            return
        
        tags = ["strategic", "high-priority", "innovation", "transformation", 
                "cloud", "security", "data", "mobile", "web", "enterprise"]
        
        for engagement_id in self.engagement_ids[:10]:
            for tag in random.sample(tags, random.randint(2, 4)):
                try:
                    await self.conn.execute(
                        """INSERT INTO engagement_tags 
                        (engagement_id, tag_name, created_at) 
                        VALUES ($1, $2, $3)""",
                        engagement_id,
                        tag,
                        datetime.now()
                    )
                    count += 1
                except Exception:
                    pass
        
        logger.info(f"✅ Created {count} engagement tags")
    
    async def populate_engagement_subscriptions(self):
        """Populate engagement_subscriptions table"""
        logger.info("Populating engagement_subscriptions...")
        count = 0
        
        if not self.engagement_ids or not self.talent_ids:
            logger.warning("No engagements or talents found, skipping subscriptions")
            return
        
        for engagement_id in self.engagement_ids[:10]:
            for talent_id in random.sample(self.talent_ids, min(3, len(self.talent_ids))):
                try:
                    await self.conn.execute(
                        """INSERT INTO engagement_subscriptions 
                        (engagement_id, talent_id, subscription_type, created_at) 
                        VALUES ($1, $2, $3, $4)""",
                        engagement_id,
                        talent_id,
                        random.choice(['updates', 'all', 'critical']),
                        datetime.now()
                    )
                    count += 1
                except Exception:
                    pass
        
        logger.info(f"✅ Created {count} engagement subscriptions")
    
    async def populate_engagement_okr(self):
        """Populate engagement_okr table"""
        logger.info("Populating engagement_okr...")
        count = 0
        
        # Get OKR IDs
        okr_ids = [r['id'] for r in await self.conn.fetch("SELECT id FROM okrs LIMIT 10")]
        
        if not self.engagement_ids or not okr_ids:
            logger.warning("No engagements or OKRs found, skipping engagement_okr")
            return
        
        for engagement_id in self.engagement_ids[:10]:
            try:
                await self.conn.execute(
                    """INSERT INTO engagement_okr 
                    (engagement_id, okr_id, alignment_score, created_at, updated_at) 
                    VALUES ($1, $2, $3, $4, $5)""",
                    engagement_id,
                    random.choice(okr_ids),
                    random.uniform(0.5, 1.0),
                    datetime.now(),
                    datetime.now()
                )
                count += 1
            except Exception:
                pass
        
        logger.info(f"✅ Created {count} engagement OKR links")
    
    # ==================== FINANCIAL ====================
    
    async def populate_fiscal_years(self):
        """Populate fiscal_years table"""
        logger.info("Populating fiscal_years...")
        count = 0
        
        for year in [2023, 2024, 2025, 2026]:
            try:
                await self.conn.execute(
                    """INSERT INTO fiscal_years 
                    (year, start_date, end_date, is_current, created_at, updated_at) 
                    VALUES ($1, $2, $3, $4, $5, $6)""",
                    year,
                    datetime(year, 1, 1),
                    datetime(year, 12, 31),
                    year == 2025,
                    datetime.now(),
                    datetime.now()
                )
                count += 1
            except Exception:
                pass
        
        logger.info(f"✅ Created {count} fiscal years")
    
    async def populate_fiscal_periods(self):
        """Populate fiscal_periods table"""
        logger.info("Populating fiscal_periods...")
        count = 0
        
        periods = ["Q1", "Q2", "Q3", "Q4"]
        
        for year in [2024, 2025]:
            for i, period in enumerate(periods):
                try:
                    await self.conn.execute(
                        """INSERT INTO fiscal_periods 
                        (name, year, quarter, start_date, end_date, created_at, updated_at) 
                        VALUES ($1, $2, $3, $4, $5, $6, $7)""",
                        f"{period} {year}",
                        year,
                        i + 1,
                        datetime(year, i * 3 + 1, 1),
                        datetime(year, i * 3 + 3, 30) if i < 3 else datetime(year, 12, 31),
                        datetime.now(),
                        datetime.now()
                    )
                    count += 1
                except Exception:
                    pass
        
        logger.info(f"✅ Created {count} fiscal periods")
    
    # ==================== DOCUMENTS & KNOWLEDGE ====================
    
    async def populate_documents(self):
        """Populate documents table (if not already populated)"""
        logger.info("Populating documents...")
        
        existing = await self.conn.fetchval("SELECT COUNT(*) FROM documents")
        if existing > 0:
            self.document_ids = [r['id'] for r in await self.conn.fetch("SELECT id FROM documents LIMIT 20")]
            logger.info(f"✅ Found {existing} existing documents")
            return
        
        count = 0
        doc_types = ["Technical Spec", "Project Plan", "Meeting Notes", "Report", "Proposal"]
        
        for i in range(20):
            try:
                result = await self.conn.fetchrow(
                    """INSERT INTO documents 
                    (title, content, type, source, created_at, updated_at) 
                    VALUES ($1, $2, $3, $4, $5, $6) RETURNING id""",
                    f"{random.choice(doc_types)} {i+1}",
                    f"This is the content of document {i+1} containing important information.",
                    random.choice(doc_types).lower().replace(' ', '_'),
                    'generated',
                    datetime.now(),
                    datetime.now()
                )
                if result:
                    self.document_ids.append(result['id'])
                    count += 1
            except Exception:
                pass
        
        logger.info(f"✅ Created {count} documents")
    
    async def populate_document_embeddings(self):
        """Populate document_embeddings table"""
        logger.info("Populating document_embeddings...")
        count = 0
        
        if not self.document_ids:
            logger.warning("No documents found, skipping embeddings")
            return
        
        for doc_id in self.document_ids[:10]:
            for chunk_idx in range(random.randint(1, 3)):
                try:
                    # Generate mock embedding (1536 dimensions for OpenAI)
                    embedding = [random.random() for _ in range(1536)]
                    
                    await self.conn.execute(
                        """INSERT INTO document_embeddings 
                        (document_id, chunk_index, content, embedding, created_at) 
                        VALUES ($1, $2, $3, $4, $5)""",
                        doc_id,
                        chunk_idx,
                        f"Chunk {chunk_idx + 1} content from document",
                        f"[{','.join(map(str, embedding[:10]))}...]",  # Truncated for storage
                        datetime.now()
                    )
                    count += 1
                except Exception:
                    pass
        
        logger.info(f"✅ Created {count} document embeddings")
    
    async def populate_knowledge_base(self):
        """Populate knowledge_base table"""
        logger.info("Populating knowledge_base...")
        count = 0
        
        kb_entries = [
            ("Best Practices", "Development best practices guide", "guide"),
            ("API Documentation", "Complete API reference", "documentation"),
            ("Troubleshooting Guide", "Common issues and solutions", "guide"),
            ("Architecture Overview", "System architecture documentation", "documentation"),
            ("Security Guidelines", "Security best practices", "policy"),
            ("Deployment Process", "Step-by-step deployment guide", "procedure"),
            ("Coding Standards", "Team coding standards", "standard"),
            ("Testing Strategy", "Testing approach and guidelines", "strategy"),
            ("Performance Tuning", "Performance optimization guide", "guide"),
            ("Disaster Recovery", "DR procedures and protocols", "procedure")
        ]
        
        for title, content, category in kb_entries:
            try:
                await self.conn.execute(
                    """INSERT INTO knowledge_base 
                    (title, content, category, created_at, updated_at) 
                    VALUES ($1, $2, $3, $4, $5)""",
                    title,
                    content,
                    category,
                    datetime.now(),
                    datetime.now()
                )
                count += 1
            except Exception:
                pass
        
        logger.info(f"✅ Created {count} knowledge base entries")
    
    async def populate_attachments(self):
        """Populate attachments table"""
        logger.info("Populating attachments...")
        count = 0
        
        if not self.engagement_ids:
            logger.warning("No engagements found, skipping attachments")
            return
        
        file_types = ["pdf", "docx", "xlsx", "png", "jpg", "zip"]
        
        for engagement_id in self.engagement_ids[:10]:
            for i in range(random.randint(1, 3)):
                try:
                    await self.conn.execute(
                        """INSERT INTO attachments 
                        (engagement_id, file_name, file_type, file_size, file_url, created_at, updated_at) 
                        VALUES ($1, $2, $3, $4, $5, $6, $7)""",
                        engagement_id,
                        f"document_{i+1}.{random.choice(file_types)}",
                        random.choice(file_types),
                        random.randint(1000, 5000000),
                        f"/uploads/{uuid.uuid4()}",
                        datetime.now(),
                        datetime.now()
                    )
                    count += 1
                except Exception:
                    pass
        
        logger.info(f"✅ Created {count} attachments")
    
    # ==================== FEEDBACK & METRICS ====================
    
    async def populate_feedbacks(self):
        """Populate feedbacks table"""
        logger.info("Populating feedbacks...")
        count = 0
        
        feedback_types = ["positive", "constructive", "improvement", "recognition"]
        
        if not self.talent_ids:
            logger.warning("No talents found, skipping feedbacks")
            return
        
        for _ in range(20):
            try:
                await self.conn.execute(
                    """INSERT INTO feedbacks 
                    (given_by, given_to, feedback_type, feedback_text, rating, created_at) 
                    VALUES ($1, $2, $3, $4, $5, $6)""",
                    random.choice(self.talent_ids),
                    random.choice(self.talent_ids),
                    random.choice(feedback_types),
                    "Great work on the recent project delivery!",
                    random.randint(3, 5),
                    datetime.now()
                )
                count += 1
            except Exception:
                pass
        
        logger.info(f"✅ Created {count} feedbacks")
    
    async def populate_kudos_categories(self):
        """Populate kudos_categories table"""
        logger.info("Populating kudos_categories...")
        count = 0
        
        categories = [
            ("Team Player", "team_player"),
            ("Innovation", "innovation"),
            ("Problem Solver", "problem_solver"),
            ("Leadership", "leadership"),
            ("Excellence", "excellence"),
            ("Mentorship", "mentorship"),
            ("Customer Focus", "customer_focus"),
            ("Technical Expert", "technical_expert")
        ]
        
        for name, slug in categories:
            try:
                await self.conn.execute(
                    """INSERT INTO kudos_categories 
                    (name, slug, created_at, updated_at) 
                    VALUES ($1, $2, $3, $4)""",
                    name, slug, datetime.now(), datetime.now()
                )
                count += 1
            except Exception:
                pass
        
        logger.info(f"✅ Created {count} kudos categories")
    
    async def populate_kudos(self):
        """Populate kudos table"""
        logger.info("Populating kudos...")
        count = 0
        
        if not self.talent_ids:
            logger.warning("No talents found, skipping kudos")
            return
        
        # Get category IDs
        categories = await self.conn.fetch("SELECT id FROM kudos_categories")
        if not categories:
            logger.warning("No kudos categories found, skipping kudos")
            return
        
        category_ids = [c['id'] for c in categories]
        
        messages = [
            "Outstanding contribution to the project!",
            "Great problem-solving skills!",
            "Excellent teamwork!",
            "Innovative solution!",
            "Above and beyond effort!",
            "Fantastic leadership!",
            "Amazing dedication!",
            "Brilliant work!"
        ]
        
        for _ in range(30):
            try:
                await self.conn.execute(
                    """INSERT INTO kudos 
                    (given_by, given_to, category_id, message, created_at) 
                    VALUES ($1, $2, $3, $4, $5)""",
                    random.choice(self.talent_ids),
                    random.choice(self.talent_ids),
                    random.choice(category_ids),
                    random.choice(messages),
                    datetime.now() - timedelta(days=random.randint(0, 90))
                )
                count += 1
            except Exception:
                pass
        
        logger.info(f"✅ Created {count} kudos")
    
    async def populate_sentiment_tracking(self):
        """Populate sentiment_tracking table"""
        logger.info("Populating sentiment_tracking...")
        count = 0
        
        if not self.engagement_ids:
            logger.warning("No engagements found, skipping sentiment tracking")
            return
        
        for engagement_id in self.engagement_ids[:10]:
            try:
                await self.conn.execute(
                    """INSERT INTO sentiment_tracking 
                    (engagement_id, sentiment_score, confidence, analysis_date, created_at) 
                    VALUES ($1, $2, $3, $4, $5)""",
                    engagement_id,
                    random.uniform(-1.0, 1.0),
                    random.uniform(0.5, 1.0),
                    datetime.now(),
                    datetime.now()
                )
                count += 1
            except Exception:
                pass
        
        logger.info(f"✅ Created {count} sentiment tracking records")
    
    # ==================== AI/LLM RELATED ====================
    
    async def populate_llm_providers(self):
        """Populate llm_providers table"""
        logger.info("Populating LLM providers...")
        count = 0
        
        providers = [
            ("OpenAI", "openai", True),
            ("Anthropic", "anthropic", True),
            ("Google", "google", False),
            ("Cohere", "cohere", False),
            ("Mistral", "mistral", False)
        ]
        
        for name, slug, is_active in providers:
            try:
                await self.conn.execute(
                    """INSERT INTO llm_providers 
                    (name, slug, is_active, created_at, updated_at) 
                    VALUES ($1, $2, $3, $4, $5)""",
                    name, slug, is_active, datetime.now(), datetime.now()
                )
                count += 1
            except Exception:
                pass
        
        logger.info(f"✅ Created {count} LLM providers")
    
    async def populate_llm_models(self):
        """Populate llm_models table"""
        logger.info("Populating LLM models...")
        count = 0
        
        # Get provider IDs
        providers = await self.conn.fetch("SELECT id, slug FROM llm_providers")
        if not providers:
            logger.warning("No LLM providers found, skipping models")
            return
        
        provider_map = {p['slug']: p['id'] for p in providers}
        
        models = [
            ("GPT-4", "gpt-4", provider_map.get('openai'), True),
            ("GPT-3.5", "gpt-3.5-turbo", provider_map.get('openai'), True),
            ("Claude 3", "claude-3-opus", provider_map.get('anthropic'), True),
            ("Claude Instant", "claude-instant", provider_map.get('anthropic'), True)
        ]
        
        for name, model_id, provider_id, is_active in models:
            if provider_id:
                try:
                    await self.conn.execute(
                        """INSERT INTO llm_models 
                        (name, model_id, provider_id, is_active, created_at, updated_at) 
                        VALUES ($1, $2, $3, $4, $5, $6)""",
                        name, model_id, provider_id, is_active, datetime.now(), datetime.now()
                    )
                    count += 1
                except Exception:
                    pass
        
        logger.info(f"✅ Created {count} LLM models")
    
    async def populate_provider_pricing(self):
        """Populate provider_pricing table"""
        logger.info("Populating provider pricing...")
        count = 0
        
        # Get model IDs
        models = await self.conn.fetch("SELECT id, model_id FROM llm_models")
        if not models:
            logger.warning("No LLM models found, skipping pricing")
            return
        
        for model in models:
            try:
                await self.conn.execute(
                    """INSERT INTO provider_pricing 
                    (model_id, input_price_per_1k, output_price_per_1k, effective_date, created_at, updated_at) 
                    VALUES ($1, $2, $3, $4, $5, $6)""",
                    model['id'],
                    random.uniform(0.001, 0.01),
                    random.uniform(0.002, 0.02),
                    datetime.now(),
                    datetime.now(),
                    datetime.now()
                )
                count += 1
            except Exception:
                pass
        
        logger.info(f"✅ Created {count} provider pricing records")
    
    async def populate_ai_prompts(self):
        """Populate ai_prompts table"""
        logger.info("Populating AI prompts...")
        count = 0
        
        prompts = [
            ("Code Review", "Review the following code for best practices and potential issues", "code_review"),
            ("Summarization", "Summarize the following text in 3 bullet points", "summarization"),
            ("Translation", "Translate the following text to Italian", "translation"),
            ("Analysis", "Analyze the following data and provide insights", "analysis"),
            ("Generation", "Generate content based on the following requirements", "generation")
        ]
        
        for name, template, category in prompts:
            try:
                await self.conn.execute(
                    """INSERT INTO ai_prompts 
                    (name, prompt_template, category, is_active, created_at, updated_at) 
                    VALUES ($1, $2, $3, $4, $5, $6)""",
                    name, template, category, True, datetime.now(), datetime.now()
                )
                count += 1
            except Exception:
                pass
        
        logger.info(f"✅ Created {count} AI prompts")
    
    async def populate_ai_agent_bindings(self):
        """Populate ai_agent_bindings table"""
        logger.info("Populating AI agent bindings...")
        count = 0
        
        agents = ["ali", "amy", "baccio", "davide", "diana", "luca", "sofia"]
        
        # Get model IDs
        models = await self.conn.fetch("SELECT id FROM llm_models LIMIT 4")
        if not models:
            logger.warning("No LLM models found, skipping agent bindings")
            return
        
        model_ids = [m['id'] for m in models]
        
        for agent in agents:
            try:
                await self.conn.execute(
                    """INSERT INTO ai_agent_bindings 
                    (agent_name, model_id, is_active, created_at, updated_at) 
                    VALUES ($1, $2, $3, $4, $5)""",
                    agent,
                    random.choice(model_ids),
                    True,
                    datetime.now(),
                    datetime.now()
                )
                count += 1
            except Exception:
                pass
        
        logger.info(f"✅ Created {count} AI agent bindings")
    
    async def populate_ai_agent_logs(self):
        """Populate ai_agent_logs table"""
        logger.info("Populating AI agent logs...")
        count = 0
        
        agents = ["ali", "amy", "baccio", "davide"]
        
        for _ in range(20):
            try:
                await self.conn.execute(
                    """INSERT INTO ai_agent_logs 
                    (agent_name, action, request_data, response_data, tokens_used, 
                    response_time_ms, created_at) 
                    VALUES ($1, $2, $3, $4, $5, $6, $7)""",
                    random.choice(agents),
                    random.choice(['query', 'analysis', 'generation', 'chat']),
                    json.dumps({"query": "Sample request"}),
                    json.dumps({"response": "Sample response"}),
                    random.randint(100, 2000),
                    random.randint(500, 5000),
                    datetime.now() - timedelta(days=random.randint(0, 30))
                )
                count += 1
            except Exception:
                pass
        
        logger.info(f"✅ Created {count} AI agent logs")
    
    # ==================== MCP RELATED ====================
    
    async def populate_mcp_servers(self):
        """Populate mcp_servers table"""
        logger.info("Populating MCP servers...")
        count = 0
        
        servers = [
            ("Main Server", "main", "http://localhost:8000", True),
            ("Dev Server", "dev", "http://localhost:8001", True),
            ("Test Server", "test", "http://localhost:8002", False),
            ("Staging Server", "staging", "http://staging.convergio.io", False)
        ]
        
        for name, slug, endpoint, is_active in servers:
            try:
                await self.conn.execute(
                    """INSERT INTO mcp_servers 
                    (name, slug, endpoint, is_active, created_at, updated_at) 
                    VALUES ($1, $2, $3, $4, $5, $6)""",
                    name, slug, endpoint, is_active, datetime.now(), datetime.now()
                )
                count += 1
            except Exception:
                pass
        
        logger.info(f"✅ Created {count} MCP servers")
    
    async def populate_mcp_agent_bindings(self):
        """Populate mcp_agent_bindings table"""
        logger.info("Populating MCP agent bindings...")
        count = 0
        
        # Get server IDs
        servers = await self.conn.fetch("SELECT id FROM mcp_servers")
        if not servers:
            logger.warning("No MCP servers found, skipping bindings")
            return
        
        server_ids = [s['id'] for s in servers]
        agents = ["ali", "amy", "baccio", "davide", "diana"]
        
        for agent in agents:
            try:
                await self.conn.execute(
                    """INSERT INTO mcp_agent_bindings 
                    (server_id, agent_name, configuration, is_active, created_at, updated_at) 
                    VALUES ($1, $2, $3, $4, $5, $6)""",
                    random.choice(server_ids),
                    agent,
                    json.dumps({"config": "default"}),
                    True,
                    datetime.now(),
                    datetime.now()
                )
                count += 1
            except Exception:
                pass
        
        logger.info(f"✅ Created {count} MCP agent bindings")
    
    # ==================== WORK MANAGEMENT ====================
    
    async def populate_workload_assignments(self):
        """Populate workload_assignments table"""
        logger.info("Populating workload assignments...")
        count = 0
        
        if not self.talent_ids or not self.engagement_ids:
            logger.warning("No talents or engagements found, skipping workload")
            return
        
        for talent_id in self.talent_ids[:10]:
            for engagement_id in random.sample(self.engagement_ids, min(3, len(self.engagement_ids))):
                try:
                    await self.conn.execute(
                        """INSERT INTO workload_assignments 
                        (talent_id, engagement_id, allocation_percentage, start_date, end_date, created_at, updated_at) 
                        VALUES ($1, $2, $3, $4, $5, $6, $7)""",
                        talent_id,
                        engagement_id,
                        random.choice([25, 50, 75, 100]),
                        datetime.now(),
                        datetime.now() + timedelta(days=random.randint(30, 180)),
                        datetime.now(),
                        datetime.now()
                    )
                    count += 1
                except Exception:
                    pass
        
        logger.info(f"✅ Created {count} workload assignments")
    
    async def populate_daily_agenda(self):
        """Populate daily_agenda table"""
        logger.info("Populating daily agenda...")
        count = 0
        
        if not self.talent_ids:
            logger.warning("No talents found, skipping daily agenda")
            return
        
        agenda_items = [
            "Team standup meeting",
            "Code review session",
            "Client presentation",
            "Sprint planning",
            "1:1 with manager",
            "Technical deep dive",
            "Project status update",
            "Training session"
        ]
        
        for talent_id in self.talent_ids[:10]:
            for _ in range(random.randint(3, 6)):
                try:
                    await self.conn.execute(
                        """INSERT INTO daily_agenda 
                        (talent_id, agenda_date, item_title, item_description, 
                        start_time, end_time, created_at, updated_at) 
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
                        talent_id,
                        datetime.now().date() + timedelta(days=random.randint(0, 7)),
                        random.choice(agenda_items),
                        "Important meeting/activity",
                        f"{random.randint(9, 17):02d}:00",
                        f"{random.randint(10, 18):02d}:00",
                        datetime.now(),
                        datetime.now()
                    )
                    count += 1
                except Exception:
                    pass
        
        logger.info(f"✅ Created {count} daily agenda items")
    
    async def populate_vacations(self):
        """Populate vacations table"""
        logger.info("Populating vacations...")
        count = 0
        
        if not self.talent_ids:
            logger.warning("No talents found, skipping vacations")
            return
        
        vacation_types = ["Annual Leave", "Sick Leave", "Personal Time", "Holiday", "Sabbatical"]
        
        for talent_id in random.sample(self.talent_ids, min(8, len(self.talent_ids))):
            try:
                start = datetime.now() + timedelta(days=random.randint(30, 180))
                await self.conn.execute(
                    """INSERT INTO vacations 
                    (talent_id, vacation_type, start_date, end_date, status, created_at, updated_at) 
                    VALUES ($1, $2, $3, $4, $5, $6, $7)""",
                    talent_id,
                    random.choice(vacation_types),
                    start,
                    start + timedelta(days=random.randint(1, 14)),
                    random.choice(['Pending', 'Approved', 'Rejected']),
                    datetime.now(),
                    datetime.now()
                )
                count += 1
            except Exception:
                pass
        
        logger.info(f"✅ Created {count} vacations")
    
    async def populate_time_off_periods(self):
        """Populate time_off_periods table"""
        logger.info("Populating time off periods...")
        count = 0
        
        if not self.talent_ids:
            logger.warning("No talents found, skipping time off")
            return
        
        for talent_id in random.sample(self.talent_ids, min(10, len(self.talent_ids))):
            try:
                start = datetime.now() - timedelta(days=random.randint(0, 90))
                await self.conn.execute(
                    """INSERT INTO time_off_periods 
                    (talent_id, period_type, start_date, end_date, hours_taken, created_at, updated_at) 
                    VALUES ($1, $2, $3, $4, $5, $6, $7)""",
                    talent_id,
                    random.choice(['vacation', 'sick', 'personal', 'holiday']),
                    start,
                    start + timedelta(days=random.randint(1, 5)),
                    random.randint(8, 40),
                    datetime.now(),
                    datetime.now()
                )
                count += 1
            except Exception:
                pass
        
        logger.info(f"✅ Created {count} time off periods")
    
    # ==================== RISK & COMPLIANCE ====================
    
    async def populate_risks(self):
        """Populate risks table"""
        logger.info("Populating risks...")
        count = 0
        
        if not self.engagement_ids:
            logger.warning("No engagements found, skipping risks")
            return
        
        risk_types = [
            ("Timeline Risk", "Project may be delayed", "High", "Medium"),
            ("Budget Risk", "Cost overrun possible", "Medium", "High"),
            ("Technical Risk", "Complex integration required", "High", "Low"),
            ("Resource Risk", "Key personnel availability", "Medium", "Medium"),
            ("Quality Risk", "Testing coverage concerns", "Low", "Low")
        ]
        
        for engagement_id in self.engagement_ids[:10]:
            for title, desc, impact, probability in random.sample(risk_types, random.randint(1, 3)):
                try:
                    await self.conn.execute(
                        """INSERT INTO risks 
                        (engagement_id, title, description, impact, probability, 
                        mitigation_plan, status, created_at, updated_at) 
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)""",
                        engagement_id,
                        title,
                        desc,
                        impact,
                        probability,
                        "Mitigation strategy in place",
                        random.choice(['Open', 'Mitigated', 'Closed']),
                        datetime.now(),
                        datetime.now()
                    )
                    count += 1
                except Exception:
                    pass
        
        logger.info(f"✅ Created {count} risks")
    
    async def populate_risk_thresholds(self):
        """Populate risk_thresholds table"""
        logger.info("Populating risk thresholds...")
        count = 0
        
        thresholds = [
            ("Budget Variance", "budget_variance", 0.1, 0.2),
            ("Timeline Variance", "timeline_variance", 0.15, 0.25),
            ("Quality Score", "quality_score", 0.7, 0.8),
            ("Resource Utilization", "resource_utilization", 0.8, 0.9),
            ("Customer Satisfaction", "customer_satisfaction", 0.7, 0.85)
        ]
        
        for name, metric, warning, critical in thresholds:
            try:
                await self.conn.execute(
                    """INSERT INTO risk_thresholds 
                    (name, metric_name, warning_threshold, critical_threshold, created_at, updated_at) 
                    VALUES ($1, $2, $3, $4, $5, $6)""",
                    name, metric, warning, critical, datetime.now(), datetime.now()
                )
                count += 1
            except Exception:
                pass
        
        logger.info(f"✅ Created {count} risk thresholds")
    
    async def populate_change_requests(self):
        """Populate change_requests table"""
        logger.info("Populating change requests...")
        count = 0
        
        if not self.engagement_ids or not self.talent_ids:
            logger.warning("No engagements or talents found, skipping change requests")
            return
        
        for _ in range(15):
            try:
                await self.conn.execute(
                    """INSERT INTO change_requests 
                    (engagement_id, requested_by, title, description, impact, status, created_at, updated_at) 
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
                    random.choice(self.engagement_ids),
                    random.choice(self.talent_ids),
                    f"Change Request {random.randint(100, 999)}",
                    "Request to modify project scope/timeline/budget",
                    random.choice(['Low', 'Medium', 'High']),
                    random.choice(['Pending', 'Approved', 'Rejected', 'In Review']),
                    datetime.now(),
                    datetime.now()
                )
                count += 1
            except Exception:
                pass
        
        logger.info(f"✅ Created {count} change requests")
    
    # ==================== SYSTEM RELATED ====================
    
    async def populate_system_settings(self):
        """Populate system_settings table"""
        logger.info("Populating system settings...")
        count = 0
        
        settings = [
            ("app_name", "Convergio", "string"),
            ("version", "2.0.0", "string"),
            ("maintenance_mode", "false", "boolean"),
            ("max_file_size", "10485760", "integer"),
            ("session_timeout", "3600", "integer"),
            ("enable_notifications", "true", "boolean"),
            ("default_language", "en", "string"),
            ("timezone", "UTC", "string")
        ]
        
        for key, value, value_type in settings:
            try:
                await self.conn.execute(
                    """INSERT INTO system_settings 
                    (setting_key, setting_value, value_type, created_at, updated_at) 
                    VALUES ($1, $2, $3, $4, $5)""",
                    key, value, value_type, datetime.now(), datetime.now()
                )
                count += 1
            except Exception:
                pass
        
        logger.info(f"✅ Created {count} system settings")
    
    async def populate_organization_settings(self):
        """Populate organization_settings table"""
        logger.info("Populating organization settings...")
        count = 0
        
        if not self.organization_ids:
            logger.warning("No organizations found, skipping settings")
            return
        
        settings = [
            ("work_hours_start", "09:00"),
            ("work_hours_end", "18:00"),
            ("default_currency", "EUR"),
            ("fiscal_year_start", "01-01"),
            ("enable_overtime", "true")
        ]
        
        for org_id in self.organization_ids[:3]:
            for key, value in settings:
                try:
                    await self.conn.execute(
                        """INSERT INTO organization_settings 
                        (organization_id, setting_key, setting_value, created_at, updated_at) 
                        VALUES ($1, $2, $3, $4, $5)""",
                        org_id, key, value, datetime.now(), datetime.now()
                    )
                    count += 1
                except Exception:
                    pass
        
        logger.info(f"✅ Created {count} organization settings")
    
    async def populate_notifications(self):
        """Populate notifications table"""
        logger.info("Populating notifications...")
        count = 0
        
        if not self.talent_ids:
            logger.warning("No talents found, skipping notifications")
            return
        
        notification_types = [
            ("New Assignment", "You have been assigned to a new project", "assignment"),
            ("Meeting Reminder", "Meeting starting in 15 minutes", "reminder"),
            ("Approval Required", "Your approval is needed", "approval"),
            ("Update Available", "New system update available", "system"),
            ("Feedback Received", "You received new feedback", "feedback")
        ]
        
        for talent_id in self.talent_ids[:10]:
            for title, message, type_val in random.sample(notification_types, random.randint(2, 4)):
                try:
                    await self.conn.execute(
                        """INSERT INTO notifications 
                        (talent_id, title, message, type, is_read, created_at) 
                        VALUES ($1, $2, $3, $4, $5, $6)""",
                        talent_id,
                        title,
                        message,
                        type_val,
                        random.choice([True, False]),
                        datetime.now() - timedelta(days=random.randint(0, 30))
                    )
                    count += 1
                except Exception:
                    pass
        
        logger.info(f"✅ Created {count} notifications")
    
    async def populate_audit_logs(self):
        """Populate audit_logs table"""
        logger.info("Populating audit logs...")
        count = 0
        
        if not self.talent_ids:
            logger.warning("No talents found, skipping audit logs")
            return
        
        actions = [
            ("login", "User logged in"),
            ("logout", "User logged out"),
            ("create", "Created new record"),
            ("update", "Updated record"),
            ("delete", "Deleted record"),
            ("export", "Exported data"),
            ("import", "Imported data")
        ]
        
        for _ in range(50):
            try:
                action, details = random.choice(actions)
                await self.conn.execute(
                    """INSERT INTO audit_logs 
                    (user_id, action, entity_type, entity_id, details, ip_address, created_at) 
                    VALUES ($1, $2, $3, $4, $5, $6, $7)""",
                    random.choice(self.talent_ids),
                    action,
                    random.choice(['engagement', 'activity', 'document', 'user']),
                    random.randint(1, 100),
                    details,
                    f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}",
                    datetime.now() - timedelta(days=random.randint(0, 90))
                )
                count += 1
            except Exception:
                pass
        
        logger.info(f"✅ Created {count} audit logs")
    
    async def populate_backup_log(self):
        """Populate backup_log table"""
        logger.info("Populating backup log...")
        count = 0
        
        for i in range(10):
            try:
                await self.conn.execute(
                    """INSERT INTO backup_log 
                    (backup_type, status, file_path, file_size, duration_seconds, created_at) 
                    VALUES ($1, $2, $3, $4, $5, $6)""",
                    random.choice(['full', 'incremental', 'differential']),
                    random.choice(['success', 'success', 'success', 'failed']),
                    f"/backups/backup_{datetime.now().strftime('%Y%m%d')}_{i}.sql",
                    random.randint(1000000, 100000000),
                    random.randint(10, 300),
                    datetime.now() - timedelta(days=i)
                )
                count += 1
            except Exception:
                pass
        
        logger.info(f"✅ Created {count} backup log entries")
    
    async def populate_import_log(self):
        """Populate import_log table"""
        logger.info("Populating import log...")
        count = 0
        
        for i in range(8):
            try:
                await self.conn.execute(
                    """INSERT INTO import_log 
                    (import_type, file_name, records_processed, records_success, 
                    records_failed, status, created_at) 
                    VALUES ($1, $2, $3, $4, $5, $6, $7)""",
                    random.choice(['talents', 'clients', 'projects', 'activities']),
                    f"import_{datetime.now().strftime('%Y%m%d')}_{i}.csv",
                    random.randint(10, 1000),
                    random.randint(8, 950),
                    random.randint(0, 50),
                    random.choice(['completed', 'completed', 'failed']),
                    datetime.now() - timedelta(days=i * 5)
                )
                count += 1
            except Exception:
                pass
        
        logger.info(f"✅ Created {count} import log entries")
    
    async def populate_experimentation_logs(self):
        """Populate experimentation_logs table"""
        logger.info("Populating experimentation logs...")
        count = 0
        
        experiments = [
            ("New UI Test", "Testing new dashboard UI"),
            ("Performance Optimization", "Testing query optimizations"),
            ("Feature Flag Test", "Testing new feature rollout"),
            ("A/B Test", "Testing conversion improvements"),
            ("Algorithm Update", "Testing new recommendation algorithm")
        ]
        
        for name, description in experiments:
            try:
                await self.conn.execute(
                    """INSERT INTO experimentation_logs 
                    (experiment_name, description, status, results, created_at, updated_at) 
                    VALUES ($1, $2, $3, $4, $5, $6)""",
                    name,
                    description,
                    random.choice(['running', 'completed', 'paused']),
                    json.dumps({
                        "conversion_rate": random.uniform(0.1, 0.3),
                        "sample_size": random.randint(100, 10000),
                        "confidence": random.uniform(0.8, 0.99)
                    }),
                    datetime.now() - timedelta(days=random.randint(0, 30)),
                    datetime.now()
                )
                count += 1
            except Exception:
                pass
        
        logger.info(f"✅ Created {count} experimentation logs")
    
    # ==================== USER RELATED ====================
    
    async def populate_users(self):
        """Populate users table"""
        logger.info("Populating users...")
        
        # Users might be same as talents in this system
        # Skip if talents exist as users
        existing = await self.conn.fetchval("SELECT COUNT(*) FROM users")
        if existing > 0:
            logger.info(f"✅ Found {existing} existing users")
            return
        
        logger.info("✅ Users managed through talents table")
    
    async def populate_bookmarks(self):
        """Populate bookmarks table"""
        logger.info("Populating bookmarks...")
        count = 0
        
        if not self.talent_ids or not self.engagement_ids:
            logger.warning("No talents or engagements found, skipping bookmarks")
            return
        
        for talent_id in self.talent_ids[:10]:
            for engagement_id in random.sample(self.engagement_ids, min(3, len(self.engagement_ids))):
                try:
                    await self.conn.execute(
                        """INSERT INTO bookmarks 
                        (talent_id, entity_type, entity_id, title, created_at) 
                        VALUES ($1, $2, $3, $4, $5)""",
                        talent_id,
                        'engagement',
                        engagement_id,
                        "Bookmarked engagement",
                        datetime.now()
                    )
                    count += 1
                except Exception:
                    pass
        
        logger.info(f"✅ Created {count} bookmarks")
    
    async def populate_chat_sessions(self):
        """Populate chat_sessions table"""
        logger.info("Populating chat sessions...")
        count = 0
        
        if not self.talent_ids:
            logger.warning("No talents found, skipping chat sessions")
            return
        
        for _ in range(15):
            try:
                await self.conn.execute(
                    """INSERT INTO chat_sessions 
                    (user_id, session_id, messages, is_active, created_at, updated_at) 
                    VALUES ($1, $2, $3, $4, $5, $6)""",
                    random.choice(self.talent_ids),
                    str(uuid.uuid4()),
                    json.dumps([
                        {"role": "user", "content": "Hello"},
                        {"role": "assistant", "content": "Hi, how can I help you?"}
                    ]),
                    random.choice([True, False]),
                    datetime.now() - timedelta(days=random.randint(0, 30)),
                    datetime.now()
                )
                count += 1
            except Exception:
                pass
        
        logger.info(f"✅ Created {count} chat sessions")
    
    async def populate_password_histories(self):
        """Populate password_histories table"""
        logger.info("Populating password histories...")
        count = 0
        
        if not self.talent_ids:
            logger.warning("No talents found, skipping password histories")
            return
        
        for talent_id in self.talent_ids[:10]:
            try:
                await self.conn.execute(
                    """INSERT INTO password_histories 
                    (talent_id, password_hash, created_at) 
                    VALUES ($1, $2, $3)""",
                    talent_id,
                    f"hash_{uuid.uuid4()}",  # Mock hash
                    datetime.now() - timedelta(days=random.randint(30, 180))
                )
                count += 1
            except Exception:
                pass
        
        logger.info(f"✅ Created {count} password history entries")
    
    async def populate_account_securities(self):
        """Populate account_securities table"""
        logger.info("Populating account securities...")
        count = 0
        
        if not self.talent_ids:
            logger.warning("No talents found, skipping account securities")
            return
        
        for talent_id in self.talent_ids[:10]:
            try:
                await self.conn.execute(
                    """INSERT INTO account_securities 
                    (talent_id, two_factor_enabled, two_factor_secret, 
                    recovery_codes, created_at, updated_at) 
                    VALUES ($1, $2, $3, $4, $5, $6)""",
                    talent_id,
                    random.choice([True, False]),
                    f"secret_{uuid.uuid4()}" if random.choice([True, False]) else None,
                    json.dumps([str(uuid.uuid4())[:8] for _ in range(6)]),
                    datetime.now(),
                    datetime.now()
                )
                count += 1
            except Exception:
                pass
        
        logger.info(f"✅ Created {count} account security records")
    
    async def populate_support_flags(self):
        """Populate support_flags table"""
        logger.info("Populating support flags...")
        count = 0
        
        flags = [
            ("beta_features", "Enable beta features", True),
            ("advanced_analytics", "Enable advanced analytics", True),
            ("export_enabled", "Enable data export", True),
            ("api_access", "Enable API access", False),
            ("custom_branding", "Enable custom branding", False)
        ]
        
        for name, description, enabled in flags:
            try:
                await self.conn.execute(
                    """INSERT INTO support_flags 
                    (flag_name, description, is_enabled, created_at, updated_at) 
                    VALUES ($1, $2, $3, $4, $5)""",
                    name, description, enabled, datetime.now(), datetime.now()
                )
                count += 1
            except Exception:
                pass
        
        logger.info(f"✅ Created {count} support flags")
    
    # ==================== TALENT RELATED ====================
    
    async def populate_talent_skills(self):
        """Populate talent_skills table"""
        logger.info("Populating talent skills...")
        count = 0
        
        if not self.talent_ids:
            logger.warning("No talents found, skipping talent skills")
            return
        
        skills = ["Python", "JavaScript", "React", "Docker", "AWS", "PostgreSQL", 
                 "Kubernetes", "TypeScript", "Go", "Redis"]
        
        for talent_id in self.talent_ids[:10]:
            for skill in random.sample(skills, random.randint(3, 6)):
                try:
                    await self.conn.execute(
                        """INSERT INTO talent_skills 
                        (talent_id, skill_name, proficiency_level, years_experience, created_at, updated_at) 
                        VALUES ($1, $2, $3, $4, $5, $6)""",
                        talent_id,
                        skill,
                        random.choice(['beginner', 'intermediate', 'advanced', 'expert']),
                        random.randint(1, 10),
                        datetime.now(),
                        datetime.now()
                    )
                    count += 1
                except Exception:
                    pass
        
        logger.info(f"✅ Created {count} talent skills")
    
    async def populate_studio_areas(self):
        """Populate studio_areas table"""
        logger.info("Populating studio areas...")
        count = 0
        
        if not self.studio_ids or not self.area_ids:
            logger.warning("No studios or areas found, skipping studio_areas")
            return
        
        for studio_id in self.studio_ids:
            for area_id in random.sample(self.area_ids, min(2, len(self.area_ids))):
                try:
                    await self.conn.execute(
                        """INSERT INTO studio_areas 
                        (studio_id, area_id, created_at) 
                        VALUES ($1, $2, $3)""",
                        studio_id,
                        area_id,
                        datetime.now()
                    )
                    count += 1
                except Exception:
                    pass
        
        logger.info(f"✅ Created {count} studio area links")


async def main():
    """Main execution function"""
    populator = CompleteDBPopulator()
    await populator.populate_all()


if __name__ == "__main__":
    asyncio.run(main())