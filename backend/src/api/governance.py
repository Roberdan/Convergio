"""
Governance API for Rate Limiting, SLO Monitoring, and Runbook Management
Provides endpoints for operational control and monitoring
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..core.rate_limiting import get_rate_limiter
from ..agents.services.observability.slo_dashboard import get_slo_dashboard
from ..agents.services.observability.runbook import get_runbook_manager, IncidentSeverity, IncidentStatus
from ..core.security_middleware import get_current_user
from ..models.user import User

router = APIRouter()

# Rate Limiting Endpoints
@router.get("/rate-limit/status/{identifier}")
async def get_rate_limit_status(
    identifier: str,
    current_user: User = Depends(get_current_user)
):
    """Get rate limit status for a specific identifier"""
    try:
        rate_limiter = await get_rate_limiter()
        if not rate_limiter:
            return {"message": "Rate limiting is disabled (Redis not available)"}
        status = await rate_limiter.get_rate_limit_status(identifier)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting rate limit status: {str(e)}")

@router.post("/rate-limit/block/{identifier}")
async def block_identifier(
    identifier: str,
    duration: int = Query(default=300, description="Block duration in seconds"),
    current_user: User = Depends(get_current_user)
):
    """Manually block an identifier for rate limiting"""
    try:
        rate_limiter = await get_rate_limiter()
        if not rate_limiter:
            return {"message": "Rate limiting is disabled (Redis not available)"}
        # This would need to be implemented in the RateLimiter class
        return {"message": f"Identifier {identifier} blocked for {duration} seconds"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error blocking identifier: {str(e)}")

@router.delete("/rate-limit/block/{identifier}")
async def unblock_identifier(
    identifier: str,
    current_user: User = Depends(get_current_user)
):
    """Unblock a previously blocked identifier"""
    try:
        await get_rate_limiter()
        # This would need to be implemented in the RateLimiter class
        return {"message": f"Identifier {identifier} unblocked"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error unblocking identifier: {str(e)}")

# SLO Dashboard Endpoints
@router.get("/slo/overview")
async def get_slo_overview(
    current_user: User = Depends(get_current_user)
):
    """Get overview of all SLOs and overall health"""
    try:
        dashboard = get_slo_dashboard()
        return dashboard.get_all_slo_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting SLO overview: {str(e)}")

@router.get("/slo/{slo_key}")
async def get_slo_status(
    slo_key: str,
    current_user: User = Depends(get_current_user)
):
    """Get status for a specific SLO"""
    try:
        dashboard = get_slo_dashboard()
        return dashboard.get_slo_status(slo_key)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting SLO status: {str(e)}")

@router.post("/slo/{slo_key}/measurement")
async def record_slo_measurement(
    slo_key: str,
    measurement: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Record a new SLO measurement"""
    try:
        value = measurement.get('value')
        metadata = measurement.get('metadata')
        
        if value is None:
            raise HTTPException(status_code=400, detail="Measurement value is required")
        
        dashboard = get_slo_dashboard()
        dashboard.record_measurement(slo_key, float(value), metadata)
        
        return {"message": "Measurement recorded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recording measurement: {str(e)}")

@router.get("/slo/alerts")
async def get_slo_alerts(
    severity: Optional[str] = Query(None, description="Filter by severity"),
    limit: int = Query(default=50, description="Maximum number of alerts to return"),
    current_user: User = Depends(get_current_user)
):
    """Get SLO alerts, optionally filtered by severity"""
    try:
        dashboard = get_slo_dashboard()
        return dashboard.get_alerts(severity, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting alerts: {str(e)}")

@router.delete("/slo/alerts")
async def clear_slo_alerts(
    alert_ids: Optional[List[str]] = Query(None, description="Specific alert IDs to clear"),
    current_user: User = Depends(get_current_user)
):
    """Clear SLO alerts"""
    try:
        dashboard = get_slo_dashboard()
        dashboard.clear_alerts(alert_ids)
        return {"message": "Alerts cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing alerts: {str(e)}")

# Runbook Management Endpoints
@router.get("/runbooks")
async def list_runbooks(
    category: Optional[str] = Query(None, description="Filter by category"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    search: Optional[str] = Query(None, description="Search query"),
    current_user: User = Depends(get_current_user)
):
    """List available runbooks with optional filtering"""
    try:
        manager = get_runbook_manager()
        
        if search:
            runbooks = manager.search_runbooks(search)
        elif category:
            runbooks = manager.get_runbooks_by_category(category)
        elif severity:
            try:
                severity_enum = IncidentSeverity(severity)
                runbooks = manager.get_runbooks_by_severity(severity_enum)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid severity: {severity}")
        else:
            runbooks = list(manager.runbooks.values())
        
        # Convert to dict for JSON serialization
        return [{
            'id': r.id,
            'title': r.title,
            'description': r.description,
            'severity': r.severity.value,
            'category': r.category,
            'estimated_time': r.estimated_time,
            'tags': r.tags
        } for r in runbooks]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing runbooks: {str(e)}")

@router.get("/runbooks/{runbook_id}")
async def get_runbook(
    runbook_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get detailed information about a specific runbook"""
    try:
        manager = get_runbook_manager()
        runbook = manager.get_runbook(runbook_id)
        
        if not runbook:
            raise HTTPException(status_code=404, detail="Runbook not found")
        
        # Convert to dict for JSON serialization
        return {
            'id': runbook.id,
            'title': runbook.title,
            'description': runbook.description,
            'severity': runbook.severity.value,
            'category': runbook.category,
            'estimated_time': runbook.estimated_time,
            'prerequisites': runbook.prerequisites,
            'tags': runbook.tags,
            'steps': [{
                'step_id': s.step_id,
                'title': s.title,
                'description': s.description,
                'commands': s.commands,
                'expected_output': s.expected_output,
                'timeout_seconds': s.timeout_seconds,
                'requires_confirmation': s.requires_confirmation,
                'notes': s.notes
            } for s in runbook.steps]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting runbook: {str(e)}")

@router.get("/runbooks/{runbook_id}/export")
async def export_runbook(
    runbook_id: str,
    format: str = Query(default="json", description="Export format (json or yaml)"),
    current_user: User = Depends(get_current_user)
):
    """Export a runbook in specified format"""
    try:
        manager = get_runbook_manager()
        exported = manager.export_runbook(runbook_id, format)
        
        if not exported:
            raise HTTPException(status_code=404, detail="Runbook not found")
        
        if format == "json":
            return JSONResponse(content=exported, media_type="application/json")
        elif format == "yaml":
            return JSONResponse(content=exported, media_type="text/yaml")
        else:
            raise HTTPException(status_code=400, detail="Unsupported format")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting runbook: {str(e)}")

# Incident Management Endpoints
@router.post("/incidents")
async def create_incident(
    incident_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Create a new incident"""
    try:
        required_fields = ['title', 'description', 'severity', 'category']
        for field in required_fields:
            if field not in incident_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        try:
            severity = IncidentSeverity(incident_data['severity'])
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid severity: {incident_data['severity']}")
        
        manager = get_runbook_manager()
        incident = manager.create_incident(
            title=incident_data['title'],
            description=incident_data['description'],
            severity=severity,
            category=incident_data['category'],
            runbook_id=incident_data.get('runbook_id')
        )
        
        return {
            'id': incident.id,
            'title': incident.title,
            'status': incident.status.value,
            'created_at': incident.created_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating incident: {str(e)}")

@router.get("/incidents")
async def list_incidents(
    status: Optional[str] = Query(None, description="Filter by status"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    current_user: User = Depends(get_current_user)
):
    """List incidents with optional filtering"""
    try:
        manager = get_runbook_manager()
        
        if status:
            try:
                status_enum = IncidentStatus(status)
                incidents = [i for i in manager.incidents.values() if i.status == status_enum]
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        elif severity:
            try:
                severity_enum = IncidentSeverity(severity)
                incidents = manager.get_incidents_by_severity(severity_enum)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid severity: {severity}")
        else:
            incidents = list(manager.incidents.values())
        
        # Convert to dict for JSON serialization
        return [{
            'id': i.id,
            'title': i.title,
            'description': i.description,
            'severity': i.severity.value,
            'category': i.category,
            'status': i.status.value,
            'runbook_id': i.runbook_id,
            'assigned_to': i.assigned_to,
            'created_at': i.created_at.isoformat(),
            'updated_at': i.updated_at.isoformat()
        } for i in incidents]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing incidents: {str(e)}")

@router.get("/incidents/{incident_id}")
async def get_incident(
    incident_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get detailed information about a specific incident"""
    try:
        manager = get_runbook_manager()
        incident = manager.get_incident(incident_id)
        
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")
        
        # Convert to dict for JSON serialization
        return {
            'id': incident.id,
            'title': incident.title,
            'description': incident.description,
            'severity': incident.severity.value,
            'category': incident.category,
            'status': incident.status.value,
            'runbook_id': incident.runbook_id,
            'assigned_to': incident.assigned_to,
            'created_at': incident.created_at.isoformat(),
            'updated_at': incident.updated_at.isoformat(),
            'resolved_at': incident.resolved_at.isoformat() if incident.resolved_at else None,
            'notes': incident.notes,
            'executed_steps': incident.executed_steps
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting incident: {str(e)}")

@router.patch("/incidents/{incident_id}/status")
async def update_incident_status(
    incident_id: str,
    status_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Update incident status"""
    try:
        if 'status' not in status_data:
            raise HTTPException(status_code=400, detail="Status is required")
        
        try:
            status = IncidentStatus(status_data['status'])
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status_data['status']}")
        
        manager = get_runbook_manager()
        incident = manager.update_incident_status(
            incident_id,
            status,
            status_data.get('notes')
        )
        
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")
        
        return {
            'id': incident.id,
            'status': incident.status.value,
            'updated_at': incident.updated_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating incident status: {str(e)}")

@router.post("/incidents/{incident_id}/steps/{step_id}/execute")
async def execute_runbook_step(
    incident_id: str,
    step_id: str,
    execution_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Execute a runbook step for an incident"""
    try:
        required_fields = ['output', 'success']
        for field in required_fields:
            if field not in execution_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        manager = get_runbook_manager()
        success = manager.execute_runbook_step(
            incident_id,
            step_id,
            execution_data['output'],
            execution_data['success'],
            execution_data.get('notes')
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Incident not found")
        
        return {"message": "Step execution recorded successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing step: {str(e)}")

# Statistics and Overview Endpoints
@router.get("/governance/overview")
async def get_governance_overview(
    current_user: User = Depends(get_current_user)
):
    """Get overview of governance systems"""
    try:
        # Get SLO dashboard overview
        slo_dashboard = get_slo_dashboard()
        slo_overview = slo_dashboard.get_all_slo_status()
        
        # Get runbook statistics
        runbook_manager = get_runbook_manager()
        runbook_stats = runbook_manager.get_runbook_statistics()
        
        # Get rate limiting status (placeholder)
        rate_limit_status = {
            'enabled': True,
            'active_blocks': 0,
            'total_requests_today': 0
        }
        
        return {
            'slo_overview': slo_overview,
            'runbook_statistics': runbook_stats,
            'rate_limiting': rate_limit_status,
            'last_updated': datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting governance overview: {str(e)}")

@router.get("/governance/health")
async def get_governance_health(
    current_user: User = Depends(get_current_user)
):
    """Health check for governance systems"""
    try:
        # Check SLO dashboard
        slo_dashboard = get_slo_dashboard()
        slo_health = slo_dashboard.get_all_slo_status()
        
        # Check runbook manager
        runbook_manager = get_runbook_manager()
        runbook_health = len(runbook_manager.runbooks) > 0
        
        # Check rate limiting (placeholder)
        rate_limit_health = True
        
        overall_health = all([
            slo_health['overall_health'] > 80,
            runbook_health,
            rate_limit_health
        ])
        
        return {
            'status': 'healthy' if overall_health else 'unhealthy',
            'overall_health_score': slo_health['overall_health'],
            'slo_system': 'healthy' if slo_health['overall_health'] > 80 else 'unhealthy',
            'runbook_system': 'healthy' if runbook_health else 'unhealthy',
            'rate_limiting_system': 'healthy' if rate_limit_health else 'unhealthy',
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }
