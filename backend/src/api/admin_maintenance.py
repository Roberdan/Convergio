"""Admin maintenance endpoints protected by admin authorization."""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.admin import require_admin
from ..core.database import get_db_session
from ..core.db_maintenance import get_db_maintenance

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])


@router.get("/db-stats")
async def get_database_statistics(
    db: AsyncSession = Depends(get_db_session),
    _: dict[str, Any] = Depends(require_admin),
) -> dict[str, Any]:
    try:
        db_maintenance = get_db_maintenance()
        table_stats = await db_maintenance.get_table_statistics(db)
        return {"status": "success", "tables": table_stats, "total_tables": len(table_stats)}
    except Exception as exc:
        logger.error("Failed to get database stats", error=str(exc))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get("/slow-queries")
async def get_slow_queries(
    threshold_ms: int = 100,
    db: AsyncSession = Depends(get_db_session),
    _: dict[str, Any] = Depends(require_admin),
) -> dict[str, Any]:
    try:
        db_maintenance = get_db_maintenance()
        slow_queries = await db_maintenance.analyze_slow_queries(db, threshold_ms)
        return {"status": "success", "threshold_ms": threshold_ms, "queries": slow_queries, "total": len(slow_queries)}
    except Exception as exc:
        logger.error("Failed to get slow queries", error=str(exc))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.post("/vacuum")
async def run_vacuum_analyze(
    tables: list[str] | None = None,
    db: AsyncSession = Depends(get_db_session),
    _: dict[str, Any] = Depends(require_admin),
) -> dict[str, Any]:
    try:
        db_maintenance = get_db_maintenance()
        results = await db_maintenance.vacuum_analyze_tables(db, tables)
        return {"status": "success", "results": results}
    except Exception as exc:
        logger.error("Failed to run VACUUM ANALYZE", error=str(exc))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get("/index-suggestions")
async def get_index_optimization_suggestions(
    db: AsyncSession = Depends(get_db_session),
    _: dict[str, Any] = Depends(require_admin),
) -> dict[str, Any]:
    try:
        db_maintenance = get_db_maintenance()
        suggestions = await db_maintenance.optimize_indexes(db)
        return {"status": "success", "suggestions": suggestions}
    except Exception as exc:
        logger.error("Failed to get index suggestions", error=str(exc))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get("/maintenance-status")
async def get_maintenance_status(_: dict[str, Any] = Depends(require_admin)) -> dict[str, Any]:
    try:
        db_maintenance = get_db_maintenance()
        return {"status": "success", "maintenance": db_maintenance.get_maintenance_status()}
    except Exception as exc:
        logger.error("Failed to get maintenance status", error=str(exc))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.post("/maintenance/schedule")
async def update_maintenance_schedule(
    vacuum_hour: int = 3,
    vacuum_minute: int = 0,
    _: dict[str, Any] = Depends(require_admin),
) -> dict[str, Any]:
    try:
        if not (0 <= vacuum_hour <= 23):
            raise ValueError("vacuum_hour must be between 0 and 23")
        if not (0 <= vacuum_minute <= 59):
            raise ValueError("vacuum_minute must be between 0 and 59")
        db_maintenance = get_db_maintenance()
        if db_maintenance.is_running:
            db_maintenance.stop_maintenance()
        db_maintenance.schedule_maintenance(vacuum_hour, vacuum_minute)
        return {"status": "success", "message": f"Maintenance scheduled for {vacuum_hour:02d}:{vacuum_minute:02d} UTC daily"}
    except Exception as exc:
        logger.error("Failed to update maintenance schedule", error=str(exc))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
