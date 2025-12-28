"""
Project management handlers for agents
"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import uuid4

import structlog
from fastapi import HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ...agents.orchestrator import get_agent_orchestrator
from ...core.redis import cache_get, cache_set
from .models import ProjectRequest

logger = structlog.get_logger()


def get_required_agents_for_project(project_type: str) -> List[str]:
    """
    Determine which agents are required for a project type.
    
    Args:
        project_type: Type of project
    
    Returns:
        List of required agent IDs
    """
    
    agent_mapping = {
        "web_development": [
            "baccio-tech-architect",
            "davide-project-manager",
            "diana-performance-dashboard",
            "luca-security"
        ],
        "data_analysis": [
            "amy-cfo",
            "diana-performance-dashboard",
            "ali-chief-of-staff"
        ],
        "marketing_campaign": [
            "sofia-social-media",
            "amy-cfo",
            "davide-project-manager"
        ],
        "business_strategy": [
            "ali-chief-of-staff",
            "amy-cfo",
            "sofia-social-media",
            "davide-project-manager"
        ],
        "security_audit": [
            "luca-security",
            "baccio-tech-architect",
            "ali-chief-of-staff"
        ],
        "system_architecture": [
            "baccio-tech-architect",
            "luca-security",
            "diana-performance-dashboard",
            "davide-project-manager"
        ],
        "financial_planning": [
            "amy-cfo",
            "ali-chief-of-staff",
            "davide-project-manager"
        ],
        "product_launch": [
            "davide-project-manager",
            "sofia-social-media",
            "amy-cfo",
            "baccio-tech-architect",
            "diana-performance-dashboard"
        ]
    }
    
    # Default team if project type not recognized
    default_team = [
        "ali-chief-of-staff",
        "davide-project-manager",
        "amy-cfo"
    ]
    
    return agent_mapping.get(project_type, default_team)


def get_expected_deliverables(project_type: str) -> List[str]:
    """
    Get expected deliverables for a project type.
    
    Args:
        project_type: Type of project
    
    Returns:
        List of expected deliverables
    """
    
    deliverables_mapping = {
        "web_development": [
            "Technical Architecture Document",
            "Project Timeline and Milestones",
            "Security Assessment Report",
            "Performance Metrics Dashboard",
            "Deployment Strategy",
            "Testing Plan"
        ],
        "data_analysis": [
            "Data Analysis Report",
            "Financial Impact Assessment",
            "Executive Summary",
            "Visualization Dashboard",
            "Recommendations Document"
        ],
        "marketing_campaign": [
            "Campaign Strategy Document",
            "Content Calendar",
            "Budget Allocation Plan",
            "Social Media Strategy",
            "ROI Projections",
            "Performance KPIs"
        ],
        "business_strategy": [
            "Strategic Plan Document",
            "Financial Projections",
            "Market Analysis",
            "Implementation Roadmap",
            "Risk Assessment",
            "Success Metrics"
        ],
        "security_audit": [
            "Security Vulnerability Report",
            "Risk Assessment Matrix",
            "Remediation Plan",
            "Compliance Check Results",
            "Security Architecture Review"
        ],
        "system_architecture": [
            "System Architecture Diagram",
            "Technical Specifications",
            "Security Considerations",
            "Performance Requirements",
            "Implementation Plan",
            "Monitoring Strategy"
        ],
        "financial_planning": [
            "Financial Plan Document",
            "Budget Breakdown",
            "Revenue Projections",
            "Cost Analysis",
            "Risk Factors",
            "Investment Recommendations"
        ],
        "product_launch": [
            "Launch Plan Document",
            "Marketing Strategy",
            "Technical Requirements",
            "Budget and Timeline",
            "Performance Metrics",
            "Risk Mitigation Plan"
        ]
    }
    
    # Default deliverables
    default_deliverables = [
        "Project Plan",
        "Requirements Analysis",
        "Implementation Strategy",
        "Success Metrics"
    ]
    
    return deliverables_mapping.get(project_type, default_deliverables)


async def handle_project_request(
    request: ProjectRequest,
    req: Request,
    db: AsyncSession
) -> Dict[str, Any]:
    """
    Handle a project management request.
    
    Args:
        request: Project request details
        req: FastAPI request object
        db: Database session
    
    Returns:
        Project execution plan
    """
    
    project_id = str(uuid4())
    user_id = request.user_id or "anonymous"
    
    logger.info(
        "📋 Starting project planning",
        project_id=project_id,
        project_type=request.project_type,
        user_id=user_id
    )
    
    try:
        # Get required agents
        required_agents = get_required_agents_for_project(request.project_type)
        expected_deliverables = get_expected_deliverables(request.project_type)
        
        # Get orchestrator
        orchestrator = await get_agent_orchestrator()
        
        # Build project context
        project_context = {
            "project_id": project_id,
            "project_type": request.project_type,
            "project_name": request.project_name,
            "description": request.description,
            "requirements": request.requirements,
            "constraints": request.constraints,
            "budget": request.budget,
            "timeline_days": request.timeline_days,
            "required_agents": required_agents,
            "expected_deliverables": expected_deliverables
        }
        
        # Create project planning prompt
        planning_prompt = f"""
        Project Planning Request:
        
        Project: {request.project_name}
        Type: {request.project_type}
        Description: {request.description}
        
        Requirements:
        {chr(10).join(f'- {req}' for req in request.requirements)}
        
        Constraints:
        {chr(10).join(f'- {con}' for con in request.constraints) if request.constraints else 'None specified'}
        
        Budget: ${request.budget:,.2f} if request.budget else 'Not specified'
        Timeline: {request.timeline_days} days if request.timeline_days else 'Not specified'
        
        Please create a comprehensive project plan including:
        1. Detailed breakdown of tasks and phases
        2. Agent assignments for each task
        3. Timeline with milestones
        4. Risk assessment and mitigation strategies
        5. Success metrics and KPIs
        6. Budget allocation (if applicable)
        7. Deliverables and their due dates
        """
        
        # Execute project planning with all required agents
        result = await orchestrator.orchestrate_conversation(
            message=planning_prompt,
            user_id=user_id,
            conversation_id=f"project_{project_id}",
            context=project_context
        )
        
        # Parse and structure the response
        project_plan = {
            "project_id": project_id,
            "project_name": request.project_name,
            "project_type": request.project_type,
            "status": "planning_complete",
            "created_at": datetime.now().isoformat(),
            "estimated_completion": (
                datetime.now() + timedelta(days=request.timeline_days)
            ).isoformat() if request.timeline_days else None,
            "assigned_agents": required_agents,
            "expected_deliverables": expected_deliverables,
            "planning_output": result.get("response"),
            "agents_consulted": result.get("agents_used", []),
            "planning_duration": result.get("duration_seconds", 0),
            "next_steps": [
                "Review project plan with stakeholders",
                "Confirm resource allocation",
                "Initialize project tracking",
                "Begin execution phase"
            ]
        }
        
        # Cache project plan
        cache_key = f"project:{project_id}"
        await cache_set(
            cache_key,
            json.dumps(project_plan),
            expire=86400  # 24 hours TTL
        )
        
        logger.info(
            "✅ Project planning completed",
            project_id=project_id,
            agents_used=result.get("agents_used")
        )
        
        return project_plan
        
    except Exception as e:
        logger.error(f"Project planning failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Project planning failed: {str(e)}"
        )


async def get_project_status(
    project_id: str,
    db: AsyncSession
) -> Dict[str, Any]:
    """
    Get the status of a project.
    
    Args:
        project_id: Project ID
        db: Database session
    
    Returns:
        Project status
    """
    
    # Try to get from cache first
    cache_key = f"project:{project_id}"
    cached_data = await cache_get(cache_key)
    
    if cached_data:
        return json.loads(cached_data)
    
    # If not in cache, return not found
    raise HTTPException(
        status_code=404,
        detail=f"Project {project_id} not found"
    )


async def list_projects(
    user_id: Optional[str],
    db: AsyncSession
) -> List[Dict[str, Any]]:
    """
    List all projects for a user.
    
    Args:
        user_id: User ID (optional)
        db: Database session
    
    Returns:
        List of projects
    """
    
    # In a real implementation, this would query the database
    # For now, return empty list as we're using cache only
    projects = []
    
    # Note: In production, implement proper database storage
    logger.info(f"Listing projects for user: {user_id or 'all'}")
    
    return projects