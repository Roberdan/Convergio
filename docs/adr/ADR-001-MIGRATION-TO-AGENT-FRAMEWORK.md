# ADR-001: Migration from AutoGen to Microsoft Agent Framework

**Data**: 2025-12-27
**Status**: Proposed
**Deciders**: Roberto, AI Team

## Context

Convergio utilizza attualmente AutoGen v0.7.3 per l'orchestrazione dei 48 agenti AI. Microsoft ha annunciato (Ottobre 2025) che AutoGen entra in maintenance mode con il nuovo **Microsoft Agent Framework** come successore ufficiale.

**GA prevista**: Q1 2026

## Decision Drivers

- AutoGen in maintenance mode (solo bug fix e security patches)
- Microsoft Agent Framework offre: checkpointing, time-travel, DevUI, middleware
- Pattern più enterprise-ready (data-flow vs event-driven)
- Supporto multi-linguaggio nativo (Python + .NET)
- Integrazione Azure nativa migliorata

---

## Analisi Attuale: AutoGen in Convergio

### Statistiche
- **47+ file** con importazioni AutoGen
- **48 agenti** specializzati (caricati dinamicamente da `.md`)
- **5 tools** principali (database, web search, vector search, etc.)
- **RoundRobinGroupChat** per orchestrazione multi-agente
- **Memory System** custom con Redis + embeddings

### Classi AutoGen Utilizzate

| Modulo | Classi |
|--------|--------|
| `autogen_agentchat.agents` | `AssistantAgent` |
| `autogen_agentchat.teams` | `RoundRobinGroupChat`, `SelectorGroupChat` |
| `autogen_agentchat.messages` | `TextMessage`, `ToolCallMessage`, `HandoffMessage` |
| `autogen_agentchat.conditions` | `MaxMessageTermination`, `TextMentionTermination` |
| `autogen_core.tools` | `BaseTool`, `FunctionTool` |
| `autogen_ext.models.openai` | `OpenAIChatCompletionClient` |

### File Critici da Migrare

```
PRIORITÀ ALTA (Core):
├── backend/src/core/ai_clients.py                    # LLM Client
├── backend/src/agents/services/agent_loader.py       # Agent Factory
├── backend/src/agents/orchestrators/unified.py       # Main Orchestrator
└── backend/src/agents/services/groupchat/agent_factory.py  # Agent Creation

PRIORITÀ MEDIA (GroupChat):
├── backend/src/agents/services/groupchat/setup.py
├── backend/src/agents/services/groupchat/runner.py
├── backend/src/agents/services/groupchat/intelligent_router.py
├── backend/src/agents/services/groupchat/selection_policy.py
├── backend/src/agents/services/groupchat/turn_by_turn_selector.py
└── backend/src/agents/services/groupchat/multi_agent_fix.py

PRIORITÀ MEDIA (Tools):
├── backend/src/agents/tools/database_tools.py
├── backend/src/agents/tools/web_search_tool.py
├── backend/src/agents/tools/vector_search_tool.py
└── backend/src/agents/tools/convergio_tools.py

PRIORITÀ BASSA (Support):
├── backend/src/agents/memory/autogen_memory_system.py
├── backend/src/agents/compatibility/*.py
├── backend/src/agents/services/streaming/runner.py
└── tests/
```

---

## Mapping AutoGen → Agent Framework

### 1. AI Client

```python
# PRIMA (AutoGen)
from autogen_ext.models.openai import OpenAIChatCompletionClient
client = OpenAIChatCompletionClient(model="gpt-4o", api_key=API_KEY)

# DOPO (Agent Framework)
from agent_framework.openai import OpenAIChatClient
# oppure
from agent_framework.azure import AzureOpenAIChatClient
client = OpenAIChatClient(model_id="gpt-4o")  # Legge API key da env
```

### 2. Agent Creation

```python
# PRIMA (AutoGen)
from autogen_agentchat.agents import AssistantAgent
agent = AssistantAgent(
    name="ali_chief_of_staff",
    model_client=client,
    system_message="You are the Chief of Staff...",
    tools=[tool1, tool2]
)

# DOPO (Agent Framework)
from agent_framework import ChatAgent
agent = ChatAgent(
    name="ali_chief_of_staff",
    chat_client=client,
    instructions="You are the Chief of Staff...",
    tools=[tool1, tool2]  # Con @ai_function decorator
)
```

### 3. Tool Definition

```python
# PRIMA (AutoGen)
from autogen_core.tools import FunctionTool

def query_talents(query: str) -> str:
    """Query talent database."""
    return execute_query(query)

tool = FunctionTool(func=query_talents, description="Query talents")

# DOPO (Agent Framework)
from agent_framework import ai_function

@ai_function
def query_talents(query: str) -> str:
    """Query talent database."""
    return execute_query(query)

# Uso diretto: tools=[query_talents]
```

### 4. Multi-Agent Orchestration

```python
# PRIMA (AutoGen) - Event-driven
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import MaxMessageTermination

team = RoundRobinGroupChat(
    participants=[agent1, agent2, agent3],
    termination_condition=MaxMessageTermination(max_messages=10)
)
result = await team.run(task=TextMessage(content="Analyze this...", source="user"))

# DOPO (Agent Framework) - Data-flow Workflow
from agent_framework import WorkflowBuilder, SequentialBuilder

# Opzione 1: Sequential (Round-Robin equivalent)
workflow = SequentialBuilder().participants([agent1, agent2, agent3]).build()

# Opzione 2: Custom Workflow
workflow = (WorkflowBuilder()
    .add_edge(agent1, agent2)
    .add_edge(agent2, agent3)
    .set_start_executor(agent1)
    .build())

# Esecuzione con streaming
async for event in workflow.run_stream("Analyze this..."):
    if isinstance(event, WorkflowOutputEvent):
        result = event.data
```

### 5. Message Types

```python
# PRIMA (AutoGen)
from autogen_agentchat.messages import TextMessage, ToolCallMessage

message = TextMessage(content="Hello", source="user")

# DOPO (Agent Framework)
# I messaggi sono gestiti internamente, non serve crearli manualmente
result = await agent.run("Hello")
print(result.text)  # Accesso semplificato
```

### 6. State Management (Nuovo!)

```python
# DOPO (Agent Framework) - AgentThread per conversazioni multi-turn
thread = agent.get_new_thread()

# Prima richiesta
r1 = await agent.run("What's 2+2?", thread=thread)

# Continua nella stessa conversazione
r2 = await agent.run("Multiply by 10", thread=thread)  # Ricorda che era 4
```

---

## Piano di Migrazione Dettagliato

### Fase 0: Preparazione (1 settimana)

- [ ] Creare branch `feature/agent-framework-migration`
- [ ] Aggiungere dipendenze Agent Framework a `requirements.txt`:
  ```
  agent-framework>=0.1.0
  agent-framework-core>=1.0.0b251016
  agent-framework-azure-ai>=0.1.0
  ```
- [ ] Setup ambiente di test isolato
- [ ] Documentare stato attuale con snapshot dei test

### Fase 1: AI Client Layer (3-4 giorni)

**File**: `backend/src/core/ai_clients.py`

```python
# Nuovo modulo: agent_framework_clients.py

from agent_framework.openai import OpenAIChatClient
from agent_framework.azure import AzureOpenAIChatClient
from azure.identity import AzureCliCredential

def get_agent_framework_client(provider: str = "azure"):
    """Factory per Agent Framework client."""
    if provider == "azure":
        return AzureOpenAIChatClient(
            credential=AzureCliCredential(),
            model_id=settings.AZURE_OPENAI_MODEL
        )
    elif provider == "openai":
        return OpenAIChatClient(model_id=settings.OPENAI_MODEL)
```

**Compatibilità**: Mantenere `get_autogen_client()` come fallback durante la migrazione.

### Fase 2: Tool Migration (3-4 giorni)

**File Target**: `backend/src/agents/tools/*.py`

```python
# PRIMA
from autogen_core.tools import FunctionTool

def query_talents_count(department: str = None) -> str:
    ...

talent_count_tool = FunctionTool(
    func=query_talents_count,
    description="Count talents..."
)

# DOPO
from agent_framework import ai_function

@ai_function
def query_talents_count(department: str = None) -> str:
    """Count talents by department.

    Args:
        department: Optional department filter

    Returns:
        JSON with talent count
    """
    ...

# Nessun wrapper necessario, usa direttamente la funzione
```

**Checklist Tools**:
- [ ] `database_tools.py` → 5 funzioni da convertire
- [ ] `web_search_tool.py` → 1 classe → funzione
- [ ] `vector_search_tool.py` → 1 classe → funzione
- [ ] `convergio_tools.py` → N funzioni da convertire
- [ ] `intelligent_tool_executor.py` → Refactor per nuovo pattern

### Fase 3: Agent Loader Refactor (5-7 giorni)

**File**: `backend/src/agents/services/agent_loader.py`

```python
# Nuovo approccio
from agent_framework import ChatAgent

class AgentFrameworkLoader:
    """Carica agenti da file .md e crea ChatAgent instances."""

    def create_agents(
        self,
        chat_client: OpenAIChatClient,
        tools_registry: Dict[str, Callable]
    ) -> Dict[str, ChatAgent]:
        agents = {}

        for agent_id, metadata in self.agent_metadata.items():
            # Seleziona tools per questo agente
            agent_tools = self._select_tools_for_agent(
                agent_id,
                tools_registry
            )

            # Crea ChatAgent
            agent = ChatAgent(
                name=agent_id,
                chat_client=chat_client,
                instructions=self._build_instructions(metadata),
                tools=agent_tools
            )
            agents[agent_id] = agent

        return agents
```

**Note**: I 48 file `.md` degli agenti rimangono invariati - cambia solo il wrapper.

### Fase 4: Orchestrator Migration (7-10 giorni)

**File**: `backend/src/agents/orchestrators/unified.py`

Questa è la fase più complessa. Il pattern cambia da event-driven a data-flow.

```python
from agent_framework import WorkflowBuilder, SequentialBuilder, WorkflowOutputEvent
from agent_framework import ChatAgent, AgentThread

class AgentFrameworkOrchestrator:
    """Orchestratore basato su Microsoft Agent Framework."""

    def __init__(self):
        self.agents: Dict[str, ChatAgent] = {}
        self.threads: Dict[str, AgentThread] = {}  # Per stato conversazione
        self.router: IntelligentAgentRouter = None

    async def orchestrate(
        self,
        message: str,
        session_id: str,
        multi_agent: bool = False
    ) -> OrchestratorResponse:
        # Ottieni o crea thread per questa sessione
        thread = self._get_or_create_thread(session_id)

        if not multi_agent:
            return await self._single_agent_execution(message, thread)
        else:
            return await self._workflow_execution(message, thread)

    async def _single_agent_execution(
        self,
        message: str,
        thread: AgentThread
    ) -> OrchestratorResponse:
        # Routing intelligente
        best_agent = self.router.select_best_agent(message, self.agents)

        # Esecuzione
        result = await best_agent.run(message, thread=thread)

        return OrchestratorResponse(
            content=result.text,
            agent_used=best_agent.name,
            tokens_used=result.usage.total_tokens if result.usage else 0
        )

    async def _workflow_execution(
        self,
        message: str,
        thread: AgentThread
    ) -> OrchestratorResponse:
        # Seleziona agenti rilevanti
        relevant_agents = self.router.select_relevant_agents(
            message,
            self.agents,
            max_agents=5
        )

        # Costruisci workflow
        workflow = SequentialBuilder().participants(relevant_agents).build()

        # Esegui con streaming
        final_output = None
        agents_used = []

        async for event in workflow.run_stream(message):
            if isinstance(event, WorkflowOutputEvent):
                final_output = event.data
            # Track agents used
            if hasattr(event, 'agent_name'):
                agents_used.append(event.agent_name)

        return OrchestratorResponse(
            content=final_output,
            agents_used=agents_used
        )
```

### Fase 5: Memory System Adaptation (3-4 giorni)

**File**: `backend/src/agents/memory/autogen_memory_system.py`

```python
# Rename a: agent_framework_memory_system.py

class AgentFrameworkMemorySystem:
    """Memory system compatibile con Agent Framework."""

    async def store_message(
        self,
        session_id: str,
        role: str,  # "user" | "assistant"
        content: str,
        agent_name: Optional[str] = None
    ):
        # Logica esistente rimane, cambia solo il formato input
        memory_entry = {
            "session_id": session_id,
            "role": role,
            "content": content,
            "agent": agent_name,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self._store_to_redis(memory_entry)
        await self._update_embeddings(content)
```

### Fase 6: Streaming & API Layer (2-3 giorni)

**File**: `backend/src/agents/services/streaming/runner.py`

```python
async def stream_agent_response(
    orchestrator: AgentFrameworkOrchestrator,
    message: str,
    session_id: str,
    websocket: WebSocket
):
    """Streaming con Agent Framework."""
    thread = orchestrator.get_thread(session_id)
    agent = orchestrator.get_best_agent(message)

    # Streaming nativo
    async for chunk in agent.run_stream(message, thread=thread):
        if chunk.text:
            await websocket.send_json({
                "type": "chunk",
                "content": chunk.text,
                "agent": agent.name
            })

    await websocket.send_json({"type": "complete"})
```

### Fase 7: Compatibility Layer (2 giorni)

Manteniamo un layer di compatibilità per rollback:

```python
# backend/src/agents/compatibility/framework_adapter.py

class FrameworkAdapter:
    """Adapter per switch tra AutoGen e Agent Framework."""

    def __init__(self, use_agent_framework: bool = True):
        self.use_agent_framework = use_agent_framework

    def get_orchestrator(self):
        if self.use_agent_framework:
            return AgentFrameworkOrchestrator()
        else:
            return UnifiedOrchestrator()  # Legacy AutoGen

    def create_agent(self, metadata, client, tools):
        if self.use_agent_framework:
            return ChatAgent(
                name=metadata.name,
                chat_client=client,
                instructions=metadata.persona,
                tools=tools
            )
        else:
            return AssistantAgent(
                name=metadata.name,
                model_client=client,
                system_message=metadata.persona,
                tools=[FunctionTool(t) for t in tools]
            )
```

### Fase 8: Testing & Validation (5-7 giorni)

- [ ] Unit tests per ogni componente migrato
- [ ] Integration tests end-to-end
- [ ] Performance benchmarking (latency, throughput)
- [ ] Memory usage comparison
- [ ] Cost comparison (token usage)

```python
# tests/integration/test_agent_framework_migration.py

class TestAgentFrameworkMigration:
    """Verifica parità funzionale tra AutoGen e Agent Framework."""

    async def test_single_agent_parity(self):
        """Output equivalente per singolo agente."""
        autogen_result = await autogen_orchestrator.orchestrate(TEST_QUERY)
        af_result = await af_orchestrator.orchestrate(TEST_QUERY)

        # Verifica similarità semantica (non esatta)
        assert semantic_similarity(
            autogen_result.content,
            af_result.content
        ) > 0.85

    async def test_multi_agent_workflow(self):
        """Multi-agent produce risultati comparabili."""
        ...
```

### Fase 9: Gradual Rollout (2 settimane)

1. **Settimana 1**: Feature flag per 10% del traffico
2. **Settimana 2**: 50% del traffico
3. **Fine settimana 2**: 100% se nessun issue

```python
# Feature flag
AGENT_FRAMEWORK_ENABLED = os.getenv("USE_AGENT_FRAMEWORK", "false") == "true"
AGENT_FRAMEWORK_PERCENTAGE = int(os.getenv("AF_ROLLOUT_PERCENTAGE", "0"))
```

### Fase 10: Cleanup & Deprecation (1 settimana)

- [ ] Rimuovere dipendenze AutoGen da `requirements.txt`
- [ ] Rimuovere codice legacy
- [ ] Aggiornare documentazione
- [ ] Archiviare compatibility layer

---

## Nuove Funzionalità Abilitate

### 1. Checkpointing (Crash Recovery)

```python
from agent_framework import FileCheckpointStorage

checkpoint_storage = FileCheckpointStorage(storage_path="./checkpoints")
workflow = (WorkflowBuilder()
    .participants([agent1, agent2])
    .with_checkpointing(checkpoint_storage=checkpoint_storage)
    .build())

# Se il sistema crasha, riprende da ultimo checkpoint
async for event in workflow.run_stream(checkpoint_id=last_checkpoint_id):
    ...
```

### 2. Human-in-the-Loop

```python
from agent_framework import RequestInfoEvent

async for event in workflow.run_stream("Complex task"):
    if isinstance(event, RequestInfoEvent):
        # Richiedi input umano
        human_input = await get_human_approval(event.data)
        pending_responses = {event.request_id: human_input}
        # Riprendi workflow
        async for resumed_event in workflow.send_responses_streaming(pending_responses):
            ...
```

### 3. Middleware per Logging/Security

```python
async def security_middleware(context: AgentRunContext, next):
    """Validazione sicurezza pre-esecuzione."""
    if not await security_guardian.validate(context.input):
        raise SecurityViolation("Input rejected")
    await next(context)

async def logging_middleware(context: AgentRunContext, next):
    """Logging strutturato."""
    logger.info(f"Agent {context.agent.name} starting", extra={
        "input": context.input[:100],
        "session": context.session_id
    })
    await next(context)
    logger.info(f"Agent {context.agent.name} completed")

agent = ChatAgent(
    name="secure_agent",
    chat_client=client,
    middleware=[security_middleware, logging_middleware]
)
```

### 4. DevUI per Debugging

Agent Framework include una DevUI per:
- Visualizzazione workflow in tempo reale
- Tracce di esecuzione
- Log delle chiamate tool
- Debug interattivo

---

## Risk Assessment

### Rischi ALTI

| Rischio | Mitigazione |
|---------|-------------|
| Breaking changes in API | Compatibility layer + feature flags |
| Performance regression | Benchmark prima/dopo, rollback automatico |
| Perdita di funzionalità | Test di parità funzionale |

### Rischi MEDI

| Rischio | Mitigazione |
|---------|-------------|
| Learning curve team | Documentazione interna + pair programming |
| Bug in nuovo framework | Monitoraggio intensivo, rollback rapido |
| Tempi di migrazione | Buffer 30% per imprevisti |

### Rischi BASSI

| Rischio | Mitigazione |
|---------|-------------|
| Costi Azure aumentati | Monitoring costi real-time |
| Incompatibilità future | Seguire roadmap Microsoft |

---

## Timeline Stimata

| Fase | Durata | Dipendenze |
|------|--------|------------|
| Fase 0: Preparazione | 1 settimana | - |
| Fase 1: AI Client | 3-4 giorni | Fase 0 |
| Fase 2: Tools | 3-4 giorni | Fase 1 |
| Fase 3: Agent Loader | 5-7 giorni | Fase 2 |
| Fase 4: Orchestrator | 7-10 giorni | Fase 3 |
| Fase 5: Memory | 3-4 giorni | Fase 4 |
| Fase 6: Streaming | 2-3 giorni | Fase 4 |
| Fase 7: Compatibility | 2 giorni | Fase 6 |
| Fase 8: Testing | 5-7 giorni | Fase 7 |
| Fase 9: Rollout | 2 settimane | Fase 8 |
| Fase 10: Cleanup | 1 settimana | Fase 9 |

**Totale stimato**: 8-10 settimane

---

## Decision

**Opzione Raccomandata**: Procedere con la migrazione seguendo il piano in 10 fasi.

**Rationale**:
1. AutoGen non riceverà nuove feature
2. Agent Framework è il futuro dell'ecosistema Microsoft
3. Nuove funzionalità (checkpointing, HITL) sono preziose
4. Il compatibility layer riduce il rischio

---

## Execution Tracking

**Live tracking files**:
- [`MIGRATION_EXECUTION_PLAN.md`](../MIGRATION_EXECUTION_PLAN.md) - Detailed task breakdown with parallel tracks
- [`MIGRATION_STATUS.json`](../MIGRATION_STATUS.json) - Machine-readable status for automation

---

## References

- [Microsoft Agent Framework GitHub](https://github.com/microsoft/agent-framework)
- [Migration Guide from AutoGen](https://learn.microsoft.com/en-us/agent-framework/migration-guide/from-autogen/)
- [Agent Framework Overview](https://learn.microsoft.com/en-us/agent-framework/overview/agent-framework-overview)
- [Multi-Agent Solutions Blog](https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/empowering-multi-agent-solutions-with-microsoft-agent-framework---code-migration/4468094)
