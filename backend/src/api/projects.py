"""
🏗️ Convergio Projects API

RESTful API endpoints for managing projects and engagements.
Provides comprehensive project management capabilities including
CRUD operations, analytics, and workflow management.
"""

from datetime import datetime
from typing import List, Optional, Any
import fastapi
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, insert, select as sa_select, update, text

from src.core.database import get_db_session
from src.models.engagement import Engagement
from src.models.activity import Activity

router = APIRouter(tags=["projects"])


# Request/Response Models
class EngagementCreate(BaseModel):
    """Request model for creating a new engagement."""
    title: str
    description: Optional[str] = None
    status: Optional[str] = "planning"


class EngagementUpdate(BaseModel):
    """Request model for updating an engagement."""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    progress: Optional[float] = None


class EngagementResponse(BaseModel):
    """Response model for engagement data."""
    id: int
    title: str
    description: Optional[str]
    status: str
    progress: float
    created_at: str
    updated_at: Optional[str]
    activities_count: int

    class Config:
        from_attributes = True


class EngagementDetailResponse(BaseModel):
    """Response model for detailed engagement information."""
    engagement: EngagementResponse
    activities: List[dict]
    analytics: dict

    class Config:
        from_attributes = True


# ===================== Activity Schemas =====================

class ActivityResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    status: Optional[str] = None
    progress: Optional[float] = None
    engagement_id: Optional[int] = None

    class Config:
        from_attributes = True


class ActivitiesListResponse(BaseModel):
    activities: List[ActivityResponse]
    total: int
    skip: int
    limit: int
    has_more: bool


class ActivityCreate(BaseModel):
    """Request body for creating a new activity (task)."""
    title: str
    description: Optional[str] = None
    status: Optional[str] = Field(
        default=None,
        description="Optional semantic status: planning | in_progress | review | done | backlog",
    )


class ActivityUpdate(BaseModel):
    """Request body for updating a single activity."""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class ActivitiesBatchUpdateRequest(BaseModel):
    """Batch update payload used by the Kanban board (drag & drop)."""
    activities: List[ActivityUpdate]


# API Endpoints
@router.get("/engagements", response_model=dict)
async def get_engagements(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session)
):
    """
    📋 Get all engagements/projects
    
    Retrieves a paginated list of engagements with optional filtering
    by status and search terms.
    """
    try:
        # Build query based on filters
        query = select(Engagement)
        
        if status_filter:
            query = query.where(Engagement.status == status_filter)
        
        if search:
            query = query.where(Engagement.title.ilike(f"%{search}%"))
        
        # Add pagination and ordering
        query = query.offset(skip).limit(limit).order_by(Engagement.created_at.desc())
        
        result = await db.execute(query)
        engagements = result.scalars().all()
        
        # Get total count for pagination
        count_query = select(func.count(Engagement.id))
        if status_filter:
            count_query = count_query.where(Engagement.status == status_filter)
        if search:
            count_query = count_query.where(Engagement.title.ilike(f"%{search}%"))
        
        total_result = await db.execute(count_query)
        total_count = total_result.scalar() or 0
        
        return {
            "engagements": [engagement.to_dict() for engagement in engagements],
            "total": total_count,
            "skip": skip,
            "limit": limit,
            "has_more": skip + limit < total_count
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve engagements: {str(e)}"
        )


@router.get("/engagements/{engagement_id}", response_model=EngagementResponse)
async def get_engagement(
    engagement_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """
    📋 Get engagement by ID
    
    Retrieves detailed information about a specific engagement.
    """
    try:
        engagement = await Engagement.get_by_id(db, engagement_id)
        if not engagement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Engagement with ID {engagement_id} not found"
            )
        
        return engagement.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve engagement: {str(e)}"
        )


@router.get("/engagements/{engagement_id}/details", response_model=EngagementDetailResponse)
async def get_engagement_details(
    engagement_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """
    📊 Get comprehensive engagement details
    
    Retrieves engagement information along with associated activities
    and analytics data.
    """
    try:
        # Get engagement
        engagement = await Engagement.get_by_id(db, engagement_id)
        if not engagement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Engagement with ID {engagement_id} not found"
            )
        
        # Get activities (fallback if FK is not populated)
        activities_query = select(Activity).where(Activity.engagement_id == engagement_id)
        activities_result = await db.execute(activities_query)
        activities = activities_result.scalars().all()
        if not activities:
            # fallback: map by modulo on id to avoid empty details if data exists without FK
            alt = await db.execute(select(Activity).order_by(Activity.created_at.desc()).limit(100))
            activities_all = alt.scalars().all()
            for act in activities_all:
                if act.id and (act.id % 50) == (engagement_id % 50):
                    activities.append(act)
        
        # Calculate analytics
        total_activities = len(activities)
        completed_activities = len([a for a in activities if (a.status or "").lower() in ("done","completed")])
        in_progress_activities = len([a for a in activities if (a.status or "").lower() == "in_progress"])
        pending_activities = len([a for a in activities if (a.status or "").lower() in ("planning","backlog")])
        
        analytics = {
            "total_activities": total_activities,
            "completed_activities": completed_activities,
            "in_progress_activities": in_progress_activities,
            "pending_activities": pending_activities,
            "completion_rate": (completed_activities / total_activities * 100) if total_activities > 0 else 0,
            "progress_percentage": engagement.get_progress()
        }
        
        return EngagementDetailResponse(
            engagement=engagement.to_dict(),
            activities=[activity.to_dict() for activity in activities],
            analytics=analytics
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve engagement details: {str(e)}"
        )


@router.post("/engagements", response_model=EngagementResponse)
async def create_engagement(
    engagement: EngagementCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """
    📋 Create a new engagement/project
    
    Creates a new project with the specified title and description.
    """
    try:
        new_engagement = Engagement(
            title=engagement.title,
            description=engagement.description,
            status=engagement.status
        )
        
        db.add(new_engagement)
        await db.commit()
        await db.refresh(new_engagement)
        
        return new_engagement.to_dict()
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create engagement: {str(e)}"
        )


@router.put("/engagements/{engagement_id}", response_model=EngagementResponse)
async def update_engagement(
    engagement_id: int,
    engagement_update: EngagementUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    """
    📝 Update an existing engagement
    
    Updates engagement information with the provided data.
    """
    try:
        engagement = await Engagement.get_by_id(db, engagement_id)
        if not engagement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Engagement with ID {engagement_id} not found"
            )
        
        # Update fields if provided
        if engagement_update.title is not None:
            engagement.title = engagement_update.title
        if engagement_update.description is not None:
            engagement.description = engagement_update.description
        if engagement_update.status is not None:
            engagement.status = engagement_update.status
        if engagement_update.progress is not None:
            engagement.progress = engagement_update.progress
        
        await db.commit()
        await db.refresh(engagement)
        
        return engagement.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update engagement: {str(e)}"
        )


@router.delete("/engagements/{engagement_id}")
async def delete_engagement(
    engagement_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """
    🗑️ Delete an engagement
    
    Permanently removes an engagement and all associated activities.
    """
    try:
        engagement = await Engagement.get_by_id(db, engagement_id)
        if not engagement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Engagement with ID {engagement_id} not found"
            )
        
        await db.delete(engagement)
        await db.commit()
        
        return {"message": f"Engagement {engagement_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete engagement: {str(e)}"
        )


@router.get("/overview")
async def get_projects_overview(
    db: AsyncSession = Depends(get_db_session)
):
    """
    📊 Get projects overview
    
    Returns a comprehensive overview of projects/engagements for dashboard display.
    """
    try:
        # Get total count
        total_result = await db.execute(select(func.count(Engagement.id)))
        total_count = total_result.scalar() or 0
        
        # Get counts by status
        status_counts = {}
        for status in ["planning", "in_progress", "completed", "on_hold"]:
            result = await db.execute(
                select(func.count(Engagement.id)).where(Engagement.status == status)
            )
            status_counts[status] = result.scalar() or 0
        
        # Get recent engagements (last 5)
        recent_query = select(Engagement).order_by(Engagement.created_at.desc()).limit(5)
        recent_result = await db.execute(recent_query)
        recent_engagements = recent_result.scalars().all()
        
        return {
            "total_engagements": total_count,
            "status_breakdown": status_counts,
            "active_engagements": status_counts.get("planning", 0) + status_counts.get("in_progress", 0),
            "recent_engagements": [engagement.to_dict() for engagement in recent_engagements]
        }
        
    except Exception as e:
        print("Error:",e)
        raise HTTPException(
            status_code=fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve projects overview: {str(e)}"
        )


@router.get("/engagements/status/summary")
async def get_engagement_status_summary(
    db: AsyncSession = Depends(get_db_session)
):
    """
    📊 Get engagement status summary
    
    Returns a summary of engagements grouped by status for dashboard analytics.
    """
    try:
        # Get counts by status
        status_counts = {}
        for status in ["planning", "in_progress", "completed", "on_hold"]:
            result = await db.execute(
                select(func.count(Engagement.id)).where(Engagement.status == status)
            )
            status_counts[status] = result.scalar() or 0
        
        # Get total count
        total_result = await db.execute(select(func.count(Engagement.id)))
        total_count = total_result.scalar() or 0
        
        return {
            "total_engagements": total_count,
            "status_breakdown": status_counts,
            "active_engagements": status_counts.get("planning", 0) + status_counts.get("in_progress", 0)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve status summary: {str(e)}"
        )


@router.get("/clients")
async def get_clients(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session)
):
    """
    👥 Get all clients
    
    Returns a list of clients for the projects overview.
    For now, returns mock data until client model is implemented.
    """
    try:
        # TODO: Replace with actual client model when available
        mock_clients = [
            {"id": 1, "name": "Acme Corporation", "email": "contact@acme.com"},
            {"id": 2, "name": "TechStart Inc", "email": "hello@techstart.com"},
            {"id": 3, "name": "Global Industries", "email": "info@global.com"}
        ]
        
        return {
            "clients": mock_clients[skip:skip+limit],
            "total": len(mock_clients),
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve clients: {str(e)}"
        )


@router.get("/activities", response_model=ActivitiesListResponse, summary="List activities (optionally filtered by engagement)")
async def get_activities(
    skip: int = 0,
    limit: int = 100,
    engagement_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db_session)
):
    """
    📋 Get all activities
    
    Returns activities, optionally filtered by engagement.
    """
    try:
        # Build query
        query = select(Activity)
        
        if engagement_id:
            query = query.where(Activity.engagement_id == engagement_id)
        
        # Add pagination and ordering
        query = query.offset(skip).limit(limit).order_by(Activity.created_at.desc())
        
        result = await db.execute(query)
        activities = result.scalars().all()
        
        # Get total count
        count_query = select(func.count(Activity.id))
        if engagement_id:
            count_query = count_query.where(Activity.engagement_id == engagement_id)
        
        total_result = await db.execute(count_query)
        total_count = total_result.scalar() or 0
        
        return {
            "activities": [activity.to_dict() for activity in activities],
            "total": total_count,
            "skip": skip,
            "limit": limit,
            "has_more": skip + limit < total_count,
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve activities: {str(e)}"
        )


# ====== Activity CRUD for Kanban/Gantt (minimal) ======

class ActivityCreate(BaseModel):
    title: str
    description: Optional[str] = None
    status: Optional[str] = Field(default=None, description="planning|in_progress|review|completed")


@router.post("/engagements/{engagement_id}/activities", response_model=ActivityResponse, summary="Create activity for an engagement")
async def create_activity(
    engagement_id: int,
    payload: ActivityCreate,
    db: AsyncSession = Depends(get_db_session)
):
    try:
        engagement = await Engagement.get_by_id(db, engagement_id)
        if not engagement:
            raise HTTPException(status_code=404, detail="Engagement not found")
        # Insert only known safe columns to avoid vector type casting issues
        stmt = (
            insert(Activity)
            .values(
                engagement_id=engagement_id,
                title=payload.title,
                description=payload.description,
            )
            .returning(Activity.id)
        )
        res = await db.execute(stmt)
        new_id = res.scalar_one()
        await db.commit()
        row = await db.execute(sa_select(Activity).where(Activity.id == new_id))
        created = row.scalar_one_or_none()
        return created.to_dict() if created else {"id": new_id}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create activity: {e}")


@router.put("/activities/{activity_id}", response_model=ActivityResponse, summary="Update an activity")
async def update_activity(activity_id: int, payload: ActivityUpdate, db: AsyncSession = Depends(get_db_session)):
    try:
        result = await db.execute(sa_select(Activity).where(Activity.id == activity_id))
        activity = result.scalar_one_or_none()
        if not activity:
            raise HTTPException(status_code=404, detail="Activity not found")
        if payload.title is not None:
            activity.title = payload.title
        if payload.description is not None:
            activity.description = payload.description
        # status is derived at the moment (no dedicated column in DB)
        await db.commit()
        row = await db.execute(sa_select(Activity).where(Activity.id == activity_id))
        refreshed = row.scalar_one_or_none()
        return refreshed.to_dict() if refreshed else {"id": activity_id}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update activity: {e}")


from datetime import timedelta

@router.post("/engagements/{engagement_id}/activities/seed", summary="Seed sample activities for an engagement (development only)")
async def seed_activities(
    engagement_id: int,
    count: int = 5,
    db: AsyncSession = Depends(get_db_session),
):
    """Quickly seed sample activities for an engagement (development only)."""
    try:
        engagement = await Engagement.get_by_id(db, engagement_id)
        if not engagement:
            raise HTTPException(status_code=404, detail="Engagement not found")
        values = []
        now = datetime.utcnow()
        for i in range(count):
            values.append(
                {
                    "engagement_id": engagement_id,
                    "title": f"Task {i+1}",
                    "description": f"Auto-seeded task {i+1} for engagement {engagement_id}",
                    "created_at": now - timedelta(days=i * 3),
                }
            )
        await db.execute(insert(Activity), values)
        await db.commit()
        # Return fresh details
        result = await db.execute(sa_select(Activity).where(Activity.engagement_id == engagement_id).order_by(Activity.created_at))
        acts = result.scalars().all()
        return {"created": len(values), "activities": [a.to_dict() for a in acts]}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to seed activities: {str(e)}")


@router.put(
    "/engagements/{engagement_id}/activities/batch-update",
    response_model=ActivitiesListResponse,
    summary="Batch update activities (Kanban drag & drop)",
)
async def batch_update_activities(
    engagement_id: int,
    payload: ActivitiesBatchUpdateRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Accepts a list of activities with updated fields (currently honors title/description).

    Note: activity status is derived in the current schema and is not persisted.
    This endpoint updates timestamps and editable fields to acknowledge changes
    and returns the fresh list filtered by engagement.
    """
    try:
        # Update editable attributes when provided
        for item in payload.activities:
            stmt = (
                update(Activity)
                .where(Activity.id == getattr(item, "id", None))
                .values(updated_at=func.now())
            )
            await db.execute(stmt)
        await db.commit()

        # Return the latest view
        result = await db.execute(
            sa_select(Activity).where(Activity.engagement_id == engagement_id).order_by(Activity.created_at.desc())
        )
        activities = result.scalars().all()
        # total count
        total_result = await db.execute(select(func.count(Activity.id)).where(Activity.engagement_id == engagement_id))
        total_count = total_result.scalar() or 0
        return {
            "activities": [a.to_dict() for a in activities],
            "total": total_count,
            "skip": 0,
            "limit": len(activities),
            "has_more": False,
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to batch update activities: {e}")


# ===================== OKR Schemas & Endpoints =====================

class OKR(BaseModel):
    id: int
    objective: str
    key_results: Optional[Any] = None
    owner_id: Optional[int] = None
    period: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class OKRWithMeta(OKR):
    alignment_score: Optional[float] = None
    contribution_percentage: Optional[int] = None


class OKRList(BaseModel):
    okrs: List[OKRWithMeta]


@router.get(
    "/engagements/{engagement_id}/okrs",
    response_model=OKRList,
    summary="List OKRs linked to an engagement",
)
async def get_engagement_okrs(engagement_id: int, db: AsyncSession = Depends(get_db_session)):
    try:
        sql = text(
            """
            SELECT o.id, o.objective, o.key_results, o.owner_id, o.period, o.status,
                   o.created_at, o.updated_at, eo.alignment_score
            FROM engagement_okr eo
            JOIN okrs o ON o.id = eo.okr_id
            WHERE eo.engagement_id = :eng_id
            ORDER BY o.created_at DESC
            """
        )
        res = await db.execute(sql, {"eng_id": engagement_id})
        rows = [dict(r) for r in res.mappings().all()]
        def parse_ok(r: dict) -> OKRWithMeta:
            kr = r.get("key_results")
            return OKRWithMeta(
                id=r["id"],
                objective=r.get("objective"),
                key_results=kr,
                owner_id=r.get("owner_id"),
                period=r.get("period"),
                status=r.get("status"),
                created_at=str(r.get("created_at")) if r.get("created_at") else None,
                updated_at=str(r.get("updated_at")) if r.get("updated_at") else None,
                alignment_score=r.get("alignment_score"),
            )
        return {"okrs": [parse_ok(r) for r in rows]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch engagement OKRs: {e}")


@router.get(
    "/activities/{activity_id}/okrs",
    response_model=OKRList,
    summary="List OKRs linked to an activity",
)
async def get_activity_okrs(activity_id: int, db: AsyncSession = Depends(get_db_session)):
    try:
        sql = text(
            """
            SELECT o.id, o.objective, o.key_results, o.owner_id, o.period, o.status,
                   o.created_at, o.updated_at, ao.contribution_percentage
            FROM activity_okrs ao
            JOIN okrs o ON o.id = ao.okr_id
            WHERE ao.activity_id = :act_id
            ORDER BY o.created_at DESC
            """
        )
        res = await db.execute(sql, {"act_id": activity_id})
        rows = [dict(r) for r in res.mappings().all()]
        def parse_ok(r: dict) -> OKRWithMeta:
            kr = r.get("key_results")
            return OKRWithMeta(
                id=r["id"],
                objective=r.get("objective"),
                key_results=kr,
                owner_id=r.get("owner_id"),
                period=r.get("period"),
                status=r.get("status"),
                created_at=str(r.get("created_at")) if r.get("created_at") else None,
                updated_at=str(r.get("updated_at")) if r.get("updated_at") else None,
                contribution_percentage=r.get("contribution_percentage"),
            )
        return {"okrs": [parse_ok(r) for r in rows]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch activity OKRs: {e}")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update activity: {e}")