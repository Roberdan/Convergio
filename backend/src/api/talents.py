"""
👥 Convergio - Talents Management API (No Auth Version)
Complete talent management with hierarchy and profiles - no authentication required
"""

from typing import List, Optional
from datetime import datetime

import structlog
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db_session
from src.models.talent import Talent

logger = structlog.get_logger()
router = APIRouter(tags=["Talent Management"])


# Request/Response models
class TalentCreateRequest(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    password_hash: Optional[str] = None
    is_admin: Optional[bool] = False


class TalentUpdateRequest(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_admin: Optional[bool] = None


class TalentResponse(BaseModel):
    id: int
    email: str
    username: str  # Computed from email
    first_name: Optional[str]
    last_name: Optional[str]
    full_name: str
    is_admin: Optional[bool]
    is_active: bool  # Computed from deleted_at
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


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
        
        return [
            TalentResponse(
                id=talent.id,
                username=talent.username,
                email=talent.email,
                first_name=talent.first_name,
                last_name=talent.last_name,
                full_name=talent.full_name,
                is_admin=talent.is_admin,
                is_active=talent.is_active,
                created_at=talent.created_at,
                updated_at=talent.updated_at,
            )
            for talent in talents
        ]
        
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
        
        return TalentResponse(
            id=talent.id,
            username=talent.username,
            email=talent.email,
            first_name=talent.first_name,
            last_name=talent.last_name,
            full_name=talent.full_name,
            position=talent.position,
            department=talent.department,
            manager_id=talent.manager_id,
            is_active=talent.is_active,
            created_at=talent.created_at,
            updated_at=talent.updated_at,
        )
        
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
        # Check if username already exists
        existing_talent = await Talent.get_by_username(db, request.username)
        if existing_talent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )
        
        # Check if email already exists
        if request.email:
            existing_email = await Talent.get_by_email(db, request.email)
            if existing_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already exists"
                )
        
        # Create talent
        talent = await Talent.create(db, **request.dict())
        
        logger.info("✅ Talent created", talent_id=talent.id, username=request.username)
        
        return TalentResponse(
            id=talent.id,
            username=talent.username,
            email=talent.email,
            first_name=talent.first_name,
            last_name=talent.last_name,
            full_name=talent.full_name,
            position=talent.position,
            department=talent.department,
            manager_id=talent.manager_id,
            is_active=talent.is_active,
            created_at=talent.created_at,
            updated_at=talent.updated_at,
        )
        
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
        
        # Update talent
        await talent.update(db, request.dict(exclude_unset=True))
        
        logger.info("✅ Talent updated", talent_id=talent_id)
        
        return TalentResponse(
            id=talent.id,
            username=talent.username,
            email=talent.email,
            first_name=talent.first_name,
            last_name=talent.last_name,
            full_name=talent.full_name,
            position=talent.position,
            department=talent.department,
            manager_id=talent.manager_id,
            is_active=talent.is_active,
            created_at=talent.created_at,
            updated_at=talent.updated_at,
        )
        
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
        
        return [
            TalentResponse(
                id=talent.id,
                username=talent.username,
                email=talent.email,
                first_name=talent.first_name,
                last_name=talent.last_name,
                full_name=talent.full_name,
                position=talent.position,
                department=talent.department,
                manager_id=talent.manager_id,
                is_active=talent.is_active,
                created_at=talent.created_at,
                updated_at=talent.updated_at,
            )
            for talent in subordinates
        ]
        
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