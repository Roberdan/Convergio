#!/usr/bin/env python3
"""
📊 Convergio Project Management Data Population Script

This script populates the database with sample project data for testing
and demonstration purposes. It creates realistic engagements and activities
that showcase the project management capabilities.

Usage:
    python populate_pm_data.py
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.database import get_async_session, init_db
from src.models.engagement import Engagement
from src.models.activity import Activity


async def populate_sample_data() -> None:
    """
    Populate the database with sample project management data.
    
    Creates realistic engagements and activities that demonstrate
    the full range of project management features.
    """
    try:
        print("🚀 Initializing database...")
        await init_db()
        
        async with get_async_session() as db:
            print("📋 Creating sample engagements...")
            
            # Sample project data with realistic scenarios
            sample_engagements = [
                {
                    "title": "AI Agent Platform Development",
                    "description": "Build a comprehensive AI agent management platform with real-time coordination, monitoring, and analytics capabilities",
                    "status": "in_progress",
                    "created_at": datetime.utcnow() - timedelta(days=15),
                    "updated_at": datetime.utcnow() - timedelta(hours=2)
                },
                {
                    "title": "Customer Support Automation",
                    "description": "Implement intelligent customer support automation using AI agents for ticket routing and resolution",
                    "status": "planning",
                    "created_at": datetime.utcnow() - timedelta(days=8),
                    "updated_at": datetime.utcnow() - timedelta(days=1)
                },
                {
                    "title": "Data Analytics Dashboard",
                    "description": "Create an advanced analytics dashboard for business intelligence and performance monitoring",
                    "status": "completed",
                    "created_at": datetime.utcnow() - timedelta(days=30),
                    "updated_at": datetime.utcnow() - timedelta(days=5)
                },
                {
                    "title": "Security Framework Implementation",
                    "description": "Deploy comprehensive security framework with AI-powered threat detection and response",
                    "status": "in_progress",
                    "created_at": datetime.utcnow() - timedelta(days=12),
                    "updated_at": datetime.utcnow() - timedelta(hours=6)
                },
                {
                    "title": "API Gateway Enhancement",
                    "description": "Upgrade API gateway with advanced routing, rate limiting, and monitoring capabilities",
                    "status": "planning",
                    "created_at": datetime.utcnow() - timedelta(days=3),
                    "updated_at": datetime.utcnow()
                }
            ]
            
            # Create and save engagements
            created_engagements = []
            for engagement_data in sample_engagements:
                engagement = Engagement(**engagement_data)
                db.add(engagement)
                created_engagements.append(engagement)
            
            await db.commit()
            print(f"✅ Created {len(created_engagements)} engagements")
            
            # Create sample activities for each engagement
            print("📝 Creating sample activities...")
            
            activity_templates = [
                {
                    "title": "Requirements Analysis",
                    "description": "Gather and analyze project requirements from stakeholders",
                    "status": "completed",
                    "priority": "high"
                },
                {
                    "title": "System Design",
                    "description": "Design system architecture and technical specifications",
                    "status": "in_progress",
                    "priority": "high"
                },
                {
                    "title": "Development",
                    "description": "Implement core functionality and features",
                    "status": "pending",
                    "priority": "medium"
                },
                {
                    "title": "Testing",
                    "description": "Perform unit, integration, and system testing",
                    "status": "pending",
                    "priority": "medium"
                },
                {
                    "title": "Documentation",
                    "description": "Create user and technical documentation",
                    "status": "pending",
                    "priority": "low"
                },
                {
                    "title": "Deployment",
                    "description": "Deploy to production environment",
                    "status": "pending",
                    "priority": "high"
                }
            ]
            
            # Create activities for each engagement
            total_activities = 0
            for engagement in created_engagements:
                for i, template in enumerate(activity_templates):
                    # Vary status based on engagement progress
                    if engagement.status == "completed":
                        activity_status = "completed"
                    elif engagement.status == "in_progress":
                        activity_status = "completed" if i < 3 else "in_progress" if i == 3 else "pending"
                    else:
                        activity_status = "pending"
                    
                    activity = Activity(
                        title=template["title"],
                        description=template["description"],
                        status=activity_status,
                        priority=template["priority"],
                        engagement_id=engagement.id,
                        created_at=engagement.created_at + timedelta(days=i),
                        updated_at=engagement.updated_at
                    )
                    db.add(activity)
                    total_activities += 1
            
            await db.commit()
            print(f"✅ Created {total_activities} activities")
            
            print("\n🎉 Data population completed successfully!")
            print(f"📊 Total engagements: {len(created_engagements)}")
            print(f"📝 Total activities: {total_activities}")
            
    except Exception as e:
        print(f"❌ Error populating data: {e}")
        raise


async def main() -> None:
    """Main entry point for the data population script."""
    print("🚀 Starting Convergio Project Management Data Population")
    print("=" * 60)
    
    try:
        await populate_sample_data()
        print("\n✅ All data has been populated successfully!")
        
    except Exception as e:
        print(f"\n❌ Failed to populate data: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
