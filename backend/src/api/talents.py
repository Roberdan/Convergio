"""
👥 Convergio - Talents Management API (No Auth Version)
Complete talent management with hierarchy and profiles - no authentication required
WS2: Enhanced with People Data Model fields
"""

from typing import List, Optional
from datetime import datetime
from decimal import Decimal

import structlog
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db_session
from ..models.talent import Talent

logger = structlog.get_logger()
router = APIRouter(tags=["Talent Management"])


# Request/Response models - WS2 Enhanced
class SkillItem(BaseModel):
    """Individual skill with proficiency level"""
    name: str
    level: str = "intermediate"  # beginner, intermediate, advanced, expert
    years: Optional[int] = None


class TalentCreateRequest(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    department: Optional[str] = None
    role: Optional[str] = Field(default=None, description="Job title/role")
    tier: Optional[str] = Field(default=None, description="Seniority: junior, mid, senior, lead, principal")
    skills: Optional[List[SkillItem]] = Field(default_factory=list)
    hourly_rate: Optional[Decimal] = None
    daily_rate: Optional[Decimal] = None
    availability: Optional[int] = Field(default=100, ge=0, le=100)
    timezone: Optional[str] = "UTC"
    phone: Optional[str] = None
    location: Optional[str] = None
    experience_years: Optional[int] = Field(default=0, ge=0)
    bio: Optional[str] = None
    is_admin: Optional[bool] = False


class TalentUpdateRequest(BaseModel):
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
    is_admin: Optional[bool] = None


class TalentResponse(BaseModel):
    id: int
    email: str
    username: str  # Computed from email
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: str
    department: Optional[str] = None
    role: Optional[str] = None
    tier: Optional[str] = None
    skills: Optional[List[SkillItem]] = None
    hourly_rate: Optional[Decimal] = None
    daily_rate: Optional[Decimal] = None
    availability: Optional[int] = 100
    timezone: Optional[str] = "UTC"
    phone: Optional[str] = None
    location: Optional[str] = None
    experience_years: Optional[int] = 0
    bio: Optional[str] = None
    rating: Optional[Decimal] = None
    is_admin: Optional[bool] = False
    is_active: bool = True  # Computed from deleted_at
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


def _talent_to_response(talent: Talent) -> TalentResponse:
    """Convert Talent model to TalentResponse"""
    skills = None
    if talent.skills:
        try:
            skills = [SkillItem(**s) if isinstance(s, dict) else s for s in talent.skills]
        except Exception:
            skills = None

    return TalentResponse(
        id=talent.id,
        email=talent.email,
        username=talent.username,
        first_name=talent.first_name,
        last_name=talent.last_name,
        full_name=talent.full_name,
        department=talent.department,
        role=talent.role,
        tier=talent.tier,
        skills=skills,
        hourly_rate=talent.hourly_rate,
        daily_rate=talent.daily_rate,
        availability=talent.availability or 100,
        timezone=talent.timezone or "UTC",
        phone=talent.phone,
        location=talent.location,
        experience_years=talent.experience_years or 0,
        bio=talent.bio,
        rating=talent.rating,
        is_admin=talent.is_admin,
        is_active=talent.is_active,
        created_at=talent.created_at,
        updated_at=talent.updated_at,
    )


@router.get("", response_model=List[TalentResponse])
async def get_all_talents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db_session)
):
    """
    👥 Get all talents with filtering and pagination
    
    Supports filtering by active status
    """
    
    try:
        talents = await Talent.get_all(
            db, 
            skip=skip, 
            limit=limit,
            is_active=is_active
        )
        
        return [_talent_to_response(talent) for talent in talents]
        
    except Exception as e:
        logger.error("❌ Failed to get talents", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve talents"
        )


@router.get("/{talent_id}", response_model=TalentResponse)
async def get_talent_by_id(
    talent_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """
    👤 Get talent by ID
    
    Returns detailed talent information
    """
    
    try:
        talent = await Talent.get_by_id(db, talent_id)
        
        if not talent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Talent not found"
            )
        
        return _talent_to_response(talent)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("❌ Failed to get talent", error=str(e), talent_id=talent_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve talent"
        )


@router.post("", response_model=TalentResponse)
async def create_talent(
    request: TalentCreateRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    ➕ Create new talent
    
    Creates talent profile (no authentication required)
    """
    
    try:
        # Check if email already exists
        existing_email = await Talent.get_by_email(db, request.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )

        # Convert skills to dict format for storage
        data = request.model_dump(exclude_unset=True)
        if 'skills' in data and data['skills']:
            data['skills'] = [s.model_dump() if hasattr(s, 'model_dump') else s for s in data['skills']]

        # Create talent
        talent = await Talent.create(db, **data)

        logger.info("✅ Talent created", talent_id=talent.id, email=request.email)

        return _talent_to_response(talent)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("❌ Failed to create talent", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create talent"
        )


@router.put("/{talent_id}", response_model=TalentResponse)
async def update_talent(
    talent_id: int,
    request: TalentUpdateRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    ✏️ Update talent information
    
    Updates talent profile data
    """
    
    try:
        talent = await Talent.get_by_id(db, talent_id)
        
        if not talent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Talent not found"
            )
        
        # Convert skills to dict format for storage
        data = request.model_dump(exclude_unset=True)
        if 'skills' in data and data['skills']:
            data['skills'] = [s.model_dump() if hasattr(s, 'model_dump') else s for s in data['skills']]

        # Update talent
        await talent.update(db, data)

        logger.info("✅ Talent updated", talent_id=talent_id)

        return _talent_to_response(talent)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("❌ Failed to update talent", error=str(e), talent_id=talent_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update talent"
        )


@router.delete("/{talent_id}")
async def delete_talent(
    talent_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """
    🗑️ Delete talent
    
    Soft delete by deactivating the talent
    """
    
    try:
        talent = await Talent.get_by_id(db, talent_id)
        
        if not talent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Talent not found"
            )
        
        # Soft delete by deactivating
        talent.is_active = False
        await talent.save(db)
        
        logger.info("✅ Talent deactivated", talent_id=talent_id)
        
        return {"message": "Talent deactivated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("❌ Failed to delete talent", error=str(e), talent_id=talent_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete talent"
        )


@router.get("/{talent_id}/subordinates", response_model=List[TalentResponse])
async def get_subordinates(
    talent_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """
    👥 Get talent's subordinates
    
    Returns all talents managed by the specified talent
    """
    
    try:
        subordinates = await Talent.get_subordinates(db, talent_id)
        
        return [_talent_to_response(talent) for talent in subordinates]

    except Exception as e:
        logger.error("❌ Failed to get subordinates", error=str(e), talent_id=talent_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve subordinates"
        )


@router.get("/{talent_id}/hierarchy")
async def get_talent_hierarchy(
    talent_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """
    🌳 Get talent hierarchy
    
    Returns the complete organizational hierarchy for the talent
    """
    
    try:
        hierarchy = await Talent.get_hierarchy(db, talent_id)
        
        return hierarchy
        
    except Exception as e:
        logger.error("❌ Failed to get hierarchy", error=str(e), talent_id=talent_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve hierarchy"
        )


@router.put("/{talent_id}/manager")
async def update_manager(
    talent_id: int,
    manager_id: Optional[int],
    db: AsyncSession = Depends(get_db_session)
):
    """
    👨‍💼 Update talent's manager
    
    Changes the reporting relationship
    """
    
    try:
        talent = await Talent.get_by_id(db, talent_id)
        
        if not talent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Talent not found"
            )
        
        # Validate manager exists if provided
        if manager_id:
            manager = await Talent.get_by_id(db, manager_id)
            if not manager:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Manager not found"
                )
        
        # Update manager
        talent.manager_id = manager_id
        await talent.save(db)
        
        logger.info("✅ Manager updated", talent_id=talent_id, manager_id=manager_id)
        
        return {"message": "Manager updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("❌ Failed to update manager", error=str(e), talent_id=talent_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update manager"
        )