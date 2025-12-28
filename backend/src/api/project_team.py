"""
🔗 Convergio - Project Team Management API
WS2: Manage team assignments (talents and agents) for projects
"""

from typing import List

import structlog
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db_session
from ..models.project_assignment import ProjectAssignment
from ..models.talent import Talent
from .schemas.project_assignment import (
    ProjectAssignmentUpdate,
    ProjectAssignmentResponse,
    ProjectAssignmentWithResource,
    ProjectTeamResponse,
    ResourceProjectsResponse,
    TeamMemberAdd,
    TeamMemberBulkAdd,
)

logger = structlog.get_logger()
router = APIRouter(tags=["Project Team Management"])


async def _get_resource_details(
    db: AsyncSession,
    resource_type: str,
    resource_id: int
) -> dict:
    """Get resource details (talent or agent)"""
    if resource_type == 'talent':
        talent = await Talent.get_by_id(db, resource_id)
        if talent:
            return {
                'resource_name': talent.full_name,
                'resource_email': talent.email,
                'resource_role': talent.role,
                'resource_availability': talent.availability,
            }
    elif resource_type == 'agent':
        return {
            'resource_name': f'Agent #{resource_id}',
            'resource_email': None,
            'resource_role': 'AI Agent',
            'resource_availability': 100,
        }
    return {}


@router.get("/projects/{project_id}/team", response_model=ProjectTeamResponse)
async def get_project_team(
    project_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """
    👥 Get complete team for a project

    Returns all talents and agents assigned to the project
    """

    try:
        assignments = await ProjectAssignment.get_by_project(db, project_id, status='active')

        talents = []
        agents = []
        total_allocation = 0

        for assignment in assignments:
            details = await _get_resource_details(db, assignment.resource_type, assignment.resource_id)
            response = ProjectAssignmentWithResource(
                id=assignment.id,
                project_id=assignment.project_id,
                resource_type=assignment.resource_type,
                resource_id=assignment.resource_id,
                allocation_pct=assignment.allocation_pct,
                role_in_project=assignment.role_in_project,
                start_date=assignment.start_date,
                end_date=assignment.end_date,
                billable=assignment.billable,
                hourly_rate_override=assignment.hourly_rate_override,
                notes=assignment.notes,
                status=assignment.status,
                created_at=assignment.created_at,
                updated_at=assignment.updated_at,
                **details
            )

            if assignment.resource_type == 'talent':
                talents.append(response)
            else:
                agents.append(response)

            total_allocation += assignment.allocation_pct

        return ProjectTeamResponse(
            project_id=project_id,
            talents=talents,
            agents=agents,
            total_members=len(talents) + len(agents),
            total_allocation=total_allocation,
        )

    except Exception as e:
        logger.error("❌ Failed to get project team", error=str(e), project_id=project_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve project team"
        )


@router.post("/projects/{project_id}/team", response_model=ProjectAssignmentResponse)
async def add_team_member(
    project_id: int,
    member: TeamMemberAdd,
    db: AsyncSession = Depends(get_db_session)
):
    """
    ➕ Add team member to project

    Assigns a talent or agent to the project
    """

    try:
        # Check available capacity
        available = await ProjectAssignment.get_available_capacity(
            db, member.resource_type, member.resource_id
        )

        if member.allocation_pct > available:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Resource only has {available}% available capacity"
            )

        # Create assignment
        assignment = await ProjectAssignment.create(
            db,
            project_id=project_id,
            resource_type=member.resource_type,
            resource_id=member.resource_id,
            allocation_pct=member.allocation_pct,
            role_in_project=member.role_in_project,
            start_date=member.start_date,
            end_date=member.end_date,
            billable=member.billable,
            hourly_rate_override=member.hourly_rate_override,
        )

        logger.info(
            "✅ Team member added",
            project_id=project_id,
            resource_type=member.resource_type,
            resource_id=member.resource_id
        )

        return ProjectAssignmentResponse.model_validate(assignment)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("❌ Failed to add team member", error=str(e), project_id=project_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add team member"
        )


@router.post("/projects/{project_id}/team/bulk", response_model=List[ProjectAssignmentResponse])
async def add_team_members_bulk(
    project_id: int,
    request: TeamMemberBulkAdd,
    db: AsyncSession = Depends(get_db_session)
):
    """
    ➕ Add multiple team members to project at once
    """

    try:
        results = []

        for member in request.members:
            # Check available capacity
            available = await ProjectAssignment.get_available_capacity(
                db, member.resource_type, member.resource_id
            )

            if member.allocation_pct > available:
                logger.warning(
                    "⚠️ Skipping member - insufficient capacity",
                    resource_type=member.resource_type,
                    resource_id=member.resource_id,
                    available=available,
                    requested=member.allocation_pct
                )
                continue

            assignment = await ProjectAssignment.create(
                db,
                project_id=project_id,
                resource_type=member.resource_type,
                resource_id=member.resource_id,
                allocation_pct=member.allocation_pct,
                role_in_project=member.role_in_project,
                start_date=member.start_date,
                end_date=member.end_date,
                billable=member.billable,
                hourly_rate_override=member.hourly_rate_override,
            )
            results.append(ProjectAssignmentResponse.model_validate(assignment))

        logger.info("✅ Bulk team members added", project_id=project_id, count=len(results))

        return results

    except Exception as e:
        logger.error("❌ Failed to add team members", error=str(e), project_id=project_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add team members"
        )


@router.patch("/projects/{project_id}/team/{resource_id}", response_model=ProjectAssignmentResponse)
async def update_team_member(
    project_id: int,
    resource_id: int,
    resource_type: str = Query(..., description="talent or agent"),
    update: ProjectAssignmentUpdate = None,
    db: AsyncSession = Depends(get_db_session)
):
    """
    ✏️ Update team member assignment
    """

    try:
        # Find the assignment
        assignments = await ProjectAssignment.get_by_project(db, project_id)
        assignment = next(
            (a for a in assignments if a.resource_type == resource_type and a.resource_id == resource_id),
            None
        )

        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found"
            )

        # Check allocation if changed
        if update and update.allocation_pct is not None:
            current = await ProjectAssignment.get_total_allocation(db, resource_type, resource_id)
            current -= assignment.allocation_pct  # Exclude current assignment
            available = 100 - current

            if update.allocation_pct > available:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Resource only has {available}% available capacity"
                )

        # Update
        if update:
            await assignment.update(db, update.model_dump(exclude_unset=True))

        logger.info(
            "✅ Team member updated",
            project_id=project_id,
            resource_type=resource_type,
            resource_id=resource_id
        )

        return ProjectAssignmentResponse.model_validate(assignment)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("❌ Failed to update team member", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update team member"
        )


@router.delete("/projects/{project_id}/team/{resource_id}")
async def remove_team_member(
    project_id: int,
    resource_id: int,
    resource_type: str = Query(..., description="talent or agent"),
    db: AsyncSession = Depends(get_db_session)
):
    """
    🗑️ Remove team member from project
    """

    try:
        # Find the assignment
        assignments = await ProjectAssignment.get_by_project(db, project_id)
        assignment = next(
            (a for a in assignments if a.resource_type == resource_type and a.resource_id == resource_id),
            None
        )

        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found"
            )

        await assignment.delete(db)

        logger.info(
            "✅ Team member removed",
            project_id=project_id,
            resource_type=resource_type,
            resource_id=resource_id
        )

        return {"message": "Team member removed successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("❌ Failed to remove team member", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove team member"
        )


@router.get("/talents/{talent_id}/projects", response_model=ResourceProjectsResponse)
async def get_talent_projects(
    talent_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """
    📋 Get all project assignments for a talent
    """

    try:
        assignments = await ProjectAssignment.get_talent_projects(db, talent_id)
        total = await ProjectAssignment.get_total_allocation(db, 'talent', talent_id)
        available = await ProjectAssignment.get_available_capacity(db, 'talent', talent_id)

        return ResourceProjectsResponse(
            resource_type='talent',
            resource_id=talent_id,
            assignments=[ProjectAssignmentResponse.model_validate(a) for a in assignments],
            total_allocation=total,
            available_capacity=available,
        )

    except Exception as e:
        logger.error("❌ Failed to get talent projects", error=str(e), talent_id=talent_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve talent projects"
        )


@router.get("/agents/{agent_id}/projects", response_model=ResourceProjectsResponse)
async def get_agent_projects(
    agent_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """
    📋 Get all project assignments for an agent
    """

    try:
        assignments = await ProjectAssignment.get_agent_projects(db, agent_id)
        total = await ProjectAssignment.get_total_allocation(db, 'agent', agent_id)
        available = await ProjectAssignment.get_available_capacity(db, 'agent', agent_id)

        return ResourceProjectsResponse(
            resource_type='agent',
            resource_id=agent_id,
            assignments=[ProjectAssignmentResponse.model_validate(a) for a in assignments],
            total_allocation=total,
            available_capacity=available,
        )

    except Exception as e:
        logger.error("❌ Failed to get agent projects", error=str(e), agent_id=agent_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve agent projects"
        )
