# 🧪 Test Suite

This folder contains all tests for the Convergio project.

## 📁 Structure

```
tests/
├── README.md                    # This file
├── run_integration_tests.py     # Runner for all integration tests
├── backend/                     # Backend-specific tests
├── frontend/                    # Frontend-specific tests
├── end2end/                     # End-to-end tests
└── integration/                 # Integration tests
    ├── test_agents_simple.py           # Agent definitions test
    ├── test_agents_standalone.py       # Standalone agent test
    ├── test_ali_coordination.py        # Ali coordination test
    ├── test_multiagent_conversations.py # Multi-agent conversations test
    ├── test_performance_optimization.py # Performance optimization test
    └── test_performance_simple.py      # Simplified performance test
```

## 🚀 Running Tests

### All tests
```bash
make test
```

### Integration tests only
```bash
make test-integration
# or
python tests/run_integration_tests.py
```

### Specific tests

**Standalone (no backend dependencies required):**
```bash
make test-agents          # Standalone agent test (complete)
make test-agents-simple   # Simple agent definitions test
```

**Backend-dependent (require backend dependencies):**
```bash
make test-coordination    # Ali coordination test
make test-conversations   # Multi-agent conversations test
make test-performance     # Performance test
make test-performance-full # Performance optimization test
```

### Individual tests

**Standalone:**
```bash
python tests/integration/test_agents_simple.py      # Simple definitions test
python tests/integration/test_agents_standalone.py  # Complete standalone test
```

**Backend-dependent:**
```bash
python tests/integration/test_ali_coordination.py
python tests/integration/test_multiagent_conversations.py
python tests/integration/test_performance_simple.py
python tests/integration/test_performance_optimization.py
```

## 📊 Test Types

### 🧪 Standalone Agent Test (`test_agents_standalone.py`)
- **Completely independent** - no backend dependencies required
- Validates all 41 agent definitions
- Verifies YAML metadata presence
- Checks file definition structure
- Analyzes expertise and tier coverage
- Tests Ali coordination in simplified mode

### 🧪 Simple Agent Test (`test_agents_simple.py`)
- Basic test for agent definition validation
- Verifies YAML metadata presence

### 🎯 Ali Coordination Test (`test_ali_coordination.py`)
- Tests Ali's coordination capabilities with all agents
- Verifies knowledge base of agents
- Analyzes distribution by tier
- Tests routing logic

### 💬 Multi-Agent Conversations Test (`test_multiagent_conversations.py`)
- Simulates complex conversations between agents
- Tests multi-agent coordination scenarios
- Verifies collaboration effectiveness

### ⚡ Performance Tests (`test_performance_simple.py`, `test_performance_optimization.py`)
- Measures performance with 41 simultaneous agents
- Tests lookup and access speed
- Analyzes scaling behavior
- Verifies memory usage

## 🔧 Configuration

Tests use relative paths based on project structure:
- `project_root/backend/` for backend code
- `project_root/backend/src/agents/definitions/` for agent definitions

## 📈 Success Criteria

- **Agents**: All 41 agents must have valid definitions
- **Coordination**: Coverage >= 90%, routing >= 60%
- **Conversations**: Success rate >= 80%, coverage >= 70%
- **Performance**: Score >= 70/100 for production

## 🐛 Troubleshooting

If tests fail:

1. **Import Error**: Verify backend dependencies are installed
2. **Path Error**: Check project structure is correct
3. **Agent Error**: Verify all agent files are present in `backend/src/agents/definitions/`

## 💜 Notes

These tests are dedicated to Mario and the FightTheStroke Foundation, to ensure the AI agent system is robust and accessible.