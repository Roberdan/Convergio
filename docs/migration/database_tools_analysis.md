# Database Tools Migration Analysis

**Task**: C1.1 - Analyze database_tools structure
**Date**: 2025-12-27
**Status**: Complete

## File Overview

**File**: `backend/src/agents/tools/database_tools.py`
**Lines**: 850
**Current Framework**: AutoGen (`autogen_core.tools.FunctionTool`)

## Current Structure

### Imports (Line 11)
```python
from autogen_core.tools import FunctionTool
```

### Helper Functions

| Function | Lines | Purpose |
|----------|-------|---------|
| `create_sync_db_session()` | 28-43 | Create sync DB session |
| `safe_run_sync_query()` | 46-75 | Execute sync queries safely |

### DatabaseTools Class (Lines 78-419)

Async class methods (NOT exposed as tools, internal use):
- `get_talents_summary()` - Line 82
- `get_talent_by_username()` - Line 120
- `get_department_overview()` - Line 160
- `get_documents_summary()` - Line 210
- `get_projects_overview()` - Line 261
- `search_documents()` - Line 319
- `get_system_health()` - Line 371

### Tool Functions (Lines 422-850)

These are the functions exposed as `FunctionTool` that need migration:

| Function | Lines | Parameters | Returns |
|----------|-------|------------|---------|
| `query_talents_count()` | 423-452 | None | str |
| `query_talent_details(name: str)` | 455-505 | name: str | str |
| `query_department_structure(department: str = None)` | 508-553 | department: Optional[str] | str |
| `query_knowledge_base()` | 556-591 | None | str |
| `search_knowledge(query: str)` | 594-648 | query: str | str |
| `query_ai_agent_info(agent_name: str)` | 651-689 | agent_name: str | str |
| `list_ai_agents()` | 692-720 | None | str |
| `query_projects()` | 767-811 | None | str |
| `query_system_status()` | 814-850 | None | str |

### get_database_tools() Function (Lines 723-764)

Returns `List[FunctionTool]` with 9 tools wrapped in `FunctionTool()`.

## Migration Plan

### Target Pattern

Replace:
```python
from autogen_core.tools import FunctionTool

def my_function() -> str:
    ...

FunctionTool(func=my_function, description="...")
```

With:
```python
from agent_framework import ai_function

@ai_function(description="...")
def my_function() -> str:
    ...
```

### Migration Tasks

1. **C1.2**: Migrate `query_talents_count` + `query_talent_details`
2. **C1.3**: Migrate `query_department_structure` + `query_system_status`
3. **C1.4**: Migrate `query_knowledge_base` + `search_knowledge`
4. **C1.5**: Migrate `query_ai_agent_info` + `list_ai_agents` + `query_projects`
5. **C1.6**: Unit tests for all migrated functions

### Compatibility Layer

The file should support both frameworks during migration:

```python
try:
    from agent_framework import ai_function
    AF_AVAILABLE = True
except ImportError:
    AF_AVAILABLE = False
    from autogen_core.tools import FunctionTool
```

### Files to Modify

1. `backend/src/agents/tools/database_tools.py` - Main migration
2. `tests/backend/unit/test_database_tools.py` - New unit tests

## Dependencies

- `agent_framework` package (already in requirements.txt)
- `sqlalchemy` - unchanged
- `structlog` - unchanged

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| AF not installed | Compatibility layer with fallback |
| Breaking existing tools | Keep `get_database_tools()` for backward compat |
| Async/sync conflicts | Tool functions already sync, no changes needed |

## Checkpoint

After C1.6, run:
```bash
pytest tests/backend/unit/test_database_tools.py -v
```
