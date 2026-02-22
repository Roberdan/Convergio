# Backend Conventions (Convergio)

## API Framework
- **FastAPI**: All endpoints must use FastAPI and be fully async (async def).
- **Type hints**: All public API functions and methods must have complete Python type hints.

## Database
- **SQLAlchemy 2.0**: Use SQLAlchemy 2.0 async ORM sessions for all DB access.
- **Session management**: Use dependency-injected async session per request.

## Data Validation
- **Pydantic v2**: All request/response schemas must use Pydantic v2 models.

## Logging
- **structlog**: Use structlog with JSON output for all logging (no print/logging module).

## Testing
- **pytest**: All tests must use pytest. Use fixtures for setup/teardown.

## Linting & Formatting
- **ruff**: Run `ruff check backend/` for linting. All code must pass ruff with project config.

## Commands
- Run tests: `pytest backend/`
- Lint: `ruff check backend/`
- Run dev server: `uvicorn backend.main:app --reload`

