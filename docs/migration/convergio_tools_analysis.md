# Convergio Tools Migration Analysis

**Task**: C3.1 - Analyze convergio_tools structure
**Date**: 2025-12-27
**Status**: Complete

## File Overview

**File**: `backend/src/agents/tools/convergio_tools.py`
**Lines**: 280
**Current Framework**: AutoGen (`autogen_core.tools.BaseTool`)

## Current Structure

### Imports (Line 12)
```python
from autogen_core.tools import BaseTool
```

### Tool Classes

| Class | Lines | Args Model | Description |
|-------|-------|------------|-------------|
| `TalentsQueryTool` | 31-86 | `TalentsQueryArgs` | Query talent information |
| `VectorSearchTool` | 94-138 | `VectorSearchArgs` | Semantic search with embeddings |
| `EngagementAnalyticsTool` | 145-214 | `EngagementAnalyticsArgs` | Business analytics |
| `BusinessIntelligenceTool` | 221-269 | `BusinessIntelligenceArgs` | Comprehensive BI reports |

### Imported Tools (from web_search_tool.py)
- `WebSearchTool`
- `WebBrowseTool`

### Exported Tools (Line 273-280)
```python
CONVERGIO_TOOLS = [
    TalentsQueryTool(),
    VectorSearchTool(),
    EngagementAnalyticsTool(),
    BusinessIntelligenceTool(),
    WebSearchTool(),
    WebBrowseTool(),
]
```

## Migration Status

### Already Migrated (in agent_framework_tools.py)
These functionalities already exist with `@ai_function`:
- `get_talents_summary()` - covers TalentsQueryTool(count)
- `get_talent_by_username()` - covers TalentsQueryTool(specific)
- `search_talents()` - covers TalentsQueryTool(search)
- `vector_search()` - covers VectorSearchTool
- `web_search()` - covers WebSearchTool

### Needs Migration
- `EngagementAnalyticsTool` - engagement/business analytics
- `BusinessIntelligenceTool` - comprehensive BI reports

## Migration Plan

### Option A: Add Missing Functions to agent_framework_tools.py
Add `@ai_function` decorated versions:
```python
@ai_function
async def get_engagement_analytics(analysis_type: str = "summary") -> str:
    ...

@ai_function
async def get_business_intelligence(focus_area: str = "overview") -> str:
    ...
```

### Option B: Keep Class-Based for Complex Tools
The class-based approach is better for tools that:
- Maintain internal state
- Compose other tools (like BusinessIntelligenceTool)
- Have complex initialization

### Recommendation
Use **Option A** - migrate to `@ai_function` pattern for consistency.
The class-based approach adds complexity that isn't needed for these tools.

## Dependencies

- `httpx` - async HTTP client
- `structlog` - logging
- `pydantic` - args validation
- `vector_search_client` - embedding functions

## Implementation Notes

1. The existing `agent_framework_tools.py` already covers most use cases
2. Add missing analytics tools as `@ai_function` decorated functions
3. Keep `CONVERGIO_TOOLS` as backward-compatible export
4. Add `get_convergio_tools_af()` function for AF-native access
