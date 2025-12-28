"""
🔗 Convergio - Project Assignment Pydantic Schemas
Request/Response models for Project Assignment API endpoints
"""

from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict


class ProjectAssignmentBase(BaseModel):
    """Base project assignment schema"""
    project_id: int
    resource_type: Literal["talent", "agent"] = Field(..., description="Type of resource")
    resource_id: int = Field(..., description="ID of the talent or agent")
    allocation_pct: int = Field(default=100, ge=0, le=100, description="Allocation percentage")
    role_in_project: Optional[str] = Field(default=None, description="Role specific to this project")
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    billable: bool = True
    hourly_rate_override: Optional[Decimal] = Field(default=None, ge=0, description="Override hourly rate for this project")
    notes: Optional[str] = None


class ProjectAssignmentCreate(ProjectAssignmentBase):
    """Schema for creating a new project assignment"""
    pass


class ProjectAssignmentUpdate(BaseModel):
    """Schema for updating an existing project assignment"""
    allocation_pct: Optional[int] = Field(default=None, ge=0, le=100)
    role_in_project: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[Literal["active", "paused", "completed", "cancelled"]] = None
    billable: Optional[bool] = None
    hourly_rate_override: Optional[Decimal] = None
    notes: Optional[str] = None


class ProjectAssignmentResponse(ProjectAssignmentBase):
    """Schema for project assignment response"""
    id: int
    status: str = "active"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ProjectAssignmentWithResource(ProjectAssignmentResponse):
    """Extended response with resource details"""
    resource_name: Optional[str] = None
    resource_email: Optional[str] = None
    resource_role: Optional[str] = None
    resource_availability: Optional[int] = None


class ProjectTeamResponse(BaseModel):
    """Response schema for a project's full team"""
    project_id: int
    talents: List[ProjectAssignmentWithResource] = []
    agents: List[ProjectAssignmentWithResource] = []
    total_members: int = 0
    total_allocation: int = 0  # Sum of all allocations


class ResourceProjectsResponse(BaseModel):
    """Response schema for a resource's project assignments"""
    resource_type: str
    resource_id: int
    assignments: List[ProjectAssignmentResponse] = []
    total_allocation: int = 0  # Current total allocation
    available_capacity: int = 100  # Remaining capacity


class TeamMemberAdd(BaseModel):
    """Schema for adding a team member to a project"""
    resource_type: Literal["talent", "agent"]
    resource_id: int
    allocation_pct: int = Field(default=100, ge=0, le=100)
    role_in_project: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    billable: bool = True
    hourly_rate_override: Optional[Decimal] = None


class TeamMemberBulkAdd(BaseModel):
    """Schema for adding multiple team members at once"""
    members: List[TeamMemberAdd]
