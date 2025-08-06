# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Convergio2030** is a unified AI-native business platform that consolidates multiple microservices into a single Python backend. The platform provides AI agent orchestration, vector search, talent management, and real-time analytics through a modern FastAPI + SvelteKit architecture.

### Core Architecture

The project follows a **unified architecture** replacing 4 separate microservices:
- **Backend**: Single Python FastAPI service (port 9000)
- **Frontend**: SvelteKit application (port 4000) 
- **Database**: Shared PostgreSQL with vector extensions
- **Cache**: Redis for sessions and caching

## Development Commands

### Backend (Python FastAPI)
```bash
# Start the unified backend
cd backend && python -m uvicorn src.main:app --host 0.0.0.0 --port 9000 --reload

# Alternative: Use the production startup script
python start.py

# Install dependencies
cd backend && pip install -r requirements.txt

# Database migrations (when available)
cd backend && alembic upgrade head

# Run tests
cd backend && pytest
```

### Frontend (SvelteKit)
```bash
# Start development server
cd frontend && npm run dev

# Build for production
cd frontend && npm run build

# Install dependencies
cd frontend && npm install

# Run tests
cd frontend && npm run test

# Run E2E tests
cd frontend && npm run test:e2e

# Lint and format
cd frontend && npm run lint
cd frontend && npm run format
```

## Key Configuration

### Environment Setup
- **Root .env file**: Single source of truth for all configuration (DO NOT MODIFY without permission)
- **Port assignments**: Backend (9000), Frontend (4000), Gateway (9001) - no conflicts
- **JWT Authentication**: RS256 with RSA keys in `secrets/jwt/`

### Dependencies
- **Backend**: FastAPI 0.115.6, SQLAlchemy 2.0.36, AutoGen 0.7.1, Redis 5.2.1
- **Frontend**: SvelteKit 2.26.1, TypeScript 5.8.3, TailwindCSS 3.4.17, Playwright 1.54.2

## AI Agent System

The platform includes 40+ specialized AI agents located in `backend/src/agents/definitions/`:
- **Ali**: Chief of Staff (orchestrator)
- **Amy**: CFO (financial analysis)
- **Baccio**: Tech Architect
- **Sofia**: Marketing Strategist
- **Luca**: Security Expert
- Plus 35+ other specialized agents

### Agent Orchestration
- Uses AutoGen 0.7.1 for multi-agent workflows
- Integrated with OpenAI GPT-4 and Anthropic Claude
- State management via Redis
- Vector search for context retrieval

## Database Architecture

### PostgreSQL Setup
- **Shared database**: `convergio_db` (compatible with original Convergio)
- **Vector extensions**: pgvector for embedding storage
- **Connection pooling**: AsyncPG with 20 connections
- **Models**: SQLAlchemy 2.0 with async support

### Key Models
- `backend/src/models/talent.py`: User and talent management
- `backend/src/models/document.py`: Document and vector storage

## API Structure

### Core Endpoints
- `/health`: Health checks and system status
- `/api/v1/talents`: Talent and resource management
- `/api/v1/agents`: AI agent orchestration
- `/api/v1/vector`: Vector search and embeddings
- `/docs`: OpenAPI documentation (dev only)
- `/metrics`: Prometheus metrics

### Security Features
- **Rate limiting**: 100 requests/minute with SlowAPI
- **CORS**: Configured for frontend ports
- **JWT RS256**: Military-grade authentication
- **Structured logging**: With request IDs and tracing

## Vector Search Integration

- **Embeddings**: sentence-transformers for text encoding
- **Storage**: PostgreSQL with pgvector extension
- **Search**: FAISS and ChromaDB for similarity search
- **Dimension**: 1536-dimensional vectors (OpenAI compatible)

## Development Guidelines

### File Structure
```
convergio/
├── backend/src/
│   ├── api/          # FastAPI routers
│   ├── agents/       # AI agent definitions and orchestration
│   ├── core/         # Configuration, database, logging
│   ├── models/       # SQLAlchemy models
│   ├── utils/        # Shared utilities
│   └── vector/       # Vector search implementation
├── frontend/src/
│   ├── routes/       # SvelteKit pages
│   ├── lib/          # Shared components and utilities
│   └── tests/        # Frontend tests
└── secrets/jwt/      # RSA keys for JWT
```

### Testing Strategy
- **Backend**: pytest with async support, fakeredis for mocking
- **Frontend**: Vitest for unit tests, Playwright for E2E
- **Coverage**: pytest-cov for backend coverage reporting

### Performance Considerations
- **Async/await**: Throughout the backend for non-blocking I/O
- **Connection pooling**: For database and Redis connections
- **Caching**: Redis for session data and frequent queries
- **Background tasks**: Celery and RQ for async processing

## Monitoring and Observability

- **Structured logging**: JSON format with correlation IDs
- **Metrics**: Prometheus endpoints at `/metrics`
- **Health checks**: Comprehensive health status at `/health`
- **Request tracing**: X-Request-ID headers for debugging

## Production Deployment

The application is designed for containerized deployment with:
- **Docker**: Multi-stage builds for optimization
- **Environment separation**: Development, staging, production configs
- **Security**: Trusted hosts, rate limiting, secure headers
- **Scalability**: Horizontal scaling with multiple workers