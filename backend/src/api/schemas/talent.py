"""
👥 Convergio - Talent Pydantic Schemas
Request/Response models for Talent API endpoints
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr, ConfigDict


class SkillItem(BaseModel):
    """Individual skill with proficiency level"""
    name: str = Field(..., description="Skill name (e.g., 'Python', 'React')")
    level: str = Field(default="intermediate", description="Proficiency: beginner, intermediate, advanced, expert")
    years: Optional[int] = Field(default=None, description="Years of experience with this skill")


class TalentBase(BaseModel):
    """Base talent schema with common fields"""
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    department: Optional[str] = None
    role: Optional[str] = Field(default=None, description="Job title/role (e.g., Software Engineer)")
    tier: Optional[str] = Field(default=None, description="Seniority: junior, mid, senior, lead, principal")
    skills: Optional[List[SkillItem]] = Field(default_factory=list, description="List of skills")
    hourly_rate: Optional[Decimal] = Field(default=None, ge=0, description="Hourly rate in USD")
    daily_rate: Optional[Decimal] = Field(default=None, ge=0, description="Daily rate in USD")
    availability: Optional[int] = Field(default=100, ge=0, le=100, description="Availability percentage 0-100")
    timezone: Optional[str] = Field(default="UTC", description="IANA timezone (e.g., Europe/Rome)")
    phone: Optional[str] = None
    location: Optional[str] = None
    experience_years: Optional[int] = Field(default=0, ge=0, description="Total years of experience")
    bio: Optional[str] = None


class TalentCreate(TalentBase):
    """Schema for creating a new talent"""
    pass


class TalentUpdate(BaseModel):
    """Schema for updating an existing talent (all fields optional)"""
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    department: Optional[str] = None
    role: Optional[str] = None
    tier: Optional[str] = None
    skills: Optional[List[SkillItem]] = None
    hourly_rate: Optional[Decimal] = None
    daily_rate: Optional[Decimal] = None
    availability: Optional[int] = Field(default=None, ge=0, le=100)
    timezone: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    experience_years: Optional[int] = Field(default=None, ge=0)
    bio: Optional[str] = None


class TalentResponse(TalentBase):
    """Schema for talent response"""
    id: int
    is_admin: Optional[bool] = False
    rating: Optional[Decimal] = Field(default=0.0, ge=0, le=5)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Computed properties
    full_name: Optional[str] = None
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


class TalentListResponse(BaseModel):
    """Schema for paginated talent list response"""
    talents: List[TalentResponse]
    total: int
    skip: int
    limit: int


class TalentSearchParams(BaseModel):
    """Schema for talent search/filter parameters"""
    department: Optional[str] = None
    role: Optional[str] = None
    tier: Optional[str] = None
    skill: Optional[str] = Field(default=None, description="Filter by skill name")
    min_availability: Optional[int] = Field(default=None, ge=0, le=100)
    location: Optional[str] = None
    is_active: Optional[bool] = True
