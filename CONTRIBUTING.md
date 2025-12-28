# Contributing to Convergio

Thank you for your interest in contributing to Convergio! This document provides guidelines and standards for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing Requirements](#testing-requirements)
- [Documentation](#documentation)

## Code of Conduct

This project adheres to professional engineering standards. Please be respectful, constructive, and focused on technical merit in all interactions.

## Getting Started

### Prerequisites

- **Python**: 3.11 or higher
- **Node.js**: 18.x or higher
- **Docker**: Latest version (optional, for containerized development)
- **Git**: For version control

### Environment Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Roberdan/Convergio.git
   cd convergio
   ```

2. **Backend setup**:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Frontend setup**:
   ```bash
   cd frontend
   npm install
   ```

4. **Environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

5. **Verify setup**:
   ```bash
   # Backend tests
   cd backend && pytest

   # Frontend tests
   cd frontend && npm test
   ```

## Development Workflow

### Branching Strategy

- `master` - Main branch, always production-ready
- `feature/*` - New features (e.g., `feature/add-ollama-provider`)
- `fix/*` - Bug fixes (e.g., `fix/memory-leak-in-orchestrator`)
- `docs/*` - Documentation updates
- `refactor/*` - Code refactoring without behavior changes

### Commit Message Conventions

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style/formatting (no logic change)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples**:
```
feat(frontend): add dark mode toggle to settings
fix(backend): resolve memory leak in agent orchestrator
docs(readme): update installation instructions for v3.0.0
```

## Pull Request Process

### Before Submitting

1. **Run all checks locally**:
   ```bash
   # Frontend
   cd frontend
   npm run lint
   npm run check
   npm run build
   npm test
   npm audit

   # Backend
   cd backend
   ruff check .
   pytest
   ```

2. **Update documentation** if you changed functionality
3. **Add tests** for new features
4. **Update CHANGELOG.md** under `[Unreleased]` section

### PR Requirements

- [ ] All tests pass
- [ ] No linting errors
- [ ] No security vulnerabilities (npm audit passes)
- [ ] Code coverage maintained or improved
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Commit messages follow conventions
- [ ] PR title follows format: `<type>: <description>`

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
Describe how you tested your changes

## Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] All checks passing
```

### Review Process

1. GitHub Copilot will automatically review your PR (1-2 minutes)
2. A maintainer will review the PR
3. Address any feedback
4. Once approved, the PR will be merged using **merge commit** (NOT squash)

## Coding Standards

### Python (Backend)

- **Linter**: `ruff` with strict mode
- **Type hints**: Required for all functions
- **Formatter**: `ruff format`
- **Docstrings**: Required for public APIs (Google style)

```python
def process_agent_request(
    agent_id: str,
    payload: dict[str, Any]
) -> AgentResponse:
    """Process an incoming agent request.

    Args:
        agent_id: Unique identifier for the agent
        payload: Request payload containing action and parameters

    Returns:
        AgentResponse object with processing results

    Raises:
        AgentNotFoundError: If agent_id is not registered
    """
    ...
```

### TypeScript/Svelte (Frontend)

- **Linter**: ESLint v9+ with TypeScript plugin
- **Type safety**: Strict mode enabled
- **Formatter**: Prettier
- **Component structure**:
  - Script setup with TypeScript
  - Props typed with interfaces
  - Events typed with custom event types

```typescript
<script lang="ts">
  interface Props {
    agentId: string;
    status: 'active' | 'idle' | 'error';
  }

  let { agentId, status }: Props = $props();
</script>
```

### General Rules

- **No TODOs/FIXMEs** in production code (use issues instead)
- **No console.log** in production code (use proper logging)
- **No commented-out code**
- **No hardcoded secrets** (use environment variables)
- **All files must be in English** (code, comments, docs, UI)

## Testing Requirements

### Backend Tests

- **Unit tests**: All business logic must have unit tests
- **Integration tests**: API endpoints must have integration tests
- **Coverage**: Minimum 80% coverage for new code
- **Framework**: pytest

```bash
cd backend
pytest --cov=. --cov-report=html
```

### Frontend Tests

- **Unit tests**: Vitest for utility functions
- **Component tests**: Vitest for Svelte components
- **E2E tests**: Playwright for critical user flows
- **Coverage**: Minimum 80% for new features

```bash
cd frontend
npm run test:coverage
npm run test:e2e
```

### Test Guidelines

- Tests must be deterministic (no flaky tests)
- Mock external APIs and services
- Use fixtures for test data
- Test both success and failure cases
- Include edge cases

## Documentation

### Required Documentation

1. **README.md**: Keep updated with major changes
2. **CHANGELOG.md**: Update under `[Unreleased]` for all changes
3. **API Documentation**: Update if you change backend APIs
4. **ADRs**: Create Architecture Decision Records for significant design decisions

### ADR Template

Create in `docs/adr/ADR-XXX-title.md`:

```markdown
# ADR-XXX: Title

## Status
Proposed | Accepted | Deprecated | Superseded

## Context
What is the issue we're facing?

## Decision
What decision are we making?

## Consequences
What are the positive and negative impacts?

## Alternatives Considered
What other options were evaluated?
```

## Release Process

Releases are managed by maintainers:

1. Version bump in VERSION, package.json files
2. CHANGELOG.md updated with release date
3. Create release branch: `release/vX.Y.Z`
4. Final validation with BRUTAL release manager agent
5. PR to master with full review
6. Merge (merge commit, not squash)
7. Tag: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
8. Push tag: `git push origin vX.Y.Z`
9. GitHub Release created automatically

## Questions?

- Open an issue for bugs or feature requests
- Check existing issues and PRs first
- For security issues, email security@convergio.io (do not open public issues)

## License

By contributing to Convergio, you agree that your contributions will be licensed under the BSL 1.1 License.
