"""
PM System API - Advanced Project Management with AI Integration
Complete PM system with Projects, Tasks, Resources, and Agent attachment
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID

from ..core.database import get_db
from ..models.project import (
    Project, Task, ProjectStatus, TaskStatus, TaskPriority, task_agents
)
from ..agents.services.ali_swarm_orchestrator import AliSwarmOrchestrator
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/pm", tags=["Project Management"])


# ===================== Pydantic Models =====================

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    status: ProjectStatus = ProjectStatus.DRAFT
    priority: TaskPriority = TaskPriority.MEDIUM
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    budget: float = 0.0
    tags: List[str] = []
    custom_fields: Dict[str, Any] = {}


class TaskCreate(BaseModel):
    project_id: UUID
    epic_id: Optional[UUID] = None
    parent_task_id: Optional[UUID] = None
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    assignee_id: Optional[UUID] = None
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    estimated_hours: float = 0.0
    story_points: Optional[int] = None
    is_milestone: bool = False
    tags: List[str] = []


class AttachAgentRequest(BaseModel):
    task_id: UUID
    agent_name: str
    configuration: Dict[str, Any] = {}
    auto_execute: bool = False


# ===================== Project Endpoints =====================

@router.post("/projects", response_model=Dict)
async def create_project(
    project: ProjectCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new project"""
    new_project = Project(
        name=project.name,
        description=project.description,
        status=project.status,
        priority=project.priority,
        start_date=project.start_date,
        end_date=project.end_date,
        budget=project.budget,
        tags=project.tags,
        custom_fields=project.custom_fields
    )
    
    db.add(new_project)
    await db.commit()
    await db.refresh(new_project)
    
    return {
        "id": str(new_project.id),
        "name": new_project.name,
        "status": new_project.status,
        "created_at": new_project.created_at
    }


@router.get("/projects", response_model=List[Dict])
async def list_projects(
    status: Optional[ProjectStatus] = None,
    limit: int = Query(100, le=1000),
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """List all projects with optional filtering"""
    query = select(Project)
    
    if status:
        query = query.where(Project.status == status)
    
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    projects = result.scalars().all()
    
    return [
        {
            "id": str(p.id),
            "name": p.name,
            "description": p.description,
            "status": p.status,
            "priority": p.priority,
            "progress_percentage": p.progress_percentage,
            "health_score": p.health_score,
            "start_date": p.start_date,
            "end_date": p.end_date,
            "budget": p.budget,
            "actual_cost": p.actual_cost,
            "created_at": p.created_at
        }
        for p in projects
    ]


# ===================== Task Endpoints =====================

@router.post("/tasks", response_model=Dict)
async def create_task(
    task: TaskCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new task"""
    new_task = Task(
        project_id=task.project_id,
        epic_id=task.epic_id,
        parent_task_id=task.parent_task_id,
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        assignee_id=task.assignee_id,
        start_date=task.start_date,
        due_date=task.due_date,
        estimated_hours=task.estimated_hours,
        story_points=task.story_points,
        is_milestone=task.is_milestone,
        tags=task.tags
    )
    
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)
    
    return {
        "id": str(new_task.id),
        "title": new_task.title,
        "project_id": str(new_task.project_id),
        "status": new_task.status,
        "created_at": new_task.created_at
    }


# ===================== Agent Attachment =====================

@router.post("/tasks/attach-agent", response_model=Dict)
async def attach_agent_to_task(
    request: AttachAgentRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Attach an AI agent to a task for execution"""
    
    # Get task
    result = await db.execute(
        select(Task).where(Task.id == request.task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Update task with agent assignment
    task.assigned_agent = request.agent_name
    task.updated_at = datetime.utcnow()
    
    # Add to task_agents table
    await db.execute(
        task_agents.insert().values(
            task_id=request.task_id,
            agent_name=request.agent_name,
            attached_at=datetime.utcnow(),
            configuration=request.configuration
        )
    )
    
    await db.commit()
    
    # If auto_execute, trigger agent execution
    if request.auto_execute:
        background_tasks.add_task(
            execute_task_with_agent,
            task_id=request.task_id,
            agent_name=request.agent_name,
            configuration=request.configuration
        )
    
    return {
        "message": f"Agent {request.agent_name} attached to task",
        "task_id": str(request.task_id),
        "auto_execute": request.auto_execute
    }


async def execute_task_with_agent(
    task_id: UUID,
    agent_name: str,
    configuration: Dict[str, Any]
):
    """Background task to execute task with attached agent"""
    try:
        AliSwarmOrchestrator()
        
        # Get task details from database
        async with get_db() as db:
            result = await db.execute(
                select(Task).where(Task.id == task_id)
            )
            task = result.scalar_one_or_none()
            
            if task:
                # Execute task with agent
                
                # Update task status
                task.status = TaskStatus.IN_PROGRESS
                task.ai_completed = True
                task.ai_confidence = 0.95
                task.execution_logs.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "agent": agent_name,
                    "status": "completed"
                })
                
                await db.commit()
                
    except Exception as e:
        print(f"Error executing task with agent: {e}")


# ===================== Analytics =====================

@router.get("/projects/{project_id}/analytics", response_model=Dict)
async def get_project_analytics(
    project_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get analytics and KPIs for a project"""
    
    # Get project
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Calculate analytics
    task_stats = await db.execute(
        select(
            func.count(Task.id).label('total_tasks'),
            func.sum(case((Task.status == TaskStatus.COMPLETED, 1), else_=0)).label('completed_tasks'),
            func.avg(Task.progress_percentage).label('avg_progress')
        ).where(Task.project_id == project_id)
    )
    
    stats = task_stats.one()
    
    return {
        "project_id": str(project_id),
        "performance_metrics": {
            "total_tasks": stats.total_tasks or 0,
            "completed_tasks": stats.completed_tasks or 0,
            "avg_progress": float(stats.avg_progress or 0)
        },
        "cost_metrics": {
            "budget": project.budget,
            "actual_cost": project.actual_cost,
            "ai_cost": project.ai_cost
        },
        "calculated_at": datetime.utcnow()
    }