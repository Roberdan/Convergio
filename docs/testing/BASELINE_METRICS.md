# Test Baseline Metrics - Agent Framework Migration

**Generated:** 2025-12-27 17:16:04 CET
**Status:** PRE-MIGRATION BASELINE
**Framework:** AutoGen (Current) → Microsoft Agent Framework (Target)

## Executive Summary

The test suite is currently **NON-FUNCTIONAL** due to missing AutoGen dependencies. All tests that depend on the backend server cannot run because of import errors related to AutoGen modules.

### Critical Issues

- **Total Test Files:** 59 Python test files
- **Tests Collected:** 148 tests (before collection errors)
- **Collection Errors:** 8 test modules fail to import
- **Execution Status:** 0 tests can run successfully
- **Primary Blocker:** Missing `autogen_agentchat`, `autogen_core`, `autogen_ext` modules

## Test Statistics

### Test Organization

```
tests/
├── backend/
│   ├── unit/              # 95+ unit tests
│   └── integration/       # Backend integration tests
├── integration/           # 25+ integration test modules
├── e2e/                   # 9 end-to-end test modules
├── performance/           # 3 performance test modules
└── security/              # 1 security test module

Total Test Files: 59
Total Test Modules: ~55 (excluding utilities)
```

### Test Collection Results

```
Collected Tests:     148 tests
Collection Errors:   8 modules
Import Failures:     100% (all tests blocked by AutoGen imports)
```

### Test Execution Results

**All tests are currently BLOCKED** and cannot execute due to:

1. **Backend Server Startup Failure**
   - Error: `ModuleNotFoundError: No module named 'autogen_agentchat'`
   - Affects: ALL tests requiring backend (95%+ of test suite)

2. **Direct Import Failures**
   - 8 test modules fail during pytest collection
   - Additional modules fail during backend server startup

## AutoGen Dependencies Analysis

### Test Files Using AutoGen (Direct Imports)

Based on code analysis, the following test files have direct AutoGen imports:

1. **tests/integration/test_ali_coordination.py**
   - Imports: `DynamicAgentLoader` which imports `autogen_agentchat.agents.AssistantAgent`
   - Status: Fails at import with `sys.exit(1)`

2. **tests/integration/test_streaming_functionality.py**
   - Line 165: `from autogen_agentchat.agents import AssistantAgent`
   - Line 166: `from autogen_ext.models.openai import OpenAIChatCompletionClient`

3. **tests/e2e/test_autogen_integration.py**
   - Comprehensive AutoGen 0.7.2 integration test suite
   - Tests group chat, turn-by-turn conversations, agent orchestration

4. **tests/backend/unit/test_vector_search_tool.py**
   - Imports: `from agents.tools.convergio_tools import VectorSearchTool`
   - Which imports: `from autogen_core.tools import BaseTool`

### Backend Source Files Using AutoGen

The following backend files require AutoGen and block test execution:

1. **backend/src/agents/orchestrators/unified.py**
   - `from autogen_agentchat.agents import AssistantAgent`

2. **backend/src/agents/services/agent_loader.py**
   - `from autogen_agentchat.agents import AssistantAgent`

3. **backend/src/agents/tools/convergio_tools.py**
   - `from autogen_core.tools import BaseTool`

4. **backend/src/agents/services/agent_framework_loader.py**
   - AutoGen framework integration

5. **backend/src/agents/compatibility/** (multiple files)
   - `agent_adapter.py`
   - `message_adapter.py`
   - `workflow_adapter.py`

6. **backend/src/agents/services/groupchat/** (multiple files)
   - `setup.py`
   - `turn_by_turn_selector.py`
   - `initializer.py`
   - `per_turn_rag.py`

7. **backend/src/agents/memory/autogen_memory_system.py**
   - AutoGen memory integration

8. **backend/src/agents/orchestrator.py**
   - Core orchestrator using AutoGen

9. **backend/src/main.py**
   - Application entry point that imports AutoGen-dependent modules

### Additional Test Files Likely Affected

The following test files reference "autogen" or "AutoGen" in their content but don't have direct imports (they may test AutoGen functionality indirectly):

- `tests/master_test_runner.py`
- `tests/backend/unit/test_hitl_flag_behavior.py`
- `tests/backend/unit/test_feature_flags_behavior.py`
- `tests/backend/test_memory_system.py`
- `tests/backend/unit/test_config_settings.py`
- `tests/integration/test_scenarios/golden_scenarios.py`
- `tests/integration/test_rag_functionality.py`
- `tests/integration/test_multiagent_conversations.py`

## Test Categories and Migration Impact

### High-Risk Tests (Will Definitely Break)

**Category: AutoGen Direct Integration (3 files)**
- `test_autogen_integration.py` - Tests AutoGen 0.7.2 specifically
- `test_ali_coordination.py` - Tests agent coordination via AutoGen
- `test_streaming_functionality.py` - Tests streaming with AutoGen agents

**Impact:** Complete rewrite required

### Medium-Risk Tests (Likely to Break)

**Category: Agent Orchestration (20+ files)**
- All tests in `tests/backend/` requiring backend server
- All tests in `tests/integration/` testing agent workflows
- Group chat and conversation tests
- Memory system tests

**Impact:** Significant modifications required

### Low-Risk Tests (May Break)

**Category: Utility and Configuration (10+ files)**
- Configuration tests
- Database tests (if they don't depend on backend server)
- Basic unit tests without agent dependencies

**Impact:** Minor modifications or no changes

## Test Execution Time

**Current:** Cannot measure (tests don't run)
**Estimated Baseline:** 60-120 seconds for full suite (based on timeouts observed)

## Code Coverage

**Current:** Not measurable (no tests can run)
**Baseline:** Unknown - no coverage data available

## Failure Patterns

### Import Error Pattern

```
ModuleNotFoundError: No module named 'autogen_agentchat'
  File "backend/src/agents/orchestrators/unified.py", line 11
    from autogen_agentchat.agents import AssistantAgent
```

**Occurrences:** 100% of test runs
**Blocking:** All backend-dependent tests

### Backend Server Startup Pattern

```
RuntimeError: Failed to start backend test server on port 9000
```

**Occurrences:** All tests requiring `ensure_backend_server` fixture
**Root Cause:** Import errors during server initialization

## Test Infrastructure

### Test Fixtures (tests/conftest.py)

Key fixtures that will need updates:

1. **`ensure_backend_server`** (line 249)
   - Starts backend server on port 9000
   - Currently fails due to AutoGen imports
   - **Action Required:** Update to use new Agent Framework

2. **Agent-related fixtures**
   - May depend on AutoGen agent types
   - **Action Required:** Review and update

### Test Configuration

- **pytest.ini:** Located in tests/
- **conftest.py:** 21,833 bytes - substantial fixture infrastructure
- **master_test_runner.py:** 31,840 bytes - custom test orchestration

## Migration Recommendations

### Phase 1: Infrastructure Setup

1. **Create Migration Test Branch**
   - Preserve current tests as reference
   - Track changes systematically

2. **Update Test Dependencies**
   - Remove AutoGen dependencies from test requirements
   - Add Microsoft Agent Framework dependencies
   - Update fixture infrastructure

### Phase 2: Test Categorization

1. **Isolate AutoGen-Specific Tests**
   - Mark tests that test AutoGen specifically
   - Consider archiving or complete rewrite

2. **Identify Reusable Tests**
   - Tests that test business logic, not framework
   - Can be adapted with fixture updates

### Phase 3: Incremental Migration

1. **Start with Unit Tests**
   - Lowest framework dependency
   - Quickest wins

2. **Move to Integration Tests**
   - Update agent orchestration tests
   - Verify workflow compatibility

3. **End with E2E Tests**
   - Complete system verification
   - Performance validation

## Critical Test Files for Migration Priority

### Must Fix First (Blockers)

1. **tests/conftest.py** - Core fixture infrastructure
2. **backend/src/main.py** - Application startup
3. **backend/src/agents/orchestrator.py** - Core orchestration

### High Priority (Core Functionality)

1. **tests/backend/unit/test_orchestrator_comprehensive.py** (47 tests)
2. **tests/backend/test_backend_comprehensive.py** (11 tests)
3. **tests/integration/test_agents.py**
4. **tests/integration/test_multiagent_conversations.py**

### Medium Priority (Features)

1. **tests/integration/test_graphflow_complete.py**
2. **tests/integration/test_workflow_generator.py**
3. **tests/backend/test_memory_system.py**
4. **tests/integration/test_rag_functionality.py**

### Low Priority (Nice to Have)

1. **tests/performance/** - Performance tests
2. **tests/security/** - Security validation
3. **tests/e2e/test_cost_tracking_*.py** - Cost tracking

## Baseline Metrics Summary

| Metric | Value | Status |
|--------|-------|--------|
| Total Test Files | 59 | ✓ Counted |
| Total Tests | 148 | ⚠️ Estimated |
| Passing Tests | 0 | ❌ None can run |
| Failing Tests | 0 | ❌ None can run |
| Error on Collection | 8+ | ❌ Blocking |
| Test Execution Time | N/A | ❌ Cannot measure |
| Code Coverage | N/A | ❌ Cannot measure |
| AutoGen Dependencies | 20+ files | ✓ Identified |

## Next Steps for Task P0.2

1. **Identify Adapter Pattern Requirements**
   - Review how AutoGen agents are used
   - Map to Agent Framework equivalents

2. **Create Test Compatibility Layer**
   - Build adapters for test fixtures
   - Enable gradual migration

3. **Establish New Baseline**
   - After infrastructure fixes
   - Run minimal test to verify setup

## Appendices

### A. Test File Listing

See `find tests -name "*.py" -type f` output above (59 files total)

### B. AutoGen Import Locations

**Backend Source Files:** 20+ files identified
**Test Files:** 11 files with direct/indirect references

### C. Error Logs

Sample errors preserved in:
- `/tmp/pytest_output.txt`
- Collection errors documented in this report

---

**Report Status:** BASELINE CAPTURED
**Migration Status:** READY TO PROCEED
**Recommended Next Task:** P0.2 - Create Compatibility Adapters
