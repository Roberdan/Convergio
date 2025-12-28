"""
Telemetry API Service - Servizio per fornire dati di telemetria al frontend
Implementa i metodi richiesti dall'API di telemetria
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import structlog

logger = structlog.get_logger()


@dataclass
class TelemetryEvent:
    """Evento di telemetria per il frontend"""
    id: str
    timestamp: datetime
    event_type: str
    conversation_id: str
    user_id: str
    agent_name: Optional[str] = None
    turn_number: Optional[int] = None
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class TelemetryAPIService:
    """Servizio per fornire dati di telemetria al frontend"""
    
    def __init__(self):
        self.events: List[TelemetryEvent] = []
        self.conversations: Dict[str, Dict[str, Any]] = {}
        self.agents: Dict[str, Dict[str, Any]] = {}
        
        # Inizializza con alcuni eventi di esempio per testing
        self._initialize_sample_data()
    
    def _initialize_sample_data(self):
        """Inizializza con dati di esempio per testing"""
        base_time = datetime.utcnow()
        
        # Eventi di esempio per una conversazione
        sample_events = [
            TelemetryEvent(
                id="evt_001",
                timestamp=base_time - timedelta(minutes=5),
                event_type="conversation.start",
                conversation_id="conv_001",
                user_id="user_001",
                agent_name="Ali",
                turn_number=1,
                data={"message": "Hello! How can I help you today?"},
                metadata={"session_id": "sess_001"}
            ),
            TelemetryEvent(
                id="evt_002",
                timestamp=base_time - timedelta(minutes=4),
                event_type="decision_made",
                conversation_id="conv_001",
                user_id="user_001",
                agent_name="Ali",
                turn_number=1,
                data={
                    "sources": ["user_input", "agent_knowledge"],
                    "tools": ["web_search", "memory_access"],
                    "rationale": "User asked for help, need to understand context",
                    "confidence": 0.85
                },
                metadata={"decision_id": "dec_001"}
            ),
            TelemetryEvent(
                id="evt_003",
                timestamp=base_time - timedelta(minutes=3),
                event_type="tool_invoked",
                conversation_id="conv_001",
                user_id="user_001",
                agent_name="Ali",
                turn_number=1,
                data={
                    "tool_name": "web_search",
                    "input": {"query": "current project status"},
                    "output": {"results": ["Project X is 75% complete"]},
                    "execution_time": 1.2
                },
                metadata={"tool_id": "tool_001"}
            ),
            TelemetryEvent(
                id="evt_004",
                timestamp=base_time - timedelta(minutes=2),
                event_type="budget_event",
                conversation_id="conv_001",
                user_id="user_001",
                agent_name="Ali",
                turn_number=1,
                data={
                    "current_cost": 0.15,
                    "budget_limit": 10.0,
                    "tokens_used": 150,
                    "remaining_budget": 9.85
                },
                metadata={"budget_id": "budget_001"}
            ),
            TelemetryEvent(
                id="evt_005",
                timestamp=base_time - timedelta(minutes=1),
                event_type="rag_injected",
                conversation_id="conv_001",
                user_id="user_001",
                agent_name="Ali",
                turn_number=1,
                data={
                    "context_items": 3,
                    "hit_rate": 0.75,
                    "latency": 0.3
                },
                metadata={"rag_id": "rag_001"}
            ),
            TelemetryEvent(
                id="evt_006",
                timestamp=base_time,
                event_type="conversation.end",
                conversation_id="conv_001",
                user_id="user_001",
                agent_name="Ali",
                turn_number=1,
                data={"final_message": "I've provided the information you requested."},
                metadata={"session_id": "sess_001"}
            )
        ]
        
        self.events.extend(sample_events)
        
        # Aggiorna statistiche
        self._update_stats()
    
    def _update_stats(self):
        """Aggiorna le statistiche aggregate"""
        # Reset stats
        self.conversations = {}
        self.agents = {}
        
        for event in self.events:
            # Aggiorna statistiche per conversazione
            conv_id = event.conversation_id
            if conv_id not in self.conversations:
                self.conversations[conv_id] = {
                    "total_events": 0,
                    "turns": set(),
                    "agents": set(),
                    "start_time": event.timestamp,
                    "end_time": event.timestamp,
                    "total_cost": 0.0,
                    "total_tokens": 0
                }
            
            self.conversations[conv_id]["total_events"] += 1
            if event.turn_number:
                self.conversations[conv_id]["turns"].add(event.turn_number)
            if event.agent_name:
                self.conversations[conv_id]["agents"].add(event.agent_name)
            
            if event.timestamp < self.conversations[conv_id]["start_time"]:
                self.conversations[conv_id]["start_time"] = event.timestamp
            if event.timestamp > self.conversations[conv_id]["end_time"]:
                self.conversations[conv_id]["end_time"] = event.timestamp
            
            # Aggiorna costi e token
            if event.event_type == "budget_event":
                cost = event.data.get("current_cost", 0.0)
                tokens = event.data.get("tokens_used", 0)
                self.conversations[conv_id]["total_cost"] += cost
                self.conversations[conv_id]["total_tokens"] += tokens
            
            # Aggiorna statistiche per agente
            if event.agent_name:
                agent_name = event.agent_name
                if agent_name not in self.agents:
                    self.agents[agent_name] = {
                        "total_events": 0,
                        "conversations": set(),
                        "total_cost": 0.0,
                        "total_tokens": 0
                    }
                
                self.agents[agent_name]["total_events"] += 1
                self.agents[agent_name]["conversations"].add(conv_id)
                
                if event.event_type == "budget_event":
                    cost = event.data.get("current_cost", 0.0)
                    tokens = event.data.get("tokens_used", 0)
                    self.agents[agent_name]["total_cost"] += cost
                    self.agents[agent_name]["total_tokens"] += tokens
        
        # Converti set in liste per JSON serialization
        for conv_id in self.conversations:
            self.conversations[conv_id]["turns"] = list(self.conversations[conv_id]["turns"])
            self.conversations[conv_id]["agents"] = list(self.conversations[conv_id]["agents"])
        
        for agent_name in self.agents:
            self.agents[agent_name]["conversations"] = list(self.agents[agent_name]["conversations"])
    
    async def get_events(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        include_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Recupera eventi di telemetria con filtri opzionali
        
        Args:
            filters: Filtri da applicare
            limit: Numero massimo di eventi da restituire
            include_metadata: Se includere i metadata
            
        Returns:
            Lista di eventi formattati
        """
        try:
            # Applica filtri
            filtered_events = self.events.copy()
            
            if filters:
                if "conversation_id" in filters:
                    filtered_events = [
                        e for e in filtered_events 
                        if e.conversation_id == filters["conversation_id"]
                    ]
                
                if "user_id" in filters:
                    filtered_events = [
                        e for e in filtered_events 
                        if e.user_id == filters["user_id"]
                    ]
                
                if "event_type" in filters:
                    filtered_events = [
                        e for e in filtered_events 
                        if e.event_type == filters["event_type"]
                    ]
                
                if "start_time" in filters:
                    filtered_events = [
                        e for e in filtered_events 
                        if e.timestamp >= filters["start_time"]
                    ]
                
                if "end_time" in filters:
                    filtered_events = [
                        e for e in filtered_events 
                        if e.timestamp <= filters["end_time"]
                    ]
            
            # Ordina per timestamp (più recenti prima)
            filtered_events.sort(key=lambda x: x.timestamp, reverse=True)
            
            # Applica limite
            if limit > 0:
                filtered_events = filtered_events[:limit]
            
            # Formatta per il frontend
            formatted_events = []
            for event in filtered_events:
                formatted_event = {
                    "id": event.id,
                    "timestamp": event.timestamp.isoformat(),
                    "event_type": event.event_type,
                    "conversation_id": event.conversation_id,
                    "user_id": event.user_id,
                    "agent_name": event.agent_name,
                    "turn_number": event.turn_number,
                    "data": event.data
                }
                
                if include_metadata:
                    formatted_event["metadata"] = event.metadata
                
                formatted_events.append(formatted_event)
            
            return formatted_events
            
        except Exception as e:
            logger.error(f"Error retrieving telemetry events: {str(e)}")
            return []
    
    async def get_status(self) -> Dict[str, Any]:
        """Restituisce lo stato del servizio di telemetria"""
        try:
            return {
                "status": "healthy",
                "total_events": len(self.events),
                "total_conversations": len(self.conversations),
                "total_agents": len(self.agents),
                "last_updated": datetime.utcnow().isoformat(),
                "sample_data": len(self.events) > 0
            }
        except Exception as e:
            logger.error(f"Error getting telemetry status: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def add_event(self, event: TelemetryEvent):
        """Aggiunge un nuovo evento di telemetria"""
        try:
            self.events.append(event)
            self._update_stats()
            logger.info(f"Added telemetry event: {event.event_type} for {event.conversation_id}")
        except Exception as e:
            logger.error(f"Error adding telemetry event: {str(e)}")


# Istanza globale del servizio
_telemetry_api_service: Optional[TelemetryAPIService] = None


def get_telemetry_api_service() -> TelemetryAPIService:
    """Restituisce l'istanza globale del servizio di telemetria API"""
    global _telemetry_api_service
    if _telemetry_api_service is None:
        _telemetry_api_service = TelemetryAPIService()
    return _telemetry_api_service


# Alias per compatibilità con l'API esistente
def get_telemetry():
    """Alias per compatibilità con l'API esistente"""
    return get_telemetry_api_service()
