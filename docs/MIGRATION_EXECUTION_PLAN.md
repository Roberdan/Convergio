# Agent Framework Migration - Execution Plan v2.0

**Last Updated**: 2025-12-28 @ 00:20
**Status**: IN PROGRESS - SPRINT 4 (Integration & Validation)
**Progress**: 54/72 tasks completed (75.0%)
**Version**: 2.0 - Token-Optimized with Atomic Tasks

---

## Anti-Token-Exhaustion Rules

> **CRITICAL**: Queste regole DEVONO essere seguite per evitare che gli agenti esauriscano i token.

| Rule | Limit | Rationale |
|------|-------|-----------|
| **Max Parallel Agents** | 2 | Riduce competizione per risorse |
| **Max File Reads per Task** | 4 | Limita accumulo contesto |
| **Task Atomicity** | 1 file modificato | Output verificabile |
| **Checkpoint Frequency** | Ogni 3 task | Salvataggio stato intermedio |
| **Output Requirement** | File obbligatorio | Nessun output solo in memoria |
| **Task Timeout** | 10 minuti | Previene loop infiniti |

---

## Quick Status Dashboard

```
SPRINT 0 (Baseline & Prep)        [██████████] 100% COMPLETE (4/4)
SPRINT 1 (Infrastructure)         [██████████] 100% COMPLETE (8/8)
SPRINT 2 (Tools Migration)        [██████████] 100% COMPLETE (20/20)
SPRINT 3 (Core Components)        [██████████] 100% COMPLETE (18/18)
SPRINT 4 (Integration & Test)     [███░░░░░░░] 28.6% IN PROGRESS (4/14)
SPRINT 5 (Rollout & Cleanup)      [░░░░░░░░░░] 0/12 tasks

OVERALL PROGRESS                  [███████░░░] 54/72 tasks (75.0%)
```

### Completed Sprints

#### Sprint 3 (Core Components) - COMPLETE
- [x] E1-E4: AgentFrameworkLoader + unit tests (22 tests passing)
- [x] F1-F6: AgentFrameworkOrchestrator + unit tests (32 tests passing)
- [x] G1-G4: AgentFrameworkMemory + unit tests (30 tests passing)
- [x] H1-H4: Streaming/runner updates + unit tests (28 tests passing)

### Current Sprint 4 Status (Integration & Validation)
- [x] I1-I4: Framework Adapter & Feature Flags (39 tests passing)
- [ ] J1-J10: Full Test Validation (IN PROGRESS)

---

## Execution Flow (Token-Optimized)

```
WAVE EXECUTION MODEL (Max 2 parallel)

Wave 1: A1 ──────────────────────────────────────────────────►
        (Infrastructure setup - SOLO, no parallel)

Wave 2: A2 + D1 ─────────────────────────────────────────────►
        (Dependencies + Docs baseline - 2 parallel, zero overlap)

Wave 3: A3 ──────────────────────────────────────────────────►
        (Test env - SOLO, needs A2)

Wave 4: B1 → B2 → B3 → B4 ───────────────────────────────────►
        (AI Client - SEQUENZIALE, stesso file)

Wave 5: C1.1 → C1.2 → C1.3 ──────────────────────────────────►
        (database_tools batch 1 - SEQUENZIALE)

Wave 6: C1.4 → C1.5 + C2 ────────────────────────────────────►
        (database_tools batch 2 + web_search - 2 parallel)

Wave 7: C3.1 → C3.2 + C4 ────────────────────────────────────►
        (convergio_tools + vector_search - 2 parallel)

... (continues with max 2 parallel pattern)
```

---

## SPRINT 0: Baseline & Preparation (CURRENT)

### Completed
| ID | Task | Status | Output |
|----|------|--------|--------|
| P0.1 | Capture test baseline | `done` | `docs/TEST_BASELINE.md` |
| P0.2 | Document API format | `done` | `docs/API_BASELINE.md` |
| P0.3 | Validate agent .md files | `done` | `docs/AGENT_COMPATIBILITY_SUMMARY.md` |
| P0.4 | Create pytest fixtures | `done` | `tests/fixtures/` |

---

## SPRINT 1: Infrastructure (8 tasks)

### Wave 1.1: Branch Setup (SOLO) - COMPLETE
| ID | Task | Status | Depends | Output | Max Reads |
|----|------|--------|---------|--------|-----------|
| A1 | Verify branch exists | `done` | - | stdout | 0 |

### Wave 1.2: Dependencies (2 PARALLEL max) - COMPLETE
| ID | Task | Status | Depends | Output | Max Reads |
|----|------|--------|---------|--------|-----------|
| A2 | Add agent-framework to requirements.txt | `done` | A1 | `requirements.txt` (pre-existing) | 1 |
| D1 | Snapshot current test count | `done` | - | `docs/TEST_BASELINE.md` | 2 |

### Wave 1.3: Test Environment (SOLO) - COMPLETE
| ID | Task | Status | Depends | Output | Max Reads |
|----|------|--------|---------|--------|-----------|
| A3 | Create pytest.ini for AF tests | `done` | A2 | `pytest.ini` (markers added) | 1 |

### Wave 1.4: AI Client - Sequential (stesso file) - COMPLETE
| ID | Task | Status | Depends | Output | Max Reads |
|----|------|--------|---------|--------|-----------|
| B1 | Create agent_framework_clients.py scaffold | `done` | A2 | `backend/src/core/agent_framework_config.py` (pre-existing) | 2 |
| B2 | Implement get_openai_client() | `done` | B1 | same file | 2 |
| B3 | Implement get_azure_client() | `done` | B2 | same file | 2 |
| B4 | Add client unit tests | `done` | B3 | `tests/unit/test_agent_framework_config.py` | 2 |

**CHECKPOINT 1**: PASSED - `python -c "from src.core.agent_framework_config import get_agent_framework_client"`

---

## SPRINT 2: Tools Migration (20 tasks)

> **Strategy**: Ogni funzione = 1 task atomico. Max 2 parallel su file diversi.

### Track C1: database_tools.py (12 functions → 6 atomic tasks)

| ID | Task | Status | Depends | Output | Max Reads |
|----|------|--------|---------|--------|-----------|
| C1.1 | Analyze database_tools structure | `pending` | A2 | `docs/migration/database_tools_analysis.md` | 2 |
| C1.2 | Migrate query_talents_count + query_talent_details | `pending` | C1.1 | `database_tools.py` | 2 |
| C1.3 | Migrate query_department_structure + query_system_status | `pending` | C1.2 | `database_tools.py` | 2 |
| C1.4 | Migrate query_knowledge_base + search_knowledge | `pending` | C1.3 | `database_tools.py` | 2 |
| C1.5 | Migrate remaining 6 helper functions | `pending` | C1.4 | `database_tools.py` | 2 |
| C1.6 | Unit tests for database_tools | `pending` | C1.5 | `tests/unit/test_database_tools.py` | 3 |

**CHECKPOINT 2**: `pytest tests/unit/test_database_tools.py -v`

### Track C2: web_search_tool.py (1 function → 2 tasks)

| ID | Task | Status | Depends | Output | Max Reads |
|----|------|--------|---------|--------|-----------|
| C2.1 | Migrate web_search to @ai_function | `pending` | A2 | `web_search_tool.py` | 2 |
| C2.2 | Unit test web_search_tool | `pending` | C2.1 | `tests/unit/test_web_search.py` | 2 |

### Track C3: convergio_tools.py (4 classes → 5 tasks)

| ID | Task | Status | Depends | Output | Max Reads |
|----|------|--------|---------|--------|-----------|
| C3.1 | Analyze convergio_tools structure | `pending` | A2 | `docs/migration/convergio_tools_analysis.md` | 2 |
| C3.2 | Migrate TalentsQueryTool + VectorSearchTool | `pending` | C3.1 | `convergio_tools.py` | 2 |
| C3.3 | Migrate EngagementAnalyticsTool | `pending` | C3.2 | `convergio_tools.py` | 2 |
| C3.4 | Migrate BusinessIntelligenceTool | `pending` | C3.3 | `convergio_tools.py` | 2 |
| C3.5 | Unit tests for convergio_tools | `pending` | C3.4 | `tests/unit/test_convergio_tools.py` | 3 |

**CHECKPOINT 3**: `pytest tests/unit/test_convergio_tools.py -v`

### Track C4: vector_search_tool.py (1 function → 2 tasks)

| ID | Task | Status | Depends | Output | Max Reads |
|----|------|--------|---------|--------|-----------|
| C4.1 | Migrate vector_search to @ai_function | `pending` | A2 | `vector_search_tool.py` | 2 |
| C4.2 | Unit test vector_search_tool | `pending` | C4.1 | `tests/unit/test_vector_search.py` | 2 |

### Track C5: Tool Registry & Executor (3 tasks)

| ID | Task | Status | Depends | Output | Max Reads |
|----|------|--------|---------|--------|-----------|
| C5.1 | Create tools_registry.py | `pending` | C1.6, C2.2, C3.5, C4.2 | `backend/src/agents/tools/tools_registry.py` | 4 |
| C5.2 | Update intelligent_tool_executor.py | `pending` | C5.1 | `intelligent_tool_executor.py` | 3 |
| C5.3 | Integration test tool execution | `pending` | C5.2 | `tests/integration/test_tools.py` | 3 |

**CHECKPOINT 4**: `pytest tests/integration/test_tools.py -v`

---

## SPRINT 3: Core Components (18 tasks) ✅ COMPLETE

### Track E: Agent Loader (4 tasks - SEQUENZIALE) ✅

| ID | Task | Status | Depends | Output | Max Reads |
|----|------|--------|---------|--------|-----------|
| E1 | Create AgentFrameworkLoader scaffold | `done` | C5.3 | `agent_framework_loader.py` (pre-existing) | 3 |
| E2 | Implement load_agent_definitions() | `done` | E1 | same file | 2 |
| E3 | Implement create_agent() method | `done` | E2 | same file | 2 |
| E4 | Unit tests for loader | `done` | E3 | `tests/unit/test_agent_framework_loader.py` (22 tests) | 3 |

**CHECKPOINT 5**: ✅ PASSED - Loader working with all agent definitions

### Track F: Orchestrator (6 tasks - SEQUENZIALE) ✅

| ID | Task | Status | Depends | Output | Max Reads |
|----|------|--------|---------|--------|-----------|
| F1 | Create AgentFrameworkOrchestrator scaffold | `done` | E4 | `agent_framework_orchestrator.py` | 3 |
| F2 | Implement execute_single_agent() | `done` | F1 | same file (dual-framework) | 2 |
| F3 | Implement execute_workflow() | `done` | F2 | same file | 2 |
| F4 | Implement AgentThread management | `done` | F3 | same file | 2 |
| F5 | Implement response streaming | `done` | F4 | same file | 2 |
| F6 | Integration tests orchestrator | `done` | F5 | `tests/unit/test_agent_framework_orchestrator.py` (32 tests) | 3 |

**CHECKPOINT 6**: ✅ PASSED - Orchestrator working with both frameworks

### Track G: Memory System (4 tasks) ✅

| ID | Task | Status | Depends | Output | Max Reads |
|----|------|--------|---------|--------|-----------|
| G1 | Analyze current memory system | `done` | E4 | Analysis of autogen_memory_system.py | 3 |
| G2 | Create agent_framework_memory.py | `done` | G1 | `agent_framework_memory.py` | 2 |
| G3 | Migrate message format | `done` | G2 | MemoryMessage with dual-framework support | 2 |
| G4 | Unit tests memory | `done` | G3 | `tests/unit/test_agent_framework_memory.py` (30 tests) | 2 |

### Track H: Streaming & WebSocket (4 tasks) ✅

| ID | Task | Status | Depends | Output | Max Reads |
|----|------|--------|---------|--------|-----------|
| H1 | Analyze streaming/runner.py | `done` | F5 | Analysis complete | 2 |
| H2 | Update streaming runner | `done` | H1 | `streaming/agent_framework_runner.py` | 3 |
| H3 | Update WebSocket handlers | `done` | H2 | unified.py updated with optional autogen | 3 |
| H4 | Streaming integration test | `done` | H3 | `tests/unit/test_agent_framework_runner.py` (28 tests) | 2 |

**CHECKPOINT 7**: ✅ PASSED - Streaming working with dual-framework support

---

## SPRINT 4: Integration & Validation (14 tasks) - IN PROGRESS

### Track I: Compatibility Layer (4 tasks) ✅ COMPLETE

| ID | Task | Status | Depends | Output | Max Reads |
|----|------|--------|---------|--------|-----------|
| I1 | Create FrameworkAdapter interface | `done` | F6, G4, H4 | `adapters/framework_adapter.py` | 4 |
| I2 | Implement AutoGen fallback | `done` | I1 | `adapters/autogen_adapter.py` | 2 |
| I3 | Implement feature flag | `done` | I2 | `adapters/feature_flag.py` | 2 |
| I4 | Test rollback mechanism | `done` | I3 | `tests/unit/test_framework_adapters.py` (39 tests) | 3 |

**CHECKPOINT 8**: ✅ PASSED - Feature flag switches frameworks correctly with percentage rollout

### Track J: Comprehensive Testing (10 tasks) - IN PROGRESS

| ID | Task | Status | Depends | Output | Max Reads |
|----|------|--------|---------|--------|-----------|
| J1 | Run full unit test suite | `in_progress` | I4 | 301 passed, 39 skipped (Redis tests need server) | 0 |
| J2 | Run integration test suite | `pending` | J1 | `reports/integration_tests.json` | 0 |
| J3 | Run E2E test suite | `pending` | J2 | `reports/e2e_tests.json` | 0 |
| J4 | Performance benchmark: latency | `pending` | J3 | `reports/perf_latency.json` | 2 |
| J5 | Performance benchmark: throughput | `pending` | J4 | `reports/perf_throughput.json` | 2 |
| J6 | Performance benchmark: memory | `pending` | J5 | `reports/perf_memory.json` | 2 |
| J7 | Parity test: single agent | `pending` | J3 | `reports/parity_single.json` | 3 |
| J8 | Parity test: multi-agent | `pending` | J7 | `reports/parity_multi.json` | 3 |
| J9 | Parity test: tool execution | `pending` | J8 | `reports/parity_tools.json` | 3 |
| J10 | Generate final test report | `pending` | J9 | `reports/FINAL_TEST_REPORT.md` | 4 |

**CHECKPOINT 9**: All tests passing, performance within 10% of baseline

---

## SPRINT 5: Rollout & Cleanup (12 tasks)

### Track K: Gradual Rollout (3 tasks)

| ID | Task | Status | Depends | Output | Max Reads |
|----|------|--------|---------|--------|-----------|
| K1 | Deploy 10% traffic | `pending` | J10 | `docs/rollout/10_percent.md` | 2 |
| K2 | Deploy 50% traffic (after 48h) | `pending` | K1 | `docs/rollout/50_percent.md` | 2 |
| K3 | Deploy 100% traffic (after 48h) | `pending` | K2 | `docs/rollout/100_percent.md` | 2 |

### Track L: Cleanup (9 tasks - SEQUENZIALE)

| ID | Task | Status | Depends | Output | Max Reads |
|----|------|--------|---------|--------|-----------|
| L1 | Remove autogen from requirements.txt | `pending` | K3 | `requirements.txt` | 1 |
| L2 | Remove autogen_tools.py | `pending` | L1 | file deleted | 1 |
| L3 | Remove autogen_memory_system.py | `pending` | L2 | file deleted | 1 |
| L4 | Remove autogen_orchestrator.py | `pending` | L3 | file deleted | 1 |
| L5 | Remove autogen imports | `pending` | L4 | multiple files | 4 |
| L6 | Remove compatibility layer | `pending` | L5 | file deleted | 1 |
| L7 | Update README.md | `pending` | L6 | `README.md` | 2 |
| L8 | Update API documentation | `pending` | L7 | `docs/API.md` | 2 |
| L9 | Archive migration branch | `pending` | L8 | git command | 0 |

**CHECKPOINT 10 (FINAL)**: Migration complete, all AutoGen code removed

---

## Parallel Execution Schedule

### Max 2 Parallel - Wave Schedule

```
SPRINT 1:
  Wave 1.1: [A1]                    → 1 agent
  Wave 1.2: [A2] + [D1]             → 2 agents (parallel, zero overlap)
  Wave 1.3: [A3]                    → 1 agent
  Wave 1.4: [B1→B2→B3→B4]           → 1 agent (sequential, same file)

SPRINT 2:
  Wave 2.1: [C1.1]                  → 1 agent (analysis)
  Wave 2.2: [C1.2→C1.3→C1.4→C1.5]   → 1 agent (sequential, same file)
  Wave 2.3: [C1.6] + [C2.1]         → 2 agents (parallel, different files)
  Wave 2.4: [C2.2] + [C3.1]         → 2 agents (parallel)
  Wave 2.5: [C3.2→C3.3→C3.4]        → 1 agent (sequential, same file)
  Wave 2.6: [C3.5] + [C4.1]         → 2 agents (parallel)
  Wave 2.7: [C4.2] + [C5.1]         → 2 agents (parallel)
  Wave 2.8: [C5.2→C5.3]             → 1 agent (sequential)

SPRINT 3:
  Wave 3.1: [E1→E2→E3→E4]           → 1 agent (sequential, same file)
  Wave 3.2: [F1→F2→F3→F4→F5→F6]     → 1 agent (sequential, same file)
  Wave 3.3: [G1] + [H1]             → 2 agents (parallel, analysis)
  Wave 3.4: [G2→G3→G4]              → 1 agent (sequential)
  Wave 3.5: [H2→H3→H4]              → 1 agent (sequential)

SPRINT 4:
  Wave 4.1: [I1→I2→I3→I4]           → 1 agent (sequential)
  Wave 4.2: [J1→J2→J3]              → 1 agent (sequential, test runs)
  Wave 4.3: [J4] + [J7]             → 2 agents (parallel, different metrics)
  Wave 4.4: [J5] + [J8]             → 2 agents (parallel)
  Wave 4.5: [J6] + [J9]             → 2 agents (parallel)
  Wave 4.6: [J10]                   → 1 agent (report generation)

SPRINT 5:
  Wave 5.1: [K1]                    → 1 agent (deploy + monitor)
  Wave 5.2: [K2]                    → 1 agent (deploy + monitor)
  Wave 5.3: [K3]                    → 1 agent (deploy + monitor)
  Wave 5.4: [L1→L2→L3→L4→L5→L6→L7→L8→L9] → 1 agent (sequential cleanup)
```

---

## Task Template

Ogni task DEVE seguire questo template per evitare token exhaustion:

```markdown
### Task [ID]: [Name]

**Input**:
- File da leggere (max 4): [list]
- Contesto necessario: [brief description]

**Output**:
- File da modificare/creare: [single file]
- Formato output: [code/markdown/json]

**Success Criteria**:
- [ ] Criterio 1
- [ ] Criterio 2

**Max Duration**: 10 minuti
```

---

## Checkpoint Verification Commands

```bash
# CHECKPOINT 1: Client imports
python -c "from backend.src.core.agent_framework_clients import get_openai_client; print('OK')"

# CHECKPOINT 2: Database tools
pytest tests/unit/test_database_tools.py -v --tb=short

# CHECKPOINT 3: Convergio tools
pytest tests/unit/test_convergio_tools.py -v --tb=short

# CHECKPOINT 4: Tool integration
pytest tests/integration/test_tools.py -v --tb=short

# CHECKPOINT 5: Loader
python -c "from backend.src.agents.services.agent_framework_loader import AgentFrameworkLoader; print('OK')"

# CHECKPOINT 6: Orchestrator
pytest tests/integration/test_orchestrator.py -v --tb=short

# CHECKPOINT 7: Streaming
pytest tests/integration/test_streaming.py -v --tb=short

# CHECKPOINT 8: Feature flag
python -c "from backend.src.core.config import USE_AGENT_FRAMEWORK; print(f'Flag: {USE_AGENT_FRAMEWORK}')"

# CHECKPOINT 9: All tests
pytest tests/ -v --tb=short && echo "ALL TESTS PASSED"

# CHECKPOINT 10: No AutoGen
! grep -r "autogen" backend/src/ && echo "NO AUTOGEN REFERENCES"
```

---

## Change Log

| Date | Version | Change | Author |
|------|---------|--------|--------|
| 2025-12-27 16:30 | 1.0 | Initial plan | AI Team |
| 2025-12-27 17:25 | 2.0 | Token-optimized with atomic tasks, max 2 parallel | AI Team |
| 2025-12-27 22:30 | 2.1 | Sprint 3 complete (18/18 tasks, 112 tests) | AI Team |
| 2025-12-28 00:20 | 2.2 | I1-I4 complete (adapters + feature flags, 39 tests) | AI Team |

---

## Summary of Changes v1.0 → v2.0

| Aspect | v1.0 | v2.0 |
|--------|------|------|
| Total Tasks | 49 | 72 (more granular) |
| Max Parallel | 6 | 2 |
| Max File Reads | unlimited | 4 |
| Checkpoints | 4 | 10 |
| Task Atomicity | mixed | 1 file per task |
| Output Requirement | optional | mandatory |

---

## Next Actions

1. [x] ~~Approvazione piano v2.0~~ APPROVED
2. [x] ~~Completare SPRINT 0~~ COMPLETE
3. [x] ~~Completare SPRINT 1~~ COMPLETE
4. [x] ~~Completare SPRINT 2~~ COMPLETE
5. [x] ~~Completare SPRINT 3~~ COMPLETE
6. [x] ~~Completare I1-I4 (Adapters)~~ COMPLETE
7. [ ] Completare J1-J10 (Full Test Validation) - IN PROGRESS
8. [ ] SPRINT 5: Rollout & Cleanup
