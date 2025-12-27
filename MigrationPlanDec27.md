# Migration Plan - December 27, 2025

## Microsoft Agent Framework Migration

**Branch**: `feature/agent-framework-migration`
**Last Commit**: `46e4382` - feat: Complete Microsoft Agent Framework migration (86% progress)
**Status**: IN PROGRESS (86.1% complete)

---

## Executive Summary

Migration from AutoGen to Microsoft Agent Framework. The core migration is complete with all agents, tools, orchestrators, and memory systems now supporting the new framework. Remaining work includes performance benchmarks, parity testing, and cleanup of legacy AutoGen code.

---

## Completed Tasks

### Sprint 0: Baseline & Preparation (DONE)
| Task | Description | Output |
|------|-------------|--------|
| P0.1 | Capture test baseline | `docs/TEST_BASELINE.md` |
| P0.2 | Document API format | `docs/API_BASELINE.md` |
| P0.3 | Validate agent .md files | `docs/AGENT_COMPATIBILITY_SUMMARY.md` |
| P0.4 | Create pytest fixtures | `tests/fixtures/` |

### Sprint 1: Infrastructure (DONE)
| Task | Description | Status |
|------|-------------|--------|
| A1 | Verify branch exists | Done |
| A2 | Add agent-framework to requirements.txt | Done |
| A3 | Create pytest.ini for AF tests | Done |
| B1-B4 | Client scaffolding and implementation | Done |

### Sprint 2: Tools Migration (DONE)
| Task | Description | Output |
|------|-------------|--------|
| C1.1-C1.6 | Database tools migration | `tests/backend/unit/test_database_tools.py` |
| C2.1-C2.2 | Web search migration | `tests/backend/unit/test_agent_framework_tools.py` |
| C3.1-C3.5 | Convergio tools migration | Covered in test_agent_framework_tools.py |
| C4.1-C4.2 | Vector search migration | Covered in test_agent_framework_tools.py |
| C5.1-C5.3 | Tools registry | `backend/src/agents/tools/tools_registry.py` |

### Sprint 3: Core Components (DONE)
| Task | Description | Output |
|------|-------------|--------|
| E1-E4 | AgentFrameworkLoader | `tests/backend/unit/test_agent_framework_loader.py` |
| F1-F6 | AgentFrameworkOrchestrator | `backend/src/agents/services/agent_framework_orchestrator.py` |
| G1-G4 | Memory system | `backend/src/agents/memory/agent_framework_memory.py` |
| H1-H4 | Streaming runner | `backend/src/agents/services/streaming/agent_framework_runner.py` |

### Sprint 4: Integration & Validation (PARTIAL)
| Task | Description | Status |
|------|-------------|--------|
| I1-I4 | Framework adapters | Done - 39 tests |
| J1 | Unit test suite | Done - 445+ passed |
| J2 | Integration test suite | Done |
| J3 | E2E test suite | Done |

---

## Bug Fixes Applied (Dec 27)

### 1. SQLAlchemy Reserved Attribute
**File**: `backend/src/models/tenant.py`
```python
# BEFORE (line 330, 366):
metadata = Column(JSON, default=dict)

# AFTER:
extra_data = Column('metadata', JSON, default=dict)
```

### 2. Non-existent Enum Value
**File**: `backend/src/models/tenant.py`
```python
# BEFORE (line 391, 415):
plan: SubscriptionPlan = SubscriptionPlan.TRIAL

# AFTER:
plan: SubscriptionPlan = SubscriptionPlan.FREE
```

### 3. Missing Tuple Import
**File**: `backend/src/models/tenant.py`
```python
# BEFORE (line 7):
from typing import Optional, List, Dict, Any

# AFTER:
from typing import Optional, List, Dict, Any, Tuple
```

### 4. Relative Imports for Package Compatibility
**Files**: All model files + `database_tools.py`
```python
# BEFORE:
from src.core.database import Base
from core.database import get_db_session

# AFTER:
from ..core.database import Base
from ...core.database import get_db_session
```

### 5. Missing GraphFlowOrchestrator Attributes
**File**: `backend/src/agents/services/unified_orchestrator_adapter.py`
```python
# ADDED to __init__:
self.executions: Dict[str, Any] = {}
self.workflows: Dict[str, Any] = {}

# ADDED methods:
async def get_workflow_status(self, execution_id: str)
async def cancel_workflow(self, execution_id: str)
```

### 6. Pytest Marker Missing
**File**: `pytest.ini`
```ini
# ADDED:
agent_framework: Microsoft Agent Framework tests
```

### 7. Test Import Errors
**File**: `tests/e2e/test_cost_tracking_simple.py`
```python
# BEFORE:
from core.database import get_async_session

# AFTER:
from src.core.database import get_async_session
```

---

## Infrastructure Setup (Dec 27)

### pgvector Extension
Installed in Apple Container:
```bash
container exec postgres sh -c "apk add --no-cache git make gcc musl-dev"
container exec postgres sh -c "cd /tmp && git clone --branch v0.7.4 https://github.com/pgvector/pgvector.git && cd pgvector && make"
container exec postgres sh -c "cp /tmp/pgvector/vector.so /usr/local/lib/postgresql/"
```

### Cost Tracking Tables
Created via SQL migration:
- `cost_tracking`
- `cost_sessions`
- `daily_cost_summary`
- `provider_pricing`
- `cost_alerts`

### Test Data
Inserted 5 test talents:
- Baccio Rossi (Engineering)
- Marco Bianchi (DevOps)
- Sara Verdi (Design)
- Paolo Neri (Quality Assurance)
- Elena Russo (Legal)

---

## Current System Status

### Backend
- **Status**: Running on port 9000
- **Health**: Healthy
- **Version**: 1.0.209

### Database
- **Status**: PostgreSQL running in Apple Container
- **Tables**: 20+ tables including cost tracking
- **pgvector**: Installed and working

### Redis
- **Status**: Running in Apple Container
- **Port**: 6379

### Frontend
- **Status**: Running on port 4000
- **Proxy**: Configured to backend:9000
- **Issues**: `TalentsOverview` component exists in dashboard, no dedicated page

### Tests
- **Collected**: 447 tests
- **Backend**: 445+ passed
- **Skipped**: ~3 (infrastructure-dependent)

---

## Remaining Tasks

### Sprint 4: Integration & Validation
| Task | Description | Priority |
|------|-------------|----------|
| J4 | Performance benchmark: latency | Medium |
| J5 | Performance benchmark: throughput | Medium |
| J6 | Performance benchmark: memory | Medium |
| J7 | Parity test: single agent | High |
| J8 | Parity test: multi-agent | High |
| J9 | Parity test: tool execution | High |
| J10 | Generate final test report | High |

### Sprint 5: Rollout & Cleanup
| Task | Description | Priority |
|------|-------------|----------|
| K1 | Deploy 10% traffic | Low |
| K2 | Deploy 50% traffic | Low |
| K3 | Deploy 100% traffic | Low |
| L1 | Remove autogen from requirements.txt | Medium |
| L2 | Remove autogen_tools.py | Medium |
| L3 | Remove autogen_memory_system.py | Medium |
| L4 | Remove autogen_orchestrator.py | Medium |
| L5 | Remove autogen imports | Medium |
| L6 | Remove compatibility layer | Low |
| L7 | Update README.md | Low |
| L8 | Update API documentation | Low |
| L9 | Archive migration branch | Low |

### Frontend Improvements
| Task | Description | Priority |
|------|-------------|----------|
| FE1 | Add dedicated Talents page | Medium |
| FE2 | Fix svelte-check warnings (333 errors, 520 warnings) | Low |
| FE3 | Verify all new Agent Framework features exposed | Medium |

---

## API Endpoints Verified

### Working
- `GET /api/v1/health` - Backend health
- `GET /api/v1/talents` - List talents (5 returned)
- `POST /api/v1/agents/ask` - Ali intelligence queries
- `GET /api/v1/workflows/catalog` - Workflow catalog
- `GET /api/v1/workflows/executions/recent` - Recent executions
- `GET /api/v1/costs/providers` - Cost providers

### Agent Database Queries
Ali successfully queries database:
```json
{
  "query": "quanti talent ci sono nel sistema?",
  "response": "5 talents totali, 5 attivi, 0 admin"
}
```

---

## Files Changed (Commit 46e4382)

**87 files changed**, +13,986 insertions, -449 deletions

### New Files (36)
- `backend/src/agents/adapters/` (5 files)
- `backend/src/agents/memory/agent_framework_memory.py`
- `backend/src/agents/services/agent_framework_orchestrator.py`
- `backend/src/agents/services/streaming/` (2 files)
- `backend/src/agents/tools/tools_registry.py`
- `docs/` (10 documentation files)
- `tests/backend/unit/` (10 new test files)
- `tests/fixtures/` (3 files)

### Modified Files (51)
- All model files (relative imports)
- All orchestrator files (Agent Framework support)
- All tool files (@ai_function decorators)
- All groupchat files (optional autogen)
- Configuration files (pytest.ini, etc.)

---

## Commands Reference

### Start Backend
```bash
cd backend && python -m uvicorn src.main:app --host 0.0.0.0 --port 9000 --reload
```

### Run Tests
```bash
python -m pytest tests/backend tests/e2e --tb=short -v
```

### Check Database
```bash
container exec postgres psql -U postgres -d convergio_db -c "SELECT COUNT(*) FROM talents;"
```

### Test Ali Agent
```bash
curl -X POST http://localhost:9000/api/v1/agents/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "chi sono i talent nel sistema?"}'
```

---

## Next Steps

1. **Run full test suite** to confirm 0 failures
2. **Complete parity tests** (J7, J8, J9) to ensure Agent Framework matches AutoGen behavior
3. **Generate final test report** (J10)
4. **Consider adding dedicated Talents page** in frontend
5. **Plan staged rollout** when ready for production

---

*Document generated: December 27, 2025*
*Author: Roberto D'Angelo with AI team assistance*
