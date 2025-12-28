"""
Telemetry API - Fornisce eventi per-turn per il frontend operational UX
Include speaker, tools, fonti, costi, razionali per ogni turn della conversazione
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import structlog

from ..agents.services.observability.telemetry import get_telemetry

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1/telemetry", tags=["telemetry"])


@router.get("/events")
async def get_telemetry_events(
    conversation_id: Optional[str] = Query(None, description="Filter by conversation ID"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    start_time: Optional[datetime] = Query(None, description="Start time for filtering"),
    end_time: Optional[datetime] = Query(None, description="End time for filtering"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of events to return")
) -> Dict[str, Any]:
    """
    Recupera eventi di telemetria per il frontend operational UX
    
    Returns:
        Dict con eventi e metadata per timeline per-turn
    """
    try:
        telemetry = get_telemetry()
        
        # Filtri di base
        filters = {}
        if conversation_id:
            filters["conversation_id"] = conversation_id
        if user_id:
            filters["user_id"] = user_id
        if event_type:
            filters["event_type"] = event_type
        if start_time:
            filters["start_time"] = start_time
        if end_time:
            filters["end_time"] = end_time
        
        # Recupera eventi dalla telemetria
        events = await telemetry.get_events(
            filters=filters,
            limit=limit,
            include_metadata=True
        )
        
        # Formatta eventi per il frontend
        formatted_events = []
        for event in events:
            formatted_event = {
                "id": event.get("id"),
                "timestamp": event.get("timestamp"),
                "event_type": event.get("event_type"),
                "conversation_id": event.get("conversation_id"),
                "user_id": event.get("user_id"),
                "agent_name": event.get("agent_name"),
                "turn_number": event.get("turn_number"),
                "data": event.get("data", {}),
                "metadata": event.get("metadata", {})
            }
            
            # Aggiungi dettagli specifici per tipo di evento
            if event.get("event_type") == "decision_made":
                formatted_event["decision"] = {
                    "sources": event.get("data", {}).get("sources", []),
                    "tools": event.get("data", {}).get("tools", []),
                    "rationale": event.get("data", {}).get("rationale", ""),
                    "confidence": event.get("data", {}).get("confidence", 0.0)
                }
            elif event.get("event_type") == "tool_invoked":
                formatted_event["tool"] = {
                    "name": event.get("data", {}).get("tool_name", ""),
                    "input": event.get("data", {}).get("input", {}),
                    "output": event.get("data", {}).get("output", {}),
                    "execution_time": event.get("data", {}).get("execution_time", 0.0)
                }
            elif event.get("event_type") == "budget_event":
                formatted_event["budget"] = {
                    "current_cost": event.get("data", {}).get("current_cost", 0.0),
                    "budget_limit": event.get("data", {}).get("budget_limit", 0.0),
                    "tokens_used": event.get("data", {}).get("tokens_used", 0),
                    "remaining_budget": event.get("data", {}).get("remaining_budget", 0.0)
                }
            elif event.get("event_type") == "rag_injected":
                formatted_event["rag"] = {
                    "context_items": event.get("data", {}).get("context_items", 0),
                    "hit_rate": event.get("data", {}).get("hit_rate", 0.0),
                    "latency": event.get("data", {}).get("latency", 0.0)
                }
            elif event.get("event_type", "").startswith("conflict_"):
                formatted_event["conflict"] = {
                    "type": event.get("event_type"),
                    "description": event.get("data", {}).get("description", ""),
                    "involved_agents": event.get("data", {}).get("involved_agents", []),
                    "resolution": event.get("data", {}).get("resolution", "")
                }
            
            formatted_events.append(formatted_event)
        
        # Calcola statistiche aggregate
        stats = {
            "total_events": len(formatted_events),
            "event_types": {},
            "conversations": {},
            "agents": {}
        }
        
        for event in formatted_events:
            # Conta eventi per tipo
            event_type = event.get("event_type", "unknown")
            stats["event_types"][event_type] = stats["event_types"].get(event_type, 0) + 1
            
            # Conta eventi per conversazione
            conv_id = event.get("conversation_id", "unknown")
            if conv_id not in stats["conversations"]:
                stats["conversations"][conv_id] = {
                    "total_events": 0,
                    "turns": set(),
                    "agents": set()
                }
            stats["conversations"][conv_id]["total_events"] += 1
            if event.get("turn_number"):
                stats["conversations"][conv_id]["turns"].add(event["turn_number"])
            if event.get("agent_name"):
                stats["conversations"][conv_id]["agents"].add(event["agent_name"])
            
            # Conta eventi per agente
            agent_name = event.get("agent_name", "unknown")
            stats["agents"][agent_name] = stats["agents"].get(agent_name, 0) + 1
        
        # Converti set in liste per JSON serialization
        for conv_id in stats["conversations"]:
            stats["conversations"][conv_id]["turns"] = list(stats["conversations"][conv_id]["turns"])
            stats["conversations"][conv_id]["agents"] = list(stats["conversations"][conv_id]["agents"])
        
        return {
            "success": True,
            "data": {
                "events": formatted_events,
                "stats": stats,
                "filters_applied": filters,
                "total_returned": len(formatted_events)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to retrieve telemetry events", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve telemetry events: {str(e)}")


@router.get("/conversation/{conversation_id}/timeline")
async def get_conversation_timeline(
    conversation_id: str
) -> Dict[str, Any]:
    """
    Recupera timeline completa per una conversazione specifica
    
    Returns:
        Dict con timeline per-turn per la conversazione
    """
    try:
        telemetry = get_telemetry()
        
        # Recupera tutti gli eventi per la conversazione
        events = await telemetry.get_events(
            filters={"conversation_id": conversation_id},
            limit=1000,  # Limite alto per conversazioni lunghe
            include_metadata=True
        )
        
        # Organizza eventi per turn
        timeline = {}
        for event in events:
            turn_number = event.get("turn_number", 0)
            if turn_number not in timeline:
                timeline[turn_number] = {
                    "turn_number": turn_number,
                    "timestamp": event.get("timestamp"),
                    "events": [],
                    "agents_involved": set(),
                    "total_cost": 0.0,
                    "total_tokens": 0
                }
            
            # Aggiungi evento al turn
            timeline[turn_number]["events"].append({
                "event_type": event.get("event_type"),
                "agent_name": event.get("agent_name"),
                "data": event.get("data", {}),
                "timestamp": event.get("timestamp")
            })
            
            # Aggiorna statistiche del turn
            if event.get("agent_name"):
                timeline[turn_number]["agents_involved"].add(event["agent_name"])
            
            if event.get("event_type") == "budget_event":
                timeline[turn_number]["total_cost"] += event.get("data", {}).get("current_cost", 0.0)
                timeline[turn_number]["total_tokens"] += event.get("data", {}).get("tokens_used", 0)
        
        # Converti set in liste e ordina per turn number
        timeline_list = []
        for turn_number in sorted(timeline.keys()):
            turn_data = timeline[turn_number]
            turn_data["agents_involved"] = list(turn_data["agents_involved"])
            timeline_list.append(turn_data)
        
        # Calcola statistiche aggregate della conversazione
        total_cost = sum(turn["total_cost"] for turn in timeline_list)
        total_tokens = sum(turn["total_tokens"] for turn in timeline_list)
        total_turns = len(timeline_list)
        all_agents = set()
        for turn in timeline_list:
            all_agents.update(turn["agents_involved"])
        
        return {
            "success": True,
            "data": {
                "conversation_id": conversation_id,
                "timeline": timeline_list,
                "summary": {
                    "total_turns": total_turns,
                    "total_cost": total_cost,
                    "total_tokens": total_tokens,
                    "agents_involved": list(all_agents),
                    "start_time": timeline_list[0]["timestamp"] if timeline_list else None,
                    "end_time": timeline_list[-1]["timestamp"] if timeline_list else None
                }
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to retrieve conversation timeline", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve conversation timeline: {str(e)}")


@router.get("/stats/summary")
async def get_telemetry_summary(
    days: int = Query(7, ge=1, le=30, description="Number of days to summarize")
) -> Dict[str, Any]:
    """
    Recupera statistiche riassuntive della telemetria
    
    Returns:
        Dict con statistiche aggregate per il periodo specificato
    """
    try:
        telemetry = get_telemetry()
        
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)
        
        # Recupera eventi per il periodo
        events = await telemetry.get_events(
            filters={"start_time": start_time, "end_time": end_time},
            limit=10000,
            include_metadata=True
        )
        
        # Calcola statistiche aggregate
        stats = {
            "period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "days": days
            },
            "total_events": len(events),
            "event_types": {},
            "conversations": {},
            "agents": {},
            "costs": {
                "total": 0.0,
                "average_per_conversation": 0.0,
                "by_agent": {}
            },
            "performance": {
                "average_turn_time": 0.0,
                "total_tokens": 0,
                "rag_hit_rate": 0.0
            }
        }
        
        # Processa eventi per statistiche
        conversation_costs = {}
        turn_times = []
        rag_hits = 0
        rag_total = 0
        
        for event in events:
            # Conta eventi per tipo
            event_type = event.get("event_type", "unknown")
            stats["event_types"][event_type] = stats["event_types"].get(event_type, 0) + 1
            
            # Conta eventi per conversazione
            conv_id = event.get("conversation_id", "unknown")
            if conv_id not in stats["conversations"]:
                stats["conversations"][conv_id] = 0
            stats["conversations"][conv_id] += 1
            
            # Conta eventi per agente
            agent_name = event.get("agent_name", "unknown")
            if agent_name not in stats["agents"]:
                stats["agents"][agent_name] = 0
            stats["agents"][agent_name] += 1
            
            # Calcola costi
            if event.get("event_type") == "budget_event":
                cost = event.get("data", {}).get("current_cost", 0.0)
                stats["costs"]["total"] += cost
                
                if conv_id not in conversation_costs:
                    conversation_costs[conv_id] = 0.0
                conversation_costs[conv_id] += cost
                
                # Costi per agente
                if agent_name not in stats["costs"]["by_agent"]:
                    stats["costs"]["by_agent"][agent_name] = 0.0
                stats["costs"]["by_agent"][agent_name] += cost
            
            # Calcola performance
            if event.get("event_type") == "tool_invoked":
                execution_time = event.get("data", {}).get("execution_time", 0.0)
                if execution_time > 0:
                    turn_times.append(execution_time)
            
            if event.get("event_type") == "rag_injected":
                rag_total += 1
                if event.get("data", {}).get("hit_rate", 0.0) > 0:
                    rag_hits += 1
            
            # Conta token
            if event.get("event_type") == "budget_event":
                tokens = event.get("data", {}).get("tokens_used", 0)
                stats["performance"]["total_tokens"] += tokens
        
        # Calcola medie
        if conversation_costs:
            stats["costs"]["average_per_conversation"] = sum(conversation_costs.values()) / len(conversation_costs)
        
        if turn_times:
            stats["performance"]["average_turn_time"] = sum(turn_times) / len(turn_times)
        
        if rag_total > 0:
            stats["performance"]["rag_hit_rate"] = (rag_hits / rag_total) * 100
        
        return {
            "success": True,
            "data": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to retrieve telemetry summary", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve telemetry summary: {str(e)}")


@router.get("/health")
async def telemetry_health() -> Dict[str, Any]:
    """Health check per l'API di telemetria"""
    try:
        telemetry = get_telemetry()
        status = await telemetry.get_status()
        
        return {
            "success": True,
            "status": "healthy",
            "telemetry_status": status,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error("Telemetry health check failed", error=str(e))
        return {
            "success": False,
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
