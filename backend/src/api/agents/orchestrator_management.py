"""
Orchestrator Management API Endpoints
Provides endpoints to list, select, and monitor orchestrators
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import structlog

from ..agents.orchestrator import get_agent_orchestrator

logger = structlog.get_logger()

router = APIRouter(tags=["Orchestrator Management"])


class OrchestratorSelection(BaseModel):
    """Request model for orchestrator selection"""
    orchestrator_name: str
    set_as_default: bool = False


class OrchestratorInfo(BaseModel):
    """Information about an orchestrator"""
    name: str
    status: str
    health: bool
    circuit_breaker_state: Optional[str] = None
    capabilities: List[str] = []
    metrics: Optional[Dict[str, Any]] = None


@router.get("/orchestrators", response_model=List[OrchestratorInfo])
async def list_orchestrators():
    """
    List all available orchestrators with their status
    """
    try:
        orchestrator = await get_agent_orchestrator()
        
        if not hasattr(orchestrator, 'orchestrator') or not hasattr(orchestrator.orchestrator, 'orchestrators'):
            return []
        
        unified = orchestrator.orchestrator
        available = []
        
        for name, orch in unified.orchestrators.items():
            # Get health status
            try:
                health = await orch.health() if hasattr(orch, 'health') else True
            except Exception:
                health = False
            
            # Get circuit breaker status
            cb_state = None
            if hasattr(orch, 'get_circuit_status'):
                cb_status = orch.get_circuit_status()
                cb_state = cb_status.get('state')
            
            # Determine capabilities based on orchestrator type
            capabilities = []
            if 'groupchat' in name.lower():
                capabilities = ['chat', 'tools', 'rag', 'perplexity']
            elif 'streaming' in name.lower():
                capabilities = ['websocket', 'stream', 'real_time']
            elif 'graphflow' in name.lower():
                capabilities = ['workflow', 'dag', 'pipeline']
            elif 'swarm' in name.lower():
                capabilities = ['multi_agent', 'coordination', 'parallel']
            
            available.append(OrchestratorInfo(
                name=name,
                status='healthy' if health else 'unhealthy',
                health=health,
                circuit_breaker_state=cb_state,
                capabilities=capabilities
            ))
        
        return available
        
    except Exception as e:
        logger.error(f"Failed to list orchestrators: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/orchestrators/select")
async def select_orchestrator(selection: OrchestratorSelection):
    """
    Select a specific orchestrator for use
    """
    try:
        orchestrator = await get_agent_orchestrator()
        
        if not hasattr(orchestrator, 'orchestrator'):
            raise HTTPException(status_code=400, detail="Unified orchestrator not available")
        
        unified = orchestrator.orchestrator
        
        # Check if orchestrator exists
        if selection.orchestrator_name not in unified.orchestrators:
            raise HTTPException(
                status_code=404, 
                detail=f"Orchestrator '{selection.orchestrator_name}' not found"
            )
        
        # Update fallback chain to prioritize selected orchestrator
        current_chain = unified.fallback_chain.copy()
        if selection.orchestrator_name in current_chain:
            current_chain.remove(selection.orchestrator_name)
        
        unified.set_fallback_chain([selection.orchestrator_name] + current_chain)
        
        # If set as default, update registry
        if selection.set_as_default and hasattr(orchestrator, 'registry'):
            orchestrator.registry.set_default(selection.orchestrator_name)
        
        return {
            "status": "success",
            "selected": selection.orchestrator_name,
            "fallback_chain": unified.fallback_chain
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to select orchestrator: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orchestrators/health")
async def get_orchestrator_health():
    """
    Get health status of all orchestrators
    """
    try:
        orchestrator = await get_agent_orchestrator()
        
        if not hasattr(orchestrator, 'orchestrator'):
            return {"status": "unavailable"}
        
        unified = orchestrator.orchestrator
        
        # Get health monitor status if available
        if hasattr(unified, 'health_monitor'):
            health_status = unified.health_monitor.get_health_status()
        else:
            health_status = {"orchestrators": {}, "summary": {}}
        
        # Get circuit breaker status for each orchestrator
        circuit_breakers = {}
        for name, orch in unified.orchestrators.items():
            if hasattr(orch, 'get_circuit_status'):
                circuit_breakers[name] = orch.get_circuit_status()
        
        return {
            "health_monitor": health_status,
            "circuit_breakers": circuit_breakers,
            "available_orchestrators": unified._get_available_orchestrators() if hasattr(unified, '_get_available_orchestrators') else []
        }
        
    except Exception as e:
        logger.error(f"Failed to get health status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orchestrators/metrics")
async def get_orchestrator_metrics():
    """
    Get usage metrics for all orchestrators
    """
    try:
        orchestrator = await get_agent_orchestrator()
        
        if not hasattr(orchestrator, 'orchestrator'):
            return {"metrics": {}}
        
        unified = orchestrator.orchestrator
        
        if hasattr(unified, 'get_metrics'):
            return unified.get_metrics()
        else:
            return {"metrics": {}}
        
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/orchestrators/reset-circuit-breaker/{orchestrator_name}")
async def reset_circuit_breaker(orchestrator_name: str):
    """
    Manually reset circuit breaker for a specific orchestrator
    """
    try:
        orchestrator = await get_agent_orchestrator()
        
        if not hasattr(orchestrator, 'orchestrator'):
            raise HTTPException(status_code=400, detail="Unified orchestrator not available")
        
        unified = orchestrator.orchestrator
        
        if orchestrator_name not in unified.orchestrators:
            raise HTTPException(
                status_code=404, 
                detail=f"Orchestrator '{orchestrator_name}' not found"
            )
        
        orch = unified.orchestrators[orchestrator_name]
        
        if hasattr(orch, 'circuit_breaker'):
            orch.circuit_breaker._reset_circuit_breaker()
            return {"status": "success", "message": f"Circuit breaker reset for {orchestrator_name}"}
        else:
            return {"status": "not_applicable", "message": f"No circuit breaker for {orchestrator_name}"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reset circuit breaker: {e}")
        raise HTTPException(status_code=500, detail=str(e))